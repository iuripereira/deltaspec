#!/usr/bin/env python3
"""Registro de perguntas da descoberta — uma por arquivo (QT-NNN), índice gerado.

Molde do `debts/` (debito.py da skill handoff): cada pergunta vive em
`docs/discovery/questions/QUESTAO_QT-NNN-<topico>.md` com frontmatter flat, e
`docs/discovery/questions.md` é a projeção gerada por `indice` — nunca editada à mão.
Gramática e ritual: references/questoes.md desta skill; decisão: ADR-0054.

  novo     cadastra uma pergunta (o ID sai do maior QT existente + 1)
  indice   valida o registro e reescreve docs/discovery/questions.md
  migrar   converte o questions.md monolítico (`### B4 · … — 🔴 Alta · ✅ respondida`) no
           layout de pastas, lendo do git a data de abertura, a de resposta e a release

A tabela `## Visão geral` do índice (ID · Tema · Dono · Prioridade · Status) é contrato com
os relatórios de status do portfólio, que a leem de cada produto — não mude as colunas.

Uso: questao.py novo [ROOT] --descricao T --para P --prioridade {alta,media,baixa}
                         [--codigo C] [--refs "RF-110, RN-116"] [--corpo-arquivo F]
     questao.py indice [ROOT]
     questao.py migrar [ROOT] [--dry-run]
     questao.py --selftest
Exit 0 = ok · 1 = registro inválido · 2 = erro de uso.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import unicodedata
from collections import Counter
from datetime import date
from pathlib import Path

INDICE = "docs/discovery/questions.md"
DIR_ITENS = "docs/discovery/questions"
# Como o script se cita nos textos que gera: pelo nome e pela skill, nunca por caminho de máquina.
CMD = "questao.py"
SKILL = "deltaspec:descoberta"
NOME_ITEM = re.compile(r"^QUESTAO_(QT-\d{3})-[a-z0-9][a-z0-9-]*\.md$")
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n?", re.S)
FM_CHAVE = re.compile(r"^([a-z]+):[ \t]*(.*?)[ \t]*$", re.M)
TITULO = re.compile(r"^#\s+\[(QT-\d{3})\]\s+-\s+(.*?)\s*$", re.M)

ESTADOS = ("aberta", "parcial", "respondida")
PRIORIDADES = ("alta", "media", "baixa")
GLIFO_PRIO = {"alta": "🔴 Alta", "media": "🟡 Média", "baixa": "🟢 Baixa"}
GLIFO_ESTADO = {"aberta": "⬜", "parcial": "🔶", "respondida": "✅"}
# Mapas inversos e alternâncias de regex derivados dos dois dicionários acima — mudar glifo é breaking
# (contrato do índice), então ele vive num lugar só.
PRIO_DE_GLIFO = {v[0]: k for k, v in GLIFO_PRIO.items()}
ESTADO_DE_GLIFO = {v: k for k, v in GLIFO_ESTADO.items()}
GLIFOS_PRIO = "|".join(PRIO_DE_GLIFO)
GLIFOS_ESTADO = "|".join(ESTADO_DE_GLIFO)
GLIFO_ESTADO_RE = re.compile(f"({GLIFOS_ESTADO})")
GLIFO_PRIO_RE = re.compile(f"({GLIFOS_PRIO})")

# Frontmatter: chaves ASCII, valores livres, parser por regex (não YAML — `estado: no`
# viraria False). Todas as chaves são sempre escritas, vazias quando não se aplicam.
FM_ORDEM = ("id", "codigo", "estado", "prioridade", "descricao", "para", "respondeu",
            "aberto", "respondido", "release", "refs")
FM_OBRIGATORIAS = ("id", "estado", "prioridade", "descricao", "para", "aberto")

# IDs citáveis que o framework governa, no título e no corpo — a "relação com RF/RN/spec".
# ID local de um projeto (decisão diferida do PRD, divergência numerada) fica no corpo (ADR-0054).
REF = re.compile(r"\b(?:RF|RNF|RN|ADR|DT)-\d+(?:\.[0-9a-z]+)*|\bdelta-\d{3}\b|specs/(?:_archive/)?(\d{3})-")
ORDEM_REF = ("RF", "RNF", "RN", "ADR", "delta", "DT")

# Link markdown (inclui imagem); alvo sem espaço, título opcional entre aspas.
LINK = re.compile(r"(!?\[[^\]]*\]\()([^)\s]+)((?:\s+\"[^\"]*\")?\))")
ALVO_EXTERNO = ("http://", "https://", "#", "mailto:")
CODE_SPAN = re.compile(r"`[^`]*`")

# --- legado: questions.md monolítico ---------------------------------------------------
# Código de época: `B4`, `T7`, `GQ10`, `NQ7`, `V-B1` — uma ou duas letras, hífen opcional, dígitos.
CODIGO = r"[A-Z]{1,2}(?:-[A-Z]{1,2})?\d{1,3}"
CAB_LEGADO = re.compile(
    rf"^### ({CODIGO}) · (.*?)\s+—\s+({GLIFOS_PRIO})\s*\S+\s*·\s*({GLIFOS_ESTADO})\s*\S+(.*)$", re.M)
# Células com padding livre: formatador de markdown alinha as colunas com espaços.
LINHA_TABELA = re.compile(rf"^\|\s*({CODIGO})\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*$", re.M)
SECAO = re.compile(r"^## (.+)$", re.M)
# No `git log -p`: cabeçalho adicionado (com o estado) e linha de tabela adicionada (com o estado
# na última célula) — a transição para ✅ conta vinda de qualquer um dos dois.
ADD_CAB = re.compile(rf"^\+###\s+({CODIGO})\b.*?({GLIFOS_ESTADO})")
ADD_TAB = re.compile(rf"^\+\|\s*({CODIGO})\s*\|(.*)$")
FONTES_LEGADO = ("tabela", "cabecalho")
# Rótulo de resposta no corpo: `**Resposta (14/08, Nome — …).**`, `**Decisão do PO (01/11).**`,
# `**Resposta (2026-08-13, Nome/PO, gate):**`.
ROTULO_RESPOSTA = re.compile(r"^\*\*(Resposta|Decis[ãa]o[^(*]*|Dire[çc][ãa]o)\s*\((.*?)\)[.:]?\*\*", re.M)
DATA_BR = re.compile(r"\b(\d{1,2})/(\d{2})(?:/(\d{4}))?\b")
DATA_ISO_SOLTA = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
# Autor = primeiro segmento depois da data, até um separador; aceito só se parece nome: palavras
# capitalizadas, partículas (de/da/do/das/dos/e), iniciais com ponto, ou o papel padrão.
# ponytail: heurística sem dicionário — "e-mail", "formulário", "PRD v3" saem sem autor e viram aviso;
# nome fora desse molde se preenche à mão em `respondeu:`.
AUTOR_PADRAO_DECISAO = "PO"  # decisão/direção sem ninguém depois da data é do PO
SEPARADOR_AUTOR = re.compile(r"\s+—\s+|\s+-\s+|\s*[,/;:()]\s*")
PALAVRA_NOME = re.compile(rf"^(?:{AUTOR_PADRAO_DECISAO}|d[aeo]s?|e|[A-ZÀ-Ý][a-zà-ÿ]*\.?)$")


def die(msg: str) -> None:
    print(f"ERRO: {msg}", file=sys.stderr)
    sys.exit(2)


def _ascii(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()


def slug(texto: str, max_palavras: int = 6) -> str:
    """kebab-case ASCII do título — vira o <topico> do nome do arquivo (regra do debito.py)."""
    palavras = re.sub(r"[^a-z0-9]+", " ", _ascii(texto).lower()).split()
    return "-".join(palavras[:max_palavras]) or "sem-titulo"


def parse_frontmatter(texto: str) -> tuple[dict[str, str], str]:
    m = FRONTMATTER.match(texto)
    if not m:
        return {}, texto
    return {k: v for k, v in FM_CHAVE.findall(m.group(1))}, texto[m.end():]


def serializa(fm: dict[str, str], corpo: str) -> str:
    linhas = ["---", *(f"{k}: {fm.get(k, '')}".rstrip() for k in FM_ORDEM), "---", "",
              f"# [{fm['id']}] - {fm['descricao']}", "", corpo.strip("\n"), ""]
    return "\n".join(linhas)


def nome_item(fm: dict[str, str]) -> str:
    return f"QUESTAO_{fm['id']}-{slug(fm['descricao'])}.md"


def _chave_ref(r: str):
    tipo, _, resto = r.partition("-")
    partes = tuple((0, int(p)) if p.isdigit() else (1, p) for p in resto.split("."))
    return (ORDEM_REF.index(tipo) if tipo in ORDEM_REF else 99, partes)


def extrair_refs(texto: str) -> list[str]:
    achados = {f"delta-{m.group(1)}" if m.group(1) else m.group(0) for m in REF.finditer(texto)}
    return sorted(achados, key=_chave_ref)


def reescreve_links(texto: str) -> str:
    """Alvo relativo escrito para resolver de docs/discovery/ ganha um nível (o item vive em questions/)."""
    def repl(m: re.Match) -> str:
        alvo = m.group(2)
        if alvo.startswith(ALVO_EXTERNO):
            return m.group(0)
        return f"{m.group(1)}../{alvo}{m.group(3)}"
    return LINK.sub(repl, texto)


def links_quebrados(texto: str, base: Path) -> list[str]:
    """Alvos relativos que não existem no disco — o consumidor costuma excluir docs/discovery do C3
    do validate_integrity, então a conferência é daqui."""
    fora = []
    for m in LINK.finditer(CODE_SPAN.sub("", texto)):  # `[x](y.md)` em crase é sintaxe citada
        alvo = m.group(2)
        if alvo.startswith(ALVO_EXTERNO):
            continue
        caminho = alvo.split("#", 1)[0]
        # normpath lexical: `base` pode ainda não existir (dry-run) e `..` não resolveria
        if caminho and not Path(os.path.normpath(base / caminho)).exists():
            fora.append(alvo)
    return fora


# --- registro -------------------------------------------------------------------------
def ler_registro(root: Path) -> tuple[list[dict], list[str]]:
    """Itens de DIR_ITENS ordenados por id + lista de violações (vazia = registro íntegro)."""
    itens, erros, vistos, codigos = [], [], set(), set()
    pasta = root / DIR_ITENS
    for arq in sorted(pasta.glob("QUESTAO_QT-*.md")) if pasta.is_dir() else []:
        m = NOME_ITEM.match(arq.name)
        if not m:
            erros.append(f"{arq.name}: nome fora de QUESTAO_QT-NNN-<topico>.md")
            continue
        texto = arq.read_text(encoding="utf-8")
        fm, corpo = parse_frontmatter(texto)
        ident = m.group(1)
        if fm.get("id") != ident:
            erros.append(f"{arq.name}: id do frontmatter ({fm.get('id')}) difere do nome ({ident})")
        if ident in vistos:
            erros.append(f"{ident}: id duplicado")
        vistos.add(ident)
        for k in FM_OBRIGATORIAS:
            if not fm.get(k):
                erros.append(f"{ident}: frontmatter sem `{k}`")
        if fm.get("estado") not in ESTADOS:
            erros.append(f"{ident}: estado `{fm.get('estado')}` fora de {ESTADOS}")
        if fm.get("prioridade") not in PRIORIDADES:
            erros.append(f"{ident}: prioridade `{fm.get('prioridade')}` fora de {PRIORIDADES}")
        for k in ("aberto", "respondido"):
            if fm.get(k):
                try:
                    date.fromisoformat(fm[k])
                except ValueError:
                    erros.append(f"{ident}: `{k}` não é uma data AAAA-MM-DD ({fm[k]})")
        if fm.get("estado") == "respondida" and not fm.get("respondido"):
            erros.append(f"{ident}: respondida sem `respondido`")
        t = TITULO.search(corpo)
        if not t or t.group(1) != ident or t.group(2) != fm.get("descricao"):
            erros.append(f"{ident}: título do corpo deve ser `# [{ident}] - {fm.get('descricao')}`")
        if "|" in fm.get("descricao", ""):
            erros.append(f"{ident}: descricao com `|` quebra a tabela Visão geral")
        if fm.get("codigo"):
            if fm["codigo"] in codigos:
                erros.append(f"{ident}: codigo `{fm['codigo']}` duplicado")
            codigos.add(fm["codigo"])
        itens.append({**fm, "arquivo": arq.name, "corpo": corpo})
    return sorted(itens, key=lambda i: i.get("id", "")), erros


def proximo_id(root: Path) -> str:
    pasta = root / DIR_ITENS
    nums = [int(m.group(1)[3:]) for a in (pasta.glob("QUESTAO_QT-*.md") if pasta.is_dir() else [])
            if (m := NOME_ITEM.match(a.name))]
    return f"QT-{(max(nums) + 1 if nums else 1):03d}"


def _tema(i: dict) -> str:
    return f"{i['codigo']} · {i['descricao']}" if i.get("codigo") else i["descricao"]


def _onde(i: dict) -> str:
    r = i.get("release", "")
    if r == "develop":
        return "develop (sem release)"
    return f"main ({r})" if r else "fora da develop"


def render_indice(itens: list[dict], hoje: date) -> str:
    n = Counter(i["estado"] for i in itens)
    pasta = DIR_ITENS.rsplit("/", 1)[-1]
    out = [
        "# Perguntas da descoberta — índice gerado",
        f"<!-- GERADO por {CMD} indice (skill {SKILL}) — não edite à mão; regenere após cadastrar/responder.",
        f"     Fonte: {DIR_ITENS}/ · contrato: a tabela Visão geral é lida pelos relatórios de status do portfólio -->",
        "",
        f"> Registro canônico em [{pasta}/]({pasta}/), uma pergunta por arquivo. Pergunta nova: `{CMD} novo .`; "
        f"resposta: no arquivo da pergunta, depois `{CMD} indice .`. Gramática e ritual: skill `{SKILL}`. "
        "Os códigos de época (`B4`, `GQ10`…) seguem citáveis — vivem em `codigo:` e na coluna Tema.",
        "",
        f"**{len(itens)} perguntas** · ✅ respondidas {n['respondida']} · 🔶 parciais {n['parcial']} · "
        f"⬜ abertas {n['aberta']} · atualizado em {hoje.isoformat()}",
        "",
        "## Visão geral",
        "",
        "| ID | Tema | Dono | Prioridade | Status |",
        "|---|---|---|---|---|",
        *(f"| {i['id']} | {_tema(i)} | {i['para']} | {GLIFO_PRIO[i['prioridade']]} | {GLIFO_ESTADO[i['estado']]} |"
          for i in itens),
        "",
        "## Pendentes",
        "",
        "Abertas e parciais, por prioridade — refs são os RF/RN/ADR/DT/deltas citados no título e no corpo "
        "(o DT, quando há, é quem descreve o que a resposta destrava).",
    ]
    pend = [i for i in itens if i["estado"] != "respondida"]
    resp = [i for i in itens if i["estado"] == "respondida"]
    for p in PRIORIDADES:
        grupo = [i for i in pend if i["prioridade"] == p]
        if grupo:
            out += ["", f"### {GLIFO_PRIO[p]}"]
            out += [f"- [{i['id']}]({pasta}/{i['arquivo']}) — {_tema(i)} — {GLIFO_ESTADO[i['estado']]} "
                    f"{i['estado']} · para {i['para']} · aberta em {i['aberto']}"
                    + (f" · {i['refs']}" if i.get("refs") else "") for i in grupo]
    out += ["", "## Respondidas", "",
            "Por prioridade — quem respondeu e quando, o que a resposta destravou (refs) e onde a resposta "
            "está integrada: `main (vX.Y.Z)` é a release que a levou à main, `develop` ainda sem release."]
    for p in PRIORIDADES:
        grupo = [i for i in resp if i["prioridade"] == p]
        if grupo:
            out += ["", f"### {GLIFO_PRIO[p]}"]
            out += [f"- [{i['id']}]({pasta}/{i['arquivo']}) — {_tema(i)} — "
                    f"{i.get('respondeu') or 'sem autor registrado'} em {i['respondido']}"
                    + (f" · {i['refs']}" if i.get("refs") else "") + f" · {_onde(i)}" for i in grupo]
    return "\n".join(out) + "\n"


# --- comandos -------------------------------------------------------------------------
def cmd_indice(root: Path) -> int:
    itens, erros = ler_registro(root)
    if erros:
        print("\n".join(erros), file=sys.stderr)
        return 1
    (root / INDICE).write_text(render_indice(itens, date.today()), encoding="utf-8")
    print(f"{INDICE}: {len(itens)} perguntas")
    return 0


def cmd_novo(root: Path, a: argparse.Namespace) -> int:
    corpo = ""
    if a.corpo_arquivo:
        corpo = Path(a.corpo_arquivo).read_text(encoding="utf-8")
    elif not sys.stdin.isatty():  # ponytail: stdin herdado e aberto sem escritor bloqueia aqui — use --corpo-arquivo
        corpo = sys.stdin.read()
    if not corpo.strip():
        corpo = f"**Pergunta:** {a.descricao}"
    fm = {"id": proximo_id(root), "codigo": a.codigo or "", "estado": "aberta", "prioridade": a.prioridade,
          "descricao": a.descricao.strip(), "para": a.para.strip(), "aberto": date.today().isoformat(),
          "refs": ", ".join(extrair_refs("\n".join((a.refs or "", a.descricao, corpo))))}
    pasta = root / DIR_ITENS
    pasta.mkdir(parents=True, exist_ok=True)
    destino = pasta / nome_item(fm)
    destino.write_text(serializa(fm, corpo), encoding="utf-8")
    print(f"{destino.relative_to(root)} — agora: {CMD} indice .")
    return 0


# --- migração -------------------------------------------------------------------------
def _celula_tabela(tema: str, dono: str, prio: str, status: str) -> dict:
    p, s = GLIFO_PRIO_RE.search(prio), GLIFO_ESTADO_RE.search(status)
    return {"tema": tema.strip(), "dono": dono.replace("**", "").strip(),
            "prioridade": PRIO_DE_GLIFO[p.group(1)] if p else "", "estado": ESTADO_DE_GLIFO[s.group(1)] if s else ""}


def parse_legado(texto: str) -> tuple[str, dict[str, dict], dict[str, str], list[dict]]:
    """(intro antes de '## Visão geral', tabela codigo→{tema, dono, prioridade, estado},
    preâmbulo por seção, perguntas)."""
    i_visao = texto.index("\n## Visão geral")
    intro = texto[:i_visao].strip("\n")
    tabela = {m.group(1): _celula_tabela(*m.group(2, 3, 4, 5)) for m in LINHA_TABELA.finditer(texto)}
    secoes = list(SECAO.finditer(texto))
    preambulos, perguntas = {}, []
    for k, s in enumerate(secoes):
        fim = secoes[k + 1].start() if k + 1 < len(secoes) else len(texto)
        bloco = texto[s.end():fim]
        if s.group(1).startswith("Visão geral"):
            continue
        cabs = list(CAB_LEGADO.finditer(bloco))
        pre = bloco[:cabs[0].start()] if cabs else bloco
        if pre.strip():
            preambulos[s.group(1)] = pre.strip("\n")
        for j, m in enumerate(cabs):
            fim_c = cabs[j + 1].start() if j + 1 < len(cabs) else len(bloco)
            perguntas.append({
                "codigo": m.group(1), "titulo": m.group(2).strip(), "secao": s.group(1),
                "prioridade": PRIO_DE_GLIFO[m.group(3)], "estado": ESTADO_DE_GLIFO[m.group(4)],
                "sufixo": m.group(5).strip(), "corpo": bloco[m.end():fim_c].strip("\n"),
            })
    return intro, tabela, preambulos, perguntas


def _git(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True).stdout


def historico_git(root: Path) -> tuple[dict[str, str], dict[str, tuple[str, str]]]:
    """aberto[codigo] = data da primeira aparição; resposta[codigo] = (sha, data) da transição
    para ✅ no cabeçalho ou na linha da tabela. Cada fonte guarda o próprio estado, e a transição
    só conta quando nenhuma das duas já dizia ✅: a tabela completada depois de o cabeçalho já
    estar ✅ (ou a linha ✅ reescrita) não é resposta nova; cabeçalho ⬜ que fica para trás não
    reabre a pergunta. Reaberta nas duas fontes e respondida de novo fica com a transição nova."""
    saida = _git(root, "log", "-p", "--reverse", "--date=short", "--format=COMMIT %H %ad", "--", INDICE)
    aberto, estado, resposta = {}, {}, {}
    sha = data = ""

    def transicao(fonte: str, cod: str, glifo: str) -> None:
        novo = ESTADO_DE_GLIFO[glifo]
        if novo == "respondida" and not any(estado.get((f, cod)) == "respondida" for f in FONTES_LEGADO):
            resposta[cod] = (sha, data)
        estado[(fonte, cod)] = novo

    for linha in saida.splitlines():
        if linha.startswith("COMMIT "):
            _, sha, data = linha.split(" ", 2)
            continue
        if (t := ADD_TAB.match(linha)):
            aberto.setdefault(t.group(1), data)
            glifos = GLIFO_ESTADO_RE.findall(t.group(2))
            if glifos:
                transicao("tabela", t.group(1), glifos[-1])
            continue
        if (c := ADD_CAB.match(linha)):
            aberto.setdefault(c.group(1), data)
            transicao("cabecalho", c.group(1), c.group(2))
    return aberto, resposta


def release_de(root: Path, sha: str) -> str:
    """Tag mais antiga que contém o commit (= release que o levou à main); `develop` se só está
    lá; vazio se ainda está numa branch."""
    tags = _git(root, "tag", "--contains", sha, "--sort=v:refname").split()
    if tags:
        return tags[0]
    ramos = set(_git(root, "branch", "-a", "--contains", sha, "--format=%(refname:short)").split())
    return "develop" if ramos & {"develop", "origin/develop"} else ""


def segmento_autor(resto: str) -> str:
    """Primeiro segmento do rótulo depois da data, até um separador — o candidato a autor."""
    return SEPARADOR_AUTOR.split(resto.strip(" ,;:—-"), 1)[0].strip()


def autor_do_rotulo(resto: str) -> str:
    """O candidato, se parece nome de pessoa (ou o papel padrão); senão vazio."""
    segmento = segmento_autor(resto)
    palavras = segmento.split()
    return segmento if palavras and all(PALAVRA_NOME.match(p) for p in palavras) else ""


def parse_resposta(corpo: str, ano_padrao: str) -> tuple[str, str]:
    """(data ISO, quem) do último rótulo de resposta/decisão do corpo; vazios se não há rótulo."""
    rotulos = ROTULO_RESPOSTA.findall(corpo)
    if not rotulos:
        return "", ""
    tipo, conteudo = rotulos[-1]
    data, fim = "", 0
    if (d := DATA_BR.search(conteudo)):
        data, fim = f"{d.group(3) or ano_padrao}-{int(d.group(2)):02d}-{int(d.group(1)):02d}", d.end()
    elif (d := DATA_ISO_SOLTA.search(conteudo)):
        data, fim = d.group(0), d.end()
    resto = conteudo[fim:]
    quem = autor_do_rotulo(resto)
    if not quem and not tipo.startswith("Resposta") and not segmento_autor(resto):
        quem = AUTOR_PADRAO_DECISAO  # segmento rejeitado NÃO cai aqui: sai sem autor e vira aviso
    return data, quem


README_CABECALHO = f"""# questions/ — registro das perguntas da descoberta

> Uma pergunta por arquivo (`QUESTAO_QT-NNN-<topico>.md`), no molde do `debts/`: frontmatter flat, corpo em prosa com notas datadas, índice gerado em [../questions.md](../questions.md) por `{CMD} indice .` — nunca editado à mão. Nenhuma pergunta é apagada: a trajetória (contexto → avanços → resposta) é o registro, e o `git log -p` do arquivo é o histórico. Gramática do frontmatter, ritual (nova → resposta → índice) e regras da migração: `references/questoes.md` da skill `{SKILL}`.

## Migração de {{hoje}}

Os arquivos nasceram do `questions.md` monolítico por `{CMD} migrar .` (regras: `references/questoes.md` da skill `{SKILL}`). Abaixo, o cabeçalho e as notas de rodada do arquivo antigo, preservados como vieram.
"""


def migrar(root: Path, hoje: str) -> tuple[list[tuple[dict, str]], list[str], list[str], str]:
    """(itens (frontmatter, corpo), avisos, links sem alvo, texto do README) — lê git, não escreve."""
    origem = root / INDICE
    texto = origem.read_text(encoding="utf-8")
    if "## Visão geral" not in texto or not CAB_LEGADO.search(texto):
        die(f"{INDICE} não está no formato legado (sem '## Visão geral' ou sem cabeçalhos '### B4 · …')")
    intro, tabela, preambulos, perguntas = parse_legado(texto)
    faltam = [p["codigo"] for p in perguntas if p["codigo"] not in tabela]
    if faltam:
        die(f"perguntas sem linha na Visão geral: {faltam} — complete a tabela antes de migrar")
    aberto, resposta = historico_git(root)
    ordem = sorted(perguntas, key=lambda p: aberto.get(p["codigo"], hoje))  # sort estável: empate = ordem do arquivo

    pasta = root / DIR_ITENS
    avisos, quebrados, itens = [], [], []
    so_na_tabela = sorted(set(tabela) - {p["codigo"] for p in perguntas})
    avisos += [f"{cod}: linha na Visão geral sem cabeçalho `###` — não migrada" for cod in so_na_tabela]
    for n, p in enumerate(ordem, 1):
        cod, t = p["codigo"], tabela[p["codigo"]]
        for campo in ("estado", "prioridade"):
            if not t[campo]:
                avisos.append(f"{cod}: tabela sem glifo de {campo} — usando o cabeçalho")
            elif t[campo] != p[campo]:
                avisos.append(f"{cod}: {campo} do cabeçalho ({p[campo]}) difere da tabela ({t[campo]}) — vale a tabela")
        estado, prio = t["estado"] or p["estado"], t["prioridade"] or p["prioridade"]
        sha, data_git = resposta.get(cod, ("", ""))
        data_resp, quem, release = "", "", ""
        if estado == "respondida":
            data_resp, quem = parse_resposta(p["corpo"], (data_git or hoje)[:4])
            data_resp = data_resp or data_git
            release = release_de(root, sha) if sha else ""
            if not data_resp:
                avisos.append(f"{cod}: respondida sem data (nem rótulo, nem transição no git)")
            if not quem:
                avisos.append(f"{cod}: respondida sem autor identificável no rótulo — preencha `respondeu:`")
        corpo_linhas = []
        if t["tema"] != p["titulo"]:
            corpo_linhas.append(f"**Pergunta:** {t['tema']}")
        if p["sufixo"]:
            corpo_linhas.append(f"**Estado:** {estado} {p['sufixo']}")
        corpo = "\n\n".join([*corpo_linhas, reescreve_links(p["corpo"])])
        fm = {"id": f"QT-{n:03d}", "codigo": cod, "estado": estado, "prioridade": prio,
              "descricao": p["titulo"], "para": t["dono"], "respondeu": quem,
              "aberto": aberto.get(cod, hoje), "respondido": data_resp, "release": release,
              "refs": ", ".join(extrair_refs(p["titulo"] + "\n" + p["corpo"]))}
        quebrados += [f"{fm['id']} ({cod}): {a}" for a in links_quebrados(corpo, pasta)]
        itens.append((fm, corpo))

    readme = [README_CABECALHO.replace("{hoje}", hoje), "## Cabeçalho e notas de rodada do arquivo antigo",
              "", reescreve_links(intro)]
    for secao, pre in preambulos.items():
        readme += ["", f"### Seção «{secao}»", "", reescreve_links(pre)]
    readme_txt = "\n".join(readme) + "\n"
    quebrados += [f"README: {a}" for a in links_quebrados(readme_txt, pasta)]
    return itens, avisos, quebrados, readme_txt


def cmd_migrar(root: Path, dry: bool) -> int:
    itens, avisos, quebrados, readme_txt = migrar(root, date.today().isoformat())
    print(f"{len(itens)} perguntas · {len(avisos)} avisos · {len(quebrados)} links sem alvo")
    for a in avisos + quebrados:
        print("  " + a)
    if dry:
        for fm, _ in itens:
            print(f"{fm['id']} {fm['codigo']:<5} {fm['estado']:<10} {fm['aberto']} {fm['respondido'] or '':<10} "
                  f"{fm['release'] or '':<9} {fm['respondeu'] or '':<20} {fm['descricao'][:60]}")
        return 0
    pasta = root / DIR_ITENS
    pasta.mkdir(parents=True, exist_ok=True)
    for fm, corpo in itens:
        (pasta / nome_item(fm)).write_text(serializa(fm, corpo), encoding="utf-8")
    (pasta / "README.md").write_text(readme_txt, encoding="utf-8")
    return cmd_indice(root)


# --- selftest -------------------------------------------------------------------------
# Fixture pseudonimizada: nome de pessoa ou de organização real não entra no plugin (ADR-0036).
LEGADO_V1 = """# Perguntas

Intro [dossiê](2026-07-27-kickoff.md).

> **Revisão de 01/08** — nota de rodada.

## Visão geral

| ID | Tema | Dono | Prioridade | Status |
| --- | --- | --- | --- | --- |
| B4 | Escopo do MVP: reposição primeiro? | Ana | 🔴 Alta | ⬜ |
| V-B1 | Acesso às bases (OQ-14) | Carla → **Davi** | 🔴 Alta | ⬜ |

---

## Ana — gerente

### B4 · Escopo do MVP — 🔴 Alta · ⬜ aberta (para o MVP)

**Pergunta.** Começamos só com reposição (RF-105)?

## Carla — dados

> Nota da seção.

### V-B1 · Acesso às bases (OQ-14) — 🔴 Alta · ⬜ aberta

**Perguntas.** Quem libera? Ver DT-039 e https://example.com/x.
"""

LEGADO_V2 = LEGADO_V1.replace(
    "| B4 | Escopo do MVP: reposição primeiro? | Ana | 🔴 Alta | ⬜ |",
    "| B4 | Escopo do MVP: reposição primeiro? | Ana | 🔴 Alta | ✅ |\n"
    "| GQ10 | Referência cruzada quebrada | Qualidade | 🟡 Média | ✅ |",
).replace(
    "### B4 · Escopo do MVP — 🔴 Alta · ⬜ aberta (para o MVP)\n\n**Pergunta.** Começamos só com reposição (RF-105)?",
    "### B4 · Escopo do MVP — 🔴 Alta · ✅ respondida (para o MVP)\n\n**Pergunta.** Começamos só com reposição (RF-105)?"
    "\n\n**Resposta (04/08, Ana — decisão de escopo).** Entra como variável — [RN-111](../prd-v2-proposta.md) "
    "e [specs](../../specs/_archive/001-ingestao/).",
).replace(
    "## Carla — dados",
    "## Atualizações da reunião de 2026-08-09\n\nFonte: dossiê.\n\n"
    "### GQ10 · Referência cruzada quebrada — 🔴 Alta · ⬜ aberta\n\n**Contexto.** O §8.4.3 não existe.\n\n"
    "**Resposta (2026-08-09, Bruno Lima/PO, gate da rodada):** referência desatualizada.\n\n## Carla — dados",
)


LEGADO_V3 = LEGADO_V2.replace("| GQ10 | Referência cruzada quebrada |", "| GQ10 | Referência cruzada quebrada (§8.4.3) |")


def _repo_fixture(root: Path) -> None:
    """Repo git com dois commits do questions.md legado e uma tag no segundo."""
    env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
           "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}

    def git(*args: str, data: str = "2026-08-01T12:00:00") -> None:
        subprocess.run(["git", "-c", "commit.gpgsign=false", *args], cwd=root, check=True, capture_output=True,
                       env={**env, "GIT_AUTHOR_DATE": data, "GIT_COMMITTER_DATE": data})

    (root / "docs" / "discovery").mkdir(parents=True)
    (root / "docs" / "discovery" / "2026-07-27-kickoff.md").write_text("# kickoff\n")
    (root / "docs" / "prd-v2-proposta.md").write_text("# prd\n")
    git("init", "-q", "-b", "main")
    (root / INDICE).write_text(LEGADO_V1, encoding="utf-8")
    git("add", "."); git("commit", "-q", "-m", "v1")
    (root / INDICE).write_text(LEGADO_V2, encoding="utf-8")
    git("add", "."); git("commit", "-q", "-m", "v2", data="2026-08-10T12:00:00")
    git("tag", "v1.0.0")
    # terceiro commit só reescreve a linha da tabela da GQ10 (já ✅): não é resposta nova
    (root / INDICE).write_text(LEGADO_V3, encoding="utf-8")
    git("add", "."); git("commit", "-q", "-m", "v3", data="2026-09-01T12:00:00")


def selftest() -> None:
    import contextlib
    import io
    import tempfile

    intro, tabela, pre, perguntas = parse_legado(LEGADO_V2)
    assert intro.startswith("# Perguntas") and "Visão geral" not in intro and "Revisão de 01/08" in intro
    assert tabela["V-B1"] == {"tema": "Acesso às bases (OQ-14)", "dono": "Carla → Davi", "prioridade": "alta",
                              "estado": "aberta"}, tabela
    assert tabela["GQ10"]["estado"] == "respondida" and tabela["GQ10"]["prioridade"] == "media"
    assert list(pre) == ["Atualizações da reunião de 2026-08-09", "Carla — dados"], list(pre)
    assert pre["Carla — dados"] == "> Nota da seção."
    assert [p["codigo"] for p in perguntas] == ["B4", "GQ10", "V-B1"], "códigos com hífen e dois dígitos"
    b4, gq10 = perguntas[0], perguntas[1]
    assert (b4["titulo"], b4["prioridade"], b4["estado"], b4["sufixo"]) == \
        ("Escopo do MVP", "alta", "respondida", "(para o MVP)"), b4
    assert b4["corpo"].startswith("**Pergunta.**") and "## Carla" not in b4["corpo"]
    assert gq10["estado"] == "aberta" and "## Carla" not in gq10["corpo"]

    # resposta: data BR e ISO, rótulo com `.` ou `:`, autor pelo segmento — nunca por tabela de nomes
    assert parse_resposta(b4["corpo"], "2026") == ("2026-08-04", "Ana")
    assert parse_resposta(gq10["corpo"], "2000") == ("2026-08-09", "Bruno Lima")
    assert parse_resposta("**Decisão do gate (02/11/2026, PRD v3.20).** x", "2000") == ("2026-11-02", ""), "segmento rejeitado não vira PO"
    assert parse_resposta("**Decisão (01/11, Ana de Souza).** x", "2026") == ("2026-11-01", "Ana de Souza")
    assert autor_do_rotulo("João da Silva — e-mail") == "João da Silva" and autor_do_rotulo("Maria dos Santos/PO") == "Maria dos Santos"
    assert parse_resposta("**Resposta (14/08, Carla Reis — e-mail, thread \"x\").** y", "2026") == ("2026-08-14", "Carla Reis")
    assert parse_resposta("**Resposta (28/08, e-mail — [dossiê](2026-08-28-x.md)).** x", "2026") == ("2026-08-28", "")
    assert parse_resposta("**Resposta (16/10, caminho diferente — ADR-0014).** x", "2026") == ("2026-10-16", "")
    assert parse_resposta("**Direção (11/08).** só direção", "2026") == ("2026-08-11", "PO")
    assert parse_resposta("**Avanço (11/08).** só avanço", "2026") == ("", "")
    assert autor_do_rotulo("Ana C. Souza — e-mail") == "Ana C. Souza" and autor_do_rotulo("formulário") == ""

    assert extrair_refs(b4["titulo"] + b4["corpo"]) == ["RF-105", "RN-111", "delta-001"]
    assert extrair_refs("RF-104.1.a.4, RN-108 e DT-104; ADR-0013; Q-3 e D14 ficam fora") == \
        ["RF-104.1.a.4", "RN-108", "ADR-0013", "DT-104"]
    r = reescreve_links(b4["corpo"])
    assert "](../../prd-v2-proposta.md)" in r and "](../../../specs/_archive/001-ingestao/)" in r
    assert reescreve_links("[x](https://e.com/a) [y](#anc) ![i](img.png)") == \
        "[x](https://e.com/a) [y](#anc) ![i](../img.png)"
    assert slug("`gerar_boletim.py` na pasta Liberação — dono, função") == "gerar-boletim-py-na-pasta-liberacao"
    assert links_quebrados("[a](../nao-existe.md) [b](https://x) [c](#x) `[d](../x.md)`", Path(".")) == ["../nao-existe.md"]

    fm = {"id": "QT-001", "codigo": "B4", "estado": "respondida", "prioridade": "alta",
          "descricao": "Escopo do MVP", "para": "Ana", "respondeu": "Ana", "aberto": "2026-07-28",
          "respondido": "2026-08-04", "release": "v1.0.0", "refs": "RF-105, RN-111"}
    texto = serializa(fm, "corpo")
    fm2, corpo2 = parse_frontmatter(texto)
    assert fm2 == fm and TITULO.search(corpo2).group(2) == "Escopo do MVP", (fm2, corpo2)
    assert nome_item(fm) == "QUESTAO_QT-001-escopo-do-mvp.md"
    fm_v1 = {**fm, "id": "QT-002", "codigo": "V-B1", "estado": "aberta", "descricao": "Acesso às bases",
             "para": "Carla → Davi", "respondeu": "", "respondido": "", "release": "", "refs": "DT-039"}
    itens = [{**fm, "arquivo": nome_item(fm)}, {**fm_v1, "arquivo": nome_item(fm_v1)}]
    ind = render_indice(itens, date(2026, 11, 2))
    # contrato com o parser dos relatórios de status: 5 células, glifos de prioridade e estado
    linha = re.search(r"^\|([^|\n]+)\|([^|\n]+)\|([^|\n]+)\|([^|\n]+)\|([^|\n]+)\|\s*$", ind.split("## Pendentes")[0]
                      .split("|---|")[-1], re.M)
    assert linha and linha.group(1).strip() == "QT-001" and "🔴" in linha.group(4) and "✅" in linha.group(5), ind
    assert "### 🔴 Alta\n- [QT-002](questions/QUESTAO_QT-002-acesso-as-bases.md) — V-B1 · Acesso às bases — ⬜ aberta" in ind
    assert "Ana em 2026-08-04 · RF-105, RN-111 · main (v1.0.0)" in ind, ind
    assert "**2 perguntas** · ✅ respondidas 1 · 🔶 parciais 0 · ⬜ abertas 1" in ind
    assert f"GERADO por {CMD} indice (skill {SKILL})" in ind
    assert _onde({"release": "develop"}) == "develop (sem release)" and _onde({"release": ""}) == "fora da develop"

    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _repo_fixture(root)
        aberto, resposta = historico_git(root)
        assert aberto == {"B4": "2026-08-01", "V-B1": "2026-08-01", "GQ10": "2026-08-10"}, aberto
        assert set(resposta) == {"B4", "GQ10"} and resposta["GQ10"][1] == "2026-08-10", "✅ só na tabela conta"
        assert resposta["B4"][1] == "2026-08-10", "linha da tabela reescrita depois do ✅ não é transição nova"
        assert release_de(root, resposta["B4"][0]) == "v1.0.0"
        # linha só na tabela avisa (não recusa); célula sem glifo avisa; rótulo sem nome vira aviso de autor
        (root / INDICE).write_text(LEGADO_V3.replace("| V-B1 | Acesso às bases (OQ-14) | Carla → **Davi** | 🔴 Alta | ⬜ |",
                                                     "| X9 | Órfã | Ana | 🟢 Baixa | ⬜ |\n| V-B1 | Acesso às bases (OQ-14) | Carla → **Davi** | — | ⬜ |")
                                   .replace("Bruno Lima/PO, gate da rodada", "e-mail"), encoding="utf-8")
        _, avisos, _, _ = migrar(root, "2026-11-03")
        for a in ("X9: linha na Visão geral sem cabeçalho `###` — não migrada", "V-B1: tabela sem glifo de prioridade — usando o cabeçalho",
                  "GQ10: respondida sem autor identificável no rótulo — preencha `respondeu:`"):
            assert a in avisos, (a, avisos)
        (root / INDICE).write_text(LEGADO_V3, encoding="utf-8")
        # dry-run: prévia e avisos, nada escrito
        with contextlib.redirect_stdout(io.StringIO()) as saida:
            assert cmd_migrar(root, dry=True) == 0
        assert not (root / DIR_ITENS).exists() and "QT-003 GQ10" in saida.getvalue()
        assert "QT-001 (B4): ../../../specs/_archive/001-ingestao/" in saida.getvalue(), "link sem alvo listado no dry-run"
        assert "GQ10: estado do cabeçalho (aberta) difere da tabela (respondida) — vale a tabela" in saida.getvalue()
        assert "GQ10: prioridade do cabeçalho (alta) difere da tabela (media) — vale a tabela" in saida.getvalue()
        # migração efetiva: arquivos, README com o legado preservado, índice regenerado
        with contextlib.redirect_stdout(io.StringIO()):
            assert cmd_migrar(root, dry=False) == 0
        itens_m, erros = ler_registro(root)
        assert not erros and [i["codigo"] for i in itens_m] == ["B4", "V-B1", "GQ10"], (erros, itens_m)
        g = itens_m[2]
        assert (g["estado"], g["prioridade"], g["respondeu"], g["respondido"], g["release"], g["para"]) == \
            ("respondida", "media", "Bruno Lima", "2026-08-09", "v1.0.0", "Qualidade"), g
        assert itens_m[0]["respondeu"] == "Ana" and itens_m[0]["aberto"] == "2026-08-01"
        assert "**Pergunta:** Escopo do MVP: reposição primeiro?" in itens_m[0]["corpo"]
        assert "**Estado:** respondida (para o MVP)" in itens_m[0]["corpo"]
        assert "](../../prd-v2-proposta.md)" in itens_m[0]["corpo"]
        readme = (root / DIR_ITENS / "README.md").read_text(encoding="utf-8")
        assert "Revisão de 01/08" in readme and "### Seção «Carla — dados»" in readme and "[dossiê](../2026-07-27-kickoff.md)" in readme
        assert "## Migração de " in readme
        indice = (root / INDICE).read_text(encoding="utf-8")
        assert "**3 perguntas** · ✅ respondidas 2" in indice and "| QT-003 | GQ10 · Referência cruzada quebrada | Qualidade | 🟡 Média | ✅ |" in indice
        # novo: id = maior + 1, corpo do arquivo, refs do título
        corpo_f = root / "corpo.md"; corpo_f.write_text("**Pergunta:** vale a RN-200?\n")
        a = argparse.Namespace(descricao="Pergunta nova (RF-300)", para="Davi", prioridade="baixa", codigo="",
                               refs="", corpo_arquivo=str(corpo_f))
        with contextlib.redirect_stdout(io.StringIO()):
            assert cmd_novo(root, a) == 0
        novo = parse_frontmatter((root / DIR_ITENS / "QUESTAO_QT-004-pergunta-nova-rf-300.md").read_text())[0]
        assert (novo["id"], novo["estado"], novo["refs"], novo["aberto"]) == ("QT-004", "aberta", "RF-300, RN-200", date.today().isoformat()), novo
        # registro inválido: indice sai 1 e não reescreve
        ruim = root / DIR_ITENS / "QUESTAO_QT-005-ruim.md"
        ruim.write_text(serializa({**novo, "id": "QT-009"}, "# [QT-009] - Pergunta nova (RF-300)"))
        antes = (root / INDICE).read_text()
        with contextlib.redirect_stderr(io.StringIO()) as err:
            assert cmd_indice(root) == 1
        assert "difere do nome" in err.getvalue() and (root / INDICE).read_text() == antes
        ruim.unlink()
        ruim2 = root / DIR_ITENS / "QUESTAO_QT-006-ruim.md"
        ruim2.write_text("---\nid: QT-006\ncodigo: B4\nestado: respondida\nprioridade: urgente\ndescricao: Com | barra\npara:\n"
                         "respondeu:\naberto: 2026-13-45\nrespondido:\nrelease:\nrefs:\n---\n\n# [QT-006] - Com | barra\n")
        _, erros = ler_registro(root)
        for msg in ("QT-006: frontmatter sem `para`", "prioridade `urgente` fora de", "`aberto` não é uma data",
                    "respondida sem `respondido`", "descricao com `|`", "codigo `B4` duplicado"):
            assert any(msg in e for e in erros), (msg, erros)
        ruim2.unlink()
    # cabeçalho sem linha na tabela: recusa antes de tocar o git
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "docs" / "discovery").mkdir(parents=True)
        (root / INDICE).write_text(LEGADO_V2.replace("| GQ10 | Referência cruzada quebrada | Qualidade | 🟡 Média | ✅ |\n", ""))
        try:
            with contextlib.redirect_stderr(io.StringIO()) as err:
                migrar(root, "2026-11-03")
            raise AssertionError("deveria recusar")
        except SystemExit as e:
            assert e.code == 2 and "['GQ10']" in err.getvalue(), err.getvalue()
    print("selftest: OK")


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        selftest()
        return 0
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for nome in ("indice", "migrar", "novo"):
        s = sub.add_parser(nome)
        s.add_argument("root", nargs="?", default=".")
    sub.choices["migrar"].add_argument("--dry-run", action="store_true")
    n = sub.choices["novo"]
    n.add_argument("--descricao", required=True)
    n.add_argument("--para", required=True)
    n.add_argument("--prioridade", required=True, choices=PRIORIDADES)
    n.add_argument("--codigo")
    n.add_argument("--refs")
    n.add_argument("--corpo-arquivo")
    a = ap.parse_args(argv)
    root = Path(a.root).resolve()
    if not (root / "docs" / "discovery").is_dir():
        die(f"{root} não tem docs/discovery/")
    if a.cmd == "indice":
        return cmd_indice(root)
    if a.cmd == "migrar":
        return cmd_migrar(root, a.dry_run)
    return cmd_novo(root, a)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
