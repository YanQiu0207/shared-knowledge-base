from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path


def read_llm_config(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip().lower()] = value.strip()
    required = ("baseurl", "api-key", "model")
    missing = [key for key in required if not values.get(key)]
    if missing:
        raise ValueError(f"missing configuration fields: {', '.join(missing)}")
    return values


def wait_for_health(url: str, timeout_seconds: int) -> dict[str, object]:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                return json.loads(response.read().decode("utf-8"))
        except OSError:
            time.sleep(1)
    raise TimeoutError(f"Gateway did not become healthy: {url}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--llm-config", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, default=Path.home() / ".memory-tencentdb" / "memory-tdai")
    args = parser.parse_args()

    source = args.source.resolve()
    config = source / "tdai-gateway.standalone.yaml"
    server = source / "src" / "gateway" / "server.ts"
    if not config.is_file() or not server.is_file():
        raise FileNotFoundError("source does not contain the standalone Gateway files")

    llm = read_llm_config(args.llm_config.resolve())
    log_dir = args.data_dir.resolve() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    environment.update({
        "TDAI_GATEWAY_CONFIG": str(config),
        "TDAI_GATEWAY_HOST": "127.0.0.1",
        "TDAI_GATEWAY_PORT": "8420",
        "TDAI_DATA_DIR": str(args.data_dir.resolve()),
        "TDAI_LLM_BASE_URL": llm["baseurl"],
        "TDAI_LLM_API_KEY": llm["api-key"],
        "TDAI_LLM_MODEL": llm["model"],
        "PYTHONUTF8": "1",
        "PYTHONIOENCODING": "utf-8",
    })
    creation_flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) | getattr(subprocess, "DETACHED_PROCESS", 0)
    with (log_dir / "gateway.stdout.log").open("ab") as stdout, (log_dir / "gateway.stderr.log").open("ab") as stderr:
        process = subprocess.Popen(
            ["node", "--import", "tsx/esm", "src/gateway/server.ts"],
            cwd=source,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=stdout,
            stderr=stderr,
            creationflags=creation_flags,
        )
    (log_dir / "gateway.pid").write_text(str(process.pid), encoding="ascii")
    health = wait_for_health("http://127.0.0.1:8420/health", 20)
    print(json.dumps({"pid": process.pid, "status": health.get("status")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
