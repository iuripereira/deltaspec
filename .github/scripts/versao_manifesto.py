#!/usr/bin/env python3
"""Gate de release (delta-057): o campo `version` do .claude-plugin/plugin.json
é espelho da tag git `vX.Y.Z` — a tag é a fonte da verdade (CLAUDE.md, tríade
de release). Falha quando o manifesto fica ATRÁS da maior tag (bump esquecido
no release); manifesto igual à tag ou à frente dela (PR que vai cortar a tag
no merge) passa. A duplicação deliberada tag ↔ manifesto está documentada no
deps.toml — ela não cabe no C1 porque o valor muda a cada release.

Segunda comparação, mesma versão vista de outro lugar (DT-080): o repositório
derivado é projeção da tag, publicada à mão por decisão humana (ADR-0036) — e
por isso pode ficar para trás sem que nada acuse. Aqui ele é **consultado**,
nunca deduzido, e a defasagem sai como `::warning::`: publicar continua sendo
decisão, então o gate informa e não reprova. O endereço do derivado não é
configuração nova — é o `repository` do próprio manifesto, que já era lido."""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

MANIFESTO = Path(".claude-plugin/plugin.json")
PADRAO_SEMVER = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")
# Consulta de rede num gate de CI: curta e sem retry — estado desconhecido é
# resposta aceitável (RNF2), gate lento não é.
LIMITE_REDE_S = 15


def parse_versao(texto: str):
    """'v1.26.1' ou '1.26.1' → (1, 26, 1); qualquer outra forma → None."""
    m = PADRAO_SEMVER.match(texto.strip())
    return tuple(int(g) for g in m.groups()) if m else None


def comparar(versao_manifesto: str, tag: str):
    """Veredito puro (ok, mensagem) — testável sem git nem filesystem."""
    vm = parse_versao(versao_manifesto)
    vt = parse_versao(tag)
    if vm is None:
        return False, f"version do manifesto não é SemVer: {versao_manifesto!r}"
    if vt is None:
        return False, f"tag não é SemVer: {tag!r}"
    if vm < vt:
        return (
            False,
            f"manifesto {versao_manifesto} ATRÁS da tag {tag} — o PR de release "
            "esqueceu o bump do plugin.json (regra: CLAUDE.md, tríade de release)",
        )
    return True, f"manifesto {versao_manifesto} × tag {tag}: OK"


def maior_versao(nomes) -> str:
    """Maior tag SemVer de uma lista de nomes; '' quando nenhuma é SemVer."""
    versoes = sorted(v for v in (parse_versao(n) for n in nomes) if v)
    return "v{}.{}.{}".format(*versoes[-1]) if versoes else ""


def comparar_derivado(tag_canonica: str, tag_derivada: str):
    """Veredito puro (atrasado, mensagem) — testável sem rede."""
    if not tag_derivada:
        return False, (
            "derivado NÃO consultado (sem resposta ou sem tag SemVer) — estado "
            "desconhecido, não presuma que está em dia"
        )
    vc, vd = parse_versao(tag_canonica), parse_versao(tag_derivada)
    if vc is None or vd is None:
        return False, f"comparação impossível: canônico {tag_canonica!r} × derivado {tag_derivada!r}"
    if vd < vc:
        return True, (
            f"derivado em {tag_derivada}, canônico em {tag_canonica} — publique com "
            f"`scripts/publica-dist.sh {tag_canonica}` (publicar é decisão sua, ADR-0036)"
        )
    return False, f"derivado em {tag_derivada} × canônico {tag_canonica}: em dia"


def tags_remotas(url: str):
    """Nomes das tags publicadas em `url`; lista vazia se o remoto não responde."""
    try:
        saida = subprocess.run(
            ["git", "ls-remote", "--tags", "--refs", url],
            capture_output=True, text=True, timeout=LIMITE_REDE_S,
            # Sem o prompt, remoto inacessível vira erro na hora em vez de um gate
            # pendurado esperando usuário e senha que ninguém vai digitar no CI.
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        )
    except (subprocess.TimeoutExpired, OSError):
        return []
    if saida.returncode != 0:
        return []
    return [linha.rsplit("/", 1)[-1] for linha in saida.stdout.splitlines() if "\t" in linha]


def maior_tag() -> str:
    """Maior tag vX.Y.Z do repo; busca as tags se o checkout raso não as trouxe."""

    def listar():
        saida = subprocess.run(
            ["git", "tag", "-l", "v*", "--sort=-v:refname"],
            capture_output=True, text=True, check=True,
        ).stdout.split()
        return saida[0] if saida else ""

    tag = listar()
    if not tag:
        subprocess.run(["git", "fetch", "--tags", "--force", "--quiet"], check=True)
        tag = listar()
    return tag


def selftest() -> int:
    ok, _ = comparar("1.26.1", "v1.26.2")
    assert not ok, "manifesto atrás da tag deveria falhar"
    ok, _ = comparar("1.26.1", "v1.26.1")
    assert ok, "manifesto igual à tag deveria passar"
    for adiante in ("1.26.2", "1.27.0", "2.0.0"):
        ok, _ = comparar(adiante, "v1.26.1")
        assert ok, f"manifesto à frente ({adiante}) deveria passar"
    ok, msg = comparar("banana", "v1.26.1")
    assert not ok and "SemVer" in msg, "version não-SemVer deveria falhar"
    ok, msg = comparar("1.26.1", "release-3")
    assert not ok and "tag" in msg, "tag não-SemVer deveria falhar"

    assert maior_versao(["v1.9.0", "v1.10.1", "v1.10.0"]) == "v1.10.1", "ordem é SemVer, não alfabética"
    assert maior_versao(["nightly", "release-3"]) == "", "sem tag SemVer não há maior versão"

    atrasado, msg = comparar_derivado("v1.40.0", "v1.39.0")
    assert atrasado and "publica-dist.sh v1.40.0" in msg, "derivado atrás deveria avisar com o comando"
    atrasado, _ = comparar_derivado("v1.40.0", "v1.40.0")
    assert not atrasado, "derivado em dia não avisa"
    atrasado, _ = comparar_derivado("v1.40.0", "v1.41.0")
    assert not atrasado, "derivado à frente é anomalia de release, não defasagem — o gate do manifesto é quem cobra"
    atrasado, msg = comparar_derivado("v1.40.0", "")
    assert not atrasado and "desconhecido" in msg, "sem resposta o estado é desconhecido, nunca 'em dia'"
    print("versao_manifesto selftest: OK (11 casos)")
    return 0


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    manifesto = json.loads(MANIFESTO.read_text(encoding="utf-8"))
    versao = manifesto.get("version", "")
    tag = maior_tag()
    if not tag:
        print("versao_manifesto: nenhuma tag vX.Y.Z encontrada — nada a comparar, e passar em silêncio esconderia o drift")
        return 1
    ok, msg = comparar(versao, tag)
    print(f"versao_manifesto: {msg}")

    derivado = manifesto.get("repository", "")
    if derivado:
        atrasado, msg_derivado = comparar_derivado(tag, maior_versao(tags_remotas(derivado)))
        prefixo = "::warning::" if atrasado else ""
        print(f"{prefixo}derivado {derivado}: {msg_derivado}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
