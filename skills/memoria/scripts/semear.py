#!/usr/bin/env python3
"""Seed da memória de projeto (delta-134, ADR-0053): migra o "Agora" de um HANDOFF.md escrito à mão
para fatos agora-* em .claude/memory/, com aprovação humana entre o rascunho e o --aplicar.

Uso:
  semear.py [ROOT]                rascunha um agora-<slug>.md por bullet do "Agora" em .claude/memoria-semente/
  semear.py [ROOT] --aplicar      move os rascunhos para .claude/memory/, desliga a memória nativa e roda o indice
  semear.py [ROOT] --so-settings  só grava "autoMemoryEnabled": false no .claude/settings.json (scaffold da projeto-init)
  semear.py --selftest
Requer Python 3.11+ (mesma linha de base do restante do plugin).
"""
import json
import os
import posixpath
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from memoria import DIR_MEMORIA, PREFIXO_AGORA, RESUMO_MAX, cmd_check, cmd_indice, ler_fato  # noqa: E402
# Dono do recorte de seção `## titulo` é o check_handoff.py da skill irmã: reusa, não duplica.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "handoff" / "scripts"))
from check_handoff import _secao  # noqa: E402

# O rascunho fica FORA de .claude/memory/ — a pasta existir já liga a rota memória, o injetar e o
# Stop — e na MESMA profundidade dela, para o link recalculado valer nos dois lugares.
RASCUNHO = Path(".claude/memoria-semente")
SETTINGS = Path(".claude/settings.json")
PALAVRAS_SLUG = 5               # termos do slug `agora-<slug>`
RE_BULLET = re.compile(r"^- ", re.M)
RE_NEGRITO = re.compile(r"\*\*(.+?)\*\*", re.S)
RE_LINK_MD = re.compile(r"\[([^\]]*)\]\([^)]*\)")
RE_ALVO_LINK = re.compile(r"(\]\()([^)\s]+)")
RE_ESQUEMA = re.compile(r"^[a-z][a-z0-9+.-]*:", re.I)


def bullets_agora(texto: str) -> list[str]:
    """Bullets de primeiro nível da seção `## Agora`, cada um com as linhas de continuação."""
    return [b.strip() for b in RE_BULLET.split(_secao(texto, "Agora") or "")[1:] if b.strip()]


def descricao_semente(bullet: str) -> str:
    """Trecho em negrito (sem ele, o bullet) em texto puro: sem símbolo inicial nem pontuação final,
    `: ` vira ` — ` (YAML sem aspas) e o corte é em RESUMO_MAX."""
    m = RE_NEGRITO.search(bullet)
    texto = RE_LINK_MD.sub(r"\1", m.group(1) if m else bullet).replace("**", "").replace("`", "")
    texto = re.sub(r"^\W+", "", re.sub(r"\s+", " ", texto)).rstrip(" .:").replace(": ", " — ")
    texto = texto or "frente semeada do HANDOFF.md"
    return texto if len(texto) <= RESUMO_MAX else texto[: RESUMO_MAX - 1] + "…"


def slug(texto: str) -> str:
    """kebab ASCII dos PALAVRAS_SLUG primeiros termos."""
    ascii_ = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()
    return "-".join(re.findall(r"[a-z0-9]+", ascii_)[:PALAVRAS_SLUG]) or "frente"


def religar_links(md: str) -> str:
    """Link relativo à raiz vira relativo a .claude/memory/ (um nível abaixo de .claude/): o seed à mão
    da delta-132 manteve o alvo da raiz e deixou 26 links mortos. Esquema, absoluto e âncora ficam."""
    def troca(m: re.Match) -> str:
        alvo, sep, ancora = m.group(2).partition("#")
        if not alvo or alvo.startswith("/") or RE_ESQUEMA.match(alvo):
            return m.group(0)
        return m.group(1) + posixpath.relpath(posixpath.normpath(alvo), DIR_MEMORIA.as_posix()) + sep + ancora
    return RE_ALVO_LINK.sub(troca, md)


def fato_semente(bullet: str, nome: str, data: str) -> str:
    return (f"---\nname: {nome}\ndescription: {descricao_semente(bullet)}\nmetadata:\n  type: project\n---\n\n"
            f"{religar_links(bullet)}\n\nOrigem: HANDOFF.md (índice à mão, {data}) — semeado por semear.py\n")


def ler_settings(root: Path) -> dict | None:
    """Conteúdo do .claude/settings.json; ausente = {}; ilegível, não objeto, diretório ou com NaN/Infinity
    (que o JSON estrito não regrava) = None — a recusa vem ANTES de qualquer escrita."""
    caminho = root / SETTINGS
    try:
        if (caminho.exists() and not caminho.is_file()) or (caminho.is_symlink() and not caminho.exists()):
            return None   # diretório ou symlink quebrado: tratar como ausente sobrescreveria o link
        config = json.loads(caminho.read_text(encoding="utf-8")) if caminho.exists() else {}
        json.dumps(config, allow_nan=False)
    except (ValueError, OSError):   # ValueError inclui UnicodeDecodeError
        return None
    return config if isinstance(config, dict) else None


def desligar_memoria_nativa(root: Path, config: dict) -> None:
    """Acrescenta "autoMemoryEnabled": false preservando as outras chaves (ADR-0050). Escrita atômica:
    arquivo temporário ao lado + os.replace, para um crash não truncar hooks e permissões do consumidor."""
    config["autoMemoryEnabled"] = False
    alvo = (root / SETTINGS).resolve()   # symlink de dotfiles: grava no alvo real, o link continua link
    alvo.parent.mkdir(parents=True, exist_ok=True)
    tmp = alvo.with_name(alvo.name + ".tmp")
    try:
        tmp.write_text(json.dumps(config, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
        if alvo.exists():
            shutil.copymode(alvo, tmp)
        os.replace(tmp, alvo)
    except BaseException:
        tmp.unlink(missing_ok=True)   # não deixa .tmp órfão; o erro segue
        raise


def semear(root: Path) -> int:
    """Rascunha um `agora-*` por bullet do "Agora" em RASCUNHO/. Não cria .claude/memory/ nem toca
    HANDOFF.md/settings: quem aprova é o humano, apagando o que não entra antes do --aplicar."""
    if (root / DIR_MEMORIA).exists():
        print(f"semear: {DIR_MEMORIA}/ já existe — o repo já tem memória")
        return 1
    if (root / RASCUNHO).exists():
        print(f"semear: {RASCUNHO}/ já existe — revise e rode `semear.py . --aplicar`, ou apague a pasta")
        return 1
    handoff = root / "HANDOFF.md"
    texto = handoff.read_text(encoding="utf-8") if handoff.is_file() else ""
    if _secao(texto, "Agora") is None:
        print("semear: HANDOFF.md ausente ou sem `## Agora` — repo sem índice nasce pelo scaffold da projeto-init")
        return 1
    bullets = bullets_agora(texto)
    if not bullets:
        print("semear: `## Agora` sem nenhum bullet — nada a semear")
        return 1
    (root / RASCUNHO).mkdir(parents=True)
    data, usados = date.today().isoformat(), set()
    for bullet in bullets:
        base = PREFIXO_AGORA + slug(descricao_semente(bullet))
        nome, n = base, 2
        while nome in usados:
            nome, n = f"{base}-{n}", n + 1
        usados.add(nome)
        (root / RASCUNHO / f"{nome}.md").write_text(fato_semente(bullet, nome, data), encoding="utf-8")
        print(f"rascunho: {RASCUNHO}/{nome}.md — {descricao_semente(bullet)}")
    print(f"{len(usados)} rascunho(s). Apague o que não entra, ajuste o resto e rode `semear.py . --aplicar`.")
    return 0


def _git_rc(root: Path, *args: str) -> subprocess.CompletedProcess:
    """git direto (o `_git` do memoria.py engole o rc != 0, que aqui é o sinal). Sem git, rc != 0."""
    try:
        return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    except OSError:
        return subprocess.CompletedProcess(args, 127, "", "")


def aplicar_semente(root: Path) -> int:
    """Valida tudo antes de escrever qualquer coisa; depois move os rascunhos, desliga a memória
    nativa no settings e regenera as projeções."""
    pasta = root / RASCUNHO
    if (root / DIR_MEMORIA).exists():
        print(f"semear --aplicar: {DIR_MEMORIA}/ já existe — o repo já tem memória")
        return 1
    if not pasta.is_dir():
        print(f"semear --aplicar: sem {RASCUNHO}/ — rode `semear.py .` antes")
        return 1
    if _git_rc(root, "check-ignore", "-q", (DIR_MEMORIA / "x.md").as_posix()).returncode == 0:
        print(f"semear: {DIR_MEMORIA}/ está no .gitignore — libere antes de aplicar")
        return 1
    status = _git_rc(root, "status", "--porcelain", "--", "HANDOFF.md")
    if status.returncode == 0 and status.stdout.strip():
        print("semear: HANDOFF.md tem alteração não commitada — commite antes de aplicar")
        return 1
    rascunhos = sorted(pasta.glob("*.md"))
    if not rascunhos:
        print(f"semear: nada a aplicar em {RASCUNHO}/ — apague a pasta para desistir")
        return 1
    achados = [a for p in rascunhos for a in ler_fato(p)[1]]
    config = ler_settings(root)
    if config is None:
        achados.append(f"{SETTINGS}: não é um objeto JSON legível — corrija antes de aplicar")
    if achados:
        for a in achados:
            print(f"achado: {a}")
        return 1
    (root / DIR_MEMORIA).mkdir(parents=True)
    for p in rascunhos:
        p.rename(root / DIR_MEMORIA / p.name)
    try:
        pasta.rmdir()
    except OSError:
        print(f"aviso: {RASCUNHO}/ ficou com arquivo que não é fato — apague à mão")
    desligar_memoria_nativa(root, config)
    cmd_indice(root, so_checar=False)
    print(f"Revise e commite {DIR_MEMORIA}/, HANDOFF.md e {SETTINGS}.")
    return 0


def so_settings(root: Path) -> int:
    """Só a chave no settings — o scaffold da projeto-init chama isto ao criar .claude/memory/."""
    config = ler_settings(root)
    if config is None:
        print(f"achado: {SETTINGS}: não é um objeto JSON legível — corrija e rode de novo")
        return 1
    desligar_memoria_nativa(root, config)
    print(f"{SETTINGS}: autoMemoryEnabled false")
    return 0


HANDOFF_SEMENTE = (
    "# HANDOFF.md\n\n**Atualizado em:** 2026-10-02\n\n## Agora\n"
    "- **✅ v1.0 nas duas pontas: delta-9 arquivada.** Ver [plano](docs/plano.md#fase-2), "
    "[sessão](.claude/handoffs/H_x.md), [site](https://exemplo.org/a) e [topo](#agora).\n"
    "  - detalhe na [ADR](docs/adrs/ADR-0001.md)\n"
    "- **✅ v1.0 nas duas pontas: delta-9 arquivada.** repetido\n"
    "- frente sem negrito com `código`\n\n"
    "## Sessões recentes\n- [H_x](.claude/handoffs/H_x.md) — não vira fato\n")


def selftest_descricao_e_slug() -> None:
    assert descricao_semente("- **📋 Plano aprovado: fase 2.** resto") == "Plano aprovado — fase 2"
    assert descricao_semente("**ÂNCORA ALFA:** resto") == "ÂNCORA ALFA"
    assert descricao_semente("sem negrito, com [link](a.md) e `código`") == "sem negrito, com link e código"
    assert len(descricao_semente("**" + "a" * 300 + "**")) == RESUMO_MAX
    assert slug("Ação já: um dois três quatro") == "acao-ja-um-dois-tres"
    assert religar_links("[a](docs/x.md#s) [b](.claude/handoffs/H.md) [c](https://x.org/y) [d](#t) [e](/abs)") == \
        "[a](../../docs/x.md#s) [b](../handoffs/H.md) [c](https://x.org/y) [d](#t) [e](/abs)"
    print("selftest_descricao_e_slug: OK")


def selftest_semear_rascunho_e_links() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for rel in ("docs/plano.md", ".claude/handoffs/H_x.md", "docs/adrs/ADR-0001.md"):
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            (root / rel).write_text("x", encoding="utf-8")
        (root / "HANDOFF.md").write_text(HANDOFF_SEMENTE, encoding="utf-8")
        antes = (root / "HANDOFF.md").read_bytes()
        assert semear(root) == 0
        nomes = sorted(p.stem for p in (root / RASCUNHO).glob("*.md"))
        assert nomes == ["agora-frente-sem-negrito-com-codigo", "agora-v1-0-nas-duas-pontas",
                         "agora-v1-0-nas-duas-pontas-2"], nomes
        for p in (root / RASCUNHO).glob("*.md"):
            assert ler_fato(p)[1] == [], (p.name, ler_fato(p)[1])
        fato, _ = ler_fato(root / RASCUNHO / "agora-v1-0-nas-duas-pontas.md")
        assert fato["description"] == "v1.0 nas duas pontas — delta-9 arquivada", fato
        texto = (root / RASCUNHO / "agora-v1-0-nas-duas-pontas.md").read_text(encoding="utf-8")
        assert "[plano](../../docs/plano.md#fase-2)" in texto and "[sessão](../handoffs/H_x.md)" in texto, texto
        assert "(https://exemplo.org/a)" in texto and "[topo](#agora)" in texto, texto
        assert "](../../docs/adrs/ADR-0001.md)" in texto, "a linha de continuação entra no corpo"
        assert f"\nOrigem: HANDOFF.md (índice à mão, {date.today().isoformat()})" in texto, texto
        # defeito real da delta-132 (26 links mortos): todo link relativo do rascunho resolve
        for p in (root / RASCUNHO).glob("*.md"):
            for alvo in re.findall(r"\]\(([^)#\s]+)", p.read_text(encoding="utf-8")):
                if not RE_ESQUEMA.match(alvo):
                    assert (p.parent / alvo).resolve().is_file(), (p.name, alvo)
        corpo = "".join(p.read_text(encoding="utf-8") for p in (root / RASCUNHO).glob("*.md"))
        assert "não vira fato" not in corpo, "Sessões recentes e handoffs antigos não viram fato"
        assert (root / "HANDOFF.md").read_bytes() == antes
        assert not (root / DIR_MEMORIA).exists() and not (root / SETTINGS).exists()
        assert semear(root) == 1, "rascunho existente: recusa"
    print("selftest_semear_rascunho_e_links: OK")


def selftest_semear_aplicar() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "docs").mkdir()
        (root / "docs" / "plano.md").write_text("x", encoding="utf-8")
        (root / "HANDOFF.md").write_text("## Agora\n- **Frente A: em curso.** ver [plano](docs/plano.md)\n"
                                         "- **Frente B** descartada\n", encoding="utf-8")
        (root / SETTINGS).parent.mkdir(parents=True)
        (root / SETTINGS).write_text('{"hooks": {"Stop": []}, "permissions": {"allow": ["Bash(ls)"]}}', encoding="utf-8")
        assert semear(root) == 0
        (root / RASCUNHO / "agora-frente-b.md").unlink()   # aprovação humana: apagar o que não entra
        assert aplicar_semente(root) == 0
        assert sorted(p.name for p in (root / DIR_MEMORIA).glob("*.md")) == ["MEMORY.md", "agora-frente-a-em-curso.md"]
        assert not (root / RASCUNHO).exists()
        assert json.loads((root / SETTINGS).read_text(encoding="utf-8")) == \
            {"hooks": {"Stop": []}, "permissions": {"allow": ["Bash(ls)"]}, "autoMemoryEnabled": False}
        handoff = (root / "HANDOFF.md").read_text(encoding="utf-8")
        assert "- **Frente A — em curso** — [agora-frente-a-em-curso](.claude/memory/agora-frente-a-em-curso.md)" in handoff, handoff
        fato = (root / DIR_MEMORIA / "agora-frente-a-em-curso.md").read_text(encoding="utf-8")
        assert "](../../docs/plano.md)" in fato and (root / DIR_MEMORIA / "../../docs/plano.md").resolve().is_file()
        assert cmd_check(root) == 0
        assert semear(root) == 1 and aplicar_semente(root) == 1, "memória existente: recusa"
    print("selftest_semear_aplicar: OK")


def selftest_semear_recusas() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        assert semear(root) == 1, "sem HANDOFF.md"
        (root / "HANDOFF.md").write_text("# só título\n", encoding="utf-8")
        assert semear(root) == 1 and not (root / RASCUNHO).exists(), "sem ## Agora"
        assert aplicar_semente(root) == 1, "sem rascunho"
        (root / "HANDOFF.md").write_text("## Agora\n- **X** y\n", encoding="utf-8")
        assert semear(root) == 0
        (root / SETTINGS).write_text("{não é json", encoding="utf-8")
        assert aplicar_semente(root) == 1
        assert (root / RASCUNHO / "agora-x.md").exists() and not (root / DIR_MEMORIA).exists(), "settings inválido: nada se move"
        (root / SETTINGS).write_text("[]", encoding="utf-8")
        assert aplicar_semente(root) == 1, "settings que não é objeto"
        (root / SETTINGS).unlink()
        (root / RASCUNHO / "agora-x.md").write_text("sem frontmatter\n", encoding="utf-8")
        assert aplicar_semente(root) == 1 and not (root / DIR_MEMORIA).exists(), "rascunho inválido: nada se move"
        (root / RASCUNHO / "agora-x.md").write_text(
            "---\nname: agora-x\ndescription: x\nmetadata:\n  type: project\n---\n", encoding="utf-8")
        assert aplicar_semente(root) == 0
        assert json.loads((root / SETTINGS).read_text(encoding="utf-8")) == {"autoMemoryEnabled": False}, "ausente vira {} + chave"
    print("selftest_semear_recusas: OK")


def selftest_correcao_1() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "HANDOFF.md").write_text("## Agora\n- **X** y\n", encoding="utf-8")
        (root / RASCUNHO).mkdir(parents=True)
        antes = (root / "HANDOFF.md").read_bytes()
        assert aplicar_semente(root) == 1, "rascunho vazio: recusa"
        assert not (root / DIR_MEMORIA).exists() and (root / "HANDOFF.md").read_bytes() == antes
        (root / RASCUNHO).rmdir()
        assert semear(root) == 0
        (root / SETTINGS).mkdir()   # settings.json como diretório
        assert aplicar_semente(root) == 1 and so_settings(root) == 1
        assert not (root / DIR_MEMORIA).exists() and (root / RASCUNHO / "agora-x.md").exists()
        (root / SETTINGS).rmdir()
        (root / SETTINGS).write_text('{"a": NaN}', encoding="utf-8")
        assert aplicar_semente(root) == 1 and not (root / DIR_MEMORIA).exists(), "NaN: recusa"
        (root / SETTINGS).write_text('{"a": 1}', encoding="utf-8")
        assert aplicar_semente(root) == 0
        assert not list((root / SETTINGS).parent.glob("*.tmp")), "sem resíduo do temporário"
    print("selftest_correcao_1: OK")


def selftest_correcao_2() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / SETTINGS).parent.mkdir(parents=True)
        real = root / "dotfiles.json"
        real.write_text('{"hooks": {}}', encoding="utf-8")
        real.chmod(0o640)
        (root / SETTINGS).symlink_to(real)
        assert so_settings(root) == 0
        assert (root / SETTINGS).is_symlink(), "o link continua link"
        assert json.loads(real.read_text(encoding="utf-8")) == {"hooks": {}, "autoMemoryEnabled": False}
        assert real.stat().st_mode & 0o777 == 0o640, "modo preservado"
        assert not list(root.rglob("*.tmp")), "sem .tmp"
        (root / SETTINGS).unlink()
        (root / SETTINGS).symlink_to(root / "some.json")   # symlink quebrado
        assert so_settings(root) == 1 and (root / SETTINGS).is_symlink() and not (root / "some.json").exists()
    print("selftest_correcao_2: OK")


def selftest_correcao_final() -> None:
    git = ["git", "-c", "user.email=t@t", "-c", "user.name=t", "-c", "commit.gpgsign=false"]
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "HANDOFF.md").write_text("## Agora\n", encoding="utf-8")
        assert semear(root) == 1 and not (root / RASCUNHO).exists(), "Agora sem bullet: recusa"
        (root / "HANDOFF.md").write_text("## Agora\n- **X** y\n", encoding="utf-8")
        subprocess.run(["git", "-C", tmp, "init", "-q"], check=True)
        (root / ".gitignore").write_text(".claude/\n", encoding="utf-8")
        subprocess.run([*git, "-C", tmp, "add", "."], check=True)
        subprocess.run([*git, "-C", tmp, "commit", "-qm", "x"], check=True)
        assert semear(root) == 0
        assert aplicar_semente(root) == 1 and not (root / DIR_MEMORIA).exists(), "memória ignorada: recusa"
        (root / ".gitignore").write_text(".claude/memory/\n", encoding="utf-8")   # padrão de diretório, pasta ainda inexistente
        assert aplicar_semente(root) == 1 and not (root / DIR_MEMORIA).exists(), "padrão com barra final: recusa"
        (root / ".gitignore").write_text("", encoding="utf-8")
        subprocess.run([*git, "-C", tmp, "commit", "-qam", "libera"], check=True)
        (root / "HANDOFF.md").write_text("## Agora\n- **X** y\n- sujo\n", encoding="utf-8")
        assert aplicar_semente(root) == 1 and not (root / DIR_MEMORIA).exists(), "HANDOFF.md sujo: recusa"
        subprocess.run([*git, "-C", tmp, "commit", "-qam", "limpa"], check=True)
        assert aplicar_semente(root) == 0, "limpo e liberado: aplica"
    print("selftest_correcao_final: OK")


def selftest_so_settings() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        assert so_settings(root) == 0
        assert json.loads((root / SETTINGS).read_text(encoding="utf-8")) == {"autoMemoryEnabled": False}, "ausente: {} + chave"
        (root / SETTINGS).write_text('{"hooks": {"Stop": []}, "autoMemoryEnabled": true}', encoding="utf-8")
        assert so_settings(root) == 0
        assert json.loads((root / SETTINGS).read_text(encoding="utf-8")) == {"hooks": {"Stop": []}, "autoMemoryEnabled": False}
        (root / SETTINGS).write_text("{quebrado", encoding="utf-8")
        assert so_settings(root) == 1 and (root / SETTINGS).read_text(encoding="utf-8") == "{quebrado", "inválido: intocado"
        assert not (root / DIR_MEMORIA).exists() and not (root / RASCUNHO).exists(), "só o settings"
    print("selftest_so_settings: OK")


def selftest() -> None:
    selftest_descricao_e_slug()
    selftest_semear_rascunho_e_links()
    selftest_semear_aplicar()
    selftest_semear_recusas()
    selftest_so_settings()
    selftest_correcao_1()
    selftest_correcao_2()
    selftest_correcao_final()
    print("selftest: OK (descrição, links, aplicar, recusas, settings)")


def main() -> None:
    if "--selftest" in sys.argv:
        selftest()
        return
    alvo = [a for a in sys.argv[1:] if not a.startswith("--")]
    root = Path(alvo[0] if alvo else ".").resolve()
    if "--so-settings" in sys.argv:
        sys.exit(so_settings(root))
    sys.exit(aplicar_semente(root) if "--aplicar" in sys.argv else semear(root))


if __name__ == "__main__":
    main()
