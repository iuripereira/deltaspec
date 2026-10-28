#!/usr/bin/env python3
"""Memória de projeto versionada (delta-132, ADR-0050): fatos em .claude/memory/, índice e projeção.

Uso:
  memoria.py check [ROOT]             gate: frontmatter, teto do índice, segredo — sai 1 com achado
  memoria.py indice [ROOT] [--check]  regenera MEMORY.md (fatos) e HANDOFF.md (Agora + git); --check só compara MEMORY.md
  memoria.py injetar [ROOT]           imprime o índice no stdout (hook SessionStart, rota fallback)
  memoria.py aprovar NAME [ROOT]      move inbox/NAME.md para .claude/memory/ com metadata.aprovado (delta-137)
  memoria.py --selftest
Requer Python 3.11+ (mesma linha de base do restante do plugin).
"""
import argparse
import io
import re
import subprocess
import sys
import tempfile
from contextlib import redirect_stdout
from datetime import date
from pathlib import Path

# Dono do catálogo de segredo é a git-guard — mesmo padrão de check_handoff.py:19-23.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "git-guard" / "scripts"))
from segredos import casar  # noqa: E402

DIR_MEMORIA = Path(".claude/memory")
INDICE = "MEMORY.md"
INBOX = DIR_MEMORIA / "inbox"   # fato user/feedback nasce aqui e só entra no índice por `aprovar` (delta-137)
TIPOS_INBOX = ("user", "feedback")
ADR_MEMORIA = "ADR-0050"        # decisão desta delta (a 0049 é issue-fecha-no-merge)
# Teto de leitura do harness (code.claude.com/docs/en/memory): o que passa do teto é
# descartado em silêncio na próxima carga — por isso o gate reprova antes.
LIMITE_LINHAS_INDICE = 200
LIMITE_BYTES_INDICE = 25 * 1024
TIPOS = ("user", "feedback", "project", "reference")
PREFIXO_AGORA = "agora-"        # fato de frente aberta: entra no "Agora" do HANDOFF.md
JANELA_SESSOES = 10             # dias com commit em "Sessões recentes" (teto ~10 da ADR-0025)
RESUMO_MAX = 180                # mesma largura do `resumo` do handoff v2 (R61)
RE_FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)
RE_NAME = re.compile(r"^name:[ \t]*([^\s]+)[ \t]*$", re.M)
RE_DESC = re.compile(r"^description:[ \t]*([^\n]+?)[ \t]*$", re.M)
RE_TYPE = re.compile(r"^[ \t]+type:[ \t]*(\w+)[ \t]*$", re.M)
RE_APROVADO_LINHA = re.compile(r"\n[ \t]+aprovado:[ \t]*\d{4}-\d{2}-\d{2}[ \t]*(?=\n|\Z)")
RE_APROVADO = re.compile(r"^[ \t]+aprovado:[ \t]*(\d{4}-\d{2}-\d{2})[ \t]*$", re.M)


def _entre_aspas(v: str) -> bool:
    return len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'"


def ler_fato(caminho: Path) -> tuple[dict | None, list[str]]:
    """Frontmatter de um fato. (None, achados) sem frontmatter; (dict, achados) com ele — achados
    podem coexistir com o dict: o índice ainda lista o fato, o gate é quem reprova."""
    try:
        texto = caminho.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None, [f"{caminho.name}: não é UTF-8"]
    m = RE_FRONTMATTER.match(texto)
    if not m:
        return None, [f"{caminho.name}: sem frontmatter"]
    fm = m.group(1)
    nome, tipo, aprovado = RE_NAME.search(fm), RE_TYPE.search(fm), RE_APROVADO.search(fm)
    desc = RE_DESC.search(fm)
    desc = desc if desc and desc.group(1).strip() else None   # só espaços = ausente
    achados: list[str] = []
    if not nome or nome.group(1) != caminho.stem:
        achados.append(f"{caminho.name}: name deve ser {caminho.stem!r}")
    if not desc:
        achados.append(f"{caminho.name}: description vazia")
    elif ": " in desc.group(1) and not _entre_aspas(desc.group(1)):
        achados.append(f"{caminho.name}: description com ': ' fora de aspas quebra o YAML")
    if not tipo or tipo.group(1) not in TIPOS:
        achados.append(f"{caminho.name}: metadata.type fora de {TIPOS}")
    achados += [f"{caminho.name}: possível segredo ({n}) na linha {l}" for n, l in casar(texto)]
    fato = {"name": caminho.stem, "description": desc.group(1).strip("\"'") if desc and _entre_aspas(desc.group(1)) else desc.group(1) if desc else "",
            "type": tipo.group(1) if tipo else "", "arquivo": caminho.name,
            "aprovado": aprovado.group(1) if aprovado else ""}
    return fato, achados


def fatos(root: Path, pasta: Path = DIR_MEMORIA) -> tuple[list[dict], list[str]]:
    """Fatos de `pasta` (menos o índice), em ordem de nome, com os achados. Não desce em
    subpasta: o inbox fica fora do índice por construção."""
    itens, achados = [], []
    for p in sorted((root / pasta).glob("*.md")):
        if p.name == INDICE:
            continue
        fato, a = ler_fato(p)
        achados += a
        if fato:
            itens.append(fato)
    return itens, achados


def checar_indice(texto: str) -> list[str]:
    """Teto do harness: acima dele a carga trunca em silêncio."""
    achados = []
    n = len(texto.splitlines())
    if n > LIMITE_LINHAS_INDICE:
        achados.append(f"{INDICE}: {n} linhas > {LIMITE_LINHAS_INDICE} — o harness descarta o excedente")
    b = len(texto.encode("utf-8"))
    if b > LIMITE_BYTES_INDICE:
        achados.append(f"{INDICE}: {b} bytes > {LIMITE_BYTES_INDICE}")
    return achados


def checar_inbox(raiz: list[dict], inbox: list[dict]) -> list[str]:
    """user/feedback só fica na raiz carimbado por `aprovar`; o inbox só recebe user/feedback."""
    achados = [f"{f['arquivo']}: fato {f['type']} fora do inbox sem metadata.aprovado — grave em "
               f"{INBOX}/ e rode `memoria.py aprovar {f['name']}`"
               for f in raiz if f["type"] in TIPOS_INBOX and not f["aprovado"]]
    achados += [f"inbox/{f['arquivo']}: inbox só recebe {TIPOS_INBOX} — grave na raiz de {DIR_MEMORIA}/"
                for f in inbox if f["type"] not in TIPOS_INBOX]
    return achados


def cmd_check(root: Path) -> int:
    itens, achados = fatos(root)
    inbox, achados_inbox = fatos(root, INBOX)
    achados += [f"inbox/{a}" for a in achados_inbox] + checar_inbox(itens, inbox)
    indice = root / DIR_MEMORIA / INDICE
    if indice.is_file():
        achados += checar_indice(indice.read_text(encoding="utf-8"))
    for a in achados:
        print(f"achado: {a}")
    return 1 if achados else 0


def render_indice(itens: list[dict]) -> str:
    """Uma linha por fato, `agora-*` primeiro — é o que o harness carrega (200 linhas/25 KB)."""
    linhas = ["# Memória do projeto — índice gerado por `memoria.py indice` (não edite à mão)", ""]
    for f in sorted(itens, key=lambda f: (not f["name"].startswith(PREFIXO_AGORA), f["name"])):
        linhas.append(f"- [{f['name']}]({f['arquivo']}) — {f['description']}")
    return "\n".join(linhas) + "\n"


def _git(root: Path, *args: str) -> str:
    r = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""


def sessoes_do_git(root: Path, janela: int = JANELA_SESSOES) -> dict[str, list[str]]:
    """Dia → assuntos dos commits (sem merges), mais recente primeiro, até `janela` dias com commit."""
    por_dia: dict[str, list[str]] = {}
    for linha in _git(root, "log", "--no-merges", "--format=%cs%x09%s").splitlines():
        dia, _, assunto = linha.partition("\t")
        if dia not in por_dia and len(por_dia) == janela:
            break
        por_dia.setdefault(dia, []).append(assunto)
    return por_dia


def data_ultimo_commit(root: Path) -> str:
    """Casa com o C16 do check_cycle.py (`git log -1 --format=%cs`); sem git, hoje."""
    return _git(root, "log", "-1", "--format=%cs").strip() or date.today().isoformat()


def _resumo(assuntos: list[str]) -> str:
    texto = "; ".join(assuntos)
    return texto if len(texto) <= RESUMO_MAX else texto[: RESUMO_MAX - 1] + "…"


def render_handoff(root: Path, itens: list[dict], por_dia: dict[str, list[str]]) -> str:
    agora = [f"- **{f['description']}** — [{f['name']}]({DIR_MEMORIA}/{f['arquivo']})"
             for f in itens if f["name"].startswith(PREFIXO_AGORA)] or \
            ["- (nenhum fato `agora-*` em `.claude/memory/` — grave um ao abrir uma frente)"]
    sessoes = [f"- {dia} — {len(a)} commit(s) — {_resumo(a)}" for dia, a in por_dia.items()] or ["- (sem commits)"]
    congelado = root / ".claude" / "handoffs"
    nota = (f"Sessões anteriores à memória vivem em `{congelado.relative_to(root)}/` — congeladas, nunca podadas (ADR-0025/{ADR_MEMORIA})."
            if congelado.is_dir() else "")
    return (
        "# HANDOFF.md — diário de bordo (projeção gerada)\n\n"
        + " ".join(p for p in (
            f"> Gerado por `memoria.py indice` ({ADR_MEMORIA}) — **não edite à mão**. \"Agora\" vem dos fatos `agora-*` de "
            f"`{DIR_MEMORIA}/`; \"Sessões recentes\" vem do git.", nota,
            "Débito/pendência/lição é [debts/](debts/); decisão com renúncia é [docs/adrs/](docs/adrs/); "
            "o que vige é [specs/TRUTH.md](specs/TRUTH.md).") if p) + "\n\n"
        f"**Atualizado em:** {data_ultimo_commit(root)}\n\n"
        "## Agora\n" + "\n".join(agora) + "\n\n"
        "## Sessões recentes\n" + "\n".join(sessoes) + "\n"
    )


def cmd_indice(root: Path, so_checar: bool) -> int:
    if not (root / DIR_MEMORIA).is_dir():  # repo sem memória: não cria pasta nem sobrescreve HANDOFF.md à mão
        print(f"sem {DIR_MEMORIA}/ — nada a projetar")
        return 0
    itens, achados = fatos(root)
    for a in achados:  # ilegível é reportado, nunca some em silêncio (mesmo molde do debito.py indice)
        print(f"[triagem] {a}")
    indice = root / DIR_MEMORIA / INDICE
    novo = render_indice(itens)
    if so_checar:
        atual = indice.read_text(encoding="utf-8") if indice.is_file() else ""
        if atual != novo:
            print(f"{INDICE} desatualizado — rode `memoria.py indice .`")
            return 1
        return 0
    indice.parent.mkdir(parents=True, exist_ok=True)
    indice.write_text(novo, encoding="utf-8")
    (root / "HANDOFF.md").write_text(render_handoff(root, itens, sessoes_do_git(root)), encoding="utf-8")
    print(f"{INDICE} e HANDOFF.md regenerados: {len(itens)} fato(s).")
    return 0


def cmd_injetar(root: Path) -> int:
    """Rota fallback (Q7): stdout do SessionStart vira contexto. Sem índice, silêncio (RNF2)."""
    indice = root / DIR_MEMORIA / INDICE
    if indice.is_file():
        print(f"Memória do projeto ({DIR_MEMORIA}/ — leia o fato antes de agir sobre ele):\n")
        print(indice.read_text(encoding="utf-8"))
    n = len(list((root / INBOX).glob("*.md")))
    if n:
        print(f"{n} fato(s) aguardando aprovação em {INBOX}/")
    return 0


def cmd_aprovar(root: Path, nome: str) -> int:
    """Move inbox/<nome>.md para a raiz da memória carimbando `metadata.aprovado` (data de hoje)."""
    if Path(nome).name != nome or nome.startswith("."):
        print(f"aprovar: nome inválido {nome!r} — use só o name do fato, sem caminho")
        return 1
    nome = nome.removesuffix(".md")
    origem, destino = root / INBOX / f"{nome}.md", root / DIR_MEMORIA / f"{nome}.md"
    if not origem.is_file():
        print(f"erro: {INBOX}/{nome}.md não existe")
        return 1
    if destino.exists():
        print(f"erro: {DIR_MEMORIA}/{nome}.md já existe — renomeie o fato do inbox antes de aprovar")
        return 1
    _, achados = ler_fato(origem)
    if achados:  # fato inválido não sai do inbox
        for a in achados:
            print(f"achado: inbox/{a}")
        return 1
    texto = origem.read_text(encoding="utf-8")
    fim = RE_FRONTMATTER.match(texto).end(1)
    texto = RE_APROVADO_LINHA.sub("", texto[:fim]) + texto[fim:]  # carimbo pré-escrito sai: vale hoje
    fim = RE_FRONTMATTER.match(texto).end(1)
    tipo = RE_TYPE.search(texto, 0, fim)
    recuo = re.match(r"[ \t]*", tipo.group(0)).group(0)
    texto = f"{texto[:tipo.end()]}\n{recuo}aprovado: {date.today().isoformat()}{texto[tipo.end():]}"
    destino.write_text(texto, encoding="utf-8")
    origem.unlink()
    print(f"aprovado: {INBOX}/{nome}.md → {DIR_MEMORIA}/{nome}.md — rode `memoria.py indice .`")
    return 0


def selftest_ler_fato_valido() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "agora-x.md"
        p.write_text("---\nname: agora-x\ndescription: frente x em curso\nmetadata:\n  type: project\n---\n\ncorpo\n", encoding="utf-8")
        fato, achados = ler_fato(p)
        assert fato == {"name": "agora-x", "description": "frente x em curso", "type": "project", "arquivo": "agora-x.md",
                        "aprovado": ""}, fato
        assert achados == [], achados
    print("selftest_ler_fato_valido: OK")


def selftest_ler_fato_nome_diverge() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "agora-x.md"
        p.write_text("---\nname: outro\ndescription: d\nmetadata:\n  type: project\n---\n", encoding="utf-8")
        _, achados = ler_fato(p)
        assert any("name deve ser 'agora-x'" in a for a in achados), achados
    print("selftest_ler_fato_nome_diverge: OK")


def selftest_ler_fato_tipo_e_segredo() -> None:
    aws_falsa = "AK" + "IA" + "3KJ7QWNP2LXVDR8T"   # concatenado: não dispara o G1 do pre-commit
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "ref-x.md"
        p.write_text(f"---\nname: ref-x\ndescription: d\nmetadata:\n  type: segredo\n---\nAWS_KEY = \"{aws_falsa}\"\n", encoding="utf-8")
        _, achados = ler_fato(p)
        assert any("metadata.type" in a for a in achados), achados
        assert any("possível segredo" in a for a in achados), achados
        sem_fm = Path(tmp) / "solto.md"
        sem_fm.write_text("texto sem frontmatter\n", encoding="utf-8")
        fato, achados = ler_fato(sem_fm)
        assert fato is None and achados == ["solto.md: sem frontmatter"], achados
    print("selftest_ler_fato_tipo_e_segredo: OK")


def selftest_ler_fato_description_vazia_e_type_ausente() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "agora-y.md"
        p.write_text("---\nname: agora-y\ndescription:\nmetadata:\n  foo: bar\n---\n", encoding="utf-8")
        fato, achados = ler_fato(p)
        assert fato["name"] == "agora-y", fato
        assert any("description vazia" in a for a in achados), achados
        assert any("metadata.type" in a for a in achados), achados
    print("selftest_ler_fato_description_vazia_e_type_ausente: OK")


def selftest_ler_fato_type_vazio_e_description_em_branco() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "agora-z.md"
        p.write_text("---\nname: agora-z\ndescription:   \nmetadata:\n  type:\nproject\n---\n", encoding="utf-8")
        fato, achados = ler_fato(p)
        assert fato["type"] == "" and fato["description"] == "", fato
        assert any("description vazia" in a for a in achados), achados
        assert any("metadata.type" in a for a in achados), achados
    print("selftest_ler_fato_type_vazio_e_description_em_branco: OK")


def selftest_ler_fato_description_com_dois_pontos() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "agora-w.md"
        base = "---\nname: agora-w\ndescription: {}\nmetadata:\n  type: project\n---\n"
        p.write_text(base.format("a: b"), encoding="utf-8")
        _, achados = ler_fato(p)
        assert any("fora de aspas" in a for a in achados), achados
        p.write_text(base.format('"a: b"'), encoding="utf-8")
        fato, achados = ler_fato(p)
        assert achados == [] and fato["description"] == "a: b", (fato, achados)
    print("selftest_ler_fato_description_com_dois_pontos: OK")


def selftest_checar_indice_teto() -> None:
    curto = "# idx\n- [a](a.md) — a\n"
    assert checar_indice(curto) == []
    no_limite = "\n".join(f"- [f{i}](f{i}.md) — x" for i in range(LIMITE_LINHAS_INDICE))
    assert checar_indice(no_limite) == [], "exatamente o teto de linhas deve passar"
    longo = "\n".join(f"- [f{i}](f{i}.md) — x" for i in range(LIMITE_LINHAS_INDICE + 1))
    assert any("linhas" in a for a in checar_indice(longo))
    gordo = "- [a](a.md) — " + "x" * LIMITE_BYTES_INDICE
    assert any("bytes" in a for a in checar_indice(gordo))
    print("selftest_checar_indice_teto: OK")


def _repo_tmp(tmp: str, commits: tuple[str, ...]) -> Path:
    root = Path(tmp)
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    for assunto in commits:
        (root / "a.txt").write_text(assunto, encoding="utf-8")
        subprocess.run(["git", "-C", str(root), "add", "."], check=True)
        subprocess.run(["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@t",
                        "-c", "commit.gpgsign=false", "-c", "tag.gpgsign=false", "commit", "-q", "-m", assunto], check=True)
    return root


def selftest_render_indice_agora_primeiro() -> None:
    itens = [{"name": "ref-z", "description": "z", "type": "reference", "arquivo": "ref-z.md"},
             {"name": "agora-b", "description": "b", "type": "project", "arquivo": "agora-b.md"}]
    linhas = render_indice(itens).splitlines()
    assert linhas[2] == "- [agora-b](agora-b.md) — b", linhas
    assert linhas[3] == "- [ref-z](ref-z.md) — z", linhas
    print("selftest_render_indice_agora_primeiro: OK")


def selftest_sessoes_do_git_agrupa_por_dia() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = _repo_tmp(tmp, ("feat: um", "fix: dois"))
        por_dia = sessoes_do_git(root)
        assert list(por_dia) == [date.today().isoformat()], por_dia
        assert por_dia[date.today().isoformat()] == ["fix: dois", "feat: um"], por_dia
    print("selftest_sessoes_do_git_agrupa_por_dia: OK")


def selftest_render_handoff_sem_git() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / DIR_MEMORIA).mkdir(parents=True)
        texto = render_handoff(root, [], {})
        assert f"**Atualizado em:** {date.today().isoformat()}" in texto, texto
        assert "nenhum fato `agora-*`" in texto, texto
        assert "## Sessões recentes\n- (sem commits)" in texto, texto
    print("selftest_render_handoff_sem_git: OK")


def selftest_indice_idempotente() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = _repo_tmp(tmp, ("feat: base",))
        (root / DIR_MEMORIA).mkdir(parents=True)
        (root / DIR_MEMORIA / "agora-x.md").write_text(
            "---\nname: agora-x\ndescription: x em curso\nmetadata:\n  type: project\n---\n", encoding="utf-8")
        (root / DIR_MEMORIA / INDICE).write_text("<<<<<<< conflito\n", encoding="utf-8")
        assert cmd_indice(root, so_checar=False) == 0
        primeiro = (root / DIR_MEMORIA / INDICE).read_text(encoding="utf-8")
        assert "conflito" not in primeiro and "- [agora-x](agora-x.md) — x em curso" in primeiro, primeiro
        assert cmd_indice(root, so_checar=True) == 0
        assert (root / DIR_MEMORIA / INDICE).read_text(encoding="utf-8") == primeiro
        handoff = (root / "HANDOFF.md").read_text(encoding="utf-8")
        assert "- **x em curso** — [agora-x](.claude/memory/agora-x.md)" in handoff, handoff
    print("selftest_indice_idempotente: OK")


def selftest_indice_sem_memoria_nao_toca_handoff() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = _repo_tmp(tmp, ("feat: base",))
        (root / "HANDOFF.md").write_text("escrito à mão\n", encoding="utf-8")
        antes = (root / "HANDOFF.md").read_bytes()
        assert cmd_indice(root, so_checar=False) == 0
        assert (root / "HANDOFF.md").read_bytes() == antes
        assert not (root / DIR_MEMORIA).exists()
        assert cmd_indice(root, so_checar=True) == 0
    print("selftest_indice_sem_memoria_nao_toca_handoff: OK")


def selftest_ler_fato_nao_utf8() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "ruim.md"
        p.write_bytes(b"\xff\xfe")
        fato, achados = ler_fato(p)
        assert fato is None and achados == ["ruim.md: não é UTF-8"], achados
    print("selftest_ler_fato_nao_utf8: OK")


FATO_FEEDBACK = "---\nname: {0}\ndescription: d\nmetadata:\n  type: feedback\n---\n\n**Why:** w\n"


def selftest_checar_inbox() -> None:
    raiz = [{"name": "pref", "type": "feedback", "arquivo": "pref.md", "aprovado": ""},
            {"name": "ok", "type": "user", "arquivo": "ok.md", "aprovado": "2026-10-24"},
            {"name": "agora-x", "type": "project", "arquivo": "agora-x.md", "aprovado": ""}]
    inbox = [{"name": "novo", "type": "user", "arquivo": "novo.md", "aprovado": ""},
             {"name": "agora-y", "type": "project", "arquivo": "agora-y.md", "aprovado": ""}]
    achados = checar_inbox(raiz, inbox)
    assert len(achados) == 2, achados
    assert achados[0].startswith("pref.md: fato feedback fora do inbox") and "aprovar pref" in achados[0], achados
    assert achados[1].startswith("inbox/agora-y.md: inbox só recebe"), achados
    print("selftest_checar_inbox: OK")


def selftest_aprovar_move_e_carimba() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / INBOX).mkdir(parents=True)
        (root / INBOX / "pref.md").write_text(FATO_FEEDBACK.format("pref"), encoding="utf-8")
        assert cmd_check(root) == 0, "fato feedback no inbox é válido"
        assert [f["name"] for f in fatos(root)[0]] == [], "inbox fora do índice"
        assert cmd_aprovar(root, "pref") == 0
        assert not (root / INBOX / "pref.md").exists()
        fato, achados = ler_fato(root / DIR_MEMORIA / "pref.md")
        assert achados == [] and fato["aprovado"] == date.today().isoformat(), (fato, achados)
        assert "  type: feedback\n  aprovado: " in (root / DIR_MEMORIA / "pref.md").read_text(encoding="utf-8")
        assert cmd_check(root) == 0, "aprovado na raiz passa no check"
        assert cmd_aprovar(root, "pref") == 1, "fora do inbox: erro"
        (root / INBOX / "pref.md").write_text(FATO_FEEDBACK.format("pref"), encoding="utf-8")
        assert cmd_aprovar(root, "pref") == 1, "destino existente: erro, nada sobrescrito"
        (root / INBOX / "ruim.md").write_text(FATO_FEEDBACK.format("outro"), encoding="utf-8")
        assert cmd_aprovar(root, "ruim") == 1 and (root / INBOX / "ruim.md").exists(), "inválido fica no inbox"
        (root / INBOX / "velho.md").write_text(FATO_FEEDBACK.format("velho").replace("feedback\n", "feedback\n  aprovado: 2000-01-01\n"), encoding="utf-8")
        assert cmd_aprovar(root, "velho.md") == 0, "nome com .md vale como sem .md"
        assert ler_fato(root / DIR_MEMORIA / "velho.md")[0]["aprovado"] == date.today().isoformat(), "carimbo sempre hoje"
        assert (root / DIR_MEMORIA / "velho.md").read_text(encoding="utf-8").count("aprovado:") == 1
        bloco = "---\nname: bloco\ndescription: |\n  um\n\n  dois\nmetadata:\n  type: feedback\n  aprovado: 2000-01-01\n---\n\ncorpo\n"
        (root / INBOX / "bloco.md").write_text(bloco, encoding="utf-8")
        assert cmd_aprovar(root, "bloco") == 0
        saida = (root / DIR_MEMORIA / "bloco.md").read_text(encoding="utf-8")
        assert "  um\n\n  dois\n" in saida and saida.count("aprovado:") == 1, saida
        assert f"aprovado: {date.today().isoformat()}" in saida, saida
        (root / DIR_MEMORIA / "solto.md").write_text(FATO_FEEDBACK.format("solto"), encoding="utf-8")
        assert cmd_check(root) == 1, "feedback na raiz sem aprovado reprova"
        solto = (root / DIR_MEMORIA / "solto.md").read_text(encoding="utf-8")
        (root / INBOX / ".oculto.md").write_text(FATO_FEEDBACK.format(".oculto"), encoding="utf-8")
        for ruim in ("../solto", "../x.md", "a/b", ".oculto"):
            assert cmd_aprovar(root, ruim) == 1, ruim
        assert (root / DIR_MEMORIA / "solto.md").read_text(encoding="utf-8") == solto, "traversal não toca a raiz"
        assert (root / INBOX / ".oculto.md").exists() and not (root / INBOX / "a").exists(), "nada se move"
    print("selftest_aprovar_move_e_carimba: OK")


def selftest_injetar_conta_inbox() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / INBOX).mkdir(parents=True)
        (root / DIR_MEMORIA / INDICE).write_text("# idx\n", encoding="utf-8")
        saida = io.StringIO()
        with redirect_stdout(saida):
            cmd_injetar(root)
        assert "aguardando aprovação" not in saida.getvalue(), "inbox vazio: silêncio"
        (root / INBOX / "a.md").write_text(FATO_FEEDBACK.format("a"), encoding="utf-8")
        (root / INBOX / "b.md").write_text(FATO_FEEDBACK.format("b"), encoding="utf-8")
        saida = io.StringIO()
        with redirect_stdout(saida):
            cmd_injetar(root)
        assert saida.getvalue().rstrip().endswith("2 fato(s) aguardando aprovação em .claude/memory/inbox/"), saida.getvalue()
    print("selftest_injetar_conta_inbox: OK")


def selftest() -> None:
    selftest_ler_fato_valido()
    selftest_ler_fato_nome_diverge()
    selftest_ler_fato_tipo_e_segredo()
    selftest_ler_fato_description_vazia_e_type_ausente()
    selftest_ler_fato_type_vazio_e_description_em_branco()
    selftest_ler_fato_description_com_dois_pontos()
    selftest_checar_indice_teto()
    selftest_render_indice_agora_primeiro()
    selftest_sessoes_do_git_agrupa_por_dia()
    selftest_render_handoff_sem_git()
    selftest_indice_idempotente()
    selftest_indice_sem_memoria_nao_toca_handoff()
    selftest_ler_fato_nao_utf8()
    selftest_checar_inbox()
    selftest_aprovar_move_e_carimba()
    selftest_injetar_conta_inbox()
    print("selftest: OK (gate, índice, projeção, inbox)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("comando", nargs="?", choices=["check", "indice", "injetar", "aprovar"])
    ap.add_argument("alvo", nargs="*", help="[ROOT]; em aprovar, NAME [ROOT]")
    ap.add_argument("--check", action="store_true", help="indice: só compara, não escreve")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return
    if not args.comando:
        ap.error("comando obrigatório sem --selftest")
    alvo = list(args.alvo)
    nome = alvo.pop(0) if args.comando == "aprovar" and alvo else ""
    if args.comando == "aprovar" and not nome:
        ap.error("aprovar exige o name do fato: memoria.py aprovar NAME [ROOT]")
    root = Path(alvo[0] if alvo else ".").resolve()
    sys.exit({"check": lambda: cmd_check(root),
              "indice": lambda: cmd_indice(root, args.check),
              "injetar": lambda: cmd_injetar(root),
              "aprovar": lambda: cmd_aprovar(root, nome)}[args.comando]())


if __name__ == "__main__":
    main()
