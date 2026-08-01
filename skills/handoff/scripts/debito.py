#!/usr/bin/env python3
"""Fila de dívida técnica do deltaspec — score determinístico e projeção para tickets.

O DEBT.md é a fonte da verdade; ferramenta de ticket é projeção (ADR-0021). Este
script **não acessa a rede**: ele lê o DEBT.md, calcula e emite arquivos. Quem
executa `gh`/`acli` é a skill (mesmo padrão do projeto-infra, que é roteiro sem
script instalável). Política de fila e contrato da projeção: references/debito.md.

  fila      valida, calcula o score e imprime a fila ordenada
  exportar  emite o JSON canônico + dialeto bulk do Jira + linhas de criação do GitHub
  diff      compara o DEBT.md com o estado coletado da ferramenta externa

Score = (juros × probabilidade) / principal, derivado na leitura e **nunca gravado**
(regra de ouro: valor calculado não vira segunda fonte). Ordenação: override,
depois trilha planejada, depois score decrescente.

Uso: debito.py fila [ROOT]
     debito.py exportar [ROOT] [--saida DIR]
     debito.py diff [ROOT] --externo ESTADO.json
     debito.py --selftest
Exit 0 = sem erro · 1 = registro inválido ou divergência · 2 = erro de uso.
"""
import argparse
import json
import re
import shlex
import subprocess
import sys
from collections import Counter
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path

STALE_DIAS = 90  # sem mudança na linha e com juros altos: força decisão explícita
JANELA_CHURN = "6 months ago"  # janela do git log que estima a probabilidade de incidência
PERCENTIL_QUENTE = 0.10  # top 10% dos arquivos mais tocados → probabilidade 9
PERCENTIL_MORNO = 0.40  # top 40% → probabilidade 3; o resto → 1
JUROS_RELEVANTE = 3  # a partir daqui o aging cobra decisão (C do references/debito.md)
FAIXA_ALTA = 9  # limiares de SCORE para a etiqueta de faixa — não confundir com a
FAIXA_MEDIA = 3  # escala dos eixos, que é fechada pelo próprio regex FILA

# Precedência do override: impedimento, não prioridade alta — entra fora da competição por score.
OVERRIDES = ("security", "compliance", "eol", "contract")
NATUREZAS_PONTUAVEIS = ("débito", "pendência")
ESTADOS_ATIVOS = ("aberto", "aceito", "vigente")
ESTADOS_FINAIS = ("quitado", "descartado")
VAZIO = ("", "—", "-")
ROTULO_NATUREZA = {"débito": "debito", "pendência": "pendencia"}  # só o que é pontuável

# `P3·J9·Pr9` com sufixos opcionais ` · trilha` / ` · !security(AAAA-MM-DD)`.
# Ancorada no início: a fila só vale na posição canônica da célula (lição 2026-07-28).
FILA = re.compile(r"^P([139])·J([139])·Pr([139])(?:\s*·\s*(.+))?$")
OVERRIDE = re.compile(r"^!(\w+)\((\d{4}-\d{2}-\d{2})\)$")
DATA = re.compile(r"\d{4}-\d{2}-\d{2}")  # data obrigatória em quitado/descartado (R18)
LINK_MD = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
TRILHA = "trilha"

# Gramática do bloco (delta-024). Todas ancoradas em início de linha: campo citado
# na prosa da descrição não é campo — a lição de 2026-07-28, agora em forma de bloco.
BLOCO = re.compile(r"^###\s+(DT-\d+)\s*·\s*([^·\n]+?)\s*·\s*([^·\n]+?)\s*$", re.M)
TITULO = re.compile(r"^\*\*(.+?)\*\*\s*$", re.M)
CAMPO = re.compile(r"^-\s+\*\*([^:*]+):\*\*\s*(.*)$", re.M)
TABELA_ANTIGA = re.compile(r"^\|\s*DT-\d+\s*\|", re.M)


def die(msg: str) -> None:
    print(f"ERRO: {msg}")
    sys.exit(2)


def parse_blocos(texto: str) -> list:
    """Blocos `### DT-NNN · natureza · estado` como dicionários.

    Cada peça vem de uma âncora de início de linha: o cabeçalho do `###`, o título
    do primeiro `**negrito**` e os campos de `- **Nome:** valor`. Nada é procurado
    por busca solta — prosa que mencione a sintaxe (a palavra "aberto" no meio de
    uma descrição, um `- **Fila:**` citado como exemplo) não pode virar campo. É a
    lição de 2026-07-28, que já custou falsos positivos em três gates diferentes.
    """
    marcas = list(BLOCO.finditer(texto))
    itens = []
    for i, m in enumerate(marcas):
        corpo = texto[m.end():marcas[i + 1].start() if i + 1 < len(marcas) else len(texto)]
        item = {"id": m.group(1), "natureza": m.group(2).strip(), "status": m.group(3).strip()}
        # O título é a primeira linha em negrito; a descrição é o que vem antes do
        # primeiro campo, sem o título — prosa livre, quantas linhas precisar.
        t = TITULO.search(corpo)
        item["título"] = t.group(1).strip() if t else ""
        antes = corpo[:CAMPO.search(corpo).start()] if CAMPO.search(corpo) else corpo
        item["descrição"] = (antes.replace(t.group(0), "", 1) if t else antes).strip()
        for campo, valor in CAMPO.findall(corpo):
            item[campo.strip().lower()] = valor.strip()
        itens.append(item)
    return itens


def estado(item: dict) -> str:
    """Estado do cabeçalho do bloco, normalizado."""
    return item.get("status", "").strip().lower()


def parse_fila(valor: str):
    """(principal, juros, probabilidade, trilha, override) ou None se malformada.

    O vocabulário de override é fechado: `!segurança-com-typo(data)` seria aceito em
    silêncio e rebaixaria um impedimento à prioridade de trilha (achado do review).
    """
    m = FILA.match(valor.strip().strip("`").strip())  # crase é formatação, não conteúdo
    if not m:
        return None
    principal, juros, prob = (int(m.group(i)) for i in (1, 2, 3))
    trilha, override = False, None
    for sufixo in (s.strip() for s in (m.group(4) or "").split("·") if s.strip()):
        if sufixo == TRILHA:
            trilha = True
        elif (mo := OVERRIDE.match(sufixo)) and mo.group(1) in OVERRIDES:
            override = mo.groups()
        else:
            return None
    return principal, juros, prob, trilha, override


def precedencia(entrada: dict) -> int:
    """Posição na fila antes do score: override (na ordem do enum) < trilha < resto."""
    if entrada["override"]:
        return OVERRIDES.index(entrada["override"][0])
    return len(OVERRIDES) if entrada["trilha"] else len(OVERRIDES) + 1


def score(principal: int, juros: int, prob: int) -> float:
    """Função pura: juros × probabilidade, amortizado pelo custo de pagar."""
    return (juros * prob) / principal


def pontuavel(item: dict) -> bool:
    return (item.get("natureza", "") in NATUREZAS_PONTUAVEIS
            and estado(item) in ESTADOS_ATIVOS)


def validar(itens: list, root: Path) -> list:
    """Erros bloqueantes: sem eles a fila mentiria. Um erro por (item, campo)."""
    erros = []
    for item in itens:
        ident, st = item.get("id", "?"), estado(item)
        if st not in ESTADOS_ATIVOS + ESTADOS_FINAIS:
            erros.append(f"{ident}: status '{st or 'vazio'}' fora do conjunto "
                         f"{', '.join(ESTADOS_ATIVOS + ESTADOS_FINAIS)}")
            continue
        if st == "aceito" and item.get("gatilho", "") in VAZIO:
            erros.append(f"{ident}: estado 'aceito' exige o campo Gatilho (reavaliação)")
        if st in ESTADOS_FINAIS and not DATA.search(item.get("encerrado", "")):
            erros.append(f"{ident}: estado '{st}' exige o campo Encerrado com data e ref — R18")
        if item.get("natureza") == "guarda" and item.get("fila", "") not in VAZIO:
            erros.append(f"{ident}: guarda não tem principal nem juros — não declare Fila")
        if not pontuavel(item):
            continue
        if item.get("título", "") in VAZIO:
            erros.append(f"{ident}: título vazio — o ticket precisa de um sintoma observável")
        if item.get("gatilho", "") in VAZIO:
            erros.append(f"{ident}: campo Gatilho ausente — sem ele o item nunca é reavaliado")
        local = item.get("local", "")
        if local in VAZIO:
            erros.append(f"{ident}: campo Local ausente — dívida sem localização não é acionável")
        else:
            for alvo in LINK_MD.findall(local):
                if not (root / alvo.split("#")[0]).exists():
                    erros.append(f"{ident}: 'Local' aponta caminho inexistente — {alvo}")
        if not parse_fila(item.get("fila", "")):
            erros.append(f"{ident}: 'Fila' malformada — esperado P{{1|3|9}}·J{{1|3|9}}·Pr{{1|3|9}}")
    return erros


def git(root: Path, *args):
    """stdout do git, ou None quando não há git/histórico — degrada como o C7."""
    try:
        r = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    except (FileNotFoundError, OSError):
        return None
    return r.stdout if r.returncode == 0 else None


@lru_cache(maxsize=None)
def churn(root: Path):
    """{caminho: commits na janela} — proxy objetivo da probabilidade de incidência.

    Em cache: o `git log` varre o repositório inteiro e o relatório o consulta por item.
    """
    saida = git(root, "log", f"--since={JANELA_CHURN}", "--name-only", "--pretty=format:")
    if saida is None:
        return None
    return Counter(l.strip() for l in saida.splitlines() if l.strip())


def prob_do_churn(caminho: str, contagem):
    """Percentil do arquivo no ranking de churn → escala do eixo (1, 3 ou 9)."""
    if not contagem:
        return None
    if caminho not in contagem:
        return 1
    ranking = [c for c, _ in contagem.most_common()]
    posicao = ranking.index(caminho) / len(ranking)
    return 9 if posicao < PERCENTIL_QUENTE else 3 if posicao < PERCENTIL_MORNO else 1


def dias_parado(root: Path, ident: str, hoje: date):
    """Dias desde a última mudança no **cabeçalho** do item — base do 'stale'.

    O ID só aparece na linha `### DT-NNN · natureza · estado`, então `-G` casa
    exatamente as mudanças de estado e natureza — que é o que "parado" quer dizer:
    editar a prosa da descrição não é decidir, e não deve reiniciar o relógio.
    (`-G` e não `-S`: o pickaxe só conta quando a string passa a existir ou some.)
    """
    saida = git(root, "log", "-1", "--format=%cs", "-G", ident, "--", "DEBT.md")
    if not saida or not saida.strip():
        return None
    try:
        return (hoje - datetime.strptime(saida.strip(), "%Y-%m-%d").date()).days
    except ValueError:
        return None


def alvo_local(item: dict) -> str:
    """Caminho do artefato apontado em 'Local' (primeiro link, sem âncora)."""
    achados = LINK_MD.findall(item.get("local", ""))
    return achados[0].split("#")[0] if achados else ""


def montar_fila(itens: list, root: Path, hoje=None) -> list:
    """Itens pontuáveis, ordenados: override, trilha, score desc. Score não é persistido."""
    hoje = hoje or date.today()
    contagem = churn(root)
    fila = []
    for item in itens:
        if not pontuavel(item):
            continue
        principal, juros, prob, trilha, override = parse_fila(item["fila"])
        derivada = prob_do_churn(alvo_local(item), contagem)
        parado = dias_parado(root, item["id"], hoje)
        fila.append({
            "item": item, "principal": principal, "juros": juros, "prob": prob,
            "trilha": trilha, "override": override,
            "score": score(principal, juros, prob),
            "prob_derivada": derivada,
            "stale": bool(parado is not None and parado > STALE_DIAS and juros >= JUROS_RELEVANTE),
        })
    fila.sort(key=lambda f: (precedencia(f), -f["score"]))
    return fila


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
    faixa = ("alta" if entrada["score"] >= FAIXA_ALTA
             else "media" if entrada["score"] >= FAIXA_MEDIA else "baixa")
    marcas = [f"dt:{item['id']}", f"deltaspec:{ROTULO_NATUREZA[item['natureza']]}", f"fila:{faixa}"]
    if entrada["trilha"]:
        marcas.append("fila:trilha")
    if entrada["override"]:
        marcas.append(f"fila:override-{entrada['override'][0]}")
    return marcas


def canonico(fila: list) -> dict:
    """JSON canônico — contrato único que alimenta os dois dialetos."""
    itens = []
    for entrada in fila:
        item = entrada["item"]
        ticket = item.get("ticket", "")
        itens.append({
            "id": item["id"],
            "title": f"[{item['id']}] {item.get('título', '')}",
            "body": corpo_ticket(item, entrada),
            "labels": etiquetas(item, entrada),
            "score": round(entrada["score"], 2),
            "fila": {"principal": entrada["principal"], "juros": entrada["juros"],
                     "probabilidade": entrada["prob"], "trilha": entrada["trilha"],
                     "override": entrada["override"][0] if entrada["override"] else None,
                     "prazo": entrada["override"][1] if entrada["override"] else None},
            "externo": None if ticket in VAZIO else ticket,
        })
    return {"version": 1, "source": "DEBT.md", "items": itens}


def carregar(root: Path):
    """Itens válidos do DEBT.md, ou None quando há erro (já reportado).

    Registro no formato de tabela (delta-023 e anteriores, incluindo o template ainda
    distribuído pelo projeto-init) devolve lista vazia com instrução de conversão: o
    arquivo continua valendo como registro, só a fila não é calculável sobre ele.
    """
    texto = (root / "DEBT.md").read_text(encoding="utf-8")
    itens = parse_blocos(texto)
    if not itens and TABELA_ANTIGA.search(texto):
        print("Registro em formato de tabela (anterior à delta-024) — o arquivo vale como "
              "registro, mas a fila precisa dos blocos `### DT-NNN · natureza · estado`. "
              "Gramática em skills/handoff/references/debito.md.")
        return []
    erros = validar(itens, root)
    for e in erros:
        print(f"[inválido] {e}")
    return None if erros else itens


def exportar(root: Path, saida: Path, projeto: str = "") -> int:
    itens = carregar(root)
    if itens is None:
        return 1
    dados = canonico(montar_fila(itens, root))
    saida.mkdir(parents=True, exist_ok=True)
    (saida / "tickets.json").write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n",
                                        encoding="utf-8")
    # Dialeto do `acli jira workitem create-bulk --from-json` (campos flat). Só é
    # emitido com a chave do projeto: sem `projectKey` o acli recusa o lote, e emitir
    # um payload que não roda seria pior que não emitir (achado do review).
    if projeto:
        bulk = {"issues": [{"summary": i["title"], "projectKey": projeto, "issueType": "Task",
                            "description": i["body"], "label": i["labels"]}
                           for i in dados["items"] if not i["externo"]]}
        (saida / "tickets-acli.json").write_text(
            json.dumps(bulk, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    linhas = ["#!/usr/bin/env bash",
              "# Emitido por debito.py — revise antes de executar. Itens já projetados são pulados.",
              "# Rode a partir da raiz do repositório: o gh resolve o repo pelo diretório corrente.",
              "set -euo pipefail", "",
              "# Etiquetas primeiro — `gh issue create` falha se a etiqueta não existir.",
              "# Idempotente: recriar uma etiqueta existente é erro, e aqui ele é inofensivo."]
    for rotulo in sorted({r for i in dados["items"] if not i["externo"] for r in i["labels"]}):
        linhas.append(f"gh label create {shlex.quote(rotulo)} "
                      f"--description {shlex.quote('Projeção do DEBT.md (ADR-0021)')} 2>/dev/null || true")
    linhas.append("")
    for i in dados["items"]:
        if i["externo"]:
            linhas.append(f"# {i['id']} já projetado em {i['externo']} — pulando")
            continue
        rotulos = " ".join(f"--label {shlex.quote(l)}" for l in i["labels"])
        linhas += [f"gh issue create --title {shlex.quote(i['title'])} {rotulos} "
                   f"--body-file - <<'CORPO_{i['id'].replace('-', '_')}'",
                   i["body"], f"CORPO_{i['id'].replace('-', '_')}", ""]
    (saida / "tickets-gh.sh").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    pendentes = sum(1 for i in dados["items"] if not i["externo"])
    print(f"{len(dados['items'])} item(ns) na fila · {pendentes} sem projeção · saída em {saida}")
    if not projeto:
        print("> Dialeto do Jira omitido: informe --projeto CHAVE para gerar o lote do acli.")
    return 0


def diff(root: Path, externo: Path) -> int:
    """DEBT.md × estado da ferramenta: tabela de divergências (formato do R27).

    Só reporta. A atualização do DEBT.md é proposta ao usuário e aplicada por ele —
    a ferramenta externa nunca sobrescreve a fonte (ADR-0021).
    """
    itens = parse_blocos((root / "DEBT.md").read_text(encoding="utf-8"))
    try:  # fronteira de confiança: o arquivo vem de fora, coletado à mão pela skill
        tickets = json.loads(externo.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as erro:
        die(f"não consegui ler {externo}: {erro}")
    if not isinstance(tickets, list):
        die(f"{externo} deveria ser a lista JSON do `gh issue list --json ...`")
    por_id = {}
    for t in tickets:
        for rotulo in t.get("labels", []):
            nome = rotulo.get("name", "") if isinstance(rotulo, dict) else str(rotulo)
            if nome.startswith("dt:"):
                por_id[nome[3:]] = t
    linhas = []
    for item in itens:
        ident, st = item["id"], estado(item)
        ticket = por_id.get(ident)
        if pontuavel(item) and not ticket:
            linhas.append((ident, f"{st}, sem chave externa", "sem ticket",
                           "dívida invisível para quem acompanha pela ferramenta",
                           "projetar com `exportar` + criar o ticket"))
        elif ticket and ticket.get("state", "").upper() == "CLOSED" and st in ESTADOS_ATIVOS:
            linhas.append((ident, f"status '{st}'", f"ticket #{ticket.get('number')} fechado",
                           "alguém deu a dívida por resolvida fora do repo",
                           "confirmar e quitar/descartar no DEBT.md, ou reabrir o ticket"))
        elif ticket and ticket.get("state", "").upper() == "OPEN" and st in ESTADOS_FINAIS:
            linhas.append((ident, f"status '{st}'", f"ticket #{ticket.get('number')} aberto",
                           "ticket órfão continua cobrando trabalho já encerrado",
                           "fechar o ticket citando a quitação"))
    conhecidos = {i["id"] for i in itens}
    for ident, ticket in sorted(por_id.items()):
        if ident not in conhecidos:
            linhas.append((ident, "não existe", f"ticket #{ticket.get('number')}",
                           "trabalho rastreado fora do registro canônico",
                           "abrir DT-NNN no DEBT.md ou fechar o ticket"))
    print(f"# Divergências DEBT.md × ferramenta externa · {len(linhas)} achado(s)\n")
    if not linhas:
        print("Nenhuma divergência: o registro e a projeção estão em sincronia.")
        return 0
    print("| ID | DEBT.md diz | Ferramenta diz | Impacto | Ação proposta |")
    print("|---|---|---|---|---|")
    for l in linhas:
        print("| " + " | ".join(l) + " |")
    print("\n> Proposta, não aplicação: nada é gravado no DEBT.md sem sua aprovação (ADR-0021).")
    return 1


def cmd_fila(root: Path, hoje=None) -> int:
    itens = carregar(root)
    if itens is None:
        return 1
    if not itens:
        return 0  # formato antigo ou registro vazio: carregar() já explicou
    fila = montar_fila(itens, root, hoje)
    print(f"# Fila de dívida — {len(fila)} item(ns) pontuável(is)\n")
    print("| # | ID | Score | Fila | Título | Marcas |")
    print("|---|---|---|---|---|---|")
    for n, e in enumerate(fila, 1):
        marcas = []
        if e["override"]:
            marcas.append(f"**override {e['override'][0]}** (prazo {e['override'][1]})")
        if e["trilha"]:
            marcas.append("trilha planejada")
        if e["stale"]:
            marcas.append(f"**stale** (>{STALE_DIAS}d sem mudança)")
        if e["prob_derivada"] and e["prob_derivada"] != e["prob"]:
            marcas.append(f"churn sugere Pr{e['prob_derivada']}")
        print(f"| {n} | {e['item']['id']} | {e['score']:.2f} | {e['item']['fila']} "
              f"| {e['item'].get('título', '')} | {' · '.join(marcas) or '—'} |")
    if churn(root) is None:
        print("\n> Aviso: sem git — a probabilidade declarada vale, sem conferência por churn.")
    return 0


def main() -> None:
    if "--selftest" in sys.argv[1:]:
        selftest()
        return
    p = argparse.ArgumentParser(description="Fila de dívida técnica e projeção para tickets.")
    p.add_argument("comando", choices=("fila", "exportar", "diff"))
    p.add_argument("root", nargs="?", default=".", help="raiz do repositório (default: .)")
    p.add_argument("--saida", help="diretório dos arquivos de importação (exportar)")
    p.add_argument("--projeto", default="", help="chave do projeto Jira (exportar)")
    p.add_argument("--externo", help="JSON do `gh issue list --json ...` (diff)")
    a = p.parse_args()
    root = Path(a.root).resolve()
    if not (root / "DEBT.md").is_file():
        die(f"DEBT.md não encontrado em {root}")
    if a.comando == "fila":
        sys.exit(cmd_fila(root))
    if a.comando == "exportar":
        sys.exit(exportar(root, Path(a.saida) if a.saida else root / "docs" / "tickets", a.projeto))
    if not a.externo:
        die("diff exige --externo ESTADO.json (saída de `gh issue list --json ...`)")
    sys.exit(diff(root, Path(a.externo)))


# ---------------------------------------------------------------- selftest


CABECALHO_FIXTURE = "# DEBT.md\n\n## Registro\n\n"


def linha(ident, natureza="débito", titulo="Título curto", local="[alvo](alvo.py)",
          fila="P3·J9·Pr9", gatilho="quando doer", status="aberto", externo="",
          descricao="descrição do sintoma", encerrado=""):
    """Um bloco de fixture. Campo com valor vazio simplesmente não é declarado —
    é assim que guarda e item encerrado se distinguem de item ativo incompleto."""
    campos = [("Fila", fila), ("Local", local), ("Gatilho", gatilho),
              ("Origem", "[PR #1](../../pull/1) · 2026-01-01"),
              ("Ticket", externo), ("Encerrado", encerrado)]
    corpo = "".join(f"- **{nome}:** {valor}\n" for nome, valor in campos if valor)
    return f"### {ident} · {natureza} · {status}\n**{titulo}**\n\n{descricao}\n\n{corpo}\n"


def selftest() -> None:
    import ast
    import contextlib
    import io
    import tempfile

    def quieto(fn, *args, **kwargs):
        """Roda um subcomando engolindo a saída — o selftest reporta o próprio veredito."""
        with contextlib.redirect_stdout(io.StringIO()):
            return fn(*args, **kwargs)

    def montar(linhas: str, com_alvo=True):
        d = tempfile.mkdtemp()
        root = Path(d)
        (root / "DEBT.md").write_text(CABECALHO_FIXTURE + linhas, encoding="utf-8")
        if com_alvo:
            (root / "alvo.py").write_text("x = 1\n", encoding="utf-8")
        return root

    # score: função pura, sem I/O
    assert score(3, 9, 9) == 27.0 and score(9, 3, 1) == (1 / 3), "fórmula do score mudou"
    assert score(1, 1, 1) == 1.0 and round(score(9, 1, 1), 2) == 0.11, "faixa do score mudou"

    # parse da fila e dos sufixos
    assert parse_fila("P3·J9·Pr9") == (3, 9, 9, False, None)
    assert parse_fila("`P3·J9·Pr9`") == (3, 9, 9, False, None), "crase de formatação quebrou a fila"
    assert parse_fila("P9·J3·Pr9 · trilha")[3] is True
    assert parse_fila("P1·J1·Pr1 · !security(2026-09-01)")[4] == ("security", "2026-09-01")
    for ruim in ("P2·J9·Pr9", "P3-J9-Pr9", "", "P3·J9", "P3·J9·Pr9 · bagunça",
                 "P3·J9·Pr9 · !secutiry(2026-09-01)"):  # typo em 'security' não pode passar
        assert parse_fila(ruim) is None, f"fila malformada aceita: {ruim!r}"

    # precedência: cada override na ordem do enum, depois trilha, depois o resto
    def entrada(trilha=False, override=None):
        return {"trilha": trilha, "override": override}
    ordem_prec = [precedencia(entrada(override=(o, "2026-01-01"))) for o in OVERRIDES]
    assert ordem_prec == sorted(ordem_prec) and len(set(ordem_prec)) == len(OVERRIDES), \
        f"overrides não respeitam a ordem do enum: {ordem_prec}"
    assert max(ordem_prec) < precedencia(entrada(trilha=True)) < precedencia(entrada()), \
        "override deve vir antes de trilha, e trilha antes do resto"

    # registro limpo passa; guarda sem Fila/Local também
    root = montar(linha("DT-001") + linha("DT-002", natureza="guarda", local="", fila="", status="vigente"))
    itens = parse_blocos((root / "DEBT.md").read_text(encoding="utf-8"))
    assert len(itens) == 2, f"parser perdeu bloco: {itens}"
    assert validar(itens, root) == [], f"fixture limpa acusada: {validar(itens, root)}"
    assert itens[0]["descrição"] == "descrição do sintoma", f"descrição mal recortada: {itens[0]}"

    # REGRESSÃO (lição 2026-07-28): a descrição menciona a palavra 'aberto' e cita a
    # própria sintaxe de campo. Busca solta leria o item como ativo e o `- **Fila:**`
    # da prosa como fila real; só a âncora de início de linha do bloco separa os dois.
    prosa = linha("DT-003", local="", fila="", status="quitado",
                  encerrado="2026-07-31 · [#85](../../pull/85) — ficou aberto 7 dias após satisfeito",
                  descricao="A dívida seguia aberto no papel. Exemplo citado: `- **Fila:** P9·J9·Pr9`.")
    root_p = montar(prosa)
    itens_p = parse_blocos((root_p / "DEBT.md").read_text(encoding="utf-8"))
    assert estado(itens_p[0]) == "quitado", f"prosa enganou o estado: {estado(itens_p[0])}"
    assert itens_p[0].get("fila", "") == "", "sintaxe citada na prosa virou campo Fila"
    assert validar(itens_p, root_p) == [], "item quitado com prosa foi cobrado como ativo"
    assert montar_fila(itens_p, root_p) == [], "item quitado entrou na fila"

    # o bloco aceita descrição de várias linhas e caractere que a tabela exigia escapar
    multi = linha("DT-004", titulo="Pipe | e travessão — livres no bloco",
                  descricao="Primeira linha da descrição.\n\nSegundo parágrafo, com `código` e | pipe.")
    itens_multi = parse_blocos(multi)
    assert itens_multi[0]["título"] == "Pipe | e travessão — livres no bloco"
    assert "Segundo parágrafo" in itens_multi[0]["descrição"], "descrição multilinha truncada"

    # validações bloqueantes, uma por campo
    casos = {
        "título": linha("DT-010", titulo=""),
        "Local": linha("DT-011", local=""),
        "Fila": linha("DT-012", fila="P2·J2·Pr2"),
        "Gatilho": linha("DT-013", status="aceito", gatilho=""),
    }
    for campo_esperado, fixture in casos.items():
        r = montar(fixture)
        erros = validar(parse_blocos((r / "DEBT.md").read_text(encoding="utf-8")), r)
        assert any(campo_esperado in e for e in erros), f"{campo_esperado} não acusado: {erros}"
        assert all(e.startswith("DT-") for e in erros), f"erro sem o DT-NNN: {erros}"
    r_morto = montar(linha("DT-014", local="[x](nao-existe.py)"))
    assert any("inexistente" in e for e in
               validar(parse_blocos((r_morto / "DEBT.md").read_text(encoding="utf-8")), r_morto)), \
        "link morto no Local não acusado"
    r_estado = montar(linha("DT-015", status="pendente"))
    assert any("fora do conjunto" in e for e in
               validar(parse_blocos((r_estado / "DEBT.md").read_text(encoding="utf-8")), r_estado)), \
        "status inventado não acusado"
    r_guarda = montar(linha("DT-016", natureza="guarda", status="vigente", fila="P1·J1·Pr1"))
    assert any("guarda" in e for e in
               validar(parse_blocos((r_guarda / "DEBT.md").read_text(encoding="utf-8")), r_guarda)), \
        "guarda com fila preenchida não acusada"
    r_sem_data = montar(linha("DT-017", local="", fila="", status="quitado"))
    assert any("Encerrado" in e for e in
               validar(parse_blocos((r_sem_data / "DEBT.md").read_text(encoding="utf-8")), r_sem_data)), \
        "quitado sem o campo Encerrado não acusado (R18 exige data e ref)"

    # os cinco estados válidos convivem; só o pontuável exige os campos novos
    r_estados = montar(
        linha("DT-050", status="aberto")
        + linha("DT-051", status="aceito", gatilho="quando o motor mudar")
        + linha("DT-052", natureza="guarda", local="", fila="", status="vigente")
        + linha("DT-053", local="", fila="", status="descartado", encerrado="2026-08-01 — virou obsoleto")
        + linha("DT-054", local="", fila="", status="quitado", encerrado="2026-08-01 · [#99](../../issues/99)"))
    itens_e = parse_blocos((r_estados / "DEBT.md").read_text(encoding="utf-8"))
    assert validar(itens_e, r_estados) == [], f"estados válidos acusados: {validar(itens_e, r_estados)}"
    assert {e["item"]["id"] for e in montar_fila(itens_e, r_estados)} == {"DT-050", "DT-051"}, \
        "só item ativo e pontuável entra na fila"

    # registro em tabela (delta-023 ou o template ainda distribuído): avisa, não quebra
    legado_txt = ("## Registro\n\n| ID | Natureza | Descrição | Origem | Aberto em "
                  "| Gatilho de correção | Status |\n|---|---|---|---|---|---|---|\n"
                  "| DT-001 | débito | x | PR #1 | 2026-01-01 | quando doer | aberto |\n")
    r_legado = Path(tempfile.mkdtemp())
    (r_legado / "DEBT.md").write_text(legado_txt, encoding="utf-8")
    assert parse_blocos(legado_txt) == [], "tabela não deveria produzir bloco"
    aviso = io.StringIO()
    with contextlib.redirect_stdout(aviso):
        assert carregar(r_legado) == [], "formato antigo deveria devolver lista vazia"
        assert cmd_fila(r_legado) == 0, "cmd_fila não degradou com registro em tabela"
    assert "formato de tabela" in aviso.getvalue(), "faltou instruir a conversão do formato antigo"

    # ordenação: override → trilha → score desc
    root_o = montar(
        linha("DT-020", fila="P1·J1·Pr1")                                # score 1
        + linha("DT-021", fila="P3·J9·Pr9")                              # score 27
        + linha("DT-022", fila="P9·J9·Pr9 · trilha")                     # trilha
        + linha("DT-023", fila="P9·J1·Pr1 · !contract(2026-12-01)")      # override tardio
        + linha("DT-024", fila="P9·J1·Pr1 · !security(2026-09-01)"))     # override primeiro
    ordem = [e["item"]["id"] for e in montar_fila(itens=parse_blocos(
        (root_o / "DEBT.md").read_text(encoding="utf-8")), root=root_o)]
    assert ordem == ["DT-024", "DT-023", "DT-022", "DT-021", "DT-020"], f"ordem errada: {ordem}"

    # exportar: três arquivos, JSON válido, item já projetado é pulado
    root_e = montar(linha("DT-030") + linha("DT-031", externo="[#7](../../issues/7)"))
    saida = root_e / "out"
    assert quieto(exportar, root_e, saida, "PROJ") == 0
    dados = json.loads((saida / "tickets.json").read_text(encoding="utf-8"))
    assert len(dados["items"]) == 2 and dados["version"] == 1
    assert dados["items"][0]["title"].startswith("[DT-0"), "título sem o ID como prefixo"
    assert any(l == "dt:DT-030" for l in dados["items"][0]["labels"]), "etiqueta de idempotência ausente"
    bulk = json.loads((saida / "tickets-acli.json").read_text(encoding="utf-8"))
    assert len(bulk["issues"]) == 1, "item já projetado entrou no bulk do Jira"
    assert bulk["issues"][0]["projectKey"] == "PROJ", "lote do Jira sem chave de projeto não roda"
    sem_projeto = root_e / "out2"
    assert quieto(exportar, root_e, sem_projeto) == 0
    assert not (sem_projeto / "tickets-acli.json").exists(), \
        "sem --projeto o dialeto do Jira deve ser omitido, não emitido quebrado"
    # O módulo não fala com a rede. A checagem lê a árvore sintática, não o texto:
    # uma busca por "import urllib" acharia a própria lista de proibidos abaixo — a
    # lição de 2026-07-28 pegando este selftest pela segunda vez.
    arvore = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    importados = {alias.name.split(".")[0] for no in ast.walk(arvore)
                  if isinstance(no, ast.Import) for alias in no.names}
    importados |= {no.module.split(".")[0] for no in ast.walk(arvore)
                   if isinstance(no, ast.ImportFrom) and no.module}
    rede = importados & {"urllib", "http", "socket", "requests", "httpx", "ftplib", "asyncio"}
    assert not rede, f"módulo passou a acessar a rede: {rede}"
    sh = (saida / "tickets-gh.sh").read_text(encoding="utf-8")
    assert "gh issue create" in sh and "DT-031 já projetado" in sh, "roteiro do gh incorreto"
    # Comando só conta na posição canônica (início da linha, fora de comentário): o
    # próprio roteiro cita 'gh issue create' num comentário, e busca solta acharia
    # ele primeiro — a lição de 2026-07-28 reincidindo dentro do próprio selftest.
    comandos = [l for l in sh.splitlines() if l and not l.lstrip().startswith("#")]
    pos_label = next(i for i, l in enumerate(comandos) if l.startswith("gh label create"))
    pos_issue = next(i for i, l in enumerate(comandos) if l.startswith("gh issue create"))
    assert pos_label < pos_issue, "etiqueta precisa ser criada antes do issue — senão o gh recusa"
    assert "dt:DT-031" not in sh, "etiqueta de item já projetado entrou no roteiro"
    assert (root_e / "DEBT.md").read_text(encoding="utf-8").find("score") == -1, \
        "score foi persistido no DEBT.md"

    # diff: os três casos de divergência + o caso limpo
    estado_ext = root_e / "estado.json"
    estado_ext.write_text(json.dumps([
        {"number": 7, "state": "CLOSED", "labels": [{"name": "dt:DT-031"}]},
        {"number": 9, "state": "OPEN", "labels": [{"name": "dt:DT-099"}]},
    ]), encoding="utf-8")
    saida_diff = io.StringIO()
    with contextlib.redirect_stdout(saida_diff):
        codigo = diff(root_e, estado_ext)
    relatorio = saida_diff.getvalue()
    assert codigo == 1, "diff não acusou divergências"
    for esperado in ("DT-030", "DT-031", "DT-099"):
        assert esperado in relatorio, f"diff não cobriu o caso de {esperado}"
    antes = (root_e / "DEBT.md").read_text(encoding="utf-8")
    quieto(diff, root_e, estado_ext)
    assert (root_e / "DEBT.md").read_text(encoding="utf-8") == antes, "diff alterou o DEBT.md"
    # caso limpo: item projetado e ticket aberto do outro lado → zero divergência
    root_ok = montar(linha("DT-060", externo="[#1](../../issues/1)"))
    sincronizado = root_ok / "estado.json"
    sincronizado.write_text(json.dumps(
        [{"number": 1, "state": "OPEN", "labels": [{"name": "dt:DT-060"}]}]), encoding="utf-8")
    limpo = io.StringIO()
    with contextlib.redirect_stdout(limpo):
        codigo_limpo = diff(root_ok, sincronizado)
    assert codigo_limpo == 0, "diff acusou divergência em registro sincronizado"
    assert "Nenhuma divergência" in limpo.getvalue(), "diff limpo não reportou sincronia"

    print("selftest: OK (score, parser posicional, regressão de prosa, validações, ordem, exportar, diff)")
    selftest_git()


def selftest_git() -> None:
    """Churn e stale com repositório git real — padrão do selftest_c7 do check_cycle."""
    import os
    import tempfile

    try:
        subprocess.run(["git", "--version"], check=True, capture_output=True)
    except (FileNotFoundError, OSError):
        print("selftest git: PULADO (git indisponível)")
        return
    # git presente: daqui em diante toda falha é ruidosa — PULADO não mascara regressão
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)

        def g(*args, quando=None):
            """`--date` só move a data do autor; o stale lê a do committer (%cs),
            que é a que sobrevive ao squash da main — por isso o fixture fixa as duas."""
            env = {**os.environ, "GIT_COMMITTER_DATE": quando, "GIT_AUTHOR_DATE": quando} if quando else None
            subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, env=env)

        g("init", "-q", "-b", "main")
        g("config", "user.email", "selftest@deltaspec")
        g("config", "user.name", "selftest")
        (root / "quente.py").write_text("x = 1\n", encoding="utf-8")
        (root / "frio.py").write_text("y = 1\n", encoding="utf-8")
        (root / "DEBT.md").write_text(
            CABECALHO_FIXTURE
            + linha("DT-040", titulo="Item quente", local="[q](quente.py)", fila="P3·J9·Pr1")
            + linha("DT-041", titulo="Item frio", local="[f](frio.py)", fila="P3·J9·Pr9"),
            encoding="utf-8")
        g("add", "-A")
        g("commit", "-qm", "base", quando="2020-01-01T00:00:00")
        for i in range(5):  # quente.py acumula churn; frio.py não é mais tocado
            (root / "quente.py").write_text(f"x = {i}\n", encoding="utf-8")
            g("add", "-A")
            g("commit", "-qm", f"toca quente {i}")

        contagem = churn(root)
        assert contagem is not None, "churn devolveu None com git presente"
        assert contagem["quente.py"] > contagem["frio.py"], f"churn não ordenou: {contagem}"
        assert prob_do_churn("quente.py", contagem) == 9, "arquivo mais tocado não virou Pr9"
        assert prob_do_churn("nunca-tocado.py", contagem) == 1, "arquivo ausente não virou Pr1"

        itens = parse_blocos((root / "DEBT.md").read_text(encoding="utf-8"))
        fila = montar_fila(itens, root, hoje=date(2020, 1, 2))
        derivadas = {e["item"]["id"]: e["prob_derivada"] for e in fila}
        assert derivadas["DT-040"] == 9, f"divergência de churn não detectada: {derivadas}"
        assert not any(e["stale"] for e in fila), "stale marcado no dia seguinte ao commit"

        # o mesmo registro, avaliado muito depois: juros altos e linha parada → stale
        tarde = montar_fila(itens, root, hoje=date(2021, 1, 1))
        assert all(e["stale"] for e in tarde), f"stale não marcado após {STALE_DIAS} dias"

        # editar só a prosa NÃO é decidir: o relógio do stale não pode reiniciar
        texto = (root / "DEBT.md").read_text(encoding="utf-8")
        (root / "DEBT.md").write_text(texto.replace("**Item quente**", "**Item quente revisado**"),
                                      encoding="utf-8")
        g("add", "-A")
        g("commit", "-qm", "reescreve o título do DT-040", quando="2020-12-31T00:00:00")
        churn.cache_clear()  # o cache é por root; o repo mudou dentro do mesmo processo
        so_prosa = {e["item"]["id"]: e["stale"]
                    for e in montar_fila(parse_blocos((root / "DEBT.md").read_text(encoding="utf-8")),
                                         root, hoje=date(2021, 1, 1))}
        assert so_prosa["DT-040"] is True, "editar prosa reiniciou o relógio de decisão"

        # mudar o ESTADO no cabeçalho é decidir: aí sim o stale sai
        texto = (root / "DEBT.md").read_text(encoding="utf-8")
        (root / "DEBT.md").write_text(texto.replace("### DT-040 · débito · aberto",
                                                    "### DT-040 · débito · aceito"), encoding="utf-8")
        g("add", "-A")
        g("commit", "-qm", "aceita o DT-040", quando="2020-12-31T00:00:00")
        churn.cache_clear()
        depois = {e["item"]["id"]: e["stale"]
                  for e in montar_fila(parse_blocos((root / "DEBT.md").read_text(encoding="utf-8")),
                                       root, hoje=date(2021, 1, 1))}
        assert depois["DT-040"] is False, "stale não sumiu depois da mudança de estado"
        assert depois["DT-041"] is True, "stale de item não tocado sumiu junto"

        sem_git = Path(tempfile.mkdtemp())
        (sem_git / "DEBT.md").write_text(CABECALHO_FIXTURE + linha("DT-050", local="",
                                                                   fila="", natureza="guarda",
                                                                   status="vigente"),
                                         encoding="utf-8")
        assert churn(sem_git) is None, "churn não degradou fora de repositório git"
    print(f"selftest git: OK (churn real, Pr derivada, stale >{STALE_DIAS}d, degradação sem git)")


if __name__ == "__main__":
    main()
