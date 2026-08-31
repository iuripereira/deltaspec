#!/usr/bin/env python3
"""Gate mecânico do handoff de sessão — skill handoff, delta-098.

Valida os itens MECANIZÁVEIS do checklist de reprovação do template v2
(1, 4, 5, 9, 10 — os outros 5 exigem julgamento textual e viram autorrevisão no
passo 3.5 do SKILL.md, não regex). Arquivo sem frontmatter é v1 (anterior a esta
delta): o gate se omite, v1 não se reescreve em massa.

Uso: check_handoff.py --selftest
     check_handoff.py .claude/handoffs/HANDOFF_<topico>_<AAAA>_<MM>_<DD>.md
Requer Python 3.11+ (mesma linha de base do restante do plugin).
"""
import argparse
import re
import sys
import tempfile
from pathlib import Path

# Import do módulo da skill irmã git-guard — mesmo padrão de
# skills/audit-workspace/scripts/audit_workspace.py:65-71: o dono do catálogo de
# segredo é a git-guard; o item 10 importa em vez de reimplementar o casamento.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "git-guard" / "scripts"))
from segredos import casar  # noqa: E402

CAMPOS_OBRIGATORIOS = ("topico", "data", "status", "seq", "veio_de", "delta", "resumo")
RE_FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)
RE_CAMPO = re.compile(r"^([a-z_]+):\s*(.*)$", re.M)

RE_TBD = re.compile(r"\b(TBD|a definir|revisar depois)\b", re.I)
RE_DT = re.compile(r"\bDT-\d+\b")
RE_PASSO_AGORA = re.compile(r"^\d+\.\s+\*agora\*.*$", re.M)
RE_PROXIMO_ITEM = re.compile(r"^\d+\.\s+\*(?:agora|depois)\*", re.M)
RE_FENCE = re.compile(r"```\n?(.*?)```", re.S)


def parse_frontmatter_handoff(caminho: Path) -> dict | None:
    """Lê o frontmatter de um HANDOFF_*.md. None = v1 sem frontmatter (gate se omite).

    Devolve os 7 campos, não só o sinal v1/v2: é a interface que a delta-099
    (handoff-md-como-indice-gerado, dependência já declarada) importa para ler
    `resumo`/`seq`/`data` sem reescrever o parser — só o gate desta delta usa o `None`.
    """
    texto = caminho.read_text(encoding="utf-8")
    m = RE_FRONTMATTER.match(texto)
    if not m:
        return None
    bruto = dict(RE_CAMPO.findall(m.group(1)))
    campos = {k: bruto.get(k, "").strip() for k in CAMPOS_OBRIGATORIOS}
    if campos["seq"]:
        campos["seq"] = int(campos["seq"])
    return campos


def validar_item_1(texto: str) -> list[str]:
    """Item 1: TBD/a definir/revisar depois sem DT-NNN na mesma linha."""
    achados = []
    for i, linha in enumerate(texto.splitlines(), start=1):
        if RE_TBD.search(linha) and not RE_DT.search(linha):
            achados.append(f"item 1 — linha {i}: pendência sem DT-NNN: {linha.strip()!r}")
    return achados


def _secao(texto: str, titulo: str) -> str | None:
    """Extrai o conteúdo de uma seção `## titulo` até o próximo `## ` ou fim do arquivo."""
    m = re.search(rf"^## {re.escape(titulo)}\s*$", texto, re.M)
    if not m:
        return None
    resto = texto[m.end():]
    fim = re.search(r"^## ", resto, re.M)
    return resto[: fim.start()] if fim else resto


def validar_item_4(texto: str) -> list[str]:
    """Item 4: passo *agora* sem 'Funciona quando:' antes do próximo item numerado."""
    secao = _secao(texto, "Próximos passos imediatos")
    if secao is None:
        return []
    achados = []
    for m in RE_PASSO_AGORA.finditer(secao):
        prox = RE_PROXIMO_ITEM.search(secao, m.end())
        bloco = secao[m.start(): prox.start() if prox else len(secao)]
        if "Funciona quando:" not in bloco:
            achados.append(f"item 4 — passo sem 'Funciona quando:': {m.group().strip()!r}")
    return achados


def validar_item_5(texto: str) -> list[str]:
    """Item 5: 'Estado do código' sem a substring 'NÃO verificado'."""
    secao = _secao(texto, "Estado do código")
    if secao is None:
        return ["item 5 — seção 'Estado do código' ausente"]
    if "NÃO verificado" not in secao:
        return ["item 5 — 'NÃO verificado' ausente em 'Estado do código'"]
    return []


def validar_item_9(texto: str) -> list[str]:
    """Item 9: 'Prompt de retomada' sem bloco de código não-vazio."""
    secao = _secao(texto, "Prompt de retomada")
    if secao is None:
        return ["item 9 — seção 'Prompt de retomada' ausente"]
    m = RE_FENCE.search(secao)
    if not m or not m.group(1).strip():
        return ["item 9 — prompt de retomada vazio ou sem bloco de código"]
    return []


def validar_item_10(texto: str) -> list[str]:
    """Item 10: segredo/token/PII — reusa o catálogo da git-guard, não reimplementa."""
    return [f"item 10 — possível segredo ({nome}) na linha {linha}"
            for nome, linha in casar(texto)]


def validar_handoff(caminho: Path) -> list[str]:
    fm = parse_frontmatter_handoff(caminho)
    if fm is None:
        return []  # v1, gate se omite
    texto = caminho.read_text(encoding="utf-8")
    achados: list[str] = []
    achados += validar_item_1(texto)
    achados += validar_item_4(texto)
    achados += validar_item_5(texto)
    achados += validar_item_9(texto)
    achados += validar_item_10(texto)
    return achados


# --- selftests -------------------------------------------------------------

def selftest_parse_frontmatter_valido() -> None:
    conteudo = (
        "---\n"
        "topico: exemplo-de-sessao\n"
        "data: 2026-08-30\n"
        "status: fechado\n"
        "seq: 1\n"
        "veio_de: \n"
        "delta: \n"
        "resumo: sessão de exemplo para o selftest\n"
        "---\n\n"
        "## Objetivo\ntexto\n"
    )
    with tempfile.TemporaryDirectory() as tmp:
        caminho = Path(tmp) / "HANDOFF_exemplo_2026_08_30.md"
        caminho.write_text(conteudo, encoding="utf-8")
        fm = parse_frontmatter_handoff(caminho)
        assert fm is not None, "frontmatter válido não deveria retornar None"
        assert fm["topico"] == "exemplo-de-sessao"
        assert fm["seq"] == 1
    print("selftest_parse_frontmatter_valido: OK")


def selftest_parse_frontmatter_v1_sem_frontmatter() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        caminho = Path(tmp) / "HANDOFF_legado_2026_07_18.md"
        caminho.write_text("# Handoff: legado\n\n**Data:** 2026-07-18\n", encoding="utf-8")
        assert parse_frontmatter_handoff(caminho) is None, \
            "v1 sem frontmatter deve retornar None, não levantar"
    print("selftest_parse_frontmatter_v1_sem_frontmatter: OK")


def selftest_item_1() -> None:
    achado = validar_item_1("- item TBD sem dono\n")
    assert achado, "TBD sem DT-NNN deveria acusar"
    limpo = validar_item_1("- item TBD, ver DT-042\n")
    assert not limpo, "TBD com DT-NNN na mesma linha não deveria acusar"
    print("selftest_item_1: OK")


def selftest_item_4() -> None:
    sem_funciona = (
        "## Próximos passos imediatos\n\n"
        "1. *agora* — fazer algo\n"
        "   - Onde: `arquivo.py:10`\n"
        "2. *depois* — outra coisa\n"
    )
    achado = validar_item_4(sem_funciona)
    assert achado, "passo *agora* sem 'Funciona quando:' deveria acusar"

    com_funciona = (
        "## Próximos passos imediatos\n\n"
        "1. *agora* — fazer algo\n"
        "   - Funciona quando: `comando` → resultado\n"
        "2. *depois* — outra coisa\n"
    )
    limpo = validar_item_4(com_funciona)
    assert not limpo, "passo *agora* com 'Funciona quando:' não deveria acusar"
    print("selftest_item_4: OK")


def selftest_item_5() -> None:
    achado = validar_item_5("## Estado do código\n\n- Mudou: x\n")
    assert achado, "seção sem 'NÃO verificado' deveria acusar"
    limpo = validar_item_5("## Estado do código\n\n- NÃO verificado: nada\n")
    assert not limpo, "seção com 'NÃO verificado' não deveria acusar"
    print("selftest_item_5: OK")


def selftest_item_9() -> None:
    vazio = validar_item_9("## Prompt de retomada\n\n```\n```\n")
    assert vazio, "bloco de código vazio deveria acusar"
    preenchido = validar_item_9("## Prompt de retomada\n\n```\nLeia o HANDOFF.md.\n```\n")
    assert not preenchido, "bloco de código preenchido não deveria acusar"
    print("selftest_item_9: OK")


def selftest_item_10() -> None:
    # Concatenado, não literal — mesmo cuidado do selftest da própria git-guard
    # (segredos.py:227): valor de credencial inteiro no fonte dispara o G1 no
    # pre-commit deste repo, mesmo sendo só fixture de teste.
    aws_falsa = "AK" + "IA" + "3KJ7QWNP2LXVDR8T"
    com_segredo = validar_item_10(f'AWS_KEY = "{aws_falsa}"\n')
    assert com_segredo, "texto com padrão de segredo deveria acusar"
    limpo = validar_item_10("nada de sensível aqui\n")
    assert not limpo, "texto limpo não deveria acusar"
    print("selftest_item_10: OK")


def selftest() -> None:
    selftest_parse_frontmatter_valido()
    selftest_parse_frontmatter_v1_sem_frontmatter()
    selftest_item_1()
    selftest_item_4()
    selftest_item_5()
    selftest_item_9()
    selftest_item_10()
    print("selftest: OK (parser, 5 itens mecanizáveis)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("caminho", nargs="?")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return
    if not args.caminho:
        ap.error("caminho do handoff é obrigatório sem --selftest")
    achados = validar_handoff(Path(args.caminho))
    for a in achados:
        print(f"achado: {a}")
    sys.exit(1 if achados else 0)


if __name__ == "__main__":
    main()
