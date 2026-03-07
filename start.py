import json
import signal
import os
import time
import threading
import subprocess
import urllib.request
import urllib.error

from rich.live import Live
from rich.table import Table
from rich.text import Text


ROOT = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(ROOT, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

HEALTH_INTERVAL = 1.0
START_TIME = time.time()

SERVICES = [
    {
        "port": 3003,
        "name": "embedder",
        "project": os.path.join(ROOT, "packages", "embedder"),
        "app_dir": os.path.join(ROOT, "packages", "embedder", "src"),
        "app": "main:app",
        "health_url": "http://localhost:3003/status",
    },
    {
        "port": 3002,
        "name": "knowledge_base",
        "project": os.path.join(ROOT, "packages", "knowledge_base"),
        "app_dir": os.path.join(ROOT, "packages", "knowledge_base", "src"),
        "app": "main:app",
        "wait_for": "embedder",
        "health_url": "http://localhost:3002/status",
    }
]

DOCKER_SERVICES = [
    {"name": "Qdrant", "port": 6333, "url": "http://localhost:6333/dashboard", "health_url": "http://localhost:6333/healthz"},
    {"name": "Chatbot", "port": 3001, "url": "http://localhost:3001", "health_url": "http://localhost:3001"},
]


def _resolve_health_url(service_name: str) -> str:
    for svc in SERVICES:
        if svc["name"] == service_name:
            return svc["health_url"]
    raise ValueError(f"Unknown service: {service_name}")


def wait_for_service(dependency: str, name: str, statuses: dict, stop_event: threading.Event, interval: int = 2):
    url = _resolve_health_url(dependency)
    statuses[name] = f"Waiting [{dependency.capitalize()}]"
    while not stop_event.is_set():
        try:
            resp = urllib.request.urlopen(url, timeout=5)
            if resp.status == 200:
                return
        except (urllib.error.URLError, OSError):
            pass
        time.sleep(interval)


def run_service(service: dict, statuses: dict, processes: dict[str, subprocess.Popen], stop_event: threading.Event):
    log_file = open(os.path.join(LOGS_DIR, f"{service['name']}.log"), "w")
    dependencies = service.get("wait_for", [])
    if isinstance(dependencies, str):
        dependencies = [dependencies]
    for dependency in dependencies:
        if stop_event.is_set():
            statuses[service["name"]] = "Stopped"
            return
        wait_for_service(dependency, service["name"], statuses, stop_event)

    for key, value in service.get("env", {}).items():
        os.environ[key] = value

    statuses[service["name"]] = "Starting..."
    env = os.environ.copy()
    env.update(service.get("env", {}))
    cmd = [
        "uv",
        "run",
        "--project",
        service["project"],
        "python",
        "-m",
        "uvicorn",
        service["app"],
        "--app-dir",
        service["app_dir"],
        "--host",
        "0.0.0.0",
        "--port",
        str(service["port"]),
        "--log-level",
        "info",
    ]
    process = subprocess.Popen(
        cmd,
        cwd=service["project"],
        stdout=log_file,
        stderr=subprocess.STDOUT,
        env=env,
        text=True,
    )
    processes[service["name"]] = process
    code = process.wait()
    if stop_event.is_set():
        statuses[service["name"]] = "Stopped"
    else:
        statuses[service["name"]] = f"Exited ({code})"


def check_health(url: str) -> str | None:
    try:
        resp = urllib.request.urlopen(url, timeout=2)
        if resp.status == 200:
            body = json.loads(resp.read().decode())
            return body.get("status", "ok")
    except (urllib.error.URLError, OSError, json.JSONDecodeError, UnicodeDecodeError):
        pass
    return None


def check_docker_health(url: str) -> bool:
    try:
        resp = urllib.request.urlopen(url, timeout=2)
        return resp.status == 200
    except (urllib.error.URLError, OSError):
        return False


def update_health_statuses(statuses: dict):
    for svc in DOCKER_SERVICES:
        health_url = svc.get("health_url")
        if not health_url:
            continue
        name = svc["name"]
        if check_docker_health(health_url):
            statuses[name] = "Running"
        else:
            statuses[name] = "Unavailable"

    for svc in SERVICES:
        health_url = svc.get("health_url")
        if not health_url:
            continue
        name = svc["name"]
        current = statuses.get(name, "")
        if current in ("Pending", "Stopped"):
            continue
        health_status = check_health(health_url)
        if health_status is not None:
            statuses[name] = f"Running [{health_status}]"
        elif current.startswith("Running"):
            statuses[name] = "Unhealthy"


def format_uptime(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}h {m:02d}m {s:02d}s"
    return f"{m}m {s:02d}s"


STATUS_COLORS = {
    "Running": "green",
    "Stopped": "red",
    "Unavailable": "red",
    "Unhealthy": "red",
    "Pending": "dim",
}


def _status_style(status: str) -> str:
    for key, color in STATUS_COLORS.items():
        if status.startswith(key):
            return color
    return "yellow"


def build_table(statuses: dict) -> Table:
    elapsed = time.time() - START_TIME

    table = Table(title=f"RAG Services  (uptime: {format_uptime(elapsed)})", caption="Press Ctrl+C to stop all services. Logs: ./logs/<service>.log")
    table.add_column("Name", style="bold", width=14)
    table.add_column("Port", width=8)
    table.add_column("Runtime", width=10)
    table.add_column("Status", width=22)
    table.add_column("URL", width=36)

    for svc in DOCKER_SERVICES:
        status = statuses.get(svc["name"], "Checking...")
        table.add_row(svc["name"], str(svc["port"]), "Docker", Text(status, style=_status_style(status)), svc["url"])

    for svc in SERVICES:
        url = f"http://localhost:{svc['port']}/docs"
        status = statuses.get(svc["name"], "Pending")
        table.add_row(svc["name"].capitalize(), str(svc["port"]), "Python", Text(status, style=_status_style(status)), url)

    return table


def main():
    statuses: dict[str, str] = {}
    processes: dict[str, subprocess.Popen] = {}
    launcher_threads: list[threading.Thread] = []
    stop_event = threading.Event()

    for svc in DOCKER_SERVICES:
        statuses[svc["name"]] = "Checking..."
    for svc in SERVICES:
        statuses[svc["name"]] = "Pending"

    for svc in SERVICES:
        t = threading.Thread(
            target=run_service,
            args=(svc, statuses, processes, stop_event),
            name=f"launcher-{svc['name']}",
            daemon=True,
        )
        t.start()
        launcher_threads.append(t)

    running = True
    last_health_check = 0.0

    def shutdown(sig, frame):
        nonlocal running
        running = False
        stop_event.set()
        for process in processes.values():
            if process.poll() is None:
                process.terminate()
        for process in processes.values():
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        for svc in SERVICES:
            statuses[svc["name"]] = "Stopped"

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    with Live(build_table(statuses), refresh_per_second=4) as live:
        while running:
            now = time.time()
            if now - last_health_check >= HEALTH_INTERVAL:
                update_health_statuses(statuses)
                last_health_check = now

            live.update(build_table(statuses))

            if launcher_threads and all(not t.is_alive() for t in launcher_threads):
                break
            time.sleep(0.25)


if __name__ == "__main__":
    main()
