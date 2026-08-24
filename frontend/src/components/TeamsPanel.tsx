import { useEffect, useState } from "react";

const API_BASE_URL = "http://127.0.0.1:8000";

type Team = {
  id: number;
  name: string;
  owner_id: number;
  created_at: string;
};

type TeamMember = {
  id: number;
  team_id: number;
  user_id: number;
  role: string;
  joined_at: string;
};

type TeamProject = {
  id: number;
  name: string;
  description: string | null;
  owner_id: number;
  team_id: number | null;
  created_at: string;
};

function authHeaders(): HeadersInit {
  const token = localStorage.getItem("access_token");

  return {
    "Content-Type": "application/json",
    ...(token
      ? {
          Authorization: `Bearer ${token}`,
        }
      : {}),
  };
}

export default function TeamsPanel() {
  const [teams, setTeams] = useState<Team[]>([]);
  const [selectedTeam, setSelectedTeam] = useState<Team | null>(null);

  const [members, setMembers] = useState<TeamMember[]>([]);
  const [projects, setProjects] = useState<TeamProject[]>([]);

  const [teamName, setTeamName] = useState("");
  const [memberId, setMemberId] = useState("");

  const [loading, setLoading] = useState(false);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    loadTeams();
  }, []);

  async function loadTeams() {
    try {
      setLoading(true);
      setError("");

      const response = await fetch(
        `${API_BASE_URL}/api/teams`,
        {
          headers: authHeaders(),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data?.detail || "Failed to load teams."
        );
      }

      setTeams(data);
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Failed to load teams."
      );
    } finally {
      setLoading(false);
    }
  }

  async function createTeam() {
    if (!teamName.trim()) {
      setError("Enter a team name.");
      return;
    }

    try {
      setLoading(true);
      setError("");

      const response = await fetch(
        `${API_BASE_URL}/api/teams`,
        {
          method: "POST",
          headers: authHeaders(),
          body: JSON.stringify({
            name: teamName.trim(),
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data?.detail || "Failed to create team."
        );
      }

      setTeams((current) => [
        ...current,
        data,
      ]);

      setTeamName("");
      setSelectedTeam(data);

      await loadTeamDetails(data.id);
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Failed to create team."
      );
    } finally {
      setLoading(false);
    }
  }

  async function loadTeamDetails(teamId: number) {
    try {
      setLoadingDetails(true);
      setError("");

      const [membersResponse, projectsResponse] =
        await Promise.all([
          fetch(
            `${API_BASE_URL}/api/teams/${teamId}/members`,
            {
              headers: authHeaders(),
            }
          ),
          fetch(
            `${API_BASE_URL}/api/teams/${teamId}/projects`,
            {
              headers: authHeaders(),
            }
          ),
        ]);

      const membersData = await membersResponse.json();
      const projectsData = await projectsResponse.json();

      if (!membersResponse.ok) {
        throw new Error(
          membersData?.detail ||
            "Failed to load team members."
        );
      }

      if (!projectsResponse.ok) {
        throw new Error(
          projectsData?.detail ||
            "Failed to load team projects."
        );
      }

      setMembers(membersData);
      setProjects(projectsData);
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Failed to load team details."
      );
    } finally {
      setLoadingDetails(false);
    }
  }

  async function selectTeam(team: Team) {
    setSelectedTeam(team);
    await loadTeamDetails(team.id);
  }

  async function addMember() {
    if (!selectedTeam) return;

    const parsedUserId = Number(memberId);

    if (!parsedUserId || parsedUserId <= 0) {
      setError("Enter a valid user ID.");
      return;
    }

    try {
      setError("");

      const response = await fetch(
        `${API_BASE_URL}/api/teams/${selectedTeam.id}/members`,
        {
          method: "POST",
          headers: authHeaders(),
          body: JSON.stringify({
            user_id: parsedUserId,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data?.detail || "Failed to add member."
        );
      }

      setMembers((current) => [
        ...current,
        data,
      ]);

      setMemberId("");
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Failed to add member."
      );
    }
  }

  async function removeMember(userId: number) {
    if (!selectedTeam) return;

    try {
      setError("");

      const response = await fetch(
        `${API_BASE_URL}/api/teams/${selectedTeam.id}/members/${userId}`,
        {
          method: "DELETE",
          headers: authHeaders(),
        }
      );

      const data =
        response.status === 204
          ? null
          : await response.json();

      if (!response.ok) {
        throw new Error(
          data?.detail || "Failed to remove member."
        );
      }

      setMembers((current) =>
        current.filter(
          (member) => member.user_id !== userId
        )
      );
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Failed to remove member."
      );
    }
  }

  async function deleteTeam() {
    if (!selectedTeam) return;

    const confirmed = window.confirm(
      `Delete "${selectedTeam.name}"?`
    );

    if (!confirmed) return;

    try {
      setError("");

      const response = await fetch(
        `${API_BASE_URL}/api/teams/${selectedTeam.id}`,
        {
          method: "DELETE",
          headers: authHeaders(),
        }
      );

      const data =
        response.status === 204
          ? null
          : await response.json();

      if (!response.ok) {
        throw new Error(
          data?.detail || "Failed to delete team."
        );
      }

      setTeams((current) =>
        current.filter(
          (team) => team.id !== selectedTeam.id
        )
      );

      setSelectedTeam(null);
      setMembers([]);
      setProjects([]);
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Failed to delete team."
      );
    }
  }

  return (
    <section className="feature-panel teams-panel">
      <div className="feature-panel-header">
        <div>
          <div className="section-kicker">
            // COLLABORATION
          </div>

          <h2>Teams</h2>

          <p>
            Build together, manage members and keep
            projects organized.
          </p>
        </div>

        <div className="feature-panel-badge">
          {teams.length}{" "}
          {teams.length === 1
            ? "TEAM"
            : "TEAMS"}
        </div>
      </div>

      {error && (
        <div className="feature-error">
          {error}
        </div>
      )}

      <div className="teams-layout">
        {/* ================================================= */}
        {/* TEAM LIST */}
        {/* ================================================= */}

        <div className="teams-sidebar">
          <div className="feature-card create-team-card">
            <div className="feature-card-label">
              NEW TEAM
            </div>

            <div className="inline-form">
              <input
                value={teamName}
                onChange={(event) =>
                  setTeamName(event.target.value)
                }
                placeholder="Team name..."
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    createTeam();
                  }
                }}
              />

              <button
                className="primary-feature-button"
                onClick={createTeam}
                disabled={loading}
              >
                {loading ? "Creating..." : "Create"}
              </button>
            </div>
          </div>

          <div className="feature-card team-list-card">
            <div className="feature-card-label">
              YOUR TEAMS
            </div>

            {loading && teams.length === 0 ? (
              <div className="feature-empty">
                Loading teams...
              </div>
            ) : teams.length === 0 ? (
              <div className="feature-empty">
                No teams yet.
              </div>
            ) : (
              <div className="team-list">
                {teams.map((team) => (
                  <button
                    key={team.id}
                    className={
                      selectedTeam?.id === team.id
                        ? "team-list-item active"
                        : "team-list-item"
                    }
                    onClick={() =>
                      selectTeam(team)
                    }
                  >
                    <span className="team-avatar">
                      {team.name
                        .charAt(0)
                        .toUpperCase()}
                    </span>

                    <span className="team-list-info">
                      <strong>{team.name}</strong>

                      <small>
                        Team #{team.id}
                      </small>
                    </span>

                    <span className="team-arrow">
                      →
                    </span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* ================================================= */}
        {/* TEAM DETAILS */}
        {/* ================================================= */}

        <div className="team-details">
          {!selectedTeam ? (
            <div className="feature-card team-placeholder">
              <div className="placeholder-icon">
                +
              </div>

              <h3>Select a team</h3>

              <p>
                Choose a team to manage members,
                projects and collaboration.
              </p>
            </div>
          ) : (
            <>
              <div className="feature-card team-hero-card">
                <div className="team-hero-main">
                  <div className="large-team-avatar">
                    {selectedTeam.name
                      .charAt(0)
                      .toUpperCase()}
                  </div>

                  <div>
                    <div className="feature-card-label">
                      TEAM #{selectedTeam.id}
                    </div>

                    <h3>
                      {selectedTeam.name}
                    </h3>

                    <p>
                      Created{" "}
                      {new Date(
                        selectedTeam.created_at
                      ).toLocaleDateString()}
                    </p>
                  </div>
                </div>

                <button
                  className="danger-feature-button"
                  onClick={deleteTeam}
                >
                  Delete Team
                </button>
              </div>

              {loadingDetails ? (
                <div className="feature-card feature-empty">
                  Loading team details...
                </div>
              ) : (
                <div className="team-detail-grid">
                  {/* MEMBERS */}

                  <div className="feature-card">
                    <div className="feature-card-top">
                      <div>
                        <div className="feature-card-label">
                          MEMBERS
                        </div>

                        <h3>
                          {members.length}
                        </h3>
                      </div>

                      <span className="feature-card-icon">
                        ◉
                      </span>
                    </div>

                    <div className="member-add-form">
                      <input
                        value={memberId}
                        onChange={(event) =>
                          setMemberId(
                            event.target.value
                          )
                        }
                        placeholder="User ID"
                        type="number"
                      />

                      <button
                        className="primary-feature-button"
                        onClick={addMember}
                      >
                        Add
                      </button>
                    </div>

                    <div className="member-list">
                      {members.length === 0 ? (
                        <div className="feature-empty">
                          No members yet.
                        </div>
                      ) : (
                        members.map(
                          (member) => (
                            <div
                              className="member-row"
                              key={member.id}
                            >
                              <div className="member-avatar">
                                {String(
                                  member.user_id
                                ).charAt(0)}
                              </div>

                              <div className="member-info">
                                <strong>
                                  User #
                                  {
                                    member.user_id
                                  }
                                </strong>

                                <span>
                                  {member.role}
                                </span>
                              </div>

                              <button
                                className="small-danger-button"
                                onClick={() =>
                                  removeMember(
                                    member.user_id
                                  )
                                }
                              >
                                ×
                              </button>
                            </div>
                          )
                        )
                      )}
                    </div>
                  </div>

                  {/* PROJECTS */}

                  <div className="feature-card">
                    <div className="feature-card-top">
                      <div>
                        <div className="feature-card-label">
                          PROJECTS
                        </div>

                        <h3>
                          {projects.length}
                        </h3>
                      </div>

                      <span className="feature-card-icon">
                        ◈
                      </span>
                    </div>

                    {projects.length === 0 ? (
                      <div className="feature-empty">
                        No projects assigned to
                        this team.
                      </div>
                    ) : (
                      <div className="team-project-list">
                        {projects.map(
                          (project) => (
                            <div
                              className="team-project-row"
                              key={project.id}
                            >
                              <div>
                                <strong>
                                  {project.name}
                                </strong>

                                <span>
                                  {project.description ||
                                    "No description"}
                                </span>
                              </div>

                              <span className="project-status">
                                {project.status ||
                                  "ACTIVE"}
                              </span>
                            </div>
                          )
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </section>
  );
}