import re

# ponytail: âncora canônica do formato de item do framework
# Propriedade crítica: nunca mude sem atualizar todos os parsers (today: T2/tickets.py, T3/check_cycle.py)
ITEM = re.compile(r"^\s*-\s*\[([ xX])\]\s*((?:T|CT)\d+)\b")

# Paradas da continuação (constante nomeada): primeira ocorrência interrompe capturas
# Motivo: linha em branco separa blocos (novo parágrafo da prosa do plano), heading é nova seção,
# novo item é escopo fechado. Sobre-captura (comer prosa) é pior que sub-captura (perder detalhe formatado).
PARADAS = ["linha em branco", "novo item", "heading"]


def itens(texto: str, prefixo: str) -> list[dict]:
    """Itens `- [ ] T1 — ...` de tasks.md/test-plan.md, com continuação de linha.

    Dono canônico do formato (delta-033): quem precisa de item do ciclo chama aqui,
    nunca reimplementa a âncora — dois parsers divergentes é como o `dep:` sumiria
    da projeção de tickets em silêncio.

    Args:
        texto: bloco de markdown contendo itens de task.
        prefixo: filtro de ID ("T" para tasks, "CT" para casos de teste).

    Returns:
        Lista de dicts com chaves: id, feito (bool), texto (linha + continuações),
        linha (1-based), resto (trecho colado após ID na primeira linha).
    """
    linhas = texto.splitlines()
    out, atual = [], None
    for n, linha in enumerate(linhas, 1):
        m = ITEM.match(linha)
        if m:
            if atual:
                out.append(atual)
            atual = {
                "id": m.group(2),
                "feito": m.group(1).lower() == "x",
                "texto": linha,
                "linha": n,
                "resto": linha[m.end():].lstrip()
            }
        elif atual is not None:
            # Parada: linha em branco, heading, ou nenhuma linha em processamento
            if not linha.strip() or linha.lstrip().startswith("#"):
                out.append(atual)
                atual = None
            else:
                # Continuação: agregar com espaço
                atual["texto"] += " " + linha.strip()
    if atual:
        out.append(atual)
    # Filtro: apenas IDs que começam com prefixo e têm dígitos após ele
    return [
        i for i in out
        if i["id"].startswith(prefixo) and i["id"][len(prefixo):].isdigit()
    ]


def selftest():
    """Testes embutidos da lógica de parsing de itens."""
    txt = ("# Tasks — delta-900\n"
           "- [ ] T1 — ação curta · arquivos: a.py · cobre: R1 · verificação: pytest\n"
           "- [x] T2 (dep: T1) — ação longa que o autor quebrou\n"
           "      · arquivos: b.py · cobre: R2 · verificação: ruff\n"
           "\n"
           "Prosa depois da lista que NÃO pode entrar em nenhuma task.\n")
    its = itens(txt, "T")
    assert [i["id"] for i in its] == ["T1", "T2"], its
    assert its[0]["feito"] is False and its[1]["feito"] is True
    assert "verificação: ruff" in its[1]["texto"], "continuação precisa entrar no texto"
    assert "Prosa depois" not in its[1]["texto"], "linha em branco corta a continuação"
    assert its[1]["resto"].startswith("(dep: T1)"), its[1]["resto"]
    assert its[0]["linha"] == 2 and its[1]["linha"] == 3
    # heading corta a continuação
    txt2 = "- [ ] CT1 — caso · cobre: R1 · tipo: auto · verificação: x\n## Outra seção\nprosa\n"
    assert len(itens(txt2, "CT")) == 1 and "Outra seção" not in itens(txt2, "CT")[0]["texto"]
    # prefixo filtra
    assert itens(txt, "CT") == []
    print("selftest itens: OK (continuação, paradas, resto, prefixo)")


if __name__ == "__main__":
    import sys
    if "--selftest" in sys.argv:
        selftest()
    else:
        print("Uso: python3 itens.py --selftest")
