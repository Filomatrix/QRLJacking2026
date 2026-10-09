# -*- coding: utf-8 -*-
"""Saída colorida no terminal (compatível com Windows 10+)."""
import os

if os.name == "nt":
    os.system("")  # habilita processamento ANSI no Windows


def _c(code, text):
    return f"\033[{code}m{text}\033[0m"


def status(msg):
    print(_c("92", "[+] ") + str(msg))


def error(msg):
    print(_c("91", "[-] ") + str(msg))


def warning(msg):
    print(_c("93", "[!] ") + str(msg))


def info(msg):
    print(_c("94", "[i] ") + str(msg))


def title(msg):
    print(_c("95;1", str(msg)))
