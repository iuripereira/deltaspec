#!/usr/bin/env python3
"""Hook PreToolUse (delta-090): comando git destrutivo ou de bypass pede confirmação.

Camada de agente do catálogo da git-guard (anti-padroes.md): é a única que
alcança G11 (--no-verify), G12 (force-push), G13 (descarte de árvore suja),
G14 (remoção forçada) e G16 (git add -A) — nem hook de git nem ruleset do
servidor chegam neles a tempo. Devolve `ask`, nunca `deny` (doutrina do R124):
o comando legítimo confirma e segue. Demais comandos: silêncio.

Um só dono: este repositório o invoca daqui (dogfood, sem cópia); o modo
`instalar` da git-guard copia para `.claude/hooks/` do consumidor e registra o
matcher `Bash` no `.claude/settings.json`.
"""

import json
import re
import shlex
import sys

# Operadores que separam comandos numa linha de shell. Cada segmento é avaliado
# sozinho: `cd x && git push -f` esconde o git atrás do cd, e a regra de negação
# por padrão de comando não o vê (catálogo, G12).
RE_SEPARADOR = re.compile(r"\s*(?:&&|\|\||;|\|)\s*")
# Tokens que podem preceder o `git` sem serem o comando: wrappers e atribuições.
PREFIXOS = {"env", "command", "sudo", "nice", "time", "exec"}
RE_ATRIBUICAO = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
# Opções globais do git que aceitam valor (`git -C /repo push`): pular as duas.
GLOBAIS_COM_VALOR = {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}


def segmentar(comando: str) -> list:
    """Segmentos de shell de um comando composto, já tokenizados."""
    segmentos = []
    for trecho in RE_SEPARADOR.split(comando):
        if not trecho.strip():
            continue
        try:
            tokens = shlex.split(trecho, posix=True)
        except ValueError:
            tokens = trecho.split()  # aspas desbalanceadas: melhor ver algo que nada
        if tokens:
            segmentos.append(tokens)
    return segmentos


def _subcomando(tokens: list):
    """(subcomando, argumentos) do primeiro `git` do segmento, ou None."""
    i = 0
    while i < len(tokens) and (tokens[i] in PREFIXOS or RE_ATRIBUICAO.match(tokens[i])):
        i += 1
    if i >= len(tokens) or tokens[i].rsplit("/", 1)[-1] != "git":
        return None
    args = tokens[i + 1:]
    while args and args[0].startswith("-"):
        args = args[2:] if args[0] in GLOBAIS_COM_VALOR else args[1:]
    if not args:
        return None
    return args[0], args[1:]


def _flag_curta(args: list, letra: str) -> bool:
    """`-f`, ou a letra dentro de um grupo curto (`-fu`); nunca dentro de `--long`."""
    return any(a.startswith("-") and not a.startswith("--") and letra in a[1:] for a in args)


def _regra(sub: str, args: list):
    """(G, razão) do primeiro anti-padrão que o subcomando casa, ou None."""
    if sub in ("commit", "push") and (
        "--no-verify" in args or (sub == "commit" and _flag_curta(args, "n"))
    ):
        return "G11", "bypass do hook (--no-verify) — o CI replica o mesmo check, então o desvio só adia a reprova"
    if sub == "push":
        if (
            any(a in ("--force", "--force-with-lease", "--force-if-includes") or a.startswith("--force-with-lease=") for a in args)
            or _flag_curta(args, "f")
            or any(a.startswith("+") and len(a) > 1 for a in args)
        ):
            return "G12", "force-push — reescreve histórico que outra sessão ou o servidor já têm"
        if "--delete" in args or _flag_curta(args, "d") or any(a.startswith(":") and len(a) > 1 for a in args):
            return "G14", "remoção de branch remota — já custou um PR dependente fechado por engano neste projeto"
    if sub == "reset" and "--hard" in args:
        return "G13", "descarte de árvore suja (reset --hard) — não há reflog para mudança não commitada"
    if sub == "checkout" and ("--" in args or "." in args):
        return "G13", "descarte de mudanças por checkout de caminho — não há reflog para mudança não commitada"
    if sub == "restore" and ("." in args or "--worktree" in args or _flag_curta(args, "W")):
        return "G13", "descarte de mudanças na árvore (restore) — não há reflog para mudança não commitada"
    if sub == "clean" and ("--force" in args or _flag_curta(args, "f") or _flag_curta(args, "x")):
        return "G13", "remoção de arquivos não rastreados (clean) — irrecuperável"
    if sub == "stash" and args[:1] and args[0] in ("drop", "clear"):
        return "G13", "descarte de stash — irrecuperável"
    if sub == "branch" and ("-D" in args or (("--delete" in args or _flag_curta(args, "d")) and ("--force" in args or _flag_curta(args, "f")))):
        return "G14", "remoção forçada de branch não integrada"
    if sub == "worktree" and args[:1] == ["remove"] and ("--force" in args or _flag_curta(args, "f")):
        return "G14", "remoção forçada de worktree com mudanças"
    if sub == "add" and any(a in ("-A", "--all", ".") for a in args):
        return "G16", "add indiscriminado — foi o que levou o auto-fix do IDE para a main (#309); prefira add nomeado"
    return None


def decidir(comando: str):
    """Decisão pura: comando com anti-padrão de git → dict de `ask`; senão None."""
    for tokens in segmentar(comando or ""):
        achado = _subcomando(tokens)
        if not achado:
            continue
        veredito = _regra(*achado)
        if veredito:
            g, razao = veredito
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "ask",
                    "permissionDecisionReason": f"[{g}] {razao} — confirme se é intencional",
                }
            }
    return None


def selftest() -> int:
    def ask(cmd):
        v = decidir(cmd)
        assert v is not None, f"deveria pedir ask: {cmd}"
        assert v["hookSpecificOutput"]["permissionDecision"] == "ask", cmd
        return v["hookSpecificOutput"]["permissionDecisionReason"]

    def livre(cmd):
        assert decidir(cmd) is None, f"deveria ficar em silêncio: {cmd}"

    # G11 — bypass do hook
    assert "G11" in ask("git commit --no-verify -m 'x'")
    assert "G11" in ask("git commit -n -m x")
    assert "G11" in ask("git push --no-verify")
    livre("git push -n origin main")            # -n no push é --dry-run, não bypass
    livre("git commit -m 'sem --no-verify no texto'")
    # G12 — force-push, em todas as grafias que a regra de negação deixa passar
    assert "G12" in ask("git push --force origin main")
    assert "G12" in ask("git push -f")
    assert "G12" in ask("git push origin main -f")
    assert "G12" in ask("git push --force-with-lease origin main")
    assert "G12" in ask("git push origin +main")
    assert "G12" in ask("git -C /repo push -fu origin main")
    livre("git push origin main")
    livre("git push -u origin feat/x")
    # G13 — descarte de árvore suja
    assert "G13" in ask("git reset --hard HEAD~1")
    assert "G13" in ask("git checkout -- .")
    assert "G13" in ask("git checkout .")
    assert "G13" in ask("git restore .")
    assert "G13" in ask("git restore --worktree src/")
    assert "G13" in ask("git clean -fd")
    assert "G13" in ask("git clean -x -f")
    assert "G13" in ask("git stash drop")
    assert "G13" in ask("git stash clear")
    livre("git reset --soft HEAD~1")
    livre("git checkout -b feat/x")
    livre("git restore --staged a.py")
    livre("git clean -n")
    livre("git stash")
    livre("git stash pop")
    # G14 — remoção forçada
    assert "G14" in ask("git branch -D feat/x")
    assert "G14" in ask("git branch --delete --force feat/x")
    assert "G14" in ask("git worktree remove --force ../wt")
    assert "G14" in ask("git push origin --delete feat/x")
    assert "G14" in ask("git push origin :feat/x")
    livre("git branch -d feat/x")
    livre("git worktree remove ../wt")
    livre("git branch --list")
    # G16 — add indiscriminado
    assert "G16" in ask("git add -A")
    assert "G16" in ask("git add --all")
    assert "git add ." and "G16" in ask("git add .")
    livre("git add -p")
    livre("git add CHANGELOG.md HANDOFF.md")
    # composição, prefixo e caminho: cada segmento é avaliado
    assert "G12" in ask("cd /repo && git push -f")
    assert "G13" in ask("git fetch; git reset --hard origin/main")
    assert "G11" in ask("env GIT_EDITOR=true git commit -n -m x")
    assert "G16" in ask("command git add -A && git commit -m x")
    assert "G12" in ask("/usr/bin/git push --force")
    assert "G13" in ask("git status | cat && git clean -f")
    livre("git log --oneline -5 | cat")
    livre("ls -la && python3 x.py")
    livre("echo 'git push --force' > notas.txt")   # string, não comando git
    livre("")
    # nunca deny, e a razão nomeia o que confirmar
    for cmd in ("git push -f", "git reset --hard", "git add -A"):
        v = decidir(cmd)["hookSpecificOutput"]
        assert v["permissionDecision"] == "ask" and "confirme" in v["permissionDecisionReason"], cmd
    print("guarda-git selftest: OK (G11 · G12 · G13 · G14 · G16 · composições · silêncio · nunca deny)")
    return 0


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    try:
        entrada = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # input inesperado: silêncio, nunca bloqueia a sessão
    comando = (entrada.get("tool_input") or {}).get("command", "")
    veredito = decidir(comando) if isinstance(comando, str) else None
    if veredito:
        print(json.dumps(veredito, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
