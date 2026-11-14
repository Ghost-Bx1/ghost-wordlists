#!/usr/bin/env python3
"""
gerador.py - Gerador de Wordlists WiFi Brasil
CVE/Tool: ghost-wifi-wordlists
Autor: Ghost-Bx1 | github.com/Ghost-Bx1

Gera wordlists personalizadas baseadas em contexto brasileiro:
- Permutacoes de nomes/palavras
- Padroes de datas brasileiras
- Padroes de SSID de provedores
- Combinacoes com sufixos/prefixos comuns
"""

import sys
import os
import argparse
import itertools
from datetime import datetime

VERSAO = "1.0.0"

SUFIXOS_COMUNS = [
    "123", "1234", "12345", "123456", "1234567", "12345678",
    "!", "@", "#", "@123", "@1234", "@2024", "@2025", "@2026",
    "2024", "2025", "2026", "2023", "2022",
    "0", "1", "01", "10", "007", "000", "111",
    "wifi", "wlan", "casa", "net", "br", "brs",
]

PREFIXOS_COMUNS = [
    "minha", "meu", "minhas", "meus", "nossa", "nosso",
    "wifi_", "rede_", "net_", "casa_",
]

SUBSTITUICOES_LEET = {
    'a': ['4', '@'],
    'e': ['3'],
    'i': ['1', '!'],
    'o': ['0'],
    's': ['5', '$'],
    'l': ['1'],
}

SUFIXOS_ANO = [str(a) for a in range(1970, 2027)]

C = {
    "G": "\033[92m", "R": "\033[91m", "Y": "\033[93m",
    "C": "\033[96m", "D": "\033[2m", "X": "\033[0m", "W": "\033[97m",
}


def _log(tag, msg, cor="W"):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"  {C[cor]}[{tag}]{C['X']} {C['D']}{ts}{C['X']} {msg}")


def gerar_permutacoes(palavra, nivel=2):
    resultados = set()
    p = palavra.lower()
    resultados.add(p)
    resultados.add(p.capitalize())
    resultados.add(p.upper())

    for suf in SUFIXOS_COMUNS:
        resultados.add(p + suf)
        resultados.add(p.capitalize() + suf)

    if nivel >= 2:
        for pre in PREFIXOS_COMUNS:
            resultados.add(pre + p)
            resultados.add(pre + p.capitalize())
        for ano in SUFIXOS_ANO[-10:]:
            resultados.add(p + ano)
            resultados.add(p.capitalize() + ano)

    if nivel >= 3:
        for c, substitutos in SUBSTITUICOES_LEET.items():
            if c in p:
                for sub in substitutos:
                    variante = p.replace(c, sub)
                    resultados.add(variante)
                    resultados.add(variante + "123")
                    resultados.add(variante + "!")

    return sorted(resultados)


def gerar_datas(dia=None, mes=None, ano=None):
    resultados = set()

    anos_base = [str(a) for a in range(1960, 2015)]
    meses = [str(m).zfill(2) for m in range(1, 13)]
    dias = [str(d).zfill(2) for d in range(1, 32)]

    if dia and mes and ano:
        d = str(dia).zfill(2)
        m = str(mes).zfill(2)
        a = str(ano)
        aa = a[2:] if len(a) == 4 else a
        resultados.update([
            f"{d}{m}{a}", f"{d}{m}{aa}",
            f"{m}{d}{a}", f"{a}{m}{d}",
            f"{d}/{m}/{a}", f"{d}-{m}-{a}",
            f"{d}{m}", f"{m}{a}",
        ])
        return sorted(resultados)

    for a in [str(x) for x in range(1980, 2010)]:
        for m in meses:
            for d in dias[:28]:
                aa = a[2:]
                resultados.add(f"{d}{m}{a}")
                resultados.add(f"{d}{m}{aa}")
    return sorted(resultados)


def gerar_padrao_ssid_claro(ssid):
    """Gera senhas candidatas para SSID Claro/NET no formato NET_XXXXXX ou CLARO_XXXXXX"""
    resultados = set()
    # Extrai sufixo hex do SSID
    partes = ssid.upper().replace("NET_", "").replace("CLARO_", "").replace("-", "").strip()
    if partes:
        resultados.add(partes.lower())
        resultados.add(partes.upper())
        resultados.add(partes[:8].lower())
        resultados.add(partes[:8].upper())
        # Senhas derivadas do MAC (ultimos 8 chars do SSID como senha)
        resultados.add(partes[-8:].lower())
        resultados.add(partes[-8:].upper())
    # Defaults fixos Claro
    resultados.update(["claro123", "net12345", "12345678", "claro@2024", "claro@2025"])
    return sorted(resultados)


def gerar_padrao_ssid_vivo(ssid):
    """Gera senhas candidatas para SSID Vivo no formato VIVO-XXXXXX"""
    resultados = set()
    partes = ssid.upper().replace("VIVO-", "").replace("VIVO_", "").strip()
    if partes:
        resultados.add(partes.lower())
        resultados.add(partes.upper())
        resultados.add(partes[:8].lower())
    resultados.update(["vivo1234", "vivo12345", "vivo@2024", "vivo@2025", "1234567890"])
    return sorted(resultados)


def gerar_provedor_regional(nome_provedor, cidade=None):
    """Gera wordlist para provedor regional brasileiro"""
    resultados = set()
    n = nome_provedor.lower().replace(" ", "").replace("-", "")
    for suf in ["123", "1234", "12345", "@123", "@2024", "@2025", "wifi", "fibra"]:
        resultados.add(n + suf)
        resultados.add(n.capitalize() + suf)
        resultados.add(n + "@" + suf.lstrip("@"))
    if cidade:
        c = cidade.lower().replace(" ", "")
        resultados.add(n + c)
        resultados.add(n + c + "123")
    return sorted(resultados)


def combinar_wordlists(arquivos, saida, deduplicar=True):
    senhas = []
    vistos = set()
    for arq in arquivos:
        try:
            with open(arq, encoding="utf-8", errors="ignore") as f:
                for linha in f:
                    s = linha.strip()
                    if not s or s.startswith("#"):
                        continue
                    if deduplicar:
                        if s not in vistos:
                            vistos.add(s)
                            senhas.append(s)
                    else:
                        senhas.append(s)
        except Exception as e:
            _log("WARN", f"Erro ao ler {arq}: {e}", "Y")
    with open(saida, "w", encoding="utf-8") as f:
        f.write("\n".join(senhas) + "\n")
    _log("OK", f"{len(senhas)} senhas salvas em {saida}", "G")
    return len(senhas)


def _parse_args():
    p = argparse.ArgumentParser(
        description="Gerador de Wordlists WiFi Brasil - Ghost-Bx1",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python gerador.py --palavra joao --nivel 2 -o joao.txt
  python gerador.py --data 15/03/1990 -o datas.txt
  python gerador.py --ssid-claro NET_A1B2C3 -o claro_candidates.txt
  python gerador.py --ssid-vivo VIVO-X1Y2Z3 -o vivo_candidates.txt
  python gerador.py --provedor "MinhaNet" --cidade "Juazeiro" -o minhanet.txt
  python gerador.py --combinar *.txt -o completa.txt
        """,
    )
    p.add_argument("--palavra", "-w", help="Palavra base para gerar permutacoes")
    p.add_argument("--nivel", "-n", type=int, default=2, choices=[1, 2, 3],
                   help="Nivel de profundidade: 1=basico 2=medio 3=completo (default: 2)")
    p.add_argument("--data", "-d", help="Data no formato DD/MM/YYYY para gerar padroes")
    p.add_argument("--todas-datas", action="store_true",
                   help="Gerar todas as datas brasileiras comuns (arquivo grande)")
    p.add_argument("--ssid-claro", metavar="SSID",
                   help="SSID no formato NET_XXXXXX ou CLARO_XXXXXX")
    p.add_argument("--ssid-vivo", metavar="SSID",
                   help="SSID no formato VIVO-XXXXXX")
    p.add_argument("--provedor", metavar="NOME",
                   help="Nome do provedor regional para gerar wordlist especifica")
    p.add_argument("--cidade", metavar="CIDADE",
                   help="Cidade do provedor (opcional, usado com --provedor)")
    p.add_argument("--combinar", "-c", nargs="+", metavar="ARQUIVO",
                   help="Combinar e deduplicar multiplos arquivos wordlist")
    p.add_argument("--output", "-o", default="wordlist_gerada.txt",
                   help="Arquivo de saida (default: wordlist_gerada.txt)")
    p.add_argument("--no-banner", action="store_true")
    return p.parse_args()


def main():
    args = _parse_args()
    if not args.no_banner:
        print(f"\n  {C['G']}Ghost-WiFi-Wordlists{C['X']} - Gerador Brasil v{VERSAO}")
        print(f"  {C['D']}By Gh0st-Bx1 | github.com/Ghost-Bx1{C['X']}\n")

    resultados = []

    if args.palavra:
        _log("GEN", f"Gerando permutacoes para: {args.palavra} (nivel {args.nivel})", "C")
        resultados = gerar_permutacoes(args.palavra, args.nivel)
        _log("OK", f"{len(resultados)} senhas geradas", "G")

    elif args.data:
        try:
            dt = datetime.strptime(args.data, "%d/%m/%Y")
            _log("GEN", f"Gerando padroes de data para {args.data}", "C")
            resultados = gerar_datas(dt.day, dt.month, dt.year)
            _log("OK", f"{len(resultados)} padroes gerados", "G")
        except ValueError:
            _log("ERR", "Formato de data invalido. Use DD/MM/YYYY", "R")
            sys.exit(1)

    elif args.todas_datas:
        _log("GEN", "Gerando todas as datas (pode demorar...)", "Y")
        resultados = gerar_datas()
        _log("OK", f"{len(resultados)} datas geradas", "G")

    elif args.ssid_claro:
        _log("GEN", f"Gerando candidatos para SSID Claro: {args.ssid_claro}", "C")
        resultados = gerar_padrao_ssid_claro(args.ssid_claro)
        _log("OK", f"{len(resultados)} candidatos", "G")

    elif args.ssid_vivo:
        _log("GEN", f"Gerando candidatos para SSID Vivo: {args.ssid_vivo}", "C")
        resultados = gerar_padrao_ssid_vivo(args.ssid_vivo)
        _log("OK", f"{len(resultados)} candidatos", "G")

    elif args.provedor:
        _log("GEN", f"Gerando wordlist para provedor: {args.provedor}", "C")
        resultados = gerar_provedor_regional(args.provedor, args.cidade)
        _log("OK", f"{len(resultados)} senhas", "G")

    elif args.combinar:
        _log("GEN", f"Combinando {len(args.combinar)} arquivos...", "C")
        total = combinar_wordlists(args.combinar, args.output)
        return

    else:
        print(f"  {C['Y']}Nenhuma acao especificada. Use --help para ver opcoes.{C['X']}\n")
        sys.exit(0)

    if resultados:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write("\n".join(resultados) + "\n")
        _log("SAVE", f"Wordlist salva em: {args.output} ({len(resultados)} entradas)", "G")


if __name__ == "__main__":
    main()
