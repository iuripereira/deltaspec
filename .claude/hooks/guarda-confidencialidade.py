#!/usr/bin/env python3
"""Gate de identificador de terceiro, nas duas pontas (delta-064).

Este repositório é **privado e é a fonte canônica**; o repositório público é
derivado dele por allowlist (`scripts/publica-dist.sh`, ADR-0036). A
documentação de processo cita casos concretos, e é natural que o nome do caso
escorregue junto com o fato técnico. O gate separa os dois: o fato entra, o
identificador não.

Dois modos, uma única regra de casamento (`achar_nomes`):

- **hook `PreToolUse`** (sem argumento, JSON no stdin) — primeira ponta, no
  momento da escrita. Sem a lista, avisa e libera: degradação graciosa (RNF2).
- **`--varre <dir>`** — segunda ponta, na publicação. Varre a árvore do
  snapshot e sai 1 se achar. Aqui a degradação **se inverte**: quem publica
  sem lista não tem gate, e sem gate não se publica — o chamador aborta.

O registro privado (`specs/`, `debts/`, handoffs) segue com nome real: o
escopo da regra é o allowlist de publicação, não todo arquivo versionado, e
é o que mantém o registro honesto (R7, delta-064).

**A lista de nomes vive FORA do git** (`.claude/nomes-confidenciais.txt`,
gitignored). Versioná-la anularia o propósito — a lista seria a exposição.

Escrita fora do diretório do projeto é ignorada: o alvo é o que pode ser
commitado.
"""

import json
import os
import re
import sys
import tempfile
from pathlib import Path

LISTA_PADRAO = ".claude/nomes-confidenciais.txt"


def carregar_nomes(texto: str) -> list[str]:
    """Parse puro da lista: uma entrada por linha, `#` comenta, vazias caem."""
    nomes = []
    for linha in texto.splitlines():
        entrada = linha.split("#", 1)[0].strip()
        if entrada:
            nomes.append(entrada)
    return nomes


def achar_nomes(conteudo: str, nomes: list[str]) -> list[str]:
    """Puro: nomes da lista presentes no conteúdo (case-insensitive, subpalavra).

    Subpalavra de propósito: a raiz curta do nome precisa casar os derivados
    (`<nome>-projeto`, `Suporte<Nome>`), que é como o identificador realmente
    aparece. O custo é falso positivo em palavra que contenha o nome; o remédio
    é a lista ser específica, não o casamento ser frouxo.
    """
    achados = []
    for nome in nomes:
        if re.search(re.escape(nome), conteudo, re.IGNORECASE):
            achados.append(nome)
    return achados


def varrer_arvore(raiz: Path, nomes: list[str]) -> list[tuple[str, str]]:
    """Puro sobre o disco: `(caminho relativo, nome)` para cada achado na árvore.

    Mesma regra de casamento do hook — `achar_nomes` é o dono. Arquivo que não
    decodifica como texto é pulado: o alvo é documentação e script, e binário
    ilegível não pode travar a publicação de tudo.
    """
    achados = []
    for arquivo in sorted(p for p in raiz.rglob("*") if p.is_file()):
        try:
            conteudo = arquivo.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        relativo = arquivo.relative_to(raiz).as_posix()
        achados.extend((relativo, nome) for nome in achar_nomes(conteudo, nomes))
    return achados


def dentro_do_projeto(caminho: str, raiz: str) -> bool:
    """Puro: o caminho cai sob a raiz do projeto?"""
    if not caminho or not raiz:
        return False
    try:
        Path(os.path.abspath(caminho)).relative_to(os.path.abspath(raiz))
        return True
    except ValueError:
        return False


def decidir(caminho: str, conteudo: str, nomes: list[str], raiz: str):
    """Decisão pura: nome confidencial em caminho do projeto → dict de `deny`."""
    if not nomes or not dentro_do_projeto(caminho, raiz):
        return None
    achados = achar_nomes(conteudo, nomes)
    if not achados:
        return None
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"nome confidencial na escrita ({', '.join(sorted(achados))}) — "
                "este caminho pode ser publicado. Use pseudônimo (`cliente-A`, "
                "`caso de referência`, `um repo consumidor`) e preserve só o "
                "fato técnico. Se a exposição for deliberada e autorizada, "
                f"retire o nome de {LISTA_PADRAO}."
            ),
        }
    }


def selftest() -> int:
    nomes = carregar_nomes("# comentário\nAcme\n\n  Globex  # inline\n")
    assert nomes == ["Acme", "Globex"], nomes

    raiz = "/repo"
    assert decidir("/repo/CHANGELOG.md", "validado na Acme", nomes, raiz) is not None
    assert decidir("/repo/CHANGELOG.md", "validado no caso X", nomes, raiz) is None
    # subpalavra: repo derivado do nome precisa casar
    assert decidir("/repo/x.md", "acme-viagens", nomes, raiz) is not None
    # sufixo separado da raiz NÃO contém a raiz, logo não casa por subpalavra —
    # é assim que dois derivados atravessaram o gate até a delta-066. A correção
    # é de dado, não de código: o sufixo entra na lista como entrada própria.
    assert decidir("/repo/x.md", "viagens", nomes, raiz) is None
    nomes_com_sufixo = carregar_nomes("Acme\nviagens\n")
    assert decidir("/repo/x.md", "viagens", nomes_com_sufixo, raiz) is not None
    # case-insensitive
    assert decidir("/repo/x.md", "SuporteACME", nomes, raiz) is not None
    # fora do projeto: silêncio (scratchpad, rascunho local)
    assert decidir("/tmp/scratch/relatorio.md", "Acme", nomes, raiz) is None
    # lista ausente: degrada, nunca bloqueia
    assert decidir("/repo/CHANGELOG.md", "Acme", [], raiz) is None
    veredito = decidir("/repo/a.md", "Globex", nomes, raiz)
    assert veredito["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "Globex" in veredito["hookSpecificOutput"]["permissionDecisionReason"]

    assert achar_nomes("nada aqui", nomes) == []
    assert dentro_do_projeto("/repo/a.md", "/repo") is True
    assert dentro_do_projeto("/outro/a.md", "/repo") is False
    assert dentro_do_projeto("", "/repo") is False

    # --- modo varredura (delta-064): a árvore publicável passa pelo mesmo casamento ---
    with tempfile.TemporaryDirectory() as tmp:
        raiz_varre = Path(tmp)
        (raiz_varre / "sub").mkdir()
        (raiz_varre / "limpo.md").write_text("só fato técnico", encoding="utf-8")
        assert varrer_arvore(raiz_varre, nomes) == []

        (raiz_varre / "sub" / "sujo.md").write_text("validado na Acme", encoding="utf-8")
        achados = varrer_arvore(raiz_varre, nomes)
        assert achados == [("sub/sujo.md", "Acme")], achados

        # binário e ilegível não derrubam a varredura
        (raiz_varre / "bin.png").write_bytes(b"\x89PNG\x00\xff\xfeAcme")
        assert [c for c, _ in varrer_arvore(raiz_varre, nomes)] == ["sub/sujo.md"]

        # lista vazia não acha nada, mas quem decide publicar é o chamador
        assert varrer_arvore(raiz_varre, []) == []

    print("guarda-confidencialidade selftest: OK (20 casos)")
    return 0


def localizar_lista() -> Path:
    """I/O: a lista mora no repo (gitignored), nunca na árvore varrida."""
    raiz = os.environ.get("CLAUDE_PROJECT_DIR", "")
    return Path(raiz) / LISTA_PADRAO if raiz else Path(LISTA_PADRAO)


def varrer(destino: str) -> int:
    """I/O do modo publicação: 0 = árvore limpa, 1 = achado ou gate indisponível.

    Ao contrário do hook, lista ausente aqui **reprova**. Publicar é porta de
    mão única; sem gate, não se atravessa.
    """
    lista = localizar_lista()
    if not lista.is_file():
        print(
            f"guarda-confidencialidade: {LISTA_PADRAO} ausente — sem gate não se publica",
            file=sys.stderr,
        )
        return 1

    nomes = carregar_nomes(lista.read_text(encoding="utf-8"))
    if not nomes:
        print(f"guarda-confidencialidade: {LISTA_PADRAO} vazia — sem gate não se publica", file=sys.stderr)
        return 1

    achados = varrer_arvore(Path(destino), nomes)
    if not achados:
        print(f"guarda-confidencialidade: árvore limpa ({len(nomes)} termos conferidos)")
        return 0

    for caminho, nome in achados:
        print(f"guarda-confidencialidade: {caminho}: {nome}", file=sys.stderr)
    print(f"guarda-confidencialidade: {len(achados)} achado(s) — publicação abortada", file=sys.stderr)
    return 1


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    if "--varre" in sys.argv:
        return varrer(sys.argv[sys.argv.index("--varre") + 1])
    try:
        entrada = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # input inesperado: silêncio, nunca bloqueia a sessão

    raiz = os.environ.get("CLAUDE_PROJECT_DIR", "")
    lista = Path(raiz) / LISTA_PADRAO if raiz else Path(LISTA_PADRAO)
    if not lista.is_file():
        print(f"guarda-confidencialidade: {LISTA_PADRAO} ausente — gate inativo", file=sys.stderr)
        return 0

    nomes = carregar_nomes(lista.read_text(encoding="utf-8"))
    tool_input = entrada.get("tool_input") or {}
    caminho = tool_input.get("file_path", "")
    # Write manda `content`; Edit manda `new_string`.
    conteudo = f"{tool_input.get('content', '')}\n{tool_input.get('new_string', '')}"

    veredito = decidir(caminho, conteudo, nomes, raiz)
    if veredito:
        print(json.dumps(veredito))
    return 0


if __name__ == "__main__":
    sys.exit(main())
