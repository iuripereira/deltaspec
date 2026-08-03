#!/usr/bin/env python3
"""Valida integridade documental contra o manifesto deps.toml (skill guarding-doc-integrity).

Checks:
  C1  espelhos em sincronia — cada pattern presente no arquivo dono E em cada espelho
  C2  materialização — pattern ausente em qualquer outro arquivo (scan_globs - exclude_globs)
  C3  links — todo link markdown relativo resolve para arquivo existente
      (scan_globs - exclude_links_globs; conjunto próprio, delta-027)

Uso: validate_integrity.py [DIR | caminho/deps.toml]   (default: ./deps.toml)
Exit 0 = íntegro; 1 = violações (listadas); 2 = erro de uso/manifesto.
Requer Python 3.11+ (tomllib).
"""
import re
import sys
import tomllib
from pathlib import Path

# ponytail: alvo sem espaços e anchors não validados; portar github_slugify se doer
MD_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")

# Dono do default do C3 quando o manifesto não declara `exclude_links_globs` (delta-027).
# Motivo e alternativas renunciadas: comentário da chave em templates/deps.toml.
EXCLUDE_LINKS_PADRAO = ["**/_archive/**/*.md", "docs/adrs/**/*.md"]

# Atalho relativo ao repositório do GitHub (`../../issues/88`), não caminho de arquivo:
# resolvê-lo como caminho acusaria os links vivos de issue e PR do DEBT.md (delta-027).
# Casa a FORMA, nunca só o prefixo `../../`: cortar por prefixo silenciava todo link que
# sobe dois níveis — 10 deles neste repo, de SKILL.md e references para ADR, justamente a
# classe que apodrece em rename (achado ALTO do review da delta-027).
ATALHO_GITHUB = re.compile(r"\.\./\.\./(issues|pull|discussions)/")

# Onde um link deixa de ser referência e vira citação (delta-029), pelo conteúdo e nunca
# pelo nome do arquivo — repo que chame o changelog de outro jeito recebe a mesma proteção.
CORTE_LANCADO = re.compile(r"^## \[\d+\.\d+\.\d+\]")  # Keep a Changelog: release publicado é imutável
CODE_SPAN = re.compile(r"`[^`]*`")                    # `[x](y.md)` é sintaxe citada
CERCA = re.compile(r"^\s*```")


def die(msg: str) -> None:
    print(f"ERRO: {msg}")
    sys.exit(2)


def load_manifest(arg: str):
    p = Path(arg)
    manifest = p if p.suffix == ".toml" else p / "deps.toml"
    if not manifest.is_file():
        die(f"manifesto não encontrado: {manifest}")
    try:
        with open(manifest, "rb") as f:
            return manifest.parent.resolve(), tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        die(f"deps.toml inválido: {e}")


def collect(root: Path, globs: list[str]) -> set[Path]:
    files: set[Path] = set()
    for g in globs:
        files.update(x for x in root.glob(g) if x.is_file())
    return files


def linhas_vivas(texto: str) -> list[tuple[int, str]]:
    """(nº, linha) onde um link é referência de verdade — pura, sem I/O (delta-029).

    Para na primeira seção de versão lançada, e devolve cada linha sem os trechos em
    crase; linha dentro de bloco cercado não sai. O que fica é o que o C3 deve cobrar.
    """
    vivas: list[tuple[int, str]] = []
    dentro_de_cerca = False
    for n, linha in enumerate(texto.splitlines(), 1):
        if CORTE_LANCADO.match(linha):
            break
        if CERCA.match(linha):
            dentro_de_cerca = not dentro_de_cerca
            continue
        if not dentro_de_cerca:
            vivas.append((n, CODE_SPAN.sub("", linha)))
    return vivas


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        selftest()
        return
    root, cfg = load_manifest(sys.argv[1] if len(sys.argv) > 1 else ".")
    varrido = collect(root, cfg.get("scan_globs", ["**/*.md"]))
    scan_valores = varrido - collect(root, cfg.get("exclude_globs", []))
    scan_links = varrido - collect(root, cfg.get("exclude_links_globs", EXCLUDE_LINKS_PADRAO))
    violations: list[str] = []

    for owner in cfg.get("owner", []):
        ofile = root / owner["file"]
        sanctioned = [ofile] + [root / m for m in owner.get("mirrors", [])]
        for path in sanctioned:
            if not path.is_file():
                violations.append(f"[C1] arquivo do manifesto não existe: {path.relative_to(root)}")
        sanctioned_ok = [p for p in sanctioned if p.is_file()]
        for val in owner.get("value", []):
            rx = re.compile(val["pattern"])
            name = val.get("name", val["pattern"])
            missing = [p for p in sanctioned_ok if not rx.search(p.read_text(encoding="utf-8"))]
            if missing:
                violations.append(
                    f"[C1] {name}: padrão ausente em "
                    + ", ".join(str(m.relative_to(root)) for m in missing)
                )
            else:
                print(f"[C1] {name}: OK (dono + {len(sanctioned) - 1} espelho(s))")
            for path in sorted(scan_valores - set(sanctioned)):
                for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                    if rx.search(line):
                        violations.append(
                            f"[C2] {name}: valor fora dos sancionados — {path.relative_to(root)}:{i}"
                        )

    checked = 0
    for path in sorted(scan_links):
        for i, line in linhas_vivas(path.read_text(encoding="utf-8")):
            for target in MD_LINK.findall(line):
                if target.startswith(("http://", "https://", "mailto:", "#", "/")) \
                        or "{" in target or ATALHO_GITHUB.match(target):
                    continue  # "{...}" = placeholder de template, não link
                checked += 1
                dest = path.parent / target.split("#")[0]
                if not dest.exists():
                    violations.append(f"[C3] link morto — {path.relative_to(root)}:{i} → {target}")
    print(f"[C3] links relativos verificados: {checked}")

    if violations:
        print("\n".join(violations))
        print(f"RESULTADO: FAIL ({len(violations)} violação(ões))")
        sys.exit(1)
    print("RESULTADO: PASS")


def selftest() -> None:
    """Exercita C1/C2/C3 contra fixtures — o gate também precisa de gate."""
    import subprocess
    import tempfile

    manifesto = """scan_globs = ["*.md"]
exclude_globs = []

[[owner]]
file = "PRD.md"
mirrors = ["CLAUDE.md"]

  [[owner.value]]
  name = "limite"
  pattern = 'R\\$ ?2\\.000'
"""

    def rodar(arquivos: dict, manifesto_txt: str = manifesto) -> subprocess.CompletedProcess:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "deps.toml").write_text(manifesto_txt, encoding="utf-8")
            for nome, txt in arquivos.items():
                caminho = root / nome
                caminho.parent.mkdir(parents=True, exist_ok=True)
                caminho.write_text(txt, encoding="utf-8")
            return subprocess.run(
                [sys.executable, __file__, str(root)], capture_output=True, text=True
            )

    limpo = rodar({
        "PRD.md": "Limite de R$ 2.000 por pedido. Ver [dicionário](CLAUDE.md).\n",
        "CLAUDE.md": "Limite: R$ 2.000.\n",
    })
    assert limpo.returncode == 0, f"fixture limpa deveria passar:\n{limpo.stdout}"
    assert "RESULTADO: PASS" in limpo.stdout

    sujo = rodar({
        "PRD.md": "Limite de R$ 2.000. Ver [sumiu](nao-existe.md).\n",  # C3 link morto
        "CLAUDE.md": "Sem o valor aqui.\n",                            # C1 espelho dessincronizado
        "OUTRO.md": "Cópia solta: R$ 2.000.\n",                        # C2 fora dos sancionados
    })
    assert sujo.returncode == 1, f"fixture suja deveria falhar:\n{sujo.stdout}"
    for codigo in ("[C1]", "[C2]", "[C3]"):
        assert codigo in sujo.stdout, f"não pegou {codigo}:\n{sujo.stdout}"

    # delta-027: o C3 tem conjunto próprio — dispensa de citar valor (C2) não é dispensa de link vivo
    limpo_c2 = manifesto.replace('exclude_globs = []', 'exclude_globs = ["NOTAS.md"]')
    excluido = rodar({
        "PRD.md": "Limite de R$ 2.000.\n",
        "CLAUDE.md": "Limite: R$ 2.000.\n",
        "NOTAS.md": "Cópia solta R$ 2.000 e um [link morto](sumiu.md).\n",
    }, limpo_c2)
    assert excluido.returncode == 1, f"link morto em arquivo excluído do C2 deveria falhar:\n{excluido.stdout}"
    # "[C3] link morto", não "[C3]": a linha de resumo do C3 sai sempre e o assert seria vácuo
    assert "[C3] link morto" in excluido.stdout, f"o C3 tem de varrer o excluído:\n{excluido.stdout}"
    assert "[C2]" not in excluido.stdout, f"o C2 continua dispensando o excluído:\n{excluido.stdout}"

    # delta-027: `../../issues/N` é atalho do GitHub, não caminho de arquivo
    atalho = rodar({
        "PRD.md": "Limite de R$ 2.000. Ticket [#88](../../issues/88) e PR [#9](../../pull/9).\n",
        "CLAUDE.md": "Limite: R$ 2.000.\n",
    })
    assert atalho.returncode == 0, f"atalho do GitHub não é link morto:\n{atalho.stdout}"

    # delta-027 (review): subir dois níveis não é atalho do GitHub — o corte casa a forma,
    # nunca o prefixo, senão silencia todo link de SKILL.md/references para ADR
    sobe = rodar({
        "PRD.md": "Limite de R$ 2.000.\n",
        "CLAUDE.md": "Limite: R$ 2.000.\n",
        "skills/x/references/n.md": "Ver [adr](../../../docs/adrs/SUMIU.md).\n",
    }, manifesto.replace('scan_globs = ["*.md"]', 'scan_globs = ["**/*.md"]'))
    assert sobe.returncode == 1, f"link ../../../ para arquivo é link, não atalho:\n{sobe.stdout}"
    assert "[C3] link morto" in sobe.stdout, f"o C3 tem de acusar:\n{sobe.stdout}"

    # delta-027: histórico imutável fora do C3 por default; a chave declarada manda
    hist = {
        "PRD.md": "Limite de R$ 2.000.\n",
        "CLAUDE.md": "Limite: R$ 2.000.\n",
        "docs/adrs/ADR-0001-x.md": "Ver [extinto](sumiu.md).\n",
        "specs/_archive/001-x/plan.md": "Ver [extinto](sumiu.md).\n",
    }
    todos = 'scan_globs = ["**/*.md"]'
    padrao = rodar(hist, manifesto.replace('scan_globs = ["*.md"]', todos))
    assert padrao.returncode == 0, f"sem a chave, o default protege o histórico:\n{padrao.stdout}"
    declarado = rodar(hist, manifesto.replace(
        'scan_globs = ["*.md"]', todos + '\nexclude_links_globs = []'))
    assert declarado.returncode == 1, f"chave declarada manda sobre o default:\n{declarado.stdout}"
    # conta a linha de violação, não o prefixo "[C3]" — a linha de resumo também o carrega
    assert declarado.stdout.count("[C3] link morto") == 2, f"os dois links do histórico:\n{declarado.stdout}"

    # delta-029: seção lançada é histórico imutável (Keep a Changelog); [Não lançado] é viva
    notas = ("# Notas\n\n"
             "## [Não lançado]\n\nVer [vivo](sumiu-vivo.md).\n\n"
             "## [1.1.0] - 2026-01-02\n\nVer [antigo](sumiu-antigo.md).\n\n"
             "## [1.0.0] - 2026-01-01\n\nVer [mais antigo](sumiu-mais.md).\n")
    lancado = rodar({
        "PRD.md": "Limite de R$ 2.000.\n", "CLAUDE.md": "Limite: R$ 2.000.\n", "NOTAS.md": notas,
    })
    assert lancado.returncode == 1, f"o link da seção viva tem de acusar:\n{lancado.stdout}"
    assert lancado.stdout.count("[C3] link morto") == 1, \
        f"só o da seção [Não lançado] — o recorte para na 1ª versão lançada:\n{lancado.stdout}"
    assert "sumiu-vivo.md" in lancado.stdout, f"o acusado é o da seção viva:\n{lancado.stdout}"

    # delta-029: arquivo sem seção lançada segue varrido inteiro
    comum = rodar({
        "PRD.md": "Limite de R$ 2.000.\n", "CLAUDE.md": "Limite: R$ 2.000.\n",
        "NOTAS.md": "# Notas\n\nTexto e [morto](sumiu.md) no fim.\n",
    })
    assert comum.returncode == 1 and "sumiu.md" in comum.stdout, \
        f"sem seção lançada, nada muda:\n{comum.stdout}"

    # delta-029: sintaxe citada não é referência — crase e bloco cercado
    citado = rodar({
        "PRD.md": "Limite de R$ 2.000.\n", "CLAUDE.md": "Limite: R$ 2.000.\n",
        "NOTAS.md": ("Escreva assim: `[texto](citado.md)`.\n\n"
                     "```\n[exemplo](cercado.md)\n```\n\n"
                     "Mas [este](de-verdade.md) é referência.\n"),
    })
    assert citado.returncode == 1, f"o link fora da crase tem de acusar:\n{citado.stdout}"
    assert citado.stdout.count("[C3] link morto") == 1, \
        f"só o de verdade; crase e cerca são sintaxe citada:\n{citado.stdout}"
    assert "de-verdade.md" in citado.stdout, f"o acusado é o de fora:\n{citado.stdout}"

    print("selftest: OK (9 fixtures, C1/C2/C3 detectados; C3 com conjunto próprio, recorte e sintaxe citada)")


if __name__ == "__main__":
    main()
