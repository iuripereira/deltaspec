#!/usr/bin/env python3
"""Gate de release (delta-057): o campo `version` do .claude-plugin/plugin.json
é espelho da tag git `vX.Y.Z` — a tag é a fonte da verdade (CLAUDE.md, tríade
de release). Falha quando o manifesto fica ATRÁS da maior tag (bump esquecido
no release); manifesto igual à tag ou à frente dela (PR que vai cortar a tag
no merge) passa. A duplicação deliberada tag ↔ manifesto está documentada no
deps.toml — ela não cabe no C1 porque o valor muda a cada release."""

import json
import re
import subprocess
import sys
from pathlib import Path

MANIFESTO = Path(".claude-plugin/plugin.json")
PADRAO_SEMVER = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")


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
    print("versao_manifesto selftest: OK (5 casos)")
    return 0


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    versao = json.loads(MANIFESTO.read_text(encoding="utf-8")).get("version", "")
    tag = maior_tag()
    if not tag:
        print("versao_manifesto: nenhuma tag vX.Y.Z encontrada — nada a comparar, e passar em silêncio esconderia o drift")
        return 1
    ok, msg = comparar(versao, tag)
    print(f"versao_manifesto: {msg}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
