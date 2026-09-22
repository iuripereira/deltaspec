#!/usr/bin/env python3
"""Gate e gerador do modelo de dados em três camadas (skill modelo-dados, delta-073 · delta-075).

Camadas e donos (regra: references/camadas.md):
  1 conceitual  → docs/data-model.md   (propósito, relações, invariantes + ERD DERIVADO)
  2 semântica   → DATA_DICTIONARY.md   (definição, domínio, steward, sensibilidade, origem, qualidade)
  3 contrato    → <saida>/schema.dbml  (dono da estrutura; ADR-0009)

Subcomandos:
  gerar-erd [RAIZ] [--dbml CAMINHO] [--escrever]   emite o bloco erDiagram (stdout) ou o grava na fence de ## Visão
  check     [RAIZ] [--dbml CAMINHO] [--forcar]     M1–M7 (tabela de severidades: references/camadas.md)
  --selftest                                         fixtures co-localizadas (RNF4)

Severidade máxima na v1: ALTO (ADR-0038; M6 e M7 são sempre BAIXO). Exit 0 sem achado, 1 com ALTO ou contrato inválido,
2 erro de uso (arquivo não encontrado, data-model.md sem fence, argumento inválido).
Perfil sem `artefatos.modelo-dados.obrigatorio: true` → o check se omite com 1 linha (RNF2).
Parsers por regex num SUBCONJUNTO declarado em camadas.md; `parse_dbml`/`parse_dicionario` são funções puras.
"""
import argparse
import re
import sys
import unicodedata
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
    settings: dict = field(default_factory=dict)   # brutos: pk, not null, unique, default, note, ref (consumidor futuro)


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
# Dicionário de dados (camada semântica) — parser puro, R1/R2 da delta-075.
# ---------------------------------------------------------------------------

DATA_DICTIONARY = "DATA_DICTIONARY.md"   # nome fixo, na raiz do projeto (R1)
CONTRATOS_HEADING = "contratos entre módulos"   # heading H2 que NÃO é entidade (R2)

# Import do módulo da skill irmã audit-workspace — mesmo padrão de check_cycle.py → validate_integrity.py:
# find_repo_roots/detect_mode são a fonte única da detecção repo×workspace (R9); audit_workspace.py não é
# estendido (read-only por contrato) — só importado. Caminho relativo ao próprio arquivo, nunca absoluto de máquina.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "audit-workspace" / "scripts"))
from audit_workspace import detect_mode, find_repo_roots  # noqa: E402


def repos_com_dicionario(base: Path) -> list:
    """R9 (padronizar): repos com DATA_DICTIONARY.md, no escopo detectado (repo único ou workspace multi-repo)."""
    modo = detect_mode(base)
    if modo == "workspace":
        return [r for r in find_repo_roots(base) if (r / DATA_DICTIONARY).is_file()]
    if modo == "repo":
        return [base] if (base / DATA_DICTIONARY).is_file() else []
    return []
RE_METADADOS = re.compile(r"(Origem|Steward|Atualização)\s*:\s*([^·\n]*)")
RE_CAMPO_CELULA = re.compile(r"^(?P<canonico>.*?)\s*·\s*`(?P<fisico>[^`]*)`\s*$")


@dataclass
class CampoDicionario:
    canonico: str
    fisico: str
    definicao: str
    dominio: str
    tipo: str
    obrigatorio: str
    default: str
    sensibilidade: str
    qualidade: str


@dataclass
class EntidadeDicionario:
    nome: str = ""   # caixa original do heading — mensagens de achado não usam a chave em minúsculas
    origem: str = ""
    steward: str = ""
    atualizacao: str = ""
    campos: list = field(default_factory=list)


@dataclass
class Dicionario:
    entidades: dict = field(default_factory=dict)   # nome (lower) -> EntidadeDicionario
    erros: list = field(default_factory=list)         # [(linha, mensagem)] — M5 consome (entidade duplicada)


def _celulas(linha: str) -> list:
    """Células de uma linha de tabela markdown, respeitando `\\|` escapado — mesma sintaxe do R1."""
    partes = re.split(r"(?<!\\)\|", linha.strip())
    celulas = [p.replace("\\|", "|").strip() for p in partes]
    if celulas and celulas[0] == "":
        celulas = celulas[1:]
    if celulas and celulas[-1] == "":
        celulas = celulas[:-1]
    return celulas


def parse_dicionario(texto: str) -> Dicionario:
    """Função pura (R2): lê o template novo (R1). Nunca lança — entidade duplicada vira erro, consumido por M5."""
    d = Dicionario()
    lf = texto.replace("\r\n", "\n")
    headings = list(RE_SECAO.finditer(lf))
    for i, h in enumerate(headings):
        nome = h.group(1).strip()
        if nome.lower() == CONTRATOS_HEADING:
            continue
        fim = headings[i + 1].start() if i + 1 < len(headings) else len(lf)
        corpo = lf[h.end():fim]
        chave = nome.lower()
        if chave in d.entidades:
            d.erros.append((lf.count("\n", 0, h.start()) + 1, f"entidade duplicada: `{nome}`"))
            continue
        linha_meta = next((l for l in corpo.splitlines() if l.strip()), "")
        rotulos = {r.lower(): v.strip() for r, v in RE_METADADOS.findall(linha_meta)}   # rótulo ausente → ""
        ent = EntidadeDicionario(
            nome=nome, origem=rotulos.get("origem", ""), steward=rotulos.get("steward", ""),
            atualizacao=rotulos.get("atualização", ""),
        )
        for linha in corpo.splitlines():
            if not linha.strip().startswith("|"):
                continue
            celulas = _celulas(linha)
            if len(celulas) != 6:
                continue
            m = RE_CAMPO_CELULA.match(celulas[0])
            if not m:
                continue   # cabeçalho, separador `|---|` ou linha malformada — nunca vira CampoDicionario
            tipo, obrig, default = ((celulas[3].split(" · ") + ["", ""])[:3])
            ent.campos.append(CampoDicionario(
                canonico=m.group("canonico").strip(), fisico=m.group("fisico").strip(),
                definicao=celulas[1], dominio=celulas[2],
                tipo=tipo.strip(), obrigatorio=obrig.strip(), default=default.strip(),
                sensibilidade=celulas[4], qualidade=celulas[5],
            ))
        d.entidades[chave] = ent
    return d


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


def _achados_m4(modelo: Modelo, dic: Dicionario) -> list:
    """M4 (R3): cobertura campo a campo .dbml ↔ dicionário nos dois sentidos + tipo espelho."""
    v = []
    tabelas = {t.nome.lower(): t for t in modelo.tabelas}
    for nome in sorted(set(tabelas) - set(dic.entidades)):
        v.append(("ALTO", "M4", f"`Table {tabelas[nome].nome}` sem seção `## {tabelas[nome].nome}` no dicionário",
                  "descreva a entidade no DATA_DICTIONARY.md (modo auditar)"))
    for nome in sorted(set(dic.entidades) - set(tabelas)):
        v.append(("ALTO", "M4", f"`## {dic.entidades[nome].nome}` no dicionário sem `Table` correspondente no .dbml",
                  "remova a seção ou acrescente a Table ao contrato"))
    for nome in sorted(set(tabelas) & set(dic.entidades)):
        tabela, ent = tabelas[nome], dic.entidades[nome]
        colunas = {c.nome.lower(): c for c in tabela.colunas}
        campos_por_fisico = {}
        for campo in ent.campos:
            chave = campo.fisico.lower()
            if chave in campos_por_fisico:
                v.append(("ALTO", "M4", f"`{tabela.nome}.{campo.fisico}` duplicado no dicionário",
                          "una as linhas duplicadas em uma só"))
                continue
            campos_por_fisico[chave] = campo
        for chave_col, coluna in colunas.items():
            campo = campos_por_fisico.get(chave_col)
            if campo is None:
                v.append(("ALTO", "M4", f"`{tabela.nome}.{coluna.nome}` sem linha no dicionário",
                          "descreva o campo no DATA_DICTIONARY.md (modo auditar)"))
                continue
            if campo.tipo.lower().split() != coluna.tipo.lower().split():
                v.append(("ALTO", "M4",
                          f"`{tabela.nome}.{coluna.nome}` tipo divergente: dicionário diz `{campo.tipo}`, .dbml diz `{coluna.tipo}`",
                          "corrija a célula Tipo ou o .dbml"))
        for chave_campo in sorted(set(campos_por_fisico) - set(colunas)):
            campo = campos_por_fisico[chave_campo]
            v.append(("ALTO", "M4", f"`{tabela.nome}.{campo.fisico}` no dicionário sem coluna no .dbml",
                      "remova a linha ou acrescente a coluna ao contrato"))
    return v


RE_PREFIXO_CONFIANCA = re.compile(r"^\[(confirmado|inferido|lacuna)\]\s*")
RE_NAO_ALFANUM_M6 = re.compile(r"[^a-z0-9]+")


def _decorativa(valor: str) -> bool:
    v = valor.strip()
    return not v or (v.startswith("{{") and v.endswith("}}"))


def _achados_m5(dic: Dicionario) -> list:
    """M5 (R4/R5): células decorativas — Definição/Sens. por campo, Steward por entidade, entidade duplicada, dicionário vazio."""
    v = []
    for linha, msg in dic.erros:
        v.append(("ALTO", "M5", f"`{DATA_DICTIONARY}:{linha}` — {msg}", "una as seções duplicadas em uma só"))
    if not dic.entidades:
        v.append(("ALTO", "M5", "dicionário vazio: nenhuma entidade documentada",
                  "documente ao menos uma entidade (modo auditar) ou remova o arquivo"))
    for ent in dic.entidades.values():
        if _decorativa(ent.steward):
            v.append(("ALTO", "M5", f"`## {ent.nome}`: Steward vazio ou placeholder", "preencha o steward na linha de metadados"))
        for campo in ent.campos:
            if _decorativa(campo.definicao):
                v.append(("ALTO", "M5", f"`{ent.nome}.{campo.fisico}`: Definição vazia ou placeholder", "preencha a definição de negócio"))
            if _decorativa(campo.sensibilidade):
                v.append(("ALTO", "M5", f"`{ent.nome}.{campo.fisico}`: Sens. vazia ou placeholder",
                          "preencha a sensibilidade (taxonomia: camadas.md)"))
    return v


def _normaliza_m6(texto: str) -> str:
    sem_prefixo = RE_PREFIXO_CONFIANCA.sub("", texto.strip())
    sem_acento = unicodedata.normalize("NFKD", sem_prefixo).encode("ascii", "ignore").decode()
    return RE_NAO_ALFANUM_M6.sub(" ", sem_acento.lower()).strip()


def _achados_m6(dic: Dicionario) -> list:
    """M6 (R6): definição normalizada == canônico ou físico normalizado. Sempre BAIXO, heurística declarada."""
    v = []
    for ent in dic.entidades.values():
        for campo in ent.campos:
            alvo = _normaliza_m6(campo.definicao)
            if alvo and alvo in (_normaliza_m6(campo.canonico), _normaliza_m6(campo.fisico)):
                v.append(("BAIXO", "M6", f"`{ent.nome}.{campo.fisico}`: definição tautológica (\"{campo.definicao}\")",
                          "descreva o que o campo representa, não repita o nome"))
    return v


def _lacuna(valor: str) -> bool:
    """Célula que a mineração/entrevista não respondeu — marcada, não vazia. `[lacuna]` é um dos
    prefixos de RE_PREFIXO_CONFIANCA (vocabulário da descoberta); os outros dois não são pauta aqui."""
    return valor.strip().startswith("[lacuna]")


def _achados_m7(dic: Dicionario) -> list:
    """M7 (delta-095): célula marcada `[lacuna]`. Sempre BAIXO — `auditoria.md` diz que lacuna
    residual "é honesto, não é defeito" e que o próximo check a reapresenta como pauta. Antes
    desta delta ela não era reapresentada por ninguém: o M5 só enxerga vazio e `{{placeholder}}`,
    então um dicionário inteiro de `[lacuna]` saía LIBERADO, sem um achado (DT-095)."""
    v = []
    for ent in dic.entidades.values():
        if _lacuna(ent.steward):
            v.append(("BAIXO", "M7", f"`## {ent.nome}`: Steward em `[lacuna]`",
                      "responda na próxima rodada do modo auditar, ou preencha"))
        for campo in ent.campos:
            for rotulo, valor in (("Definição", campo.definicao), ("Sens.", campo.sensibilidade)):
                if _lacuna(valor):
                    v.append(("BAIXO", "M7", f"`{ent.nome}.{campo.fisico}`: {rotulo} em `[lacuna]`",
                              "responda na próxima rodada do modo auditar, ou preencha"))
    return v


def checar(raiz: Path, dbml: Path) -> list:
    """M1–M7. Severidade máxima ALTO (M6 e M7 são sempre BAIXO — ADR-0038). Devolve [(sev, onde, inconsistência, ação)]."""
    v = []
    dm = raiz / DATA_MODEL
    dic_path = raiz / DATA_DICTIONARY
    dbml_ok, dm_ok, dic_ok = dbml.is_file(), dm.is_file(), dic_path.is_file()

    dicionario_only = not dbml_ok and not dm_ok and dic_ok   # R4 (MUDA R99): única exceção nova
    if not dicionario_only:
        if not dbml_ok:
            onde = str(dbml.relative_to(raiz)) if dbml.is_relative_to(raiz) else str(dbml)
            v.append(("ALTO", onde, "contrato `.dbml` ausente",
                      "crie o .dbml na pasta `saida` do perfil (categoria modelo-dados, ADR-0009)"))
        if not dm_ok:
            v.append(("ALTO", DATA_MODEL, "artefato conceitual ausente",
                      "rode /deltaspec:modelo-dados (template em skills/modelo-dados/references/templates/)"))

    modelo = None
    if dbml_ok:
        modelo = parse_dbml(dbml.read_text(encoding="utf-8-sig"))
        if modelo.erros:
            for linha, msg in modelo.erros:
                v.append(("ALTO", "M1", f"`{dbml.name}:{linha}` — {msg}",
                          "corrija o .dbml (subconjunto: camadas.md); M2, M3 e M4 não rodaram: contrato não parseou"))
            modelo = None

    if dm_ok and modelo is not None:
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

    if dic_ok:
        dic = parse_dicionario(dic_path.read_text(encoding="utf-8-sig"))
        v += _achados_m5(dic)
        v += _achados_m6(dic)
        v += _achados_m7(dic)
        if modelo is not None:
            v += _achados_m4(modelo, dic)
        elif not dbml_ok:
            print("M4 não rodou: projeto sem .dbml", file=sys.stderr)
    return v


def relatorio(v: list, nome: str) -> int:
    """Mesmo formato do check_cycle.py, para colar no analyze.md sem conversão. Devolve o exit code."""
    v = sorted(v, key=lambda f: ORDEM.get(f[0], 2))
    print(f"# Modelo de dados (mecânico) — {nome}")
    print("| # | Severidade | Onde | Inconsistência | Ação sugerida |")
    print("|---|---|---|---|---|")
    for i, (sev, onde, o_que, acao) in enumerate(v, 1):
        print(f"| {i} | {sev} | {onde} | {o_que} | {acao} |")
    print("\nParcial: cobre M1–M7 (camada conceitual × contrato × dicionário).")
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
    assert m.tabelas[0].colunas[0].settings.get("not null") is True, "setting bruto 'not null' deve sobreviver ao parse"
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
        assert [s for s, *_ in r] == ["ALTO"] and r[0][1] == "M1" and "M2, M3 e M4 não rodaram" in r[0][3], f"malformado: {r}"
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

        # --- M4: cobertura + tipo (delta-075)
        cab = ("| Campo (canônico · físico) | Definição de negócio | Domínio de valores | Tipo · obrig. · default | Sens. | Qualidade |\n"
               "| --- | --- | --- | --- | --- | --- |\n")
        dic_ok = (
            "## clientes\nOrigem: CRM · Steward: vendas · Atualização: transacional\n\n" + cab +
            "| Id · `id` | identificador | sequencial | int · sim · — | interna | ok |\n"
            "| Nome · `nome` | nome civil | livre | varchar(120) · sim · — | pessoal (PII) | ok |\n\n"
            "## pedidos\nOrigem: ERP · Steward: financeiro · Atualização: transacional\n\n" + cab +
            "| Id · `id` | identificador | sequencial | int · sim · — | interna | ok |\n"
            "| Cliente · `cliente_id` | quem fez o pedido | fk | int · sim · — | interna | ok |\n"
            "| Total · `total` | valor do pedido | faixa | decimal(10,2) · sim · 0 | interna | ok |\n\n"
            "## itens do pedido\nOrigem: ERP · Steward: financeiro · Atualização: transacional\n\n" + cab +
            "| Pedido · `pedido_id` | pedido de origem | fk | int · sim · — | interna | ok |\n"
            "| SKU · `sku` | identificador do produto | livre | double  precision · sim · — | interna | ok |\n"
        )

        def roda_com_dicionario(dbml_txt, dm_txt, dic_txt):
            raiz = monta(perfil_obrig, dbml_txt, dm_txt)
            (raiz / DATA_DICTIONARY).write_text(dic_txt, encoding="utf-8")
            return checar(raiz, resolve_dbml(raiz, carrega_perfil(raiz), None))

        # zero achados, inclusive o espaço interno duplo de "double  precision" (sku) vs "double precision" (.dbml)
        assert roda_com_dicionario(dbml, dm_limpo, dic_ok) == [], f"fixture M4 limpa: {roda_com_dicionario(dbml, dm_limpo, dic_ok)}"

        r = roda_com_dicionario(dbml, dm_limpo, dic_ok.replace("## clientes\n", "## fantasma\n", 1))
        assert sevs(r) == ["ALTO:M4", "ALTO:M4"] and any("sem seção" in x[2] for x in r) and any("sem `Table`" in x[2] for x in r), \
            f"heading trocado no dicionário: órfão nos dois sentidos, M2 (data-model×dbml) intocado: {r}"

        sem_cliente_id = dic_ok.replace("| Cliente · `cliente_id` | quem fez o pedido | fk | int · sim · — | interna | ok |\n", "")
        r = roda_com_dicionario(dbml, dm_limpo, sem_cliente_id)
        assert sevs(r) == ["ALTO:M4"] and "cliente_id" in r[0][2] and "sem linha no dicionário" in r[0][2], f"coluna órfã: {r}"

        campo_fantasma = dic_ok.replace(
            "| Total · `total` | valor do pedido | faixa | decimal(10,2) · sim · 0 | interna | ok |\n",
            "| Total · `total` | valor do pedido | faixa | decimal(10,2) · sim · 0 | interna | ok |\n"
            "| Bonus · `bonus` | não existe no .dbml | livre | int · não · — | interna | ok |\n")
        r = roda_com_dicionario(dbml, dm_limpo, campo_fantasma)
        assert sevs(r) == ["ALTO:M4"] and "bonus" in r[0][2] and "sem coluna no .dbml" in r[0][2], f"campo órfão: {r}"

        tipo_divergente = dic_ok.replace("| Total · `total` | valor do pedido | faixa | decimal(10,2) · sim · 0 |",
                                          "| Total · `total` | valor do pedido | faixa | numeric(10,2) · sim · 0 |")
        r = roda_com_dicionario(dbml, dm_limpo, tipo_divergente)
        assert sevs(r) == ["ALTO:M4"] and "tipo divergente" in r[0][2], f"tipo divergente: {r}"

        campo_duplicado = dic_ok.replace(
            "| Id · `id` | identificador | sequencial | int · sim · — | interna | ok |\n",
            "| Id · `id` | identificador | sequencial | int · sim · — | interna | ok |\n"
            "| Id · `id` | identificador de novo | sequencial | int · sim · — | interna | ok |\n", 1)
        r = roda_com_dicionario(dbml, dm_limpo, campo_duplicado)
        assert sevs(r) == ["ALTO:M4"] and "duplicado" in r[0][2], f"campo duplicado: {r}"

        # sem .dbml, com data-model.md: continua acusando o artefato ausente (R99 sem mudança), sem M4
        raiz_sem_dbml = monta(perfil_obrig, None, dm_limpo)
        (raiz_sem_dbml / DATA_DICTIONARY).write_text(dic_ok, encoding="utf-8")
        r = checar(raiz_sem_dbml, resolve_dbml(raiz_sem_dbml, carrega_perfil(raiz_sem_dbml), None))
        assert len(r) == 1 and r[0][0] == "ALTO" and DBML_NOME in r[0][1], f"sem .dbml, com data-model: só o ALTO de artefato ausente, sem M4: {r}"

        # dicionário-only: nem .dbml nem data-model.md — MUDA R99 (R4)
        raiz_dic_only = monta(perfil_obrig, None, None)
        (raiz_dic_only / DATA_DICTIONARY).write_text(dic_ok, encoding="utf-8")
        r = checar(raiz_dic_only, resolve_dbml(raiz_dic_only, carrega_perfil(raiz_dic_only), None))
        assert r == [], f"dicionário-only limpo: zero achados de artefato ausente e M4/5/6 passam: {r}"

        # M1 com erro: M2, M3 e M4 todos se omitem (dependem do mesmo parse_dbml bem-sucedido)
        r = roda_com_dicionario("Table a {\n  id int\n", dm_limpo, dic_ok)
        assert [s for s, *_ in r] == ["ALTO"] and r[0][1] == "M1", f"M1 falho bloqueia M2/M3/M4: {r}"

        # --- M5: células decorativas (delta-075)
        dic_decorativo = dic_ok.replace("| Nome · `nome` | nome civil |", "| Nome · `nome` |  |", 1)
        r = roda_com_dicionario(dbml, dm_limpo, dic_decorativo)
        assert sevs(r) == ["ALTO:M5"] and "Definição vazia" in r[0][2], f"definição vazia: {r}"

        dic_placeholder = dic_ok.replace("| pessoal (PII) | ok |\n\n## pedidos", "| {{sensibilidade}} | ok |\n\n## pedidos", 1)
        r = roda_com_dicionario(dbml, dm_limpo, dic_placeholder)
        assert sevs(r) == ["ALTO:M5"] and "Sens. vazia" in r[0][2], f"placeholder cru em Sens.: {r}"

        dic_sem_steward = dic_ok.replace("Steward: vendas ·", "Steward:  ·", 1)
        r = roda_com_dicionario(dbml, dm_limpo, dic_sem_steward)
        assert sevs(r) == ["ALTO:M5"] and "Steward vazio" in r[0][2] and "clientes" in r[0][2], f"steward vazio: {r}"

        dic_duplicado = dic_ok + "\n## clientes\nOrigem: dup · Steward: dup · Atualização: dup\n"
        r = roda_com_dicionario(dbml, dm_limpo, dic_duplicado)
        assert sevs(r) == ["ALTO:M5"] and "duplicada" in r[0][2], f"entidade duplicada vira M5: {r}"

        # dicionário vazio, sem .dbml (senão M4 também acusa as 3 tabelas órfãs — ruído fora do que este caso testa)
        dic_vazio = "# Dicionário de dados\n<!-- nada ainda -->\n"
        raiz_vazio = monta(perfil_obrig, None, None)
        (raiz_vazio / DATA_DICTIONARY).write_text(dic_vazio, encoding="utf-8")
        r = checar(raiz_vazio, resolve_dbml(raiz_vazio, carrega_perfil(raiz_vazio), None))
        assert sevs(r) == ["ALTO:M5"] and "vazio" in r[0][2], f"dicionário sem entidade, sem .dbml: {r}"

        # --- M6: anti-tautologia, sempre BAIXO (delta-075)
        dic_tautologico = dic_ok.replace("| Id · `id` | identificador |", "| Id · `id` | id |", 1)
        r = roda_com_dicionario(dbml, dm_limpo, dic_tautologico)
        assert sevs(r) == ["BAIXO:M6"] and "tautológica" in r[0][2], f"definição == físico: {r}"

        dic_tautologico_canonico = dic_ok.replace(
            "| Nome · `nome` | nome civil | livre |", "| Nome · `nome` | Nome | livre |", 1)
        r = roda_com_dicionario(dbml, dm_limpo, dic_tautologico_canonico)
        assert sevs(r) == ["BAIXO:M6"], f"definição == canônico (maiúscula) também acusa: {r}"

        dic_confianca_ok = dic_ok.replace(
            "| Nome · `nome` | nome civil |", "| Nome · `nome` | [confirmado] nome civil |", 1)
        assert roda_com_dicionario(dbml, dm_limpo, dic_confianca_ok) == [], "prefixo de confiança não conta como tautologia"

        # --- M7: célula marcada [lacuna], sempre BAIXO (delta-095)
        dic_lacuna = dic_ok.replace("| Nome · `nome` | nome civil |", "| Nome · `nome` | [lacuna] |", 1)
        r = roda_com_dicionario(dbml, dm_limpo, dic_lacuna)
        assert sevs(r) == ["BAIXO:M7"] and "Definição" in r[0][2], f"[lacuna] na Definição vira pauta, não silêncio: {r}"

        # o prefixo com texto atrás continua sendo lacuna — o conteúdo não foi validado
        dic_lacuna_prefixo = dic_ok.replace(
            "| Nome · `nome` | nome civil |", "| Nome · `nome` | [lacuna] talvez o nome civil |", 1)
        r = roda_com_dicionario(dbml, dm_limpo, dic_lacuna_prefixo)
        assert sevs(r) == ["BAIXO:M7"], f"[lacuna] com texto atrás também é pauta: {r}"

        # M7 nunca bloqueia: dicionário 100% [lacuna] sai com achados e exit 0 (auditoria.md: "não é gate")
        dic_todo_lacuna = dic_ok
        for antes, depois in (("| nome civil |", "| [lacuna] |"), ("| identificador |", "| [lacuna] |")):
            dic_todo_lacuna = dic_todo_lacuna.replace(antes, depois)
        r = roda_com_dicionario(dbml, dm_limpo, dic_todo_lacuna)
        assert r and all(s == "BAIXO" for s, *_ in r), f"lacuna em massa nunca vira ALTO: {r}"
        assert not any(s == "ALTO" for s, *_ in r), "M5 não pode reclassificar [lacuna] como célula decorativa"

        # a fronteira com o M5: [lacuna] é honesto, célula vazia é esquecimento
        dic_vazia_vs_lacuna = dic_ok.replace("| Nome · `nome` | nome civil |", "| Nome · `nome` |  |", 1)
        r = roda_com_dicionario(dbml, dm_limpo, dic_vazia_vs_lacuna)
        assert sevs(r) == ["ALTO:M5"], f"célula vazia continua ALTO no M5, não vira M7: {r}"

        # [confirmado] e [inferido] não são lacuna
        for marca in ("[confirmado]", "[inferido]"):
            dic_marcado = dic_ok.replace("| Nome · `nome` | nome civil |", f"| Nome · `nome` | {marca} nome civil |", 1)
            assert roda_com_dicionario(dbml, dm_limpo, dic_marcado) == [], f"{marca} não é pauta de lacuna"

        # --- repos_com_dicionario (R9): reaproveita find_repo_roots/detect_mode do audit_workspace.py
        repo_unico = monta(perfil_obrig, dbml, dm_limpo)
        (repo_unico / ".git").mkdir()
        (repo_unico / DATA_DICTIONARY).write_text(dic_ok, encoding="utf-8")
        assert repos_com_dicionario(repo_unico) == [repo_unico], "modo repo, com dicionário → [base]"

        repo_sem_dic = monta(perfil_obrig, dbml, dm_limpo)
        (repo_sem_dic / ".git").mkdir()
        assert repos_com_dicionario(repo_sem_dic) == [], "modo repo, sem dicionário → []"

        ws = Path(tmp) / "workspace-fixture"
        (ws / "a" / ".git").mkdir(parents=True)
        (ws / "a" / DATA_DICTIONARY).write_text(dic_ok, encoding="utf-8")
        (ws / "b" / ".git").mkdir(parents=True)   # sem dicionário
        assert repos_com_dicionario(ws) == [ws / "a"], "modo workspace filtra só quem tem DATA_DICTIONARY.md"

        vazio_sem_git = Path(tmp) / "nem-repo-nem-workspace"
        vazio_sem_git.mkdir()
        assert repos_com_dicionario(vazio_sem_git) == [], "sem .git e sem subpastas git → []"

        saida = io.StringIO()
        with contextlib.redirect_stdout(saida):
            codigo = relatorio(roda(perfil_obrig, dbml, dm_limpo.replace("### pedidos\n", "")), "demo")
        assert codigo == 1 and "| 1 | ALTO | M2 |" in saida.getvalue() and "**Veredito:** LIBERADO COM RESSALVAS" in saida.getvalue()
        with contextlib.redirect_stdout(io.StringIO()):
            assert relatorio([], "demo") == 0

    # --- parse_dicionario: subconjunto do R1/R2
    dic_bruto = '''# Dicionário de dados
<!-- comentário de cabeçalho -->

## clientes
Origem: CRM · Steward: time de vendas · Atualização: transacional

| Campo (canônico · físico) | Definição de negócio | Domínio de valores | Tipo · obrig. · default | Sens. | Qualidade |
| --- | --- | --- | --- | --- | --- |
| Nome · `nome` | [confirmado] nome civil completo | livre | varchar(120) · sim · — | pessoal (PII) | não vazio |
| Id · `id` | identificador único do cliente | sequencial | int · sim · — | interna | chave primária |

## pedidos
Origem: ERP · Steward: {{papel/pessoa}} · Atualização: transacional

| Campo (canônico · físico) | Definição de negócio | Domínio de valores | Tipo · obrig. · default | Sens. | Qualidade |
| --- | --- | --- | --- | --- | --- |
| Cliente | `cliente_id` | quem fez o pedido | fk \\| interno | int · sim · — | interna | referencia clientes.id |
| Total · `total` | | faixa 0-100000 | decimal(10,2) · sim · 0 | interna | nunca negativo |

## Contratos entre módulos
- exemplo mantido do template legado

## clientes
Origem: duplicata · Steward: x · Atualização: x
'''
    d = parse_dicionario(dic_bruto)
    assert set(d.entidades) == {"clientes", "pedidos"}, set(d.entidades)
    assert d.entidades["clientes"].origem == "CRM" and d.entidades["clientes"].steward == "time de vendas"
    assert d.entidades["clientes"].atualizacao == "transacional"
    assert len(d.entidades["clientes"].campos) == 2, d.entidades["clientes"].campos
    nome = d.entidades["clientes"].campos[0]
    assert nome.canonico == "Nome" and nome.fisico == "nome" and nome.definicao == "[confirmado] nome civil completo"
    assert nome.tipo == "varchar(120)" and nome.obrigatorio == "sim" and nome.default == "—"
    assert nome.sensibilidade == "pessoal (PII)" and nome.qualidade == "não vazio"
    assert len(d.entidades["pedidos"].campos) == 1, "linha 'Cliente' tem 7 células (erro de autor) — descartada em silêncio"
    total = d.entidades["pedidos"].campos[0]
    assert total.fisico == "total" and total.definicao == "", "célula vazia vira string vazia, não erro"
    assert d.entidades["pedidos"].steward == "{{papel/pessoa}}", "placeholder cru sobrevive ao parse (M5 decide)"
    linhas_dup = [l for l, _ in d.erros]
    assert len(d.erros) == 1 and "clientes" in d.erros[0][1], f"segunda '## clientes' deve virar erro: {d.erros}"
    assert linhas_dup[0] > 15, "linha do erro deve ser a da segunda ocorrência, não a primeira"

    vazio = parse_dicionario("# Dicionário\n\n## Contratos entre módulos\n- nada\n")
    assert vazio.entidades == {} and vazio.erros == [], "só 'Contratos entre módulos' → zero entidades, sem erro"

    escapado = parse_dicionario(
        "## a\nOrigem: x · Steward: y · Atualização: z\n\n"
        "| Campo (canônico · físico) | Definição de negócio | Domínio de valores | Tipo · obrig. · default | Sens. | Qualidade |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
        "| Nome · `nome` | domínio a\\|b\\|c | a\\|b\\|c | varchar · sim · — | interna | ok |\n"
    )
    campo = escapado.entidades["a"].campos[0]
    assert campo.definicao == "domínio a|b|c" and campo.dominio == "a|b|c", f"pipe escapado deve desescapar: {campo}"

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
