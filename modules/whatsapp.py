# -*- coding: utf-8 -*-
from modules import Module

MODULE = Module(
    name="whatsapp",
    url="https://web.whatsapp.com/",
    qr_selectors=[
        "div[data-ref] canvas",     # wrapper clássico do QR do WhatsApp Web
        "canvas[aria-label]",
        "canvas",
    ],
    success_selectors=[
        "#side",                    # painel de chats
        "div[data-testid='chat-list']",
    ],
    success_url_contains=[],
    pre_click_xpath=[],
    browser="auto",
    note=("O WhatsApp passou a exigir a confirmação de um código numérico no "
          "celular após escanear o QR (mitigação introduzida em 2023). Este "
          "módulo serve para validar a mitigação/detecção, não conte com "
          "concluir a sessão nas versões atuais."),
    phishing={
        "TITLE": "WhatsApp Web",
        "COLOR": "#00a884",
        "TAGLINE": "Envie e receba mensagens do WhatsApp rapidamente.",
        "FOOTER": "Mantenha seu celular conectado à internet.",
        "REFRESH_MS": "2500",
    },
)
