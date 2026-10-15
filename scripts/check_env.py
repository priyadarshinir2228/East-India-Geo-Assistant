"""Check that this laptop can run the PoC: Python, pinned packages, tools, ports and services.
No secrets are printed. Run: python -m scripts.check_env
"""
import importlib.metadata as md
import platform
import shutil
import socket
import subprocess
import sys
from pathlib import Path

import requests

from common import config

ROOT = Path(__file__).resolve().parents[1]
PORTS = {9200: "Elasticsearch", 5601: "Kibana", 8080: "GeoServer", 8081: "llama-server", 8501: "Streamlit"}


def line(ok, text):
    print(f"  [{'ok' if ok else '!!'}] {text}")


def pinned():
    out = {}
    for row in (ROOT / "requirements.txt").read_text().splitlines():
        row = row.split("#")[0].strip()
        if "==" in row:
            name, ver = row.split("==")
            out[name.strip()] = ver.strip()
    return out


def tool_version(cmd):
    if not shutil.which(cmd[0]):
        return None
    r = subprocess.run(cmd, capture_output=True, text=True)
    return (r.stdout or r.stderr).strip().splitlines()[0]


def port_open(port):
    with socket.socket() as s:
        s.settimeout(1)
        return s.connect_ex(("127.0.0.1", port)) == 0


def main():
    print("Python")
    line(sys.version_info >= (3, 10), f"{platform.python_version()} at {sys.executable}")
    line(sys.prefix != sys.base_prefix, f"virtual environment {sys.prefix} (base {sys.base_prefix})")

    print("Pinned packages (requirements.txt)")
    for name, want in pinned().items():
        try:
            got = md.version(name)
        except md.PackageNotFoundError:
            got = None
        line(got == want, f"{name}=={want}" + ("" if got == want else f"  (installed: {got})"))
    print(f"  torch {md.version('torch')} (not pinned; CPU build is enough)")

    print("Tools")
    for cmd in (["docker", "--version"], ["cmake", "--version"], ["git", "--version"]):
        v = tool_version(cmd)
        line(v is not None, v or f"{cmd[0]} not found")
    llama = shutil.which("llama-server") or (r"D:\llama-bin\llama-server.exe" if Path(r"D:\llama-bin\llama-server.exe").exists() else None)
    line(llama is not None, f"llama-server: {llama or 'not found'}")
    gguf = ROOT / "models" / "Qwen2.5-3B-Instruct-Q4_K_M.gguf"
    line(gguf.exists(), f"{gguf.name}: {gguf.stat().st_size / 1e9:.2f} GB" if gguf.exists() else f"{gguf.name} missing")

    print("Ports on 127.0.0.1")
    for port, name in PORTS.items():
        line(port_open(port) or port == 8501, f"{port} {name}: {'listening' if port_open(port) else 'closed'}")

    print("Services")
    try:
        h = requests.get(config.ES_URL + "/_cluster/health", headers={"Authorization": f"ApiKey {config.ES_API_KEY}"}, timeout=10).json()
        line(h.get("status") == "green", f"Elasticsearch as rag_app (API key): status {h.get('status')}")
    except Exception as e:
        line(False, f"Elasticsearch: {e.__class__.__name__}")
    try:
        r = requests.get(config.LLM_URL + "/health", timeout=30)
        line(r.status_code == 200, f"llama-server /health: {r.status_code} {r.text.strip()}")
    except Exception as e:
        line(False, f"llama-server: {e.__class__.__name__}")
    try:  # the admin page is slow on first load, so allow a minute
        r = requests.get(config.GEOSERVER_URL + "/web/", timeout=60)
        line(r.status_code == 200, f"GeoServer admin page: {r.status_code}")
    except Exception as e:
        line(False, f"GeoServer admin page: {e.__class__.__name__}")


if __name__ == "__main__":
    main()
