#!/usr/bin/env python3
"""Recorta do CHANGELOG a seção de uma versão e confere a sync (delta-117).

A skill `release` publica a Release do GitHub com `--notes-file`, e as notas são o
corpo do `## [X.Y.Z]` do CHANGELOG. O mesmo recorte confere a sync `main → develop`
por conjunto de bullets — bullet que some no merge é a fusão silenciosa que o DT-142
registra. Um recorte só, testado, em vez de um awk por skill.

Uso: secao_changelog.py X.Y.Z [--changelog CHANGELOG.md]   # imprime o corpo da seção
     secao_changelog.py "Não lançado"                       # qualquer rótulo entre colchetes
     secao_changelog.py --sync X.Y.Z --antes DEV.md --main MAIN.md --depois RESULTADO.md
     secao_changelog.py --selftest
Exit 0 = ok · 1 = seção ausente ou sync que perde/infla bullet · 2 = erro de uso.

ESPELHO: `conferir_sync()` tem gêmeo em shell/awk no template
`skills/projeto-infra/references/infra/workflows/sync-check.yml` — o CI do consumidor
não tem o framework nem Python (ADR-0045). Mesma regra dos dois lados: bullet é a
linha que começa com `- `, a seção vai do `## [rótulo]` ao próximo `## ` e linhas de
comentário HTML não contam. Mudou um, mude o outro no mesmo commit.

Por que não importa `secoes()`/`bullets()` do `check_changelog.py` (revisão da PR #442):
o contrato é outro. `conferir_sync()` é o gêmeo em Python do awk do `sync-check.yml` e
precisa dar o mesmo veredito que ele — bullet é a primeira linha `- `, sem juntar a
continuação e sem exigir categoria, que é o que o awk consegue repetir. O `bullets()`
do `check_changelog` junta a continuação e só vê bullet sob categoria; usá-lo faria o
Python e o CI divergirem. E `secao()` recorta o corpo bruto das notas da Release
mascarando comentário HTML, que o `check_changelog` ainda não mascara (DT-167).
Limite conhecido, igual nos dois gêmeos: linha `- ` dentro de bloco cercado, no corpo
de uma seção, conta como bullet. Se um dia os dois precisarem entender cerca, ela entra
nos dois no mesmo commit.
"""
import argparse
import sys
from pathlib import Path
import re

CHANGELOG_PADRAO = "CHANGELOG.md"
NAO_LANCADO = "Não lançado"
# Onde a seção acaba: o próximo cabeçalho de nível 2 (versão ou não — é o mesmo
# critério do `check_changelog.bullets()`) ou a primeira definição de link do rodapé
# (`[1.2.0]: https://...`) — sem a segunda parada, a seção mais antiga levaria o
# rodapé inteiro junto.
RE_FIM = re.compile(r"^(?:## |\[[^\]]+\]:)", re.M)
MARCA_BULLET = "- "
ABRE_COMENTARIO, FECHA_COMENTARIO = "<!--", "-->"
# Marcador que o git deixa no conflito. Só `<<<<<<<` e `>>>>>>>`: `=======` sozinho
# também é sublinhado de título setext em Markdown.
RE_MARCADOR_CONFLITO = re.compile(r"^(?:<{7}|>{7})(?: |$)", re.M)


class SecaoAusente(ValueError):
    """O rótulo pedido não tem `## [rótulo]` no texto."""


def sem_comentarios(texto: str) -> str:
    """Tira as linhas que tocam um bloco `<!-- … -->`, inclusive o bloco sem fecho.
    Por linha, não por caractere, para o awk do sync-check fazer igual. Sem isso a
    primeira release vinda do template leva a instrução comentada nas notas e termina
    num `<!--` aberto, que esconde o resto do corpo da PR."""
    fora, dentro = [], False
    for linha in texto.splitlines(keepends=True):
        if not dentro and ABRE_COMENTARIO in linha:
            dentro = True
        if dentro:
            if FECHA_COMENTARIO in linha:
                dentro = False
            continue
        fora.append(linha)
    return "".join(fora)


def secao(texto: str, rotulo: str) -> str:
    """Corpo de `## [rotulo]`: do cabeçalho (exclusive) ao próximo `## ` ou ao rodapé
    de links (exclusive), sem comentários HTML. Termina com uma quebra de linha; vazio
    quando a seção não tem corpo. Rótulo ausente levanta SecaoAusente."""
    texto = sem_comentarios(texto)
    m = re.search(rf"^## \[{re.escape(rotulo)}\][^\n]*\n?", texto, re.M)
    if not m:
        raise SecaoAusente(f"seção '## [{rotulo}]' ausente no CHANGELOG")
    resto = texto[m.end():]
    fim = RE_FIM.search(resto)
    corpo = resto[:fim.start()] if fim else resto
    corpo = corpo.strip("\n")
    return corpo + "\n" if corpo else ""


def bullets(corpo: str) -> list[str]:
    """Linhas de bullet `- ` do corpo, na ordem. A linha de continuação de um bullet
    quebrado não entra — é a regra que o awk do sync-check consegue repetir."""
    return [linha for linha in corpo.splitlines() if linha.startswith(MARCA_BULLET)]


def conferir_sync(antes: str, main: str, depois: str, versao: str) -> list[str]:
    """Problemas da sync `main → develop` da versão lançada; lista vazia = ok.

    `antes` é o CHANGELOG da develop antes da sync, `main` o da main com a versão
    lançada, `depois` o resultado do merge. Duas regras, por conjunto, nunca por
    contagem — a develop ainda carrega no `[Não lançado]` o que a release acabou de
    lançar, então a contagem cai em toda sync correta e empata em troca de bullet:
    1. todo bullet do `[Não lançado]` de antes está, depois, no `[Não lançado]` ou
       na `## [versao]` da main (perdido = nenhum dos dois);
    2. a `## [versao]` do resultado não tem bullet fora da mesma seção da main
       (é o bullet não lançado que o merge limpo empurra para baixo do cabeçalho).
    Marcador de conflito no resultado também é problema: a conferência roda antes do
    commit, e um conflito mal resolvido passaria nas duas regras.
    Seção ausente no resultado conta como vazia; nas outras entradas levanta
    SecaoAusente."""
    marcadores = [f"marcador de conflito no resultado, linha {depois.count(chr(10), 0, m.start()) + 1}"
                  for m in RE_MARCADOR_CONFLITO.finditer(depois)]
    lancada_main = bullets(secao(main, versao))
    try:
        nao_lancado_depois = bullets(secao(depois, NAO_LANCADO))
    except SecaoAusente:
        nao_lancado_depois = []
    try:
        lancada_depois = bullets(secao(depois, versao))
    except SecaoAusente:
        lancada_depois = []
    lancada = set(lancada_main)
    aceitos = set(nao_lancado_depois) | lancada
    problemas = [f"perdido — estava no [{NAO_LANCADO}] da develop e sumiu: {b}"
                 for b in bullets(secao(antes, NAO_LANCADO)) if b not in aceitos]
    problemas += [f"fora do lançado — está no [{versao}] da develop mas não no da main: {b}"
                  for b in lancada_depois if b not in lancada]
    return marcadores + problemas


def selftest() -> int:
    texto = (
        "# Changelog\n\nprosa de abertura\n\n"
        "## [Não lançado]\n\n### Adicionado\n- bullet solto (#9)\n\n"
        "## [1.2.0] - 2026-01-02\n\n### Adicionado\n- primeiro (#1)\n- segundo (#2)\n\n"
        "### Corrigido\n- terceiro (#3)\n\n"
        "## [1.1.0] - 2026-01-01\n\n### Adicionado\n- antigo (#0)\n\n"
        "[Não lançado]: https://x/compare/v1.2.0...HEAD\n"
        "[1.2.0]: https://x/compare/v1.1.0...v1.2.0\n"
    )
    meio = secao(texto, "1.2.0")
    assert meio.startswith("### Adicionado\n- primeiro (#1)"), meio
    assert meio.endswith("- terceiro (#3)\n") and "1.1.0" not in meio, "para no próximo `## [`"
    assert len(bullets(meio)) == 3, bullets(meio)
    ultima = secao(texto, "1.1.0")
    assert ultima == "### Adicionado\n- antigo (#0)\n", f"a mais antiga para antes do rodapé: {ultima!r}"
    assert bullets(secao(texto, NAO_LANCADO)) == ["- bullet solto (#9)"], "rótulo com espaço e acento funciona"
    assert secao("## [0.1.0]\n\n## [0.0.1]\n- x\n", "0.1.0") == "", "seção sem corpo é vazia, não erro"
    assert secao("## [0.1.0]", "0.1.0") == "", "cabeçalho no fim do arquivo, sem quebra"
    try:
        secao(texto, "1.2")
        raise AssertionError("prefixo de versão não pode casar `1.2.0`")
    except SecaoAusente:
        pass
    # Fim de seção = qualquer `## ` (mesmo critério do check_changelog e do awk).
    migracao = "## [Não lançado]\n\n### Adicionado\n- a (#1)\n\n## Notas de migração\n\n- passo 1\n"
    assert bullets(secao(migracao, NAO_LANCADO)) == ["- a (#1)"], "`## ` sem colchete encerra a seção"
    # Template liberado como 0.1.0: instrução comentada e rodapé comentado sem sair nas notas.
    template = (
        "## [Não lançado]\n\n## [0.1.0] - 2026-01-01\n\n### Adicionado\n- x (#1)\n\n"
        "<!--\nNo release: renomeie ... -->\n\n"
        "<!-- Rodapé: um link por versão.\n[Não lançado]: https://x/compare/v0.1.0...HEAD\n"
        "[0.1.0]: https://x/releases/tag/v0.1.0 -->\n"
    )
    assert secao(template, "0.1.0") == "### Adicionado\n- x (#1)\n", secao(template, "0.1.0")
    assert secao("## [1.0.0]\n- a (#1)\n<!-- sem fecho\n- b (#2)\n", "1.0.0") == "- a (#1)\n", \
        "comentário sem fecho some até o fim"

    # conferir_sync — o ensaio da revisão: release/1.1.0 levou A e B; N entrou na develop depois.
    def cl(nao_lancado: list[str], lancada: list[str] | None = None, versao: str = "1.1.0") -> str:
        s = "# Changelog\n\n## [Não lançado]\n\n### Adicionado\n" + "".join(f"{b}\n" for b in nao_lancado)
        if lancada is not None:
            s += f"\n## [{versao}] - 2026-01-02\n\n### Adicionado\n" + "".join(f"{b}\n" for b in lancada)
        return s + "\n## [1.0.0] - 2026-01-01\n\n### Adicionado\n- velho (#1)\n"
    A, B, N, E = "- Coisa A (#2)", "- Coisa B (#3)", "- Coisa N (#4)", "- Coisa E (#6)"
    main = cl([], [A, B])
    antes = cl([A, B, N])
    assert conferir_sync(antes, main, cl([N], [A, B]), "1.1.0") == [], "sync correta passa"
    assert conferir_sync(cl([A, B]), main, cl([], [A, B]), "1.1.0") == [], \
        "sync sem bullet novo passa — a contagem caía de 2 para 0 e reprovava"
    limpo = conferir_sync(antes, main, cl([], [N, A, B]), "1.1.0")
    assert len(limpo) == 2 and all(N in p for p in limpo), f"merge limpo que empurra N sob [1.1.0]: {limpo}"
    troca = conferir_sync(antes, main, cl([E], [A, B]), "1.1.0")
    assert troca == [f"perdido — estava no [Não lançado] da develop e sumiu: {N}"], \
        f"troca de bullet não empata: {troca}"
    H = "- Conserto H (#7)"
    assert conferir_sync(cl([N]), cl([], [H], "1.1.1"), cl([N], [H], "1.1.1"), "1.1.1") == [], "hotfix passa"
    conflito = cl([N], [A, B]).replace(f"{N}\n", f"<<<<<<< HEAD\n{N}\n=======\n>>>>>>> origin/main\n")
    marcas = conferir_sync(antes, main, conflito, "1.1.0")
    assert marcas == ["marcador de conflito no resultado, linha 6", "marcador de conflito no resultado, linha 9"], \
        f"conflito mal resolvido não passa, mesmo com os bullets no lugar: {marcas}"
    assert conferir_sync(cl([N]), main, "# Changelog\n", "1.1.0") == \
        [f"perdido — estava no [Não lançado] da develop e sumiu: {N}"], "resultado sem seções perde tudo"
    try:
        conferir_sync(antes, cl([]), cl([N], [A, B]), "1.1.0")
        raise AssertionError("main sem a versão lançada não pode passar")
    except SecaoAusente:
        pass
    print("selftest secao_changelog: OK (meio, rodapé, rótulo livre, vazio, ausente, `## ` encerra, "
          "comentário, sync por conjunto: correta, sem bullet, merge limpo, troca, hotfix, marcador)")
    return 0


def ler(caminho: str) -> str:
    p = Path(caminho)
    if not p.is_file():
        raise FileNotFoundError(f"arquivo ausente: {p}")
    return p.read_text(encoding="utf-8")


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return selftest()
    p = argparse.ArgumentParser(description="imprime o corpo de `## [rótulo]` do CHANGELOG ou confere a sync")
    p.add_argument("rotulo", nargs="?", help="versão X.Y.Z (com ou sem `v`) ou outro rótulo, como 'Não lançado'")
    p.add_argument("--changelog", default=CHANGELOG_PADRAO, help=f"caminho do arquivo (default {CHANGELOG_PADRAO})")
    p.add_argument("--sync", metavar="X.Y.Z", help="confere a sync main→develop da versão lançada")
    p.add_argument("--antes", help="CHANGELOG da develop antes da sync (com --sync)")
    p.add_argument("--main", help="CHANGELOG da main com a versão lançada (com --sync)")
    p.add_argument("--depois", help="CHANGELOG resultante do merge (com --sync)")
    args = p.parse_args(argv)
    try:
        if args.sync:
            if not (args.antes and args.main and args.depois):
                p.error("--sync exige --antes, --main e --depois")
            problemas = conferir_sync(ler(args.antes), ler(args.main), ler(args.depois), args.sync)
            for linha in problemas:
                print(linha, file=sys.stderr)
            if problemas:
                return 1
            print(f"sync v{args.sync}: nenhum bullet perdido, nenhum bullet fora do lançado")
            return 0
        if not args.rotulo:
            p.error("informe o rótulo ou --sync")
        rotulo = args.rotulo[1:] if re.fullmatch(r"v\d.*", args.rotulo) else args.rotulo
        sys.stdout.write(secao(ler(args.changelog), rotulo))
        return 0
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        return 2
    except SecaoAusente as e:
        print(str(e), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
