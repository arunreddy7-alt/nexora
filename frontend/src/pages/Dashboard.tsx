import { useState } from "react";

import TeamsPanel from "../components/TeamsPanel";
import MeetingsPanel from "../components/MeetingsPanel";
import DownloadProjectButton from "../components/DownloadProjectButton";

const API_BASE_URL = "http://127.0.0.1:8000";

type ProjectFile = {
  path: string;
  content: string;
};

type PreviewData = {
  project_id: number;
  status: string;
  url?: string | null;
  port?: number;
};

type PipelineResponse = {
  preview?: PreviewData;
};

type ModificationResponse = {
  project_id: number;
  instruction: string;

  modifier?: {
    diagnosis?: {
      request?: string;
      approach?: string;
      explanation?: string;
    };

    files_to_update?: unknown[];
    files_to_create?: unknown[];
    files_to_delete?: unknown[];

    dependencies_changed?: boolean;
  };

  changes?: {
    project_id?: number;
    updated_files?: string[];
    created_files?: string[];
    deleted_files?: string[];
    total_changes?: number;
  };

  execution?: {
    install?: {
      success?: boolean;
      skipped?: boolean;
      message?: string;
    };

    test?: {
      success?: boolean;
      test?: {
        success?: boolean;
        stderr?: string;
        stdout?: string;
      };
    };

    build?: {
      success?: boolean;
      build?: {
        success?: boolean;
        stderr?: string;
        stdout?: string;
      };
    };
  };

  success?: boolean;
};

type ActivePanel =
  | "projects"
  | "teams"
  | "meetings";

export default function Dashboard({
  onLogout,
}: {
  onLogout: () => void;
}) {
  const [description, setDescription] =
    useState("");

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  const [pipeline, setPipeline] =
    useState<PipelineResponse | null>(null);

  const [previewUrl, setPreviewUrl] =
    useState<string | null>(null);

  const [files, setFiles] =
    useState<ProjectFile[]>([]);

  const [selectedFile, setSelectedFile] =
    useState<ProjectFile | null>(null);

  const [projectId, setProjectId] =
    useState<number | null>(null);

  const [activePanel, setActivePanel] =
    useState<ActivePanel>("projects");

  const [modifying, setModifying] =
    useState(false);

  const [modificationResult, setModificationResult] =
    useState<ModificationResponse | null>(null);

  const token =
    localStorage.getItem("access_token");

  const headers: HeadersInit = {
    "Content-Type": "application/json",

    ...(token
      ? {
          Authorization: `Bearer ${token}`,
        }
      : {}),
  };

  // ==========================================================
  // NEW PROJECT
  // ==========================================================

  function startNewProject() {
    setProjectId(null);

    setDescription("");

    setError("");

    setPipeline(null);

    setPreviewUrl(null);

    setFiles([]);

    setSelectedFile(null);

    setModificationResult(null);

    setModifying(false);

    setActivePanel("projects");
  }

  // ==========================================================
  // GENERATE PROJECT
  // ==========================================================

  async function generateProject() {
    if (!description.trim()) {
      setError(
        "Describe what you want to build first."
      );

      return;
    }

    setLoading(true);

    setError("");

    setPipeline(null);

    setPreviewUrl(null);

    setFiles([]);

    setSelectedFile(null);

    setModificationResult(null);

    setProjectId(null);

    try {
      // ------------------------------------------------------
      // CREATE PROJECT
      // ------------------------------------------------------

      const projectResponse =
        await fetch(
          `${API_BASE_URL}/api/projects`,
          {
            method: "POST",
            headers,

            body: JSON.stringify({
              name: description
                .trim()
                .slice(0, 50),

              description:
                description.trim(),
            }),
          }
        );

      const projectData =
        await projectResponse.json();

      if (!projectResponse.ok) {
        throw new Error(
          projectData?.detail ||
            "Could not create project."
        );
      }

      const createdProjectId =
        projectData.id;

      setProjectId(
        createdProjectId
      );

      // ------------------------------------------------------
      // RUN PIPELINE
      // ------------------------------------------------------

      const pipelineResponse =
        await fetch(
          `${API_BASE_URL}/api/projects/${createdProjectId}/agent-outputs/run-pipeline?project_description=${encodeURIComponent(
            description.trim()
          )}`,
          {
            method: "POST",
            headers,
          }
        );

      const data =
        await pipelineResponse.json();

      console.log(
        "PIPELINE RESPONSE:",
        data
      );

      if (!pipelineResponse.ok) {
        throw new Error(
          data?.detail ||
            "Pipeline failed."
        );
      }

      setPipeline(data);

      // ------------------------------------------------------
      // SAVE PREVIEW URL
      // ------------------------------------------------------

      if (data.preview?.url) {
        setPreviewUrl(
          data.preview.url
        );
      }

      // ------------------------------------------------------
      // LOAD WORKSPACE
      // ------------------------------------------------------

      await loadWorkspace(
        createdProjectId
      );
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Something went wrong."
      );
    } finally {
      setLoading(false);
    }
  }

  // ==========================================================
  // MODIFY EXISTING PROJECT
  // ==========================================================

  async function modifyProject() {
    if (!projectId) {
      setError(
        "Create a project before modifying it."
      );

      return;
    }

    if (!description.trim()) {
      setError(
        "Describe what you want to change."
      );

      return;
    }

    setModifying(true);

    setError("");

    setModificationResult(null);

    try {
      const response =
        await fetch(
          `${API_BASE_URL}/api/projects/${projectId}/agent-outputs/modify?instruction=${encodeURIComponent(
            description.trim()
          )}`,
          {
            method: "POST",
            headers,
          }
        );

      const data =
        await response.json();

      console.log(
        "MODIFICATION RESPONSE:",
        data
      );

      if (!response.ok) {
        throw new Error(
          data?.detail ||
            "Could not modify project."
        );
      }

      setModificationResult(data);

      if (data.success === false) {
        throw new Error(
          "The project was modified, but the final build did not succeed."
        );
      }

      // ------------------------------------------------------
      // IMPORTANT:
      // Keep the existing project ID.
      // We DO NOT create a new project here.
      // ------------------------------------------------------

      await loadWorkspace(
        projectId
      );

      // ------------------------------------------------------
      // KEEP EXISTING PREVIEW
      // ------------------------------------------------------

      if (previewUrl) {
        const separator =
          previewUrl.includes("?")
            ? "&"
            : "?";

        const refreshedUrl =
          `${previewUrl}${separator}refresh=${Date.now()}`;

        setPreviewUrl(
          refreshedUrl
        );
      }

      // Clear the modification prompt
      // after a successful update.

      setDescription("");
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Something went wrong."
      );
    } finally {
      setModifying(false);
    }
  }

  // ==========================================================
  // LOAD WORKSPACE
  // ==========================================================

  async function loadWorkspace(
    currentProjectId: number
  ) {
    const response =
      await fetch(
        `${API_BASE_URL}/api/projects/${currentProjectId}/agent-outputs/workspace`,
        {
          headers,
        }
      );

    const data =
      await response.json();

    if (!response.ok) {
      throw new Error(
        data?.detail ||
          "Could not load workspace."
      );
    }

    const projectFiles:
      ProjectFile[] =
      data.files || [];

    setFiles(
      projectFiles
    );

    if (projectFiles.length > 0) {
      setSelectedFile(
        projectFiles[0]
      );
    } else {
      setSelectedFile(null);
    }
  }

  // ==========================================================
  // UI
  // ==========================================================

  return (
    <div className="dashboard">

      {/* ================================================== */}
      {/* NAVIGATION */}
      {/* ================================================== */}

      <header className="dashboard-nav">

        <div className="brand">

          <span className="brand-mark">
            N
          </span>

          <span>
            Nexora
          </span>

        </div>

        <nav className="dashboard-tabs">

          <button
            className={
              activePanel === "projects"
                ? "dashboard-tab active"
                : "dashboard-tab"
            }
            onClick={() =>
              setActivePanel(
                "projects"
              )
            }
          >
            Projects
          </button>

          <button
            className={
              activePanel === "teams"
                ? "dashboard-tab active"
                : "dashboard-tab"
            }
            onClick={() =>
              setActivePanel("teams")
            }
          >
            Teams
          </button>

          <button
            className={
              activePanel === "meetings"
                ? "dashboard-tab active"
                : "dashboard-tab"
            }
            onClick={() =>
              setActivePanel(
                "meetings"
              )
            }
          >
            Meetings
          </button>

        </nav>

        <div className="dashboard-nav-right">

          <span className="nav-status">

            <span className="live-dot" />

            AI ENGINEERING PLATFORM

          </span>

          <button
            className="ghost-button dark-ghost"
            onClick={onLogout}
          >
            Logout
          </button>

        </div>

      </header>

      {/* ================================================== */}
      {/* TEAMS */}
      {/* ================================================== */}

      {activePanel === "teams" && (
        <main className="dashboard-main">

          <TeamsPanel />

        </main>
      )}

      {/* ================================================== */}
      {/* MEETINGS */}
      {/* ================================================== */}

      {activePanel === "meetings" && (
        <main className="dashboard-main">

          <MeetingsPanel />

        </main>
      )}

      {/* ================================================== */}
      {/* PROJECTS */}
      {/* ================================================== */}

      {activePanel === "projects" && (
        <main className="dashboard-main">

          {/* ================================================= */}
          {/* BUILDER / MODIFIER */}
          {/* ================================================= */}

          <div className="dashboard-hero">

            <div className="section-kicker light-kicker">

              {projectId
                ? "// EXISTING PROJECT"
                : "// MULTI-AGENT SOFTWARE ENGINEERING"}

            </div>

            <h1>

              {projectId ? (
                <>
                  What would you
                  <br />
                  <span>
                    change?
                  </span>
                </>
              ) : (
                <>
                  What should we
                  <br />
                  <span>
                    build today?
                  </span>
                </>
              )}

            </h1>

            <p>

              {projectId
                ? "Describe any change you want to make to this project. Nexora will modify the existing application without creating a new project."
                : "Describe your application. Nexora will plan, architect, develop, test and launch it."}

            </p>

            <div className="builder-box">

              <textarea
                value={description}
                onChange={(event) =>
                  setDescription(
                    event.target.value
                  )
                }
                disabled={
                  loading ||
                  modifying
                }
                placeholder={
                  projectId
                    ? "e.g. Add dark mode, create a contact page, change the navbar, add authentication..."
                    : "e.g. Build an app for cafes with menus, reservations and online ordering..."
                }
              />

              <div className="builder-actions">

                <button
                  onClick={
                    projectId
                      ? modifyProject
                      : generateProject
                  }
                  disabled={
                    loading ||
                    modifying
                  }
                >

                  {loading
                    ? "Building project..."
                    : modifying
                    ? "Updating project..."
                    : projectId
                    ? "Modify Project →"
                    : "Generate Project →"}

                </button>

                {projectId &&
                  !loading &&
                  !modifying && (

                    <button
                      type="button"
                      className="ghost-button"
                      onClick={
                        startNewProject
                      }
                    >
                      + New Project
                    </button>

                  )}

              </div>

            </div>

            {error && (
              <div className="dashboard-error">
                {error}
              </div>
            )}

          </div>

          {/* ================================================= */}
          {/* MODIFICATION RESULT */}
          {/* ================================================= */}

          {modificationResult &&
            !modifying && (

              <section className="dashboard-section">

                <div className="project-action-card">

                  <div>

                    <div className="section-kicker light-kicker">
                      // PROJECT UPDATED
                    </div>

                    <h2>
                      Changes applied successfully.
                    </h2>

                    <p>
                      Project #
                      {projectId}
                      {" "}
                      was updated without
                      creating a new project.
                    </p>

                  </div>

                  <div className="project-actions">

                    <span className="pipeline-done">
                      ✓ BUILD PASSED
                    </span>

                    {modificationResult
                      .changes
                      ?.total_changes !==
                      undefined && (

                      <span>

                        {
                          modificationResult
                            .changes
                            .total_changes
                        }

                        {" "}
                        file
                        {modificationResult
                          .changes
                          .total_changes ===
                        1
                          ? ""
                          : "s"}{" "}
                        changed

                      </span>

                    )}

                  </div>

                </div>

              </section>

            )}

          {/* ================================================= */}
          {/* PIPELINE */}
          {/* ================================================= */}

          {loading && (
            <Pipeline
              running
            />
          )}

          {pipeline &&
            !loading && (
              <Pipeline />
            )}

          {/* ================================================= */}
          {/* PROJECT ACTIONS */}
          {/* ================================================= */}

          {projectId &&
            !loading && (

              <section className="dashboard-section project-actions-section">

                <div className="project-action-card">

                  <div>

                    <div className="section-kicker light-kicker">
                      // PROJECT READY
                    </div>

                    <h2>
                      Your project is ready.
                    </h2>

                    <p>
                      Preview, inspect,
                      modify or download
                      the application.
                    </p>

                  </div>

                  <div className="project-actions">

                    {previewUrl && (

                      <a
                        className="preview-link action-link"
                        href={previewUrl}
                        target="_blank"
                        rel="noreferrer"
                      >
                        Open Preview →
                      </a>

                    )}

                    <DownloadProjectButton
                      projectId={
                        projectId
                      }
                    />

                  </div>

                </div>

              </section>

            )}

          {/* ================================================= */}
          {/* LIVE PREVIEW */}
          {/* ================================================= */}

          {previewUrl && (

            <section className="dashboard-section">

              <div className="dashboard-section-head">

                <div>

                  <div className="section-kicker light-kicker">
                    // LIVE OUTPUT
                  </div>

                  <h2>
                    Live Preview
                  </h2>

                  <p>
                    Your generated
                    application is running.
                  </p>

                </div>

                <a
                  className="preview-link"
                  href={previewUrl}
                  target="_blank"
                  rel="noreferrer"
                >
                  Open preview →
                </a>

              </div>

              <div className="preview-shell">

                <div className="browser-bar">

                  <span />
                  <span />
                  <span />

                  <div>
                    {previewUrl}
                  </div>

                </div>

                <iframe
                  key={previewUrl}
                  src={previewUrl}
                  title="Generated Project Preview"
                />

              </div>

            </section>

          )}

          {/* ================================================= */}
          {/* WORKSPACE */}
          {/* ================================================= */}

          {files.length > 0 && (

            <section className="dashboard-section">

              <div className="dashboard-section-head">

                <div>

                  <div className="section-kicker light-kicker">
                    // WORKSPACE
                  </div>

                  <h2>
                    Generated Project
                  </h2>

                  <p>
                    {files.length}
                    {" "}
                    files currently
                    in the project.
                  </p>

                </div>

                {projectId && (

                  <DownloadProjectButton
                    projectId={
                      projectId
                    }
                    label="Download ZIP"
                  />

                )}

              </div>

              <div className="workspace-grid">

                <div className="file-list">

                  {files.map(
                    (file) => (

                      <button
                        key={file.path}
                        className={
                          selectedFile?.path ===
                          file.path
                            ? "file-item active"
                            : "file-item"
                        }
                        onClick={() =>
                          setSelectedFile(
                            file
                          )
                        }
                      >

                        <span>
                          ◈
                        </span>

                        {file.path}

                      </button>

                    )
                  )}

                </div>

                <div className="code-panel">

                  {selectedFile ? (
                    <>

                      <div className="code-title">
                        {
                          selectedFile.path
                        }
                      </div>

                      <pre>
                        {
                          selectedFile.content
                        }
                      </pre>

                    </>
                  ) : (

                    <div className="empty-code">
                      Select a file.
                    </div>

                  )}

                </div>

              </div>

            </section>

          )}

        </main>
      )}

    </div>
  );
}


/* ========================================================== */
/* PIPELINE                                                   */
/* ========================================================== */

function Pipeline({
  running = false,
}: {
  running?: boolean;
}) {

  const agents = [
    "CEO",
    "PM",
    "ARCHITECT",
    "DEVELOPER",
    "TEST",
    "BUILD",
  ];

  return (
    <section className="pipeline">

      <div className="pipeline-head">

        <div>

          <div className="section-kicker light-kicker">
            // ORCHESTRATOR
          </div>

          <h2>
            Engineering pipeline
          </h2>

        </div>

        <span
          className={
            running
              ? "pipeline-running"
              : "pipeline-done"
          }
        >
          {running
            ? "RUNNING"
            : "✓ COMPLETED"}
        </span>

      </div>

      <div className="pipeline-agents">

        {agents.map(
          (agent, index) => (

            <div
              className="pipeline-agent"
              key={agent}
            >

              <div
                className={
                  running
                    ? "agent-node"
                    : "agent-node done"
                }
              >
                {running
                  ? index + 1
                  : "✓"}
              </div>

              <span>
                {agent}
              </span>

              {index <
                agents.length - 1 && (

                <div className="agent-connector" />

              )}

            </div>

          )
        )}

      </div>

    </section>
  );
}