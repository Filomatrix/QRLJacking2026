# -*- coding: utf-8 -*-
"""Registro de módulos do QRLJacker v2.

Um módulo é um dataclass com os seletores do alvo. Módulos builtin ficam
em modules/*.py; módulos personalizados são arquivos JSON carregados com
--module-file.
"""
import json
from dataclasses import dataclass, field, fields
from pathlib import Path


@dataclass
class Module:
    name: str
    url: str                                   # página de login por QR
    qr_selectors: list                         # seletores CSS do QR (em ordem de prioridade)
    success_selectors: list                    # seletores que indicam sessão estabelecida
    success_url_contains: list                 # fragmentos de URL que indicam sessão estabelecida
    pre_click_xpath: list                      # XPath de botões a clicar antes (ex.: "Login por QR")
    phishing: dict = field(default_factory=dict)  # contexto do template de phishing
    browser: str = "auto"                      # chrome | firefox | auto
    note: str = ""                             # observação exibida ao operador


MODULES_LIST = ["whatsapp", "telegram", "discord"]


def load_builtin(name):
    if name not in MODULES_LIST:
        raise KeyError(f"Módulo builtin '{name}' não existe")
    mod = __import__(f"modules.{name}", fromlist=["MODULE"])
    return mod.MODULE


def from_json(path):
    """Cria um Module a partir de um arquivo JSON configurado pelo operador."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    allowed = {f.name for f in fields(Module)}
    missing = {"name", "url"} - set(data)
    if missing:
        raise ValueError(f"JSON do módulo sem campos obrigatórios: {', '.join(missing)}")
    kwargs = {k: v for k, v in data.items() if k in allowed}
    defaults = {"qr_selectors": [], "success_selectors": [],
                "success_url_contains": [], "pre_click_xpath": [],
                "phishing": {}, "browser": "auto", "note": ""}
    for k, v in defaults.items():
        kwargs.setdefault(k, v)
    return Module(**kwargs)
