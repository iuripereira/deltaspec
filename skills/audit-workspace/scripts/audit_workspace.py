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

Bloco G — higiene de git (skill git-guard, delta-076). Catálogo canônico dos anti-padrões,
com dano, frequência, camada de trava e o que fica sem trava:
skills/git-guard/references/anti-padroes.md
  G1  segredo versionado (ou .env fora do git em repo sem .gitignore)     CRÍTICO
  G2  gate local desligado — core.hooksPath ausente, quebrado ou inerte   ALTO
  G3  camada de agente ausente — nada intercepta comando git do harness   ALTO
  G4  repositório que publica, sem CI versionado                          ALTO
  G5  commit acima do limiar canônico de tamanho (ignorando merges)       MÉDIO
  G6  aderência a Conventional Commits abaixo do piso do perfil           MÉDIO
  G7  arquivo rastreado acima do limite de tamanho                        MÉDIO

O nível de exigência vem do PERFIL do repositório (skills/git-guard/references/perfis.md),
derivado de sinais do próprio repo: em perfil `rascunho` só o G1 é cobrado, o resto é
informativo — repo sem servidor não pode ser cobrado por regra de servidor.

Uso: audit_workspace.py [DIR] [--profundidade N] [--excluir PADRAO]... [--apenas-git]
  --profundidade N  desce até N níveis procurando repos (default 1). O default preserva o
                    alcance histórico byte a byte; a varredura profunda é DECISÃO explícita,
                    nunca default, porque a skill promete não varrer o filesystem sozinha.
  --excluir PADRAO  trecho de caminho a podar (repetível). Somam-se às podas embutidas.
  --apenas-git      roda só o bloco G. É o modo da varredura profunda: os W varrem cada
                    repo com rglob e o custo não paga em dezenas de repositórios.
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

# Mesma justificativa do import acima: o layout skills/<nome>/scripts/ é estável no repo e
# no cache do plugin. O dono dos padrões de segredo é a git-guard, dona do catálogo — o G1
# importa a função em vez de reimplementar o casamento (regra de ouro: uma fonte por regra).
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "git-guard" / "scripts"))
from segredos import arquivo_ignorado, casar  # noqa: E402

CODE_SPAN_PATH = re.compile(r"`([\w./-]+\.(?:py|sh))`")
ABS_PATH_LITERAL = re.compile(r"""(['"])(/[^'"\n]+)\1""")
SKILL_CMD = re.compile(r"/([a-z][a-z0-9_-]*):([a-z][a-z0-9_-]*)")
DIARY_NAMES = ("HANDOFF.md", "STATE.md", ".claude/HANDOFF.md")
DIARY_DIR = ".claude/handoffs"  # handoffs por sessão (delta-037) — diretório, não arquivo

# ------------------------------------------------------------------- bloco G: limiares ---
# TETO_COMMIT é ESPELHO do limiar canônico de tamanho de PR (dono:
# skills/projeto-init/references/canonical-rules.md, âncora pr-limiar-tamanho no deps.toml).
# Não é número novo: a leitura é "um commit que sozinho estoura o teto do PR é mudança não
# relacionada empacotada junto". Mudou lá, muda aqui — o C1 do validate_integrity vigia.
TETO_COMMIT = 500
TETO_ARQUIVO_BYTES = 1_000_000
AMOSTRA_COMMITS = 20
# Piso de aderência a Conventional Commits por perfil. Este script é o DONO do valor;
# perfis.md governa só a ordem (cliente ≥ rigido > padrao > rascunho) e aponta para cá.
PISO_CC = {"cliente": 0.9, "rigido": 0.9, "padrao": 0.6, "rascunho": None}
RE_CONVENTIONAL = re.compile(
    r"^(feat|fix|docs|refactor|chore|ci|test|style|perf|build|revert)(\([^)]+\))?!?: .+"
)
# Poda embutida da varredura profunda: diretório de dependência/build, nunca código do dono,
# mais o cache de plugins do harness, que é código de terceiro por construção.
PODAS_EMBUTIDAS = (
    "node_modules", "__pycache__", ".venv", "venv", "vendor", ".tox", ".next", "dist",
    ".claude/plugins",
)
# Segmento de caminho que marca repositório aposentado: entra no relatório, nunca é cobrado
# (vira perfil rascunho). Comparado por SUFIXO DE SEGMENTO, não por substring solta — assim
# um segmento como "NN-arquivo" ou "NN-quarentena" casa, e "meus-arquivos" (plural) não —
# sem que o script publicado carregue o nome de pasta de ninguém.
SUFIXOS_DE_SEGMENTO_APOSENTADO = (
    "arquivo", "arquivo-morto", "quarentena", "archive", "deprecated", "obsoleto",
)
# Teto de leitura por arquivo no G1. Acima disto é dado, não configuração — e ler 33 repos
# inteiros sem teto é o que faria a varredura profunda deixar de ser hábito (RNF10).
TETO_LEITURA_BYTES = 512_000


def _podado(caminho: Path, extras: tuple[str, ...] = ()) -> bool:
    """Puro: caminho cai numa poda embutida ou declarada pelo chamador."""
    texto = str(caminho).replace("\\", "/")
    return any(f"/{p}" in f"/{texto}" for p in (*PODAS_EMBUTIDAS, *extras))


def find_repo_roots(base: Path, profundidade: int = 1, excluir: tuple[str, ...] = ()) -> list[Path]:
    """Repos git sob `base`, descendo até `profundidade` níveis.

    profundidade=1 é exatamente `base.glob("*/.git")` — o alcance histórico, preservado
    byte a byte para que os W1-W10 não mudem de comportamento (R56: a skill nunca varre o
    filesystem silenciosamente; descer é decisão explícita de quem chama).
    Encontrado um repo, não desce dentro dele: worktree e submódulo não viram repo-membro.
    """
    achados: list[Path] = []

    def desce(atual: Path, nivel: int) -> None:
        if nivel > profundidade:
            return
        try:
            subpastas = sorted(p for p in atual.iterdir() if p.is_dir() and not p.is_symlink())
        except OSError:
            return
        for sub in subpastas:
            if sub.name == ".git" or _podado(sub, excluir):
                continue
            if (sub / ".git").exists():
                achados.append(sub)
                continue
            desce(sub, nivel + 1)

    desce(base, 1)
    return sorted(achados)


def detect_mode(target: Path, profundidade: int = 1, excluir: tuple[str, ...] = ()) -> str | None:
    if (target / ".git").exists():
        return "repo"
    if len(find_repo_roots(target, profundidade, excluir)) >= 2:
        return "workspace"
    return None


# ------------------------------------------------------------------- bloco G: perfil -----

def _git(repo: Path, *args: str) -> str:
    """Saída de um comando git só-leitura; string vazia se o comando falhar."""
    proc = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True
    )
    return proc.stdout.strip() if proc.returncode == 0 else ""


def _doc_profile(repo: Path) -> dict:
    """doc-profile.yaml do repo, ou {}. PyYAML ausente → {} com aviso (RNF2: degrada)."""
    arquivo = repo / "doc-profile.yaml"
    if not arquivo.is_file():
        return {}
    try:
        import yaml  # dependência única admitida (ADR-0023)
    except ImportError:
        print("[G] doc-profile.yaml não lido — PyYAML ausente; perfil cai na detecção por "
              "sinais de git (pip install pyyaml para honrar override)", file=sys.stderr)
        return {}
    try:
        return yaml.safe_load(arquivo.read_text(encoding="utf-8")) or {}
    except (yaml.YAMLError, OSError):
        return {}


def derivar_perfil(repo: Path) -> tuple[str, str]:
    """Puro-o-bastante (só lê): devolve (perfil, origem). Regras: git-guard/references/perfis.md."""
    perfil_doc = _doc_profile(repo)
    declarado = (perfil_doc.get("git") or {}).get("perfil")
    if declarado in PISO_CC:
        return declarado, "override"

    if (perfil_doc.get("publico") or {}).get("cliente") is True:
        return "cliente", "detectado"
    if any(parte.lower().endswith(SUFIXOS_DE_SEGMENTO_APOSENTADO) for parte in repo.parts):
        return "rascunho", "detectado"

    tem_remoto = bool(_git(repo, "remote"))
    if not tem_remoto:
        return "rascunho", "detectado"
    # `rigido` = publica release (tag + remoto). CI DELIBERADAMENTE fora do sinal: se ter
    # workflow fosse condição para ser `rigido`, o G4 ("publica sem CI") nunca dispararia
    # em `rigido` e nasceria morto — e o caso real que ele existe para pegar é justamente
    # o repositório com dezenas de tags e nenhum CI.
    if _git(repo, "tag"):
        return "rigido", "detectado"
    return "padrao", "detectado"


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


# ------------------------------------------------------ checks G — higiene de git --------
# Cada check devolve [(repo, linha)]; quem decide se a linha é cobrança ou informação é
# `classificar()`, com a tabela COBRANCA — a política mora num lugar só, não em 7 checks.

# ESPELHO da tabela de perfis.md. A duplicação é deliberada (doutrina legível lá, política
# executável aqui) e vigiada: o selftest parseia perfis.md e exige que as duas coincidam.
COBRANCA = {
    "cliente":  {"G1", "G2", "G3", "G4", "G5", "G6", "G7"},
    "rigido":   {"G1", "G2", "G3", "G4", "G5", "G6", "G7"},
    "padrao":   {"G1", "G2", "G3", "G5", "G6", "G7"},
    "rascunho": {"G1"},
}


def _rotulo(repo: Path, root: Path) -> str:
    try:
        relativo = str(repo.relative_to(root))
    except ValueError:
        return repo.name
    # repo == root devolve "." — inútil como rótulo de relatório; o nome diz mais.
    return repo.name if relativo in (".", "") else relativo


def check_g1_segredo(repos: list[Path], root: Path) -> list[tuple[Path, str]]:
    achados = []
    for repo in repos:
        rastreados = _git(repo, "ls-files").splitlines()
        for rel in rastreados:
            if arquivo_ignorado(Path(rel).name):
                continue
            alvo = repo / rel
            try:
                if alvo.stat().st_size > TETO_LEITURA_BYTES:
                    continue
                texto = alvo.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            for nome, linha in casar(texto):
                # o trecho casado NUNCA entra na mensagem — só arquivo, padrão e linha
                achados.append((repo, f"[G1] segredo versionado ({nome}) — "
                                      f"{_rotulo(repo, root)}/{rel}:{linha}"))
        if (repo / ".env").is_file() and ".env" not in rastreados and not (repo / ".gitignore").is_file():
            achados.append((repo, f"[G1] .env fora do git em repo sem .gitignore — "
                                  f"{_rotulo(repo, root)} (um `git add -A` versiona o segredo)"))
    return achados


def check_g2_gate_local(repos: list[Path], root: Path) -> list[tuple[Path, str]]:
    achados = []
    for repo in repos:
        rotulo = _rotulo(repo, root)
        configurado = _git(repo, "config", "--get", "core.hooksPath")
        if not configurado:
            extra = (" — .githooks/ existe e está versionado, mas nada o liga ao git"
                     if (repo / ".githooks").is_dir() else "")
            achados.append((repo, f"[G2] core.hooksPath não configurado{extra} — {rotulo}"))
            continue
        # relativo resolve contra o topo da árvore de trabalho, que é onde o git roda o hook
        alvo = Path(configurado) if Path(configurado).is_absolute() else repo / configurado
        if not alvo.is_dir():
            achados.append((repo, f"[G2] core.hooksPath aponta para diretório inexistente "
                                  f"('{configurado}') — {rotulo}: nenhum hook roda, e sem erro"))
            continue
        executaveis = [
            p for p in alvo.iterdir()
            if p.is_file() and not p.name.endswith(".sample") and os.access(p, os.X_OK)
        ]
        if not executaveis:
            achados.append((repo, f"[G2] core.hooksPath existe mas não tem hook executável "
                                  f"('{configurado}') — {rotulo}"))
    return achados


def _alcanca_bash(settings: dict) -> bool:
    """True se algum hook do settings.json intercepta ferramenta Bash, ou se há deny de git."""
    for eventos in (settings.get("hooks") or {}).values():
        for entrada in eventos or []:
            matcher = entrada.get("matcher", "")
            try:
                if matcher and re.search(matcher, "Bash"):
                    return True
            except re.error:
                continue
    negados = ((settings.get("permissions") or {}).get("deny")) or []
    return any("git" in str(regra) for regra in negados)


def check_g3_camada_agente(repos: list[Path], root: Path) -> list[tuple[Path, str]]:
    achados = []
    for repo in repos:
        arquivo = repo / ".claude" / "settings.json"
        rotulo = _rotulo(repo, root)
        motivo = None
        if not arquivo.is_file():
            motivo = "sem .claude/settings.json versionado"
        else:
            try:
                if not _alcanca_bash(json.loads(arquivo.read_text(encoding="utf-8"))):
                    motivo = "settings.json não intercepta Bash nem nega comando git"
            except (json.JSONDecodeError, OSError):
                motivo = ".claude/settings.json ilegível"
        if motivo:
            achados.append((repo, f"[G3] camada de agente ausente ({motivo}) — {rotulo}: "
                                  f"--no-verify, force-push e descarte de árvore suja ficam sem trava"))
    return achados


def check_g4_publica_sem_ci(repos: list[Path], root: Path) -> list[tuple[Path, str]]:
    achados = []
    for repo in repos:
        fluxos = repo / ".github" / "workflows"
        if fluxos.is_dir() and any(fluxos.glob("*.y*ml")):
            continue
        tags = _git(repo, "tag").splitlines()
        achados.append((repo, f"[G4] publica release sem CI versionado — {_rotulo(repo, root)} "
                              f"({len(tags)} tag(s), nenhum workflow): não há check para o "
                              f"ruleset exigir antes do merge"))
    return achados


def check_g5_commit_gigante(repos: list[Path], root: Path) -> list[tuple[Path, str]]:
    achados = []
    for repo in repos:
        saida = _git(repo, "log", f"-{AMOSTRA_COMMITS}", "--no-merges", "--shortstat",
                     "--format=%h")
        # --no-merges é o recorte que evita o falso positivo: um merge commit soma o diff
        # inteiro do ramo e infla a medição sem que ninguém tenha escrito nada grande.
        grandes, atual = [], None
        for linha in saida.splitlines():
            texto = linha.strip()
            if not texto:
                continue
            if not texto.startswith(("1 file", "2 file")) and " file" not in texto:
                atual = texto
                continue
            total = sum(int(n) for n in re.findall(r"(\d+) (?:insertion|deletion)", texto))
            if total > TETO_COMMIT and atual:
                grandes.append((atual, total))
        if grandes:
            pior = max(grandes, key=lambda g: g[1])
            achados.append((repo, f"[G5] {len(grandes)} de {AMOSTRA_COMMITS} commits acima do "
                                  f"limiar canônico ({TETO_COMMIT} linhas) — "
                                  f"{_rotulo(repo, root)}, pior: {pior[0]} com {pior[1]}"))
    return achados


def check_g6_mensagem_generica(repos: list[Path], root: Path,
                               perfis: dict[Path, tuple[str, str]]) -> list[tuple[Path, str]]:
    achados = []
    for repo in repos:
        piso = PISO_CC.get(perfis[repo][0])
        if piso is None:
            continue
        assuntos = _git(repo, "log", f"-{AMOSTRA_COMMITS}", "--no-merges", "--format=%s").splitlines()
        if not assuntos:
            continue
        taxa = sum(1 for a in assuntos if RE_CONVENTIONAL.match(a)) / len(assuntos)
        if taxa < piso:
            achados.append((repo, f"[G6] aderência a Conventional Commits em {taxa:.0%}, "
                                  f"piso do perfil {perfis[repo][0]} é {piso:.0%} — "
                                  f"{_rotulo(repo, root)}"))
    return achados


def check_g7_arquivo_grande(repos: list[Path], root: Path) -> list[tuple[Path, str]]:
    achados = []
    for repo in repos:
        grandes = []
        for rel in _git(repo, "ls-files").splitlines():
            try:
                tamanho = (repo / rel).stat().st_size
            except OSError:
                continue
            if tamanho > TETO_ARQUIVO_BYTES:
                grandes.append((rel, tamanho))
        if grandes:
            pior = max(grandes, key=lambda g: g[1])
            achados.append((repo, f"[G7] {len(grandes)} arquivo(s) rastreado(s) acima de "
                                  f"{TETO_ARQUIVO_BYTES // 1000} kB — {_rotulo(repo, root)}, "
                                  f"maior: {pior[0]} ({pior[1] // 1000} kB)"))
    return achados


def classificar(achados: list[tuple[Path, str]],
                perfis: dict[Path, tuple[str, str]]) -> tuple[list[str], list[str]]:
    """Separa cobrança de informação pelo perfil do repo de origem. Política num lugar só."""
    cobrados, informativos = [], []
    for repo, linha in achados:
        check = linha[1:linha.index("]")]
        perfil = perfis.get(repo, ("padrao", "detectado"))[0]
        if check in COBRANCA.get(perfil, set()):
            cobrados.append(linha)
        else:
            informativos.append(f"{linha}  (informativo: perfil {perfil})")
    return cobrados, informativos


def rodar_bloco_g(repos: list[Path], root: Path) -> tuple[list[str], list[str], int]:
    """Ordem de invocação = ordem de severidade = ordem do relatório (R108).

    Devolve (linhas_cobradas, linhas_informativas, n_achados). O terceiro valor existe
    porque as linhas cobradas incluem cabeçalho de agrupamento — contar linhas anunciaria
    mais achados do que existem.
    """
    perfis = {repo: derivar_perfil(repo) for repo in repos}
    cobrados: list[str] = []
    informativos: list[str] = []
    n_achados = 0
    for nome, achados in (
        ("G1", check_g1_segredo(repos, root)),
        ("G2", check_g2_gate_local(repos, root)),
        ("G3", check_g3_camada_agente(repos, root)),
        ("G4", check_g4_publica_sem_ci(repos, root)),
        ("G5", check_g5_commit_gigante(repos, root)),
        ("G6", check_g6_mensagem_generica(repos, root, perfis)),
        ("G7", check_g7_arquivo_grande(repos, root)),
    ):
        c, i = classificar(achados, perfis)
        if c:
            # cabeçalho por achado: o relatório agrupa por anti-padrão, não por repo, porque
            # a decisão que o leitor toma é sobre o anti-padrão (R108)
            repos_afetados = len({r for r, linha in achados if linha in c})
            cobrados.append(f"[{nome}] {repos_afetados} repositório(s) afetado(s):")
            cobrados.extend(f"  {linha}" for linha in c)
            n_achados += len(c)
        informativos.extend(f"  {linha}" for linha in i)
    return cobrados, informativos, n_achados


# --------------------------------------------------------------------------- main --------

def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(add_help=True, description=__doc__)
    parser.add_argument("alvo", nargs="?", default=".")
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--profundidade", type=int, default=1)
    parser.add_argument("--excluir", action="append", default=[])
    parser.add_argument("--apenas-git", action="store_true", dest="apenas_git")
    args = parser.parse_args()

    if args.selftest:
        selftest()
        return

    excluir = tuple(args.excluir)
    target = Path(args.alvo).resolve()
    mode = detect_mode(target, args.profundidade, excluir)
    if mode is None:
        print(
            f"ERRO: {target} não é um repositório git nem um workspace reconhecível "
            "(pasta sem .git com 2+ subpastas imediatas contendo .git)"
            + ("" if args.profundidade > 1 else
               " — se os repositórios estão mais fundo, use --profundidade N"),
            file=sys.stderr,
        )
        sys.exit(2)

    violations: list[str] = []
    info: list[str] = []
    repos = [target] if mode == "repo" else find_repo_roots(target, args.profundidade, excluir)

    # Os dois blocos são DISJUNTOS por desenho, não por economia: a audit-workspace audita
    # consistência de referência entre repos, a git-guard audita higiene de git. Misturar as
    # saídas apagaria a fronteira que as duas SKILL.md declaram.
    n_achados = 0
    if args.apenas_git:
        cobrados_g, info_g, n_achados = rodar_bloco_g(repos, target)
        violations += cobrados_g
        info += info_g
    else:
        if mode == "repo":
            violations += check_w3_deps_toml_gap(repos)
            violations += check_w5_stale_absolute_paths(repos, target)
            violations += check_w6_stale_skill_refs(repos, target)
            violations += check_w9_gate_without_hook(repos, target)
            violations += check_w10_orphan_framework_copy(repos, target)
        else:
            violations += check_w1_cross_repo_links(target, repos)
            violations += check_w2_remote_name_drift(repos)
            violations += check_w3_deps_toml_gap(repos)
            violations += check_w5_stale_absolute_paths(repos, target)
            violations += check_w6_stale_skill_refs(repos, target)
            violations += check_w8_editor_config_drift(target, repos)
            violations += check_w9_gate_without_hook(repos, target)
            violations += check_w10_orphan_framework_copy(repos, target)
            info += check_w7_diary_map(repos)

    print(f"audit-workspace: modo {mode} — {target}"
          + (" — bloco git (git-guard)" if args.apenas_git else ""))
    if args.profundidade > 1:
        # corte silencioso de cobertura lê-se como cobertura completa: sempre declarar
        podas = ", ".join((*PODAS_EMBUTIDAS, *excluir))
        print(f"varredura: {len(repos)} repositório(s), profundidade {args.profundidade}; "
              f"podado por: {podas}")
    # Cobrança primeiro, informação depois: numa varredura de dezenas de repositórios o
    # informativo é volumoso e afogaria o acionável se viesse antes.
    if violations:
        print("\n".join(violations))
    if info:
        print(f"\n— informativo ({len(info)} linha(s), não derruba o resultado) —")
        print("\n".join(info))
    if violations:
        total = n_achados if args.apenas_git else len(violations)
        alcance = f" em {len(repos)} repositório(s)" if len(repos) > 1 else ""
        print(f"\nRESULTADO: FAIL ({total} achado(s){alcance})")
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

    def _commit(repo: Path, msg: str, arquivo: str, conteudo: str) -> None:
        (repo / arquivo).parent.mkdir(parents=True, exist_ok=True)
        (repo / arquivo).write_text(conteudo, encoding="utf-8")
        subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True,
                       capture_output=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", msg], check=True,
                       capture_output=True)

    def _identidade(repo: Path) -> None:
        subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@example.com"], check=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], check=True)

    # ------------------------------------------------------------------ bloco G ----------

    # G-perfil — derivação e precedência do override
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        sem_remoto = root / "rascunho"
        _git_init(sem_remoto)
        assert derivar_perfil(sem_remoto) == ("rascunho", "detectado"), derivar_perfil(sem_remoto)

        com_remoto = root / "padrao"
        _git_init(com_remoto, remote="git@github.com:example/padrao.git")
        _identidade(com_remoto)
        _commit(com_remoto, "feat: x", "a.txt", "x\n")
        assert derivar_perfil(com_remoto)[0] == "padrao", derivar_perfil(com_remoto)

        subprocess.run(["git", "-C", str(com_remoto), "tag", "v1.0.0"], check=True)
        assert derivar_perfil(com_remoto)[0] == "rigido", \
            "tag + remoto = publica release; CI fora do sinal, senão o G4 nasce morto"

        # override no doc-profile.yaml vence a detecção, e a origem é declarada
        _write(root, {"padrao/doc-profile.yaml": "git:\n  perfil: rascunho\n"})
        try:
            import yaml  # noqa: F401
            assert derivar_perfil(com_remoto) == ("rascunho", "override"), derivar_perfil(com_remoto)
            _write(root, {"padrao/doc-profile.yaml": "publico:\n  cliente: true\n"})
            assert derivar_perfil(com_remoto)[0] == "cliente", derivar_perfil(com_remoto)
        except ImportError:
            print("[selftest] PyYAML ausente — casos de override não verificados", file=sys.stderr)

        # caminho marcado como morto rebaixa para rascunho mesmo com remoto
        morto = root / "07-quarentena" / "antigo"  # sintético: testa o prefixo numerado
        _git_init(morto, remote="git@github.com:example/antigo.git")
        assert derivar_perfil(morto)[0] == "rascunho", derivar_perfil(morto)

    # G1 — segredo versionado, e o contrato de nunca imprimir o valor casado
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        repo = root / "repo-a"
        _git_init(repo, remote="git@github.com:example/repo-a.git")
        _identidade(repo)
        # montada em runtime: literal no fonte faria o G1 acusar o próprio selftest
        segredo = "AK" + "IA" + "7QW3ZKJ9PLMN2XVD"
        _commit(repo, "feat: x", "conf.env", f"AWS_KEY={segredo}\n")
        _commit(repo, "feat: y", "conf.env.example", f"AWS_KEY={segredo}\n")
        achados = check_g1_segredo([repo], root)
        assert len(achados) == 1, achados
        assert "conf.env:1" in achados[0][1], achados
        assert segredo not in achados[0][1], "o trecho casado NUNCA pode sair no relatório"
        assert ".example" not in achados[0][1], "arquivo de exemplo não é achado"

    # G2 — core.hooksPath resolvido contra o disco, não apenas lido da config
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        repo = root / "repo-a"
        _git_init(repo)
        assert "não configurado" in check_g2_gate_local([repo], root)[0][1]

        subprocess.run(["git", "-C", str(repo), "config", "core.hooksPath",
                        str(root / "sumiu")], check=True)
        achado = check_g2_gate_local([repo], root)
        assert achado and "inexistente" in achado[0][1], \
            "config apontando para diretório que não existe: ler a config diria que há hook"

        ganchos = repo / ".githooks"
        ganchos.mkdir()
        (ganchos / "pre-commit").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(repo), "config", "core.hooksPath", ".githooks"], check=True)
        assert "não tem hook executável" in check_g2_gate_local([repo], root)[0][1], \
            "diretório certo mas hook sem bit de execução: o git ignora em silêncio"

        (ganchos / "pre-commit").chmod(0o755)
        assert check_g2_gate_local([repo], root) == [], "hooksPath relativo, existente e executável"

    # G5 — merge commit não conta: sem --no-merges um merge infla a medição sozinho
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        repo = root / "repo-a"
        _git_init(repo)
        _identidade(repo)
        _commit(repo, "feat: base", "a.txt", "linha\n")
        subprocess.run(["git", "-C", str(repo), "checkout", "-q", "-b", "ramo"], check=True)
        _commit(repo, "feat: grande", "b.txt", "".join(f"linha {i}\n" for i in range(TETO_COMMIT + 50)))
        subprocess.run(["git", "-C", str(repo), "checkout", "-q", "-"], check=True)
        subprocess.run(["git", "-C", str(repo), "merge", "-q", "--no-ff", "ramo", "-m",
                        "chore: merge"], check=True, capture_output=True)
        linhas = [l for _, l in check_g5_commit_gigante([repo], root)]
        assert linhas and "1 de" in linhas[0], \
            f"deve acusar 1 commit grande, nunca 2 — o merge repete o mesmo diff: {linhas}"

    # Sincronia COBRANCA × perfis.md — a duplicação é deliberada, então é vigiada.
    doutrina = Path(__file__).resolve().parents[2] / "git-guard" / "references" / "perfis.md"
    if doutrina.is_file():
        da_doutrina: dict[str, set[str]] = {}
        for linha in doutrina.read_text(encoding="utf-8").splitlines():
            celulas = [c.strip().strip("`") for c in linha.strip().strip("|").split("|")]
            if len(celulas) == 8 and celulas[0] in COBRANCA:
                da_doutrina[celulas[0]] = {
                    f"G{i}" for i, c in enumerate(celulas[1:], 1) if c == "cobra"
                }
        assert da_doutrina == COBRANCA, (
            f"perfis.md e COBRANCA divergiram — doutrina={da_doutrina} código={COBRANCA}"
        )

    print("selftest: OK (9 fixtures W + 5 fixtures G — W1-W3 e W5-W10, derivação de perfil "
          "com override, G1 sem vazar valor, G2 resolvendo o caminho, G5 ignorando merge, "
          "e a sincronia entre perfis.md e COBRANCA; W4 removido, ver plan.md)")


if __name__ == "__main__":
    main()
