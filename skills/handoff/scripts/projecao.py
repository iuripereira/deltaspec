#!/usr/bin/env python3
"""Dialetos de projeção para tickets — módulo comum importável por T2/T3 da delta-017.

Emite .sh de creates unitários em Jira CLI (acli) — decisão da delta-017 (DT-021: bulk
rejeita \n). Contrato: funções puras de corpo_ticket/etiquetas (copiadas de debito.py
sem mudança de assinatura) + emitir_sh_acli que orquestra.
"""
import json
import re
import shlex
import sys
import tempfile
from pathlib import Path

from md_para_adf import converter  # o acli lê ADF, não Markdown (delta-034)

try:
    import yaml  # única dependência externa admitida nos gates (ADR-0023)
except ModuleNotFoundError:
    # Diferente do tickets.py, que aborta: aqui a ausência degrada (RNF2). O `debito.py`
    # roda em repo sem doc-profile.yaml e precisa seguir rodando sem PyYAML instalado —
    # perder a leitura do perfil só devolve o destino ao default, que é o GitHub.
    yaml = None

# Constantes — copiadas do contexto de debito.py onde são usadas
ARQUIVO_PERFIL = "doc-profile.yaml"
FAIXA_ALTA = 9
FAIXA_MEDIA = 3
ROTULO_NATUREZA = {"débito": "debito", "pendência": "pendencia"}
LINK_MD = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")

# Tipos de item em Jira — zero valor mágico
TIPO_ITEM = "Task"
TIPO_EPICO = "Epic"


def nome_var(id_: str) -> str:
    """Nome de variável bash válido a partir de um id (ex.: 'DT-001' -> 'DT_001')."""
    return re.sub(r"[^0-9A-Za-z_]", "_", id_)


def ler_projeto_jira(root: Path) -> str | None:
    """`motores.jira.projeto` do doc-profile.yaml; ausente ou desligado → None (RNF2).

    Dono único da leitura do destino (delta-035, DT-033): `debito.py` e `tickets.py`
    chamam esta função, nunca releem o campo por conta própria — dois leitores do mesmo
    campo divergiriam em silêncio, que é exatamente a classe de falha do DT-033.
    Ausência de `motores.jira` **é** a declaração de que a rota é o GitHub.
    """
    perfil = root / ARQUIVO_PERFIL
    if not perfil.is_file():
        return None
    if yaml is None:
        # Perfil existe mas não dá para lê-lo: sem este aviso o destino cairia no default
        # e a causa ficaria invisível — "não declarei" e "não consigo ler" viram a mesma
        # saída silenciosa, que é a família de falha que o DT-033 fecha.
        print(f"aviso: PyYAML ausente — {ARQUIVO_PERFIL} não lido, destino cai no default "
              "(pip install pyyaml, ADR-0023)")
        return None
    try:
        dados = yaml.safe_load(perfil.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        # Perfil ilegível não pode derrubar a projeção: o DEBT.md vale sozinho (RNF2).
        print(f"aviso: {ARQUIVO_PERFIL} ilegível — destino do ticket cai no default")
        return None
    jira = (dados.get("motores") or {}).get("jira")
    if not isinstance(jira, dict):
        return None
    projeto = jira.get("projeto")
    return projeto if projeto else None


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


def emitir_sh_acli(itens: list, projeto: str, saida: Path, epico: str | None = None,
                    capturar_chaves: bool = False, epico_existente: str | None = None,
                    epico_labels: list | None = None) -> Path:
    """Emite .sh de creates unitários — decisão da delta-017 (DT-021: bulk rejeita \n).

    Args:
        itens: lista de {"id","title","body","labels"}
        projeto: projeto Jira (--project)
        saida: Path onde escrever corpo-<id>.md e tickets-acli.sh
        epico: se presente, cria épico primeiro e usa --parent nas filhas
        epico_existente: se presente (e `epico` ausente), **não cria** o épico — usa a
            chave já conhecida (ex.: vinda do `Externo` do tickets.md) como `EPICO=<chave>`
            literal, e as filhas seguem usando `--parent "$EPICO"`. Idempotência do épico
            (delta-017, correção pós-review): reexportar não deve duplicar o épico no Jira.
        capturar_chaves: se True, cada create de filha vira `<ID>_KEY=$(... --json | ...)`
            em vez de um `--json` solto — usado pelo tickets.py (T3) para depois emitir
            `acli jira workitem link` entre as chaves capturadas (arestas `dep:`)
        epico_labels: etiquetas do épico recém-criado (só usado com `epico`). Achado da
            validação real (delta-017/T7): sem etiqueta, o `acli jira workitem search
            --jql "... AND labels=delta:NNN"` documentado para a volta (R3) nunca devolve
            o épico, e o achado "épico aberto com delta arquivada" fica inalcançável na
            prática — só o selftest sintético cobria o caso.

    Returns:
        Path do tickets-acli.sh gerado
    """
    linhas = ["#!/usr/bin/env bash",
              "# Emitido por projecao.py — revise antes de executar (R52: quem executa é a skill).",
              "set -euo pipefail", ""]
    if epico:
        rotulos_epico = f" --label {shlex.quote(','.join(epico_labels))}" if epico_labels else ""
        linhas += [f"EPICO=$(acli jira workitem create --project {shlex.quote(projeto)} "
                   f"--type {TIPO_EPICO} --summary {shlex.quote(epico)}{rotulos_epico} --json "
                   "| python3 -c 'import json,sys; print(json.load(sys.stdin)[\"key\"])')",
                   'echo "épico criado: $EPICO"', ""]
    elif epico_existente:
        linhas += [f"EPICO={shlex.quote(epico_existente)}",
                   'echo "épico reaproveitado: $EPICO"', ""]
    for i in itens:
        # Dois arquivos por item: o `.md` é a fonte legível (byte-idêntica ao DEBT.md,
        # conferível a olho antes de rodar); o `.adf.json` é o que o acli consome — ele
        # aceita texto puro ou ADF, nunca Markdown (delta-034).
        corpo = saida / f"corpo-{i['id']}.md"
        corpo.write_text(i["body"], encoding="utf-8")
        corpo_adf = saida / f"corpo-{i['id']}.adf.json"
        corpo_adf.write_text(json.dumps(converter(i["body"]), ensure_ascii=False),
                             encoding="utf-8")
        rotulos = f" --label {shlex.quote(','.join(i['labels']))}" if i["labels"] else ""
        pai = ' --parent "$EPICO"' if (epico or epico_existente) else ""
        comando = (f"acli jira workitem create --project {shlex.quote(projeto)} "
                   f"--type {TIPO_ITEM} --summary {shlex.quote(i['title'])}{rotulos}"
                   f"{pai} --description-file {shlex.quote(str(corpo_adf))} --json")
        if capturar_chaves:
            var = f"{nome_var(i['id'])}_KEY"
            linhas.append(f"{var}=$({comando} "
                          "| python3 -c 'import json,sys; print(json.load(sys.stdin)[\"key\"])')")
            linhas.append(f'echo "{i["id"]}: ${var}"')
        else:
            linhas.append(comando)
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
        # (c2) o acli lê ADF, não Markdown (delta-034): o `.md` fica como fonte legível,
        # mas quem vai para --description-file é o `.adf.json` — senão a marcação chega
        # literal no ticket, como aconteceu de SBX-11 a SBX-14.
        assert "--description-file" in texto and "corpo-DT-001.md " not in texto, \
            "o .md não pode ir para o acli — ele não interpreta Markdown"
        adf = json.loads((saida / "corpo-DT-001.adf.json").read_text(encoding="utf-8"))
        assert [b["type"] for b in adf["content"]] == \
            ["paragraph", "bulletList", "rule", "paragraph"], "estrutura do corpo perdida"
        assert "**" not in json.dumps(adf) and "---" not in json.dumps(adf), \
            "marcação crua vazou para o ADF"
        sh2 = emitir_sh_acli(itens, "SBX", saida, epico="[delta-017] jira-tickets")
        t2 = sh2.read_text(encoding="utf-8")
        assert t2.index("--type Epic") < t2.index("--type Task")
        assert '--parent "$EPICO"' in t2
        # (e) capturar_chaves=True (T3, delta-017): create de filha vira <ID>_KEY=$(...),
        # sem quebrar o modo default (capturar_chaves=False testado acima).
        sh3 = emitir_sh_acli(itens, "SBX", saida, capturar_chaves=True)
        t3 = sh3.read_text(encoding="utf-8")
        assert "DT_001_KEY=$(acli jira workitem create" in t3
        assert "DT_002_KEY=$(acli jira workitem create" in t3
        assert t3.count("_KEY=$(") == 2 and 'echo "DT-001: $DT_001_KEY"' in t3
        assert "create-bulk" not in t3
        # (f) epico_existente (correção pós-review, delta-017): reexportar não recria o
        # épico — EPICO vira atribuição literal, sem `--type Epic`, filhas com --parent.
        sh4 = emitir_sh_acli(itens, "SBX", saida, epico_existente="SBX-1")
        t4 = sh4.read_text(encoding="utf-8")
        assert "--type Epic" not in t4, "epico_existente não deveria recriar o épico"
        assert "EPICO=SBX-1" in t4 and '--parent "$EPICO"' in t4
        # (g) epico_labels (achado da validação real, delta-017/T7): sem etiqueta o JQL
        # do diff (labels=delta:NNN) nunca acha o épico — "épico aberto com delta
        # arquivada" (R3) fica inalcançável fora do selftest sintético.
        sh5 = emitir_sh_acli(itens, "SBX", saida, epico="[delta-017] jira-tickets",
                             epico_labels=["delta:017"])
        t5 = sh5.read_text(encoding="utf-8")
        assert "--type Epic --summary '[delta-017] jira-tickets' --label delta:017" in t5, \
            "épico com epico_labels deveria carregar --label"
        assert "--label delta:017" not in t2, "épico sem epico_labels não deveria ganhar --label"
    # (h) ler_projeto_jira (delta-035, DT-033): dono único do destino declarado.
    with tempfile.TemporaryDirectory() as td:
        raiz = Path(td)
        assert ler_projeto_jira(raiz) is None, "sem perfil, o destino é o GitHub"
        perfil = raiz / ARQUIVO_PERFIL
        perfil.write_text("motores:\n  jira:\n    projeto: TP\n", encoding="utf-8")
        assert ler_projeto_jira(raiz) == "TP"
        # desligado de todas as formas que um perfil real usa — nenhuma vira projeto
        for desligado in ("motores:\n  jira: false\n", "motores:\n  jira: {}\n",
                          "motores:\n  jira:\n    projeto: ''\n", "motores: {}\n", "{}\n"):
            perfil.write_text(desligado, encoding="utf-8")
            assert ler_projeto_jira(raiz) is None, f"deveria degradar: {desligado!r}"
        # perfil quebrado não derruba a projeção — o DEBT.md vale sozinho (RNF2)
        perfil.write_text("motores:\n  jira: [\n", encoding="utf-8")
        assert ler_projeto_jira(raiz) is None, "YAML inválido deveria degradar, não estourar"
    print("selftest projecao: OK")


if __name__ == "__main__":
    selftest()
