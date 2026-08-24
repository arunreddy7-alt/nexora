type DownloadProjectButtonProps = {
  projectId: number;
  className?: string;
  label?: string;
};

const API_BASE_URL = "http://127.0.0.1:8000";

export default function DownloadProjectButton({
  projectId,
  className = "",
  label = "Download Project",
}: DownloadProjectButtonProps) {
  async function downloadProject() {
    const token =
      localStorage.getItem(
        "access_token"
      );

    try {
      const response =
        await fetch(
          `${API_BASE_URL}/api/projects/${projectId}/download`,
          {
            method: "GET",

            headers: {
              ...(token
                ? {
                    Authorization: `Bearer ${token}`,
                  }
                : {}),
            },
          }
        );

      if (!response.ok) {
        let message =
          "Failed to download project.";

        try {
          const data =
            await response.json();

          message =
            data?.detail ||
            message;
        } catch {
          // Backend did not return JSON.
        }

        throw new Error(
          message
        );
      }

      const blob =
        await response.blob();

      const url =
        window.URL.createObjectURL(
          blob
        );

      const link =
        document.createElement(
          "a"
        );

      link.href = url;

      const disposition =
        response.headers.get(
          "Content-Disposition"
        );

      let filename =
        `project-${projectId}.zip`;

      if (disposition) {
        const match =
          disposition.match(
            /filename\*?=(?:UTF-8''|")?([^";]+)"?/i
          );

        if (match?.[1]) {
          try {
            filename =
              decodeURIComponent(
                match[1]
              );
          } catch {
            filename =
              match[1];
          }
        }
      }

      link.download =
        filename;

      document.body.appendChild(
        link
      );

      link.click();

      link.remove();

      window.setTimeout(() => {
        window.URL.revokeObjectURL(
          url
        );
      }, 1000);
    } catch (error) {
      console.error(
        "Project download failed:",
        error
      );

      alert(
        error instanceof Error
          ? error.message
          : "Failed to download project."
      );
    }
  }

  return (
    <button
      type="button"
      className={`download-project-button ${className}`}
      onClick={
        downloadProject
      }
    >
      <span className="download-project-icon">
        ↓
      </span>

      <span>
        {label}
      </span>
    </button>
  );
}