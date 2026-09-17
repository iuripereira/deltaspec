#!/usr/bin/env python3
"""Núcleo puro do painel de abertura de sessão: estado de cada delta, ordem, foco e bancada.

Nada aqui toca disco, rede ou processo — a evidência chega por argumento e sai como dado.
É o que torna o `--selftest` suficiente para esta camada. As REGRAS são deste arquivo; a
SKILL.md aponta para cá e não as reescreve.

Item = delta `SIGLA/NNN`, declarada na fila do projeto (intenção e dependência, nunca status).
PR ou branch ligados à delta: branch com `NNN` como segmento (`feat/NNN-x`, não `dt-NNN`),
título com escopo `(NNN`, ou o campo `branch` do item.

Estado, no primeiro caso que casa:
  1. arquivo_prova na base                       → MERGED (destrava quem depende)
  2. PR aberto                                   → EM REVISÃO
  3. PR mergeado sem prova                       → EM CURSO (archive pendente)
  4. só PRs fechados sem merge                   → DIVERGENTE
  5. branch ligada com commits à frente da base  → EM CURSO
  6. todo depende_de MERGED → PRONTO PRA COMEÇAR; senão BLOQUEADO
Trava = dependência não mergeada de item não MERGED; não muda o estado.

Ordem = topológica (Kahn). Empate: dependentes diretos (desc), ordem de repos da config, id.
Próximo = sem trava antes de com trava; depois o foco; depois DIVERGENTE > EM REVISÃO >
EM CURSO > PRONTO; depois a ordem.

Foco: texto livre vira sigla e só desempata o Próximo — nunca muda estado nem esconde item.

Bancada = worktree e branch local, no primeiro caso que casa: SUJA (mudança não commitada) >
REPRESADA (commits fora da base sem PR aberto) > LIBERÁVEL (nada fora da base, ou HEAD solto).
Branch com PR aberto e worktree na própria base não aparecem. Detalha o repo em foco e as
SUJAS de todos, com teto por repo; o resto vira contagem.

Grafo sai como nós e arestas; o renderizador é fino em cima, para que dois formatos do mesmo
grafo não divirjam.
"""
from __future__ import annotations

import argparse
import datetime as dt
import heapq
import re
import sys

LIMITE_BANCADA = 6
TETO_EMBUTIDO = 20  # acima disto o diagrama embutido deixa de ser legível numa tela
FALLBACK_DIAS = 1

MERGED, REVISAO, CURSO = "MERGED", "EM REVISÃO", "EM CURSO"
PRONTO, BLOQUEADO, DIVERGENTE = "PRONTO PRA COMEÇAR", "BLOQUEADO", "DIVERGENTE"
FORA = "(fora do painel)"
PRIORIDADE = (DIVERGENTE, REVISAO, CURSO, PRONTO)  # fechar antes de começar
LIMPA_FOCO = ("sem", "nenhum", "none", "limpar", "-")
SUJA, REPRESADA, LIBERAVEL = "SUJA", "REPRESADA", "LIBERÁVEL"
PRIORIDADE_BANCADA = (SUJA, REPRESADA, LIBERAVEL)  # trabalho não salvo antes de trabalho parado
PLURAL_BANCADA = {SUJA: "sujas", REPRESADA: "represadas", LIBERAVEL: "liberáveis"}
CLASSE = {MERGED: "merged", REVISAO: "revisao", CURSO: "curso", PRONTO: "pronto",
          BLOQUEADO: "bloqueado", DIVERGENTE: "divergente", FORA: "bloqueado"}
COR = {"merged": "#c8e6c9", "revisao": "#bbdefb", "curso": "#fff9c4",
       "pronto": "#e1bee7", "bloqueado": "#eeeeee", "divergente": "#ffcdd2"}

RE_ID = re.compile(r"^([A-Z]+)/(\d{3})$")
RE_BRANCH_SPEC = re.compile(r"Branch:\**\s*`?([^\s`·*]+)")
RE_TAREFA = re.compile(r"^\s*[-*] \[ \] (.+)$")


# ---------- fila e estado ----------

def validar(fila, siglas):
    """(itens aceitos, alertas). Sem `id` válido ou sem `arquivo_prova`, o item não entra.

    `siglas` são as do projeto (da config): a fila declara intenção, a config declara quem existe.
    """
    fila = fila if isinstance(fila, dict) else {}
    conhecidas = list(siglas)
    aceitos, alertas, vistos = [], [], set()
    for it in fila.get("itens") or []:
        if not isinstance(it, dict):
            alertas.append(f"entrada que não é item recusada: {it!r}")
            continue
        iid = str(it.get("id") or "").strip()
        m = RE_ID.match(iid)
        if not m or m.group(1) not in conhecidas:
            alertas.append(f"id inválido recusado: {iid!r} (esperado SIGLA/NNN com sigla em {'|'.join(conhecidas)})")
        elif not str(it.get("arquivo_prova") or "").strip():
            alertas.append(f"`{iid}` sem `arquivo_prova`: fora da fila até ganhar prova")
        elif iid in vistos:
            alertas.append(f"`{iid}` duplicado: só a primeira ocorrência vale")
        else:
            vistos.add(iid)
            aceitos.append({**it, "id": iid, "repo": m.group(1), "nnn": m.group(2),
                            "depende_de": [str(d) for d in it.get("depende_de") or []]})
    return aceitos, alertas


def ligado(nnn, branch, ref, titulo=""):
    """Branch/PR pertence à delta NNN: segmento `NNN` na branch, escopo `(NNN` no título, ou branch declarada."""
    if branch and ref == branch:
        return True
    if re.search(rf"(^|/){nnn}(-|$)", ref):
        return True
    return bool(re.match(rf"^[a-z]+!?\({nnn}\b", titulo))


def ligar_prs(nnn, branch, prs):
    return [p for p in prs if ligado(nnn, branch, p["headRefName"], p.get("title", ""))]


def classificar(prova, prs, ahead, deps_ok):
    """(estado, PR, nota) — para no primeiro caso que casa. `prs` vem do mais recente ao mais antigo."""
    if prova:
        return MERGED, "", ""
    for estado, alvo, nota in ((REVISAO, "OPEN", ""), (CURSO, "MERGED", "archive pendente")):
        hit = [p for p in prs if p["state"] == alvo]
        if hit:
            return estado, f"#{hit[0]['number']}", nota
    if prs:
        return DIVERGENTE, f"#{prs[0]['number']}", f"PR #{prs[0]['number']} fechado sem merge e nenhum aberto"
    if ahead:
        return CURSO, "", ""
    return (PRONTO, "", "") if deps_ok else (BLOQUEADO, "", "")


def ordenar(deps, prioridade):
    """Kahn; empate por (dependentes diretos desc, prioridade(id), id). (ordem, presos); presos ≠ [] = ciclo."""
    pend = {i: {d for d in ds if d in deps} for i, ds in deps.items()}
    dependentes = {i: [j for j in deps if i in pend[j]] for i in deps}

    def chave(i):
        return (-len(dependentes[i]), prioridade(i), i)

    heap = [chave(i) for i in deps if not pend[i]]
    heapq.heapify(heap)
    ordem = []
    while heap:
        i = heapq.heappop(heap)[2]
        ordem.append(i)
        for j in dependentes[i]:
            pend[j].discard(i)
            if not pend[j]:
                heapq.heappush(heap, chave(j))
    return ordem, sorted(set(deps) - set(ordem))


def montar(itens, provas, evid, ordem_repos):
    """Linhas em ordem topológica: (linhas, presos, alertas). `evid[id]` = {"prs", "ahead"}.

    Item cujo repo não está em `provas` (repo fora da config) não entra; dependência nele alerta.
    """
    itens = [it for it in itens if it["id"] in provas]
    deps = {it["id"]: it["depende_de"] for it in itens}
    pos = {r: k for k, r in enumerate(ordem_repos)}
    ordem, presos = ordenar(deps, lambda i: pos.get(i.split("/")[0], len(pos)))
    if presos:
        return None, presos, []
    por_id = {it["id"]: it for it in itens}
    linhas, alertas = [], []
    for i in ordem:
        faltam = [d for d in deps[i] if not provas.get(d)]
        for d in faltam:
            if d not in deps:
                alertas.append(f"`{i}` depende de `{d}`, que não está no painel "
                               "(fora da fila ou repo fora da config) — conta como não mergeado")
        e = evid.get(i, {})
        estado, pr, nota = classificar(provas[i], e.get("prs", []), e.get("ahead", 0), not faltam)
        linhas.append({"id": i, "repo": por_id[i]["repo"], "titulo": str(por_id[i].get("titulo") or ""),
                       "estado": estado, "pr": pr, "nota": nota,
                       "trava": f"depende de {', '.join(faltam)}" if faltam and estado != MERGED else ""})
    return linhas, [], alertas


def proximos(linhas, foco=()):
    """Sem trava antes de com trava; depois o foco; depois PRIORIDADE; depois a ordem topológica."""
    cands = [((bool(l["trava"]), l["repo"] not in foco, PRIORIDADE.index(l["estado"]), n), l)
             for n, l in enumerate(linhas) if l["estado"] in PRIORIDADE]
    return [l for _, l in sorted(cands, key=lambda c: c[0])]


def filtrar_painel(linhas, lib, novos):
    """MERGED só enquanto falta liberar na branch lançável, ou se entrou desde a última sessão."""
    return [l for l in linhas if l["estado"] != MERGED or lib.get(l["id"]) != "main" or l["id"] in novos]


def proxima_tarefa(texto):
    m = next((RE_TAREFA.match(l) for l in (texto or "").splitlines() if RE_TAREFA.match(l)), None)
    return m.group(1).strip() if m else ""


def semear_itens(sigla, specs):
    """`specs` = [(pasta da delta ativa, texto do spec.md ou None)] → itens da fila."""
    itens = []
    for nome, texto in specs:
        texto = texto or ""
        titulo = next((l[2:].strip() for l in texto.splitlines() if l.startswith("# ")), nome)
        m = RE_BRANCH_SPEC.search(texto)
        it = {"id": f"{sigla}/{nome[:3]}", "titulo": titulo, "spec": f"specs/{nome}/spec.md",
              "arquivo_prova": f"specs/_archive/{nome}/spec.md", "depende_de": []}
        if m:
            it["branch"] = m.group(1)
        itens.append(it)
    return itens


def ultima_sessao(carimbo, hoje):
    try:
        return dt.date.fromisoformat((carimbo or "").strip())
    except ValueError:
        return hoje - dt.timedelta(days=FALLBACK_DIAS)


# ---------- foco ----------

def normalizar_foco(texto, repos):
    """Texto livre → siglas. `repos` = {sigla: pasta}. Vazio ou palavra de limpeza → []."""
    t = (texto or "").strip().lower()
    if not t or t in LIMPA_FOCO:
        return []
    return sorted({s for s, pasta in repos.items()
                   if re.search(rf"\b{s.lower()}\b", t) or str(pasta).lstrip("_").split("-")[0].lower() in t})


def resolver_foco(arg, carimbado, repos):
    """(siglas, herdado, alerta). O argumento vence o carimbo; texto sem sigla conhecida alerta."""
    if arg is None:
        siglas = normalizar_foco(carimbado, repos)
        return siglas, bool(siglas), ""
    siglas = normalizar_foco(arg, repos)
    if not siglas and arg.strip() and arg.strip().lower() not in LIMPA_FOCO:
        return [], False, (f"foco não reconhecido em {arg!r} — use uma sigla "
                           f"({'|'.join(repos)}), o nome da pasta, ou a palavra `sem`")
    return siglas, False, ""


# ---------- bancada ----------

def classificar_bancada(e):
    """(classe, nota) de um worktree/branch; ('', '') = nada a fazer. Primeiro caso que casa."""
    if e.get("sujo") or e.get("novos"):
        partes = ([f"{e['sujo']} modificado(s)"] if e.get("sujo") else []) \
            + ([f"{e['novos']} não rastreado(s)"] if e.get("novos") else [])
        return SUJA, ", ".join(partes)
    if e.get("detached"):
        return LIBERAVEL, "HEAD solto, sem branch"
    if e.get("base"):
        return (REPRESADA, f"{e['ahead']} commit(s) da base local fora da origin") if e.get("ahead") else ("", "")
    if e.get("ahead"):
        return ("", "") if e.get("pr") else (REPRESADA, f"{e['ahead']} commit(s) fora da base, sem PR aberto")
    return LIBERAVEL, "nada fora da base"


def resumir_bancada(entradas, detalhar, limite=LIMITE_BANCADA):
    """(contagem por classe, itens a mostrar, ocultos). `detalhar` falso mostra só as SUJAS."""
    marcadas = []
    for e in entradas:
        classe, nota = classificar_bancada(e)
        if classe:
            marcadas.append({**e, "classe": classe, "nota": nota})
    contagem = {c: n for c, n in ((c, sum(m["classe"] == c for m in marcadas)) for c in PRIORIDADE_BANCADA) if n}
    mostrar = sorted(marcadas, key=lambda m: (PRIORIDADE_BANCADA.index(m["classe"]), m["nome"]))
    if not detalhar:
        mostrar = [m for m in mostrar if m["classe"] == SUJA]
    return contagem, mostrar[:limite], max(0, len(mostrar) - limite)


# ---------- grafo ----------

def grafo(itens, linhas, merged_ocultos=()):
    """(nós, arestas). Nó = (id, repo, estado); repo vazio = dependência fora do painel.

    Dependência que o filtro do painel ocultou porque já está concluída entra como MERGED —
    nó cinza de bloqueio ali mentiria sobre a trava.
    """
    estado = {l["id"]: l["estado"] for l in linhas}
    nos = [(l["id"], l["repo"], l["estado"]) for l in linhas]
    externos = sorted({d for it in itens if it["id"] in estado for d in it["depende_de"] if d not in estado})
    nos += [(d, "", MERGED if d in merged_ocultos else FORA) for d in externos]
    arestas = [(d, it["id"]) for it in itens if it["id"] in estado for d in it["depende_de"]]
    return nos, arestas


def render_d2(nos, arestas):
    """Mesmo grafo, layout melhor: para quando o formato embutido fica ilegível de tão denso.

    Consome a MESMA estrutura do renderizador embutido — é o que impede os dois retratos do
    mesmo grafo de divergirem quando um deles for regerado e o outro não.
    """
    ident = {i: re.sub(r"[^A-Za-z0-9]", "_", i) for i, _, _ in nos}
    out = []
    for repo in dict.fromkeys(r for _, r, _ in nos if r):
        out.append(f"{repo}: {{")
        out += [f'  {ident[i]}: "{i}\\n{e}"' for i, r, e in nos if r == repo]
        out.append("}")
    out += [f'{ident[i]}: "{i}\\n{e}"' for i, r, e in nos if not r]
    for origem, destino in arestas:
        if origem in ident and destino in ident:
            a = next((f"{r}.{ident[origem]}" if r else ident[origem] for i, r, _ in nos if i == origem), ident[origem])
            b = next((f"{r}.{ident[destino]}" if r else ident[destino] for i, r, _ in nos if i == destino), ident[destino])
            out.append(f"{a} -> {b}")
    return "\n".join(out) + "\n"


def precisa_externo(quantidade_de_nos, disponivel=True, teto=TETO_EMBUTIDO):
    """Acima do teto o diagrama embutido vira emaranhado; sem o renderizador externo, porém,
    o embutido ilegível ainda é melhor que diagrama nenhum."""
    return quantidade_de_nos > teto and bool(disponivel)


def render_mermaid(nos, arestas):
    """Renderizador fino sobre (nós, arestas) — formato que o editor de notas lê nativamente."""
    ident = {i: f"n{k}" for k, (i, _, _) in enumerate(nos)}
    out = ["graph LR"]
    for repo in dict.fromkeys(r for _, r, _ in nos if r):
        out.append(f"  subgraph {repo}")
        out += [f'    {ident[i]}["{i}<br/>{e}"]:::{CLASSE.get(e, "bloqueado")}' for i, r, e in nos if r == repo]
        out.append("  end")
    out += [f'  {ident[i]}["{i}<br/>{e}"]:::{CLASSE.get(e, "bloqueado")}' for i, r, e in nos if not r]
    out += [f"  {ident[o]} --> {ident[d]}" for o, d in arestas if o in ident and d in ident]
    out += [f"  classDef {c} fill:{cor},stroke:#555" for c, cor in COR.items()]
    return "\n".join(out)


# ---------- render do painel ----------

def render_bancada(bancada):
    """Uma linha por repo; abaixo dela o que pede ação, já podado por `resumir_bancada`."""
    out = ["## Bancada (worktrees e branches)"]
    for b in bancada:
        resumo = ", ".join(f"{n} {c.lower() if n == 1 else PLURAL_BANCADA[c]}"
                           for c, n in b["contagem"].items()) or "nada pedindo ação"
        out.append(f"- **{b['repo']}** · {b['worktrees']} worktree(s), {b['branches']} branch(es) · {resumo}")
        for m in b["itens"]:
            onde = "worktree" if m["wt"] else "branch"
            rotulo = f"`{m['nome']}`" + (f" [{m['branch']}]" if m["wt"] and not m["detached"] else "")
            out.append(f"  - {m['classe']} · {onde} {rotulo} — {m['nota']}")
        if b["ocultos"]:
            out.append(f"  - … +{b['ocultos']} sem listar — laudo por branch é a auditoria de branches")
    return out


def renderizar(titulo, hoje, desde, logs, linhas, alertas, lib, diagrama, fila, tarefa,
               bancada=(), foco=(), herdado=False, debito=(), retro=(), janela=""):
    marca = f", foco: {'/'.join(foco)}{' (herdado)' if herdado else ''}" if foco else ""
    out = [f"# Painel {titulo} — {hoje.isoformat()} (última sessão: {desde.isoformat()}{marca})"]
    if janela:
        out.append(f"> {janela}")
    diverg = [l for l in linhas if l["estado"] == DIVERGENTE]
    if diverg or alertas:
        out.append("## ⚠️ Divergências e alertas")
        out += [f"- `{l['id']}`: {l['nota']}" for l in diverg]
        out += [f"- {a}" for a in alertas]
    out.append(f"## Desde {desde.isoformat()} nas bases")
    out += [f"- {s} {c}" for s, cs in logs for c in cs] or ["- nada entrou"]
    out += list(retro)
    out.append("## Estado agora")
    out.append("| # | Repo | Item | Estado | Liberação | PR | Trava |\n|---|---|---|---|---|---|---|")
    for n, l in enumerate(linhas, 1):
        item = (f"{l['id']} — {l['titulo']}" if l["titulo"] else l["id"]).replace("|", "/")
        estado = f"{l['estado']} ({l['nota']})" if l["nota"] and l["estado"] == CURSO else l["estado"]
        out.append(f"| {n} | {l['repo']} | {item} | {estado} | {lib.get(l['id'], '')} | "
                   f"{l['pr'] or '—'} | {l['trava'] or '—'} |")
    if bancada:
        out += render_bancada(bancada)
    out += list(debito)
    out.append("## Grafo\n```mermaid\n" + diagrama + "\n```")
    out.append("## Próximo")
    if not linhas:
        out.append("fila vazia, precisa de spec nova")
    elif not fila:
        out.append("nada destravado: todo item pendente está BLOQUEADO")
    else:
        for k, l in enumerate(fila[:3], 1):
            linha = f"{k}. `{l['id']}` — {l['estado']}" + (f" ({l['nota']})" if l["nota"] else "") \
                + (f" · trava: {l['trava']}" if l["trava"] else "")
            if k == 1 and tarefa:
                linha += f"\n   próxima tarefa: {tarefa}"
            out.append(linha)
    return "\n".join(out)


# ---------- selftest ----------

def selftest():
    def pr(n, s, head="feat/042-x", title=""):
        return {"number": n, "state": s, "headRefName": head, "title": title}

    # ligação PR/branch ↔ delta
    assert ligado("042", None, "feat/042-plano") and ligado("042", None, "042-plano")
    assert not ligado("042", None, "fix/dt-042-x") and not ligado("042", None, "feat/0421-x")
    assert ligado("042", None, "chore/x", "docs(042): arquiva") and ligado("042", None, "y", "feat(042-plano)!: x")
    assert not ligado("042", None, "chore/x", "docs(0421): x") and ligado("042", "chore/x", "chore/x")
    assert [p["number"] for p in ligar_prs("002", None, [pr(1, "MERGED", "docs/002-spec"), pr(2, "OPEN", "fix/dt-002")])] == [1]

    # classificação, na ordem das regras
    def c(prova=False, prs=(), ahead_=0, ok=True):
        return classificar(prova, list(prs), ahead_, ok)

    assert c(prova=True, prs=[pr(1, "OPEN")])[0] == MERGED
    assert c(prs=[pr(8, "OPEN"), pr(5, "MERGED")]) == (REVISAO, "#8", "")
    assert c(prs=[pr(5, "MERGED"), pr(3, "CLOSED")]) == (CURSO, "#5", "archive pendente")
    assert c(prs=[pr(3, "CLOSED")])[0] == DIVERGENTE
    assert c(ahead_=2)[0] == CURSO
    assert c()[0] == PRONTO and c(ok=False)[0] == BLOQUEADO

    # validação: a config diz quais siglas existem
    aceitos, alertas = validar({"itens": [
        {"id": "APP/002", "arquivo_prova": "a"}, {"id": "APP-002", "arquivo_prova": "b"},
        {"id": "ZZ/001", "arquivo_prova": "c"}, {"id": "GEST/042", "arquivo_prova": " "},
        {"id": "APP/002", "arquivo_prova": "d"}, "lixo"]}, ["APP", "GEST"])
    assert [i["id"] for i in aceitos] == ["APP/002"] and len(alertas) == 5, alertas
    assert aceitos[0]["repo"] == "APP" and aceitos[0]["nnn"] == "002"

    # ordem: dependentes desc, depois prioridade do repo, depois id
    prio = {"APP": 0, "GEST": 1}
    ordem, presos = ordenar({"GEST/001": [], "APP/001": [], "APP/002": ["GEST/001"], "GEST/002": ["GEST/001"]},
                            lambda i: prio[i.split("/")[0]])
    assert (ordem, presos) == (["GEST/001", "APP/001", "APP/002", "GEST/002"], [])
    assert ordenar({"X": ["Y"], "Y": ["X"], "Z": ["X"]}, lambda i: 0)[1] == ["X", "Y", "Z"]

    # montagem: trava, dependência externa/oculta, filtro por repo da config
    itens, _ = validar({"itens": [
        {"id": "GEST/001", "arquivo_prova": "a"},
        {"id": "APP/002", "arquivo_prova": "b", "depende_de": ["GEST/001"]},
        {"id": "APP/003", "arquivo_prova": "c", "depende_de": ["LIB/001"]},
        {"id": "LIB/001", "arquivo_prova": "d"},
        {"id": "DOC/001", "arquivo_prova": "e", "depende_de": ["GEST/001"]},
    ]}, ["APP", "GEST", "LIB", "DOC"])
    provas = {"GEST/001": True, "APP/002": False, "APP/003": False, "DOC/001": False}  # LIB fora da config
    linhas, presos, al = montar(itens, provas, {"APP/002": {"prs": [pr(7, "MERGED")], "ahead": 0}},
                                ["APP", "DOC", "GEST"])
    est = {l["id"]: l for l in linhas}
    # APP/003 (sem dependência resolvível) empata com APP/002 em dependentes e repo; id desempata
    assert presos == [] and "LIB/001" not in est
    assert [l["id"] for l in linhas] == ["GEST/001", "APP/002", "APP/003", "DOC/001"]
    assert est["APP/002"]["estado"] == CURSO and est["APP/002"]["nota"] == "archive pendente" and est["APP/002"]["trava"] == ""
    assert est["APP/003"]["estado"] == BLOQUEADO and est["APP/003"]["trava"] == "depende de LIB/001"
    assert est["DOC/001"]["estado"] == PRONTO and len(al) == 1 and "LIB/001" in al[0]
    assert [l["id"] for l in proximos(linhas)] == ["APP/002", "DOC/001"]
    assert [l["id"] for l in proximos(linhas, ["DOC"])] == ["DOC/001", "APP/002"]  # foco só desempata
    assert [l["id"] for l in proximos(linhas, ["LIB"])] == ["APP/002", "DOC/001"]  # foco vazio não esconde
    assert montar(validar({"itens": [{"id": "APP/001", "arquivo_prova": "x", "depende_de": ["APP/001"]}]}, ["APP"])[0],
                  {"APP/001": False}, {}, ["APP"])[1] == ["APP/001"]

    # filtro de MERGED no painel
    m1 = {"id": "GEST/001", "estado": MERGED}
    m2 = {"id": "GEST/002", "estado": MERGED}
    assert filtrar_painel([m1, m2, est["APP/002"]], {"GEST/001": "main", "GEST/002": "—"}, set()) == [m2, est["APP/002"]]
    assert filtrar_painel([m1], {"GEST/001": "main"}, {"GEST/001"}) == [m1]

    # foco: texto livre → sigla, herança e recusa
    repos = {"APP": "aplicacao", "GEST": "_gestao", "DOC": "documentos-tecnicos"}
    assert normalizar_foco("APP", repos) == ["APP"] and normalizar_foco("continua na aplicacao", repos) == ["APP"]
    assert normalizar_foco("hoje é APP e GEST", repos) == ["APP", "GEST"]
    assert normalizar_foco("documentos-tecnicos", repos) == ["DOC"]  # casa pelo nome da pasta
    assert normalizar_foco("", repos) == [] and normalizar_foco("sem", repos) == [] and normalizar_foco(None, repos) == []
    assert resolver_foco(None, "APP\n", repos) == (["APP"], True, "")
    assert resolver_foco("GEST", "APP", repos) == (["GEST"], False, "")  # argumento vence o carimbo
    assert resolver_foco("sem", "APP", repos) == ([], False, "")
    assert resolver_foco("marketing", "APP", repos)[:2] == ([], False)
    assert "não reconhecido" in resolver_foco("marketing", "", repos)[2]

    # bancada: primeiro caso que casa
    def b(**kw):
        return {"nome": kw.pop("nome", "x"), "branch": kw.pop("branch", "feat/x"),
                "wt": True, "detached": False, "base": False,
                "sujo": 0, "novos": 0, "ahead": 0, "pr": False, **kw}

    assert classificar_bancada(b(sujo=3, novos=1, ahead=9))[0] == SUJA
    assert classificar_bancada(b(sujo=0, novos=2))[1] == "2 não rastreado(s)"
    assert classificar_bancada(b(detached=True, ahead=4))[0] == LIBERAVEL
    assert classificar_bancada(b(base=True, ahead=2))[0] == REPRESADA and classificar_bancada(b(base=True))[0] == ""
    assert classificar_bancada(b(ahead=5))[0] == REPRESADA and classificar_bancada(b(ahead=5, pr=True))[0] == ""
    assert classificar_bancada(b())[0] == LIBERAVEL
    entradas = [b(nome="wt-a", sujo=2), b(nome="wt-b", ahead=3), b(nome="br-c", wt=False), b(nome="wt-d", ahead=1, pr=True)]
    contagem, itens_b, ocultos = resumir_bancada(entradas, True)
    assert contagem == {SUJA: 1, REPRESADA: 1, LIBERAVEL: 1} and [m["nome"] for m in itens_b] == ["wt-a", "wt-b", "br-c"]
    assert ocultos == 0 and resumir_bancada(entradas, True, limite=2)[2] == 1
    assert [m["nome"] for m in resumir_bancada(entradas, False)[1]] == ["wt-a"]  # fora do foco, só a suja
    assert resumir_bancada(entradas, False)[0] == contagem  # a contagem não encolhe com o foco

    # grafo: dado primeiro, render depois
    nos, arestas = grafo(itens, linhas)
    assert ("APP/002", "APP", CURSO) in nos and ("LIB/001", "", FORA) in nos
    assert ("GEST/001", "APP/002") in arestas and ("LIB/001", "APP/003") in arestas
    nos_ocultos, _ = grafo(itens, linhas, merged_ocultos={"LIB/001"})
    assert ("LIB/001", "", MERGED) in nos_ocultos  # dependência concluída não vira nó de bloqueio
    # os dois renderizadores comem a mesma estrutura: é o que os impede de divergir
    d = render_d2(nos, arestas)
    assert "APP: {" in d and 'n_a_m_e' not in d
    assert 'GEST_001: "GEST/001\\nMERGED"' in d and "GEST.GEST_001 -> APP.APP_002" in d
    assert 'LIB_001: "LIB/001\\n(fora do painel)"' in d  # nó externo fica fora de subgrafo
    assert precisa_externo(21) and not precisa_externo(20)
    assert not precisa_externo(21, disponivel=False)  # sem o binário, o embutido serve
    g = render_mermaid(nos, arestas)
    assert "subgraph APP" in g and 'n0["GEST/001' in g and "n0 --> n1" in g
    assert f'["LIB/001<br/>{FORA}"]:::bloqueado' in g
    assert '["LIB/001<br/>MERGED"]:::merged' in render_mermaid(*grafo(itens, linhas, {"LIB/001"}))

    # semente e tarefa
    app_md = "# delta-002 — ingestao\n\nEstado: proposta · Branch: feat/002-ingestao · Perfil: completo\n"
    gest_md = "# Delta 042 — plano\n\n> **Status:** proposta · **Branch:** `chore/plano` · **Data:** x\n"
    s = semear_itens("APP", [("002-ingestao", app_md), ("043-sem-spec", None)]) + semear_itens("GEST", [("042-dot", gest_md)])
    assert [x["id"] for x in s] == ["APP/002", "APP/043", "GEST/042"]
    assert s[0]["branch"] == "feat/002-ingestao" and "branch" not in s[1] and s[2]["branch"] == "chore/plano"
    assert s[0]["arquivo_prova"] == "specs/_archive/002-ingestao/spec.md" and s[1]["titulo"] == "043-sem-spec"
    assert validar({"itens": s}, ["APP", "GEST"])[1] == []
    assert proxima_tarefa("- [x] T1 feito\n  - [ ] T2 — parser (dep: T1) · arquivos: a.py\n- [ ] T3") == "T2 — parser (dep: T1) · arquivos: a.py"
    assert proxima_tarefa("- [x] tudo\n") == "" and proxima_tarefa(None) == ""

    # última sessão pelo carimbo
    hoje = dt.date(2026, 9, 13)
    assert ultima_sessao("2026-09-10\n", hoje) == dt.date(2026, 9, 10)
    assert ultima_sessao("", hoje) == dt.date(2026, 9, 12) and ultima_sessao("lixo", hoje) == dt.date(2026, 9, 12)

    # render
    banc = [{"repo": "APP", "contagem": contagem, "itens": itens_b, "ocultos": 2, "worktrees": 3, "branches": 1}]
    r = renderizar("Projeto X", hoje, dt.date(2026, 9, 12), [("APP", ["abc feat: x"])], linhas, al,
                   {"GEST/001": "main"}, g, proximos(linhas), "T22 — carga", banc, ["APP"], True,
                   retro=["### Também desde então", "- handoff: APP/H_x.md"], janela="Janela: 5 sessões")
    assert "# Painel Projeto X — 2026-09-13" in r and "foco: APP (herdado)" in r
    assert "| 2 | APP | APP/002 | EM CURSO (archive pendente) |" in r and "1. `APP/002`" in r
    assert "próxima tarefa: T22" in r and "Divergências" in r and "- APP abc feat: x" in r
    assert "## Bancada" in r and "3 worktree(s), 1 branch(es)" in r and "1 suja, 1 represada, 1 liberável" in r
    assert "> Janela: 5 sessões" in r and "### Também desde então" in r and "- handoff: APP/H_x.md" in r
    assert "SUJA · worktree `wt-a` [feat/x] — 2 modificado(s)" in r and "+2 sem listar" in r
    assert "fila vazia, precisa de spec nova" in renderizar("P", hoje, hoje, [], [], [], {}, "", [], "")
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true", help="valida as funções puras deste módulo")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
