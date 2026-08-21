#!/usr/bin/env python3
"""Audita consistência de um repositório único ou de um workspace multi-repo (pasta sem
.git com repos git como subpastas) — skill audit-workspace, delta-036.

Modo automático (R1): "repo" (.git no alvo) ou "workspace" (alvo sem .git, com 2+
subpastas imediatas contendo .git). Sem flag manual.

Checks:
  W1  link relativo cruza a raiz do .git de origem e não resolve no destino (workspace)
  W2  remote 'origin' de um repo-membro termina num nome diferente da pasta local (workspace)
  W3  CLAUDE.md do repo cita deps.toml, mas o arquivo não existe na raiz
  W4  (removido — ver specs/036-audit-workspace/plan.md: colisão de DT-NNN entre ledgers
      independentes é o estado normal, não um achado; cada repo numera a partir de 1)
  W5  path absoluto hardcoded (prefixo do próprio alvo/workspace) inexistente no disco,
      citado como literal de string num .py/.sh
  W6  comando /plugin:skill cujo namespace não está no registro local de plugins instalados
  W7  mapa de diário de bordo (HANDOFF.md/STATE.md) por repo-membro — informativo (workspace)
  W8  *.code-workspace com pastas divergentes dos repos git presentes (workspace)
  W9  script citado (code-span) num CLAUDE.md sem hook de pré-commit nem workflow de CI
      que o invoque
  W10 arquivo local cujo basename bate com um script de $CLAUDE_PLUGIN_ROOT e o conteúdo diverge
      (repo cujo .claude-plugin/plugin.json tem o mesmo name do plugin em $CLAUDE_PLUGIN_ROOT
      é a fonte publicada dele — auto-auditoria, W10 pula esse repo; delta-072)

W6 e W10 dependem de artefatos do harness Claude Code (registro local de plugins,
$CLAUDE_PLUGIN_ROOT); ausentes → o check se omite com 1 linha de aviso em stderr, nunca falha.

Uso: audit_workspace.py [DIR]   (default: .)
Exit 0 = sem achado; 1 = achado(s); 2 = alvo não é repo nem workspace reconhecível.
Requer Python 3.11+ (mesma linha de base do restante do plugin).
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

# Import do módulo da skill irmã guarding-doc-integrity — mesmo padrão de
# skills/spec-feature/scripts/tickets.py → skills/handoff/scripts/projecao.py: o layout
# skills/<nome>/scripts/ é estável tanto no repo quanto no cache do plugin instalado, por
# isso o caminho é relativo ao próprio arquivo, nunca absoluto de máquina. Import direto
# em vez de subprocess+parse de texto formatado (achado do review, delta-036).
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "guarding-doc-integrity" / "scripts"))
from validate_integrity import collect, scan_links_c3, EXCLUDE_LINKS_PADRAO  # noqa: E402

CODE_SPAN_PATH = re.compile(r"`([\w./-]+\.(?:py|sh))`")
ABS_PATH_LITERAL = re.compile(r"""(['"])(/[^'"\n]+)\1""")
SKILL_CMD = re.compile(r"/([a-z][a-z0-9_-]*):([a-z][a-z0-9_-]*)")
DIARY_NAMES = ("HANDOFF.md", "STATE.md", ".claude/HANDOFF.md")
DIARY_DIR = ".claude/handoffs"  # handoffs por sessão (delta-037) — diretório, não arquivo


def find_repo_roots(base: Path) -> list[Path]:
    return sorted(p.parent for p in base.glob("*/.git"))


def detect_mode(target: Path) -> str | None:
    if (target / ".git").exists():
        return "repo"
    if len(find_repo_roots(target)) >= 2:
        return "workspace"
    return None


def _git_tracked_text(repo: Path, sub: str) -> str:
    """Concatena o conteúdo dos arquivos RASTREADOS pelo git sob repo/sub — só isso conta
    como "versionado" (W9); glob pegaria arquivo local não commitado, dando falso PASS."""
    proc = subprocess.run(["git", "-C", str(repo), "ls-files", sub], capture_output=True, text=True)
    if proc.returncode != 0:
        return ""
    text = ""
    for rel in proc.stdout.splitlines():
        p = repo / rel
        try:
            text += p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
    return text


def _plugin_name(path: Path) -> str | None:
    manifest = path / ".claude-plugin" / "plugin.json"
    if not manifest.is_file():
        return None
    try:
        return json.loads(manifest.read_text(encoding="utf-8")).get("name")
    except (json.JSONDecodeError, OSError):
        return None


def installed_plugin_namespaces() -> set[str] | None:
    registro = Path.home() / ".claude" / "plugins" / "installed_plugins.json"
    if not registro.is_file():
        return None
    try:
        data = json.loads(registro.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    # schema real: {"version": N, "plugins": {"nome@marketplace": {...}, ...}}
    return {key.split("@", 1)[0] for key in data.get("plugins", {})}


# ---------------------------------------------------------------- checks (workspace) ----

def check_w1_cross_repo_links(workspace_root: Path, repo_roots: list[Path]) -> list[str]:
    varrido = collect(workspace_root, ["**/*.md"])
    scan_links = varrido - collect(workspace_root, EXCLUDE_LINKS_PADRAO)
    _checked, dead = scan_links_c3(workspace_root, scan_links)
    violations = []
    for path, lineno, target in dead:
        src_repo = next((r for r in repo_roots if path.is_relative_to(r)), None)
        if src_repo is None:
            continue  # arquivo solto na raiz do workspace, não pertence a nenhum repo-membro
        dest = Path(os.path.normpath(str(path.parent / target.split("#")[0])))
        if dest.is_relative_to(src_repo):
            continue  # link morto, mas não cruza fronteira — fora do escopo de W1
        relpath = path.relative_to(workspace_root)
        violations.append(f"[W1] link cruza fronteira de repo e está morto — {relpath}:{lineno} → {target}")
    return violations


def check_w2_remote_name_drift(repo_roots: list[Path]) -> list[str]:
    violations = []
    for repo in repo_roots:
        proc = subprocess.run(
            ["git", "-C", str(repo), "remote", "get-url", "origin"],
            capture_output=True, text=True,
        )
        if proc.returncode != 0:
            continue  # sem remote configurado — nada para comparar
        url = proc.stdout.strip()
        remote_name = re.sub(r"\.git$", "", url.rstrip("/").rsplit("/", 1)[-1])
        if remote_name and remote_name != repo.name:
            violations.append(
                f"[W2] remote 'origin' termina em '{remote_name}', pasta local é '{repo.name}'"
            )
    return violations


def check_w7_diary_map(repo_roots: list[Path]) -> list[str]:
    lines = ["[W7] diário de bordo por repo (informativo):"]
    for repo in repo_roots:
        found = [n for n in DIARY_NAMES if (repo / n).is_file()]
        if (repo / DIARY_DIR).is_dir():
            found.append(DIARY_DIR + "/")
        lines.append(f"  {repo.name}: {', '.join(found) if found else '(nenhum)'}")
    return lines


def check_w8_editor_config_drift(workspace_root: Path, repo_roots: list[Path]) -> list[str]:
    violations = []
    present = {r.resolve() for r in repo_roots}
    for cw in workspace_root.glob("*.code-workspace"):
        try:
            data = json.loads(cw.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        declared = {
            (workspace_root / f.get("path", ".")).resolve() for f in data.get("folders", [])
        }
        declared.discard(workspace_root)  # "." é autorreferência ao próprio workspace — padrão comum, não é repo
        for missing in sorted(present - declared):
            violations.append(f"[W8] repo git presente mas ausente de {cw.name} — {missing.name}")
        for extra in sorted(declared - present):
            violations.append(f"[W8] {cw.name} lista pasta sem repo git correspondente — {extra.name}")
    return violations


# --------------------------------------------------------- checks (repo ou workspace) ----

def check_w3_deps_toml_gap(repos: list[Path]) -> list[str]:
    violations = []
    for repo in repos:
        claude_md = repo / "CLAUDE.md"
        if not claude_md.is_file():
            continue
        if "deps.toml" in claude_md.read_text(encoding="utf-8") and not (repo / "deps.toml").is_file():
            violations.append(f"[W3] CLAUDE.md cita deps.toml mas o arquivo não existe — {repo.name}/CLAUDE.md")
    return violations


def check_w5_stale_absolute_paths(repos: list[Path], prefix_root: Path) -> list[str]:
    prefix = str(prefix_root)
    violations = []
    for repo in repos:
        for path in list(repo.rglob("*.py")) + list(repo.rglob("*.sh")):
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            for i, line in enumerate(text.splitlines(), 1):
                for _quote, literal in ABS_PATH_LITERAL.findall(line):
                    if literal != prefix and not literal.startswith(prefix + "/"):
                        continue
                    if not Path(literal).exists():
                        violations.append(
                            f"[W5] path absoluto hardcoded, inexistente no disco — "
                            f"{path.relative_to(prefix_root)}:{i} → {literal}"
                        )
    return violations


def check_w6_stale_skill_refs(repos: list[Path], root: Path) -> list[str]:
    namespaces = installed_plugin_namespaces()
    if namespaces is None:
        print("[W6] NÃO RODOU — registro local de plugins ausente ou inválido "
              "(~/.claude/plugins/installed_plugins.json); pulando", file=sys.stderr)
        return []
    violations = []
    for repo in repos:
        for path in repo.rglob("CLAUDE.md"):
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            for m in SKILL_CMD.finditer(text):
                ns, skill = m.group(1), m.group(2)
                if ns not in namespaces:
                    violations.append(
                        f"[W6] comando /{ns}:{skill} — plugin '{ns}' não está instalado — "
                        f"{path.relative_to(root)}"
                    )
    return violations


def check_w9_gate_without_hook(repos: list[Path], root: Path) -> list[str]:
    violations = []
    for repo in repos:
        cited: set[str] = set()
        for claude_md in repo.rglob("CLAUDE.md"):
            try:
                cited |= set(CODE_SPAN_PATH.findall(claude_md.read_text(encoding="utf-8")))
            except (UnicodeDecodeError, OSError):
                continue
        if not cited:
            continue
        # ".git/hooks/pre-commit" nunca é versionado (não é clonado, não vai pra outra
        # máquina) — não conta como evidência de "hook versionado" (R3). A evidência tem
        # de vir de arquivo rastreado pelo git: .githooks/, scripts/ ou .github/workflows/.
        hook_text = (
            _git_tracked_text(repo, ".githooks")
            + _git_tracked_text(repo, "scripts")
            + _git_tracked_text(repo, ".github/workflows")
        )
        for script_path in sorted(cited):
            if Path(script_path).name not in hook_text:
                violations.append(
                    f"[W9] gate citado sem hook/CI versionado que o chame — {repo.name}/CLAUDE.md → {script_path}"
                )
    return violations


def check_w10_orphan_framework_copy(repos: list[Path], root: Path) -> list[str]:
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if not plugin_root:
        print("[W10] NÃO RODOU — $CLAUDE_PLUGIN_ROOT ausente (fora do harness Claude Code); "
              "pulando", file=sys.stderr)
        return []
    plugin_scripts = list(Path(plugin_root).glob("skills/*/scripts/*.py"))
    if not plugin_scripts:
        return []
    by_name: dict[str, Path] = {}
    by_content: dict[str, Path] = {}
    for p in plugin_scripts:
        by_name[p.name] = p
        try:
            by_content[p.read_text(encoding="utf-8")] = p
        except (UnicodeDecodeError, OSError):
            continue
    plugin_root_resolved = str(Path(plugin_root).resolve())
    plugin_name = _plugin_name(Path(plugin_root))
    violations = []
    for repo in repos:
        # repo é a fonte publicada deste mesmo plugin (nome do manifesto bate, não o
        # remote git — remote pode divergir do nome do plugin, ex.: deltaspec-lab
        # publica o plugin "deltaspec"; delta-072) — comparar contra o próprio cache
        # instalado não é cópia órfã, é auto-auditoria.
        if plugin_name is not None and _plugin_name(repo) == plugin_name:
            continue
        for path in repo.rglob("*.py"):
            if str(path.resolve()).startswith(plugin_root_resolved):
                continue
            try:
                local_text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            # nome OU conteúdo bate com um script já publicado no framework (R3)
            upstream = by_name.get(path.name) or by_content.get(local_text)
            if upstream is None:
                continue
            estado = "é idêntica ao" if local_text == upstream.read_text(encoding="utf-8") else "diverge do"
            violations.append(
                f"[W10] cópia local {estado} script upstream do framework — "
                f"{path.relative_to(root)} (compare com {upstream})"
            )
    return violations


# --------------------------------------------------------------------------- main --------

def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        selftest()
        return

    target = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    mode = detect_mode(target)
    if mode is None:
        print(
            f"ERRO: {target} não é um repositório git nem um workspace reconhecível "
            "(pasta sem .git com 2+ subpastas imediatas contendo .git)",
            file=sys.stderr,
        )
        sys.exit(2)

    violations: list[str] = []
    info: list[str] = []

    if mode == "repo":
        repos = [target]
        violations += check_w3_deps_toml_gap(repos)
        violations += check_w5_stale_absolute_paths(repos, target)
        violations += check_w6_stale_skill_refs(repos, target)
        violations += check_w9_gate_without_hook(repos, target)
        violations += check_w10_orphan_framework_copy(repos, target)
    else:
        repo_roots = find_repo_roots(target)
        violations += check_w1_cross_repo_links(target, repo_roots)
        violations += check_w2_remote_name_drift(repo_roots)
        violations += check_w3_deps_toml_gap(repo_roots)
        violations += check_w5_stale_absolute_paths(repo_roots, target)
        violations += check_w6_stale_skill_refs(repo_roots, target)
        violations += check_w8_editor_config_drift(target, repo_roots)
        violations += check_w9_gate_without_hook(repo_roots, target)
        violations += check_w10_orphan_framework_copy(repo_roots, target)
        info += check_w7_diary_map(repo_roots)

    print(f"audit-workspace: modo {mode} — {target}")
    for line in info:
        print(line)
    if violations:
        print("\n".join(violations))
        print(f"RESULTADO: FAIL ({len(violations)} achado(s))")
        sys.exit(1)
    print("RESULTADO: PASS")


# ------------------------------------------------------------------------ selftest -------

def selftest() -> None:
    """1 fixture por check no mínimo, nomes sintéticos — nenhum dado de cliente real."""
    import tempfile

    def _write(root: Path, tree: dict) -> None:
        for name, content in tree.items():
            p = root / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")

    def _git_init(repo: Path, remote: str | None = None) -> None:
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        if remote:
            subprocess.run(["git", "-C", str(repo), "remote", "add", "origin", remote], check=True)

    def _run(args: list, env: dict | None = None) -> subprocess.CompletedProcess:
        full_env = os.environ.copy()
        full_env.pop("CLAUDE_PLUGIN_ROOT", None)
        if env:
            full_env.update(env)
        return subprocess.run(
            [sys.executable, __file__, *args], capture_output=True, text=True, env=full_env
        )

    # R1 — detecção de modo (CT1-CT3)
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _git_init(root / "repo-a")
        r = _run([str(root / "repo-a")])
        assert "modo repo" in r.stdout, r.stdout
        assert not any(f"[W{n}]" in r.stdout for n in (1, 2, 8)), \
            f"checks cross-repo não devem rodar em modo repo:\n{r.stdout}"

        r0 = _run([str(root)])
        assert r0.returncode == 2 and "não é um repositório" in r0.stderr, r0.stderr

        _git_init(root / "repo-b")
        r2 = _run([str(root)])
        assert "modo workspace" in r2.stdout, r2.stdout

    # W1 — link cruzando fronteira de repo (CT4-CT5)
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _git_init(root / "repo-a")
        _git_init(root / "repo-b")
        _write(root, {"repo-a/nota.md": "Ver [x](../repo-b/sumiu.md).\n"})
        r = _run([str(root)])
        assert r.returncode == 1 and "[W1]" in r.stdout, r.stdout

        _write(root, {"repo-b/sumiu.md": "existe\n"})
        r2 = _run([str(root)])
        assert "[W1]" not in r2.stdout, r2.stdout  # CT19: mesma fixture cobre a chamada a --links-only

    # W2 — remote diverge do nome local (CT6-CT7)
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _git_init(root / "repo-a", remote="git@github.com:example/old-name.git")
        _git_init(root / "repo-b")
        r = _run([str(root)])
        w2_lines = [l for l in r.stdout.splitlines() if "[W2]" in l]
        assert any("old-name" in l for l in w2_lines), r.stdout
        assert not any("repo-b" in l for l in w2_lines), r.stdout  # sem remote — nada a comparar

    # W5 — path absoluto hardcoded inexistente (CT8-CT9)
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _git_init(root / "repo-a")
        _git_init(root / "repo-b")
        sumiu = str(root / "repo-a" / "old-dir" / "x.md")
        _write(root, {"repo-a/scripts/gate.py": f'ALVO = "{sumiu}"\n'})
        r = _run([str(root)])
        assert "[W5]" in r.stdout, r.stdout

        existe = str(root / "repo-a" / "existe.md")
        _write(root, {"repo-a/existe.md": "ok\n", "repo-a/scripts/gate2.py": f'ALVO = "{existe}"\n'})
        r2 = _run([str(root)])
        assert not any("gate2.py" in l for l in r2.stdout.splitlines() if "[W5]" in l), r2.stdout

    # W6 — comando de skill sem plugin instalado (CT10)
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        repo = root / "repo-a"
        _git_init(repo)
        _write(root, {"repo-a/CLAUDE.md": "Use `/plugin-real:algo` e `/plugin-fake:outro`.\n"})
        fake_home = root / "fakehome"
        (fake_home / ".claude" / "plugins").mkdir(parents=True)
        (fake_home / ".claude" / "plugins" / "installed_plugins.json").write_text(
            json.dumps({"version": 1, "plugins": {"plugin-real@marketplace-x": {}}}),
            encoding="utf-8",
        )
        r = _run([str(repo)], env={"HOME": str(fake_home)})
        w6_lines = [l for l in r.stdout.splitlines() if "[W6]" in l]
        assert any("plugin-fake" in l for l in w6_lines), r.stdout
        assert not any("plugin-real" in l for l in w6_lines), r.stdout

        r2 = _run([str(repo)], env={"HOME": str(root / "sem-home")})
        assert "[W6] NÃO RODOU" in r2.stderr, r2.stderr

    # W9 — gate citado sem hook/CI VERSIONADO (CT11-CT12)
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        repo = root / "repo-a"
        _git_init(repo)
        _write(root, {"repo-a/CLAUDE.md": "Gate: `scripts/gate.py`.\n", "repo-a/scripts/gate.py": "pass\n"})
        r = _run([str(repo)])
        assert "[W9]" in r.stdout, r.stdout

        # hook em .git/hooks/ não é versionado — sozinho não deve limpar o achado
        (repo / ".git" / "hooks").mkdir(parents=True, exist_ok=True)
        (repo / ".git" / "hooks" / "pre-commit").write_text(
            "#!/bin/sh\npython3 scripts/gate.py\n", encoding="utf-8"
        )
        r_unversioned = _run([str(repo)])
        assert "[W9]" in r_unversioned.stdout, \
            f"hook não-versionado não pode satisfazer W9:\n{r_unversioned.stdout}"

        # só some quando a evidência é RASTREADA pelo git (.githooks/, scripts/, workflows/)
        subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@example.com"], check=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], check=True)
        _write(root, {"repo-a/.githooks/pre-commit": "#!/bin/sh\npython3 scripts/gate.py\n"})
        subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "x"], check=True)
        r2 = _run([str(repo)])
        assert "[W9]" not in r2.stdout, r2.stdout

    # W10 — cópia órfã de script do framework (CT13)
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        repo = root / "repo-a"
        _git_init(repo)
        plugin_root = root / "fake-plugin"
        _write(root, {
            "fake-plugin/skills/x/scripts/util.py": "def f():\n    return 1\n",
            "repo-a/scripts/util.py": "def f():\n    return 2\n",  # mesmo nome, diverge
            "repo-a/scripts/copia_identica.py": "def f():\n    return 1\n",  # nome diferente, conteúdo igual
        })
        r = _run([str(repo)], env={"CLAUDE_PLUGIN_ROOT": str(plugin_root)})
        w10_lines = [l for l in r.stdout.splitlines() if "[W10]" in l]
        assert any("diverge" in l and "util.py" in l for l in w10_lines), r.stdout
        assert any("idêntica" in l and "copia_identica.py" in l for l in w10_lines), \
            f"nome diferente mas conteúdo igual ao upstream também é achado (R3: nome OU conteúdo):\n{r.stdout}"

        r2 = _run([str(repo)])
        assert "[W10] NÃO RODOU" in r2.stderr, r2.stderr

        # auto-auditoria: repo é a fonte publicada do plugin em $CLAUDE_PLUGIN_ROOT — nome
        # do manifesto bate, W10 pula o repo mesmo com script idêntico (delta-072)
        _write(root, {
            "fake-plugin/.claude-plugin/plugin.json": json.dumps({"name": "meu-plugin"}),
            "repo-a/.claude-plugin/plugin.json": json.dumps({"name": "meu-plugin"}),
        })
        r3 = _run([str(repo)], env={"CLAUDE_PLUGIN_ROOT": str(plugin_root)})
        assert "[W10]" not in r3.stdout, \
            f"repo com plugin.json igual ao de $CLAUDE_PLUGIN_ROOT é auto-auditoria, não achado:\n{r3.stdout}"

        # nome de plugin diferente não é auto-auditoria — achado continua valendo (regressão)
        _write(root, {"repo-a/.claude-plugin/plugin.json": json.dumps({"name": "outro-plugin"})})
        r4 = _run([str(repo)], env={"CLAUDE_PLUGIN_ROOT": str(plugin_root)})
        assert "[W10]" in r4.stdout, \
            f"nome de plugin diferente não deve ser tratado como auto-auditoria:\n{r4.stdout}"

    # W3 — deps.toml citado mas ausente (CT14)
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _git_init(root / "repo-a")
        _git_init(root / "repo-b")
        _write(root, {"repo-a/CLAUDE.md": "Governado pelo manifesto deps.toml.\n"})
        r = _run([str(root)])
        assert any("repo-a" in l for l in r.stdout.splitlines() if "[W3]" in l), r.stdout

    # W4 removido (ver plan.md) — CT15 descontinuado, nada a testar aqui

    # W7 — mapa de diário de bordo, informativo (CT16)
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _git_init(root / "repo-a")
        _git_init(root / "repo-b")
        _write(root, {"repo-a/HANDOFF.md": "x\n", "repo-b/STATE.md": "x\n",
                      "repo-a/.claude/handoffs/HANDOFF_x_2026_08_09.md": "x\n"})
        r = _run([str(root)])
        assert r.returncode == 0, r.stdout
        assert "[W7]" in r.stdout and "HANDOFF.md" in r.stdout and "STATE.md" in r.stdout, r.stdout
        assert ".claude/handoffs/" in r.stdout, r.stdout  # diretório de handoffs por sessão (delta-037)

    # W8 — *.code-workspace divergente (CT17)
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _git_init(root / "repo-a")
        _git_init(root / "repo-b")
        _write(root, {"ws.code-workspace": json.dumps({"folders": [{"path": "."}, {"path": "repo-a"}]})})
        r = _run([str(root)])
        assert any("repo-b" in l for l in r.stdout.splitlines() if "[W8]" in l), r.stdout
        assert not any(l.endswith(root.name) for l in r.stdout.splitlines() if "[W8]" in l), \
            f"autorreferência '.' ao workspace não é achado:\n{r.stdout}"

    print("selftest: OK (9 fixtures, W1-W3 e W5-W10 detectados — W4 removido, ver plan.md; "
          "CT18/CT19 cobertos por validate_integrity.py::selftest e pela fixture de W1)")


if __name__ == "__main__":
    main()
