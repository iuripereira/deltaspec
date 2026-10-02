#!/usr/bin/env python3
"""Parsers puros do que a camada de evidência traz: fila de débitos e recortes por janela.

REGRAS — este texto é o dono; a SKILL.md aponta para cá e não as reescreve.

**A ordem da fila de débitos é copiada, nunca recalculada.** O registro de débitos já
ordena por precedência — impedimento com data antes de trilha, trilha antes de score — e
reproduzir essa regra aqui criaria uma segunda fonte que diverge no dia em que a de lá
mudar. Este módulo lê a tabela, preserva a ordem e corta o topo.

Linha fora do formato é ignorada, e repositório cuja leitura aborta vira **linha de
alerta**: débito que some em silêncio é pior que débito mal formatado.
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
import unicodedata

LIMITE_DEBITO = 5
TRILHA = "trilha"
RE_LINHA = re.compile(r"^\|\s*\d+\s*\|\s*(DT-\d+)\s*\|\s*([\d.]+)\s*\|([^|]*)\|([^|]*)\|([^|]*)\|$")
RE_OVERRIDE = re.compile(r"!(\w+)\((\d{4}-\d{2}-\d{2})\)")
RE_DT = re.compile(r"(DT-\d+)")
RE_DATA = re.compile(r"(\d{4}-\d{2}-\d{2})")
RE_HIGIENE = re.compile(r"^\s*\[(G\d+)\]\s+.*?\s+—\s+(.+)$")
# `_` fica de fora de propósito: underscore de identificador (snake_case, DATA_DICTIONARY)
# é muito mais comum que ênfase por underscore, e rebalancear comia o título inteiro.
PARES = ("`", "**")


def parse_fila_debito(texto):
    """Itens na ordem impressa pelo registro. Linha fora do formato e aviso são ignorados."""
    itens = []
    for linha in (texto or "").splitlines():
        m = RE_LINHA.match(linha.strip())
        if not m:
            continue
        ident, score, fila, titulo, _marcas = m.groups()
        ov = RE_OVERRIDE.search(fila)
        itens.append({"id": ident, "score": float(score), "fila": fila.strip(),
                      "override": (ov.group(1), ov.group(2)) if ov else None,
                      "trilha": TRILHA in fila, "titulo": titulo.strip()})
    return itens


def resumir_debito(itens, cunhados=(), quitados=(), limite=LIMITE_DEBITO):
    """Topo na ordem que o registro deu, mais o delta desde a última sessão."""
    return {"prioritarios": itens[:limite], "total": len(itens),
            "cunhados": sorted(set(cunhados)), "quitados": sorted(set(quitados))}


def truncar_titulo(texto, limite):
    """Corta em palavra e fecha marcação que ficou órfã — título cortado no meio de uma
    crase quebra a tabela de quem lê o painel em markdown."""
    texto = (texto or "").strip()
    if len(texto) <= limite:
        return texto
    corte = texto[:limite].rsplit(" ", 1)[0].rstrip(" ,;:—-")
    for marca in PARES:
        if corte.count(marca) % 2:
            corte = corte.rsplit(marca, 1)[0].rstrip(" ,;:—-")
    return corte + "…"


def ids_de(linhas):
    """Identificadores de débito citados em caminhos de arquivo, sem repetir."""
    achados = []
    for linha in linhas or []:
        m = RE_DT.search(str(linha))
        if m and m.group(1) not in achados:
            achados.append(m.group(1))
    return sorted(achados)


def render_debito(secoes, limite_titulo=70):
    """Uma linha por repositório; abaixo dela o topo da fila e o delta da janela."""
    out = ["## Débito"]
    for s in secoes:
        if s.get("erro"):
            out.append(f"- **{s['repo']}** · ⚠ {s['erro']}")
            continue
        delta = []
        if s["cunhados"]:
            delta.append(f"+{len(s['cunhados'])} cunhado(s): {', '.join(s['cunhados'])}")
        if s["quitados"]:
            delta.append(f"−{len(s['quitados'])} quitado(s): {', '.join(s['quitados'])}")
        resumo = f"{s['total']} pontuável(is)" + (f" · {' · '.join(delta)}" if delta else "")
        out.append(f"- **{s['repo']}** · {resumo}")
        for it in s["prioritarios"]:
            if it["override"]:
                tipo, prazo = it["override"]
                marca = f"⚠ impedimento {tipo}, prazo {prazo}"
            elif it["trilha"]:
                marca = "trilha"
            else:
                marca = f"score {it['score']:.0f}"
            out.append(f"  - {it['id']} · {marca} — {truncar_titulo(it['titulo'], limite_titulo)}")
    return out


def contar_sessoes(timestamps, desde, fuso_horas):
    """Registros de sessão na janela. O horário vem em UTC e a janela é local: sem o
    deslocamento, tudo que roda de madrugada cai no dia errado."""
    n, corte = 0, dt.datetime.combine(desde, dt.time.min)
    for ts in timestamps or []:
        try:
            quando = dt.datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        except ValueError:
            continue
        local = quando.replace(tzinfo=None) + dt.timedelta(hours=fuso_horas)
        if local >= corte:
            n += 1
    return n


def pendencias_desde(linhas, desde):
    """Linhas do ledger com data igual ou posterior ao corte.

    O formato do arquivo é de quem o mantém; a única coisa assumida aqui é a data em ISO
    na linha — tolerante de propósito, porque ledger é captura, não registro estruturado.
    """
    novas = []
    for linha in linhas or []:
        m = RE_DATA.search(str(linha))
        if m and m.group(1) >= desde.isoformat():
            novas.append(str(linha).strip())
    return novas


def alerta_de_ferramenta(pedido, encontrada, o_que):
    """Ferramenta PEDIDA na config e ausente vira alerta; não pedida, silêncio.

    Os dois casos parecem o mesmo de dentro do código — nenhuma saída — e são opostos para
    quem lê: um é escolha do usuário, o outro é a escolha dele não tendo sido cumprida.
    """
    if pedido and not encontrada:
        return f"{o_que} pedida na config, mas a ferramenta não foi encontrada"
    return ""


def parse_higiene(texto):
    """{repo: [códigos de check]} a partir do relatório da auditoria.

    A chave é (check, repositório), não a linha inteira: o texto do achado carrega contagens
    e hashes que mudam a cada commit, e comparar linha crua acusaria novidade todo dia.
    """
    achados = {}
    for linha in (texto or "").splitlines():
        m = RE_HIGIENE.match(linha)
        if not m:
            continue
        check, alvo = m.groups()
        repo = re.split(r"[,:]", alvo, 1)[0].strip().split("/")[0]
        if repo and check not in achados.setdefault(repo, []):
            achados[repo].append(check)
    return {r: sorted(c) for r, c in achados.items()}


def render_retrospectiva(handoffs, licoes, ledger, higiene, erro_higiene="", base_higiene=0):
    """As linhas que a rotina de retrospectiva produzia, agora derivadas. Vazio = nada a dizer.

    `base_higiene` > 0 é a estreia: sem execução anterior, TUDO seria novidade, e despejar o
    estado inicial como se fosse mudança da noite treina o leitor a ignorar a seção.
    """
    out = []
    for repo, arquivos in sorted(handoffs.items()):
        for a in arquivos:
            out.append(f"- handoff: {repo}/{a.rsplit('/', 1)[-1]}")
    for repo, n in sorted(licoes.items()):
        out.append(f"- lições: {repo} · {n} alteração(ões)")
    if ledger:
        out.append(f"- ledger: {len(ledger)} pendência(s) nova(s) fora de projeto")
    if erro_higiene:
        out.append(f"- higiene: ⚠ {erro_higiene}")
    elif base_higiene:
        out.append(f"- higiene: linha de base registrada ({base_higiene} repositório(s) com achado); "
                   "da próxima sessão em diante só o que mudar aparece aqui")
    else:
        for repo, checks in sorted((higiene or {}).get("novos", {}).items()):
            out.append(f"- higiene: {repo} · {', '.join(checks)} passou(aram) a acusar")
        for repo, checks in sorted((higiene or {}).get("sumidos", {}).items()):
            out.append(f"- higiene: {repo} · {', '.join(checks)} deixou(aram) de acusar")
    return ["### Também desde então"] + out if out else []


def delta_higiene(antes, agora):
    """(novos, sumidos) por repositório — só o que mudou desde a execução anterior."""
    antes, agora = antes or {}, agora or {}
    novos = {r: [a for a in achados if a not in antes.get(r, [])]
             for r, achados in agora.items()}
    sumidos = {r: [a for a in achados if a not in agora.get(r, [])]
               for r, achados in antes.items()}
    return {"novos": {r: v for r, v in novos.items() if v},
            "sumidos": {r: v for r, v in sumidos.items() if v}}


def sem_acento(texto):
    return "".join(c for c in unicodedata.normalize("NFKD", texto or "") if not unicodedata.combining(c))


# ---------- selftest ----------

def selftest():
    tabela = (
        "# Fila de dívida — 3 item(ns) pontuável(is)\n"
        "\n"
        "| # | ID | Score | Fila | Título | Marcas |\n"
        "|---|---|---|---|---|---|\n"
        "| 1 | DT-022 | 9.00 | P9·J9·Pr9 · !contract(2026-10-02) | Obrigação com prazo | **override contract** |\n"
        "> aviso que não é linha de tabela\n"
        "| 2 | DT-083 | 81.00 | P1·J9·Pr9 | Insumo do cliente parado | churn sugere Pr1 |\n"
        "| 3 | DT-018 | 9.00 | P9·J3·Pr9 · trilha | Item de trilha planejada | — |\n"
        "lixo solto\n"
    )
    itens = parse_fila_debito(tabela)
    # a ordem é a do registro: impedimento com data vem antes de score maior
    assert [i["id"] for i in itens] == ["DT-022", "DT-083", "DT-018"]
    assert itens[0]["override"] == ("contract", "2026-10-02") and itens[0]["score"] == 9.0
    assert itens[1]["override"] is None and itens[1]["score"] == 81.0
    assert itens[2]["trilha"] and not itens[1]["trilha"]
    assert parse_fila_debito("") == [] and parse_fila_debito(None) == []

    r = resumir_debito(itens, cunhados=["DT-090", "DT-090"], quitados=["DT-007"], limite=2)
    assert [i["id"] for i in r["prioritarios"]] == ["DT-022", "DT-083"] and r["total"] == 3
    assert r["cunhados"] == ["DT-090"] and r["quitados"] == ["DT-007"]  # repetido não duplica

    # render: impedimento nomeia o prazo; erro vira linha, nunca omissão
    linhas = render_debito([{"repo": "APP", **r}])
    assert "- **APP** · 3 pontuável(is) · +1 cunhado(s): DT-090 · −1 quitado(s): DT-007" in linhas
    assert "  - DT-022 · ⚠ impedimento contract, prazo 2026-10-02 — Obrigação com prazo" in linhas
    assert "  - DT-083 · score 81 — Insumo do cliente parado" in linhas
    assert render_debito([{"repo": "GEST", "erro": "registro abortou"}]) == ["## Débito", "- **GEST** · ⚠ registro abortou"]

    # truncagem: corta em palavra e não deixa crase órfã
    assert truncar_titulo("usa `npm run build` para tudo", 14) == "usa…"
    assert truncar_titulo("titulo curto", 40) == "titulo curto"
    assert truncar_titulo("uma frase bem comprida que precisa caber", 20).endswith("…")
    assert "`" not in truncar_titulo("abre `codigo aqui e continua", 12)
    # underscore de identificador não é marcação: o título sobrevive ao corte
    assert truncar_titulo("DATA_DICTIONARY tem campos a confirmar e 3 entidades sem Steward", 40) \
        == "DATA_DICTIONARY tem campos a confirmar…"

    # ids a partir de caminhos de arquivo
    assert ids_de(["debts/ativos/DEBT_DT-092-x.md", "debts/ativos/DEBT_DT-091-y.md", "README.md"]) == ["DT-091", "DT-092"]
    assert ids_de([]) == [] and ids_de(None) == []

    # sessões: a virada do dia é local, não UTC
    assert contar_sessoes(["2026-09-17T02:00:00Z", "2026-09-17T12:00:00Z"], dt.date(2026, 9, 17), -3) == 1
    assert contar_sessoes(["2026-09-17T02:00:00Z"], dt.date(2026, 9, 16), -3) == 1
    assert contar_sessoes(["não é data"], dt.date(2026, 9, 17), -3) == 0

    # ledger: data na linha manda; o resto do formato é de quem mantém o arquivo
    ledger = ["- [ ] 2026-09-17 — cobrar planilha — origem: app",
              "- [ ] 2026-09-10 — item velho — origem: gest",
              "## cabeçalho sem data", ""]
    assert pendencias_desde(ledger, dt.date(2026, 9, 16)) == ["- [ ] 2026-09-17 — cobrar planilha — origem: app"]
    assert pendencias_desde(ledger, dt.date(2026, 9, 1))[1].startswith("- [ ] 2026-09-10")
    assert pendencias_desde([], dt.date(2026, 9, 1)) == [] and pendencias_desde(None, dt.date(2026, 9, 1)) == []

    # ferramenta ausente: silêncio só quando o silêncio foi pedido
    assert alerta_de_ferramenta(True, False, "auditoria de higiene") \
        == "auditoria de higiene pedida na config, mas a ferramenta não foi encontrada"
    assert alerta_de_ferramenta(False, False, "auditoria de higiene") == ""  # não pediu, não reclama
    assert alerta_de_ferramenta(True, True, "auditoria de higiene") == ""

    # higiene: a chave é (check, repo), para contagem que muda todo dia não virar novidade
    relatorio = ("[G1] 1 repositório(s) afetado(s):\n"
                 "  [G1] segredo versionado (x) — app/debts/ativos/DEBT_DT-046-y.md:15\n"
                 "[G5] 2 repositório(s) afetado(s):\n"
                 "  [G5] 3 de 20 commits acima do limiar (500 linhas) — gest, pior: f7dff89 com 6689\n"
                 "  [G5] 1 de 20 commits acima do limiar (500 linhas) — app, pior: abc1234 com 900\n")
    assert parse_higiene(relatorio) == {"app": ["G1", "G5"], "gest": ["G5"]}
    assert parse_higiene("") == {} and parse_higiene(None) == {}
    # a mesma auditoria com números diferentes não muda a chave
    assert parse_higiene(relatorio.replace("3 de 20", "9 de 20").replace("6689", "7777")) == parse_higiene(relatorio)

    # render da retrospectiva
    linhas = render_retrospectiva({"APP": ["x/.claude/handoffs/H_a_2026_09_17.md"]}, {"GEST": 2},
                                  ["- [ ] 2026-09-17 cobrar planilha"],
                                  {"novos": {"DOT": ["G3"]}, "sumidos": {}})
    assert linhas[0] == "### Também desde então"
    assert "- handoff: APP/H_a_2026_09_17.md" in linhas and "- lições: GEST · 2 alteração(ões)" in linhas
    assert "- ledger: 1 pendência(s) nova(s) fora de projeto" in linhas
    assert "- higiene: DOT · G3 passou(aram) a acusar" in linhas
    assert render_retrospectiva({}, {}, [], {"novos": {}, "sumidos": {}}) == []  # nada a dizer, nada impresso
    # estreia: o estado inicial não é despejado como se fosse mudança da noite
    base = " ".join(render_retrospectiva({}, {}, [], {}, base_higiene=7))
    assert "linha de base registrada (7 repositório(s)" in base and "passou(aram)" not in base
    assert "⚠ auditoria abortou" in " ".join(render_retrospectiva({}, {}, [], {}, "auditoria abortou"))

    # higiene: só o delta
    d = delta_higiene({"a": ["G3"]}, {"a": ["G3"], "b": ["G7"]})
    assert d == {"novos": {"b": ["G7"]}, "sumidos": {}}
    assert delta_higiene({"a": ["G3"]}, {})["sumidos"] == {"a": ["G3"]}
    assert delta_higiene({}, {}) == {"novos": {}, "sumidos": {}}

    assert sem_acento("Ação e coração") == "Acao e coracao"
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true", help="valida as funções puras deste módulo")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
