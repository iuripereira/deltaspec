#!/usr/bin/env python3
"""Gera o fonte `.excalidraw` a partir de um esboço enxuto de elementos.

O `.excalidraw` é o único formato da tabela categoria→ferramenta (ADR-0009) que não
é texto livre: cada elemento carrega ~25 campos obrigatórios, dos quais a maioria é
constante. Este módulo preenche os constantes e expõe só o que varia — é o
equivalente stdlib do `convertToExcalidrawElements` do pacote npm, descartado na
delta-068 porque não carrega em Node headless e não é publicável pelo allowlist.

Uso:
    python3 gera_excalidraw.py < esboco.json > diagrama.excalidraw
    python3 gera_excalidraw.py --selftest

O esboço é uma lista JSON de objetos com as chaves que variam:
    [{"tipo": "rectangle", "x": 0, "y": 0, "largura": 200, "altura": 80,
      "texto": "Publicar"}]
"""

import json
import sys

# Envelope do arquivo. `version` é a do formato, não a do Excalidraw.
FORMATO_VERSAO = 2
FONTE = "https://excalidraw.com"
FUNDO_PADRAO = "#ffffff"

# Constantes do elemento: valem para todo elemento emitido e nunca variam por
# esboço. Mudam só se o formato do Excalidraw mudar (contrato de terceiro —
# risco registrado na spec da delta-068).
TRACO_PADRAO = "#1e1e1e"
PREENCHIMENTO_PADRAO = "transparent"
ESTILO_PREENCHIMENTO = "solid"      # hachure | cross-hatch | solid
ESTILO_TRACO = "solid"              # solid | dashed | dotted
LARGURA_TRACO = 2
RUGOSIDADE = 1
OPACIDADE = 100
ARREDONDAMENTO_ADAPTATIVO = 3       # RoundnessType.ADAPTIVE_RADIUS

# Constantes do elemento de texto.
FONTE_TAMANHO = 20
FONTE_FAMILIA = 1                   # 1 = Virgil (mão livre), 2 = Helvetica
ALTURA_LINHA = 1.25
LARGURA_CARACTERE = 0.55            # razão largura/altura da Virgil, para medir o texto

# Tipos que recebem os campos extras de texto.
TIPOS_TEXTO = ("text",)
# Tipos que aceitam borda arredondada.
TIPOS_ARREDONDADOS = ("rectangle", "diamond")


def elemento(tipo, x, y, largura, altura, texto=None, cor=None, fundo=None):
    """Monta um elemento completo a partir do que varia. Função pura."""
    el = {
        "id": "",                   # carimbado por `documento`
        "type": tipo,
        "x": x,
        "y": y,
        "width": largura,
        "height": altura,
        "strokeColor": cor or TRACO_PADRAO,
        "backgroundColor": fundo or PREENCHIMENTO_PADRAO,
        "fillStyle": ESTILO_PREENCHIMENTO,
        "strokeWidth": LARGURA_TRACO,
        "strokeStyle": ESTILO_TRACO,
        "roundness": {"type": ARREDONDAMENTO_ADAPTATIVO} if tipo in TIPOS_ARREDONDADOS else None,
        "roughness": RUGOSIDADE,
        "opacity": OPACIDADE,
        "angle": 0,
        "seed": 0,                  # carimbado por `documento`
        "version": 1,
        "versionNonce": 0,          # carimbado por `documento`
        "index": None,
        "isDeleted": False,
        "groupIds": [],
        "frameId": None,
        "boundElements": None,
        "updated": 1,
        "link": None,
        "locked": False,
    }
    if tipo in TIPOS_TEXTO:
        conteudo = texto or ""
        el.update({
            "text": conteudo,
            "originalText": conteudo,
            "fontSize": FONTE_TAMANHO,
            "fontFamily": FONTE_FAMILIA,
            "textAlign": "left",
            "verticalAlign": "top",
            "containerId": None,
            "lineHeight": ALTURA_LINHA,
            "autoResize": True,
        })
    return el


def largura_do_texto(conteudo):
    """Largura aproximada de uma linha de texto, em pixels."""
    return round(len(conteudo) * FONTE_TAMANHO * LARGURA_CARACTERE)


def documento(elementos):
    """Envelopa os elementos e carimba os campos que precisam ser únicos.

    O carimbo é derivado da posição, não de `random`: o mesmo esboço gera sempre
    o mesmo arquivo, o que mantém o diff legível e o selftest determinístico.
    """
    carimbados = []
    for i, el in enumerate(elementos):
        copia = dict(el)
        copia["id"] = f"el{i}"
        copia["seed"] = (i + 1) * 1000
        copia["versionNonce"] = (i + 1) * 2000
        carimbados.append(copia)
    return {
        "type": "excalidraw",
        "version": FORMATO_VERSAO,
        "source": FONTE,
        "elements": carimbados,
        "appState": {"gridSize": None, "viewBackgroundColor": FUNDO_PADRAO},
        "files": {},
    }


def do_esboco(esboco):
    """Converte a lista enxuta do esboço em documento pronto. Função pura."""
    return documento([
        elemento(
            item["tipo"],
            item["x"],
            item["y"],
            item.get("largura", 0),
            item.get("altura", 0),
            texto=item.get("texto"),
            cor=item.get("cor"),
            fundo=item.get("fundo"),
        )
        for item in esboco
    ])


# Campos que todo elemento emitido precisa carregar; o selftest verifica.
CAMPOS_OBRIGATORIOS = (
    "id", "type", "x", "y", "width", "height", "strokeColor", "backgroundColor",
    "fillStyle", "strokeWidth", "strokeStyle", "roundness", "roughness", "opacity",
    "angle", "seed", "version", "versionNonce", "index", "isDeleted", "groupIds",
    "frameId", "boundElements", "updated", "link", "locked",
)
CAMPOS_TEXTO = ("text", "originalText", "fontSize", "fontFamily", "lineHeight")


def selftest():
    esboco = [
        {"tipo": "rectangle", "x": 0, "y": 0, "largura": 200, "altura": 80},
        {"tipo": "text", "x": 20, "y": 30, "largura": 160, "altura": 25, "texto": "Publicar"},
        {"tipo": "ellipse", "x": 300, "y": 0, "largura": 120, "altura": 120},
    ]
    doc = do_esboco(esboco)

    assert doc["type"] == "excalidraw", "envelope sem type"
    assert doc["version"] == FORMATO_VERSAO, "versão do formato errada"
    assert len(doc["elements"]) == len(esboco), "perdeu elemento no caminho"

    ids = set()
    for el in doc["elements"]:
        faltando = [c for c in CAMPOS_OBRIGATORIOS if c not in el]
        assert not faltando, f"elemento {el.get('type')} sem campos: {faltando}"
        assert el["id"] not in ids, "id repetido entre elementos"
        ids.add(el["id"])
        assert el["seed"] != 0 and el["versionNonce"] != 0, "seed/nonce não carimbados"
        if el["type"] in TIPOS_TEXTO:
            faltando = [c for c in CAMPOS_TEXTO if c not in el]
            assert not faltando, f"texto sem campos: {faltando}"
            assert el["text"] == el["originalText"], "text e originalText divergem"

    retorno = json.loads(json.dumps(doc))
    assert retorno == doc, "documento não sobrevive ao round-trip JSON"

    assert do_esboco(esboco) == doc, "geração não é determinística"

    retangulo = doc["elements"][0]
    assert retangulo["roundness"] == {"type": ARREDONDAMENTO_ADAPTATIVO}, "retângulo sem arredondamento"
    assert doc["elements"][2]["roundness"] is None, "elipse não leva arredondamento"

    assert largura_do_texto("") == 0, "texto vazio mede zero"
    assert largura_do_texto("abc") > 0, "texto medido como zero"

    print("selftest: OK")


def main():
    if "--selftest" in sys.argv:
        selftest()
        return
    esboco = json.load(sys.stdin)
    json.dump(do_esboco(esboco), sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
