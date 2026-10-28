#!/usr/bin/env python3
"""Ancoragem determinística do projeto a uma versão do deltaspec — delta-104.

O projeto declara em `doc-profile.yaml` a versão do framework que consome; este
script a confronta com o plugin REALMENTE em execução ($CLAUDE_PLUGIN_ROOT). Sem
isso a âncora dependia de disciplina: `/plugin install` não aceita versão e um
`/plugin update` tira o consumidor da âncora sem avisar.

Teto declarado (R1): o plugin roda de onde o harness o instalou e nenhum arquivo
no repositório muda isso. O que se alcança é DETECÇÃO — a deriva deixa de depender
de alguém lembrar e passa a reprovar sozinha, em três pontos: este comando, o C17
do check_cycle.py e o hook de pré-commit do git-guard.

Duas omissões deliberadas, ambas exit 0:
  - chave ausente  → todo projeto já inicializado está assim; a chave é opcional
                     por desenho, como a cauda do doc-profile já é (C11).
  - sem plugin root→ é o CI de um repo consumidor, onde nenhum plugin existe.
                     A deriva só existe onde o plugin roda; reprovar aqui quebraria
                     o CI de todo consumidor (RNF2, molde do W6/W10 do audit-workspace).

Uso: ancora.py verificar [RAIZ]        (default: cwd)
     ancora.py fixar RAIZ VERSAO       escreve a chave, relê e recusa não-SemVer
     ancora.py --selftest
Exit 0 = em dia, omitido ou degradado · 1 = fora da âncora ou declaração inválida
       · 2 = erro de uso.
Requer Python 3.11+ (mesma linha de base do restante do plugin).
"""
import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path

PERFIL = "doc-profile.yaml"
MANIFESTO_PLUGIN = Path(".claude-plugin") / "plugin.json"
# `v` é cosmético: a tag git usa, o manifesto não. Normalizar impede que a mesma
# versão escrita nas duas formas vire falso positivo.
RE_SEMVER = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")
# Leitura rasa do doc-profile: só a chave `ancora` sob `deltaspec`. Regex e não
# PyYAML de propósito — o hook de pré-commit roda antes de qualquer instalação de
# dependência, e este script não pode exigir o que o projeto ainda não tem.
RE_BLOCO_DELTASPEC = re.compile(r"^deltaspec:\s*$(.*?)(?=^\S|\Z)", re.M | re.S)
RE_ANCORA = re.compile(r"^\s+ancora:\s*[\"']?([^\"'#\s]+)[\"']?", re.M)


def normalizar(versao: str) -> tuple[int, int, int] | None:
    """'v1.51.1' e '1.51.1' → (1, 51, 1). None = não é SemVer reconhecível. Pura."""
    m = RE_SEMVER.match(versao.strip())
    return (int(m[1]), int(m[2]), int(m[3])) if m else None


def comparar(declarada: str, em_execucao: str) -> str | None:
    """None = em dia. str = o achado, já redigido. Pura — o coração do gate.

    Âncora é pino EXATO, não piso: plugin mais novo deriva tanto quanto mais velho.
    Quem quer faixa não quer âncora (renúncia registrada no spec da delta-104).
    """
    alvo = normalizar(declarada)
    if alvo is None:
        return (f"âncora declarada inválida: {declarada!r} não é SemVer — "
                f"declaração ilegível aparenta proteção e não protege; "
                f"corrija com `ancora.py fixar . vX.Y.Z`")
    atual = normalizar(em_execucao)
    if atual is None:
        return (f"versão do plugin em execução ilegível: {em_execucao!r} — "
                f"esperado SemVer no .claude-plugin/plugin.json")
    if alvo == atual:
        return None
    sentido = "mais nova" if atual > alvo else "mais velha"
    return (f"fora da âncora: o projeto declara {declarada}, o plugin em execução é "
            f"{em_execucao} ({sentido}) — reancore conscientemente lendo o CHANGELOG "
            f"entre as duas, ou volte o plugin para a versão declarada")


def ler_ancora(raiz: Path) -> str | None:
    """Versão declarada no doc-profile.yaml, ou None quando não há perfil nem chave."""
    perfil = raiz / PERFIL
    if not perfil.is_file():
        return None
    try:
        texto = perfil.read_text(encoding="utf-8")
    except OSError:
        return None
    bloco = RE_BLOCO_DELTASPEC.search(texto)
    if not bloco:
        return None
    m = RE_ANCORA.search(bloco[1])
    return m[1] if m else None


def versao_em_execucao() -> str | None:
    """Versão do plugin sob $CLAUDE_PLUGIN_ROOT. None = artefato do harness ausente."""
    raiz = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if not raiz:
        return None
    try:
        dados = json.loads((Path(raiz) / MANIFESTO_PLUGIN).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    versao = dados.get("version")
    return versao if isinstance(versao, str) else None


def verificar(raiz: Path) -> tuple[int, str | None]:
    """(exit_code, achado). Ambas as omissões devolvem 0 — ver docstring do módulo."""
    declarada = ler_ancora(raiz)
    if declarada is None:
        return 0, None
    atual = versao_em_execucao()
    if atual is None:
        print("[ancora] $CLAUDE_PLUGIN_ROOT ausente ou sem manifesto legível — "
              "verificação omitida (a deriva só existe onde o plugin roda)",
              file=sys.stderr)
        return 0, None
    achado = comparar(declarada, atual)
    return (1, achado) if achado else (0, None)


def fixar(raiz: Path, versao: str) -> tuple[int, str]:
    """Escreve `deltaspec.ancora` e RELÊ antes de devolver (doutrina do debito.py novo).

    Recusa antes de tocar o disco: versão inválida não deixa arquivo alterado.
    """
    if normalizar(versao) is None:
        return 2, f"versão {versao!r} não é SemVer — nada foi escrito"
    perfil = raiz / PERFIL
    if not perfil.is_file():
        return 2, f"{PERFIL} não encontrado em {raiz} — rode a projeto-init antes"
    texto = perfil.read_text(encoding="utf-8")
    linha = f'  ancora: "{versao}"'
    if RE_BLOCO_DELTASPEC.search(texto):
        novo = RE_BLOCO_DELTASPEC.sub(
            lambda m: f"deltaspec:\n{linha}\n", texto, count=1)
    else:
        bloco = ("\n# Versão do deltaspec a que este projeto está ancorado (delta-104).\n"
                 "# Preenchida = o gate reprova quando o plugin em execução diverge.\n"
                 "deltaspec:\n" + linha + "\n")
        novo = texto.rstrip("\n") + "\n" + bloco
    perfil.write_text(novo, encoding="utf-8")
    relido = ler_ancora(raiz)
    if relido != versao:
        return 2, (f"escrita não conferiu na releitura: gravei {versao!r}, li {relido!r} "
                   f"— o perfil pode ter formato inesperado; confira à mão")
    return 0, f"âncora fixada em {versao} ({PERFIL})"


# --- selftest -----------------------------------------------------------------
# Fixtures co-localizadas (RNF4). O plugin root é simulado por variável de ambiente
# e diretório temporário: nenhum caso depende de haver plugin instalado na máquina.

PERFIL_MINIMO = (
    'decisao: { data: "2026-01-01", justificativa: "x" }\n'
    'publico: { interno: true, cliente: false }\n'
    "artefatos:\n"
    "  arquitetura: { obrigatorio: false }\n"
)


def _monta(tmp: Path, ancora: str | None) -> Path:
    raiz = tmp / "repo"
    raiz.mkdir(exist_ok=True)
    texto = PERFIL_MINIMO
    if ancora is not None:
        texto += f'deltaspec:\n  ancora: "{ancora}"\n'
    (raiz / PERFIL).write_text(texto, encoding="utf-8")
    return raiz


def _plugin(tmp: Path, versao: str | None) -> None:
    """Aponta $CLAUDE_PLUGIN_ROOT para um plugin falso, ou o remove (versao=None)."""
    if versao is None:
        os.environ.pop("CLAUDE_PLUGIN_ROOT", None)
        return
    raiz = tmp / "plugin"
    (raiz / ".claude-plugin").mkdir(parents=True, exist_ok=True)
    (raiz / MANIFESTO_PLUGIN).write_text(
        json.dumps({"name": "deltaspec", "version": versao}), encoding="utf-8")
    os.environ["CLAUDE_PLUGIN_ROOT"] = str(raiz)


def selftest_puras() -> None:
    assert normalizar("v1.51.1") == (1, 51, 1)
    assert normalizar("1.51.1") == (1, 51, 1), "o 'v' é cosmético — CT4"
    assert normalizar("1.51") is None and normalizar("main") is None
    assert comparar("v1.51.1", "1.51.1") is None, "mesma versão em formas diferentes — CT4"
    frente = comparar("v1.51.1", "1.52.0")
    assert frente and "mais nova" in frente, f"deriva para frente — CT2: {frente}"
    tras = comparar("v1.51.1", "1.50.0")
    assert tras and "mais velha" in tras, f"deriva para trás é deriva — CT3: {tras}"
    invalida = comparar("ultima", "1.51.1")
    assert invalida and "não é SemVer" in invalida, f"âncora inválida — CT7: {invalida}"
    assert comparar("v1.51.1", "sei-la") is not None, "manifesto ilegível também acusa"
    print("selftest_puras: OK")


def selftest_verificar() -> None:
    guardado = os.environ.get("CLAUDE_PLUGIN_ROOT")
    try:
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            _plugin(tmp, "1.51.1")
            assert verificar(_monta(tmp, "v1.51.1")) == (0, None), "em dia — CT1"

            code, achado = verificar(_monta(tmp, "v1.50.0"))
            assert code == 1 and achado and "fora da âncora" in achado, f"CT2: {achado}"

            # chave ausente: omite em silêncio, porque é o estado de todo projeto
            # já inicializado — a chave não propaga retroativamente (C11)
            assert verificar(_monta(tmp, None)) == (0, None), "chave ausente — CT5"

            # perfil inexistente também omite: repo sem doc-profile não é consumidor
            assert verificar(tmp / "vazio") == (0, None), "sem doc-profile, omite"

            code, achado = verificar(_monta(tmp, "ultima"))
            assert code == 1 and achado and "não é SemVer" in achado, f"CT7: {achado}"

            # sem plugin root, com âncora declarada: avisa e NÃO reprova — é o CI
            # de um repo consumidor; reprovar aqui quebraria todo consumidor (CT6)
            _plugin(tmp, None)
            assert verificar(_monta(tmp, "v1.51.1")) == (0, None), "sem plugin root — CT6"
    finally:
        os.environ.pop("CLAUDE_PLUGIN_ROOT", None)
        if guardado is not None:
            os.environ["CLAUDE_PLUGIN_ROOT"] = guardado
    print("selftest_verificar: OK")


def selftest_fixar() -> None:
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        raiz = _monta(tmp, None)
        antes = (raiz / PERFIL).read_text(encoding="utf-8")

        code, msg = fixar(raiz, "nao-semver")
        assert code == 2 and (raiz / PERFIL).read_text(encoding="utf-8") == antes, \
            f"versão inválida não pode tocar o disco — CT8: {msg}"

        code, msg = fixar(raiz, "v1.51.1")
        assert code == 0, msg
        assert ler_ancora(raiz) == "v1.51.1", "releitura devolve o gravado — CT9"

        # refixar substitui em vez de acumular um segundo bloco `deltaspec:`
        assert fixar(raiz, "v1.52.0")[0] == 0
        assert ler_ancora(raiz) == "v1.52.0"
        assert (raiz / PERFIL).read_text(encoding="utf-8").count("deltaspec:") == 1, \
            "refixar não pode duplicar o bloco"

        assert fixar(tmp / "vazio", "v1.51.1")[0] == 2, "sem doc-profile, recusa"
    print("selftest_fixar: OK")


def selftest() -> None:
    selftest_puras()
    selftest_verificar()
    selftest_fixar()
    print("selftest: OK (normalização, comparação, verificar, fixar)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("comando", nargs="?", choices=("verificar", "fixar"))
    ap.add_argument("raiz", nargs="?", default=".")
    ap.add_argument("versao", nargs="?")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return
    if not args.comando:
        ap.error("informe `verificar` ou `fixar` (ou --selftest)")
    if args.comando == "fixar":
        if not args.versao:
            ap.error("fixar exige a versão: `ancora.py fixar . v1.51.1`")
        code, msg = fixar(Path(args.raiz), args.versao)
        print(f"[ancora] {msg}", file=sys.stderr if code else sys.stdout)
        sys.exit(code)
    code, achado = verificar(Path(args.raiz))
    if achado:
        print(f"[ancora] ALTO — {achado}")
    sys.exit(code)


if __name__ == "__main__":
    main()
