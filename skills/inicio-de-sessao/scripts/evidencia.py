#!/usr/bin/env python3
"""Camada de evidência do painel: tudo que toca `git`, `gh` e disco, e nada além disso.

Devolve dado cru para o núcleo puro classificar. A separação é o que faz o autoteste do
`fila.py` bastar para as regras: aqui não há decisão, só coleta.

REGRAS — este texto é o dono; a SKILL.md aponta para cá e não as reescreve.

Base de um repositório = a primeira ref de `bases` da config que existir nele.
Sem `git fetch` não há painel: fetch que falha derruba a execução, porque estado de ontem
apresentado como de hoje é pior que a ausência dele.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

LIMITE_PRS = 200
RE_ORIGIN = re.compile(r"github\.com[:/](.+?)(?:\.git)?$")
RE_SPEC = re.compile(r"^(\d{3})-[\w-]+$")


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)


def saida(repo, *args):
    r = git(repo, *args)
    return r.stdout.splitlines() if r.returncode == 0 else []


def existe(repo, ref, caminho):
    return git(repo, "cat-file", "-e", f"{ref}:{caminho}").returncode == 0


def fetch(repo):
    r = git(repo, "fetch", "--all", "--prune")
    if r.returncode:
        sys.exit(f"git fetch falhou em {repo} — sem fetch não há painel.\n{r.stderr.strip()}\n"
                 "(num sandbox de agente o fetch costuma falhar por sistema de arquivos somente "
                 "leitura ou por chave recusada: rode fora dele)")


def base_de(repo, bases):
    for b in bases:
        if git(repo, "rev-parse", "--verify", "-q", b).returncode == 0:
            return b
    sys.exit(f"{repo} não tem {' nem '.join(bases)}")


def prs_de(repo):
    url = (saida(repo, "remote", "get-url", "origin") or [""])[0].strip()
    m = RE_ORIGIN.search(url)
    if not m:
        sys.exit(f"origin de {repo} não é do GitHub: {url!r}")
    r = subprocess.run(["gh", "pr", "list", "-R", m.group(1), "--state", "all", "--limit", str(LIMITE_PRS),
                        "--json", "number,headRefName,state,title"], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"gh pr list falhou em {repo}: {r.stderr.strip()}")
    return json.loads(r.stdout)


def deltas_de(repo, base):
    """(ativas, arquivadas) — nomes de pasta `NNN-nome` em specs/ e specs/_archive/ da base."""
    arquivadas = {Path(p).name for p in saida(repo, "ls-tree", "--name-only", base, "specs/_archive/")}
    ativas = [Path(p).name for p in saida(repo, "ls-tree", "-d", "--name-only", base, "specs/")]
    return [n for n in ativas if RE_SPEC.match(n) and n not in arquivadas], arquivadas


def ahead_de(repo, base, ref):
    return int((saida(repo, "rev-list", "--count", f"{base}..{ref}") or ["0"])[0]) if ref else 0


def ahead_max(repo, base, nnn, branch, refs, ligado):
    """Maior distância da base entre as refs ligadas à delta. `ligado` vem do núcleo puro."""
    ligadas = [r for r in refs if ligado(nnn, branch, r.removeprefix("origin/"))]
    return max((ahead_de(repo, base, r) for r in ligadas), default=0)


def liberacao(repo, caminho, releases):
    for ref in ("origin/main", *releases):
        if existe(repo, ref, caminho):
            return ref.removeprefix("origin/")
    return "—"


def ler_yaml(texto):
    import yaml  # só o I/O precisa; o selftest do núcleo roda sem PyYAML
    return yaml.safe_load(texto) if texto else None


def ler_fila(cfg):
    """Fila do repositório que a config declara dono, lida da base dele. None = não existe."""
    repo = cfg["repos"][cfg["fila"]["repo"]]
    r = git(repo, "show", f"{base_de(repo, cfg['bases'])}:{cfg['fila']['caminho']}")
    return ler_yaml(r.stdout) if r.returncode == 0 else None


def worktrees_de(raiz):
    """[{caminho, head, branch}] do `git worktree list --porcelain`; branch None = HEAD solto.

    O parse é do núcleo puro (delta-128), para que o selftest o cubra; aqui só a chamada.
    """
    import fila as nucleo  # importado aqui: o módulo é irmão, e só esta função precisa dele
    return [{**w, "caminho": Path(w["caminho"]), "branch": w["branch"] or None}
            for w in nucleo.parse_worktrees(saida(raiz, "worktree", "list", "--porcelain"))]


def worktree_ref(raiz, base, wt, nnn, prs, agora):
    """Dado cru de uma worktree para o quadro (delta-128): dias desde o último commit, commits
    à frente da base, PR mergeado da branch, e os textos de tasks.md/plan.md da delta `nnn`
    lidos na ref da branch (None = arquivo ausente). Só leitura."""
    ref = wt["branch"] or wt["head"]
    carimbo = saida(raiz, "log", "-1", "--format=%ct", ref)
    ativas, arquivadas = deltas_de(raiz, ref) if nnn else ([], set())
    pasta = next((n for n in ativas if n[:3] == nnn), "")

    def texto(arquivo):
        r = git(raiz, "show", f"{ref}:specs/{pasta}/{arquivo}") if pasta else None
        return r.stdout if r is not None and r.returncode == 0 else None

    return {"dias": (agora - int(carimbo[0])) // 86400 if carimbo else None,
            "ahead": ahead_de(raiz, base, ref),
            "pr_merged": any(p["state"] == "MERGED" and p["headRefName"] == wt["branch"] for p in prs),
            "prova": any(n[:3] == nnn for n in deltas_de(raiz, base)[1]) if nnn else False,
            "tasks": texto("tasks.md"), "plan": texto("plan.md")}


def bancada_de(raiz, base, prs):
    """Worktrees do repositório + branches locais fora deles, com sujeira, ahead e PR aberto."""
    abertos = {p["headRefName"] for p in prs if p["state"] == "OPEN"}
    base_local = base.removeprefix("origin/")
    entradas, com_wt = [], set()
    for wt in worktrees_de(raiz):
        br, st = wt["branch"], saida(wt["caminho"], "status", "--porcelain")
        com_wt.add(br)
        entradas.append({"nome": wt["caminho"].name, "branch": br or "(HEAD solto)", "wt": True,
                         "detached": not br, "base": br == base_local,
                         "sujo": sum(not l.startswith("??") for l in st),
                         "novos": sum(l.startswith("??") for l in st),
                         "ahead": ahead_de(raiz, base, br), "pr": br in abertos})
    for br in saida(raiz, "branch", "--format=%(refname:short)"):
        if br not in com_wt:
            entradas.append({"nome": br, "branch": br, "wt": False, "detached": False,
                             "base": br == base_local, "sujo": 0, "novos": 0,
                             "ahead": ahead_de(raiz, base, br), "pr": br in abertos})
    return entradas


def colher(cfg, itens, ligado, ligar_prs, siglas=None):
    """Por repositório da config (`siglas`; default a ordem da fila): fetch, base, refs, PRs e
    deltas ativas.

    Devolve (info por sigla, provas, evidências por item, alertas). As funções de ligação
    chegam por argumento porque a regra de quem pertence a qual delta é do núcleo puro.
    """
    info, provas, evid, alertas = {}, {}, {}, []
    for sigla in siglas or cfg["ordem"]:
        raiz = cfg["repos"][sigla]
        fetch(raiz)
        base = base_de(raiz, cfg["bases"])
        refs = set(saida(raiz, "for-each-ref", "--format=%(refname:short)", "refs/remotes/origin", "refs/heads"))
        prs = prs_de(raiz)
        ativas, _ = deltas_de(raiz, base)
        info[sigla] = {"raiz": raiz, "base": base, "refs": refs, "ativas": ativas, "prs": prs}
        meus = [it for it in itens if it["repo"] == sigla]
        for it in meus:
            provas[it["id"]] = existe(raiz, base, it["arquivo_prova"])
            evid[it["id"]] = {"prs": ligar_prs(it["nnn"], it.get("branch"), prs),
                              "ahead": ahead_max(raiz, base, it["nnn"], it.get("branch"), refs, ligado)}
        na_fila = {it["nnn"] for it in meus}
        alertas += [f"delta ativa fora da fila: {sigla}/{n[:3]} ({n}) — `semear --so-novos` gera o item"
                    for n in ativas if n[:3] not in na_fila]
    return info, provas, evid, alertas


def caminho_script(skill, arquivo):
    """Script de outra skill do plugin: raiz do plugin, senão o módulo irmão. NUNCA por varredura.

    Existem cópias desses scripts espalhadas pelos repositórios de quem usa o framework, e elas
    divergem por construção — procurar a mais próxima traria a errada em silêncio.
    """
    candidatos = []
    raiz = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if raiz:
        candidatos.append(Path(raiz) / "skills" / skill / "scripts" / arquivo)
    candidatos.append(Path(__file__).resolve().parents[2] / skill / "scripts" / arquivo)
    return next((c for c in candidatos if c.is_file()), None)


def caminho_debito():
    return caminho_script("handoff", "debito.py")


def fila_debito(raiz_repo):
    """(texto da tabela, erro). Subprocesso, nunca import: o código de saída importa."""
    script = caminho_debito()
    if not script:
        return "", "registro de débitos não encontrado na raiz do plugin nem no módulo irmão"
    r = subprocess.run([sys.executable, str(script), "fila", str(raiz_repo)],
                       capture_output=True, text=True)
    if r.returncode:
        bruto = (r.stderr or r.stdout).strip().splitlines()
        return "", f"registro de débitos abortou: {bruto[-1] if bruto else 'sem mensagem'}"
    return r.stdout, ""


def arquivos_desde(info_repo, desde, pasta):
    """Caminhos adicionados na pasta desde a data, pela base do repositório."""
    return saida(info_repo["raiz"], "log", info_repo["base"], f"--since={desde}",
                 "--diff-filter=A", "--name-only", "--format=", "--", pasta)


def caminho_higiene():
    return caminho_script("audit-workspace", "audit_workspace.py")


def higiene_em_curso(higiene):
    """(processo, erro). Nada de esperar aqui: a varredura é a parte mais cara do painel e
    roda escondida atrás do fetch. Seção ausente na config é silêncio legítimo; ferramenta
    ausente com a seção declarada é alerta, nunca silêncio."""
    if not higiene:
        return None, ""
    script = caminho_higiene()
    if not script:
        return None, ("auditoria de higiene pedida na config, mas o script não está na raiz "
                      "do plugin nem no módulo irmão")
    return subprocess.Popen(
        [sys.executable, str(script), str(higiene["raiz"]), "--profundidade",
         str(higiene["profundidade"]), "--apenas-git"]
        + sum([["--excluir", x] for x in higiene["excluir"]], []),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True), ""


def colher_higiene(processo):
    """(texto, erro) da varredura disparada antes. Falha vira alerta, nunca omissão."""
    if processo is None:
        return "", ""
    saida_, erro = processo.communicate()
    if processo.returncode not in (0, 1):  # 1 = achados; acima disso é falha de execução
        bruto = (erro or saida_).strip().splitlines()
        return "", f"auditoria de higiene abortou: {bruto[-1] if bruto else 'sem mensagem'}"
    return saida_, ""


def handoffs_desde(info_repo, desde):
    """Arquivos de handoff de sessão adicionados na base desde a data."""
    return arquivos_desde(info_repo, desde, ".claude/handoffs")


def licoes_alteradas(info_repo, desde):
    """Quantos commits tocaram o arquivo de lições do repositório na janela."""
    return len(saida(info_repo["raiz"], "log", info_repo["base"], f"--since={desde}",
                     "--format=%h", "--", "debts/LICOES.md"))


def linhas_do_ledger(caminho):
    """Linhas do arquivo de pendências fora de projeto; ausente devolve vazio, sem erro."""
    try:
        return caminho.read_text(encoding="utf-8").splitlines() if caminho and caminho.is_file() else []
    except OSError:
        return []


def timestamps_de_sessao(raiz_estado):
    """Horários dos registros de sessão do harness, em UTC, como vêm."""
    marcas = []
    for arquivo in sorted(raiz_estado.glob("*/*.jsonl")) if raiz_estado.is_dir() else []:
        try:
            with arquivo.open(encoding="utf-8", errors="ignore") as f:
                primeira = f.readline()
        except OSError:
            continue
        m = re.search(r'"timestamp"\s*:\s*"([^"]+)"', primeira)
        if m:
            marcas.append(m.group(1))
    return marcas


def texto_na_base(info_repo, caminho):
    return git(info_repo["raiz"], "show", f"{info_repo['base']}:{caminho}").stdout


def log_desde(info_repo, desde, limite=10):
    return saida(info_repo["raiz"], "log", info_repo["base"], "--oneline", f"-{limite}", f"--since={desde}")


def entrou_desde(info_repo, desde, caminho):
    return bool(saida(info_repo["raiz"], "log", info_repo["base"], f"--since={desde}",
                      "--diff-filter=A", "--format=%h", "--", caminho))


def releases_de(info_repo):
    return sorted(r for r in info_repo["refs"] if r.startswith("origin/release/"))
