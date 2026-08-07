#!/usr/bin/env python3
"""Dialetos de projeção para tickets — módulo comum importável por T2/T3 da delta-017.

Emite .sh de creates unitários em Jira CLI (acli) — decisão da delta-017 (DT-021: bulk
rejeita \n). Contrato: funções puras de corpo_ticket/etiquetas (copiadas de debito.py
sem mudança de assinatura) + emitir_sh_acli que orquestra.
"""
import re
import shlex
import tempfile
from pathlib import Path

# Constantes — copiadas do contexto de debito.py onde são usadas
FAIXA_ALTA = 9
FAIXA_MEDIA = 3
ROTULO_NATUREZA = {"débito": "debito", "pendência": "pendencia"}
LINK_MD = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")

# Tipos de item em Jira — zero valor mágico
TIPO_ITEM = "Task"
TIPO_EPICO = "Epic"


def alvo_local(item: dict) -> str:
    """Caminho do artefato apontado em 'Local' (primeiro link, sem âncora)."""
    achados = LINK_MD.findall(item.get("local", ""))
    return achados[0].split("#")[0] if achados else ""


def corpo_ticket(item: dict, entrada: dict) -> str:
    """Markdown do ticket — sempre declarando que o arquivo é a fonte, não ele.

    O `Local` entra como caminho literal, não como link relativo: dentro de um
    issue o relativo resolve contra a URL da issue (não contra a árvore do repo)
    e quebra; no Jira ele nem é interpretado.
    """
    caminho = alvo_local(item) or item.get("local", "—")
    return (
        f"{item.get('descrição', '')}\n\n"
        f"- **Local:** `{caminho}`\n"
        f"- **Origem:** {item.get('origem', '—')}\n"
        f"- **Fila:** {item.get('fila', '—')} · **Score:** {entrada['score']:.2f}\n"
        f"- **Gatilho:** {item.get('gatilho', '—')}\n\n---\n"
        f"_Projeção de **{item['id']}** do `DEBT.md`. A fonte da verdade é o arquivo versionado; "
        f"este ticket é espelho para gestão (ADR-0021)._"
    )


def etiquetas(item: dict, entrada: dict) -> list:
    """Etiquetas de fila e natureza baseadas em score e estado."""
    faixa = ("alta" if entrada["score"] >= FAIXA_ALTA
             else "media" if entrada["score"] >= FAIXA_MEDIA else "baixa")
    marcas = [f"dt:{item['id']}", f"deltaspec:{ROTULO_NATUREZA[item['natureza']]}", f"fila:{faixa}"]
    if entrada["trilha"]:
        marcas.append("fila:trilha")
    if entrada["override"]:
        marcas.append(f"fila:override-{entrada['override'][0]}")
    return marcas


def emitir_sh_acli(itens: list, projeto: str, saida: Path, epico: str | None = None) -> Path:
    """Emite .sh de creates unitários — decisão da delta-017 (DT-021: bulk rejeita \n).

    Args:
        itens: lista de {"id","title","body","labels"}
        projeto: projeto Jira (--project)
        saida: Path onde escrever corpo-<id>.md e tickets-acli.sh
        epico: se presente, cria épico primeiro e usa --parent nas filhas

    Returns:
        Path do tickets-acli.sh gerado
    """
    linhas = ["#!/usr/bin/env bash",
              "# Emitido por projecao.py — revise antes de executar (R52: quem executa é a skill).",
              "set -euo pipefail", ""]
    if epico:
        linhas += [f"EPICO=$(acli jira workitem create --project {shlex.quote(projeto)} "
                   f"--type {TIPO_EPICO} --summary {shlex.quote(epico)} --json "
                   "| python3 -c 'import json,sys; print(json.load(sys.stdin)[\"key\"])')",
                   'echo "épico criado: $EPICO"', ""]
    for i in itens:
        corpo = saida / f"corpo-{i['id']}.md"
        corpo.write_text(i["body"], encoding="utf-8")
        rotulos = f" --label {shlex.quote(','.join(i['labels']))}" if i["labels"] else ""
        pai = ' --parent "$EPICO"' if epico else ""
        linhas.append(f"acli jira workitem create --project {shlex.quote(projeto)} "
                      f"--type {TIPO_ITEM} --summary {shlex.quote(i['title'])}{rotulos}"
                      f"{pai} --description-file {shlex.quote(str(corpo))} --json")
    destino = saida / "tickets-acli.sh"
    destino.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return destino


def selftest():
    """Casos de verificação: (a) 2 itens sem épico; (b) com épico; (c) corpo multi-linha
    byte-idêntico; (d) summary com aspas."""
    with tempfile.TemporaryDirectory() as td:
        saida = Path(td)
        itens = [
            {"id": "DT-001", "title": 'a "b"', "body": "l1\n\n- item\n\n---\nfim", "labels": ["dt:DT-001"]},
            {"id": "DT-002", "title": "c", "body": "curto", "labels": ["x", "y"]},
        ]
        sh = emitir_sh_acli(itens, "SBX", saida)
        texto = sh.read_text(encoding="utf-8")
        assert "create-bulk" not in texto, "bulk quebrado não pode voltar (DT-021)"
        assert texto.count("acli jira workitem create ") == 2
        assert (saida / "corpo-DT-001.md").read_text(encoding="utf-8") == itens[0]["body"]
        assert "--label dt:DT-001" in texto and "--label x,y" in texto
        sh2 = emitir_sh_acli(itens, "SBX", saida, epico="[delta-017] jira-tickets")
        t2 = sh2.read_text(encoding="utf-8")
        assert t2.index("--type Epic") < t2.index("--type Task")
        assert '--parent "$EPICO"' in t2
    print("selftest projecao: OK")


if __name__ == "__main__":
    selftest()
