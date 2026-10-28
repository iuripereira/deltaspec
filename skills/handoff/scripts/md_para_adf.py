#!/usr/bin/env python3
"""Markdown → ADF (Atlassian Document Format) — dialeto de description do Jira.

`acli jira workitem create --description[-file]` aceita **só texto puro ou ADF**, nunca
Markdown: o corpo emitido por `corpo_ticket()` chegava literal no ticket (`**Local:**`,
crases, `---`) desde que a delta-017 trocou o `create-bulk` pelo create unitário. Este
módulo converte o subset que `corpo_ticket()` de fato emite — nada além, porque o resto
nunca aparece na projeção:

  bloco:  parágrafo · lista com `- ` · regra horizontal `---`
  inline: `**negrito**` · `` `código` `` · `_itálico_` · `[texto](url)`

Funções puras (`converter` não toca disco); o I/O fica no `main`. Uso direto:

    python3 md_para_adf.py corpo.md > corpo.adf.json

Na projeção quem chama é o `emitir_sh_acli` do `projecao.py`, que escreve o `.md` (fonte
legível, byte-idêntica ao DEBT.md) e o `.adf.json` ao lado — só o segundo vai para o
acli. Verificação: `python3 md_para_adf.py --selftest`.
"""
import json
import re
import sys

# Um só passe alternado — a ordem é o contrato: código primeiro (dentro de crase nada
# mais é interpretado), link antes de itálico (a URL pode conter `_`).
INLINE = re.compile(
    r"(?P<cerca>`+)(?P<code>.+?)(?P=cerca)"
    r"|\*\*(?P<strong>.+?)\*\*"
    r"|\[(?P<texto>[^\]]+)\]\((?P<href>[^)\s]+)\)"
    r"|(?<!\w)_(?P<em>[^_\n]+)_(?!\w)"
)
REGRA = re.compile(r"^\s*(?:-{3,}|\*{3,}|_{3,})\s*$")
ITEM_LISTA = re.compile(r"^\s*[-*]\s+(?P<texto>.*)$")


def _texto(valor: str, marks: list | None = None) -> dict | None:
    """Nó de texto ADF. Devolve None para string vazia — ADF recusa text node vazio."""
    if not valor:
        return None
    no = {"type": "text", "text": valor}
    if marks:
        no["marks"] = marks
    return no


def inline(linha: str, marks: list | None = None) -> list:
    """Converte a marcação inline de uma linha em nós de texto ADF com marks.

    Recursivo: o corpo de negrito/itálico/link é reprocessado e as marcas se acumulam
    no mesmo text node (ADF aceita lista de marks). Sem isso o aninhamento real que a
    projeção emite — `_Projeção de **T1** do `tasks.md`._` — chegaria cru dentro do
    itálico. Código é literal e não recursa: dentro de crase nada é interpretado.
    """
    marks = marks or []
    nos, cursor = [], 0
    for m in INLINE.finditer(linha):
        nos.append(_texto(linha[cursor:m.start()], marks))
        if m.group("code") is not None:
            # `code` é exclusiva no ADF: só coexiste com `link`. Combinada com em/strong
            # o Jira recusa o documento inteiro ("not valid ADF") — confirmado por
            # bissecção no SBX em 2026-08-07. Herança de formatação é descartada aqui.
            herdadas = [k for k in marks if k["type"] == "link"]
            # Cerca de N crases (`` `x` `` exibe crase literal): o par tem de casar pelo
            # mesmo comprimento, senão os pares desalinham e todo o resto da linha perde
            # a formatação **em silêncio** — como se viu no SBX-23. CommonMark manda tirar
            # um espaço de cada ponta quando ambas têm.
            literal = m.group("code")
            if literal.startswith(" ") and literal.endswith(" ") and literal.strip():
                literal = literal[1:-1]
            nos.append(_texto(literal, herdadas + [{"type": "code"}]))
        elif m.group("strong") is not None:
            nos += inline(m.group("strong"), marks + [{"type": "strong"}])
        elif m.group("href") is not None:
            nos += inline(m.group("texto"),
                          marks + [{"type": "link", "attrs": {"href": m.group("href")}}])
        else:
            nos += inline(m.group("em"), marks + [{"type": "em"}])
        cursor = m.end()
    nos.append(_texto(linha[cursor:], marks))
    return [n for n in nos if n]


def _paragrafo(linhas: list) -> dict | None:
    """Parágrafo com hardBreak entre as linhas — a quebra escrita foi deliberada."""
    conteudo = []
    for i, l in enumerate(linhas):
        if i:
            conteudo.append({"type": "hardBreak"})
        conteudo += inline(l)
    return {"type": "paragraph", "content": conteudo} if conteudo else None


def converter(markdown: str) -> dict:
    """Documento ADF a partir do markdown. Função pura — o chamador serializa."""
    blocos, buffer_par, buffer_lista = [], [], []

    def fecha_par():
        if buffer_par:
            no = _paragrafo(buffer_par)
            if no:
                blocos.append(no)
            buffer_par.clear()

    def fecha_lista():
        if buffer_lista:
            blocos.append({"type": "bulletList", "content": [
                {"type": "listItem", "content": [{"type": "paragraph", "content": inline(t)}]}
                for t in buffer_lista if inline(t)]})
            buffer_lista.clear()

    for linha in markdown.splitlines():
        if REGRA.match(linha):
            fecha_par(), fecha_lista()
            blocos.append({"type": "rule"})
        elif (m := ITEM_LISTA.match(linha)):
            fecha_par()
            buffer_lista.append(m.group("texto"))
        elif not linha.strip():
            fecha_par(), fecha_lista()
        else:
            fecha_lista()
            buffer_par.append(linha)
    fecha_par(), fecha_lista()

    # ADF recusa doc sem content; parágrafo vazio é o mínimo aceito.
    return {"type": "doc", "version": 1,
            "content": blocos or [{"type": "paragraph", "content": []}]}


def selftest() -> None:
    """Cobre o subset inteiro e as armadilhas que a execução real revelou."""
    # inline: cada marca, isolada
    assert inline("**oi**") == [{"type": "text", "text": "oi", "marks": [{"type": "strong"}]}]
    assert inline("`x.py`") == [{"type": "text", "text": "x.py", "marks": [{"type": "code"}]}]
    assert inline("_it_") == [{"type": "text", "text": "it", "marks": [{"type": "em"}]}]
    assert inline("[a](http://b)") == [
        {"type": "text", "text": "a",
         "marks": [{"type": "link", "attrs": {"href": "http://b"}}]}]

    # precedência: dentro de crase nada é interpretado
    assert inline("`**cru**`") == [
        {"type": "text", "text": "**cru**", "marks": [{"type": "code"}]}]

    # cerca dupla (`` `x` `` exibe a crase) não pode desalinhar os pares seguintes —
    # o desalinhamento é silencioso e comeu a formatação do resto da linha no SBX-23
    duplo = inline("a `` `c` `` e `d` fim")
    assert [n["text"] for n in duplo] == ["a ", "`c`", " e ", "d", " fim"], duplo
    assert duplo[1]["marks"] == duplo[3]["marks"] == [{"type": "code"}]

    # underscore de identificador não vira itálico (snake_case, nomes de arquivo)
    assert inline("corpo_ticket e doc_profile") == [
        {"type": "text", "text": "corpo_ticket e doc_profile"}]

    # texto misto preserva ordem e as partes sem marca
    assert inline("- **Local:** `x.py`")[0]["text"] == "- "

    # aninhamento real da projeção: negrito e código DENTRO de itálico acumulam marcas
    aninhado = inline("_Projeção de **T1** do `tasks.md`._")
    assert [n["text"] for n in aninhado] == ["Projeção de ", "T1", " do ", "tasks.md", "."]
    assert aninhado[0]["marks"] == [{"type": "em"}]
    assert aninhado[1]["marks"] == [{"type": "em"}, {"type": "strong"}]
    # `code` descarta em/strong herdados — o Jira recusa o doc inteiro se combinadas
    assert aninhado[3]["marks"] == [{"type": "code"}]
    assert inline("**a `b` c**")[1]["marks"] == [{"type": "code"}]
    # ...mas preserva `link`, a única que o ADF admite junto de code
    assert inline("[`x`](http://b)")[0]["marks"] == [
        {"type": "link", "attrs": {"href": "http://b"}}, {"type": "code"}]
    assert "**" not in json.dumps(aninhado), "marcação crua vazou para dentro do itálico"

    # link com texto marcado mantém href e a marca interna
    marcado = inline("[**a**](http://b)")
    assert marcado[0]["marks"] == [
        {"type": "link", "attrs": {"href": "http://b"}}, {"type": "strong"}]

    # blocos
    doc = converter("intro\n\n- **a:** 1\n- b\n\n---\n_fim_")
    tipos = [b["type"] for b in doc["content"]]
    assert tipos == ["paragraph", "bulletList", "rule", "paragraph"], tipos
    assert len(doc["content"][1]["content"]) == 2, "dois itens de lista"
    assert doc["content"][3]["content"][0]["marks"] == [{"type": "em"}]

    # regra horizontal só sozinha na linha — hífen no meio do texto é texto
    assert [b["type"] for b in converter("a - b")["content"]] == ["paragraph"]

    # linhas contíguas de parágrafo viram hardBreak, não blocos separados
    p = converter("l1\nl2")["content"][0]
    assert [n["type"] for n in p["content"]] == ["text", "hardBreak", "text"]

    # nenhum text node vazio em lugar nenhum — ADF recusa
    def sem_vazio(no):
        assert not (no.get("type") == "text" and not no.get("text")), "text vazio"
        for f in no.get("content", []):
            sem_vazio(f)
    sem_vazio(converter("**a****b**\n\n- \n\n`c`"))

    # documento vazio continua sendo ADF válido
    assert converter("")["content"] == [{"type": "paragraph", "content": []}]

    print("selftest md_para_adf: OK")


def main() -> None:
    if "--selftest" in sys.argv:
        return selftest()
    if len(sys.argv) != 2:
        sys.exit("uso: md_para_adf.py CORPO.md  (ou --selftest)")
    with open(sys.argv[1], encoding="utf-8") as fh:
        json.dump(converter(fh.read()), sys.stdout, ensure_ascii=False)
        print()


if __name__ == "__main__":
    main()
