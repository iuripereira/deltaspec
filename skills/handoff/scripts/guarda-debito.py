#!/usr/bin/env python3
"""Hook PreToolUse (delta-142): PR para a main com DT prometido para a versão não sai.

Terceira camada do gate de release — as outras são o step do `release-check` e o passo do
`criar-release`. Esta é a única que alcança `gh pr create --base main` e `gh pr merge`
digitados à mão, antes da rede. Devolve `deny`, não `ask` como o guarda-git: a promessa
`!release(V)` está no registro, e confirmar não a cumpre — quitar, adiar ou descartar cumpre.
Outro comando, gate verde, ou gate que não roda (sem debito.py, exit 2): silêncio (RNF2) —
o CI é a rede.

Molde do guarda-git: este repositório o invoca daqui (dogfood, .claude/settings.json); o
`git-guard instalar` copia para `.claude/hooks/` do consumidor, e a cópia acha o debito.py
pelo `git config deltaspec.plugin-root` que o mesmo instalar grava.
"""

import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

# ESPELHO de guarda-git.segmentar (skills/git-guard/scripts/guarda-git.py): mudou um, mude o outro.
RE_SEPARADOR = re.compile(r"\s*(?:&&|\|\||;|\|)\s*")
RE_BRANCH_RELEASE = re.compile(r"^(?:release|hotfix)/(\d+\.\d+\.\d+)$")
DEBITO_REL = "skills/handoff/scripts/debito.py"
# Opções do `gh pr merge` que levam valor — o primeiro posicional que sobra é a PR alvo.
MERGE_COM_VALOR = {"-b", "--body", "-F", "--body-file", "-t", "--subject", "-A", "--author-email",
                   "--match-head-commit", "-R", "--repo"}


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


def _opcao(tokens: list, longa: str, curta: str):
    """Valor de `--longa X`, `--longa=X` ou `-c X`; None se ausente."""
    for i, t in enumerate(tokens):
        if t in (longa, curta) and i + 1 < len(tokens):
            return tokens[i + 1]
        if t.startswith(longa + "="):
            return t.split("=", 1)[1]
    return None


def alvo_gate(tokens: list):
    """('create', base, head) · ('merge', None, None) · None — o `gh pr` que o gate alcança."""
    if len(tokens) < 3 or tokens[0].rsplit("/", 1)[-1] != "gh" or tokens[1] != "pr":
        return None
    if tokens[2] == "merge":
        return "merge", None, _alvo_merge(tokens[3:])
    if tokens[2] == "create":
        return "create", _opcao(tokens, "--base", "-B"), _opcao(tokens, "--head", "-H")
    return None


def _alvo_merge(args: list):
    """A PR que o `gh pr merge` recebe (número, URL ou branch), ou None = a da branch atual."""
    i = 0
    while i < len(args):
        if args[i] in MERGE_COM_VALOR:
            i += 2
            continue
        if not args[i].startswith("-"):
            return args[i]
        i += 1
    return None


def versao_da_branch(nome: str):
    m = RE_BRANCH_RELEASE.match(nome or "")
    return m.group(1) if m else None


def decidir(comando: str, branch_atual: str, rodar_gate):
    """Decisão pura: `rodar_gate(versao) -> (exit, stdout)` é injetado — o selftest não roda git."""
    for tokens in segmentar(comando or ""):
        achado = alvo_gate(tokens)
        if not achado:
            continue
        acao, base, head = achado
        # sem --base o gh abre contra a branch default — a main, que o fluxo nomeia literalmente
        if acao == "create" and base not in (None, "main"):
            continue
        if acao == "merge" and head not in (None, branch_atual):
            # `gh pr merge 777` estando numa release/*: é OUTRA PR, e deny não tem como confirmar.
            # ponytail: número/URL da própria PR exigiria rede para casar; o release-check cobre
            continue
        versao = versao_da_branch(head or branch_atual)
        if not versao:
            continue  # ponytail: merge fora da branch de release exigiria rede; o release-check cobre
        codigo, saida = rodar_gate(versao)
        if codigo == 1:
            conselho = (" — quite o DT, adie o !release(V) ou descarte antes de abrir/mergear a PR para a main"
                        if "[bloqueia]" in saida else "")  # registro inválido: a saída do gate já diz o que fazer
            return {"hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f"[gate release {versao}] {saida.strip()}{conselho}",
            }}
    return None


def debito_py():
    """O debito.py vizinho (dogfood) ou o do plugin pelo `git config deltaspec.plugin-root`."""
    local = Path(__file__).resolve().with_name("debito.py")
    if local.is_file():
        return local
    raiz = subprocess.run(["git", "config", "deltaspec.plugin-root"],
                          capture_output=True, text=True).stdout.strip()
    candidato = Path(raiz) / DEBITO_REL if raiz else None
    return candidato if candidato and candidato.is_file() else None


def gate_real(cwd: Path):
    def rodar(versao):
        script = debito_py()
        if not script:
            return 0, ""
        raiz = subprocess.run(["git", "-C", str(cwd), "rev-parse", "--show-toplevel"],
                              capture_output=True, text=True).stdout.strip() or str(cwd)
        r = subprocess.run([sys.executable, str(script), "gate", raiz, "--release", versao],
                           capture_output=True, text=True)
        return r.returncode, r.stdout
    return rodar


def selftest() -> int:
    vermelho = lambda v: (1, f"[bloqueia] DT-230: !release({v}) — promessa aberta")
    verde = lambda v: (0, f"gate release {v}: OK")

    def deny(cmd, branch="release/1.64.0", gate=vermelho):
        v = decidir(cmd, branch, gate)
        assert v is not None, f"deveria negar: {cmd}"
        assert v["hookSpecificOutput"]["permissionDecision"] == "deny", cmd
        return v["hookSpecificOutput"]["permissionDecisionReason"]

    def livre(cmd, branch="release/1.64.0", gate=vermelho):
        assert decidir(cmd, branch, gate) is None, f"deveria ficar em silêncio: {cmd}"

    assert "1.64.0" in deny("gh pr create --base main --title 'chore(release): 1.64.0' --body-file corpo.md")
    assert "DT-230" in deny("gh pr create -B main -t x")
    assert "1.65.0" in deny("gh pr create --base=main --head release/1.65.0", branch="feat/x")  # --head manda
    assert "1.64.1" in deny("gh pr merge --merge", branch="hotfix/1.64.1")
    deny("gh pr merge release/1.64.0 --merge")                 # o argumento é a própria branch
    deny("gh pr create --title 'chore(release): 1.64.0'")      # sem --base o gh usa a default, que é a main
    livre("gh pr merge 777 --squash")                          # número de OUTRA PR: não é esta release
    livre("gh pr merge outra/branch")
    invalido = lambda v: (1, f"> gate release {v}: registro inválido — o gate não lê promessas")
    motivo = deny("gh pr create --base main", gate=invalido)
    assert "registro inválido" in motivo and "adie o !release" not in motivo, motivo
    deny("cd /repo && gh pr create --base main")
    deny("/usr/bin/gh pr create --base main")
    livre("gh pr create --base develop --title x")       # PR de escopo: o gate é da main
    livre("gh pr create --base main", gate=verde)        # gate verde: silêncio
    livre("gh pr create --base main", branch="feat/x")   # sem versão na branch nem no --head: release-check cobre
    livre("gh pr merge 600", branch="develop")           # ponytail: merge fora da branch de release exigiria rede
    livre("gh pr create --base main", gate=lambda v: (2, ""))  # exit 2 = erro de uso, não bloqueio
    livre("gh pr view 600")
    livre("git push -u origin release/1.64.0")
    livre("echo 'gh pr merge' > notas.txt")
    livre("")
    print("guarda-debito selftest: OK (create --base main · merge · --head · composições · silêncio · nunca ask)")
    return 0


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    try:
        entrada = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # input inesperado: silêncio, nunca bloqueia a sessão
    comando = (entrada.get("tool_input") or {}).get("command", "")
    if not isinstance(comando, str) or "gh" not in comando:
        return 0  # o caminho comum sai antes de qualquer subprocesso
    cwd = Path(entrada.get("cwd") or os.getcwd())
    branch = subprocess.run(["git", "-C", str(cwd), "branch", "--show-current"],
                            capture_output=True, text=True).stdout.strip()
    veredito = decidir(comando, branch, gate_real(cwd))
    if veredito:
        print(json.dumps(veredito, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
