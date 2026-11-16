#!/usr/bin/env python3
"""Uso das skills de um plugin nos transcripts locais do Claude Code (delta-143).

Conta, por skill de `<raiz>/skills/`, as invocações — ferramenta `Skill` com
`<plugin>:<skill>` e `/<plugin>:<skill>` digitado — e as chamadas aos scripts da
skill pelo caminho do plugin instalado (`plugins/cache|marketplaces/.../<plugin>/...`
ou `${CLAUDE_PLUGIN_ROOT}`). É o uso em consumidor: o desenvolvimento no próprio repo
chama `skills/...` relativo e não conta. Skill sem nenhum dos dois na janela é
`dormente` — uso só por script conta, porque `memoria` e `guarding-doc-integrity`
trabalham por hook e gate. A saída nunca carrega `cwd` nem nome de projeto (RNF1):
vai para o corpo de PR, e o `cwd` dos transcripts tem nome de cliente.

    uso_skills.py RAIZ [--desde AAAA-MM-DD] [--projetos DIR]
    uso_skills.py RAIZ --secao-pr --base REF [--desde AAAA-MM-DD] [--projetos DIR]
    uso_skills.py --selftest

Relatório não bloqueia (R3): sai 0 sempre que lê, inclusive sem transcripts; 2 em uso inválido.
"""
import json
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

TAG_ESTRITA = re.compile(r"^v\d+\.\d+\.\d+$")
RELEASES_NA_JANELA = 2  # janela padrão: desde a penúltima tag estrita, duas releases (R2)
FRONTMATTER = re.compile(r"\A---[ \t\r]*\n(.*?)\r?\n---[ \t\r]*$", re.S | re.M)  # LF ou CRLF
PROJETOS_PADRAO = Path(os.environ.get("CLAUDE_CONFIG_DIR", Path.home() / ".claude")) / "projects"


def bloco_frontmatter(texto: str) -> str | None:
    """Bloco entre as linhas que são só `---` — nunca pela substring: a description
    da ticket-to-jira contém `---` e o split cortava o bloco ali (delta-143, R6)."""
    m = FRONTMATTER.match(texto)
    return m.group(1) if m else None


def padroes(plugin: str) -> tuple[re.Pattern, re.Pattern]:
    p = re.escape(plugin)
    script = re.compile(
        r"(?:plugins/(?:cache|marketplaces)/(?:[^\s\"'/]+/)*?" + p + r"(?:/[^\s\"'/]+)*?"
        r"|\$\{?CLAUDE_PLUGIN_ROOT\}?)/skills/([a-z0-9-]+)/scripts/")
    comando = re.compile(r"<command-name>/?" + p + r":([a-z0-9-]+)</command-name>")
    return script, comando


def contar(linhas, plugin: str, skills: list[str], desde: str | None) -> dict:
    """Pura sobre as linhas JSONL: {skill: {invocacoes, scripts, sessoes:set, ultimo}}."""
    uso = {s: {"invocacoes": 0, "scripts": 0, "sessoes": set(), "ultimo": None} for s in skills}
    re_script, re_comando = padroes(plugin)
    vistos = set()

    def registra(skill, campo, chave, ts, sessao):
        if skill not in uso or (chave, skill, campo) in vistos:
            return
        vistos.add((chave, skill, campo))
        u = uso[skill]
        u[campo] += 1
        u["sessoes"].add(sessao)
        u["ultimo"] = max(filter(None, (u["ultimo"], ts[:10])), default=None)

    for linha in linhas:
        if '"Skill"' not in linha and "command-name" not in linha and "/skills/" not in linha:
            continue
        try:
            e = json.loads(linha)
        except json.JSONDecodeError:
            continue
        ts = e.get("timestamp") or ""
        if not ts or (desde and ts[:10] < desde):
            continue
        sessao, conteudo = e.get("sessionId"), (e.get("message") or {}).get("content")
        if e.get("type") == "assistant" and isinstance(conteudo, list):
            for b in conteudo:
                if not isinstance(b, dict) or b.get("type") != "tool_use":
                    continue
                entrada = b.get("input") or {}
                if b.get("name") == "Skill":
                    ns, _, nome = str(entrada.get("skill", "")).partition(":")
                    if ns == plugin:
                        registra(nome, "invocacoes", b.get("id"), ts, sessao)
                elif b.get("name") == "Bash":
                    # ponytail: qualquer Bash que cite o caminho conta — `cat`/`grep` de um arquivo em
                    # scripts/ também vira chamada; casar o interpretador se o falso positivo pesar
                    for nome in set(re_script.findall(str(entrada.get("command", "")))):
                        registra(nome, "scripts", b.get("id"), ts, sessao)
        elif e.get("type") == "user":
            textos = [conteudo] if isinstance(conteudo, str) else [
                b.get("text", "") for b in conteudo or [] if isinstance(b, dict)]
            for nome in {n for t in textos for n in re_comando.findall(t or "")}:
                registra(nome, "invocacoes", e.get("uuid"), ts, sessao)
    return uso


def dormentes(uso: dict) -> list[str]:
    return sorted(s for s, u in uso.items() if u["invocacoes"] == 0 and u["scripts"] == 0)


def dts_que_citam(skill: str, debts: dict[str, str]) -> list[str]:
    """Pura: ids dos DTs ativos cujo texto cita a skill como palavra inteira."""
    citacao = re.compile(r"(?<![\w-])" + re.escape(skill) + r"(?![\w-])")
    return sorted(m.group(1) for nome, texto in debts.items()
                  if citacao.search(texto) and (m := re.search(r"(DT-\d+)", nome)))


def tabela(uso: dict, desde: str | None) -> str:
    linhas = [f"Uso desde {desde or 'o início do histórico'}, nos transcripts locais.\n",
              "| Skill | Invocações | Scripts | Sessões | Último uso | |", "|---|---|---|---|---|---|"]
    ordem = sorted(uso, key=lambda s: (-(uso[s]["invocacoes"] + uso[s]["scripts"]), s))
    for s in ordem:
        u = uso[s]
        marca = "dormente" if u["invocacoes"] == u["scripts"] == 0 else ""
        linhas.append(f"| `{s}` | {u['invocacoes']} | {u['scripts']} | {len(u['sessoes'])} "
                      f"| {u['ultimo'] or '—'} | {marca} |")
    return "\n".join(linhas)


def secao_pr(dorm: list[str], debts: dict[str, str], mudaram: list[str],
             desde: str | None, ultima_tag: str | None) -> str:
    """Seção `## Revisão das skills` do corpo da PR de release; vazia quando nada a dizer (R3)."""
    if not dorm and not mudaram:
        return ""
    partes = ["## Revisão das skills", ""]
    if dorm:
        partes.append(f"**Dormentes desde {desde or 'o início do histórico'}** — nenhuma invocação "
                      "nem chamada de script pelo plugin instalado, nos transcripts de quem cortou:")
        for s in dorm:
            partes.append(f"- `{s}` — {', '.join(dts_que_citam(s, debts)) or 'sem DT'}")
        partes.append("")
    if mudaram:
        partes.append(f"**Frontmatter mudou desde {ultima_tag}** — medir disparo antes do corte "
                      "(suíte `evals/disparo/`, rodada do terminal):")
        partes += [f"- `{s}`" for s in mudaram]
    return "\n".join(partes).rstrip()


def git(raiz: Path, *args: str) -> str | None:
    r = subprocess.run(["git", "-C", str(raiz), *args], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def tags_estritas(raiz: Path) -> list[str]:
    saida = git(raiz, "tag", "--list", "v*", "--sort=-v:refname") or ""
    return [t for t in saida.split() if TAG_ESTRITA.match(t)]


def janela_padrao(raiz: Path) -> str | None:
    tags = tags_estritas(raiz)
    if len(tags) < RELEASES_NA_JANELA:
        return None
    return (git(raiz, "log", "-1", "--format=%cs", tags[RELEASES_NA_JANELA - 1]) or "").strip() or None


def frontmatter_mudou(raiz: Path, skills: list[str], base: str) -> tuple[str | None, list[str]]:
    tags = tags_estritas(raiz)
    if not tags:
        return None, []
    def bloco(ref, s):
        texto = git(raiz, "show", f"{ref}:skills/{s}/SKILL.md")
        return bloco_frontmatter(texto) if texto is not None else None
    return tags[0], [s for s in skills if bloco(tags[0], s) != bloco(base, s)]


def ler_transcripts(projetos: Path):
    for arq in sorted(projetos.rglob("*.jsonl")):
        with arq.open(encoding="utf-8", errors="replace") as f:
            yield from f


def data_iso(texto: str) -> str:
    """Tipo do --desde: data inválida é erro de uso (exit 2), não janela vazia em silêncio."""
    return date.fromisoformat(texto).isoformat()


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return selftest()
    import argparse
    ap = argparse.ArgumentParser(prog="uso_skills.py", description=__doc__.split("\n\n")[0])
    ap.add_argument("raiz", type=Path)
    ap.add_argument("--desde", type=data_iso, help="AAAA-MM-DD; padrão: data da penúltima tag vX.Y.Z")
    ap.add_argument("--projetos", type=Path, default=PROJETOS_PADRAO)
    ap.add_argument("--secao-pr", action="store_true", help="só a seção da PR de release (exige --base)")
    ap.add_argument("--base", help="ref da base do corte, comparada com a última tag")
    try:
        a = ap.parse_args(argv)
        if a.secao_pr and not a.base:
            ap.error("--secao-pr exige --base")
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 2
    try:
        plugin = json.loads((a.raiz / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))["name"]
    except (OSError, ValueError, KeyError):
        print(f"uso_skills: {a.raiz} não é raiz de plugin (sem .claude-plugin/plugin.json com 'name')",
              file=sys.stderr)
        return 2
    skills = sorted(p.name for p in (a.raiz / "skills").iterdir() if (p / "SKILL.md").is_file())
    desde = a.desde or janela_padrao(a.raiz)
    sem_transcripts = not a.projetos.is_dir() or next(a.projetos.rglob("*.jsonl"), None) is None
    if sem_transcripts:
        print(f"aviso: sem transcripts em {a.projetos} — revisão de uso omitida", file=sys.stderr)
    if not a.secao_pr:
        if not sem_transcripts:
            print(tabela(contar(ler_transcripts(a.projetos), plugin, skills, desde), desde))
        return 0
    # a lista de frontmatter alterado só depende do git: não some junto com a de dormentes (R3)
    dorm = [] if sem_transcripts else dormentes(contar(ler_transcripts(a.projetos), plugin, skills, desde))
    debts = {p.name: p.read_text(encoding="utf-8")
             for p in sorted((a.raiz / "debts" / "ativos").glob("DEBT_DT-*.md"))}
    ultima, mudaram = frontmatter_mudou(a.raiz, skills, a.base)
    secao = secao_pr(dorm, debts, mudaram, desde, ultima)
    if secao:
        print(secao)
    return 0


def selftest() -> int:
    import tempfile
    def ev(tipo, ts, sessao="s1", cwd="/casa/cliente-secreto/repo", **kw):
        return json.dumps({"type": tipo, "timestamp": ts, "sessionId": sessao, "cwd": cwd, **kw})
    def tool(nome, id_, **entrada):
        return {"content": [{"type": "tool_use", "name": nome, "id": id_, "input": entrada}]}
    cache = "python3 /h/.claude/plugins/cache/deltaspec/deltaspec/1.63.0/skills/memoria/scripts/memoria.py check ."
    linhas = [
        ev("assistant", "2026-11-01T10:00:00Z", message=tool("Skill", "t1", skill="deltaspec:handoff")),
        ev("assistant", "2026-11-01T10:00:00Z", message=tool("Skill", "t1", skill="deltaspec:handoff")),
        ev("user", "2026-11-02T09:00:00Z", "s2", uuid="u1",
           message={"content": "<command-name>/deltaspec:spec-feature</command-name>"}),
        ev("assistant", "2026-11-03T08:00:00Z", message=tool("Bash", "t2", command=cache)),
        ev("assistant", "2026-11-03T08:00:00Z", message=tool(
            "Bash", "t3", command="python3 skills/memoria/scripts/memoria.py indice .")),
        ev("assistant", "2026-11-03T08:00:00Z", message=tool("Skill", "t4", skill="max:handoff")),
        ev("assistant", "2026-01-01T08:00:00Z", message=tool("Skill", "t5", skill="deltaspec:replan-doc")),
        ev("assistant", "2026-11-04T08:00:00Z", message=tool(
            "Bash", "t6", command="python3 ${CLAUDE_PLUGIN_ROOT}/skills/handoff/scripts/debito.py fila .")),
        "linha que não é json mas cita /skills/",
    ]
    skills = ["busca-falhas", "handoff", "memoria", "replan-doc", "spec-feature"]
    uso = contar(linhas, "deltaspec", skills, "2026-10-01")
    assert uso["handoff"]["invocacoes"] == 1, "mesmo id de tool_use repetido conta uma vez; max:handoff não conta"
    assert uso["handoff"]["scripts"] == 1, "${CLAUDE_PLUGIN_ROOT} literal conta como plugin instalado"
    assert uso["spec-feature"]["invocacoes"] == 1, "slash digitado conta como invocação"
    assert uso["memoria"] == {"invocacoes": 0, "scripts": 1, "sessoes": {"s1"}, "ultimo": "2026-11-03"}, \
        "script pelo cache conta; skills/... relativo (desenvolvimento) não"
    assert dormentes(uso) == ["busca-falhas", "replan-doc"], "fora da janela não conta; uso só por script não é dormente"
    assert contar(linhas, "deltaspec", skills, None)["replan-doc"]["invocacoes"] == 1, "sem janela conta tudo"

    debts = {"DEBT_DT-007-x.md": "rota para a busca-falhas", "DEBT_DT-009-y.md": "fala da replan-docs"}
    assert dts_que_citam("busca-falhas", debts) == ["DT-007"]
    assert dts_que_citam("replan-doc", debts) == [], "replan-docs não é citação de replan-doc"
    secao = secao_pr(dormentes(uso), debts, ["handoff"], "2026-10-01", "v1.2.0")
    assert "- `busca-falhas` — DT-007" in secao and "- `replan-doc` — sem DT" in secao, secao
    assert "desde v1.2.0" in secao and "- `handoff`" in secao, secao
    assert secao_pr([], debts, [], "2026-10-01", "v1.2.0") == "", "nada a dizer: a seção some"
    for texto in (secao, tabela(uso, "2026-10-01")):
        assert "cliente-secreto" not in texto and "/casa/" not in texto, "RNF1: nada de cwd na saída"

    assert bloco_frontmatter("---\nname: a\ndescription: x --- y\ndisable-model-invocation: true\n---\n# a\n") \
        == "name: a\ndescription: x --- y\ndisable-model-invocation: true", "--- na description não corta o bloco"
    assert bloco_frontmatter("# sem frontmatter\n") is None
    assert bloco_frontmatter("---\r\nname: a\r\ndescription: b\r\n---\r\n# a\r\n") \
        == "name: a\r\ndescription: b", "frontmatter com CRLF é lido"

    with tempfile.TemporaryDirectory() as d:
        raiz = Path(d)
        env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
               "GIT_COMMITTER_EMAIL": "t@t", "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
        def run(*a, data=None):
            subprocess.run(["git", "-C", d, *a], check=True, capture_output=True,
                           env={**env, **({"GIT_COMMITTER_DATE": data, "GIT_AUTHOR_DATE": data} if data else {})})
        def skill(nome, desc):
            (raiz / "skills" / nome).mkdir(parents=True, exist_ok=True)
            (raiz / "skills" / nome / "SKILL.md").write_text(f"---\nname: {nome}\ndescription: {desc}\n---\n# {nome}\n")
        run("init", "-q")
        (raiz / ".claude-plugin").mkdir()
        (raiz / ".claude-plugin" / "plugin.json").write_text('{"name": "deltaspec"}')
        skill("a", "um"); skill("c", "três")
        for versao, data in (("v1.0.0", "2026-09-01T12:00:00"), ("v1.1.0", "2026-10-01T12:00:00"),
                             ("v1.2.0", "2026-11-01T12:00:00")):
            (raiz / "marca").write_text(versao)
            run("add", "-A"); run("commit", "-qm", versao, data=data); run("tag", versao)
            if versao == "v1.0.0":
                assert janela_padrao(raiz) is None, "uma tag só: sem janela padrão, sem IndexError"
        run("tag", "1.5.0")
        assert tags_estritas(raiz) == ["v1.2.0", "v1.1.0", "v1.0.0"], "1.5.0 fora do formato é ignorada"
        assert janela_padrao(raiz) == "2026-10-01", "penúltima tag estrita: duas releases"
        skill("a", "um, reescrita"); skill("b", "nova")
        run("add", "-A"); run("commit", "-qm", "muda")
        assert frontmatter_mudou(raiz, ["a", "b", "c"], "HEAD") == ("v1.2.0", ["a", "b"])

        import contextlib
        import io
        with contextlib.redirect_stderr(io.StringIO()) as erro:
            assert main([d, "--projetos", str(raiz / "sem-transcripts")]) == 0, "sem transcripts: sai 0"
            assert "aviso: sem transcripts" in erro.getvalue(), "e avisa em 1 linha (RNF2 do framework)"
            assert main([]) == 2 and main([d, "--secao-pr"]) == 2, "uso inválido sai 2"
            assert main([d, "--desde", "2026-13-01"]) == 2, "--desde que não é data sai 2"
        vazio = raiz / "vazio"
        vazio.mkdir()
        with contextlib.redirect_stderr(io.StringIO()) as erro:
            assert main([d, "--projetos", str(vazio)]) == 0, "projetos existente sem .jsonl: sai 0"
            assert "aviso: sem transcripts" in erro.getvalue(), "e avisa, em vez de marcar tudo dormente"
            with contextlib.redirect_stdout(io.StringIO()) as saida:
                assert main([d, "--secao-pr", "--base", "HEAD", "--projetos", str(vazio)]) == 0
            assert "**Frontmatter mudou desde v1.2.0**" in saida.getvalue() and "- `a`" in saida.getvalue() \
                and "Dormentes" not in saida.getvalue(), "sem transcripts a lista de frontmatter sai (R3)"
    with tempfile.TemporaryDirectory() as d:
        subprocess.run(["git", "-C", d, "init", "-q"], check=True, capture_output=True)
        assert janela_padrao(Path(d)) is None, "repo sem tag: sem janela padrão"
        assert frontmatter_mudou(Path(d), ["a"], "HEAD") == (None, []), "repo sem tag: nada a comparar"
    print("uso_skills selftest: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
