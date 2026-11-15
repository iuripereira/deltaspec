#!/usr/bin/env python3
"""Gate do DT-056: script novo que aceita '--selftest' não pode ficar fora do CI ou dos
dois READMEs sem que nada acuse — aconteceu de verdade com o guarda-confidencialidade.py
no PR #237, passou pelo CI verde do próprio PR. Detecção é lexical (procura a string
'--selftest' no texto-fonte), não semântica: um script cujo selftest roda incondicional
ao ser chamado como módulo principal (caso do projecao.py) não é candidato — limite
conhecido do método, documentado aqui em vez de resolvido com lista de exceção."""

import re
import sys
from pathlib import Path

DIRETORIOS = ("skills/*/scripts/*.py", ".github/scripts/*.py", ".claude/hooks/*.py")
FLAG = "--selftest"


def candidatos(root: Path) -> list[Path]:
    """.py sob os três diretórios cujo texto-fonte contém a flag — ordenado para saída estável."""
    achados = []
    for padrao in DIRETORIOS:
        achados.extend(root.glob(padrao))
    return sorted(p for p in achados if FLAG in p.read_text(encoding="utf-8"))


def faltando(rel: str, ci_txt: str, readme_txt: str, readme_en_txt: str) -> list[str]:
    """Nomes dos destinos que não citam '<rel> --selftest'; [] quando os três citam."""
    padrao = re.compile(rf"{re.escape(rel)}\s+{re.escape(FLAG)}\b")
    destinos = {"ci.yml": ci_txt, "README.md": readme_txt, "README.en.md": readme_en_txt}
    return [nome for nome, texto in destinos.items() if not padrao.search(texto)]


def selftest() -> int:
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "skills" / "x" / "scripts").mkdir(parents=True)
        (root / ".github" / "scripts").mkdir(parents=True)
        (root / ".claude" / "hooks").mkdir(parents=True)
        (root / "skills" / "x" / "scripts" / "a.py").write_text("if '--selftest' in __import__('sys').argv: pass\n")
        (root / ".github" / "scripts" / "b.py").write_text("# sem a flag\n")
        (root / ".claude" / "hooks" / "c.py").write_text("'--selftest'\n")
        achados = candidatos(root)
        assert sorted(p.name for p in achados) == ["a.py", "c.py"], f"só a.py e c.py declaram a flag: {achados}"

    assert faltando("skills/x/scripts/a.py", "skills/x/scripts/a.py --selftest\n", "", "") == ["README.md", "README.en.md"], \
        "presente só no ci.yml deveria acusar os dois READMEs"
    assert faltando("skills/x/scripts/a.py",
                     "skills/x/scripts/a.py --selftest\n",
                     "skills/x/scripts/a.py --selftest\n",
                     "skills/x/scripts/a.py --selftest\n") == [], \
        "presente nos três não deveria acusar nada"
    assert faltando("a.py", "b.py --selftest\n", "a.py --selftest\n", "a.py --selftest\n") == ["ci.yml"], \
        "caminho parecido não deveria casar (a.py não é b.py)"
    print("inventario_selftests selftest: OK (4 casos)")
    return 0


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    root = Path(__file__).resolve().parents[2]
    ci_txt = (root / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    readme_txt = (root / "README.md").read_text(encoding="utf-8")
    readme_en_txt = (root / "README.en.md").read_text(encoding="utf-8")
    ok = True
    for p in candidatos(root):
        rel = str(p.relative_to(root))
        omissos = faltando(rel, ci_txt, readme_txt, readme_en_txt)
        if omissos:
            ok = False
            print(f"inventario_selftests: {rel} aceita --selftest mas falta em: {', '.join(omissos)}")
    if ok:
        print("inventario_selftests: todos os candidatos registrados nos três destinos")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
