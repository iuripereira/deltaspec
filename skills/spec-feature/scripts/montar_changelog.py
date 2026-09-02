#!/usr/bin/env python3
"""Monta o CHANGELOG a partir dos fragmentos de changelog.d/ (delta-105).

Cada PR deixa um arquivo `changelog.d/<slug>.<categoria>.md` com UMA linha: o
bullet, sem o `- ` inicial. O montador colide tudo no `## [Não lançado]` e apaga
os fragmentos. Nomes distintos = zero conflito entre PRs vivas, que é a dor que
este mecanismo existe para matar.

O formato do bullet é o mesmo da ADR-0035 e quem o valida é o check_changelog.py
— aqui não há regra de forma duplicada.

Uso: montar_changelog.py [--dir changelog.d] [--changelog CHANGELOG.md]
     montar_changelog.py --preencher-pr 186 [--dir changelog.d]
     montar_changelog.py --verificar        # gate: valida fragmentos, não escreve
     montar_changelog.py --selftest
Exit 0 = ok · 1 = corrigir · 2 = erro de uso.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_changelog import CATEGORIAS, LIMITE_CHARS, RE_REFERENCIA, checar  # noqa: E402

# Sufixo ASCII do arquivo -> categoria PT-BR. ASCII de propósito: 'Segurança' e
# 'Obsoleto' viram nome de arquivo em qualquer sistema, sem acento no caminho.
CATEGORIA_POR_SUFIXO = {
    "adicionado": "Adicionado", "mudado": "Mudado", "corrigido": "Corrigido",
    "removido": "Removido", "obsoleto": "Obsoleto", "seguranca": "Segurança",
}
RE_FRAGMENTO = re.compile(r"^(?P<slug>.+)\.(?P<cat>" + "|".join(CATEGORIA_POR_SUFIXO) + r")\.md$")


def ler_fragmentos(diretorio: Path):
    """(categoria, texto, caminho) de cada fragmento, na ordem canônica das
    categorias e, dentro de cada uma, por nome de arquivo. Arquivo fora do
    padrão de nome é ignorado — README.md e .gitkeep convivem no diretório."""
    achados = []
    for caminho in sorted(diretorio.glob("*.md")):
        m = RE_FRAGMENTO.match(caminho.name)
        if not m:
            continue
        texto = caminho.read_text(encoding="utf-8").strip()
        achados.append((CATEGORIA_POR_SUFIXO[m.group("cat")], texto, caminho))
    return sorted(achados, key=lambda f: (CATEGORIAS.index(f[0]), f[2].name))


def montar(frags) -> str:
    """Bloco '## [Não lançado]' com uma subseção por categoria que tem fragmento.
    Categoria vazia não vira subseção — o check_changelog não reclama de seção
    vazia, mas ela é ruído para quem lê."""
    linhas = ["## [Não lançado]", ""]
    atual = None
    for categoria, texto, _ in frags:
        if categoria != atual:
            if atual is not None:
                linhas.append("")
            linhas.append(f"### {categoria}")
            atual = categoria
        linhas.append(f"- {texto}")
    linhas.append("")
    return "\n".join(linhas)


def verificar(frags) -> list[str]:
    """Valida cada fragmento com o MESMO gate do CHANGELOG (check_changelog.checar),
    montando um bloco de um bullet só. Devolve mensagens já com o caminho do
    fragmento — número de linha do bloco montado não ajuda a achar o arquivo."""
    problemas = []
    for categoria, texto, caminho in frags:
        bloco = f"## [Não lançado]\n\n### {categoria}\n- {texto}\n"
        falhas = checar(bloco)
        for check in ("C1", "C2", "C3"):
            for _linha, msg in falhas[check]:
                problemas.append(f"{caminho.name}: [{check}] {msg}")
    return problemas


RE_SECAO_NAO_LANCADO = re.compile(r"^## \[Não lançado\][^\n]*\n(?:(?!^## \[).*\n)*", re.MULTILINE)


def preencher_pr(frags, numero: int):
    """Acrescenta '(#N)' ao fragmento que ainda não tem referência. Idempotente:
    fragmento já referenciado não é tocado, então rodar duas vezes não duplica."""
    mudados = []
    for _categoria, texto, caminho in frags:
        if RE_REFERENCIA.search(texto):
            continue
        caminho.write_text(f"{texto} (#{numero})\n", encoding="utf-8")
        mudados.append(caminho)
    return mudados


def aplicar(changelog: Path, bloco: str) -> None:
    """Troca a seção '## [Não lançado]' pelo bloco. Versão lançada e rodapé não
    são tocados — a licença da ADR-0035 é para reprojeção deliberada, nunca
    efeito colateral de um montador."""
    texto = changelog.read_text(encoding="utf-8")
    if not RE_SECAO_NAO_LANCADO.search(texto):
        raise SystemExit(f"{changelog}: não achei a seção '## [Não lançado]' — crie-a antes de montar.")
    changelog.write_text(RE_SECAO_NAO_LANCADO.sub(bloco.rstrip("\n") + "\n\n", texto, count=1), encoding="utf-8")


def selftest() -> None:
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        raiz = Path(d)
        (raiz / "b-regras.adicionado.md").write_text("Regras nativas no config (#186)\n", encoding="utf-8")
        (raiz / "a-ids.corrigido.md").write_text("Ids de vigência corrigidos (#186)\n", encoding="utf-8")
        (raiz / "README.md").write_text("# changelog.d\n\nprosa qualquer\n", encoding="utf-8")
        frags = ler_fragmentos(raiz)
        # README.md não casa o padrão de nome e some sem erro
        assert len(frags) == 2, frags
        # ordem canônica das categorias vence a ordem alfabética do arquivo
        assert [f[0] for f in frags] == ["Adicionado", "Corrigido"], frags
        texto = montar(frags)
        assert texto.startswith("## [Não lançado]\n"), texto
        assert "### Adicionado\n- Regras nativas no config (#186)\n" in texto
        assert "### Corrigido\n- Ids de vigência corrigidos (#186)\n" in texto
        assert texto.endswith("\n")
        # categoria sem fragmento não vira subseção vazia
        assert "### Mudado" not in texto

    with tempfile.TemporaryDirectory() as d:
        raiz = Path(d)
        (raiz / "longo.adicionado.md").write_text("x" * (LIMITE_CHARS + 1) + " (#1)\n", encoding="utf-8")
        (raiz / "sem-ref.mudado.md").write_text("Bullet sem referência de PR\n", encoding="utf-8")
        (raiz / "ok.corrigido.md").write_text("Bullet correto (#2)\n", encoding="utf-8")
        problemas = verificar(ler_fragmentos(raiz))
        assert len(problemas) == 2, problemas
        assert any("longo.adicionado.md" in p and "chars" in p for p in problemas), problemas
        assert any("sem-ref.mudado.md" in p and "#NNN" in p for p in problemas), problemas
        assert not any("ok.corrigido.md" in p for p in problemas), problemas
        # o caminho do fragmento entra na mensagem: o número de linha do bloco
        # montado não ajuda ninguém a achar o arquivo errado

    with tempfile.TemporaryDirectory() as d:
        raiz = Path(d)
        (raiz / "sem.adicionado.md").write_text("Entrada sem referência\n", encoding="utf-8")
        (raiz / "com.mudado.md").write_text("Entrada já referenciada (#12)\n", encoding="utf-8")
        mudados = preencher_pr(ler_fragmentos(raiz), 186)
        assert [c.name for c in mudados] == ["sem.adicionado.md"], mudados
        assert (raiz / "sem.adicionado.md").read_text(encoding="utf-8") == "Entrada sem referência (#186)\n"
        assert (raiz / "com.mudado.md").read_text(encoding="utf-8") == "Entrada já referenciada (#12)\n"

    with tempfile.TemporaryDirectory() as d:
        raiz = Path(d)
        cl = raiz / "CHANGELOG.md"
        cl.write_text(
            "# Changelog\n\nprosa\n\n## [Não lançado]\n\n## [1.0.0] - 2026-01-01\n\n"
            "### Adicionado\n- Coisa antiga (#1)\n\n[1.0.0]: http://x/v1.0.0\n",
            encoding="utf-8")
        aplicar(cl, "## [Não lançado]\n\n### Corrigido\n- Coisa nova (#2)\n")
        saida = cl.read_text(encoding="utf-8")
        assert "### Corrigido\n- Coisa nova (#2)" in saida, saida
        assert "- Coisa antiga (#1)" in saida, "versão lançada é intocável"
        assert "[1.0.0]: http://x/v1.0.0" in saida, "rodapé preservado"
        assert saida.index("## [Não lançado]") < saida.index("## [1.0.0]"), "ordem C4"
        assert saida.count("## [Não lançado]") == 1, saida

    # A CLI recusa argumento desconhecido ANTES de tocar arquivo: o default
    # escreve o CHANGELOG e apaga fragmentos, e --help/typo não podem cair nele
    # (defeito real: '--help' aplicou o montador no repo em 2026-09-02).
    import subprocess
    r = subprocess.run([sys.executable, __file__, "--nao-existe"], capture_output=True, text=True)
    assert r.returncode == 2 and "desconhecido" in r.stderr, (r.returncode, r.stderr)
    r = subprocess.run([sys.executable, __file__, "--dir"], capture_output=True, text=True)
    assert r.returncode == 2 and "exige um valor" in r.stderr, (r.returncode, r.stderr)
    r = subprocess.run([sys.executable, __file__, "--help"], capture_output=True, text=True)
    assert r.returncode == 0 and "Uso:" in r.stdout, (r.returncode, r.stdout)
    print("selftest OK")


# Flags que recebem valor e flags sem valor. Argumento fora destas listas aborta
# com erro de uso ANTES de qualquer leitura: o default deste script escreve o
# CHANGELOG e apaga fragmentos, e um typo (ou --help) não pode cair nele.
COM_VALOR = ("--dir", "--changelog", "--preencher-pr")
SEM_VALOR = ("--selftest", "--verificar")


def main() -> None:
    args = sys.argv[1:]
    if "--help" in args or "-h" in args:
        print(__doc__.strip())
        return
    i = 0
    while i < len(args):
        arg = args[i]
        if arg in COM_VALOR:
            if i + 1 >= len(args):
                print(f"erro de uso: {arg} exige um valor.", file=sys.stderr)
                sys.exit(2)
            i += 2
        elif arg in SEM_VALOR:
            i += 1
        else:
            print(f"erro de uso: argumento desconhecido {arg!r} — veja --help.", file=sys.stderr)
            sys.exit(2)
    if "--selftest" in args:
        selftest()
        return

    def opcao(nome, default):
        return args[args.index(nome) + 1] if nome in args else default

    diretorio = Path(opcao("--dir", "changelog.d"))
    if not diretorio.is_dir():
        print(f"{diretorio}/ não existe — nada a montar.")
        return
    frags = ler_fragmentos(diretorio)

    # --preencher-pr roda ANTES da validação: fragmento sem '(#NNN)' é o estado
    # normal enquanto a PR não existe, e validar primeiro trancaria o único
    # comando capaz de resolver isso. Depois de carimbar, valida como os demais.
    if "--preencher-pr" in args:
        for caminho in preencher_pr(frags, int(opcao("--preencher-pr", "0"))):
            print(f"  + referência em {caminho.name}")
        frags = ler_fragmentos(diretorio)

    problemas = verificar(frags)
    if problemas:
        print("fragmentos fora do formato:", file=sys.stderr)
        for p in problemas:
            print(f"  {p}", file=sys.stderr)
        sys.exit(1)

    if "--preencher-pr" in args:
        return
    if "--verificar" in args:
        print(f"OK — {len(frags)} fragmento(s) no formato.")
        return

    if not frags:
        print("Nenhum fragmento — CHANGELOG intocado.")
        return
    aplicar(Path(opcao("--changelog", "CHANGELOG.md")), montar(frags))
    for _c, _t, caminho in frags:
        caminho.unlink()
    print(f"[Não lançado] montado com {len(frags)} entrada(s); fragmentos removidos.")


if __name__ == "__main__":
    main()
