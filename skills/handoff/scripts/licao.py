#!/usr/bin/env python3
"""Registro de lições do deltaspec — cadastro determinístico e índice gerado (ADR-0042).

Molde do débito (ADR-0030/0031): uma lição é **um arquivo** em `debts/licoes/`,
com frontmatter validado, cadastrada só por comando, nunca à mão. `debts/LICOES.md`
é projeção gerada (`indice`), nunca fonte. A lição é imutável depois do commit —
reincidência é lição nova que cita a antiga (`reincide:`), nunca edição da velha.

Este script **não acessa a rede**. Reaproveita, em vez de reimplementar, o que já
existe no `debito.py` (mesmo diretório): parsing de frontmatter, reescrita de
links, slug e leitura de IDs de débito — um módulo por responsabilidade
(CLAUDE.md, Clean Code), não um subcomando enfiado num script de 2000+ linhas.

  nova     cadastra uma lição em debts/licoes/, já validada (o ID sai da união)
  indice   regenera o LICOES.md como índice das lições (projeção, ADR-0042)

Uso: licao.py nova [ROOT] --descricao T --familia F --deteccao D --prevencao P
                       --origem O [--gerou DT-NNN[,DT-MMM]] [--reincide L-NNN[,L-MMM]]
                       [--data AAAA-MM-DD] [--registro R] [--corpo-arquivo ARQ]
     licao.py indice [ROOT] [--verificar]
     licao.py --selftest
Exit 0 = sem erro · 1 = registro inválido ou índice divergente · 2 = erro de uso.
"""
import argparse
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path, PurePosixPath

from debito import (ATALHO_GH, CAMPO, DATA, DESCRICAO_LIMITE, FM_CHAVE, FRONTMATTER,
                    VAZIO, die, git, ids_em_disco, reescreve_links, slug)

DIR_LICOES = "debts/licoes"
INDICE_LICOES = "debts/LICOES.md"

# Nome e ID — mesma forma do débito, prefixo L em vez de DT.
NOME_LICAO = re.compile(r"^LICAO_(L-\d+)-[a-z0-9][a-z0-9-]*\.md$")
ID_L = re.compile(r"^L-(\d+)$")
TITULO_LICAO = re.compile(r"^#\s+\[(L-\d+)\]\s+-\s+(.*?)\s*$")

# Frontmatter flat, todas as chaves obrigatórias (R1, delta-107) — `gerou`/`reincide`
# aceitam "—" como lista vazia explícita, então a ausência da CHAVE é o erro, não o
# valor vazio (por isso a checagem de obrigatoriedade usa `in fm`, não VAZIO).
FM_OBRIGATORIAS_LICAO = ("id", "data", "descricao", "familia", "deteccao", "prevencao",
                        "origem", "gerou", "reincide")

# Os dois enums são valor governado (deps.toml, delta-107) — os comentários ao lado
# são o espelho que o C1 lê (mesmo arranjo do LIMITE_CHARS): o valor real é a tupla,
# mas o C1 casa texto-fonte, e o pipe só existe nos docs — não reescreva um sem o outro.
DETECCOES = ("gate", "revisao", "humano", "sorte")  # gate|revisao|humano|sorte
PREVENCOES = ("gate", "debito", "disciplina")  # gate|debito|disciplina

FAMILIA = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LISTA_DT = re.compile(r"^DT-\d+(?:,\s*DT-\d+)*$")
LISTA_L = re.compile(r"^L-\d+(?:,\s*L-\d+)*$")

# Ordem fixa das quatro seções do corpo (R1) — a posição de cada uma no texto é
# o que secoes_em_ordem confere; seção citada em prosa fora do heading não conta
# (mesma âncora de início de linha do CAMPO, lição de 2026-07-28).
SECOES = ("## O que aconteceu", "## Causa", "## Desfecho", "## Prevenção")

# Acima disso o cadastro AVISA, nunca recusa — narrativa longa fica no handoff/PR,
# linkada em vez de duplicada aqui (regra de ouro).
LICAO_TETO_PALAVRAS = 250


def secoes_em_ordem(corpo: str) -> list:
    """Erros: seção ausente, ou presente fora da ordem canônica de SECOES."""
    erros = []
    pos_anterior, nome_anterior = -1, None
    for nome in SECOES:
        m = re.search(rf"^{re.escape(nome)}\s*$", corpo, re.M)
        if not m:
            erros.append(f"seção '{nome}' ausente")
            continue
        if m.start() <= pos_anterior:
            erros.append(f"seção '{nome}' fora de ordem (esperada depois de '{nome_anterior}')")
        else:
            pos_anterior, nome_anterior = m.start(), nome
    return erros


def _normaliza_lista(valor: str) -> str:
    """"—"/vazio vira "—"; senão, forma canônica "X, Y" (determinismo do render)."""
    if not valor or valor.strip() in VAZIO:
        return "—"
    partes = [p.strip() for p in valor.split(",") if p.strip()]
    return ", ".join(partes) if partes else "—"


def parse_licao(caminho: Path):
    """(item, erros estruturais) de um arquivo de debts/licoes/.

    Sempre devolve item quando o nome e o frontmatter são ao menos lidos — mesmo
    com erros — para o `indice` poder decidir excluir e reportar (R3); só devolve
    None quando o arquivo é ilegível de saída (nome fora do padrão, sem frontmatter).
    """
    nome = caminho.name
    m_nome = NOME_LICAO.match(nome)
    if not m_nome:
        return None, [f"{nome}: nome fora do padrão LICAO_L-NNN-<topico>.md em {DIR_LICOES}/"]
    ident = m_nome.group(1)
    texto = caminho.read_text(encoding="utf-8")
    m_fm = FRONTMATTER.match(texto)
    if not m_fm:
        return None, [f"{ident}: frontmatter ausente ou sem fechamento (--- … ---) em {nome}"]

    erros = []
    fm = dict(FM_CHAVE.findall(m_fm.group(1)))
    for linha_fm in m_fm.group(1).splitlines():
        if linha_fm.strip() and not FM_CHAVE.match(linha_fm):
            chave = linha_fm.split(":", 1)[0].strip()
            erros.append(f"{ident}: chave de frontmatter inválida ({chave!r}) — use ASCII "
                         f"minúsculo sem acento")
    for chave in FM_OBRIGATORIAS_LICAO:
        if chave not in fm:
            erros.append(f"{ident}: frontmatter sem a chave obrigatória '{chave}'")

    if fm.get("id") and fm["id"] != ident:
        erros.append(f"{ident}: frontmatter declara id '{fm['id']}' ≠ nome do arquivo — "
                     f"o nome é a fonte; iguale os dois")
    if "data" in fm and not DATA.fullmatch(fm.get("data", "")):
        erros.append(f"{ident}: 'data' malformada — esperado AAAA-MM-DD")
    if "descricao" in fm and fm.get("descricao", "") in VAZIO:
        erros.append(f"{ident}: 'descricao' vazia — é a regra que fica, resumida em uma linha")
    if "familia" in fm and not FAMILIA.fullmatch(fm.get("familia", "")):
        erros.append(f"{ident}: 'familia' fora do kebab-case (letras/dígitos minúsculos e hífen)")
    if "deteccao" in fm and fm.get("deteccao") not in DETECCOES:
        erros.append(f"{ident}: 'deteccao' {fm.get('deteccao')!r} fora do conjunto "
                     f"{'|'.join(DETECCOES)}")
    if "prevencao" in fm and fm.get("prevencao") not in PREVENCOES:
        erros.append(f"{ident}: 'prevencao' {fm.get('prevencao')!r} fora do conjunto "
                     f"{'|'.join(PREVENCOES)}")
    if "origem" in fm and fm.get("origem", "") in VAZIO:
        erros.append(f"{ident}: 'origem' vazia — onde o incidente ocorreu")

    gerou, reincide = [], []
    if "gerou" in fm:
        valor = fm["gerou"]
        if valor in VAZIO:
            gerou = []
        elif LISTA_DT.fullmatch(valor):
            gerou = [x.strip() for x in valor.split(",")]
        else:
            erros.append(f"{ident}: 'gerou' malformado — esperado DT-NNN[, DT-MMM] ou —")
    if "reincide" in fm:
        valor = fm["reincide"]
        if valor in VAZIO:
            reincide = []
        elif LISTA_L.fullmatch(valor):
            reincide = [x.strip() for x in valor.split(",")]
        else:
            erros.append(f"{ident}: 'reincide' malformado — esperado L-NNN[, L-MMM] ou —")

    item = {"id": ident, "data": fm.get("data", ""), "descricao": fm.get("descricao", ""),
            "familia": fm.get("familia", ""), "deteccao": fm.get("deteccao", ""),
            "prevencao": fm.get("prevencao", ""), "origem": fm.get("origem", ""),
            "gerou": gerou, "reincide": reincide, "_arquivo": f"{DIR_LICOES}/{nome}"}

    corpo = texto[m_fm.end():]
    primeira, _, depois = corpo.lstrip("\n").partition("\n")
    m_t = TITULO_LICAO.match(primeira)
    if not m_t:
        erros.append(f"{ident}: primeira linha do corpo deve ser o título "
                     f"`# [{ident}] - <descricao>` (R1)")
    else:
        corpo = depois
        if m_t.group(1) != ident or m_t.group(2) != item["descricao"]:
            erros.append(f"{ident}: título H1 divergente do frontmatter — espelhe "
                         f"`# [{ident}] - {item['descricao']}`")

    erros += [f"{ident}: {e}" for e in secoes_em_ordem(corpo)]
    campos_corpo = {c.strip().lower(): v.strip() for c, v in CAMPO.findall(corpo)}
    if "origem" not in campos_corpo:
        erros.append(f"{ident}: corpo sem o campo '- **Origem:**'")
    if "registro" in campos_corpo:
        item["registro"] = campos_corpo["registro"]
    return item, erros


def ids_licoes_em_disco(root: Path) -> set:
    """IDs de lição já cadastradas, lidos do **nome** dos arquivos de debts/licoes/."""
    pasta = root / DIR_LICOES
    if not pasta.is_dir():
        return set()
    return {m.group(1) for p in pasta.glob("*.md") if (m := NOME_LICAO.match(p.name))}


def ids_licoes_em_refs_remotas(root: Path) -> set:
    """IDs de lição em branches remotas já buscadas — sem tocar a rede (mesmo desenho
    de `debito.ids_em_refs_remotas`, cegueira conhecida do DT-071 documentada lá)."""
    refs = git(root, "for-each-ref", "--format=%(refname)", "refs/remotes/")
    if not refs:
        return set()
    ids = set()
    for ref in refs.split():
        saida = git(root, "ls-tree", "-r", "--name-only", ref, DIR_LICOES)
        ids |= {m.group(1) for linha in (saida or "").splitlines()
                if (m := NOME_LICAO.match(PurePosixPath(linha).name))}
    return ids


def proximo_id_licao(ids: set) -> str:
    """Maior ID da união + 1, com 3 dígitos — numeração global, nunca reutilizada."""
    numeros = [int(m.group(1)) for i in ids if (m := ID_L.match(i))]
    return f"L-{max(numeros, default=0) + 1:03d}"


def validar_licao(item: dict, ids_dt: set, ids_l: set) -> list:
    """Erros de referência cruzada — dependem de sets externos, por isso separados
    do parse (que só lê o próprio arquivo)."""
    erros = []
    ident = item.get("id", "?")
    if len(item.get("descricao", "")) > DESCRICAO_LIMITE:
        erros.append(f"{ident}: descricao com {len(item['descricao'])} caracteres, "
                     f"acima do teto de {DESCRICAO_LIMITE}")
    for dt in item.get("gerou", []):
        if dt not in ids_dt:
            erros.append(f"{ident}: 'gerou' cita {dt}, que não existe em debts/ativos/ "
                         f"nem debts/_archive/")
    for l in item.get("reincide", []):
        if l not in ids_l:
            erros.append(f"{ident}: 'reincide' cita {l}, que não existe em debts/licoes/")
    if item.get("prevencao") == "debito" and not item.get("gerou"):
        erros.append(f"{ident}: prevencao 'debito' exige ao menos um DT em 'gerou'")
    return erros


def render_licao(campos: dict, corpo: str) -> tuple:
    """(nome_base, conteúdo) do arquivo novo — links do corpo e da Origem/Registro
    reescritos para 2 níveis (mesma profundidade de debts/ativos/)."""
    ident, titulo = campos["id"], campos["descricao"]
    fm_linhas = ["---"] + [f"{chave}: {campos[chave]}" for chave in FM_OBRIGATORIAS_LICAO] + ["---"]
    corpo_reescrito = reescreve_links(corpo.strip())
    campos_extra = [f"- **Origem:** {reescreve_links(campos['origem'])}"]
    if campos.get("registro"):
        campos_extra.append(f"- **Registro:** {reescreve_links(campos['registro'])}")
    conteudo = ("\n".join(fm_linhas) + "\n\n" + f"# [{ident}] - {titulo}\n\n"
                + corpo_reescrito + "\n\n" + "\n".join(campos_extra) + "\n")
    return f"LICAO_{ident}-{slug(titulo)}", conteudo


def cmd_nova(root: Path, descricao, familia, deteccao, prevencao, origem, gerou,
            reincide, corpo, data=None, registro="", hoje=None) -> int:
    """Cadastra uma lição em debts/licoes/ — o arquivo nasce válido ou não nasce."""
    if not (root / "debts").is_dir():
        die("debts/ não encontrado — crie o registro pelo template da projeto-init")
    pasta = root / DIR_LICOES
    pasta.mkdir(parents=True, exist_ok=True)

    ids_disco = ids_licoes_em_disco(root)
    ids_remotos = ids_licoes_em_refs_remotas(root)
    print(f"[id] {len(ids_disco)} em disco + {len(ids_remotos)} em refs remotas" if ids_remotos
          else "[id] só o disco — nenhum ref remoto buscado (git fetch --prune)")
    ident = proximo_id_licao(ids_disco | ids_remotos)

    campos = {
        "id": ident,
        "data": data or (hoje or date.today()).isoformat(),
        "descricao": descricao.strip(),
        "familia": familia.strip(),
        "deteccao": deteccao,
        "prevencao": prevencao,
        "origem": origem.strip(),
        "gerou": _normaliza_lista(gerou),
        "reincide": _normaliza_lista(reincide),
        "registro": (registro or "").strip(),
    }
    corpo = corpo or ""
    nome_base, conteudo = render_licao(campos, corpo)
    destino = pasta / f"{nome_base}.md"
    if destino.exists():
        print(f"[recusado] {destino.relative_to(root)} já existe — mude a descrição")
        return 1

    n_palavras = len(corpo.split())
    destino.write_text(conteudo, encoding="utf-8")
    item, erros = parse_licao(destino)
    if item:
        erros += validar_licao(item, ids_em_disco(root), ids_disco)
    if erros:
        destino.unlink()  # item inválido nunca fica no disco (ADR-0030, mesma regra do débito)
        for e in erros:
            print(f"[recusado] {e}")
        return 1
    if n_palavras > LICAO_TETO_PALAVRAS:
        print(f"[aviso] corpo com {n_palavras} palavras, acima de LICAO_TETO_PALAVRAS "
              f"({LICAO_TETO_PALAVRAS}) — narrativa longa vai no handoff/PR, linkada")
    print(destino.relative_to(root))
    print(f"regenere o índice: python3 {Path(__file__).name} indice .")
    return 0


def reincidencias(itens: list) -> dict:
    """id → [ids POSTERIORES que o citam em reincide] — nunca gravado na lição antiga."""
    mapa = {}
    for item in itens:
        for alvo in item.get("reincide", []):
            mapa.setdefault(alvo, []).append(item["id"])
    return mapa


def render_indice(itens: list) -> str:
    """Render determinístico do LICOES.md — mesmas lições, mesmos bytes."""
    contagem_deteccao = Counter(i.get("deteccao", "") for i in itens)
    contagem_prevencao = Counter(i.get("prevencao", "") for i in itens)
    rein = reincidencias(itens)
    familias = {}
    for item in itens:
        familias.setdefault(item.get("familia", ""), []).append(item["id"])

    ordenados = sorted(itens, key=lambda i: (i.get("data", ""), i["id"]), reverse=True)
    linhas_lic = []
    for item in ordenados:
        marcas = []
        if item.get("gerou"):
            marcas.append("gerou " + ", ".join(item["gerou"]))
        if item.get("reincide"):
            marcas.append("reincide " + ", ".join(item["reincide"]))
        posteriores = rein.get(item["id"])
        if posteriores:
            marcas.append("reincidiu em " + ", ".join(posteriores))
        sufixo = f" · {' · '.join(marcas)}" if marcas else ""
        nome = item["_arquivo"].rsplit("/", 1)[-1]
        linhas_lic.append(f"- [{item['id']}](licoes/{nome}) — {item['data']} — "
                          f"{item['descricao']} · {item['familia']}{sufixo}")

    det_txt = " · ".join(f"{k} {v}" for k, v in contagem_deteccao.items() if k and v)
    prev_txt = " · ".join(f"{k} {v}" for k, v in contagem_prevencao.items() if k and v)
    partes = [
        "# Lições — post-mortems",
        "<!-- GERADO por licao.py indice — não edite à mão; regenere após cadastrar.",
        "     Fonte: debts/licoes/ -->",
        "",
        "> Registro canônico em [licoes/](licoes/) ([ADR-0042]"
        "(../docs/adrs/ADR-0042-licoes-em-arquivo-por-item.md)): uma lição por "
        "arquivo, imutável — reincidência é lição nova que cita a antiga. Ação "
        "pendente é DT em [ativos/](ativos/); regras em [README.md](README.md).",
        "",
        f"**{len(itens)} lições** · detecção: {det_txt} · prevenção: {prev_txt}",
        "",
        "## Lições",
    ]
    partes += linhas_lic
    familias_rein = {f: sorted(ids) for f, ids in familias.items() if len(ids) >= 2}
    if familias_rein:
        partes += ["", "## Famílias com reincidência"]
        for fam in sorted(familias_rein):
            partes.append(f"- **{fam}**: {', '.join(familias_rein[fam])}")
    return "\n".join(partes) + "\n"


def cmd_indice(root: Path, verificar: bool = False) -> int:
    """Regenera (ou verifica) debts/LICOES.md a partir de debts/licoes/."""
    pasta = root / DIR_LICOES
    itens, ilegiveis = [], []
    if pasta.is_dir():
        for p in sorted(pasta.glob("*.md")):
            item, erros = parse_licao(p)
            if erros or item is None:
                ilegiveis.append((p.name, erros))
            else:
                itens.append(item)

    render = render_indice(itens)
    destino = root / INDICE_LICOES
    if verificar:
        atual = destino.read_text(encoding="utf-8") if destino.is_file() else None
        if atual != render:
            print(f"{INDICE_LICOES} diverge do render — regenere: "
                  f"python3 {Path(__file__).name} indice .")
            return 1
        return 0

    destino.write_text(render, encoding="utf-8")
    for nome, erros in ilegiveis:
        print(f"[ilegível] {nome}: fora do índice")
        for e in erros:
            print(f"  {e}")
    return 1 if ilegiveis else 0


def main() -> None:
    if "--selftest" in sys.argv[1:]:
        selftest()
        return
    p = argparse.ArgumentParser(description="Registro de lições do deltaspec.")
    p.add_argument("comando", choices=("nova", "indice"))
    p.add_argument("root", nargs="?", default=".")
    p.add_argument("--descricao", help="nova: a regra que fica, uma linha")
    p.add_argument("--familia", help="nova: agrupador kebab-case livre")
    p.add_argument("--deteccao", choices=DETECCOES, help="nova: como o problema foi pego")
    p.add_argument("--prevencao", choices=PREVENCOES, help="nova: o que impede a reincidência")
    p.add_argument("--origem", help="nova: onde o incidente ocorreu (delta/PR/sessão)")
    p.add_argument("--gerou", default="—", help="nova: DT-NNN[, DT-MMM] ou — (default)")
    p.add_argument("--reincide", default="—", help="nova: L-NNN[, L-MMM] ou — (default)")
    p.add_argument("--data", help="nova: AAAA-MM-DD do incidente (default: hoje)")
    p.add_argument("--registro", default="", help="nova: commit/PR que gravou a lição")
    p.add_argument("--corpo-arquivo", help="nova: arquivo com as 4 seções (default: stdin)")
    p.add_argument("--verificar", action="store_true", help="indice: não escreve, só compara")
    a = p.parse_args()
    root = Path(a.root).resolve()

    if a.comando == "indice":
        sys.exit(cmd_indice(root, a.verificar))

    if not (a.descricao and a.familia and a.deteccao and a.prevencao and a.origem):
        die("nova exige --descricao --familia --deteccao --prevencao --origem")
    corpo = (Path(a.corpo_arquivo).read_text(encoding="utf-8") if a.corpo_arquivo
             else "" if sys.stdin.isatty() else sys.stdin.read())
    sys.exit(cmd_nova(root, a.descricao, a.familia, a.deteccao, a.prevencao, a.origem,
                      a.gerou, a.reincide, corpo, data=a.data, registro=a.registro))


# ---------------------------------------------------------------- selftest


def selftest_parse() -> None:
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        pasta = root / DIR_LICOES
        pasta.mkdir(parents=True)

        corpo_valido = (
            "## O que aconteceu\nAlgo aconteceu de verdade.\n\n"
            "## Causa\n- fator um\n- fator dois\n\n"
            "## Desfecho\nFoi corrigido em algum lugar.\n\n"
            "## Prevenção\n- disciplina: regra tal\n\n"
            "- **Origem:** delta-001\n"
        )

        def fm(ident, **over):
            base = {"id": ident, "data": "2026-01-01", "descricao": "a regra que fica",
                    "familia": "familia-teste", "deteccao": "gate", "prevencao": "disciplina",
                    "origem": "delta-001", "gerou": "—", "reincide": "L-001"}
            base.update(over)
            linhas = "\n".join(f"{k}: {v}" for k, v in base.items())
            return f"---\n{linhas}\n---\n\n# [{ident}] - {base['descricao']}\n\n{corpo_valido}"

        def escreve(conteudo):
            (pasta / "LICAO_L-002-x.md").write_text(conteudo, encoding="utf-8")

        # (a) válido
        escreve(fm("L-002"))
        item, erros = parse_licao(pasta / "LICAO_L-002-x.md")
        assert erros == [], f"deveria ser válido: {erros}"
        assert item["gerou"] == [] and item["reincide"] == ["L-001"], item

        # (b) sem familia
        escreve(fm("L-002").replace("familia: familia-teste\n", ""))
        _, erros = parse_licao(pasta / "LICAO_L-002-x.md")
        assert any("familia" in e for e in erros), erros

        # (c) deteccao inválida
        escreve(fm("L-002", deteccao="manual"))
        _, erros = parse_licao(pasta / "LICAO_L-002-x.md")
        assert any("deteccao" in e for e in erros), erros

        # (d) familia fora do kebab-case
        escreve(fm("L-002", familia="Teste Auto"))
        _, erros = parse_licao(pasta / "LICAO_L-002-x.md")
        assert any("familia" in e for e in erros), erros

        # (e) H1 divergente
        txt = fm("L-002").replace("# [L-002] - a regra que fica", "# [L-002] - outra coisa")
        escreve(txt)
        _, erros = parse_licao(pasta / "LICAO_L-002-x.md")
        assert any("título H1" in e for e in erros), erros

        # (f) seções fora de ordem
        corpo_errado = (
            "## Causa\n- fator um\n- fator dois\n\n"
            "## O que aconteceu\nAlgo aconteceu de verdade.\n\n"
            "## Desfecho\nFoi corrigido em algum lugar.\n\n"
            "## Prevenção\n- disciplina: regra tal\n\n"
            "- **Origem:** delta-001\n"
        )
        escreve(fm("L-002").replace(corpo_valido, corpo_errado))
        _, erros = parse_licao(pasta / "LICAO_L-002-x.md")
        assert any("fora de ordem" in e for e in erros), erros

        # (g) campo citado dentro da prosa não é frontmatter
        escreve(fm("L-002") + "\ndescricao: outra\n")
        item, erros = parse_licao(pasta / "LICAO_L-002-x.md")
        assert erros == [] and item["descricao"] == "a regra que fica", (erros, item)

        # (h) proximo_id_licao
        assert proximo_id_licao(set()) == "L-001"
        assert proximo_id_licao({"L-003", "L-010", "lixo"}) == "L-011"

        # (i) ids_licoes_em_disco só lê o padrão
        (pasta / "rascunho.md").write_text("nada", encoding="utf-8")
        escreve(fm("L-002"))
        assert ids_licoes_em_disco(root) == {"L-002"}, ids_licoes_em_disco(root)

    print("licao selftest_parse: OK (9 casos)")


def selftest_nova() -> None:
    import io
    import tempfile
    from contextlib import redirect_stdout

    def novo_repo():
        root = Path(tempfile.mkdtemp())
        (root / "debts" / "ativos").mkdir(parents=True)
        (root / "debts" / "_archive").mkdir(parents=True)
        (root / "debts" / "ativos" / "DEBT_DT-001-x.md").write_text("placeholder", encoding="utf-8")
        return root

    corpo_ok = (
        "## O que aconteceu\nAlgo [x](docs/a.md) aconteceu.\n\n"
        "## Causa\n- fator\n\n"
        "## Desfecho\nCorrigido, ver [#5](../../pull/5).\n\n"
        "## Prevenção\n- disciplina: regra tal\n"
    )

    # (a) válido, com links reescritos para 2 níveis
    root = novo_repo()
    r = cmd_nova(root, "regra que fica", "familia-x", "gate", "disciplina", "delta-001",
                "—", "—", corpo_ok, hoje=date(2026, 9, 4))
    assert r == 0
    arq = next((root / DIR_LICOES).glob("LICAO_L-001-*.md"))
    item, erros = parse_licao(arq)
    assert erros == [], erros
    texto = arq.read_text(encoding="utf-8")
    assert "../../docs/a.md" in texto, texto
    assert "../../../../pull/5" in texto, texto

    # (b) gerou inexistente — nada fica no disco
    root = novo_repo()
    r = cmd_nova(root, "x", "fam", "gate", "gate", "delta-001", "DT-009", "—", corpo_ok)
    assert r == 1 and not list((root / DIR_LICOES).glob("*.md"))

    # (c) reincide inexistente
    root = novo_repo()
    r = cmd_nova(root, "x", "fam", "gate", "gate", "delta-001", "—", "L-007", corpo_ok)
    assert r == 1 and not list((root / DIR_LICOES).glob("*.md"))

    # (d) prevencao debito sem gerou
    root = novo_repo()
    r = cmd_nova(root, "x", "fam", "gate", "debito", "delta-001", "—", "—", corpo_ok)
    assert r == 1

    # (e) descricao acima do teto
    root = novo_repo()
    r = cmd_nova(root, "x" * (DESCRICAO_LIMITE + 1), "fam", "gate", "gate", "delta-001",
                "—", "—", corpo_ok)
    assert r == 1

    # (f) corpo sem Prevenção
    root = novo_repo()
    corpo_incompleto = "## O que aconteceu\nx\n\n## Causa\n- y\n\n## Desfecho\nz\n"
    r = cmd_nova(root, "x", "fam", "gate", "gate", "delta-001", "—", "—", corpo_incompleto)
    assert r == 1

    # (g) teto de palavras — aviso, não recusa
    root = novo_repo()
    corpo_longo = corpo_ok + ("palavra " * (LICAO_TETO_PALAVRAS + 10))
    saida = io.StringIO()
    with redirect_stdout(saida):
        r = cmd_nova(root, "x", "fam", "gate", "gate", "delta-001", "—", "—", corpo_longo)
    assert r == 0, saida.getvalue()
    assert "aviso" in saida.getvalue()

    # (h) --data omitido = hoje (injetado)
    root = novo_repo()
    cmd_nova(root, "x", "fam", "gate", "gate", "delta-001", "—", "—", corpo_ok,
             hoje=date(2026, 9, 4))
    arq = next((root / DIR_LICOES).glob("*.md"))
    item, _ = parse_licao(arq)
    assert item["data"] == "2026-09-04", item["data"]

    # (i) debts/ ausente
    root = Path(tempfile.mkdtemp())
    try:
        cmd_nova(root, "x", "fam", "gate", "gate", "delta-001", "—", "—", corpo_ok)
        assert False, "deveria morrer (die)"
    except SystemExit as e:
        assert e.code == 2

    # (j) segunda chamada recebe L-002
    root = novo_repo()
    cmd_nova(root, "primeira", "fam", "gate", "gate", "delta-001", "—", "—", corpo_ok,
             hoje=date(2026, 9, 4))
    cmd_nova(root, "segunda", "fam", "gate", "gate", "delta-001", "—", "—", corpo_ok,
             hoje=date(2026, 9, 4))
    nomes = sorted(p.name for p in (root / DIR_LICOES).glob("*.md"))
    assert nomes[0].startswith("LICAO_L-001-") and nomes[1].startswith("LICAO_L-002-"), nomes

    # (k) --registro omitido = sem linha Registro
    root = novo_repo()
    cmd_nova(root, "x", "fam", "gate", "gate", "delta-001", "—", "—", corpo_ok,
             hoje=date(2026, 9, 4))
    arq = next((root / DIR_LICOES).glob("*.md"))
    assert "Registro" not in arq.read_text(encoding="utf-8")

    print("licao selftest_nova: OK (11 casos)")


def selftest_indice() -> None:
    import tempfile

    root = Path(tempfile.mkdtemp())
    (root / "debts" / "ativos").mkdir(parents=True)
    (root / "debts" / "ativos" / "DEBT_DT-001-x.md").write_text("placeholder", encoding="utf-8")

    corpo_ok = "## O que aconteceu\nx\n\n## Causa\n- y\n\n## Desfecho\nz\n\n## Prevenção\n- disciplina: r\n"

    cmd_nova(root, "regra 1", "a", "gate", "gate", "origem-1", "—", "—", corpo_ok, data="2026-07-18")
    cmd_nova(root, "regra 2", "a", "revisao", "debito", "origem-2", "DT-001", "L-001", corpo_ok,
             data="2026-08-01")
    cmd_nova(root, "regra 3", "b", "sorte", "disciplina", "origem-3", "—", "—", corpo_ok,
             data="2026-08-01")

    itens = []
    for p in sorted((root / DIR_LICOES).glob("*.md")):
        item, erros = parse_licao(p)
        assert not erros, erros
        itens.append(item)

    render = render_indice(itens)
    assert render.startswith("# Lições"), render[:40]
    assert "GERADO por licao.py indice" in render
    assert "**3 lições**" in render
    assert "gate 1" in render and "sorte 1" in render, render

    linhas = [l for l in render.splitlines() if l.startswith("- [L-")]
    assert linhas[0].startswith("- [L-003]"), linhas
    assert linhas[1].startswith("- [L-002]"), linhas
    assert linhas[2].startswith("- [L-001]"), linhas
    assert "reincidiu em L-002" in linhas[2], linhas[2]
    assert "reincide L-001" in linhas[1] and "gerou DT-001" in linhas[1], linhas[1]
    assert "## Famílias com reincidência" in render
    assert "L-001, L-002" in render
    assert "**b**" not in render
    assert render_indice(itens) == render, "determinístico"

    r = cmd_indice(root)
    assert r == 0
    assert (root / INDICE_LICOES).is_file()
    r = cmd_indice(root, verificar=True)
    assert r == 0
    (root / INDICE_LICOES).write_text("alterado à mão\n", encoding="utf-8")
    assert cmd_indice(root, verificar=True) == 1

    (root / DIR_LICOES / "LICAO_L-099-quebrada.md").write_text("sem frontmatter", encoding="utf-8")
    assert cmd_indice(root) == 1
    texto = (root / INDICE_LICOES).read_text(encoding="utf-8")
    assert "L-099" not in texto

    print("licao selftest_indice: OK (12 casos)")


def selftest() -> None:
    selftest_parse()
    selftest_nova()
    selftest_indice()
    print("licao selftest: OK (32 casos)")


if __name__ == "__main__":
    main()
