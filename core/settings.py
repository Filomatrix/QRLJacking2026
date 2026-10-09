# -*- coding: utf-8 -*-
"""Configurações globais do QRLJacker v2."""
import json
from pathlib import Path

VERSION = "2.0.0"

BASE_DIR = Path(__file__).resolve().parent.parent

SESSIONS_DIR = BASE_DIR / "sessions"
SHOTS_DIR = BASE_DIR / "shots"
PROFILES_DIR = BASE_DIR / "profiles"
TEMPLATES_DIR = BASE_DIR / "templates"
SESSIONS_FILE = SESSIONS_DIR / "sessions.json"

# Rede / servidor
HOST = "0.0.0.0"
PORT = 8080

# Comportamento
QR_REFRESH_SECONDS = 3      # intervalo entre capturas do QR
POLL_SECONDS = 2            # intervalo de checagem de sessão estabelecida
PAGE_SETTLE_SECONDS = 4     # espera após abrir a página / clicar pré-ações
RELOAD_AFTER = 35           # recarrega a página do alvo se o QR sumir por N segundos
ONCE_TIMEOUT = 90           # limite global do modo --once (segundos)

# Binários opcionais (deixe vazio para autodetecção)
CHROME_BINARY = ""
FIREFOX_BINARY = ""

# Depuração
VERBOSE = False
DEBUG = False


def ensure_dirs():
    for d in (SESSIONS_DIR, SHOTS_DIR, PROFILES_DIR):
        d.mkdir(parents=True, exist_ok=True)
    if not SESSIONS_FILE.exists():
        SESSIONS_FILE.write_text("{}", encoding="utf-8")


def load_sessions():
    try:
        return json.loads(SESSIONS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_sessions(sessions):
    SESSIONS_FILE.write_text(json.dumps(sessions, indent=2), encoding="utf-8")
