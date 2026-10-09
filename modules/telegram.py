# -*- coding: utf-8 -*-
from modules import Module

MODULE = Module(
    name="telegram",
    url="https://web.telegram.org/k/",
    qr_selectors=[
        "canvas",
    ],
    success_selectors=[
        "aside.sidebar",
        "#left-column",
    ],
    success_url_contains=[],
    pre_click_xpath=[
        "//button[contains(., 'og in by QR')]",   # "Log in by QR code" / pt-BR
    ],
    browser="auto",
    note=("Cliente Web K. Dependendo da versão, o Telegram pode pedir "
          "confirmação no app antes de parear — valide no seu ambiente."),
    phishing={
        "TITLE": "Telegram Web",
        "COLOR": "#2AABEE",
        "TAGLINE": "Telegram para navegadores.",
        "FOOTER": "Acesse suas conversas de qualquer lugar.",
        "REFRESH_MS": "2500",
    },
)
