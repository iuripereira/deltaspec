#!/usr/bin/env python3
"""Vista da fila de integração — quem está em voo, onde, há quanto tempo, em que ordem (delta-114).

Vista **derivada**, nunca registro: lê git (refs, worktrees, cherry, stashes), `gh pr list` e,
opcionalmente, o cronograma do portfólio. Sessões por checkout ficam para a delta-113 R2
(coluna `?` até lá). Não escreve refs além do que `--fetch` (opt-in, timeout por repo) pede,
não cria arquivo versionado e degrada sem `gh`/rede (colunas `?`, exit 0). Gramática e
limiares: `references/integracao.md` (dono; `deps.toml`).

Uso: integracao.py [ALVO] [--repo DIR]... [--cronograma ARQ] [--json] [--fetch]
     integracao.py --selftest
ALVO = repo git (modo repo) ou pasta-mãe com repos filhos (modo workspace); default `.`.
Exit 0 = vista emitida (mesmo degradada) · 2 = erro de uso.
"""
import argparse
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta
from pathlib import Path

from debito import die, git

# Limiares do agente branch-killer (fora do repo). Dono textual: references/integracao.md;
# o deps.toml casa `ATIVA_DIAS = 2` / `DEFASADA_DIAS = 7` aqui — não reescreva um sem o outro.
ATIVA_DIAS = 2  # sem commit há mais que isto e sem PR → parada
DEFASADA_DIAS = 7  # sem commit há mais que isto → defasada, com ou sem PR
MERGEADAS_DIAS = 7
BASE_PREFERIDA = "develop"
NUNCA_CANDIDATAS = ("main", "develop", "HEAD")
PREFIXO_BOT = "release-please--branches--"
PREFIXO_RELEASE = "release/"  # topo da fila (R5) e nome do 3º bloco de merges (R6) — mesma constante nos dois usos
LABEL_FILA = re.compile(r"^fila:(\d+)$")
BASES_MARCO = ("contrato", "portfolio")
DIR_PLANOS = ".claude/plans"
CAMPOS_PR = "number,headRefName,baseRefName,isDraft,createdAt,labels,url"
CAMPOS_MERGE = "number,headRefName,mergedAt,mergeCommit"
SEM_MARCO = "9999-12-31"
INF = 10**9
FETCH_TIMEOUT = 10  # s por repo; fetch travado sai da vista, nunca a trava
MAX_THREADS = 8  # ponytail: um repo por thread, teto fixo; o custo é o gh (~0,6 s/chamada), não o git


# ---------------------------------------------------------------- puras: parsing


def parse_refs(texto: str) -> dict:
    """`for-each-ref` → {branch: {data, upstream, local, remota, gone}}; data = tip mais novo dos dois lados.

    `gone` vem de `%(upstream:track)` (`[gone]` explícito do git) — nunca da ausência de ref
    remota homônima: toda branch nova criada a partir de uma base remota herda o upstream
    *dela* sem nunca ter sido publicada com o próprio nome, e não pode virar "gone" por isso.
    """
    fora = {}
    for linha in texto.splitlines():
        if not linha.strip():
            continue
        nome, data, upstream, track = (linha.split("|") + ["", "", "", ""])[:4]
        remota = nome.startswith("origin/")
        branch = nome[7:] if remota else nome
        if branch in NUNCA_CANDIDATAS or branch.startswith(PREFIXO_BOT):
            continue
        r = fora.setdefault(branch, {"data": "", "upstream": None, "local": False, "remota": False, "gone": False})
        r["data"] = max(r["data"], data)
        r["local"] |= not remota
        r["remota"] |= remota
        if not remota and upstream:
            r["upstream"] = upstream
            r["gone"] = "[gone]" in track
    return fora


def parse_worktrees(texto: str) -> list:
    """`worktree list --porcelain` → [{caminho, branch, principal, detached, locked, prunable}]."""
    fora = []
    for bloco in texto.strip().split("\n\n"):
        if not bloco.strip():
            continue
        w = {"caminho": "", "branch": None, "principal": not fora,
             "detached": False, "locked": False, "prunable": False}
        for linha in bloco.splitlines():
            chave, _, valor = linha.partition(" ")
            if chave == "worktree":
                w["caminho"] = valor
            elif chave == "branch":
                w["branch"] = valor.removeprefix("refs/heads/")
            elif chave in ("detached", "locked", "prunable"):
                w[chave] = True
        fora.append(w)
    return fora


def label_fila(labels) -> "int | None":
    for nome in labels:
        m = LABEL_FILA.match(nome)
        if m and int(m.group(1)) >= 1:
            return int(m.group(1))
    return None


def estado(dias: int, pr) -> str:
    """Ordem dos testes = decisão 6 do plano: a idade alarma antes de qualquer PR."""
    if dias > DEFASADA_DIAS:
        return "defasada"
    if pr:
        return "draft" if pr["draft"] else "em PR"
    return "parada" if dias > ATIVA_DIAS else "ativa"


LINHA_MARCO = re.compile(r"^\|\s*([^|]+?)\s*\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*([^|]+?)\s*\|\s*(contrato|portfolio)\s*\|\s*$")
DIR_PROJETO = re.compile(r"^## (.+?)\s*\n\*\*Dir:\*\*\s*([^\s·]+)", re.M)


def _marcos_por_projeto(texto: str, hoje: date) -> dict:
    """{projeto: (data, nome)} — marco futuro mais próximo; só `## Marcos`, bases contrato/portfolio.

    `D+7`, `presumido` e datas passadas caem pelo regex e pela comparação, sem `if` dedicado —
    a tabela do _pmo é a única fonte e muda de forma raramente.
    """
    partes = ("\n" + texto).split("\n## Marcos", 1)
    if len(partes) < 2:
        return {}
    corpo = partes[1].split("\n## ", 1)[0]
    por_projeto = {}
    for m in (LINHA_MARCO.match(linha) for linha in corpo.splitlines()):
        if m and m.group(2) >= hoje.isoformat():
            atual = por_projeto.get(m.group(3))
            if not atual or m.group(2) < atual[0]:
                por_projeto[m.group(3)] = (m.group(2), m.group(1))
    return por_projeto


def _dir_por_projeto(texto: str) -> dict:
    return {p: d for p, d in DIR_PROJETO.findall(texto)}


def marcos_por_dir(texto: str, hoje: date) -> dict:
    """{dir: (data, nome)} — projeto sem `**Dir:**` (ex.: `todos`) cai aqui, sem `if`."""
    marcos, dirs = _marcos_por_projeto(texto, hoje), _dir_por_projeto(texto)
    return {dirs[p]: m for p, m in marcos.items() if p in dirs}


def avisos_cronograma(texto: str, hoje: date) -> list:
    """Degradação nunca silenciosa: o cronograma é markdown editado à mão em outro repo (sem gate lá).

    Nomeia qual das três causas ocorreu (Q6, revisão adversarial de 08/09): seção ausente/cabeçalho
    fora do esperado, tabela lida sem marco futuro casável, ou projeto com marco e sem `**Dir:**` —
    colapsar as duas primeiras numa mensagem só manda procurar no lugar errado, já que as colunas
    de `## Marcos` casam por posição.
    """
    partes = ("\n" + texto).split("\n## Marcos", 1)
    corpo = partes[1].split("\n## ", 1)[0] if len(partes) >= 2 else ""
    cabecalho = next((l.strip() for l in corpo.splitlines() if l.strip()), "")
    if " ".join(cabecalho.split()) != "| Marco | Data | Projeto | Base |":
        return ["aviso: cronograma sem a seção '## Marcos' (ou cabeçalho fora do esperado: "
                "| Marco | Data | Projeto | Base |)"]
    marcos, dirs = _marcos_por_projeto(texto, hoje), _dir_por_projeto(texto)
    if not marcos:
        return ["aviso: '## Marcos' lida, nenhum marco futuro com base contrato/portfolio"]
    return [f"aviso: projeto '{p}' tem marco mas não tem '**Dir:**'" for p in sorted(set(marcos) - set(dirs))]


# ---------------------------------------------------------------- puras: ordem


def chave_propria(item) -> tuple:
    """fila:N (override) → PR mais antiga → tip mais antigo → nome."""
    pr = item["pr"]
    return (item["fila"] or INF, pr["criada"] if pr else SEM_MARCO, item["data"], item["branch"])


def raiz_da_pilha(item, por_branch, base):
    """Segue `pr.base` até a base do repo → (raiz, profundidade). Ciclo para no `visto`; base ausente = raiz própria."""
    visto, atual, prof = set(), item, 0
    while atual["pr"] and atual["pr"]["base"] != base and atual["pr"]["base"] not in visto:
        b = atual["pr"]["base"]
        visto.add(b)
        if b not in por_branch:
            break
        atual, prof = por_branch[b], prof + 1
    return atual, prof


def ordenar(itens, base: str) -> list:
    """`release/*` no topo do repo (spec R5, emenda 08/09) → pilha logo após a raiz → `chave_propria`.

    A prioridade de `release/*` é do próprio item, não da raiz da pilha: uma branch empilhada
    sobre uma release não "sobe" com ela — só a `release/*` em si fura a fila. Preenche
    `ordem` e `pilha_base`.
    """
    por_branch = {i["branch"]: i for i in itens}

    def chave(i):
        raiz, prof = raiz_da_pilha(i, por_branch, base)
        return (not i["branch"].startswith(PREFIXO_RELEASE), chave_propria(raiz), prof, chave_propria(i))

    for i in itens:
        i["pilha_base"] = i["pr"]["base"] if i["pr"] and i["pr"]["base"] != base else None
    fora = sorted(itens, key=chave)
    for n, i in enumerate(fora, 1):
        i["ordem"] = n
    return fora


def chave_repo(bloco) -> tuple:
    """Entre repos: marco futuro mais próximo; sem marco vai ao fim; empate → nome."""
    return ((bloco["marco"] or {"data": SEM_MARCO})["data"], bloco["repo"])


# ---------------------------------------------------------------- I/O


def repos_do_alvo(alvo: Path, extras) -> list:
    """Modo repo (alvo tem .git) ou workspace (filhos com .git) — pasta filha sem .git cai fora em silêncio."""
    base = [alvo] if (alvo / ".git").exists() else sorted(p.parent for p in alvo.glob("*/.git"))
    return base + [Path(e).resolve() for e in extras]


def base_do_repo(repo: Path) -> str:
    for cand in (f"origin/{BASE_PREFERIDA}", BASE_PREFERIDA):
        if git(repo, "rev-parse", "--verify", "-q", cand):
            return cand
    head = git(repo, "symbolic-ref", "--short", "-q", "refs/remotes/origin/HEAD")
    return head.strip() if head else "main"


def novos(repo: Path, base: str, ref: str) -> int:
    """Commits de `ref` ausentes em `base` por patch-id (`git cherry`): sobrevive a squash."""
    return sum(1 for l in (git(repo, "cherry", base, ref) or "").splitlines() if l.startswith("+"))


def plano_da_branch(repo: Path, base: str, ref: str):
    """Primeiro arquivo adicionado em .claude/plans/ pela branch (decisão 10: só plano no git conta)."""
    saida = git(repo, "log", "--diff-filter=A", "--format=", "--name-only", f"{base}..{ref}", "--", DIR_PLANOS) or ""
    nomes = [l for l in saida.splitlines() if l.strip()]
    return Path(nomes[-1]).name if nomes else None


def repo_gh(url: str):
    m = re.search(r"github\.com[:/]([^/\s]+/[^/\s]+?)(?:\.git)?/?$", url.strip())
    return m.group(1) if m else None


def gh_json(repo: Path, *args):
    """`gh <args>` com `-R owner/repo`; degrada para None em qualquer falha (ausente/rede/remoto/exit/JSON — emenda 08/09)."""
    alvo = repo_gh(git(repo, "remote", "get-url", "origin") or "")
    if not alvo:
        return None
    try:
        r = subprocess.run(["gh", *args, "-R", alvo], capture_output=True, text=True)
    except (FileNotFoundError, OSError):
        return None
    if r.returncode != 0:
        return None
    try:
        dados = json.loads(r.stdout)
    except ValueError:
        return None
    if isinstance(dados, list) and len(dados) == 100:
        print(f"aviso: {repo.name} — gh {' '.join(map(str, args[:4]))} retornou 100, pode truncar", file=sys.stderr)
    return dados


def prs_abertas(repo: Path):
    dados = gh_json(repo, "pr", "list", "--state", "open", "--limit", "100", "--json", CAMPOS_PR)
    if dados is None:
        return None
    return {p["headRefName"]: {"numero": p["number"], "base": p["baseRefName"], "draft": p["isDraft"],
                               "criada": p["createdAt"][:10], "labels": [l["name"] for l in p.get("labels", [])],
                               "url": p["url"]} for p in dados}


def mergeadas_recentes(repo: Path, base: str, desde: str, bloco: str, tags=None) -> list:
    """PRs mergeadas em `base` desde `desde`; `bloco` rotula entrou/saiu/corrigido_na_release; `tags` = {sha: nome} (R6)."""
    dados = gh_json(repo, "pr", "list", "--state", "merged", "--base", base,
                    "--search", f"merged:>={desde}", "--limit", "100", "--json", CAMPOS_MERGE) or []
    fora = [{"numero": p["number"], "branch": p["headRefName"], "mergeada_em": p["mergedAt"][:10], "bloco": bloco,
             "tag": (tags or {}).get((p.get("mergeCommit") or {}).get("oid"))} for p in dados]
    return sorted(fora, key=lambda m: (m["mergeada_em"], m["numero"]), reverse=True)


def fetch_com_timeout(repo: Path) -> bool:
    """`git fetch --prune` com teto de tempo — fora do `git()` do debito.py, que não tem timeout. False = ficou com as refs locais."""
    try:
        r = subprocess.run(["git", "-C", str(repo), "fetch", "-q", "--prune", "origin"],
                           capture_output=True, text=True, timeout=FETCH_TIMEOUT)
    except (subprocess.TimeoutExpired, OSError):
        return False
    return r.returncode == 0


def coletar(repo: Path, marcos: dict, hoje: date, fetch: bool) -> dict:
    """Um bloco por repo. Sessões são sempre None nesta delta (reservado à 113 R2) → coluna `?`."""
    ok_fetch = fetch_com_timeout(repo) if fetch else None
    base = base_do_repo(repo)
    base_bare = base.removeprefix("origin/")
    refs = parse_refs(git(repo, "for-each-ref",
                          "--format=%(refname:short)|%(committerdate:short)|%(upstream:short)|%(upstream:track)",
                          "refs/heads", "refs/remotes/origin") or "")
    wts = parse_worktrees(git(repo, "worktree", "list", "--porcelain") or "")
    prs = prs_abertas(repo)
    if prs is None:
        print(f"aviso: {repo.name} — gh indisponível; PR e mergeadas saem sem dado", file=sys.stderr)
    wt_por_branch = {w["branch"]: w for w in wts if w["branch"]}
    itens = []
    for branch, r in sorted(refs.items()):
        ref = branch if r["local"] else f"origin/{branch}"
        n = novos(repo, base, ref)
        wt = wt_por_branch.get(branch)
        if n == 0 and not wt:
            continue
        pr = (prs or {}).get(branch)
        dias = (hoje - date.fromisoformat(r["data"])).days
        itens.append({"branch": branch, "estado": estado(dias, pr), "dias": dias, "novos": n, "data": r["data"],
                      "worktree": ("(principal)" if wt["principal"] else Path(wt["caminho"]).name) if wt else None,
                      "sessoes": None,
                      "pr": pr, "fila": label_fila(pr["labels"]) if pr else None,
                      "plano": plano_da_branch(repo, base, ref),
                      "upstream_gone": r["gone"]})
    checkouts = [{"caminho": w["caminho"], "branch": w["branch"] or "(detached)",
                  "sujos": len((git(Path(w["caminho"]), "status", "--porcelain") or "").splitlines()),
                  "flags": [k for k in ("prunable", "locked", "detached") if w[k]], "sessoes": None} for w in wts]
    mergeadas = []
    if prs is not None:
        desde = (hoje - timedelta(days=MERGEADAS_DIAS)).isoformat()
        tags = dict(l.split(" ", 1) for l in (git(repo, "for-each-ref",
                    "--format=%(objectname) %(refname:short)", "refs/tags") or "").splitlines() if l.strip())
        mergeadas += mergeadas_recentes(repo, base_bare, desde, "entrou")
        mergeadas += mergeadas_recentes(repo, "main", desde, "saiu", tags)
        for rb in sorted(b for b in refs if b.startswith(PREFIXO_RELEASE)):
            ref_rb = rb if refs[rb]["local"] else f"origin/{rb}"
            sha = (git(repo, "merge-base", base, ref_rb) or "").strip()
            corte = (git(repo, "show", "-s", "--format=%cs", sha) or "").strip() if sha else ""
            if corte:
                mergeadas += mergeadas_recentes(repo, rb, corte, "corrigido_na_release")
    m = marcos.get(repo.name)
    return {"repo": repo.name, "caminho": str(repo), "base": base, "gh": prs is not None, "fetch": ok_fetch,
            "marco": {"data": m[0], "nome": m[1]} if m else None,
            "stashes": len((git(repo, "stash", "list") or "").splitlines()),
            "checkouts": checkouts, "itens": ordenar(itens, base_bare), "mergeadas": mergeadas}


def montar(repos, marcos, hoje: date, agora: datetime, fetch: bool) -> dict:
    """Um repo por thread: o custo é o `gh` (~0,6 s por chamada, 3-4 por repo), não o git."""
    with ThreadPoolExecutor(max_workers=min(MAX_THREADS, len(repos))) as ex:
        blocos = sorted(ex.map(lambda r: coletar(r, marcos, hoje, fetch), repos), key=chave_repo)
    return {"contrato": 1, "gerado": agora.strftime("%Y-%m-%dT%H:%M"), "ativa_dias": ATIVA_DIAS,
            "defasada_dias": DEFASADA_DIAS, "repos": blocos}


def _sessoes(lista) -> str:
    return "?" if lista is None else (", ".join(lista) or "—")


def render(vista: dict) -> str:
    """Texto determinístico: bloco por repo (na ordem), tabela de itens, checkouts, trailer de merges em 3 blocos."""
    linhas = []
    for r in vista["repos"]:
        marco = f"marco {r['marco']['data']} ({r['marco']['nome']})" if r["marco"] else "sem marco"
        linhas += [f"## {r['repo']} · base {r['base']} · {marco} · stashes {r['stashes']}"
                   + ("" if r["gh"] else " · gh ?") + ("" if r["fetch"] is not False else " · fetch falhou"), ""]
        if r["itens"]:
            linhas += ["| # | Branch | Estado | Dias | Novos | PR | Worktree | Sessões | Plano |",
                       "|---|---|---|---|---|---|---|---|---|"]
        else:
            linhas.append("_nada em voo_")
        for i in r["itens"]:
            if not r["gh"]:
                pr = "?"
            elif i["pr"]:
                pr = f"#{i['pr']['numero']}" + (f" (pilha ← {i['pilha_base']})" if i["pilha_base"] else "")
            else:
                pr = "—"
            branch = i["branch"] + (" (gone)" if i["upstream_gone"] else "")
            est = i["estado"] + (f" fila:{i['fila']}" if i["fila"] else "")
            linhas.append(f"| {i['ordem']} | {branch} | {est} | {i['dias']} | {i['novos']} | {pr} | "
                          f"{i['worktree'] or '—'} | {_sessoes(i['sessoes'])} | {i['plano'] or '—'} |")
        linhas.append("")
        for c in r["checkouts"]:
            linhas.append(f"checkout: {c['caminho']}" + (f" ({', '.join(c['flags'])})" if c["flags"] else "") +
                          f" · {c['branch']} · {c['sujos']} sujos · sessões {_sessoes(c['sessoes'])}")
        linhas.append("")
    linhas.append(f"## mudanças recentes ({MERGEADAS_DIAS} dias)")
    for r in vista["repos"]:
        for i in r["mergeadas"]:
            linhas.append(f"- {r['repo']} {i['bloco'].replace('_', ' ')} #{i['numero']} {i['branch']} · "
                          f"{i['mergeada_em']}" + (f" ({i['tag']})" if i["bloco"] == "saiu" and i["tag"] else ""))
    return "\n".join(linhas) + "\n"


def main() -> None:
    if "--selftest" in sys.argv[1:]:
        selftest()
        return
    p = argparse.ArgumentParser(description="Vista da fila de integração (delta-114).")
    p.add_argument("alvo", nargs="?", default=".", help="repo git ou pasta-mãe de repos (default: .)")
    p.add_argument("--repo", action="append", default=[], help="repo extra, repetível (ex.: o deltaspec)")
    p.add_argument("--cronograma", help="cronograma.md do portfólio (seção ## Marcos + **Dir:**)")
    p.add_argument("--json", action="store_true", help="contrato para consumidores (references/integracao.md)")
    p.add_argument("--fetch", action="store_true", help=f"git fetch --prune antes de ler (opt-in; {FETCH_TIMEOUT}s/repo)")
    a = p.parse_args()
    alvo = Path(a.alvo).resolve()
    repos = repos_do_alvo(alvo, a.repo)
    if not repos:
        die(f"nenhum repositório git em {alvo}")
    hoje, agora = date.today(), datetime.now()
    marcos = {}
    if a.cronograma:
        arq = Path(a.cronograma)
        if not arq.exists() or arq.is_dir():
            die(f"cronograma não encontrado: {arq}")
        texto = arq.read_text(encoding="utf-8")
        marcos = marcos_por_dir(texto, hoje)
        for aviso in avisos_cronograma(texto, hoje):
            print(aviso, file=sys.stderr)
    vista = montar(repos, marcos, hoje, agora, a.fetch)
    print(json.dumps(vista, ensure_ascii=False, indent=1) if a.json else render(vista), end="")


# ---------------------------------------------------------------- selftest


def selftest_parse() -> None:
    refs = parse_refs("main|2026-09-01|origin/main|\norigin/main|2026-09-01||\n"
                      "feat/a|2026-09-03|origin/feat/a|\norigin/feat/a|2026-09-05||\n"
                      "fix/b|2026-09-07|origin/develop|[ahead 3]\norigin/docs/c|2026-09-02||\n"
                      "chore/x|2026-09-04|origin/chore/x|[gone]\n"
                      "origin/HEAD|2026-09-01||\norigin/release-please--branches--main|2026-09-06||\n")
    assert set(refs) == {"feat/a", "fix/b", "docs/c", "chore/x"}, refs
    assert refs["feat/a"] == {"data": "2026-09-05", "upstream": "origin/feat/a", "local": True, "remota": True, "gone": False}
    # fix/b: upstream aponta pra OUTRA branch (herdado da base, nunca publicada com o próprio nome) — não é gone
    assert refs["fix/b"] == {"data": "2026-09-07", "upstream": "origin/develop", "local": True, "remota": False, "gone": False}
    assert refs["docs/c"]["local"] is False and refs["docs/c"]["upstream"] is None
    assert refs["chore/x"]["gone"] is True and refs["chore/x"]["remota"] is False  # upstream removido de verdade
    wts = parse_worktrees("worktree /r\nHEAD aaa\nbranch refs/heads/main\n\n"
                          "worktree /r/.claude/worktrees/x\nHEAD bbb\nbranch refs/heads/feat/x\nlocked\n\n"
                          "worktree /tmp/y\nHEAD ccc\ndetached\nprunable gitdir file points to non-existent location\n")
    assert [w["principal"] for w in wts] == [True, False, False]
    assert wts[1]["branch"] == "feat/x" and wts[1]["locked"] and not wts[1]["prunable"]
    assert wts[2]["detached"] and wts[2]["prunable"] and wts[2]["branch"] is None
    assert parse_worktrees("") == []
    assert label_fila(["fila:2", "bug"]) == 2 and label_fila(["fila:alta"]) is None
    assert label_fila(["fila:0"]) is None and label_fila(["fila:x"]) is None and label_fila([]) is None
    pr, draft = {"draft": False}, {"draft": True}
    assert [estado(d, None) for d in (0, 2, 3, 7, 8)] == ["ativa", "ativa", "parada", "parada", "defasada"]
    assert [estado(d, pr) for d in (3, 7, 8)] == ["em PR", "em PR", "defasada"]
    assert estado(1, draft) == "draft" and estado(8, draft) == "defasada"
    hoje = date(2026, 9, 7)
    cron = ("# Cronograma\n\n## Marcos\n\n| Marco | Data | Projeto | Base |\n|---|---|---|---|\n"
            "| D0 | 2026-08-03 | todos | portfolio |\n| Entrega | 2026-09-02 | Est | contrato |\n"
            "| Fim | 2026-10-02 | Est | contrato |\n| Entrega | 2026-09-21 | Acad | portfolio |\n"
            "| M1 | D+7 | Est | presumido |\n| X | 2026-09-10 | Est | presumido |\n"
            "| Fim | 2026-10-21 | Acad | portfolio |\n\n## Est\n**Dir:** estoque · **Prazo:** x\n\n"
            "## Acad\n**Dir:** academia · **Prazo:** y\n")
    assert marcos_por_dir(cron, hoje) == {"estoque": ("2026-10-02", "Fim"), "academia": ("2026-09-21", "Entrega")}
    assert marcos_por_dir("# nada\n", hoje) == {}
    assert marcos_por_dir(cron, date(2026, 10, 22)) == {}
    assert avisos_cronograma(cron, hoje) == []
    assert avisos_cronograma("# nada\n", hoje) == ["aviso: cronograma sem a seção '## Marcos' (ou cabeçalho fora do esperado: | Marco | Data | Projeto | Base |)"]
    assert avisos_cronograma(cron, date(2026, 10, 22)) == ["aviso: '## Marcos' lida, nenhum marco futuro com base contrato/portfolio"]
    solto = cron.replace("| Fim | 2026-10-21 | Acad | portfolio |", "| Fim | 2026-10-21 | Solto | portfolio |")
    assert avisos_cronograma(solto, hoje) == ["aviso: projeto 'Solto' tem marco mas não tem '**Dir:**'"]
    desalinhado = cron.replace("| Marco | Data | Projeto | Base |", "| Marco | Projeto | Data | Base |")
    assert avisos_cronograma(desalinhado, hoje) == ["aviso: cronograma sem a seção '## Marcos' (ou cabeçalho fora do esperado: | Marco | Data | Projeto | Base |)"]
    print("integracao selftest_parse: OK (22 casos)")


def selftest_ordenar() -> None:
    def it(branch, data="2026-09-01", pr=None, fila=None):
        return {"branch": branch, "data": data, "pr": pr, "fila": fila}

    def pr(n, base="main", criada="2026-09-01"):
        return {"numero": n, "base": base, "draft": False, "criada": criada, "labels": [], "url": ""}

    # pilha a←b←c contígua logo após a raiz, mesmo com c mais antiga que a raiz
    itens = [it("c", "2026-08-01", pr(3, "b")), it("solta", "2026-08-15", pr(9, criada="2026-08-20")),
             it("a", pr=pr(1, criada="2026-08-25")), it("b", pr=pr(2, "a"))]
    fora = ordenar(itens, "main")
    assert [i["branch"] for i in fora] == ["solta", "a", "b", "c"], [i["branch"] for i in fora]
    assert [i["pilha_base"] for i in fora] == [None, None, "a", "b"]
    assert [i["ordem"] for i in fora] == [1, 2, 3, 4]
    # fila:N sobrepõe PR mais antiga; PR vence branch sem PR; empate de data → nome
    itens = [it("x", pr=pr(1, criada="2026-08-01")), it("y", pr=pr(2, criada="2026-08-10"), fila=1),
             it("z", "2026-07-01"), it("w", "2026-07-01")]
    assert [i["branch"] for i in ordenar(itens, "main")] == ["y", "x", "w", "z"]
    # ciclo não trava; base ausente vira raiz própria com pilha_base informativo
    itens = [it("p", pr=pr(1, "q")), it("q", pr=pr(2, "p")), it("r", pr=pr(3, "sumida"))]
    fora = ordenar(itens, "main")
    assert len(fora) == 3 and next(i for i in fora if i["branch"] == "r")["pilha_base"] == "sumida"
    # release/* fura a fila mesmo com fila:1 e pilha (spec R5, emenda 08/09) — a pilha a←b segue contígua depois
    itens = [it("y", pr=pr(2, criada="2026-08-10"), fila=1), it("release/1.2.3", "2026-08-01"),
             it("a", pr=pr(1, criada="2026-08-25")), it("b", pr=pr(3, "a"))]
    assert [i["branch"] for i in ordenar(itens, "main")] == ["release/1.2.3", "y", "a", "b"]
    # entre repos: marco vence sem marco; empate → nome
    blocos = [{"repo": "z", "marco": None}, {"repo": "b", "marco": {"data": "2026-10-02"}},
              {"repo": "a", "marco": {"data": "2026-10-02"}}, {"repo": "c", "marco": {"data": "2026-09-21"}}]
    assert [b["repo"] for b in sorted(blocos, key=chave_repo)] == ["c", "a", "b", "z"]
    print("integracao selftest_ordenar: OK (7 casos)")


def selftest_git() -> None:
    """R1/R2/R6/R7 com git real — molde do selftest_git do debito.py; `gh` substituído por stub."""
    import os
    import tempfile
    global gh_json
    original = gh_json
    with tempfile.TemporaryDirectory() as tmp:
        raiz = Path(tmp).resolve() / "ws"
        r = raiz / "alfa"
        r.mkdir(parents=True)
        env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t",
                   GIT_COMMITTER_EMAIL="t@t", GIT_AUTHOR_DATE="2026-09-01T12:00:00", GIT_COMMITTER_DATE="2026-09-01T12:00:00")

        def g(*a, data=None, cwd=r):
            e = dict(env, GIT_COMMITTER_DATE=data, GIT_AUTHOR_DATE=data) if data else env
            return subprocess.run(["git", "-C", str(cwd), *a], env=e, capture_output=True, text=True, check=True).stdout.strip()

        g("init", "-q", "-b", "main")
        (r / "a").write_text("1", encoding="utf-8")
        g("add", "-A")
        g("commit", "-qm", "base")
        assert base_do_repo(r) == "main"  # sem remoto
        g("checkout", "-qb", "feat/x")
        (r / DIR_PLANOS).mkdir(parents=True)
        (r / DIR_PLANOS / "PLAN_x.md").write_text("p", encoding="utf-8")
        g("add", "-A")
        g("commit", "-qm", "1", data="2026-09-02T12:00:00")
        (r / "b").write_text("2", encoding="utf-8")
        g("add", "-A")
        g("commit", "-qm", "2", data="2026-09-03T12:00:00")
        g("checkout", "-q", "main")
        assert novos(r, "main", "feat/x") == 2 and plano_da_branch(r, "main", "feat/x") == "PLAN_x.md"
        sha = g("rev-parse", "main")
        g("update-ref", "refs/remotes/origin/develop", sha)  # ref remoto sem rede
        assert base_do_repo(r) == "origin/develop"
        # bug do (gone) falso, com git real: branch criada a partir de uma base remota herda o
        # upstream DELA (nunca publicada com o próprio nome) — não pode virar "gone" só por isso.
        # DWIM de upstream ao dar checkout num remote-tracking ref exige remote configurado.
        g("remote", "add", "origin", str(Path(tmp) / "nao-existe"))
        g("checkout", "-qb", "chore/multi-root", "origin/develop")
        fmt_ref = "%(refname:short)|%(committerdate:short)|%(upstream:short)|%(upstream:track)"
        saida_ref = git(r, "for-each-ref", "--format=" + fmt_ref, "refs/heads/chore/multi-root")
        assert parse_refs(saida_ref)["chore/multi-root"]["gone"] is False
        g("update-ref", "-d", "refs/remotes/origin/develop")  # agora o upstream some de verdade
        saida_ref = git(r, "for-each-ref", "--format=" + fmt_ref, "refs/heads/chore/multi-root")
        assert parse_refs(saida_ref)["chore/multi-root"]["gone"] is True
        g("checkout", "-q", "main")
        g("branch", "-D", "chore/multi-root")
        g("remote", "remove", "origin")
        g("update-ref", "refs/remotes/origin/main", sha)
        g("symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
        assert base_do_repo(r) == "origin/main"
        # squash-mergeada fica fora; em worktree com novos=0 fica dentro
        g("checkout", "-qb", "feat/sq")
        (r / "c").write_text("3", encoding="utf-8")
        g("add", "-A")
        g("commit", "-qm", "sq", data="2026-09-04T12:00:00")
        g("checkout", "-q", "main")
        g("merge", "--squash", "-q", "feat/sq")
        g("commit", "-qm", "squash", data="2026-09-05T12:00:00")
        sha_squash = g("rev-parse", "main")
        g("update-ref", "refs/remotes/origin/main", sha_squash)
        wt = Path(tmp).resolve() / "wt-sq"
        g("worktree", "add", "-q", str(wt), "feat/sq")
        (wt / "sujo").write_text("x", encoding="utf-8")
        (r / "a").write_text("mudou", encoding="utf-8")
        g("stash", "push", "-q")
        hoje = date(2026, 9, 7)
        gh_json = lambda *a, **k: None  # noqa: E731 — sem gh
        try:
            bloco = coletar(r, {}, hoje, False)
        finally:
            gh_json = original
        assert bloco["gh"] is False and bloco["fetch"] is None and bloco["marco"] is None
        assert bloco["stashes"] == 1 and bloco["mergeadas"] == []
        por = {i["branch"]: i for i in bloco["itens"]}
        assert set(por) == {"feat/x", "feat/sq"}, set(por)
        x = por["feat/x"]
        assert (x["novos"], x["dias"], x["estado"], x["plano"], x["pr"], x["sessoes"], x["upstream_gone"]) == \
            (2, 4, "parada", "PLAN_x.md", None, None, False), x
        assert por["feat/sq"]["novos"] == 0 and por["feat/sq"]["worktree"] == "wt-sq"
        sujos = {c["caminho"]: c["sujos"] for c in bloco["checkouts"]}
        assert sujos[str(wt)] == 1 and sujos[str(r)] == 0, sujos
        assert all(c["sessoes"] is None for c in bloco["checkouts"])
        assert repos_do_alvo(raiz, [str(r)]) == [r, r] and repos_do_alvo(r, []) == [r]
        # fetch com origin morta: False rápido, vista segue com as refs locais
        g("remote", "add", "origin", str(Path(tmp) / "nao-existe"))
        assert fetch_com_timeout(r) is False
        gh_json = lambda *a, **k: None  # noqa: E731
        try:
            bloco = coletar(r, {}, hoje, True)
            assert bloco["fetch"] is False and {i["branch"] for i in bloco["itens"]} == {"feat/x", "feat/sq"}
            vista = montar([r], {}, hoje, datetime(2026, 9, 7, 12), False)
            texto = render(vista)
            assert texto == render(vista) and "gh ?" in texto and texto.endswith("## mudanças recentes (7 dias)\n")
            linha = next(l for l in texto.splitlines() if l.startswith("| 1 |"))
            colunas = [c.strip() for c in linha.strip("|").split("|")]
            assert colunas == ["1", "feat/x", "parada", "4", "2", "?", "—", "?", "PLAN_x.md"], colunas
            assert "fetch falhou" in render(montar([r], {}, hoje, datetime(2026, 9, 7, 12), True))
            json.loads(json.dumps(vista))
            com_marco = montar([r], {"alfa": ("2026-09-21", "Entrega")}, hoje, datetime(2026, 9, 7, 12), False)
            assert "marco 2026-09-21 (Entrega)" in render(com_marco) and "sessões ?" in render(com_marco)
        finally:
            gh_json = original

        g("tag", "v1.0.0", sha_squash)  # tag real no commit "saiu" — resolução exigida em 08/09, sem dict fabricado

        def stub(repo, *args):
            if "--search" in args:
                assert args[args.index("--search") + 1] == "merged:>=2026-08-31", args
                return [{"number": 7, "headRefName": "feat/sq", "mergedAt": "2026-09-05T10:00:00Z",
                         "mergeCommit": {"oid": sha_squash}}]
            return [{"number": 5, "headRefName": "feat/x", "baseRefName": "main", "isDraft": True,
                     "createdAt": "2026-09-03T10:00:00Z", "labels": [{"name": "fila:1"}], "url": "u"}]

        gh_json = stub
        try:
            bloco = coletar(r, {}, hoje, False)
        finally:
            gh_json = original
        por = {i["branch"]: i for i in bloco["itens"]}
        assert por["feat/x"]["estado"] == "draft" and por["feat/x"]["fila"] == 1 and por["feat/x"]["pr"]["numero"] == 5
        assert bloco["gh"] is True and len(bloco["mergeadas"]) == 2
        entrou = next(m for m in bloco["mergeadas"] if m["bloco"] == "entrou")
        saiu = next(m for m in bloco["mergeadas"] if m["bloco"] == "saiu")
        assert entrou == {"numero": 7, "branch": "feat/sq", "mergeada_em": "2026-09-05",
                          "bloco": "entrou", "tag": None}, entrou
        # nome da tag chega ao bloco "saiu" via git real (for-each-ref refs/tags), não por dict fabricado
        assert saiu == {"numero": 7, "branch": "feat/sq", "mergeada_em": "2026-09-05",
                        "bloco": "saiu", "tag": "v1.0.0"}, saiu
        assert repo_gh("git@github.com:acme-tech/exemplo-pmo.git") == "acme-tech/exemplo-pmo"
        assert repo_gh("https://github.com/a/b") == "a/b" and repo_gh("gitlab.com/a/b") is None
        g("worktree", "remove", "--force", str(wt))
    print("integracao selftest_git: OK (27 casos)")


def selftest() -> None:
    selftest_parse()
    selftest_ordenar()
    selftest_git()
    print("integracao selftest: OK (56 casos)")


if __name__ == "__main__":
    main()
