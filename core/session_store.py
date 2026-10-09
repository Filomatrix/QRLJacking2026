# -*- coding: utf-8 -*-
"""Armazenamento e replay de sessões capturadas (cookies + localStorage)."""
import pickle
import time

from core import settings
from core.color import status, error
from core.browser import make_driver

# Chaves aceitas ao reinjetar cookies (evita erros de schema entre navegadores)
COOKIE_KEYS = ("name", "value", "path", "domain", "secure",
               "httpOnly", "expiry", "sameSite")


def next_free_id(sessions):
    i = 0
    while str(i) in sessions:
        i += 1
    return str(i)


def save_session(module_name, url, useragent, payload, extra=None):
    settings.ensure_dirs()
    sessions = settings.load_sessions()
    sid = next_free_id(sessions)
    fname = f"{sid}_{module_name}_{time.strftime('%Y%m%d-%H%M%S')}.session"
    fpath = settings.SESSIONS_DIR / fname
    with open(fpath, "wb") as f:
        pickle.dump(payload, f)
    entry = {
        "name": module_name,
        "web_url": url,
        "useragent": useragent,
        "session_path": str(fpath),
        "saved_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    if extra:
        entry.update(extra)
    sessions[sid] = entry
    settings.save_sessions(sessions)
    status(f"Sessão #{sid} de '{module_name}' salva em sessions/{fname}")
    return sid


def get_session(sid):
    return settings.load_sessions().get(str(sid))


def load_payload(sid):
    entry = get_session(sid)
    if not entry:
        raise KeyError(f"Sessão {sid} não existe")
    with open(entry["session_path"], "rb") as f:
        return pickle.load(f)


def replay(sid, browser="auto", headless=False):
    """Abre um navegador com a sessão capturada (cookies + localStorage).

    O User-Agent salvo na captura é reutilizado — muitos serviços ligam a
    sessão ao fingerprint do navegador original.
    """
    entry = get_session(sid)
    if not entry:
        error(f"Sessão {sid} não encontrada")
        return None
    payload = load_payload(sid)
    driver, _ = make_driver(browser=browser, headless=headless,
                            useragent=entry["useragent"])
    driver.get(entry["web_url"])
    driver.delete_all_cookies()
    driver.execute_script("window.localStorage.clear()")
    for c in payload.get("cookies", []):
        cookie = {k: c[k] for k in COOKIE_KEYS if k in c and c[k] is not None}
        try:
            driver.add_cookie(cookie)
        except Exception:
            pass
    local = payload.get("localStorage") or {}
    if local:
        script = ("for (const [k, v] of Object.entries(arguments[0])) {"
                  "  window.localStorage.setItem(k, v); }")
        driver.execute_script(script, local)
    driver.refresh()
    status(f"Sessão {sid} carregada em navegador {'headless' if headless else 'visível'}")
    return driver
