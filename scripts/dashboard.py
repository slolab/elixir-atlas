import argparse
import os
import signal
import socket
import subprocess
import time
from contextlib import suppress
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen


def interrupted(signum, frame):
    raise KeyboardInterrupt


def main():
    root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Launch the dashboard over a local SQLite snapshot.")
    parser.add_argument("snapshot", nargs="?", type=Path, default=root / "graph/build/graph.sqlite")
    parser.add_argument("--port", type=int, default=5180)
    args = parser.parse_args()
    snapshot = args.snapshot.resolve()
    if not snapshot.is_file():
        parser.error(f"Snapshot missing: {snapshot}. Build the graph or supply the path to graph.sqlite.")
    processes = []
    signal.signal(signal.SIGTERM, interrupted)
    try:
        if not (root / "dashboard/node_modules/.bin/vite").exists():
            subprocess.run(["npm", "ci"], cwd=root / "dashboard", check=True)
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            api_port = listener.getsockname()[1]
        api_url = f"http://127.0.0.1:{api_port}"
        environment = {**os.environ, "ATLAS_SQLITE_PATH": str(snapshot), "ATLAS_API_URL": api_url}
        environment.pop("DATABASE_URL", None)
        print(f"Opening local snapshot: {snapshot}", flush=True)
        api = subprocess.Popen(["uv", "run", "--directory", str(root / "server"), "uvicorn", "atlas_api.main:app", "--host", "127.0.0.1", "--port", str(api_port)], env=environment, start_new_session=True)
        processes.append(api)
        deadline = time.monotonic() + 90
        while True:
            if api.poll() is not None:
                raise RuntimeError("The local API could not start; see its error above.")
            try:
                with urlopen(api_url + "/healthz", timeout=1):
                    break
            except (URLError, TimeoutError):
                if time.monotonic() > deadline:
                    raise RuntimeError("The local API did not become ready within 90 seconds.")
                time.sleep(0.2)
        frontend = subprocess.Popen(["npm", "run", "dev:api", "--", "--host", "127.0.0.1", "--port", str(args.port), "--strictPort"], cwd=root / "dashboard", env=environment, start_new_session=True)
        processes.append(frontend)
        print(f"Local dashboard: http://127.0.0.1:{args.port} — Ctrl+C stops both processes. Restart after rebuilding the snapshot.", flush=True)
        while all(process.poll() is None for process in processes):
            time.sleep(0.2)
        raise SystemExit(next(process.returncode for process in processes if process.returncode is not None))
    except KeyboardInterrupt:
        return
    finally:
        for process in reversed(processes):
            with suppress(ProcessLookupError):
                os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                with suppress(ProcessLookupError):
                    os.killpg(process.pid, signal.SIGKILL)
                process.wait()


if __name__ == "__main__":
    main()
