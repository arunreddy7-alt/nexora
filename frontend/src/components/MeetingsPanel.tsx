import { useEffect, useState } from "react";

const API_BASE_URL = "http://127.0.0.1:8000";

type Team = {
  id: number;
  name: string;
};

type Meeting = {
  id: number;
  title: string;
  description: string | null;
  start_time: string;
  end_time: string;
  organizer_id: number;
  team_id: number | null;
  created_at: string;
};

type Participant = {
  id: number;
  meeting_id: number;
  user_id: number;
  status: string;
  joined_at: string | null;
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

export default function MeetingsPanel() {
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [participants, setParticipants] = useState<
    Participant[]
  >([]);

  const [selectedMeeting, setSelectedMeeting] =
    useState<Meeting | null>(null);

  const [title, setTitle] = useState("");
  const [description, setDescription] =
    useState("");

  const [startTime, setStartTime] =
    useState("");
  const [endTime, setEndTime] = useState("");

  const [teamId, setTeamId] = useState("");
  const [participantId, setParticipantId] =
    useState("");

  const [loading, setLoading] = useState(false);
  const [detailsLoading, setDetailsLoading] =
    useState(false);
  const [error, setError] = useState("");

  const currentUserId = getCurrentUserId();

  useEffect(() => {
    loadMeetings();
    loadTeams();
  }, []);

  function getCurrentUserId(): number | null {
    /*
     * The JWT contains the user ID in "sub".
     * We decode it only for UI purposes.
     * Backend authorization remains authoritative.
     */

    const token =
      localStorage.getItem("access_token");

    if (!token) {
      return null;
    }

    try {
      const payload = JSON.parse(
        atob(
          token.split(".")[1]
            .replace(/-/g, "+")
            .replace(/_/g, "/")
        )
      );

      return payload.sub
        ? Number(payload.sub)
        : null;
    } catch {
      return null;
    }
  }

  async function loadMeetings() {
    try {
      setLoading(true);
      setError("");

      const response = await fetch(
        `${API_BASE_URL}/api/meetings`,
        {
          headers: authHeaders(),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data?.detail ||
            "Failed to load meetings."
        );
      }

      setMeetings(data);
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Failed to load meetings."
      );
    } finally {
      setLoading(false);
    }
  }

  async function loadTeams() {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/teams`,
        {
          headers: authHeaders(),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data?.detail ||
            "Failed to load teams."
        );
      }

      setTeams(data);
    } catch {
      // Teams are optional for personal meetings.
    }
  }

  async function loadParticipants(
    meetingId: number
  ) {
    try {
      setDetailsLoading(true);
      setError("");

      const response = await fetch(
        `${API_BASE_URL}/api/meetings/${meetingId}/participants`,
        {
          headers: authHeaders(),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data?.detail ||
            "Failed to load participants."
        );
      }

      setParticipants(data);
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Failed to load participants."
      );
    } finally {
      setDetailsLoading(false);
    }
  }

  async function selectMeeting(
    meeting: Meeting
  ) {
    setSelectedMeeting(meeting);

    await loadParticipants(
      meeting.id
    );
  }

  async function createMeeting() {
    if (!title.trim()) {
      setError("Enter a meeting title.");
      return;
    }

    if (!startTime || !endTime) {
      setError(
        "Select both start and end times."
      );
      return;
    }

    const start = new Date(startTime);
    const end = new Date(endTime);

    if (end <= start) {
      setError(
        "End time must be after start time."
      );
      return;
    }

    try {
      setLoading(true);
      setError("");

      const response = await fetch(
        `${API_BASE_URL}/api/meetings`,
        {
          method: "POST",
          headers: authHeaders(),
          body: JSON.stringify({
            title: title.trim(),
            description:
              description.trim() || null,
            start_time: start.toISOString(),
            end_time: end.toISOString(),
            team_id: teamId
              ? Number(teamId)
              : null,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data?.detail ||
            "Failed to create meeting."
        );
      }

      setMeetings((current) => [
        ...current,
        data,
      ]);

      setSelectedMeeting(data);
      setParticipants([]);

      setTitle("");
      setDescription("");
      setStartTime("");
      setEndTime("");
      setTeamId("");
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Failed to create meeting."
      );
    } finally {
      setLoading(false);
    }
  }

  async function addParticipant() {
    if (!selectedMeeting) return;

    const userId = Number(participantId);

    if (!userId || userId <= 0) {
      setError("Enter a valid user ID.");
      return;
    }

    try {
      setError("");

      const response = await fetch(
        `${API_BASE_URL}/api/meetings/${selectedMeeting.id}/participants`,
        {
          method: "POST",
          headers: authHeaders(),
          body: JSON.stringify({
            user_id: userId,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data?.detail ||
            "Failed to add participant."
        );
      }

      setParticipants((current) => [
        ...current,
        data,
      ]);

      setParticipantId("");
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Failed to add participant."
      );
    }
  }

  async function updateMyStatus(
    status: string
  ) {
    if (!selectedMeeting) return;

    try {
      setError("");

      const response = await fetch(
        `${API_BASE_URL}/api/meetings/${selectedMeeting.id}/participants/me`,
        {
          method: "PUT",
          headers: authHeaders(),
          body: JSON.stringify({
            status,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data?.detail ||
            "Failed to update meeting status."
        );
      }

      setParticipants((current) =>
        current.map((participant) =>
          participant.user_id ===
          currentUserId
            ? data
            : participant
        )
      );
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Failed to update status."
      );
    }
  }

  async function removeParticipant(
    userId: number
  ) {
    if (!selectedMeeting) return;

    try {
      setError("");

      const response = await fetch(
        `${API_BASE_URL}/api/meetings/${selectedMeeting.id}/participants/${userId}`,
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
            "Failed to remove participant."
        );
      }

      setParticipants((current) =>
        current.filter(
          (participant) =>
            participant.user_id !== userId
        )
      );
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Failed to remove participant."
      );
    }
  }

  async function deleteMeeting() {
    if (!selectedMeeting) return;

    const confirmed = window.confirm(
      `Delete "${selectedMeeting.title}"?`
    );

    if (!confirmed) return;

    try {
      setError("");

      const response = await fetch(
        `${API_BASE_URL}/api/meetings/${selectedMeeting.id}`,
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
            "Failed to delete meeting."
        );
      }

      setMeetings((current) =>
        current.filter(
          (meeting) =>
            meeting.id !==
            selectedMeeting.id
        )
      );

      setSelectedMeeting(null);
      setParticipants([]);
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Failed to delete meeting."
      );
    }
  }

  function formatDate(
    value: string
  ) {
    return new Date(value).toLocaleDateString(
      undefined,
      {
        weekday: "short",
        month: "short",
        day: "numeric",
      }
    );
  }

  function formatTime(
    value: string
  ) {
    return new Date(value).toLocaleTimeString(
      undefined,
      {
        hour: "numeric",
        minute: "2-digit",
      }
    );
  }

  function isUpcoming(
    meeting: Meeting
  ) {
    return (
      new Date(meeting.start_time) >
      new Date()
    );
  }

  return (
    <section className="feature-panel meetings-panel">
      <div className="feature-panel-header">
        <div>
          <div className="section-kicker">
            // COLLABORATION
          </div>

          <h2>Meetings</h2>

          <p>
            Schedule meetings, invite teammates
            and keep everyone aligned.
          </p>
        </div>

        <div className="feature-panel-badge">
          {meetings.length}{" "}
          {meetings.length === 1
            ? "MEETING"
            : "MEETINGS"}
        </div>
      </div>

      {error && (
        <div className="feature-error">
          {error}
        </div>
      )}

      <div className="meetings-layout">
        {/* ================================================= */}
        {/* CREATE MEETING */}
        {/* ================================================= */}

        <div className="feature-card create-meeting-card">
          <div className="feature-card-label">
            NEW MEETING
          </div>

          <input
            value={title}
            onChange={(event) =>
              setTitle(event.target.value)
            }
            placeholder="Meeting title..."
          />

          <textarea
            value={description}
            onChange={(event) =>
              setDescription(
                event.target.value
              )
            }
            placeholder="Description..."
            rows={3}
          />

          <div className="meeting-time-grid">
            <div>
              <label>START</label>

              <input
                type="datetime-local"
                value={startTime}
                onChange={(event) =>
                  setStartTime(
                    event.target.value
                  )
                }
              />
            </div>

            <div>
              <label>END</label>

              <input
                type="datetime-local"
                value={endTime}
                onChange={(event) =>
                  setEndTime(
                    event.target.value
                  )
                }
              />
            </div>
          </div>

          <div>
            <label>TEAM</label>

            <select
              value={teamId}
              onChange={(event) =>
                setTeamId(
                  event.target.value
                )
              }
            >
              <option value="">
                Personal meeting
              </option>

              {teams.map((team) => (
                <option
                  key={team.id}
                  value={team.id}
                >
                  {team.name}
                </option>
              ))}
            </select>
          </div>

          <button
            className="primary-feature-button full-feature-button"
            onClick={createMeeting}
            disabled={loading}
          >
            {loading
              ? "Creating..."
              : "Create Meeting →"}
          </button>
        </div>

        {/* ================================================= */}
        {/* MEETING LIST */}
        {/* ================================================= */}

        <div className="feature-card meeting-list-card">
          <div className="feature-card-label">
            YOUR SCHEDULE
          </div>

          {loading && meetings.length === 0 ? (
            <div className="feature-empty">
              Loading meetings...
            </div>
          ) : meetings.length === 0 ? (
            <div className="feature-empty">
              No meetings scheduled.
            </div>
          ) : (
            <div className="meeting-list">
              {meetings.map((meeting) => (
                <button
                  key={meeting.id}
                  className={
                    selectedMeeting?.id ===
                    meeting.id
                      ? "meeting-list-item active"
                      : "meeting-list-item"
                  }
                  onClick={() =>
                    selectMeeting(
                      meeting
                    )
                  }
                >
                  <div className="meeting-date-block">
                    <strong>
                      {new Date(
                        meeting.start_time
                      ).getDate()}
                    </strong>

                    <span>
                      {new Date(
                        meeting.start_time
                      ).toLocaleDateString(
                        undefined,
                        {
                          month: "short",
                        }
                      )}
                    </span>
                  </div>

                  <div className="meeting-list-info">
                    <strong>
                      {meeting.title}
                    </strong>

                    <span>
                      {formatTime(
                        meeting.start_time
                      )}{" "}
                      —{" "}
                      {formatTime(
                        meeting.end_time
                      )}
                    </span>

                    <small>
                      {meeting.team_id
                        ? `Team #${meeting.team_id}`
                        : "Personal"}
                    </small>
                  </div>

                  <span
                    className={
                      isUpcoming(meeting)
                        ? "meeting-status upcoming"
                        : "meeting-status past"
                    }
                  >
                    {isUpcoming(meeting)
                      ? "UPCOMING"
                      : "PAST"}
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* =================================================== */}
      {/* MEETING DETAILS */}
      {/* =================================================== */}

      {selectedMeeting && (
        <div className="meeting-details feature-card">
          <div className="meeting-details-header">
            <div>
              <div className="feature-card-label">
                {selectedMeeting.team_id
                  ? `TEAM MEETING · TEAM #${selectedMeeting.team_id}`
                  : "PERSONAL MEETING"}
              </div>

              <h3>
                {selectedMeeting.title}
              </h3>

              <p>
                {selectedMeeting.description ||
                  "No description provided."}
              </p>
            </div>

            <button
              className="danger-feature-button"
              onClick={deleteMeeting}
            >
              Delete
            </button>
          </div>

          <div className="meeting-info-strip">
            <div>
              <span>DATE</span>
              <strong>
                {formatDate(
                  selectedMeeting.start_time
                )}
              </strong>
            </div>

            <div>
              <span>TIME</span>
              <strong>
                {formatTime(
                  selectedMeeting.start_time
                )}{" "}
                —{" "}
                {formatTime(
                  selectedMeeting.end_time
                )}
              </strong>
            </div>

            <div>
              <span>ORGANIZER</span>
              <strong>
                User #
                {
                  selectedMeeting.organizer_id
                }
              </strong>
            </div>
          </div>

          <div className="meeting-participant-section">
            <div className="feature-card-top">
              <div>
                <div className="feature-card-label">
                  PARTICIPANTS
                </div>

                <h3>
                  {participants.length}
                </h3>
              </div>
            </div>

            {selectedMeeting.organizer_id ===
              currentUserId && (
              <div className="member-add-form">
                <input
                  value={participantId}
                  onChange={(event) =>
                    setParticipantId(
                      event.target.value
                    )
                  }
                  type="number"
                  placeholder="User ID"
                />

                <button
                  className="primary-feature-button"
                  onClick={
                    addParticipant
                  }
                >
                  Invite
                </button>
              </div>
            )}

            {detailsLoading ? (
              <div className="feature-empty">
                Loading participants...
              </div>
            ) : participants.length === 0 ? (
              <div className="feature-empty">
                No participants yet.
              </div>
            ) : (
              <div className="member-list">
                {participants.map(
                  (participant) => (
                    <div
                      className="member-row"
                      key={participant.id}
                    >
                      <div className="member-avatar">
                        {String(
                          participant.user_id
                        ).charAt(0)}
                      </div>

                      <div className="member-info">
                        <strong>
                          User #
                          {
                            participant.user_id
                          }
                        </strong>

                        <span>
                          {participant.status}
                        </span>
                      </div>

                      <div className="participant-actions">
                        {participant.user_id ===
                          currentUserId && (
                          <>
                            <button
                              className="status-button"
                              onClick={() =>
                                updateMyStatus(
                                  "accepted"
                                )
                              }
                            >
                              Accept
                            </button>

                            <button
                              className="status-button"
                              onClick={() =>
                                updateMyStatus(
                                  "declined"
                                )
                              }
                            >
                              Decline
                            </button>

                            <button
                              className="status-button"
                              onClick={() =>
                                updateMyStatus(
                                  "joined"
                                )
                              }
                            >
                              Join
                            </button>
                          </>
                        )}

                        {selectedMeeting.organizer_id ===
                          currentUserId &&
                          participant.user_id !==
                            currentUserId && (
                            <button
                              className="small-danger-button"
                              onClick={() =>
                                removeParticipant(
                                  participant.user_id
                                )
                              }
                            >
                              ×
                            </button>
                          )}
                      </div>
                    </div>
                  )
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </section>
  );
}