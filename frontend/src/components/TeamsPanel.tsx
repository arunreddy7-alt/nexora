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
  status?: string;
};

function authHeaders(): HeadersInit {
  const token =
    localStorage.getItem("access_token");

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
  const [teams, setTeams] =
    useState<Team[]>([]);

  const [selectedTeam, setSelectedTeam] =
    useState<Team | null>(null);

  const [members, setMembers] =
    useState<TeamMember[]>([]);

  const [projects, setProjects] =
    useState<TeamProject[]>([]);

  const [teamName, setTeamName] =
    useState("");

  const [memberId, setMemberId] =
    useState("");

  const [loading, setLoading] =
    useState(false);

  const [loadingDetails, setLoadingDetails] =
    useState(false);

  const [error, setError] =
    useState("");

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

      const data =
        await response.json();

      if (!response.ok) {
        throw new Error(
          data?.detail ||
            "Failed to load teams."
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

      const data =
        await response.json();

      if (!response.ok) {
        throw new Error(
          data?.detail ||
            "Failed to create team."
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

  async function loadTeamDetails(
    teamId: number
  ) {
    try {
      setLoadingDetails(true);
      setError("");

      const [
        membersResponse,
        projectsResponse,
      ] = await Promise.all([
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

      const membersData =
        await membersResponse.json();

      const projectsData =
        await projectsResponse.json();

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

  async function selectTeam(
    team: Team
  ) {
    setSelectedTeam(team);
    await loadTeamDetails(team.id);
  }

  async function addMember() {
    if (!selectedTeam) return;

    const parsedUserId =
      Number(memberId);

    if (
      !parsedUserId ||
      parsedUserId <= 0
    ) {
      setError(
        "Enter a valid user ID."
      );
      return;
    }

    try {
      setError("");

      const response =
        await fetch(
          `${API_BASE_URL}/api/teams/${selectedTeam.id}/members`,
          {
            method: "POST",
            headers: authHeaders(),

            body: JSON.stringify({
              user_id: parsedUserId,
            }),
          }
        );

      const data =
        await response.json();

      if (!response.ok) {
        throw new Error(
          data?.detail ||
            "Failed to add member."
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

  async function removeMember(
    userId: number
  ) {
    if (!selectedTeam) return;

    try {
      setError("");

      const response =
        await fetch(
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
          data?.detail ||
            "Failed to remove member."
        );
      }

      setMembers((current) =>
        current.filter(
          (member) =>
            member.user_id !== userId
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

    const confirmed =
      window.confirm(
        `Delete "${selectedTeam.name}"?`
      );

    if (!confirmed) return;

    try {
      setError("");

      const response =
        await fetch(
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
          data?.detail ||
            "Failed to delete team."
        );
      }

      setTeams((current) =>
        current.filter(
          (team) =>
            team.id !==
            selectedTeam.id
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

      <div className="teams-page-header">

        <div>
          <div className="teams-eyebrow">
            COLLABORATION
          </div>

          <h1>
            Work together.
          </h1>

          <p>
            Create teams, invite members and
            organize projects in one place.
          </p>
        </div>

        <div className="teams-summary">
          <span className="teams-summary-number">
            {teams.length}
          </span>

          <span className="teams-summary-label">
            {teams.length === 1
              ? "TEAM"
              : "TEAMS"}
          </span>
        </div>

      </div>


      {error && (
        <div className="teams-error">
          {error}
        </div>
      )}


      <div className="teams-layout">

        <aside className="teams-sidebar">

          <div className="teams-create-card">

            <div className="teams-card-eyebrow">
              CREATE TEAM
            </div>

            <h3>
              Start collaborating
            </h3>

            <p>
              Give your workspace a name
              and bring your team together.
            </p>

            <input
              value={teamName}
              onChange={(event) =>
                setTeamName(
                  event.target.value
                )
              }
              onKeyDown={(event) => {
                if (
                  event.key === "Enter"
                ) {
                  createTeam();
                }
              }}
              placeholder="e.g. Product Team"
            />

            <button
              className="teams-primary-button"
              onClick={createTeam}
              disabled={loading}
            >
              {loading
                ? "Creating..."
                : "Create team →"}
            </button>

          </div>


          <div className="teams-list-card">

            <div className="teams-list-header">
              <span>
                YOUR TEAMS
              </span>

              <span>
                {teams.length}
              </span>
            </div>

            {loading &&
            teams.length === 0 ? (
              <div className="teams-empty">
                Loading teams...
              </div>
            ) : teams.length === 0 ? (
              <div className="teams-empty">
                <div className="teams-empty-icon">
                  +
                </div>

                <strong>
                  No teams yet
                </strong>

                <span>
                  Create your first team
                  above.
                </span>
              </div>
            ) : (
              <div className="teams-list">

                {teams.map((team) => (
                  <button
                    key={team.id}
                    className={
                      selectedTeam?.id ===
                      team.id
                        ? "team-item active"
                        : "team-item"
                    }
                    onClick={() =>
                      selectTeam(team)
                    }
                  >

                    <span className="team-item-avatar">
                      {team.name
                        .charAt(0)
                        .toUpperCase()}
                    </span>

                    <span className="team-item-content">

                      <strong>
                        {team.name}
                      </strong>

                      <small>
                        Team #{team.id}
                      </small>

                    </span>

                    <span className="team-item-arrow">
                      →
                    </span>

                  </button>
                ))}

              </div>
            )}

          </div>

        </aside>


        <div className="teams-content">

          {!selectedTeam ? (

            <div className="teams-welcome">

              <div className="teams-welcome-symbol">
                <span />
                <span />
                <span />
              </div>

              <div className="teams-eyebrow">
                TEAM WORKSPACE
              </div>

              <h2>
                Select a team
                <br />
                <span>to get started.</span>
              </h2>

              <p>
                Choose a team from the left
                to manage members, projects
                and collaboration.
              </p>

            </div>

          ) : (

            <>

              <div className="team-detail-header">

                <div className="team-detail-identity">

                  <div className="team-large-avatar">
                    {selectedTeam.name
                      .charAt(0)
                      .toUpperCase()}
                  </div>

                  <div>

                    <div className="teams-card-eyebrow">
                      TEAM #{selectedTeam.id}
                    </div>

                    <h2>
                      {selectedTeam.name}
                    </h2>

                    <p>
                      Created{" "}
                      {new Date(
                        selectedTeam.created_at
                      ).toLocaleDateString()}
                    </p>

                  </div>

                </div>

                <button
                  className="teams-delete-button"
                  onClick={deleteTeam}
                >
                  Delete team
                </button>

              </div>


              {loadingDetails ? (

                <div className="teams-loading">
                  Loading team workspace...
                </div>

              ) : (

                <div className="team-detail-grid">

                  <div className="team-detail-card">

                    <div className="team-stat-header">

                      <div>
                        <span>
                          MEMBERS
                        </span>

                        <strong>
                          {members.length}
                        </strong>
                      </div>

                      <div className="team-stat-icon">
                        ◉
                      </div>

                    </div>


                    <div className="member-add">

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
                        className="teams-primary-button"
                        onClick={addMember}
                      >
                        Add
                      </button>

                    </div>


                    <div className="member-list">

                      {members.length === 0 ? (

                        <div className="teams-small-empty">
                          No members yet.
                        </div>

                      ) : (

                        members.map(
                          (member) => (
                            <div
                              className="member-item"
                              key={member.id}
                            >

                              <div className="member-avatar">
                                {String(
                                  member.user_id
                                ).charAt(0)}
                              </div>

                              <div className="member-details">

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
                                className="member-remove"
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


                  <div className="team-detail-card">

                    <div className="team-stat-header">

                      <div>
                        <span>
                          PROJECTS
                        </span>

                        <strong>
                          {projects.length}
                        </strong>
                      </div>

                      <div className="team-stat-icon">
                        ◈
                      </div>

                    </div>


                    {projects.length === 0 ? (

                      <div className="projects-empty">

                        <div className="projects-empty-icon">
                          ◈
                        </div>

                        <strong>
                          No projects yet
                        </strong>

                        <span>
                          Projects assigned to
                          this team will appear
                          here.
                        </span>

                      </div>

                    ) : (

                      <div className="team-projects">

                        {projects.map(
                          (project) => (
                            <div
                              className="team-project"
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

                              <span className="project-pill">
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