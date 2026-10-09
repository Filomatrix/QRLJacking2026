# -*- coding: utf-8 -*-
"""Fábrica de navegadores (Selenium 4).

Drivers (chromedriver/geckodriver) são resolvidos automaticamente pelo
Selenium Manager — não é preciso instalar nada manualmente, diferente do
QRLJacker original que exigia geckodriver em /usr/local/share.
"""
from selenium import webdriver
from selenium.webdriver.common.by import By

from core.color import warning
from core import settings

UA_FALLBACK = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
               "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")


def pick_useragent(useragent="(random)"):
    """Resolve o User-Agent que será fixado no navegador."""
    if useragent and useragent.strip().lower() not in ("", "(random)"):
        return useragent.strip()
    try:
        from user_agent import generate_user_agent
        return generate_user_agent(os=("windows", "mac", "linux"), device_type="desktop")
    except Exception:
        return UA_FALLBACK


def _chrome_options(headless, ua):
    opts = webdriver.ChromeOptions()
    if headless:
        opts.add_argument("--headless=new")
    # Disfarces básicos de automação
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--window-size=1280,900")
    opts.add_argument(f"--user-agent={ua}")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument("--no-first-run")
    opts.add_argument("--no-default-browser-check")
    if settings.CHROME_BINARY:
        opts.binary_location = settings.CHROME_BINARY
    return opts


def _firefox_options(headless, ua):
    opts = webdriver.FirefoxOptions()
    if headless:
        opts.add_argument("-headless")
    opts.set_preference("general.useragent.override", ua)
    opts.set_preference("dom.webdriver.enabled", False)
    opts.set_preference("marionette.webdriver.enabled", False)
    opts.set_preference("privacy.trackingprotection.enabled", False)
    if settings.FIREFOX_BINARY:
        opts.binary_location = settings.FIREFOX_BINARY
    return opts


def make_driver(browser="auto", headless=True, useragent="(random)"):
    """Cria um WebDriver pronto para uso. Retorna (driver, useragent)."""
    ua = pick_useragent(useragent)
    order = ["chrome", "firefox"] if browser == "auto" else [browser]
    last = None
    for b in order:
        try:
            if b == "chrome":
                drv = webdriver.Chrome(options=_chrome_options(headless, ua))
            elif b == "firefox":
                drv = webdriver.Firefox(options=_firefox_options(headless, ua))
            else:
                raise ValueError(f"navegador desconhecido: {b}")
            drv.set_window_size(1280, 900)
            return drv, ua
        except Exception as e:
            last = e
            first_line = str(e).splitlines()[0] if str(e) else repr(e)
            warning(f"Falha ao iniciar '{b}': {first_line}")
    raise RuntimeError(f"Nenhum navegador disponível ({last})")


def visible_elements(driver, css):
    """Retorna apenas elementos visíveis que casam com o seletor CSS."""
    out = []
    try:
        for el in driver.find_elements(By.CSS_SELECTOR, css):
            try:
                if el.size["width"] > 0 and el.size["height"] > 0:
                    out.append(el)
            except Exception:
                continue
    except Exception:
        pass
    return out


def best_square(elements, min_side=100):
    """Heurística de fallback: QR codes são quadrados grandes.

    Retorna o elemento visível mais quadrado (razão de aspecto < 0.25 de
    diferença entre lados) com o maior lado.
    """
    cands = []
    for el in elements:
        try:
            w, h = el.size["width"], el.size["height"]
            if min(w, h) >= min_side and abs(w - h) / max(w, h, 1) < 0.25:
                cands.append(el)
        except Exception:
            continue
    return max(cands, key=lambda e: min(e.size["width"], e.size["height"])) if cands else None
