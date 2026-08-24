from pathlib import Path
import json
import socket
import subprocess
import time
from typing import Any


PREVIEW_PROCESSES: dict[int, subprocess.Popen] = {}

PREVIEW_INFO: dict[int, dict[str, Any]] = {}


# ============================================================
# WORKSPACE
# ============================================================

def get_workspace(
    project_id: int,
) -> Path:

    workspace = (
        Path(__file__).resolve().parents[3]
        / "workspaces"
        / f"project_{project_id}"
    )

    if not workspace.exists():
        raise FileNotFoundError(
            f"Workspace does not exist: {workspace}"
        )

    return workspace.resolve()


# ============================================================
# PACKAGE.JSON
# ============================================================

def find_package_json(
    workspace: Path,
) -> Path:

    root_package = (
        workspace / "package.json"
    )

    if root_package.exists():
        return root_package

    frontend_package = (
        workspace
        / "frontend"
        / "package.json"
    )

    if frontend_package.exists():
        return frontend_package

    raise FileNotFoundError(
        "No package.json found in project workspace."
    )


# ============================================================
# PORT
# ============================================================

def get_free_port() -> int:

    with socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM,
    ) as sock:

        sock.bind(
            ("127.0.0.1", 0)
        )

        return sock.getsockname()[1]


def is_port_open(
    host: str,
    port: int,
) -> bool:

    try:

        with socket.create_connection(
            (host, port),
            timeout=0.5,
        ):
            return True

    except (
        OSError,
        ConnectionRefusedError,
        TimeoutError,
    ):
        return False


# ============================================================
# PREVIEW COMMAND
# ============================================================

def detect_preview_command(
    package_json: Path,
    port: int,
) -> list[str]:

    data = json.loads(
        package_json.read_text(
            encoding="utf-8"
        )
    )

    scripts = data.get(
        "scripts",
        {},
    )

    if not isinstance(
        scripts,
        dict,
    ):
        raise ValueError(
            "package.json scripts must be an object."
        )

    if "dev" not in scripts:
        raise ValueError(
            "Generated project does not have "
            "a 'dev' script."
        )

    package_text = json.dumps(
        data
    ).lower()

    # --------------------------------------------------------
    # VITE
    # --------------------------------------------------------

    if "vite" in package_text:

        return [
            "npm.cmd",
            "run",
            "dev",
            "--",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ]

    # --------------------------------------------------------
    # NEXT.JS
    # --------------------------------------------------------

    if "next" in package_text:

        return [
            "npm.cmd",
            "run",
            "dev",
            "--",
            "--hostname",
            "127.0.0.1",
            "--port",
            str(port),
        ]

    # --------------------------------------------------------
    # GENERIC
    # --------------------------------------------------------

    return [
        "npm.cmd",
        "run",
        "dev",
        "--",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
    ]


# ============================================================
# STOP PREVIEW
# ============================================================

def stop_project_preview(
    project_id: int,
) -> None:

    process = PREVIEW_PROCESSES.get(
        project_id
    )

    if process is not None:

        if process.poll() is None:

            try:

                process.terminate()

                process.wait(
                    timeout=5
                )

            except subprocess.TimeoutExpired:

                try:
                    process.kill()
                except Exception:
                    pass

        PREVIEW_PROCESSES.pop(
            project_id,
            None,
        )

    PREVIEW_INFO.pop(
        project_id,
        None,
    )


# ============================================================
# READ PROCESS OUTPUT
# ============================================================

def read_process_output(
    process: subprocess.Popen,
) -> str:

    if process.stdout is None:
        return ""

    try:

        output = process.stdout.read()

        if output:
            return output

    except Exception:
        pass

    return ""


# ============================================================
# START PREVIEW
# ============================================================

def start_project_preview(
    project_id: int,
) -> dict[str, Any]:

    workspace = get_workspace(
        project_id
    )

    package_json = find_package_json(
        workspace
    )

    project_directory = (
        package_json.parent
    )

    port = get_free_port()

    command = detect_preview_command(
        package_json=package_json,
        port=port,
    )

    # --------------------------------------------------------
    # Stop old preview
    # --------------------------------------------------------

    stop_project_preview(
        project_id
    )

    # --------------------------------------------------------
    # Start process
    # --------------------------------------------------------

    process = subprocess.Popen(
        command,
        cwd=project_directory,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        shell=True,
    )

    PREVIEW_PROCESSES[
        project_id
    ] = process

    url = (
        f"http://127.0.0.1:{port}"
    )

    preview_info = {
        "project_id": project_id,
        "status": "STARTING",
        "url": url,
        "port": port,
        "directory": str(
            project_directory
        ),
        "command": " ".join(
            command
        ),
    }

    PREVIEW_INFO[
        project_id
    ] = preview_info

    # --------------------------------------------------------
    # Wait for the server to actually listen.
    #
    # Maximum wait:
    # 30 seconds
    #
    # We do NOT simply sleep for 2 seconds.
    # --------------------------------------------------------

    timeout_seconds = 30

    start_time = time.time()

    while (
        time.time() - start_time
        < timeout_seconds
    ):

        # Process already died.
        if process.poll() is not None:

            output = (
                read_process_output(
                    process
                )
            )

            PREVIEW_PROCESSES.pop(
                project_id,
                None,
            )

            PREVIEW_INFO.pop(
                project_id,
                None,
            )

            raise RuntimeError(
                "Preview server failed to start.\n"
                + output[-4000:]
            )

        # Actual readiness check.
        if is_port_open(
            "127.0.0.1",
            port,
        ):

            preview_info[
                "status"
            ] = "RUNNING"

            PREVIEW_INFO[
                project_id
            ] = preview_info

            return preview_info

        time.sleep(0.5)

    # --------------------------------------------------------
    # Server process still exists but never opened the port.
    # --------------------------------------------------------

    output = ""

    try:

        if process.stdout:

            output = (
                process.stdout.read(
                    4000
                )
            )

    except Exception:
        pass

    stop_project_preview(
        project_id
    )

    raise RuntimeError(
        "Preview server did not become ready "
        f"within {timeout_seconds} seconds.\n"
        + output[-4000:]
    )


# ============================================================
# GET PREVIEW
# ============================================================

def get_project_preview(
    project_id: int,
) -> dict[str, Any]:

    process = PREVIEW_PROCESSES.get(
        project_id
    )

    preview_info = PREVIEW_INFO.get(
        project_id
    )

    # --------------------------------------------------------
    # No process
    # --------------------------------------------------------

    if process is None:

        if preview_info:

            return preview_info

        return {
            "project_id": project_id,
            "status": "STOPPED",
            "url": None,
            "port": None,
        }

    # --------------------------------------------------------
    # Process died
    # --------------------------------------------------------

    if process.poll() is not None:

        output = ""

        try:

            if process.stdout:

                output = (
                    process.stdout.read()
                )

        except Exception:
            pass

        PREVIEW_PROCESSES.pop(
            project_id,
            None,
        )

        if preview_info:

            preview_info = {
                **preview_info,
                "status": "STOPPED",
                "error": output[-4000:],
            }

            PREVIEW_INFO[
                project_id
            ] = preview_info

            return preview_info

        return {
            "project_id": project_id,
            "status": "STOPPED",
            "url": None,
            "port": None,
        }

    # --------------------------------------------------------
    # Running
    # --------------------------------------------------------

    if preview_info:

        preview_info[
            "status"
        ] = "RUNNING"

        return preview_info

    return {
        "project_id": project_id,
        "status": "RUNNING",
        "url": None,
        "port": None,
    }