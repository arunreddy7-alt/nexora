const API_BASE_URL = "http://127.0.0.1:8000";

function getAuthHeaders(): HeadersInit {
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

export interface Project {
  id: number;
  owner_id: number;
  name: string;
  description: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface PipelineRunResponse {
  pipeline_run: {
    id: number;
    project_id: number;
    status: string;
    current_agent: string | null;
    started_at: string | null;
    completed_at: string | null;
  };

  ceo: any;
  pm: any;
  architect: any;
  developer: any;

  workspace?: any;

  execution?: {
    tests?: any;
    build?: any;
  };
}

export async function getProjects(): Promise<Project[]> {
  const response = await fetch(
    `${API_BASE_URL}/api/projects`,
    {
      method: "GET",
      headers: getAuthHeaders(),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data?.detail || "Failed to fetch projects"
    );
  }

  return data;
}

export async function createProject(
  name: string,
  description: string
): Promise<Project> {
  const response = await fetch(
    `${API_BASE_URL}/api/projects`,
    {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        name,
        description,
      }),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data?.detail || "Failed to create project"
    );
  }

  return data;
}

export async function runAgentPipeline(
  projectId: number,
  projectDescription: string
): Promise<PipelineRunResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/projects/${projectId}/agent-outputs/run-pipeline?project_description=${encodeURIComponent(
      projectDescription
    )}`,
    {
      method: "POST",
      headers: getAuthHeaders(),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data?.detail || "Failed to run agent pipeline"
    );
  }

  return data;
}