#!/usr/bin/env python3
"""Gate e gerador do modelo de dados em três camadas (skill modelo-dados, delta-073).

Camadas e donos (regra: references/camadas.md):
  1 conceitual  → docs/data-model.md   (propósito, relações, invariantes + ERD DERIVADO)
  2 semântica   → DATA_DICTIONARY.md   (delta-074)
  3 contrato    → <saida>/schema.dbml  (dono da estrutura; ADR-0009)

Subcomandos:
  gerar-erd [RAIZ] [--dbml CAMINHO] [--escrever]   emite o bloco erDiagram (stdout) ou o grava na fence de ## Visão
  check     [RAIZ] [--dbml CAMINHO] [--forcar]     M1 .dbml parseável · M2 set-diff entidades · M3 ERD byte-igual
  --selftest                                         fixtures co-localizadas (RNF4)

Severidade máxima na v1: ALTO (ADR-0038). Exit 0 sem achado, 1 com ALTO ou contrato inválido, 2 erro de uso
(arquivo não encontrado, data-model.md sem fence, argumento inválido).
Perfil sem `artefatos.modelo-dados.obrigatorio: true` → o check se omite com 1 linha (RNF2).
Parser DBML por regex num SUBCONJUNTO declarado em camadas.md; função pura importável pela delta-074.
"""
import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

try:
    import yaml  # única dependência externa admitida nos gates (ADR-0023)
except ModuleNotFoundError:
    sys.exit("ERRO: PyYAML ausente — rode 'pip install pyyaml' (ADR-0023)")

DATA_MODEL = "docs/data-model.md"   # nome fixo do artefato conceitual (R2)
DBML_NOME = "schema.dbml"           # nome fixo do contrato dentro de `saida` (R1)
SAIDA_DEFAULT = "docs/diagrams/"    # default do template doc-profile.yaml quando `saida` falta
ORDEM = {"CRÍTICO": 0, "ALTO": 1, "MÉDIO": 2, "BAIXO": 3}


@dataclass
class Coluna:
    nome: str
    tipo: str
    settings: dict = field(default_factory=dict)   # brutos: pk, not null, unique, default, note, ref (delta-074 consome)


@dataclass
class Tabela:
    nome: str
    alias: str | None = None
    colunas: list = field(default_factory=list)


@dataclass
class Ref:
    origem: tuple   # (tabela, coluna)
    op: str         # > < - <>
    destino: tuple


@dataclass
class Modelo:
    tabelas: list = field(default_factory=list)
    refs: list = field(default_factory=list)
    erros: list = field(default_factory=list)   # [(linha, mensagem)] — M1


# ---------------------------------------------------------------------------
# Parser DBML (funções puras — R3). Subconjunto e regras: references/camadas.md.
# ---------------------------------------------------------------------------

BOM = "\ufeff"
# Comentários e strings, leftmost-first: string antes de `//` dentro dela, `'''` antes de `'`; `\'` escapado respeitado.
RE_APAGA = re.compile(r"//[^\n]*|/\*.*?\*/|'''.*?'''|'(?:\\.|[^'\\])*'|`[^`]*`", re.S)


def blanking(texto: str) -> str:
    """Apaga comentários (`//`, `/* */`) e strings (`'''`, `'`, crase) preservando a contagem de linhas
    (padrão lint_spine do BMAD). Aspas duplas ficam: em DBML delimitam identificador, não string."""
    return RE_APAGA.sub(lambda m: re.sub(r"[^\n]", " ", m.group()), texto)


IDENT = r'(?:"[^"]+"|\w+)'
NOME_QUALIFICADO = rf'{IDENT}(?:\.{IDENT})*'
RE_TABLE = re.compile(rf'^\s*Table\s+(?P<nome>{NOME_QUALIFICADO})(?:\s+as\s+(?P<alias>{IDENT}))?(?:\s*\[[^\]]*\])?\s*\{{\s*$')
RE_TABLE_SEM_BLOCO = re.compile(r'^\s*Table\b')
RE_BLOCO_ANINHADO = re.compile(r'^\s*(?:indexes|Note)\b[^{]*\{\s*$')   # dentro de Table; fora, RE_ABRE genérico
RE_COLUNA = re.compile(rf'^\s*(?P<nome>{IDENT})\s+(?P<tipo>"[^"]+"|\S+)(?:\s*\[(?P<settings>[^\]]*)\])?\s*$')
RE_NOTE_LINHA = re.compile(r'^\s*Note\s*:')
LADO = rf'{IDENT}(?:\.{IDENT})+'
RE_REF = re.compile(rf'^\s*Ref(?:\s+{IDENT})?\s*:\s*(?P<a>{LADO})\s*(?P<op><>|>|<|-)\s*(?P<b>{LADO})(?:\s*\[[^\]]*\])?\s*$')
RE_REF_INLINE = re.compile(rf'^(?P<op><>|>|<|-)\s*(?P<lado>{LADO})$')
RE_FECHA = re.compile(r'^\s*\}\s*$')
RE_ABRE = re.compile(r'\{\s*$')


def _limpa(ident: str) -> str:
    return ident.strip().strip('"')


def _segmentos(qualificado: str) -> list:
    return [_limpa(p) for p in re.findall(IDENT, qualificado)]


def _nome_fisico(qualificado: str) -> str:
    """`public.users`, `"s"."users"`, `users` → `users` (último segmento, sem aspas, sem schema)."""
    return _segmentos(qualificado)[-1]


def _lado(texto: str) -> tuple:
    partes = _segmentos(texto)
    return (partes[-2], partes[-1])


def _settings(bruto: str | None) -> dict:
    """`pk, not null, ref: > C.id, default: 0` → {'pk': True, 'not null': True, 'ref': '> C.id', 'default': '0'}.
    `primary key` normaliza para `pk`; strings já vieram apagadas pelo blanking (valor fica vazio)."""
    d = {}
    for item in (bruto or "").split(","):
        item = item.strip()
        if not item:
            continue
        chave, sep, valor = item.partition(":")
        chave = chave.strip().lower()
        if chave == "primary key":
            chave = "pk"
        d[chave] = valor.strip() if sep else True
    return d


def parse_dbml(texto: str) -> Modelo:
    """Função pura (R3): lê o subconjunto DBML de camadas.md. Nunca lança — erros vão em `modelo.erros` (M1)."""
    m = Modelo()
    pilha = []          # [(tipo, linha)] — 'table' | 'ignorado'
    tabela = None
    refs_brutas = []    # (linha, lado_a, op, lado_b) — resolvidas no fim, quando todas as tabelas existem
    for num, linha in enumerate(blanking(texto.lstrip(BOM)).splitlines(), 1):
        if not linha.strip():
            continue
        if RE_FECHA.match(linha):
            if not pilha:
                m.erros.append((num, "chave `}` sem abertura"))
                continue
            tipo, _ = pilha.pop()
            if tipo == "table":
                tabela = None
            continue
        if pilha and pilha[-1][0] == "ignorado":
            if RE_ABRE.search(linha):
                pilha.append(("ignorado", num))
            continue
        if tabela is not None and RE_TABLE.match(linha):
            _, aberta_em = pilha.pop()   # `Table` nova sem fechar a anterior: acusa na linha de abertura e segue
            m.erros.append((aberta_em, f"`Table {tabela.nome}` aberta e nunca fechada"))
            tabela = None
        if tabela is not None:
            if RE_BLOCO_ANINHADO.match(linha):
                pilha.append(("ignorado", num))
                continue
            if RE_NOTE_LINHA.match(linha):
                continue
            col = RE_COLUNA.match(linha)
            if not col:
                m.erros.append((num, f"linha dentro de `Table {tabela.nome}` não é coluna do subconjunto"))
                continue
            settings = _settings(col.group("settings"))
            coluna = Coluna(_limpa(col.group("nome")), _limpa(col.group("tipo")), settings)
            tabela.colunas.append(coluna)
            inline = RE_REF_INLINE.match(settings["ref"]) if isinstance(settings.get("ref"), str) else None
            if inline:
                refs_brutas.append((num, (tabela.nome, coluna.nome), inline.group("op"), _lado(inline.group("lado"))))
            continue
        t = RE_TABLE.match(linha)
        if t:
            tabela = Tabela(_nome_fisico(t.group("nome")), _limpa(t.group("alias")) if t.group("alias") else None)
            m.tabelas.append(tabela)
            pilha.append(("table", num))
            continue
        if RE_TABLE_SEM_BLOCO.match(linha):
            m.erros.append((num, "`Table` sem bloco `{` na mesma linha ou cabeçalho fora do subconjunto"))
            continue
        r = RE_REF.match(linha)
        if r:
            refs_brutas.append((num, _lado(r.group("a")), r.group("op"), _lado(r.group("b"))))
            continue
        if RE_ABRE.search(linha):
            pilha.append(("ignorado", num))   # Enum, TableGroup, Project, Ref { } … — fora do subconjunto, sem erro
        # resto (Project inline, Ref composta, …) é ignorado sem erro (Fora de escopo da delta-073)
    for tipo, num in pilha:
        m.erros.append((num, f"bloco `{tipo}` aberto e nunca fechado"))
    por_nome = {t.nome: t for t in m.tabelas}
    por_nome.update({t.alias: t for t in m.tabelas if t.alias})
    for num, a, op, b in refs_brutas:
        lados = []
        for tab, col in (a, b):
            t = por_nome.get(tab)
            if t is None:
                m.erros.append((num, f"Ref cita tabela inexistente: `{tab}`"))
                break
            if col not in {c.nome for c in t.colunas}:
                m.erros.append((num, f"Ref cita coluna inexistente: `{tab}.{col}`"))
                break
            lados.append((t.nome, col))
        else:
            m.refs.append(Ref(lados[0], op, lados[1]))
    return m


# ---------------------------------------------------------------------------
# ERD derivado (R3) — determinístico, byte-igual entre execuções; formato pinado pelo golden do selftest.
# ---------------------------------------------------------------------------

RE_SANITIZA = re.compile(r"[^A-Za-z0-9_]")
RE_PARAMETROS = re.compile(r"\(.*\)$")
# Aresta por operador (dona: camadas.md). O Mermaid não tem opcionalidade no DBML → mínimo fixo.
CONECTOR = {">": "||--o{", "<": "||--o{", "-": "||--||", "<>": "}o--o{"}


def sanitiza(token: str) -> str:
    """Aspas fora, parâmetros `(…)` fora, resto fora de [A-Za-z0-9_] vira `_` — o Mermaid rejeita vírgula e aspas no atributo."""
    return RE_SANITIZA.sub("_", RE_PARAMETROS.sub("", token))


def _aresta(ref: Ref) -> tuple:
    """(um, muitos, rótulo). `a.x > b.y` → b é o lado um; `<` → a; `-`/`<>` → ordem do arquivo, rótulo da esquerda."""
    (ta, ca), (tb, cb) = ref.origem, ref.destino
    if ref.op == ">":
        return tb, ta, ca
    if ref.op == "<":
        return ta, tb, cb
    return ta, tb, ca


def gerar_erd(modelo: Modelo) -> str:
    # FK = coluna do lado muitos (`>`: origem · `<`: destino) e a da esquerda em `-`; `<>` não marca
    fk = {r.origem if r.op in (">", "-") else r.destino for r in modelo.refs if r.op != "<>"}
    linhas = ["erDiagram"]
    for t in modelo.tabelas:
        if not t.colunas:
            linhas.append(f"  {sanitiza(t.nome)}")
            continue
        linhas.append(f"  {sanitiza(t.nome)} {{")
        for c in t.colunas:
            chaves = [k for k, ok in (("PK", c.settings.get("pk") is True), ("FK", (t.nome, c.nome) in fk)) if ok]
            sufixo = f" {','.join(chaves)}" if chaves else ""
            linhas.append(f"    {sanitiza(c.tipo)} {sanitiza(c.nome)}{sufixo}")
        linhas.append("  }")
    for r in modelo.refs:
        um, muitos, rotulo = _aresta(r)
        linhas.append(f"  {sanitiza(um)} {CONECTOR[r.op]} {sanitiza(muitos)} : {sanitiza(rotulo)}")
    return "\n".join(linhas) + "\n"


# ---------------------------------------------------------------------------
# data-model.md (camada conceitual) — leitura das entidades e da fence derivada.
# ---------------------------------------------------------------------------

RE_SECAO = re.compile(r"^##\s+(.+?)\s*$", re.M)
RE_H3 = re.compile(r"^###\s+(.+?)\s*$", re.M)
RE_FENCE = re.compile(r"^```mermaid[^\n]*\n(.*?)^```[ \t]*$", re.M | re.S)


def _secao(texto: str, titulo: str) -> tuple:
    """(início, corpo) da seção `## titulo` até o próximo `##` (ou o fim); (None, None) se não existe."""
    secoes = list(RE_SECAO.finditer(texto))
    for i, s in enumerate(secoes):
        if s.group(1).lower() == titulo.lower():
            fim = secoes[i + 1].start() if i + 1 < len(secoes) else len(texto)
            return s.end(), texto[s.end():fim]
    return None, None


def entidades_do_data_model(texto: str) -> list:
    """Nome = texto inteiro do heading `###` sob `## Entidades`, sem aspas (R4 — sem tolerância a sufixo)."""
    _, corpo = _secao(texto.replace("\r\n", "\n"), "Entidades")
    return [h.strip().strip('"') for h in RE_H3.findall(corpo)] if corpo else []


def bloco_erd(texto: str) -> str | None:
    """Conteúdo da primeira fence ```mermaid de `## Visão`; None se seção ou fence ausente."""
    _, corpo = _secao(texto.replace("\r\n", "\n"), "Visão")
    f = RE_FENCE.search(corpo) if corpo else None
    return f.group(1) if f else None


def substitui_bloco(texto: str, novo: str) -> str | None:
    """Troca o conteúdo da primeira fence mermaid de ## Visão; preserva o resto e o final de linha do arquivo."""
    crlf = "\r\n" in texto
    lf = texto.replace("\r\n", "\n")
    inicio, corpo = _secao(lf, "Visão")
    f = RE_FENCE.search(corpo) if corpo else None
    if not f:
        return None
    a, b = inicio + f.start(1), inicio + f.end(1)
    saida = lf[:a] + novo + lf[b:]
    return saida.replace("\n", "\r\n") if crlf else saida


# ---------------------------------------------------------------------------
# Perfil, resolução do contrato e gate (I/O) — R1, R4.
# ---------------------------------------------------------------------------

def carrega_perfil(raiz: Path) -> dict | None:
    """None = perfil ausente; {} = malformado (o C11 do check_cycle já acusa; aqui vale como não obrigatório)."""
    perfil = raiz / "doc-profile.yaml"
    if not perfil.is_file():
        return None
    try:
        d = yaml.safe_load(perfil.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return {}
    return d if isinstance(d, dict) else {}


def _categoria(perfil: dict | None) -> dict:
    cat = ((perfil or {}).get("artefatos") or {}).get("modelo-dados")
    return cat if isinstance(cat, dict) else {}


def modelo_dados_obrigatorio(perfil: dict | None) -> bool:
    return _categoria(perfil).get("obrigatorio") is True


def resolve_dbml(raiz: Path, perfil: dict | None, override: str | None) -> Path:
    """R1: `<artefatos.modelo-dados.saida>/schema.dbml`; `saida` ausente → docs/diagrams/; `--dbml` sobrepõe."""
    if override:
        return raiz / override   # absoluto em `override` vence o join
    saida = _categoria(perfil).get("saida") or SAIDA_DEFAULT
    return raiz / saida / DBML_NOME


def checar(raiz: Path, dbml: Path) -> list:
    """M1–M3. Severidade máxima ALTO (ADR-0038). Devolve [(sev, onde, inconsistência, ação)]."""
    v = []
    dm = raiz / DATA_MODEL
    if not dbml.is_file():
        onde = str(dbml.relative_to(raiz)) if dbml.is_relative_to(raiz) else str(dbml)
        v.append(("ALTO", onde, "contrato `.dbml` ausente",
                  "crie o .dbml na pasta `saida` do perfil (categoria modelo-dados, ADR-0009)"))
    if not dm.is_file():
        v.append(("ALTO", DATA_MODEL, "artefato conceitual ausente",
                  "rode /deltaspec:modelo-dados (template em skills/modelo-dados/references/templates/)"))
    if v:
        return v
    modelo = parse_dbml(dbml.read_text(encoding="utf-8-sig"))
    if modelo.erros:
        for linha, msg in modelo.erros:
            v.append(("ALTO", "M1", f"`{dbml.name}:{linha}` — {msg}",
                      "corrija o .dbml (subconjunto: camadas.md); M2 e M3 não rodaram: contrato não parseou"))
        return v
    texto_dm = dm.read_text(encoding="utf-8-sig")
    fisicas = {t.nome.lower() for t in modelo.tabelas}
    conceituais = {e.lower() for e in entidades_do_data_model(texto_dm)}
    for nome in sorted(fisicas - conceituais):
        v.append(("ALTO", "M2", f"`Table {nome}` sem `### {nome}` em data-model.md",
                  "descreva a entidade (stub via /deltaspec:modelo-dados)"))
    for nome in sorted(conceituais - fisicas):
        v.append(("ALTO", "M2", f"`### {nome}` em data-model.md sem `Table` no .dbml",
                  "remova a seção ou acrescente a Table ao contrato"))
    bloco = bloco_erd(texto_dm)
    if bloco is None:
        v.append(("ALTO", "M3", "bloco erDiagram ausente em `## Visão`", "rode `check_data_model.py gerar-erd --escrever`"))
    elif bloco.rstrip("\n") != gerar_erd(modelo).rstrip("\n"):   # lados já sem BOM (utf-8-sig) e em LF
        v.append(("ALTO", "M3", "erDiagram divergente do derivado do .dbml (drift)",
                  "rode `check_data_model.py gerar-erd --escrever`"))
    return v


def relatorio(v: list, nome: str) -> int:
    """Mesmo formato do check_cycle.py, para colar no analyze.md sem conversão. Devolve o exit code."""
    v = sorted(v, key=lambda f: ORDEM.get(f[0], 2))
    print(f"# Modelo de dados (mecânico) — {nome}")
    print("| # | Severidade | Onde | Inconsistência | Ação sugerida |")
    print("|---|---|---|---|---|")
    for i, (sev, onde, o_que, acao) in enumerate(v, 1):
        print(f"| {i} | {sev} | {onde} | {o_que} | {acao} |")
    print("\nParcial: cobre M1–M3 (camada conceitual × contrato); a camada semântica (M4–M6) chega na delta-074.")
    sevs = {f[0] for f in v}
    print(f"\n**Veredito:** {'BLOQUEADO' if 'CRÍTICO' in sevs else 'LIBERADO COM RESSALVAS' if v else 'LIBERADO'}")
    return 1 if sevs & {"CRÍTICO", "ALTO"} else 0


def selftest() -> None:
    # --- blanking preserva linhas e apaga comentários/strings, mantendo identificadores entre aspas duplas
    bruto = "Table a { // com }\n  x int [note: 'tem { chave']\n  /* multi\n  linha } */ y int\n}\n"
    limpo = blanking(bruto)
    assert limpo.count("\n") == bruto.count("\n"), "blanking alterou a contagem de linhas"
    assert "}" not in limpo.splitlines()[0][9:], "comentário // não foi apagado"
    assert "chave" not in limpo, "string entre aspas simples não foi apagada"
    assert "linha }" not in limpo, "comentário /* */ não foi apagado"
    assert '"' in blanking('Table "user accounts" {'), "identificador entre aspas duplas deve sobreviver ao blanking"

    # --- parse_dbml: subconjunto do R3
    dbml = '''Project demo { database_type: 'PostgreSQL' }
Table public.clientes as C [headercolor: #fff] {
  id int [pk, not null]
  nome "varchar(120)" [note: 'nome { civil']
  indexes {
    (id, nome) [unique]
  }
  Note: 'tabela de { clientes'
}
Table pedidos {
  id int [primary key]
  cliente_id int [ref: > C.id, not null]
  total decimal(10,2) [default: 0]
}
Table "itens do pedido" {
  pedido_id int [pk]
  sku "double precision"
}
Enum status { aberto  fechado }
Ref fk_itens: "itens do pedido".pedido_id > pedidos.id [delete: cascade]
Ref: clientes.id - pedidos.id
Ref: clientes.id <> pedidos.id
Ref: pedidos.id < "itens do pedido".pedido_id
'''
    m = parse_dbml(dbml)
    assert m.erros == [], f"modelo limpo não pode ter erro: {m.erros}"
    assert [t.nome for t in m.tabelas] == ["clientes", "pedidos", "itens do pedido"], [t.nome for t in m.tabelas]
    assert m.tabelas[0].alias == "C" and m.tabelas[0].colunas[0].settings.get("pk") is True
    assert m.tabelas[0].colunas[0].settings.get("not null") is True, "setting bruto 'not null' deve sobreviver (delta-074)"
    assert [c.nome for c in m.tabelas[0].colunas] == ["id", "nome"], "indexes/Note não podem virar coluna"
    assert m.tabelas[1].colunas[1].settings.get("pk") is None and m.tabelas[1].colunas[0].settings.get("pk") is True
    assert m.tabelas[1].colunas[2].tipo == "decimal(10,2)" and m.tabelas[1].colunas[2].settings.get("default") == "0"
    assert m.tabelas[2].colunas[1].tipo == "double precision"
    ops = [r.op for r in m.refs]
    assert ops == [">", ">", "-", "<>", "<"], ops   # inline primeiro (ordem do arquivo), depois as Ref: soltas
    assert m.refs[0].origem == ("pedidos", "cliente_id") and m.refs[0].destino == ("clientes", "id"), "alias C deve resolver para clientes"
    assert m.refs[1].origem == ("itens do pedido", "pedido_id")

    sujo = parse_dbml("Table a {\n  id int\n\nTable b {\n  id int\n}\nRef: a.id > c.id\nRef: a.zz > b.id\n")
    linhas = [l for l, _ in sujo.erros]
    assert 1 in linhas, f"Table a sem fechamento deve acusar na linha de abertura: {sujo.erros}"
    assert any("c" in msg for _, msg in sujo.erros), "Ref para tabela inexistente deve acusar"
    assert any("zz" in msg for _, msg in sujo.erros), "Ref para coluna inexistente deve acusar"
    assert parse_dbml("}\n").erros and parse_dbml("Table x\n").erros, "chave solta e Table sem bloco acusam"
    assert [t.nome for t in parse_dbml(BOM + "Table a {\n  id int\n}\n").tabelas] == ["a"], "BOM não pode silenciar o parser puro"
    assert parse_dbml("Table a {\n  id int [note: 'it\\'s {']\n}\n").erros == [], "aspa escapada dentro de string"

    # --- gerar_erd: golden (pinado — mudar o formato é mudar o M3 de todo consumidor)
    esperado = """erDiagram
  clientes {
    int id PK,FK
    varchar nome
  }
  pedidos {
    int id PK
    int cliente_id FK
    decimal total
  }
  itens_do_pedido {
    int pedido_id PK,FK
    double_precision sku
  }
  clientes ||--o{ pedidos : cliente_id
  pedidos ||--o{ itens_do_pedido : pedido_id
  clientes ||--|| pedidos : id
  clientes }o--o{ pedidos : id
  pedidos ||--o{ itens_do_pedido : pedido_id
"""
    assert gerar_erd(m) == esperado, "ERD divergiu do golden:\n" + gerar_erd(m)
    assert gerar_erd(m) == gerar_erd(parse_dbml(dbml)), "gerar_erd não é determinístico"
    assert gerar_erd(parse_dbml("Table vazia {\n}\n")) == "erDiagram\n  vazia\n", "Table sem coluna sai só o nome"

    # --- data-model.md: entidades e bloco
    dm = ("# Modelo\n\n## Visão\n<!-- derivado -->\n```mermaid\nerDiagram\n  a\n```\n\n## Entidades\n### clientes\ntexto\n"
          "### Pedidos\n\n## Fora do modelo\n### nao_conta\n")
    assert entidades_do_data_model(dm) == ["clientes", "Pedidos"], entidades_do_data_model(dm)
    assert bloco_erd(dm) == "erDiagram\n  a\n", repr(bloco_erd(dm))
    novo = substitui_bloco(dm, "erDiagram\n  b\n")
    assert bloco_erd(novo) == "erDiagram\n  b\n" and novo.replace("  b\n", "  a\n") == dm, "substitui_bloco tocou fora da fence"
    assert substitui_bloco("# sem visao\n", "x") is None and bloco_erd("## Visão\nsem fence\n## Entidades\n") is None
    crlf = dm.replace("\n", "\r\n")
    assert substitui_bloco(crlf, "erDiagram\n  b\n").count("\r\n") == crlf.count("\r\n"), "--escrever deve preservar CRLF"

    # --- check M1–M3 em fixtures reais (tempdir)
    import contextlib
    import io
    import tempfile
    perfil_obrig = "artefatos:\n  modelo-dados: { obrigatorio: true, saida: docs/diagrams/ }\n"
    perfil_opc = perfil_obrig.replace("true", "false")
    dm_limpo = ("# Modelo de dados — demo\n\n## Visão\n```mermaid\n" + esperado + "```\n\n## Entidades\n"
                "### clientes\n### pedidos\n### itens do pedido\n\n## Fora do modelo\n- nada\n")

    with tempfile.TemporaryDirectory() as tmp:
        def monta(perfil, dbml_txt, dm_txt):
            raiz = Path(tempfile.mkdtemp(dir=tmp))
            if perfil is not None:
                (raiz / "doc-profile.yaml").write_text(perfil, encoding="utf-8")
            (raiz / "docs" / "diagrams").mkdir(parents=True)
            if dbml_txt is not None:
                (raiz / "docs" / "diagrams" / DBML_NOME).write_text(dbml_txt, encoding="utf-8")
            if dm_txt is not None:
                (raiz / DATA_MODEL).write_text(dm_txt, encoding="utf-8")
            return raiz

        def roda(perfil, dbml_txt, dm_txt):
            raiz = monta(perfil, dbml_txt, dm_txt)
            return checar(raiz, resolve_dbml(raiz, carrega_perfil(raiz), None))

        def sevs(achados):
            return sorted(f"{s}:{onde}" for s, onde, _, _ in achados)

        assert roda(perfil_obrig, dbml, dm_limpo) == [], "fixture limpa deve ter zero achados"
        assert not modelo_dados_obrigatorio(carrega_perfil(monta(perfil_opc, dbml, dm_limpo))), "perfil opcional → omissão"
        assert carrega_perfil(monta(None, dbml, dm_limpo)) is None
        raiz = monta(perfil_obrig, dbml, dm_limpo)
        assert resolve_dbml(raiz, None, "x/y.dbml") == raiz / "x/y.dbml" and \
            resolve_dbml(raiz, {}, None) == raiz / SAIDA_DEFAULT / DBML_NOME, "resolução do R1"

        r = roda(perfil_obrig, "Table a {\n  id int\n", dm_limpo)
        assert [s for s, *_ in r] == ["ALTO"] and r[0][1] == "M1" and "M2 e M3 não rodaram" in r[0][3], f"malformado: {r}"
        r = roda(perfil_obrig, dbml, dm_limpo.replace("### pedidos\n", ""))
        assert sevs(r) == ["ALTO:M2"] and "pedidos" in r[0][2] and "data-model" in r[0][2], f"órfão no .dbml: {r}"
        r = roda(perfil_obrig, dbml, dm_limpo.replace("### pedidos\n", "### pedidos\n### fantasma\n"))
        assert sevs(r) == ["ALTO:M2"] and "fantasma" in r[0][2], f"órfão no data-model: {r}"
        r = roda(perfil_obrig, dbml, dm_limpo.replace("  clientes {", "  clientes_editado {"))
        assert sevs(r) == ["ALTO:M3"] and "--escrever" in r[0][3], f"drift acusa M3 com correção: {r}"
        r = roda(perfil_obrig, dbml, dm_limpo.replace("```mermaid\n" + esperado + "```\n", ""))
        assert sevs(r) == ["ALTO:M3"] and "ausente" in r[0][2], f"fence ausente acusa M3: {r}"
        r = roda(perfil_obrig, dbml, None)
        assert sevs(r) == [f"ALTO:{DATA_MODEL}"], f"artefato ausente: {r}"
        r = roda(perfil_obrig, None, dm_limpo)
        assert len(r) == 1 and r[0][0] == "ALTO" and DBML_NOME in r[0][1], f"contrato ausente: {r}"
        assert roda(perfil_obrig, dbml, BOM + dm_limpo.replace("\n", "\r\n")) == [], "CRLF/BOM não pode acusar M3"

        saida = io.StringIO()
        with contextlib.redirect_stdout(saida):
            codigo = relatorio(roda(perfil_obrig, dbml, dm_limpo.replace("### pedidos\n", "")), "demo")
        assert codigo == 1 and "| 1 | ALTO | M2 |" in saida.getvalue() and "**Veredito:** LIBERADO COM RESSALVAS" in saida.getvalue()
        with contextlib.redirect_stdout(io.StringIO()):
            assert relatorio([], "demo") == 0

    print("selftest OK")


def main() -> None:
    if sys.argv[1:] == ["--selftest"]:
        selftest()
        return
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    comum = argparse.ArgumentParser(add_help=False)
    comum.add_argument("raiz", nargs="?", default=".", help="raiz do projeto (doc-profile.yaml e docs/)")
    comum.add_argument("--dbml", help="sobrepõe a resolução <saida>/schema.dbml (relativo à raiz)")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("gerar-erd", parents=[comum]).add_argument(
        "--escrever", action="store_true", help="grava na fence ```mermaid de ## Visão do data-model.md")
    sub.add_parser("check", parents=[comum]).add_argument(
        "--forcar", action="store_true", help="roda mesmo com perfil ausente ou categoria opcional")
    a = p.parse_args()
    raiz = Path(a.raiz).resolve()
    perfil = carrega_perfil(raiz)
    dbml = resolve_dbml(raiz, perfil, a.dbml)
    if a.cmd == "gerar-erd":
        if not dbml.is_file():
            print(f"ERRO: contrato não encontrado: {dbml}", file=sys.stderr)
            sys.exit(2)
        modelo = parse_dbml(dbml.read_text(encoding="utf-8-sig"))
        if modelo.erros:
            sys.exit("ERRO: .dbml não parseou — " + "; ".join(f"linha {l}: {m}" for l, m in modelo.erros))
        erd = gerar_erd(modelo)
        if not a.escrever:
            sys.stdout.write(erd)
            return
        dm = raiz / DATA_MODEL
        novo = substitui_bloco(dm.open(encoding="utf-8", newline="").read(), erd) if dm.is_file() else None
        if novo is None:
            print(f"ERRO: {DATA_MODEL} ausente ou sem fence ```mermaid em `## Visão` — "
                  "crie do template via /deltaspec:modelo-dados", file=sys.stderr)
            sys.exit(2)
        with dm.open("w", encoding="utf-8", newline="") as f:   # preserva CRLF do arquivo alvo (RNF5)
            f.write(novo)
        print(f"ERD regravado em {DATA_MODEL}")
        return
    if not a.forcar and not modelo_dados_obrigatorio(perfil):
        motivo = "doc-profile.yaml ausente" if perfil is None else "artefatos.modelo-dados não é obrigatório"
        print(f"check_data_model: omitido — {motivo} (use --forcar para rodar assim mesmo)")
        return
    sys.exit(relatorio(checar(raiz, dbml), raiz.name))


if __name__ == "__main__":
    main()
