#!/usr/bin/env python3
"""Monta o CHANGELOG a partir dos fragmentos de changelog.d/ (delta-105).

Cada PR deixa um arquivo `changelog.d/<slug>.<categoria>.md` com UMA linha: o
bullet, sem o `- ` inicial. O montador acrescenta tudo ao `## [Não lançado]` —
mescla, nunca troca: o bullet que já estava lá fica — e apaga os fragmentos.
Nomes distintos = zero conflito entre PRs vivas, que é a dor que este mecanismo
existe para matar.

O formato do bullet é o mesmo da ADR-0035 e quem o valida é o check_changelog.py
— aqui não há regra de forma duplicada.

Uso: montar_changelog.py [--dir changelog.d] [--changelog CHANGELOG.md]
     montar_changelog.py --preencher-pr 186 [--dir changelog.d]
     montar_changelog.py --verificar        # gate: valida fragmentos, não escreve
     montar_changelog.py --liberar 1.2.0 [--changelog CHANGELOG.md]   # corte da release (delta-117)
     montar_changelog.py --selftest
Exit 0 = ok · 1 = corrigir (inclui, no --liberar, versão não maior que a última
lançada) · 2 = erro de uso (versão fora do SemVer, argumento ausente, arquivo
inexistente).
"""
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_changelog import (  # noqa: E402
    CATEGORIAS, LIMITE_CHARS, RE_CERCA, RE_DEF_LINK, RE_REFERENCIA, bullets, categorias, checar, rodape, secoes)

# Sufixo ASCII do arquivo -> categoria PT-BR. ASCII de propósito: 'Segurança' e
# 'Obsoleto' viram nome de arquivo em qualquer sistema, sem acento no caminho.
CATEGORIA_POR_SUFIXO = {
    "adicionado": "Adicionado", "mudado": "Mudado", "corrigido": "Corrigido",
    "removido": "Removido", "obsoleto": "Obsoleto", "seguranca": "Segurança",
}
RE_FRAGMENTO = re.compile(r"^(?P<slug>.+)\.(?P<cat>" + "|".join(CATEGORIA_POR_SUFIXO) + r")\.md$")
# Comentário HTML não é conteúdo do CHANGELOG: o template do projeto-init traz
# um rodapé de exemplo dentro de `<!-- -->`, e contá-lo como rodapé duplicava a
# definição ou reprovava a primeira release (S6). A máscara troca o comentário
# pelos seus '\n', então a linha N do texto visível é a linha N do real —
# análise num, edição no outro.
# ponytail: '<!--' dentro de bloco cercado não é distinguido; um exemplo cercado
# com comentário aberto mascara até o próximo '-->'. Tratar se aparecer.
RE_COMENTARIO = re.compile(r"<!--.*?-->", re.DOTALL)


class ErroDeUso(ValueError):
    """Argumento inválido — exit 2 na CLI."""


class Corrigir(ValueError):
    """Estado do CHANGELOG impede a operação — exit 1 na CLI."""


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


# ── Leitura por linha ─────────────────────────────────────────────────────────
# Tudo que localiza seção, subseção e bullet passa pelo secoes()/categorias()/
# bullets() do check_changelog, que ignoram blocos cercados (S11). Regex sobre o
# texto inteiro achava o '## [Não lançado]' de um exemplo cercado no preâmbulo.

def _linhas(texto: str) -> list[str]:
    """Linhas com o fim preservado. Arquivo sem newline final ganha um: a última
    linha sem '\\n' ficava fora da seção e o corte dizia 'vazio' (S7)."""
    return (texto if texto.endswith("\n") else texto + "\n").splitlines(keepends=True)


def _visivel(linhas: list[str]) -> str:
    return RE_COMENTARIO.sub(lambda m: "\n" * m.group().count("\n"), "".join(linhas))


def _limites(visivel: str, qual):
    """(início, fim) em índice 0 da primeira seção `## [qual]` (None = Não
    lançado) — fim exclusivo: a próxima seção ou o fim do arquivo."""
    achadas = secoes(visivel)
    for k, (n, versao) in enumerate(achadas):
        if versao == qual:
            fim = achadas[k + 1][0] - 1 if k + 1 < len(achadas) else len(visivel.splitlines())
            return n - 1, fim
    return None


def _bullets(visivel: str, limites=None) -> Counter:
    """Multiconjunto (categoria, texto) dos bullets — do arquivo, ou da seção."""
    ini, fim = limites or (-1, float("inf"))
    return Counter((cat, corpo) for n, cat, corpo in bullets(visivel) if ini < n - 1 < fim)


def _fim_subsecao(vis: list[str], inicio: int, limite: int) -> int:
    """Índice logo após a última linha não vazia da subseção `###` em `inicio`.
    Encerra a subseção: outro heading, cerca ou definição de link (rodapé)."""
    fim = inicio + 1
    for j in range(inicio + 1, limite):
        if vis[j].startswith("#") or RE_CERCA.match(vis[j]) or RE_DEF_LINK.match(vis[j]):
            break
        if vis[j].strip():
            fim = j + 1
    return fim


def _ordem(categoria: str) -> int:
    return CATEGORIAS.index(categoria) if categoria in CATEGORIAS else len(CATEGORIAS)


def mesclar(texto: str, frags):
    """Devolve (texto_novo, bullets_que_já_estavam) com os fragmentos acrescentados
    ao `## [Não lançado]`. Cada bullet entra no fim da subseção da sua categoria;
    categoria ausente nasce na posição canônica, e categoria sem fragmento não
    vira subseção vazia. Nada sai da seção: trocá-la pelo bloco dos fragmentos
    apagava o bullet devolvido pelo sync (S1). Versão lançada e rodapé não são
    tocados — a licença da ADR-0035 é para reprojeção deliberada."""
    linhas = _linhas(texto)
    visivel = _visivel(linhas)
    limites = _limites(visivel, None)
    if limites is None:
        raise Corrigir("não achei a seção '## [Não lançado]' — crie-a antes de montar.")
    ini, fim = limites
    vis = visivel.splitlines()
    subs = [(n - 1, nome) for n, nome in categorias(visivel) if ini < n - 1 < fim]
    insercoes = {}
    for categoria in CATEGORIAS:
        novos = [f"- {t}\n" for c, t, _ in frags if c == categoria]
        if not novos:
            continue
        mesma = [i for i, nome in subs if nome == categoria]
        depois = [i for i, nome in subs if _ordem(nome) > _ordem(categoria)]
        if mesma:
            pos, bloco = _fim_subsecao(vis, mesma[-1], fim), novos
        elif depois:
            pos, bloco = depois[0], [f"### {categoria}\n", *novos, "\n"]
        else:
            pos = _fim_subsecao(vis, subs[-1][0], fim) if subs else ini + 1
            bloco = ["\n", f"### {categoria}\n", *novos]
        # mesma posição: a ordem canônica do laço decide quem vem antes
        insercoes.setdefault(pos, []).extend(bloco)
    for pos in sorted(insercoes, reverse=True):
        linhas[pos:pos] = insercoes[pos]

    # Invariante: a seção depois = seção antes + fragmentos, e o resto do arquivo
    # igual. O esperado passa pelo mesmo bullets(), para comparar igual com igual.
    esperado = _bullets("## [Não lançado]\n" + "".join(f"### {c}\n- {t}\n" for c, t, _ in frags))
    depois_vis = _visivel(linhas)
    secao_antes = _bullets(visivel, limites)
    if (_bullets(depois_vis, _limites(depois_vis, None)) != secao_antes + esperado
            or _bullets(depois_vis) != _bullets(visivel) + esperado):
        raise Corrigir("invariante violada na montagem — a seção não ficou com os bullets de antes mais "
                       "os fragmentos (fragmento com cerca ou heading solto?); nada gravado.")
    return "".join(linhas), sum(secao_antes.values())


def aplicar(changelog: Path, frags) -> int:
    """I/O do mesclar(): lê, mescla, grava. Devolve os bullets preservados."""
    novo, preservados = mesclar(changelog.read_text(encoding="utf-8"), frags)
    changelog.write_text(novo, encoding="utf-8")
    return preservados


# --liberar X.Y.Z (delta-117): o corte da release renomeia o `## [Não lançado]`
# para `## [X.Y.Z] - AAAA-MM-DD` e abre um `[Não lançado]` novo em cima. É a
# receita que hoje vive de cabeça em cada CLAUDE.md consumidor; aqui ela vira
# função pura com invariante (nenhum bullet nasce nem some no corte).
# SemVer 2.0.0: sem zero à esquerda; fullmatch porque o `$` casa antes de um
# '\n' final e a versão com newline passava (S10).
RE_SEMVER = re.compile(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)")
# Linha do rodapé que aponta os commits ainda não lançados; dela sai a base da
# URL (o `<base>/compare/`) para a definição da versão nova.
RE_RODAPE_NAO_LANCADO = re.compile(r"^\[Não lançado\]: *(?P<base>\S+?)/compare/v\d+\.\d+\.\d+\.\.\.HEAD *$")
# Checks do check_changelog que o corte confere no resultado. C2/C3 ficam de
# fora de propósito: passivo pré-existente de consumidor não é problema do corte.
CHECKS_DO_CORTE = ("C4", "C5")


def _rotulo(versao) -> str:
    return ".".join(str(p) for p in versao)


def _linha_rodape(vis: list[str]):
    """Índice da linha `[Não lançado]: …/compare/vA.B.C...HEAD`, fora de cerca."""
    cercado = False
    for i, linha in enumerate(vis):
        if RE_CERCA.match(linha):
            cercado = not cercado
        elif not cercado and RE_RODAPE_NAO_LANCADO.match(linha):
            return i
    return None


def liberar(texto: str, versao: str, hoje: date):
    """Devolve (texto_novo, relatorio) com o `## [Não lançado]` liberado como
    `## [X.Y.Z] - AAAA-MM-DD`. Não toca arquivo — quem grava é o main()."""
    m = RE_SEMVER.fullmatch(versao)
    if not m:
        raise ErroDeUso(f"versão {versao!r} não é SemVer X.Y.Z.")
    nova = tuple(int(g) for g in m.groups())
    linhas = _linhas(texto)
    visivel = _visivel(linhas)
    achadas = secoes(visivel)
    if not achadas or achadas[0][1] is not None:
        raise Corrigir("'## [Não lançado]' não é a primeira seção — nada a liberar.")
    limites = _limites(visivel, None)
    liberados = _bullets(visivel, limites)
    # Vazio antes da comparação de versão: rodar o corte duas vezes com a mesma
    # versão diz "nada a liberar", que é a causa, e não "versão repetida".
    if not liberados:
        raise Corrigir("'## [Não lançado]' vazio — nada a liberar.")
    lancadas = [v for _n, v in achadas if v is not None]
    maior = max(lancadas) if lancadas else None
    if maior is not None and nova <= maior:
        raise Corrigir(f"versão {versao} não é maior que a última lançada ({_rotulo(maior)}).")

    relatorio = []
    linhas[limites[0]:limites[0] + 1] = ["## [Não lançado]\n", "\n", f"## [{versao}] - {hoje.isoformat()}\n"]
    visivel_novo = _visivel(linhas)
    i = _linha_rodape(visivel_novo.splitlines())
    if i is not None:
        base = RE_RODAPE_NAO_LANCADO.match(visivel_novo.splitlines()[i]).group("base")
        substituta = [f"[Não lançado]: {base}/compare/v{versao}...HEAD\n"]
        if nova in {v for _n, v in rodape(visivel_novo)}:
            relatorio.append(f"rodapé: '[{versao}]:' já definido — mantido, sem duplicar.")
        else:
            definicao = (f"[{versao}]: {base}/compare/v{_rotulo(maior)}...v{versao}" if maior
                         else f"[{versao}]: {base}/releases/tag/v{versao}")
            substituta.append(definicao + "\n")
            relatorio.append(f"rodapé: + {definicao}")
        linhas[i:i + 1] = substituta
    else:
        relatorio.append("AVISO: sem linha '[Não lançado]: .../compare/vA.B.C...HEAD' no rodapé (fora de "
                         f"comentário HTML) — definição '[{versao}]:' não criada; escreva-a à mão se o repo tem remoto.")

    # Invariante: os bullets do arquivo são os mesmos, os do [Não lançado] de
    # antes são os da seção nova, e o [Não lançado] novo nasce vazio.
    depois = _visivel(linhas)
    if (_bullets(depois) != _bullets(visivel) or _bullets(depois, _limites(depois, nova)) != liberados
            or _bullets(depois, _limites(depois, None))):
        raise Corrigir(f"invariante violada: os bullets do [Não lançado] não chegaram íntegros a [{versao}] "
                       "— corte abortado, nada gravado.")
    falhas = checar(depois)
    problemas = [f"[{c}] linha {n}: {msg}" for c in CHECKS_DO_CORTE for n, msg in falhas[c]]
    if problemas:
        raise Corrigir("resultado do corte reprova no check_changelog:\n  " + "\n  ".join(problemas))
    relatorio.insert(0, f"[Não lançado] liberado como [{versao}] - {hoje.isoformat()} "
                        f"({sum(liberados.values())} bullet(s) preservados).")
    return "".join(linhas), relatorio


def _falha(chamada, erro) -> str:
    """Mensagem do erro esperado; AssertionError se a chamada não falhou."""
    try:
        chamada()
    except erro as e:
        return str(e)
    raise AssertionError(f"devia falhar com {erro.__name__}")


def selftest() -> None:
    import subprocess
    import tempfile
    x = Path("x")  # caminho de fragmento sem arquivo: mesclar() não lê o disco
    hoje = date(2026, 9, 10)
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
        # seção vazia: cada categoria nasce na ordem canônica, sem subseção vazia;
        # versão lançada e rodapé intocados, [Não lançado] segue o primeiro (C4)
        texto, preservados = mesclar(
            "# Changelog\n\nprosa\n\n## [Não lançado]\n\n## [1.0.0] - 2026-01-01\n\n"
            "### Adicionado\n- Coisa antiga (#1)\n\n[1.0.0]: http://x/v1.0.0\n", frags)
        assert preservados == 0, preservados
        assert ("## [Não lançado]\n\n### Adicionado\n- Regras nativas no config (#186)\n\n"
                "### Corrigido\n- Ids de vigência corrigidos (#186)\n\n## [1.0.0]") in texto, texto
        assert "### Mudado" not in texto and texto.count("## [Não lançado]") == 1, texto
        assert "- Coisa antiga (#1)" in texto and "[1.0.0]: http://x/v1.0.0" in texto, texto

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

    # S1 — estado misto (bullet devolvido pelo sync + fragmento): mescla, não troca.
    base = "# Changelog\n\nprosa\n\n## [Não lançado]\n\n### Corrigido\n- Voltou do sync (#40)\n\n"
    base += "## [1.0.0] - 2026-01-01\n\n### Adicionado\n- Coisa antiga (#1)\n\n"
    rodape_ok = "[Não lançado]: http://x/compare/v1.0.0...HEAD\n[1.0.0]: http://x/releases/tag/v1.0.0\n"
    texto, preservados = mesclar(base + rodape_ok, [("Adicionado", "Nova (#41)", x), ("Corrigido", "Conserto (#42)", x)])
    assert preservados == 1, preservados
    assert ("## [Não lançado]\n\n### Adicionado\n- Nova (#41)\n\n### Corrigido\n- Voltou do sync (#40)\n"
            "- Conserto (#42)\n\n## [1.0.0]") in texto, texto
    novo, relatorio = liberar(texto, "1.1.0", hoje)
    assert "## [1.1.0] - 2026-09-10\n\n### Adicionado\n- Nova (#41)\n\n### Corrigido\n- Voltou do sync (#40)\n" in novo, novo
    assert "(3 bullet(s) preservados)" in relatorio[0], relatorio  # o relatório conta a seção, e é verdade
    # invariante nomeada, nunca assert: cerca solta no fragmento engoliria o resto do arquivo
    msg = _falha(lambda: mesclar(base + rodape_ok, [("Adicionado", "Quebra (#43)\n```", x)]), Corrigir)
    assert "invariante" in msg and "nada gravado" in msg, msg
    msg = _falha(lambda: mesclar("# C\n\n## [1.0.0] - 2026-01-01\n", [("Adicionado", "a (#1)", x)]), Corrigir)
    assert "não achei" in msg, msg

    # --liberar (delta-117): caso feliz, com rodapé no formato de compare.
    novo, relatorio = liberar(base + rodape_ok, "1.1.0", hoje)
    assert "## [Não lançado]\n\n## [1.1.0] - 2026-09-10\n\n### Corrigido\n- Voltou do sync (#40)\n" in novo, novo
    assert novo.count("## [Não lançado]") == 1 and novo.index("## [Não lançado]") < novo.index("## [1.1.0]"), novo
    assert "[Não lançado]: http://x/compare/v1.1.0...HEAD\n[1.1.0]: http://x/compare/v1.0.0...v1.1.0\n[1.0.0]:" in novo, novo
    assert not any(checar(novo)[c] for c in CHECKS_DO_CORTE), checar(novo)
    assert any("rodapé: +" in r for r in relatorio) and "(1 bullet(s) preservados)" in relatorio[0], relatorio
    # invariante: nenhum bullet nasce nem some no corte, em nenhuma seção
    assert len(bullets(base + rodape_ok)) == len(bullets(novo)) == 2, bullets(novo)
    # D2: vazio e versão ≤ última → corrigir (exit 1); fora do SemVer → erro de uso (exit 2)
    vazio = base.replace("### Corrigido\n- Voltou do sync (#40)\n\n", "", 1) + rodape_ok
    for texto, versao, erro in ((vazio, "1.1.0", Corrigir), (base + rodape_ok, "1.0.0", Corrigir),
                                (base + rodape_ok, "0.9.9", Corrigir), (base + rodape_ok, "v1.1.0", ErroDeUso),
                                (base + rodape_ok, "1.1.0\n", ErroDeUso), (base + rodape_ok, "01.1.0", ErroDeUso)):
        _falha(lambda: liberar(texto, versao, hoje), erro)
    # definição da versão já no rodapé: não duplica
    pre = rodape_ok.replace("[1.0.0]:", "[1.1.0]: http://x/compare/v1.0.0...v1.1.0\n[1.0.0]:")
    novo, relatorio = liberar(base + pre, "1.1.0", hoje)
    assert novo.count("[1.1.0]:") == 1 and any("já definido" in r for r in relatorio), (novo, relatorio)
    # sem rodapé: avisa e não inventa definição — C5 se omite sem rodapé nenhum
    novo, relatorio = liberar(base, "1.1.0", hoje)
    assert "[1.1.0]:" not in novo and any("AVISO" in r for r in relatorio), (novo, relatorio)
    # primeira release (repo sem versão lançada): definição vira link de tag
    primeira = "# Changelog\n\n## [Não lançado]\n\n### Adicionado\n- a (#1)\n\n[Não lançado]: http://x/compare/v0.0.0...HEAD\n"
    novo, _ = liberar(primeira, "0.1.0", hoje)
    assert "[0.1.0]: http://x/releases/tag/v0.1.0" in novo, novo

    # S6 — o molde do projeto-init: subseções vazias e rodapé de exemplo DENTRO de
    # comentário HTML. O comentário não é rodapé: nada é escrito nele, e a
    # primeira release pode ser qualquer versão.
    modelo = ("# Changelog\n\nprosa\n\n## [Não lançado]\n\n### Adicionado\n### Mudado\n### Corrigido\n\n"
              "<!--\nNo release: renomeie a seção.\n-->\n\n<!-- Rodapé: um link por versão.\n"
              "[Não lançado]: https://github.com/U/R/compare/v0.1.0...HEAD\n"
              "[0.1.0]: https://github.com/U/R/releases/tag/v0.1.0 -->\n")
    texto, _ = mesclar(modelo, [("Adicionado", "a (#1)", x), ("Corrigido", "c (#2)", x)])
    assert "### Adicionado\n- a (#1)\n### Mudado\n### Corrigido\n- c (#2)\n\n<!--\nNo release" in texto, texto
    for versao in ("1.0.0", "0.1.0"):
        novo, relatorio = liberar(texto, versao, hoje)
        assert novo.endswith(modelo[modelo.index("<!-- Rodapé"):]), novo  # comentário intocado
        assert novo.count("[0.1.0]:") == 1 and any("AVISO" in r for r in relatorio), (versao, novo, relatorio)

    # S7 — sem newline no fim do arquivo: a última linha é da seção.
    sem_nl = "# C\n\n## [Não lançado]\n\n### Adicionado\n- a (#1)"
    novo, _ = liberar(sem_nl, "0.1.0", hoje)
    assert novo.endswith("## [0.1.0] - 2026-09-10\n\n### Adicionado\n- a (#1)\n"), novo
    texto, _ = mesclar(sem_nl, [("Adicionado", "b (#2)", x)])
    assert texto.endswith("- a (#1)\n- b (#2)\n"), texto

    # S11 — '## [Não lançado]' de exemplo dentro de cerca no preâmbulo: ignorado.
    cercado = ("# C\n\n```\n## [Não lançado]\n### Adicionado\n- exemplo (#9)\n```\n\n"
               "## [Não lançado]\n\n### Adicionado\n- real (#2)\n")
    novo, relatorio = liberar(cercado, "0.1.0", hoje)
    assert novo.startswith(cercado[:cercado.index("```\n\n") + 5]), novo  # cerca intocada
    assert "## [0.1.0] - 2026-09-10\n\n### Adicionado\n- real (#2)\n" in novo and "(1 bullet" in relatorio[0], novo
    texto, _ = mesclar(cercado, [("Adicionado", "novo (#3)", x)])
    assert texto.endswith("- real (#2)\n- novo (#3)\n") and "- exemplo (#9)\n```" in texto, texto

    # A CLI recusa argumento desconhecido ANTES de tocar arquivo: o default
    # escreve o CHANGELOG e apaga fragmentos, e --help/typo não podem cair nele
    # (defeito real: '--help' aplicou o montador no repo em 2026-09-02).
    r = subprocess.run([sys.executable, __file__, "--nao-existe"], capture_output=True, text=True)
    assert r.returncode == 2 and "desconhecido" in r.stderr, (r.returncode, r.stderr)
    r = subprocess.run([sys.executable, __file__, "--dir"], capture_output=True, text=True)
    assert r.returncode == 2 and "exige um valor" in r.stderr, (r.returncode, r.stderr)
    r = subprocess.run([sys.executable, __file__, "--help"], capture_output=True, text=True)
    assert r.returncode == 0 and "Uso:" in r.stdout, (r.returncode, r.stdout)
    with tempfile.TemporaryDirectory() as d:
        # o passo 3 da criar-release, de ponta a ponta: montar e depois --liberar
        # sobre um [Não lançado] que já tem bullet (S1). Nenhum bullet some.
        raiz = Path(d)
        cl, frags_dir = raiz / "CHANGELOG.md", raiz / "changelog.d"
        frags_dir.mkdir()
        (frags_dir / "nova.adicionado.md").write_text("Nova (#41)\n", encoding="utf-8")
        cl.write_text(base + rodape_ok, encoding="utf-8")
        r = subprocess.run([sys.executable, __file__, "--dir", str(frags_dir), "--changelog", str(cl)],
                           capture_output=True, text=True)
        assert r.returncode == 0 and "1 bullet(s) que já estavam" in r.stdout, (r.returncode, r.stdout, r.stderr)
        assert not list(frags_dir.glob("*.md")), "fragmento apagado depois de montar"
        # --liberar roda sem changelog.d/ (o corte não depende de fragmento) e a
        # segunda chamada acha o [Não lançado] vazio → exit 1.
        cmd = [sys.executable, __file__, "--liberar", "1.1.0", "--changelog", str(cl), "--dir", str(raiz / "nao-existe")]
        r = subprocess.run(cmd, capture_output=True, text=True)
        assert r.returncode == 0 and "(2 bullet(s) preservados)" in r.stdout, (r.returncode, r.stdout, r.stderr)
        assert "- Voltou do sync (#40)" in cl.read_text(encoding="utf-8").split("## [1.1.0]")[1].split("## [1.0.0]")[0]
        r = subprocess.run(cmd, capture_output=True, text=True)
        assert r.returncode == 1 and "nada a liberar" in r.stderr, (r.returncode, r.stderr)
        r = subprocess.run(cmd[:2] + ["--liberar", "x.y.z", "--changelog", str(cl)], capture_output=True, text=True)
        assert r.returncode == 2 and "SemVer" in r.stderr, (r.returncode, r.stderr)
        # D2 na CLI: versão ≤ última lançada é 1, o mesmo código do versao_corte.py
        cl.write_text(base + rodape_ok, encoding="utf-8")
        r = subprocess.run(cmd[:2] + ["--liberar", "1.0.0", "--changelog", str(cl)], capture_output=True, text=True)
        assert r.returncode == 1 and "não é maior" in r.stderr, (r.returncode, r.stderr)
    print("selftest OK")


# Flags que recebem valor e flags sem valor. Argumento fora destas listas aborta
# com erro de uso ANTES de qualquer leitura: o default deste script escreve o
# CHANGELOG e apaga fragmentos, e um typo (ou --help) não pode cair nele.
COM_VALOR = ("--dir", "--changelog", "--preencher-pr", "--liberar")
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

    # --liberar vem ANTES da saída precoce de changelog.d/: o corte trabalha só
    # sobre o CHANGELOG, e repo sem fragmentos também corta release.
    if "--liberar" in args:
        changelog = Path(opcao("--changelog", "CHANGELOG.md"))
        if not changelog.is_file():
            print(f"erro de uso: {changelog} não existe — nada a liberar.", file=sys.stderr)
            sys.exit(2)
        try:
            novo, relatorio = liberar(changelog.read_text(encoding="utf-8"), opcao("--liberar", ""), date.today())
        except ErroDeUso as e:
            print(f"erro de uso: {e}", file=sys.stderr)
            sys.exit(2)
        except Corrigir as e:
            print(f"{changelog}: {e}", file=sys.stderr)
            sys.exit(1)
        changelog.write_text(novo, encoding="utf-8")
        for linha in relatorio:
            print(linha)
        return

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
    changelog = Path(opcao("--changelog", "CHANGELOG.md"))
    try:
        preservados = aplicar(changelog, frags)
    except Corrigir as e:
        print(f"{changelog}: {e}", file=sys.stderr)
        sys.exit(1)
    for _c, _t, caminho in frags:
        caminho.unlink()
    print(f"[Não lançado] montado com {len(frags)} entrada(s) e {preservados} bullet(s) que já estavam "
          "lá preservados; fragmentos removidos.")


if __name__ == "__main__":
    main()
