#!/usr/bin/env python3
"""Checks do bloco D — `.claude/` só com o que o Claude Code lê, mais `handoffs/`
(skill project-review-dotclaude, delta-123).

Dono da doutrina, da severidade e da correção: ../references/catalogo.md. Quem descobre
repositórios, agrupa por achado e imprime o relatório é o audit_workspace.py
(`--apenas-dotclaude`); este módulo só responde "o que está errado neste repositório".

  D1  caminho rastreado em .claude/ fora do que o Claude Code lê              ALTO
  D2  .claude/commands/ rastreado (formato antigo de skills/)                 MÉDIO
  D3  item não rastreado em .claude/ sem regra no .gitignore versionado       ALTO
  D4  artefato de execução rastreado em .claude/                              MÉDIO
  D5  hook citado no settings.json e não rastreado                            ALTO
  D6  handoff mais antigo que a retenção e sem citação no HANDOFF.md          informativo
  D7  .claude/handoffs/ rastreado sem HANDOFF.md na raiz                      ALTO
  D8  arquivo que o D1 acusaria, citado por arquivo vivo                      ALTO

Uso: dotclaude.py --selftest
"""
import json
import re
import subprocess
import sys
from datetime import date
from fnmatch import fnmatch
from pathlib import Path

# ESPELHO do catálogo. Duplicação deliberada — doutrina legível lá, política executável
# aqui — e vigiada: o selftest parseia o catálogo e exige igualdade.
PERMITIDOS = frozenset({"CLAUDE.md", "settings.json", "rules", "skills", "commands",
                        "output-styles", "agents", "workflows", "agent-memory",
                        "hooks", "handoffs", ".gitignore"})
EXECUCAO = frozenset({"worktrees", ".cc-writes", "__pycache__", "settings.local.json",
                      "agent-memory-local", "*.lock"})  # padrões do fnmatch, por segmento
SEVERIDADE = {"D1": "ALTO", "D2": "MÉDIO", "D3": "ALTO", "D4": "MÉDIO", "D5": "ALTO",
              "D6": "informativo", "D7": "ALTO", "D8": "ALTO"}
NIVEIS = ("ALTO", "MÉDIO", "informativo")
ORDEM = tuple(sorted(SEVERIDADE, key=lambda c: (NIVEIS.index(SEVERIDADE[c]), int(c[1:]))))

RETENCAO_HANDOFF_DIAS = 60
# O Claude Code grava os dois no ignore global da máquina; o D3 não os cobra onde quer que a
# regra more. Rastreados, seguem sendo D4.
IGNORADO_PELO_HARNESS = frozenset({"settings.local.json", ".cc-writes"})
# Histórico não ancora: qualquer pasta _archive/ (specs/, debts/, docs/…) e os dois diários.
PASTA_HISTORICO = "_archive"
ARQUIVOS_HISTORICO = ("CHANGELOG.md", "HANDOFF.md")
PASTA_REGISTRO = "debts"  # registrar o achado não pode mudar o achado
RE_DATA_HANDOFF = re.compile(r"_(\d{4})_(\d{2})_(\d{2})\.md$")
RE_HOOK_CITADO = re.compile(r"\.claude/hooks/[\w./-]+")
RE_REGRA = re.compile(r"^(.*?):(\d+):(.*)$")  # fonte:linha:padrão, antes do TAB



def _git(repo: Path, *args: str) -> list[str]:
    """Linhas de um comando git só-leitura (NUL com -z); [] se falhar. O audit_workspace.py
    tem o seu, que devolve texto: importar de lá seria import circular."""
    proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    if proc.returncode != 0:
        return []
    return [l for l in proc.stdout.split("\0" if "-z" in args else "\n") if l]


def _entrada(caminho: str) -> str:
    """Primeiro componente depois de .claude/ — a unidade que a doutrina julga."""
    return caminho.split("/")[1]


def _raiz_execucao(caminho: str) -> str | None:
    """Trecho do caminho até o artefato de execução, ou None se não for um."""
    partes = caminho.rstrip("/").split("/")
    for i, parte in enumerate(partes[1:], 1):
        if any(fnmatch(parte, padrao) for padrao in EXECUCAO):
            return "/".join(partes[:i + 1]) + ("/" if i + 1 < len(partes) or caminho.endswith("/") else "")
    return None


def _vivo(caminho: str) -> bool:
    """Arquivo que ancora: fora do histórico e do registro de débito e, em .claude/, só o que o
    Claude Code lê — handoffs/ não. O que é texto quem decide é o `git grep -I`."""
    partes = caminho.split("/")
    if caminho in ARQUIVOS_HISTORICO or PASTA_HISTORICO in partes[:-1] or partes[0] == PASTA_REGISTRO:
        return False
    return partes[0] != ".claude" or (partes[1] in PERMITIDOS and partes[1] != "handoffs")


def _ancoras(repo: Path, candidatos: list[str]) -> dict[str, str]:
    """candidato → primeiro arquivo vivo que o cita por <pasta>/<nome>. O par e não o
    basename: plano e prompt de uma mesma sessão costumam ter o mesmo nome."""
    agulhas = {"/".join(c.split("/")[-2:]): c for c in candidatos}
    args = ["grep", "-I", "-F", "-o", "--null"] + [x for agulha in agulhas for x in ("-e", agulha)]
    achou: dict[str, str] = {}
    for linha in _git(repo, *args):
        arquivo, _, trecho = linha.partition("\0")
        candidato = agulhas.get(trecho)
        if candidato and candidato not in achou and _vivo(arquivo):
            achou[candidato] = arquivo
    return achou


def check_d1_d8(repo: Path, rastreados: list[str]) -> list[tuple[str, str]]:
    fora = [r for r in rastreados if r.startswith(".claude/")
            and _entrada(r) not in PERMITIDOS and _raiz_execucao(r) is None]
    if not fora:
        return []
    ancorados = _ancoras(repo, fora)
    achados = [("D8", f"{c} citado por {v} — documento canônico no lugar errado: "
                      "mover para docs/ ou scripts/") for c, v in sorted(ancorados.items())]
    por_entrada: dict[str, int] = {}
    for r in fora:
        if r not in ancorados:
            rotulo = ".claude/" + _entrada(r) + ("/" if r.count("/") > 1 else "")
            por_entrada[rotulo] = por_entrada.get(rotulo, 0) + 1
    achados += [("D1", f"{e} com {n} arquivo(s) rastreado(s) fora do que o Claude Code lê")
                for e, n in sorted(por_entrada.items())]
    return achados


def check_d2(rastreados: list[str]) -> list[tuple[str, str]]:
    n = sum(1 for r in rastreados if r.startswith(".claude/commands/"))
    return [("D2", f".claude/commands/ com {n} arquivo(s) — formato antigo: um "
                   ".claude/skills/<nome>/SKILL.md por comando")] if n else []


def _fonte_da_regra(repo: Path, sonda: str) -> str | None:
    """Arquivo cuja regra ignora `sonda`, ou None se nenhuma ignora (ou se a regra é !negação)."""
    linhas = _git(repo, "check-ignore", "-v", "--", sonda)
    m = RE_REGRA.match(linhas[0].split("\t", 1)[0]) if linhas else None
    if not m or m.group(3).startswith("!"):
        return None
    return m.group(1)


def check_d3(repo: Path, rastreados: list[str]) -> list[tuple[str, str]]:
    com_rastreado = {_entrada(r) for r in rastreados if r.startswith(".claude/")}
    versionados = set(rastreados)
    candidatos = set()
    for item in (repo / ".claude").iterdir():
        # config oficial não versionada é trabalho em andamento: o conselho seria versionar,
        # não ignorar — fica fora do D3 (achado da primeira rodada num workspace real)
        if item.name in com_rastreado or item.name in IGNORADO_PELO_HARNESS or item.name in PERMITIDOS:
            continue
        candidatos.add(f".claude/{item.name}" + ("/" if item.is_dir() else ""))
    # artefato de execução dentro de entrada que tem algo rastreado (ex.: hooks/__pycache__/)
    for caminho in _git(repo, "ls-files", "-o", "--directory", "-z", "--", ".claude/"):
        raiz = _raiz_execucao(caminho) if _entrada(caminho) in com_rastreado else None
        if raiz and raiz.rstrip("/").rsplit("/", 1)[1] not in IGNORADO_PELO_HARNESS:
            candidatos.add(raiz)
    achados = []
    for rotulo in sorted(candidatos):
        # o check-ignore só herda a exclusão de uma pasta quando recebe um caminho de dentro dela
        fonte = _fonte_da_regra(repo, f"{rotulo}x" if rotulo.endswith("/") else rotulo)
        if fonte in versionados:
            continue
        motivo = f"ignorado só por {fonte}" if fonte else "nenhuma regra o ignora"
        achados.append(("D3", f"{rotulo} não rastreado sem regra no .gitignore versionado ({motivo})"))
    return achados


def check_d4(rastreados: list[str]) -> list[tuple[str, str]]:
    raizes = sorted({raiz for r in rastreados if r.startswith(".claude/")
                     and (raiz := _raiz_execucao(r)) is not None})
    return [("D4", f"{raiz} rastreado — artefato de execução: git rm --cached e regra no .gitignore")
            for raiz in raizes]


def check_d5(repo: Path, rastreados: list[str]) -> list[tuple[str, str]]:
    if ".claude/settings.json" not in rastreados:
        return []
    try:
        dados = json.loads((repo / ".claude" / "settings.json").read_text(encoding="utf-8"))
    except OSError:
        return []
    except ValueError:
        return [("D5", ".claude/settings.json rastreado não é JSON válido — o Claude Code não lê hook nenhum dele")]
    hooks = dados.get("hooks", {}) if isinstance(dados, dict) else {}
    versionados = set(rastreados)
    return [("D5", f"{c} citado em .claude/settings.json e não rastreado — o hook não chega a quem clona")
            for c in sorted(set(RE_HOOK_CITADO.findall(json.dumps(hooks, ensure_ascii=False)))) if c not in versionados]


def check_d6_d7(repo: Path, rastreados: list[str], hoje: date) -> list[tuple[str, str]]:
    handoffs = [r for r in rastreados if r.startswith(".claude/handoffs/")]
    if not handoffs:
        return []
    if "HANDOFF.md" not in rastreados:
        # sem índice todo handoff velho seria D6 também — ruído por cima do achado que importa
        return [("D7", f".claude/handoffs/ com {len(handoffs)} arquivo(s) e nenhum HANDOFF.md "
                       "na raiz — ninguém chega a eles")]
    try:
        indice = (repo / "HANDOFF.md").read_text(encoding="utf-8", errors="ignore")
    except OSError:  # rastreado e apagado da árvore: conta como índice vazio
        indice = ""
    achados = []
    for h in handoffs:
        m = RE_DATA_HANDOFF.search(h)
        try:
            idade = (hoje - date(*map(int, m.groups()))).days if m else 0
        except ValueError:
            continue
        if idade > RETENCAO_HANDOFF_DIAS and h.rsplit("/", 1)[1] not in indice:
            achados.append(("D6", f"{h} com {idade} dias e sem citação no HANDOFF.md — "
                                  "candidato a sair do repo pela regra de retenção"))
    return achados


def auditar(repo: Path, hoje: date | None = None) -> list[tuple[str, str]]:
    """Achados (Dn, detalhe) de um repositório. Sem .claude/ não há o que auditar."""
    if not (repo / ".claude").is_dir():
        return []
    rastreados = _git(repo, "ls-files", "-z")
    return [*check_d1_d8(repo, rastreados), *check_d2(rastreados), *check_d3(repo, rastreados),
            *check_d4(rastreados), *check_d5(repo, rastreados),
            *check_d6_d7(repo, rastreados, hoje or date.today())]



def _do_catalogo(texto: str) -> tuple[frozenset, frozenset, dict[str, str]]:
    """(permitidos, execução, severidade) lidos do catálogo — só para a sincronia do selftest."""
    linhas = texto.splitlines()

    def lista(rotulo: str) -> frozenset:
        linha = next(l for l in linhas if l.startswith(f"- **{rotulo}:**"))
        return frozenset(t.rstrip("/") for t in re.findall(r"`([^`]+)`", linha))

    severidade = {}
    for l in linhas:
        celulas = [c.strip() for c in l.strip().strip("|").split("|")]
        if len(celulas) >= 3 and re.fullmatch(r"D\d+", celulas[0]):
            severidade[celulas[0]] = celulas[2]
    return lista("Permitidos"), lista("Execução"), severidade



def selftest() -> None:
    """1 fixture por check, nomes sintéticos. Rastreado = no índice (git add): sem commit."""
    import os
    import tempfile

    # hermético: o ignore global e o gitconfig de quem roda não entram nas fixtures do D3
    os.environ.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_COUNT="1",
                      GIT_CONFIG_KEY_0="core.excludesFile", GIT_CONFIG_VALUE_0=os.devnull)

    def _repo(raiz: Path, arquivos: dict[str, str], rastrear: tuple[str, ...]) -> Path:
        subprocess.run(["git", "init", "-q", str(raiz)], check=True)
        for nome, conteudo in arquivos.items():
            (raiz / nome).parent.mkdir(parents=True, exist_ok=True)
            (raiz / nome).write_text(conteudo, encoding="utf-8")
        if rastrear:
            subprocess.run(["git", "-C", str(raiz), "add", "--", *rastrear], check=True)
        return raiz

    def _ids(achados: list[tuple[str, str]]) -> list[str]:
        return [c for c, _ in achados]

    hoje = date(2026, 9, 21)
    config = {
        ".claude/settings.json": json.dumps({"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [
            {"type": "command", "command": 'python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/guarda.py"'}]}]}}),
        ".claude/hooks/guarda.py": "print()\n",
        ".claude/skills/x/SKILL.md": "---\nname: x\n---\n",
        ".claude/handoffs/HANDOFF_a_2026_09_01.md": "sessão\n",
        "HANDOFF.md": "- [a](.claude/handoffs/HANDOFF_a_2026_09_01.md)\n",
        ".gitignore": ".claude/worktrees/\n",
        ".claude/.gitignore": "*.tmp\n",
    }
    limpos = tuple(config)

    with tempfile.TemporaryDirectory() as d:
        # repo limpo: config + handoff citado + worktree ignorado por regra versionada
        r = _repo(Path(d) / "limpo", {**config, ".claude/worktrees/wt/f": "x\n",
                                       ".claude/settings.local.json": "{}\n"}, limpos)
        assert auditar(r, hoje) == [], auditar(r, hoje)

        # sem .claude/ não há o que auditar
        assert auditar(_repo(Path(d) / "vazio", {"a.md": "x\n"}, ("a.md",)), hoje) == []

        # D1 e D8: citado por arquivo vivo vira D8, o resto segue D1. Vivo é todo texto rastreado,
        # sem lista de extensão; em .claude/, o que o Claude Code lê. Não ancoram: histórico
        # (_archive/, CHANGELOG), handoffs/ e debts/ — registrar o achado não pode mudar o achado.
        cfg1 = {**config, ".claude/plans/p.md": "x\n", ".claude/prompts/q.md": "x\n",
                ".claude/notas/n.md": "x\n", ".claude/audits/a.md": "x\n",
                "docs/guia.md": "Ver plans/p.md.\n", "src/app.ts": "// ver notas/n.md\n",
                ".claude/CLAUDE.md": "Detalhe em audits/a.md.\n",
                "CHANGELOG.md": "cita prompts/q.md, mas é histórico\n",
                "docs/_archive/velho.md": "também cita prompts/q.md\n",
                "debts/ativos/DEBT_DT-001-x.md": "o registro do achado cita prompts/q.md\n",
                ".claude/handoffs/HANDOFF_b_2026_09_02.md": "o handoff cita prompts/q.md\n"}
        r = _repo(Path(d) / "d1", cfg1, tuple(cfg1))
        a = auditar(r, hoje)
        assert _ids(a) == ["D8", "D8", "D8", "D1"], a
        assert [det.split(" ")[0] for _, det in a[:3]] == \
            [".claude/audits/a.md", ".claude/notas/n.md", ".claude/plans/p.md"], a
        assert ".claude/prompts/" in a[3][1], a

        # D2: commands/ é legado
        r = _repo(Path(d) / "d2", {**config, ".claude/commands/c.md": "x\n"}, (*limpos, ".claude/commands/c.md"))
        assert _ids(auditar(r, hoje)) == ["D2"], auditar(r, hoje)

        # D3: sem regra nenhuma, e regra só no .git/info/exclude; settings.local.json nunca
        r = _repo(Path(d) / "d3", {**{k: v for k, v in config.items() if k != ".gitignore"},
                                    ".claude/worktrees/wt/f": "x\n", ".claude/.assets/a": "x\n",
                                    ".claude/settings.local.json": "{}\n",
                                    ".claude/agents/novo.md": "em andamento\n",
                                    ".claude/.cc-writes/t": "x\n",
                                    ".claude/hooks/__pycache__/g.pyc": "x"},
                  tuple(k for k in limpos if k != ".gitignore"))
        (r / ".git" / "info" / "exclude").write_text(".claude/worktrees/\n", encoding="utf-8")
        a = auditar(r, hoje)
        assert _ids(a) == ["D3", "D3", "D3"], a
        assert "nenhuma regra" in a[0][1] and ".assets" in a[0][1], a
        assert "nenhuma regra" in a[1][1] and "hooks/__pycache__/" in a[1][1], a
        assert ".git/info/exclude" in a[2][1] and "worktrees" in a[2][1], a

        # regra !negação desfaz o ignore: é como se não houvesse regra
        cfgn = {**config, ".gitignore": ".claude/worktrees/\n!.claude/worktrees/\n",
                ".claude/worktrees/wt/f": "x\n"}
        r = _repo(Path(d) / "neg", cfgn, limpos)
        a = auditar(r, hoje)
        assert _ids(a) == ["D3"] and "nenhuma regra" in a[0][1], a

        # D4: artefato de execução rastreado
        r = _repo(Path(d) / "d4", {**config, ".claude/scheduled_tasks.lock": "1\n",
                                    ".claude/hooks/__pycache__/g.pyc": "x",
                                    ".claude/agent-memory-local/m.md": "x\n"},
                  (*limpos, ".claude/scheduled_tasks.lock", ".claude/hooks/__pycache__/g.pyc",
                   ".claude/agent-memory-local/m.md"))
        a = auditar(r, hoje)
        assert _ids(a) == ["D4", "D4", "D4"], a

        # D5: hook citado e não rastreado
        cfg5 = {**config, ".claude/hooks/guarda-ção.py": "print()\n",
                ".claude/settings.json": json.dumps({"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [
                    {"type": "command", "command": 'python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/sumiu.py"'},
                    {"type": "command", "command": 'python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/guarda-ção.py"'}]}]}})}
        r = _repo(Path(d) / "d5", cfg5, tuple(cfg5))
        a = auditar(r, hoje)
        assert _ids(a) == ["D5"] and ".claude/hooks/sumiu.py" in a[0][1], a

        # settings.json rastreado que não parseia: o Claude Code não lê hook nenhum dele
        r = _repo(Path(d) / "d5m", {**config, ".claude/settings.json": "{ não é json"}, limpos)
        a = auditar(r, hoje)
        assert _ids(a) == ["D5"] and "não é JSON" in a[0][1], a

        # D7: handoffs sem índice — e sem D6, que seria ruído por cima do D7
        cfg7 = {k: v for k, v in config.items() if k != "HANDOFF.md"}
        cfg7[".claude/handoffs/HANDOFF_velho_2026_01_05.md"] = "x\n"
        r = _repo(Path(d) / "d7", cfg7, tuple(cfg7))
        assert _ids(auditar(r, hoje)) == ["D7"], auditar(r, hoje)

        # D6: velho e não citado é informativo; recente ou citado, nada
        cfg6 = {**config, ".claude/handoffs/HANDOFF_velho_2026_01_05.md": "x\n",
                ".claude/handoffs/HANDOFF_citado_2026_01_05.md": "x\n"}
        cfg6["HANDOFF.md"] += "- [c](.claude/handoffs/HANDOFF_citado_2026_01_05.md)\n"
        r = _repo(Path(d) / "d6", cfg6, tuple(cfg6))
        a = auditar(r, hoje)
        assert _ids(a) == ["D6"] and "HANDOFF_velho" in a[0][1] and "259 dias" in a[0][1], a
        (r / "HANDOFF.md").unlink()  # rastreado e apagado da árvore: índice vazio, sem quebrar
        assert _ids(auditar(r, hoje)) == ["D6", "D6"], auditar(r, hoje)

    # Sincronia catálogo × constantes — a duplicação é deliberada, então é vigiada.
    catalogo = Path(__file__).resolve().parents[1] / "references" / "catalogo.md"
    permitidos, execucao, severidade = _do_catalogo(catalogo.read_text(encoding="utf-8"))
    assert permitidos == PERMITIDOS, f"catálogo={sorted(permitidos)} código={sorted(PERMITIDOS)}"
    assert execucao == EXECUCAO, f"catálogo={sorted(execucao)} código={sorted(EXECUCAO)}"
    assert severidade == SEVERIDADE, f"catálogo={severidade} código={SEVERIDADE}"

    print("selftest: OK (11 fixtures D — repo limpo, sem .claude/, D1+D8 com a definição de "
          "arquivo vivo, D2, D3 no primeiro nível e aninhado, !negação, D4, D5 com acento e JSON "
          "inválido, D6 com índice apagado, D7 — e a sincronia catálogo × constantes)")


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        selftest()
    else:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
