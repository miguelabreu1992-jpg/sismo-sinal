"""Mantem os servicos do visualizador num unico processo e encerra-os juntos."""

import os
import signal
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PORT = 8766
children = []
shutting_down = False


def find_sclang():
    candidates = [
        Path(os.environ.get("ProgramFiles", "")) / "SuperCollider" / "sclang.exe",
        Path(os.environ.get("ProgramFiles", "")) / "SuperCollider-3.14.1" / "sclang.exe",
        Path(os.environ.get("ProgramFiles", "")) / "SuperCollider-3.13.0" / "sclang.exe",
        Path(os.environ.get("ProgramFiles", "")) / "SuperCollider-3.12.2" / "sclang.exe",
        Path(os.environ.get("ProgramFiles(x86)", "")) / "SuperCollider" / "sclang.exe",
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return "sclang.exe"


def stop_process(process):
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    else:
        process.terminate()


def shutdown(*_args):
    global shutting_down
    if shutting_down:
        return
    shutting_down = True
    print("\nA encerrar SuperCollider, orquestra e servidor web...", flush=True)
    for process in reversed(children):
        stop_process(process)
    children.clear()


def wait_for_visualizer():
    url = f"http://127.0.0.1:{PORT}/visualizer.html"
    for _ in range(20):
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status == 200:
                    webbrowser.open(url)
                    print(f"Visualizador aberto em {url}", flush=True)
                    return True
        except OSError:
            time.sleep(1)
    print("O servidor web nao respondeu a tempo.", flush=True)
    return False


def main():
    signal.signal(signal.SIGINT, shutdown)
    if hasattr(signal, "SIGBREAK"):
        signal.signal(signal.SIGBREAK, shutdown)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, shutdown)

    sclang = find_sclang()
    print("A iniciar o receptor SuperCollider...", flush=True)
    children.append(subprocess.Popen([
        sclang, "-D", str(ROOT / "live_sismo_autostart.scd"),
    ]))

    print("Escolhe a saida na janela do SuperCollider e clica em 'Iniciar audio'.", flush=True)
    print("A aguardar o arranque do servidor de audio...", flush=True)
    time.sleep(15)
    if shutting_down:
        return

    print("A iniciar as quatro estacoes...", flush=True)
    children.append(subprocess.Popen([
        sys.executable, "-u", str(ROOT / "orquestra_sismo.py"),
    ], cwd=ROOT))

    print("A iniciar o servidor do visualizador...", flush=True)
    children.append(subprocess.Popen([
        sys.executable, "-u", str(ROOT / "control_server.py"),
    ], cwd=ROOT))

    if not wait_for_visualizer():
        return

    print("Sistema ativo. Fechar esta consola encerra todos os processos.", flush=True)
    while not shutting_down:
        time.sleep(1)
        if any(process.poll() is not None for process in children):
            print("Um servico terminou; a encerrar o sistema.", flush=True)
            shutdown()


if __name__ == "__main__":
    try:
        main()
    finally:
        shutdown()
