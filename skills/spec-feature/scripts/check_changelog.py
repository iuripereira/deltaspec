#!/usr/bin/env python3
"""Gate determinístico do formato do CHANGELOG (delta-062).

A entrada de changelog é uma linha com a referência do PR que conta a história.
A narrativa — porquê, medição, renúncia, delta-NNN, DT-NNN — tem dono canônico
(o PR, a delta arquivada, a ADR) e a entrada apenas referencia (ADR-0035).

  C1  categoria — subseção fora das seis PT-BR (mecaniza o anti-padrão
      "changelog em inglês", que até aqui só existia como juízo do analyze)
  C2  tamanho — bullet acima de LIMITE_CHARS
  C3  referência — bullet sem '(#NNN)' no fim; omitido com --sem-pr
  C4  ordenação — '[Não lançado]' fora do topo, ou versões fora de ordem
      decrescente (defeito real medido num repo consumidor, cujo '[Não lançado]'
      ficou abaixo da [0.4.0] quando dois geradores escreveram no mesmo arquivo)
  C5  rodapé — heading '## [X.Y.Z]' sem definição '[X.Y.Z]:' e definição sem
      heading; omitido quando não há rodapé nenhum, que é a projeção derivada
      (o publica-dist.sh trunca o rodapé inteiro — R80) ou repo sem remoto

Uso: check_changelog.py [ARQUIVO|DIR]   (default: ./CHANGELOG.md)
     check_changelog.py --sem-pr [...]  repo cujo fluxo não passa por PR
     check_changelog.py --selftest
Exit 0 = formato ok (ou arquivo ausente) · 1 = corrigir · 2 = erro de uso.

O montar_changelog.py importa CATEGORIAS, LIMITE_CHARS e checar() daqui: o
fragmento de changelog.d/ é validado pelas MESMAS regras C1/C2/C3, sem
duplicação. Mudar a assinatura de checar() quebra o montador (delta-105).
"""
import re
import sys
from pathlib import Path

# Teto do bullet. Dono deste valor: a regra canônica do módulo release-triad
# (skills/projeto-init/references/canonical-rules.md); o deps.toml governa os
# espelhos, mesmo arranjo do pr-limiar-tamanho.
LIMITE_CHARS = 200

CATEGORIAS = ("Adicionado", "Mudado", "Corrigido", "Removido", "Obsoleto", "Segurança")

RE_NAO_LANCADO = re.compile(r"^## \[Não lançado\]")
RE_VERSAO = re.compile(r"^## \[(\d+)\.(\d+)\.(\d+)\]")
RE_CATEGORIA = re.compile(r"^### +(.+?) *$")
RE_BULLET = re.compile(r"^- +(.+)$")
RE_REFERENCIA = re.compile(r"\(#\d+(?:, *#\d+)*\)$")
RE_CERCA = re.compile(r"^ *```")
RE_DEF_LINK = re.compile(r"^\[[^\]]+\]: *\S")


# Definição de link do rodapé: `[X.Y.Z]: <url>`. O `[Não lançado]` fica de fora
# de propósito — não é versão lançada, e sua linha aponta commits, não uma tag.
RE_RODAPE = re.compile(r"^\[(\d+)\.(\d+)\.(\d+)\]:\s*\S")


def _e_continuacao(linha: str) -> bool:
    """Linha que pertence ao bullet anterior: indentada, ou prosa solta de um
    bullet hard-wrapped. Estrutura (heading, bullet novo, definição de link,
    cerca) encerra o bullet."""
    if not linha.strip():
        return False
    if linha[0].isspace():
        return True
    return not (linha.startswith(("#", "- ", "-\t")) or RE_CERCA.match(linha) or RE_DEF_LINK.match(linha))


def bullets(texto: str):
    """Extrai (linha_inicial, categoria, texto_completo) de cada bullet que vive
    sob uma categoria de uma seção de versão. Função pura sobre o texto."""
    linhas = texto.splitlines()
    achados, categoria, secao, cercado = [], None, False, False
    i = 0
    while i < len(linhas):
        linha = linhas[i]
        if RE_CERCA.match(linha):
            cercado = not cercado
            i += 1
            continue
        if cercado:
            i += 1
            continue
        if linha.startswith("## "):
            secao = bool(RE_NAO_LANCADO.match(linha) or RE_VERSAO.match(linha))
            categoria = None
        elif (m := RE_CATEGORIA.match(linha)):
            categoria = m.group(1)
        elif secao and categoria and (m := RE_BULLET.match(linha)):
            corpo, j = m.group(1), i + 1
            while j < len(linhas) and _e_continuacao(linhas[j]):
                corpo += " " + linhas[j].strip()
                j += 1
            achados.append((i + 1, categoria, corpo.strip()))
            i = j
            continue
        i += 1
    return achados


def categorias(texto: str):
    """(linha, nome) de cada '### ' que vive dentro de uma seção de versão."""
    achados, secao, cercado = [], False, False
    for n, linha in enumerate(texto.splitlines(), 1):
        if RE_CERCA.match(linha):
            cercado = not cercado
        elif cercado:
            continue
        elif linha.startswith("## "):
            secao = bool(RE_NAO_LANCADO.match(linha) or RE_VERSAO.match(linha))
        elif secao and (m := RE_CATEGORIA.match(linha)):
            achados.append((n, m.group(1)))
    return achados


def secoes(texto: str):
    """(linha, versão|None) de cada '## [...]'. None = '[Não lançado]'."""
    achados, cercado = [], False
    for n, linha in enumerate(texto.splitlines(), 1):
        if RE_CERCA.match(linha):
            cercado = not cercado
        elif cercado:
            continue
        elif RE_NAO_LANCADO.match(linha):
            achados.append((n, None))
        elif (m := RE_VERSAO.match(linha)):
            achados.append((n, tuple(int(g) for g in m.groups())))
    return achados


def rodape(texto: str):
    """(linha, versão) de cada definição `[X.Y.Z]:` fora de bloco cercado."""
    achados, cercado = [], False
    for n, linha in enumerate(texto.splitlines(), 1):
        if RE_CERCA.match(linha):
            cercado = not cercado
        elif cercado:
            continue
        elif (m := RE_RODAPE.match(linha)):
            achados.append((n, tuple(int(g) for g in m.groups())))
    return achados


def checar(texto: str, sem_pr: bool = False):
    """Devolve {check: [(linha, mensagem)]} — vazio em cada check que passou."""
    falhas = {"C1": [], "C2": [], "C3": [], "C4": [], "C5": []}

    for n, nome in categorias(texto):
        if nome not in CATEGORIAS:
            falhas["C1"].append((n, f"categoria '{nome}' fora das seis PT-BR"))

    for n, _cat, corpo in bullets(texto):
        if len(corpo) > LIMITE_CHARS:
            falhas["C2"].append((n, f"bullet com {len(corpo)} chars (limite {LIMITE_CHARS})"))
        if not sem_pr and not RE_REFERENCIA.search(corpo):
            falhas["C3"].append((n, "bullet sem referência '(#NNN)' no fim"))

    achadas = secoes(texto)
    for pos, (n, versao) in enumerate(achadas):
        if versao is None and pos != 0:
            falhas["C4"].append((n, "'[Não lançado]' não é a primeira seção"))
    lancadas = [(n, v) for n, v in achadas if v is not None]
    for (_, anterior), (n, atual) in zip(lancadas, lancadas[1:]):
        if atual >= anterior:
            v = ".".join(str(p) for p in atual)
            falhas["C4"].append((n, f"versão {v} não é menor que a anterior"))

    # C5 — correspondência heading <-> rodapé, nos dois sentidos. Mede estrutura,
    # nunca se a URL responde: o script não acessa a rede. Um heading sem rodapé foi
    # o defeito real da v1.38.0; um rodapé órfão sobrevive a uma versão renomeada.
    versoes = {v: n for n, v in lancadas}
    definidas = {v: n for n, v in rodape(texto)}
    # Sem rodapé nenhum o C5 se omite: é a projeção derivada, cujo rodapé o
    # publica-dist.sh trunca inteiro (R80) — o CI do derivado rodava este check
    # sobre o arquivo truncado e reprovava todas as versões (delta-089). Uma
    # linha faltando entre as demais segue sendo achado.
    for v, n in (sorted(versoes.items(), reverse=True) if definidas else ()):
        if v not in definidas:
            rot = ".".join(str(p) for p in v)
            falhas["C5"].append((n, f"versão {rot} sem definição '[{rot}]:' no rodapé"))
    for v, n in sorted(definidas.items(), reverse=True):
        if v not in versoes:
            rot = ".".join(str(p) for p in v)
            falhas["C5"].append((n, f"rodapé define '[{rot}]:' sem seção correspondente"))

    return falhas


ROTULOS = {
    "C1": "categorias PT-BR",
    "C2": f"tamanho do bullet (<= {LIMITE_CHARS})",
    "C3": "referência de PR",
    "C4": "ordenação das seções",
    "C5": "rodapé: uma definição por versão",
}


def main() -> None:
    args = sys.argv[1:]
    if "--selftest" in args:
        selftest()
        return
    sem_pr = "--sem-pr" in args
    resto = [a for a in args if not a.startswith("--")]
    if len(resto) > 1:
        print("uso: check_changelog.py [--sem-pr] [ARQUIVO|DIR]", file=sys.stderr)
        sys.exit(2)

    alvo = Path(resto[0]).resolve() if resto else Path.cwd() / "CHANGELOG.md"
    if alvo.is_dir():
        alvo = alvo / "CHANGELOG.md"
    if not alvo.is_file():
        # Degradação graciosa (RNF2): projeto sem changelog não é violação.
        print(f"AVISO: {alvo} ausente — gate do changelog omitido")
        return

    texto = alvo.read_text(encoding="utf-8")
    falhas = checar(texto, sem_pr)
    sem_rodape = not rodape(texto)
    if sem_pr:
        print("AVISO: --sem-pr — C3 (referência de PR) omitido")
    if sem_rodape:
        print("AVISO: sem rodapé — C5 (heading ↔ rodapé) omitido: projeção derivada ou repo sem remoto (R80)")
    for check, rotulo in ROTULOS.items():
        if (check == "C3" and sem_pr) or (check == "C5" and sem_rodape):
            continue
        itens = falhas[check]
        print(f"[{check}] {rotulo}: {'FAIL' if itens else 'OK'}")
        for n, msg in itens:
            print(f"  {alvo.name}:{n} {msg}")
    ruim = any(falhas[c] for c in falhas if not (c == "C3" and sem_pr))
    print(f"RESULTADO: {'FAIL' if ruim else 'PASS'}")
    sys.exit(1 if ruim else 0)


def selftest() -> None:
    limpo = """# Changelog

## [Não lançado]

### Adicionado
- Skills de efeito colateral viram manual-only (#227)

## [1.29.0] - 2026-08-13

### Corrigido
- **BREAKING** `STATE.md` renomeado para `HANDOFF.md` (#44, #45)

## [1.28.0] - 2026-08-12

### Mudado
- Duplicações deliberadas saem do comentário e entram no gate (#225)

[1.29.0]: https://github.com/iuripereira/deltaspec/releases/tag/v1.29.0
[1.28.0]: https://github.com/iuripereira/deltaspec/releases/tag/v1.28.0
"""
    assert not any(checar(limpo).values()), "fixture limpa não pode acusar nada"

    # C1 — categoria em inglês, o anti-padrão registrado na projeto-init.
    f = checar(limpo.replace("### Adicionado", "### Added"))
    assert len(f["C1"]) == 1 and "Added" in f["C1"][0][1], f["C1"]
    assert not f["C2"] and not f["C4"], "C1 não contamina os outros"

    # C1 não olha heading fora de seção de versão (preâmbulo do arquivo).
    assert not checar("# Changelog\n\n### Convenções\n\n## [1.0.0] - 2026-01-01\n")["C1"]

    # C5 — heading sem definição de rodapé: o defeito real que a v1.38.0 sofreu
    # sem nada acusar (a linha do rodapé sumiu e o gate seguiu verde).
    f = checar(limpo.replace("[1.28.0]: https://github.com/iuripereira/deltaspec/releases/tag/v1.28.0\n", ""))
    assert len(f["C5"]) == 1 and "1.28.0" in f["C5"][0][1], f["C5"]
    assert not f["C1"] and not f["C4"], "C5 não contamina os outros"

    # C5 — definição órfã: rodapé de versão que não tem seção no arquivo.
    f = checar(limpo + "[9.9.9]: https://example.invalid/releases/tag/v9.9.9\n")
    assert len(f["C5"]) == 1 and "9.9.9" in f["C5"][0][1], f["C5"]

    # C5 — '[Não lançado]' fica fora da correspondência: não é versão lançada.
    assert not checar(limpo)["C5"], "'[Não lançado]' sem rodapé não é achado"

    # C5 — sem rodapé nenhum o C5 se omite: é a projeção derivada, cujo rodapé o
    # publica-dist.sh trunca inteiro (R80), ou repo sem remoto. Uma linha a menos
    # entre as demais continua sendo achado (caso da v1.38.0, acima).
    sem_rodape = limpo.split("\n[1.29.0]:")[0] + "\n"
    assert "]: " not in sem_rodape, "fixture sem rodapé mal cortada"
    assert not checar(sem_rodape)["C5"], "CHANGELOG sem rodapé (projeção derivada) não é achado do C5"

    # C2 — bullet longo, incluindo o caso hard-wrapped (a continuação conta).
    longo = "x" * (LIMITE_CHARS - 10)
    f = checar(limpo.replace("- Skills de efeito colateral viram manual-only (#227)",
                             f"- {longo}\n  {longo} (#227)"))
    esperado = 2 * len(longo) + len(" ") + len(" (#227)")
    assert len(f["C2"]) == 1 and f"{esperado} chars" in f["C2"][0][1], f["C2"]
    assert not f["C3"], "referência na continuação ainda vale"

    # C2 mede o bullet inteiro, não a linha: exatamente no limite passa.
    assert not checar(limpo.replace("- Skills de efeito colateral viram manual-only (#227)",
                                    "- " + "y" * (LIMITE_CHARS - 7) + " (#9)"))["C2"]

    # C3 — sem referência, e a degradação por --sem-pr.
    sem_ref = limpo.replace("viram manual-only (#227)", "viram manual-only")
    assert len(checar(sem_ref)["C3"]) == 1, "bullet sem (#NNN) reprova"
    assert len(checar(limpo.replace("(#227)", "(#NNN)"))["C3"]) == 1, "placeholder (#NNN) reprova"
    assert not checar(sem_ref, sem_pr=True)["C3"], "--sem-pr omite o C3"
    assert not checar(limpo.replace("(#227)", "(#227, #228)"))["C3"], "vários PRs no mesmo parêntese"
    assert checar(limpo.replace("(#227)", "(#227) — e mais"))["C3"], "referência tem de fechar o bullet"

    # C4 — '[Não lançado]' fora do topo (o defeito real de um repo consumidor).
    fora = """# Changelog

## [0.4.0] - 2026-01-02

### Adicionado
- a (#1)

## [Não lançado]

### Adicionado
- b (#2)
"""
    assert len(checar(fora)["C4"]) == 1 and "não é a primeira" in checar(fora)["C4"][0][1]

    # C4 — versões fora de ordem decrescente, e a igual não passa por empate.
    assert len(checar(limpo.replace("## [1.28.0]", "## [1.30.0]"))["C4"]) == 1
    assert len(checar(limpo.replace("## [1.28.0]", "## [1.29.0]"))["C4"]) == 1
    assert not checar(limpo.replace("## [1.28.0]", "## [1.9.0]"))["C4"], "ordena por número, não por texto"

    # Bloco cercado é sintaxe citada, não conteúdo — o template documenta o formato.
    citado = limpo.replace("### Adicionado\n- Skills",
                           "### Adicionado\n\n```markdown\n### Added\n- " + "z" * 400 + "\n```\n\n- Skills")
    assert not any(checar(citado).values()), "bloco cercado é ignorado nos quatro checks"

    print(f"selftest: OK (C1 categoria · C2 tamanho e hard-wrap · C3 referência e --sem-pr · "
          f"C4 topo e ordem · C5 rodapé nos dois sentidos e omitido sem rodapé · cerca ignorada · limite {LIMITE_CHARS})")


if __name__ == "__main__":
    main()
