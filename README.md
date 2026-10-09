# QRLJacker v2 — QRLJacking Exploitation Framework (reescrita moderna)

Reescrita moderna do **QRLJacker** original ([OWASP/QRLJacking](https://github.com/OWASP/QRLJacking)),
que está inativo desde 2025 e quebrado com as versões atuais de navegador e Selenium.

**QRLJacking** (Quick Response Code Login Jacking) é o vetor de ataque que sequestra
sessões de serviços que usam "login por QR code": o atacante exibe, em uma página
controlada por ele, o QR de login de uma sessão que *ele* controla; a vítima escaneia
o QR com o próprio celular e pareia a sessão no navegador do atacante.

> **Uso exclusivo em ambientes autorizados** (laboratório, clientes com contrato de
> teste, avaliação dos seus próprios sistemas). Engenharia social contra terceiros é
> crime na maioria das jurisdições (no Brasil, art. 154-A do Código Penal e Lei Geral
> de Proteção de Dados).

---

## O que mudou em relação ao original

| Original (2020) | Esta versão (2026) |
|---|---|
| `selenium==3.141.0` (quebra no Selenium 4) | Selenium 4.x |
| geckodriver manual em `/usr/local/share` | Selenium Manager resolve os drivers sozinho |
| Só Firefox | Chrome e Firefox (padrão: auto) |
| XPath absoluto (quebra a cada redesign) | Seletores CSS em lista + heurística "maior quadrado visível" |
| Dependências antigas pinadas (`urllib3 1.26`, `pathlib2`) | Apenas `selenium` e `user-agent` |
| Servidor com HTML fixo | Template parametrizado (título, cor, textos) por módulo |
| Perfil do Firefox salvo em disco (frágil) | Cookies + localStorage (mais robusto e portável) |
| Python 3.7 | Python 3.10+ (testado no 3.14) |

## Instalação

```bash
# Requisitos: Python 3.10+ e Chrome ou Firefox instalados
git clone <este-repo>  # ou descompacte o pacote
cd qrljacker-modern
pip install -r requirements.txt

# Diagnóstico do ambiente (navegadores, drivers, módulos)
python QrlJacker.py --check
```

Não há etapa manual de geckodriver/chromedriver: o Selenium Manager baixa
o driver compatível automaticamente na primeira execução.

## Uso

### Menu interativo

```bash
python QrlJacker.py
```

### Linha de comando

```bash
# Teste rápido: captura um QR e sai (valida seletores sem phishing)
python QrlJacker.py -m telegram --once
# → o QR fica em shots/telegram.png

# Operação completa: grabber headless + servidor de phishing na porta 8080
python QrlJacker.py -m telegram --host 0.0.0.0 --port 8080

# Navegador visível (para depurar seletores)
python QrlJacker.py -m telegram --visible

# Sessões capturadas e replay (abre navegador já logado)
python QrlJacker.py --sessions
python QrlJacker.py --replay 0
```

### Fluxo de operação

1. O grabber abre a página de login do alvo em um navegador **headless**;
2. A thread de QR atualiza `shots/<modulo>.png` a cada 3 s (screenshot do elemento);
3. O servidor de phishing serve a página em `http://<seu-ip>:8080/` com o QR ao vivo;
4. A vítima escaneia o QR exibido — a sessão pareia no navegador do atacante;
5. O watcher detecta a sessão (seletor presente ou URL mudou), salva
   **cookies + localStorage** em `sessions/` (índice em `sessions/sessions.json`);
6. `--replay <id>` abre um navegador **visível** já autenticado com a sessão, usando
   o mesmo User-Agent da captura (o pareamento de sessão costuma ser ligado ao fingerprint);
7. Enquanto isso, a vítima vê apenas "Carregando…" na página de phishing.

### Módulo personalizado (qualquer serviço)

```bash
python QrlJacker.py --module-file meu_alvo.json
```

```json
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
    "FOOTER": "Mantenha seu celular conectado.",
    "REFRESH_MS": "2500"
  }
}
```

- `qr_selectors`: tentados em ordem; se nenhum casar, entra a heurística do
  maior quadrado visível (`canvas`/`img`).
- `success_selectors` / `success_url_contains`: como o framework sabe que a
  sessão foi estabelecida (elemento presente OU URL contém o fragmento).
- `pre_click_xpath`: cliques necessários antes do QR (ex.: botão "Entrar por QR").
- Valide sempre com `--once` e `--visible` antes de uma operação real.

## Estado dos módulos builtin (out/2026)

| Módulo | Estado | Observação |
|---|---|---|
| `whatsapp` | **Mitigado** | Desde 2023 o WhatsApp exige a confirmação de um código numérico no celular após o escaneio. Útil para validar a mitigação, não para concluir sessão. |
| `telegram` | **Verificar** | Cliente Web K. Dependendo da versão, pode pedir confirmação no app. |
| `discord` | **Verificar** | Versões recentes podem pedir confirmação no celular; sucesso detectado pela mudança para `/channels`. |

A técnica permanece válida contra serviços que pareiam a sessão **sem confirmação
no dispositivo** — teste cada alvo no seu laboratório antes da operação.

## Solução de problemas

- **"QR não localizado ainda"** — veja `shots/<modulo>_debug.png` (screenshot da
  página inteira). Ajuste `qr_selectors` no módulo. Use `--visible` para inspecionar.
- **`SessionNotCreatedException`** — atualize o navegador; o Selenium Manager baixa
  o driver, mas o binário do navegador precisa existir.
- **Nada acontece ao escanear** — o alvo provavelmente adotou confirmação no
  dispositivo (veja a tabela acima) ou liga a sessão a outros fingerprints.
- **Porta ocupada** — troque com `--port`.
- **Controles corporativos** — o QR live-refresh precisa de `no-store`; proxies com
  cache agressivo podem atrasar a atualização do QR para a vítima.

## Estrutura

```
QrlJacker.py            CLI (menu interativo + flags)
core/
  settings.py           configurações e caminhos
  browser.py            fábrica Selenium 4 (Chrome/Firefox) + heurística de QR
  grabber.py            motor: loops de QR e de detecção de sessão
  server.py             servidor de phishing (QR em tempo real + status)
  session_store.py      persistência e replay de sessões
  color.py              saída colorida
modules/
  __init__.py           dataclass Module + carregadores
  whatsapp.py telegram.py discord.py generic.py
templates/index.html    página de phishing parametrizada
sessions/ shots/ profiles/
```

## Créditos

Técnica originalmente documentada por **Mohamed Abdelbasset Elnouby** (project leader
do OWASP Qrljacker) e framework original por **Karim Shoair (D4Vinci)** — OWASP/QRLJacking.
Esta reescrita mantém o espírito do projeto com a pilha atual.
