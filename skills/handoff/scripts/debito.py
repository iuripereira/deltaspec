#!/usr/bin/env python3
"""Fila de dívida técnica do deltaspec — score determinístico e projeção para tickets.

O registro é a fonte da verdade; ferramenta de ticket é projeção (ADR-0021). Este
script **não acessa a rede**: ele lê o registro, calcula e emite arquivos. Quem
executa `gh`/`acli` é a skill (mesmo padrão do projeto-infra, que é roteiro sem
script instalável). Política de fila e contrato da projeção: references/debito.md.

Dois layouts (dual-mode, ADR-0030): o novo é a pasta `debts/` na raiz — um arquivo
por item ativo em `debts/ativos/`, encerrados em `debts/_archive/` — e tem
precedência; o legado (blocos no `DEBT.md`) segue lido integralmente, com aviso
de deprecação apontando o `migrar`.

  novo      cadastra um item em debts/ativos/, já validado (o ID sai da união)
  quitar    mecaniza a quitação/descarte de um item já com estado final no frontmatter
  fila      valida, calcula o score e imprime a fila ordenada
  exportar  emite o JSON canônico + dialeto unitário do Jira (acli) + linhas de criação do GitHub
  diff      compara o registro com o estado coletado da ferramenta externa
  migrar    converte registro legado (blocos ou tabela) para o layout debts/
  indice    regenera o DEBT.md como índice dos ativos (projeção, ADR-0031)

Score = (juros × probabilidade) / principal, derivado na leitura e **nunca gravado**
(regra de ouro: valor calculado não vira segunda fonte). Ordenação: override,
depois trilha planejada, depois score decrescente.

Uso: debito.py novo [ROOT] --natureza N --descricao T [--fila P·J·Pr] [--local L]
                        [--gatilho G] [--origem O] [--ticket K] [--corpo-arquivo F]
     debito.py quitar [ROOT] DT-NNN --como "..." [--ticket-ref REF]
     debito.py fila [ROOT]
     debito.py exportar [ROOT] [--saida DIR]
     debito.py diff [ROOT] --externo ESTADO.json
     debito.py migrar [ROOT]
     debito.py indice [ROOT]
     debito.py --selftest
Exit 0 = sem erro · 1 = registro inválido ou divergência · 2 = erro de uso.
"""
import argparse
import json
import posixpath
import re
import shlex
import subprocess
import sys
import unicodedata
from collections import Counter
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path, PurePosixPath

from projecao import (LINK_MD, alvo_local, corpo_ticket, emitir_sh_acli, etiquetas,
                      ler_destino_tickets)

STALE_DIAS = 90  # sem mudança na linha e com juros altos: força decisão explícita
JANELA_CHURN = "6 months ago"  # janela do git log que estima a probabilidade de incidência
PERCENTIL_QUENTE = 0.10  # top 10% dos arquivos mais tocados → probabilidade 9
PERCENTIL_MORNO = 0.40  # top 40% → probabilidade 3; o resto → 1
JUROS_RELEVANTE = 3  # a partir daqui o aging cobra decisão (C do references/debito.md)

# Precedência do override: impedimento, não prioridade alta — entra fora da competição por score.
OVERRIDES = ("security", "compliance", "eol", "contract")
NATUREZAS_PONTUAVEIS = ("débito", "pendência")
ESTADOS_ATIVOS = ("aberto", "aceito", "vigente")
ESTADOS_FINAIS = ("quitado", "descartado")
VAZIO = ("", "—", "-")
DESCRICAO_LIMITE = 100  # descricao vira título do índice, da fila e da issue (DT-130)

# Layout novo (ADR-0030): registro na pasta debts/ da raiz — ativo em debts/ativos/
# (DEBT_DT-NNN-<topico>.md, sem data), encerrado em debts/_archive/ com a data do
# encerramento no nome. DEBTS_DIR permanece para o legado (ADR-0028) e para a união
# de arquivados em repo em migração parcial. O DT-NNN no nome dispensa parser no
# archive: o diff lê o ID dali.
DIR_ATIVOS = "debts/ativos"
DIR_ARCHIVE = "debts/_archive"
DEBTS_DIR = ".claude/debts"
ARQUIVADO = re.compile(r"^DEBT_(DT-\d+)")
ID_DT = re.compile(r"^DT-(\d+)$")  # o identificador em si, sem o prefixo do nome de arquivo
NOME_ATIVO = re.compile(r"^DEBT_(DT-\d+)-[a-z0-9][a-z0-9-]*\.md$")

# Frontmatter flat do arquivo ativo — chaves ASCII minúsculas, sem acento (valores
# livres). Regex stdlib e não PyYAML: a fila é caminho obrigatório e o PyYAML é
# opcional neste repo (ADR-0023, só o destino Jira); YAML interpretaria valores
# (`estado: no` viraria False). Âncoras de início de linha — lição 2026-07-28.
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n?", re.S)
FM_CHAVE = re.compile(r"^([a-z]+):[ \t]*(.*?)[ \t]*$", re.M)
FM_OBRIGATORIAS = ("id", "natureza", "estado", "descricao", "aberto")
# Título humano do arquivo (delta-048): primeira linha do corpo, espelho validado
# do frontmatter — terceira duplicação sancionada (id×nome, data nome×frontmatter).
TITULO_ATIVO = re.compile(r"^#\s+\[(DT-\d+)\]\s+-\s+(.*?)\s*$")
# Atalho GitHub (../../issues/N em qualquer profundidade) — nunca é caminho de repo,
# então a normalização do Local e a reescrita do migrar o tratam à parte.
ATALHO_GH = re.compile(r"^(\.\./)+(issues|pull|discussions)/")

# `P3·J9·Pr9` com sufixos opcionais ` · trilha` / ` · !security(AAAA-MM-DD)`.
# Ancorada no início: a fila só vale na posição canônica da célula (lição 2026-07-28).
FILA = re.compile(r"^P([139])·J([139])·Pr([139])(?:\s*·\s*(.+))?$")
OVERRIDE = re.compile(r"^!(\w+)\((\d{4}-\d{2}-\d{2})\)$")
DATA = re.compile(r"\d{4}-\d{2}-\d{2}")  # data obrigatória em quitado/descartado (R18)
TRILHA = "trilha"

# Gramática do bloco (delta-024). Todas ancoradas em início de linha: campo citado
# na prosa da descrição não é campo — a lição de 2026-07-28, agora em forma de bloco.
BLOCO = re.compile(r"^###\s+(DT-\d+)\s*·\s*([^·\n]+?)\s*·\s*([^·\n]+?)\s*$", re.M)
TITULO = re.compile(r"^\*\*(.+?)\*\*\s*$", re.M)
CAMPO = re.compile(r"^-\s+\*\*([^:*]+):\*\*\s*(.*)$", re.M)
TABELA_ANTIGA = re.compile(r"^\|\s*DT-\d+\s*\|", re.M)


def die(msg: str) -> None:
    print(f"ERRO: {msg}")
    sys.exit(2)


def parse_blocos(texto: str) -> list:
    """Blocos `### DT-NNN · natureza · estado` como dicionários.

    Cada peça vem de uma âncora de início de linha: o cabeçalho do `###`, o título
    do primeiro `**negrito**` e os campos de `- **Nome:** valor`. Nada é procurado
    por busca solta — prosa que mencione a sintaxe (a palavra "aberto" no meio de
    uma descrição, um `- **Fila:**` citado como exemplo) não pode virar campo. É a
    lição de 2026-07-28, que já custou falsos positivos em três gates diferentes.
    """
    marcas = list(BLOCO.finditer(texto))
    itens = []
    for i, m in enumerate(marcas):
        corpo = texto[m.end():marcas[i + 1].start() if i + 1 < len(marcas) else len(texto)]
        item = {"id": m.group(1), "natureza": m.group(2).strip(), "status": m.group(3).strip()}
        # O título é a primeira linha em negrito; a descrição é o que vem antes do
        # primeiro campo, sem o título — prosa livre, quantas linhas precisar.
        t = TITULO.search(corpo)
        item["título"] = t.group(1).strip() if t else ""
        antes = corpo[:CAMPO.search(corpo).start()] if CAMPO.search(corpo) else corpo
        item["descrição"] = (antes.replace(t.group(0), "", 1) if t else antes).strip()
        for campo, valor in CAMPO.findall(corpo):
            item[campo.strip().lower()] = valor.strip()
        itens.append(item)
    return itens


def estado(item: dict) -> str:
    """Estado do cabeçalho do bloco, normalizado."""
    return item.get("status", "").strip().lower()


def modo_novo(root: Path) -> bool:
    """Layout debts/ presente = precedência do novo (ADR-0030)."""
    return (root / DIR_ATIVOS).is_dir()


def fonte_de(root: Path) -> str:
    return DIR_ATIVOS if modo_novo(root) else "DEBT.md"


def _troca_alvo(m, novo: str) -> str:
    """Substitui o ALVO do link pelo span do grupo, nunca por replace de texto.

    `[CLAUDE.md](CLAUDE.md)` tem texto igual ao alvo: um replace de string
    reescreveria o texto e deixaria o alvo morto — a família da lição de
    2026-08-03 ("procurei o texto literal em vez do alvo").
    """
    ini, fim = m.start(1) - m.start(0), m.end(1) - m.start(0)
    completo = m.group(0)
    return completo[:ini] + novo + completo[fim:]


def _normaliza_local(valor: str) -> str:
    """Reescreve alvos de link do Local de relativos-ao-arquivo para relativos-à-raiz.

    O arquivo ativo vive 2 níveis abaixo (`debts/ativos/`), então `../../x` vira `x`.
    Atalho GitHub e URL não são caminho de repo e ficam como estão; alvo que ainda
    escapar da raiz depois da normalização é mantido para o validar acusar.
    """
    def troca(m):
        alvo = m.group(1)
        if alvo.startswith(("http://", "https://", "#")) or ATALHO_GH.match(alvo):
            return m.group(0)
        caminho, _, ancora = alvo.partition("#")
        novo = posixpath.normpath(posixpath.join(DIR_ATIVOS, caminho))
        return _troca_alvo(m, novo + (f"#{ancora}" if ancora else ""))
    return LINK_MD.sub(troca, valor)


def parse_arquivo_ativo(caminho: Path):
    """(item, erros estruturais) de um arquivo de debts/ativos/ — mesmo dict do parse_blocos.

    O id vem do **nome** do arquivo; o `id:` do frontmatter duplica de propósito e a
    igualdade é validada — duplicação sancionada com check mecânico (ADR-0030). O
    corpo mantém a gramática de campos `- **Campo:** valor` (regex CAMPO, intacta);
    `- **Fila:**` no corpo é erro, porque a fila vive só no frontmatter (fonte única).
    """
    nome = caminho.name
    m_nome = NOME_ATIVO.match(nome)
    if not m_nome:
        return None, [f"{nome}: nome fora do padrão DEBT_DT-NNN-<topico>.md em {DIR_ATIVOS}/"]
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
                         f"minúsculo sem acento (ex.: 'descricao', não 'descrição')")
    for chave in FM_OBRIGATORIAS:
        if fm.get(chave, "") in VAZIO:
            erros.append(f"{ident}: frontmatter sem a chave obrigatória '{chave}'")
    if fm.get("id") and fm["id"] != ident:
        erros.append(f"{ident}: frontmatter declara id '{fm['id']}' ≠ nome do arquivo — "
                     f"o nome é a fonte; iguale os dois")
    if fm.get("natureza") and fm["natureza"] not in NATUREZAS_PONTUAVEIS + ("guarda",):
        erros.append(f"{ident}: natureza '{fm['natureza']}' fora do conjunto "
                     f"{' · '.join(NATUREZAS_PONTUAVEIS + ('guarda',))} — "
                     f"'debito' sem acento viraria item não pontuável em silêncio")
    item = {"id": ident, "natureza": fm.get("natureza", ""), "status": fm.get("estado", ""),
            "título": fm.get("descricao", ""), "aberto": fm.get("aberto", ""),
            "fila": fm.get("fila", ""), "_arquivo": f"{DIR_ATIVOS}/{nome}"}
    corpo = texto[m_fm.end():]
    # Título humano `# [DT-NNN] - <descricao>` (R18, delta-048): espelho, nunca fonte —
    # sai do corpo antes do recorte da descrição e a igualdade é validada.
    primeira, _, depois = corpo.lstrip("\n").partition("\n")
    m_t = TITULO_ATIVO.match(primeira)
    if not m_t:
        erros.append(f"{ident}: primeira linha do corpo deve ser o título "
                     f"`# [{ident}] - <descricao do frontmatter>` (R18)")
    else:
        corpo = depois  # o título é espelho de leitura — nunca entra na descrição
        if m_t.group(1) != ident or m_t.group(2) != item["título"]:
            erros.append(f"{ident}: título H1 divergente do frontmatter — espelhe "
                         f"`# [{ident}] - {item['título']}`")
    antes = corpo[:CAMPO.search(corpo).start()] if CAMPO.search(corpo) else corpo
    item["descrição"] = antes.strip()
    for campo, valor in CAMPO.findall(corpo):
        chave = campo.strip().lower()
        if chave == "fila":
            erros.append(f"{ident}: '- **Fila:**' no corpo — a fila vive só no frontmatter; "
                         f"duas fontes divergiriam em silêncio")
            continue
        item[chave] = valor.strip()
    if item.get("local"):
        item["local"] = _normaliza_local(item["local"])
        for alvo in LINK_MD.findall(item["local"]):
            if alvo.startswith("../") and not ATALHO_GH.match(alvo):
                erros.append(f"{ident}: 'Local' aponta para fora do repositório — {alvo}")
    return item, erros


def parse_ativos(root: Path):
    """(itens, erros estruturais) de todos os arquivos de debts/ativos/, por nome."""
    itens, erros, vistos = [], [], set()
    for p in sorted((root / DIR_ATIVOS).glob("*.md")):
        item, e = parse_arquivo_ativo(p)
        erros += e
        if item is None:
            continue
        if item["id"] in vistos:
            erros.append(f"{item['id']}: ID duplicado em {DIR_ATIVOS}/ — numeração é global")
        vistos.add(item["id"])
        itens.append(item)
    duplicados = vistos & ids_arquivados(root)
    for ident in sorted(duplicados):
        erros.append(f"{ident}: existe em {DIR_ATIVOS}/ e no archive — ID nunca é reutilizado")
    return itens, erros


def ids_arquivados(root: Path) -> set:
    """IDs encerrados, lidos do nome do arquivo — união de debts/_archive/ e .claude/debts/.

    A união cobre repo em migração parcial (ADR-0030): o diff nunca regride ao falso
    "não existe". Sem pasta nenhuma, devolve vazio — o diretório nasce no primeiro
    arquivamento, sem scaffold (mesma regra da delta-037).
    """
    ids = set()
    for pasta in (root / DIR_ARCHIVE, root / DEBTS_DIR):
        if pasta.is_dir():
            ids |= {m.group(1) for p in pasta.glob("*.md") if (m := ARQUIVADO.match(p.name))}
    return ids


def ids_em_disco(root: Path) -> set:
    """IDs de todo item cadastrado, lidos do **nome** dos arquivos das duas pastas.

    Do nome, nunca do parse: o registro real carrega ativos malformados (DT-079) e
    um parse que tropeça neles devolveria um ID já usado como se estivesse livre.
    """
    ativos = {m.group(1) for p in (root / DIR_ATIVOS).glob("*.md")
              if (m := ARQUIVADO.match(p.name))}
    return ativos | ids_arquivados(root)


def ids_em_refs_remotas(root: Path) -> set:
    """IDs que existem em branches remotas já buscadas — sem tocar a rede.

    Cegueira conhecida do DT-071: quem só lê o disco entrega o mesmo número para
    duas sessões em branches diferentes. Os refs de rastreio (`refs/remotes/*`) já
    estão em disco, então lê-los é grátis e não quebra o contrato "sem rede" deste
    script. Branch nunca buscada continua invisível — por isso o comando diz
    quantos refs entraram na conta.
    """
    refs = git(root, "for-each-ref", "--format=%(refname)", "refs/remotes/")
    if not refs:
        return set()
    ids = set()
    for ref in refs.split():
        saida = git(root, "ls-tree", "-r", "--name-only", ref, DIR_ATIVOS, DIR_ARCHIVE)
        ids |= {m.group(1) for linha in (saida or "").splitlines()
                if (m := ARQUIVADO.match(PurePosixPath(linha).name))}
    return ids


def proximo_id(ids: set) -> str:
    """Maior ID da união + 1, com 3 dígitos — numeração global, nunca reutilizada.

    Recebe o conjunto pronto (disco + refs remotos) em vez de ir buscá-lo: função
    pura, testável sem repositório de mentira. Entrada fora do padrão é ignorada.
    """
    numeros = [int(m.group(1)) for i in ids if (m := ID_DT.match(i))]
    return f"DT-{max(numeros, default=0) + 1:03d}"


def parse_fila(valor: str):
    """(principal, juros, probabilidade, trilha, override) ou None se malformada.

    O vocabulário de override é fechado: `!segurança-com-typo(data)` seria aceito em
    silêncio e rebaixaria um impedimento à prioridade de trilha (achado do review).
    """
    m = FILA.match(valor.strip().strip("`").strip())  # crase é formatação, não conteúdo
    if not m:
        return None
    principal, juros, prob = (int(m.group(i)) for i in (1, 2, 3))
    trilha, override = False, None
    for sufixo in (s.strip() for s in (m.group(4) or "").split("·") if s.strip()):
        if sufixo == TRILHA:
            trilha = True
        elif (mo := OVERRIDE.match(sufixo)) and mo.group(1) in OVERRIDES:
            override = mo.groups()
        else:
            return None
    return principal, juros, prob, trilha, override


def precedencia(entrada: dict) -> int:
    """Posição na fila antes do score: override (na ordem do enum) < trilha < resto."""
    if entrada["override"]:
        return OVERRIDES.index(entrada["override"][0])
    return len(OVERRIDES) if entrada["trilha"] else len(OVERRIDES) + 1


def score(principal: int, juros: int, prob: int) -> float:
    """Função pura: juros × probabilidade, amortizado pelo custo de pagar."""
    return (juros * prob) / principal


def pontuavel(item: dict) -> bool:
    return (item.get("natureza", "") in NATUREZAS_PONTUAVEIS
            and estado(item) in ESTADOS_ATIVOS)


def validar(itens: list, root: Path) -> list:
    """Erros bloqueantes: sem eles a fila mentiria. Um erro por (item, campo)."""
    erros = []
    for item in itens:
        ident, st = item.get("id", "?"), estado(item)
        if st not in ESTADOS_ATIVOS + ESTADOS_FINAIS:
            erros.append(f"{ident}: status '{st or 'vazio'}' fora do conjunto "
                         f"{', '.join(ESTADOS_ATIVOS + ESTADOS_FINAIS)}")
            continue
        if st == "aceito" and item.get("gatilho", "") in VAZIO:
            erros.append(f"{ident}: estado 'aceito' exige o campo Gatilho (reavaliação)")
        if st in ESTADOS_FINAIS and not DATA.search(item.get("encerrado", "")):
            erros.append(f"{ident}: estado '{st}' exige o campo Encerrado com data e ref — R18")
        if item.get("natureza") == "guarda" and item.get("fila", "") not in VAZIO:
            erros.append(f"{ident}: guarda não tem principal nem juros — não declare Fila")
        if not pontuavel(item):
            continue
        if item.get("título", "") in VAZIO:
            erros.append(f"{ident}: título vazio — o ticket precisa de um sintoma observável")
        if item.get("gatilho", "") in VAZIO:
            erros.append(f"{ident}: campo Gatilho ausente — sem ele o item nunca é reavaliado")
        local = item.get("local", "")
        if local in VAZIO:
            erros.append(f"{ident}: campo Local ausente — dívida sem localização não é acionável")
        else:
            for alvo in LINK_MD.findall(local):
                if not (root / alvo.split("#")[0]).exists():
                    erros.append(f"{ident}: 'Local' aponta caminho inexistente — {alvo}")
        if not parse_fila(item.get("fila", "")):
            erros.append(f"{ident}: 'Fila' malformada — esperado P{{1|3|9}}·J{{1|3|9}}·Pr{{1|3|9}}")
    return erros


def git(root: Path, *args):
    """stdout do git, ou None quando não há git/histórico — degrada como o C7."""
    try:
        r = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    except (FileNotFoundError, OSError):
        return None
    return r.stdout if r.returncode == 0 else None


@lru_cache(maxsize=None)
def churn(root: Path):
    """{caminho: commits na janela} — proxy objetivo da probabilidade de incidência.

    Em cache: o `git log` varre o repositório inteiro e o relatório o consulta por item.
    """
    saida = git(root, "log", f"--since={JANELA_CHURN}", "--name-only", "--pretty=format:")
    if saida is None:
        return None
    return Counter(l.strip() for l in saida.splitlines() if l.strip())


def prob_do_churn(caminho: str, contagem):
    """Percentil do arquivo no ranking de churn → escala do eixo (1, 3 ou 9)."""
    if not contagem:
        return None
    if caminho not in contagem:
        return 1
    ranking = [c for c, _ in contagem.most_common()]
    posicao = ranking.index(caminho) / len(ranking)
    return 9 if posicao < PERCENTIL_QUENTE else 3 if posicao < PERCENTIL_MORNO else 1


def dias_parado(root: Path, item: dict, hoje: date):
    """Dias desde a última mudança no **cabeçalho** do item — base do 'stale'.

    Layout novo: `-G` sobre as chaves `natureza:`/`estado:` do frontmatter, no
    arquivo do próprio item — criação e mudança de estado/natureza reiniciam o
    relógio; editar a prosa não. Legado: o ID só aparece na linha `### DT-NNN ·
    natureza · estado` do DEBT.md, então `-G ident` mede o mesmo.
    (`-G` e não `-S`: o pickaxe só conta quando a string passa a existir ou some.)
    """
    if "_arquivo" in item:
        saida = git(root, "log", "-1", "--format=%cs",
                    "-G", "^(natureza|estado):", "--", item["_arquivo"])
    else:
        saida = git(root, "log", "-1", "--format=%cs", "-G", item["id"], "--", "DEBT.md")
    if not saida or not saida.strip():
        return None
    try:
        return (hoje - datetime.strptime(saida.strip(), "%Y-%m-%d").date()).days
    except ValueError:
        return None


def montar_fila(itens: list, root: Path, hoje=None) -> list:
    """Itens pontuáveis, ordenados: override, trilha, score desc. Score não é persistido."""
    hoje = hoje or date.today()
    contagem = churn(root)
    fila = []
    for item in itens:
        if not pontuavel(item):
            continue
        principal, juros, prob, trilha, override = parse_fila(item["fila"])
        derivada = prob_do_churn(alvo_local(item), contagem)
        parado = dias_parado(root, item, hoje)
        fila.append({
            "item": item, "principal": principal, "juros": juros, "prob": prob,
            "trilha": trilha, "override": override,
            "score": score(principal, juros, prob),
            "prob_derivada": derivada,
            "stale": bool(parado is not None and parado > STALE_DIAS and juros >= JUROS_RELEVANTE),
        })
    fila.sort(key=lambda f: (precedencia(f), -f["score"]))
    return fila


def canonico(fila: list, fonte: str) -> dict:
    """JSON canônico — contrato único que alimenta os dois dialetos."""
    itens = []
    for entrada in fila:
        item = entrada["item"]
        ticket = item.get("ticket", "")
        itens.append({
            "id": item["id"],
            "title": f"[{item['id']}] {item.get('título', '')}",
            "body": corpo_ticket(item, entrada),
            "labels": etiquetas(item, entrada),
            "score": round(entrada["score"], 2),
            "fila": {"principal": entrada["principal"], "juros": entrada["juros"],
                     "probabilidade": entrada["prob"], "trilha": entrada["trilha"],
                     "override": entrada["override"][0] if entrada["override"] else None,
                     "prazo": entrada["override"][1] if entrada["override"] else None},
            "externo": None if ticket in VAZIO else ticket,
        })
    return {"version": 1, "source": fonte, "items": itens}


def carregar(root: Path):
    """Itens válidos do registro, ou None quando há erro (já reportado).

    Dual-mode (ADR-0030): debts/ativos/ presente tem precedência — blocos de um
    DEBT.md remanescente são ignorados, e a pasta vazia avisa (esvaziamento
    acidental nunca é silencioso). Sem a pasta, o caminho legado segue igual, com
    aviso de deprecação. Registro no formato de tabela (delta-023 e anteriores,
    incluindo o template ainda distribuído) devolve lista vazia com instrução de
    conversão: o arquivo continua valendo como registro, só a fila não é calculável.
    """
    if modo_novo(root):
        itens, erros = parse_ativos(root)
        if not itens and not erros:
            print(f"{DIR_ATIVOS}/ presente e vazio — o layout novo tem precedência; "
                  f"blocos num DEBT.md remanescente são ignorados (ADR-0030).")
            return []
        erros += validar(itens, root)
        for e in erros:
            print(f"[inválido] {e}")
        return None if erros else itens
    texto = (root / "DEBT.md").read_text(encoding="utf-8")
    itens = parse_blocos(texto)
    if not itens and TABELA_ANTIGA.search(texto):
        print("Registro em formato de tabela (anterior à delta-024) — o arquivo vale como "
              "registro, mas a fila precisa dos blocos `### DT-NNN · natureza · estado`. "
              "Converta com `debito.py migrar`; gramática em skills/handoff/references/debito.md.")
        return []
    print(f"> Layout legado (blocos no DEBT.md): segue lido; o formato novo é a pasta "
          f"{DIR_ATIVOS}/ — converta com `debito.py migrar` (ADR-0030).")
    erros = validar(itens, root)
    for e in erros:
        print(f"[inválido] {e}")
    return None if erros else itens


def exportar(root: Path, saida: Path, projeto: str = "", faixa: str = "") -> int:
    destino, _ = ler_destino_tickets(root)
    if destino == "none":
        print("[recusado] destino `none`; declare `motores.tickets` no doc-profile.yaml "
              "para projetar (none | github-issues | jira)")
        return 1
    itens = carregar(root)
    if itens is None:
        return 1
    dados = canonico(montar_fila(itens, root), fonte_de(root))
    if faixa:
        # Reusa a label que canonico()/etiquetas() já calculou — mesmo corte de score,
        # zero limiar duplicado (FAIXA_ALTA/FAIXA_MEDIA vivem só em projecao.py).
        dados["items"] = [i for i in dados["items"] if f"fila:{faixa}" in i["labels"]]
    saida.mkdir(parents=True, exist_ok=True)
    (saida / "tickets.json").write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n",
                                        encoding="utf-8")
    # Dialeto unitário do `acli jira workitem create` (DT-021: `create-bulk` rejeita \n
    # na description). Só é emitido com a chave do projeto: sem ela o acli recusa o
    # create, e emitir um roteiro que não roda seria pior que não emitir (achado do review).
    if projeto:
        pendentes_acli = [{"id": i["id"], "title": i["title"], "body": i["body"], "labels": i["labels"]}
                          for i in dados["items"] if not i["externo"]]
        emitir_sh_acli(pendentes_acli, projeto, saida)
    linhas = ["#!/usr/bin/env bash",
              "# Emitido por debito.py — revise antes de executar. Itens já projetados são pulados.",
              "# Rode a partir da raiz do repositório: o gh resolve o repo pelo diretório corrente.",
              "set -euo pipefail", "",
              "# Etiquetas primeiro — `gh issue create` falha se a etiqueta não existir.",
              "# Idempotente: recriar uma etiqueta existente é erro, e aqui ele é inofensivo."]
    for rotulo in sorted({r for i in dados["items"] if not i["externo"] for r in i["labels"]}):
        linhas.append(f"gh label create {shlex.quote(rotulo)} "
                      f"--description {shlex.quote('Projeção do registro de débito (ADR-0021)')} 2>/dev/null || true")
    linhas.append("")
    for i in dados["items"]:
        if i["externo"]:
            linhas.append(f"# {i['id']} já projetado em {i['externo']} — pulando")
            continue
        rotulos = " ".join(f"--label {shlex.quote(l)}" for l in i["labels"])
        linhas += [f"gh issue create --title {shlex.quote(i['title'])} {rotulos} "
                   f"--body-file - <<'CORPO_{i['id'].replace('-', '_')}'",
                   i["body"], f"CORPO_{i['id'].replace('-', '_')}", ""]
    (saida / "tickets-gh.sh").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    pendentes = sum(1 for i in dados["items"] if not i["externo"])
    print(f"{len(dados['items'])} item(ns) na fila · {pendentes} sem projeção · saída em {saida}")
    if not projeto:
        print("> Dialeto do Jira omitido: declare `motores.jira.projeto` no doc-profile.yaml "
              "(ou passe --projeto CHAVE para uma exportação pontual). Sem isso o destino "
              "é o GitHub, via tickets-gh.sh.")
    return 0


def diff(root: Path, externo: Path) -> int:
    """Registro × estado da ferramenta: tabela de divergências (formato do R27).

    Só reporta. A atualização do registro é proposta ao usuário e aplicada por ele —
    a ferramenta externa nunca sobrescreve a fonte (ADR-0021). Aqui o registro é
    lido cru (sem validar), como sempre foi: o diff compara, não valida.
    """
    if modo_novo(root):
        itens = parse_ativos(root)[0]
    else:
        itens = parse_blocos((root / "DEBT.md").read_text(encoding="utf-8"))
    try:  # fronteira de confiança: o arquivo vem de fora, coletado à mão pela skill
        tickets = json.loads(externo.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as erro:
        die(f"não consegui ler {externo}: {erro}")
    if not isinstance(tickets, list):
        die(f"{externo} deveria ser a lista JSON do `gh issue list --json ...`")
    por_id = {}
    for t in tickets:
        for rotulo in t.get("labels", []):
            nome = rotulo.get("name", "") if isinstance(rotulo, dict) else str(rotulo)
            if nome.startswith("dt:"):
                por_id[nome[3:]] = t
    linhas = []
    for item in itens:
        ident, st = item["id"], estado(item)
        ticket = por_id.get(ident)
        if pontuavel(item) and not ticket:
            linhas.append((ident, f"{st}, sem chave externa", "sem ticket",
                           "dívida invisível para quem acompanha pela ferramenta",
                           "projetar com `exportar` + criar o ticket"))
        elif ticket and ticket.get("state", "").upper() == "CLOSED" and st in ESTADOS_ATIVOS:
            linhas.append((ident, f"status '{st}'", f"ticket #{ticket.get('number')} fechado",
                           "alguém deu a dívida por resolvida fora do repo",
                           "confirmar e quitar/descartar no registro, ou reabrir o ticket"))
        elif ticket and ticket.get("state", "").upper() == "OPEN" and st in ESTADOS_FINAIS:
            linhas.append((ident, f"status '{st}'", f"ticket #{ticket.get('number')} aberto",
                           "ticket órfão continua cobrando trabalho já encerrado",
                           "fechar o ticket citando a quitação"))
    # Item arquivado (debts/_archive/ ou .claude/debts/) é estado final: ticket
    # aberto é órfão; ticket fechado é sincronia — e nunca o falso "não existe".
    arquivados = ids_arquivados(root) - {i["id"] for i in itens}
    for ident in sorted(arquivados):
        ticket = por_id.get(ident)
        if ticket and ticket.get("state", "").upper() == "OPEN":
            linhas.append((ident, "arquivado (estado final)",
                           f"ticket #{ticket.get('number')} aberto",
                           "ticket órfão continua cobrando trabalho já encerrado",
                           "fechar o ticket citando a quitação"))
    conhecidos = {i["id"] for i in itens} | arquivados
    for ident, ticket in sorted(por_id.items()):
        if ident not in conhecidos:
            linhas.append((ident, "não existe", f"ticket #{ticket.get('number')}",
                           "trabalho rastreado fora do registro canônico",
                           "abrir DT-NNN no registro ou fechar o ticket"))
    print(f"# Divergências registro × ferramenta externa · {len(linhas)} achado(s)\n")
    if not linhas:
        print("Nenhuma divergência: o registro e a projeção estão em sincronia.")
        return 0
    print("| ID | Registro diz | Ferramenta diz | Impacto | Ação proposta |")
    print("|---|---|---|---|---|")
    for l in linhas:
        print("| " + " | ".join(l) + " |")
    print("\n> Proposta, não aplicação: nada é gravado no registro sem sua aprovação (ADR-0021).")
    return 1


def cmd_fila(root: Path, hoje=None) -> int:
    itens = carregar(root)
    if itens is None:
        return 1
    if not itens:
        return 0  # formato antigo ou registro vazio: carregar() já explicou
    fila = montar_fila(itens, root, hoje)
    print(f"# Fila de dívida — {len(fila)} item(ns) pontuável(is)\n")
    print("| # | ID | Score | Fila | Título | Marcas |")
    print("|---|---|---|---|---|---|")
    for n, e in enumerate(fila, 1):
        marcas = []
        if e["override"]:
            marcas.append(f"**override {e['override'][0]}** (prazo {e['override'][1]})")
        if e["trilha"]:
            marcas.append("trilha planejada")
        if e["stale"]:
            marcas.append(f"**stale** (>{STALE_DIAS}d sem mudança)")
        if e["prob_derivada"] and e["prob_derivada"] != e["prob"]:
            marcas.append(f"churn sugere Pr{e['prob_derivada']}")
        print(f"| {n} | {e['item']['id']} | {e['score']:.2f} | {e['item']['fila']} "
              f"| {e['item'].get('título', '')} | {' · '.join(marcas) or '—'} |")
    longas = [i["id"] for i in itens if len(i.get("título", "")) > DESCRICAO_LIMITE]
    if longas:
        print(f"\n> {len(longas)} item(ns) com descricao acima do teto de "
              f"{DESCRICAO_LIMITE} chars — teto vale para cadastro novo, item antigo se "
              f"ajusta quando for tocado: {', '.join(longas)}")
    finais = [i["id"] for i in itens if estado(i) in ESTADOS_FINAIS]
    if finais:
        destino = DIR_ARCHIVE if modo_novo(root) else DEBTS_DIR
        print(f"\n> {len(finais)} item(ns) em estado final ainda no registro — candidato(s) a "
              f"arquivar em {destino}/ (ADR-0030): {', '.join(finais)}")
    if churn(root) is None:
        print("\n> Aviso: sem git — a probabilidade declarada vale, sem conferência por churn.")
    if modo_novo(root):  # drift do índice-projeção nunca é silencioso (ADR-0031)
        crus, _ = parse_ativos(root)
        atual = (root / "DEBT.md").read_text(encoding="utf-8") if (root / "DEBT.md").is_file() else ""
        if atual != render_indice(root, crus):
            print("\n> Índice do DEBT.md desatualizado — regenere com `debito.py indice .` (ADR-0031).")
    return 0


# ------------------------------------------------------------- migrar (ADR-0030)

# README mínimo que o migrar deixa quando o repo ainda não tem um (o completo vem
# do template debts-README.md do projeto-init; este só garante ponteiro sem link
# morto e as três regras que não podem esperar).
README_MINIMO = """# debts/ — registro de débito técnico, pendências e guardas

> Um arquivo por item (modelo ADR-0030 do deltaspec): ativos em `ativos/`, encerrados
> em `_archive/` (nasce no primeiro arquivamento). Fila: `debito.py fila .` — o score
> `(J×Pr)/P` é derivado na leitura, nunca gravado. Quitação = editar `estado:`/`encerrado:`
> no frontmatter, escrever a seção `#### Como foi quitado` (2–4 frases amigáveis; o
> técnico fica no commit/issue — no Jira, fechamento em nível de negócio), trocar Ticket
> por **Encerrado** e `git mv` para `_archive/` com a data no nome, tudo no mesmo
> commit. Formato completo e gramática: `references/debito.md`
> da skill handoff do deltaspec (template integral: projeto-init, `debts-README.md`).
"""


def render_indice(root: Path, itens: list) -> str:
    """Índice gerado do DEBT.md (ADR-0031) — projeção determinística de debts/ativos/.

    Agrupa por valor GRAVADO (override e o eixo J), nunca por limiar novo; a ordem
    interna de cada seção é o score derivado na geração — materializado como
    projeção regenerável, mesma doutrina do tickets.json (ADR-0021). `stale` fica
    fora de propósito: marca temporal apodreceria num arquivo gerado. Só linka o
    que existe (lição da delta-045: C3 de consumidor varre este arquivo).
    """
    secoes = {ch: [] for ch in ("criticos", "j9", "j3", "j1", "sem_triagem", "guardas")}
    for item in itens:
        if item.get("natureza") == "guarda":
            secoes["guardas"].append((0.0, item, None))
            continue
        if estado(item) not in ESTADOS_ATIVOS:
            continue  # estado final em ativos/ é transitório; a fila avisa o candidato
        parsed = parse_fila(item.get("fila", ""))
        if not parsed:
            secoes["sem_triagem"].append((0.0, item, None))
            continue
        principal, juros, prob, trilha, override = parsed
        chave = "criticos" if override else {9: "j9", 3: "j3", 1: "j1"}[juros]
        secoes[chave].append((score(principal, juros, prob), item, (trilha, override)))

    def linha_de(entrada):
        pontos, item, extra = entrada
        marcas = []
        if extra and extra[1]:
            marcas.append(f"!{extra[1][0]}({extra[1][1]})")
        if extra and extra[0]:
            marcas.append("trilha")
        sufixo = f" · {' · '.join(marcas)}" if marcas else ""
        return f"- [{item['id']}]({item.get('_arquivo', '')}) — {item.get('título', '')}{sufixo}"

    cab_links = ["[ativos/](debts/ativos/)"]
    for alvo, rotulo in ((DIR_ARCHIVE, "[_archive/](debts/_archive/)"),):
        if (root / alvo).is_dir():
            cab_links.append(rotulo)
    if (root / "debts/LICOES.md").is_file():
        cab_links.append("[LICOES.md](debts/LICOES.md)")
    if (root / "debts/README.md").is_file():
        cab_links.append("[README.md](debts/README.md)")
    partes = [
        "# DEBT.md — índice dos débitos ativos",
        "<!-- GERADO por debito.py indice — não edite à mão; regenere após cadastrar/quitar.",
        "     Fonte: debts/ativos/ · fila viva: debito.py fila . -->",
        "",
        f"> Registro canônico em [debts/](debts/) (ADR-0030/0031): {' · '.join(cab_links)}.",
    ]
    titulos = (("criticos", "Críticos (impedimento com prazo)"),
               ("j9", "Importantes (bloqueiam entrega — J9)"),
               ("j3", "Médios (atrasam — J3)"),
               ("j1", "Não urgentes (incômodo — J1)"),
               ("sem_triagem", "Sem triagem (eixos pendentes)"),
               ("guardas", "Guardas"))
    for chave, titulo in titulos:
        entradas = secoes[chave]
        if not entradas:
            continue  # seção vazia é omitida — o render segue determinístico
        entradas.sort(key=lambda e: (-e[0], e[1]["id"]))
        partes += ["", f"## {titulo}"] + [linha_de(e) for e in entradas]
    return "\n".join(partes) + "\n"


def cmd_indice(root: Path) -> int:
    """Regenera o DEBT.md como índice dos ativos (ADR-0031) — projeção, nunca fonte."""
    if not modo_novo(root):
        die(f"{DIR_ATIVOS}/ não encontrado — o índice só projeta o layout novo; "
            f"converta o registro legado com `debito.py migrar` primeiro")
    itens, erros = parse_ativos(root)
    for e in erros:  # ilegível/incompleto é reportado, nunca some em silêncio (R71)
        print(f"[triagem] {e}")
    (root / "DEBT.md").write_text(render_indice(root, itens), encoding="utf-8")
    ativos = sum(1 for i in itens if estado(i) in ESTADOS_ATIVOS or i.get("natureza") == "guarda")
    print(f"DEBT.md regenerado: índice com {ativos} item(ns) de {DIR_ATIVOS}/.")
    return 0

ROTULO_CAMPO = (("local", "Local"), ("gatilho", "Gatilho"), ("origem", "Origem"),
                ("ticket", "Ticket"), ("encerrado", "Encerrado"))


def _ascii(texto: str) -> str:
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()


def slug(texto: str, max_palavras: int = 6) -> str:
    """kebab-case ASCII do título — vira o <topico> do nome do arquivo."""
    palavras = re.sub(r"[^a-z0-9]+", " ", _ascii(texto).lower()).split()
    return "-".join(palavras[:max_palavras]) or "sem-titulo"


def reescreve_links(texto: str) -> str:
    """Alvos relativos da raiz ganham 2 níveis (o arquivo novo vive em debts/*/).

    Regra única: alvo que não é URL nem âncora recebe `../../` — vale igual para
    caminho de repo (`x` → `../../x`) e para atalho GitHub (`../../issues/N` →
    `../../../../issues/N`), porque ambos estavam escritos para resolver da raiz.
    """
    def troca(m):
        alvo = m.group(1)
        if alvo.startswith(("http://", "https://", "#")):
            return m.group(0)
        return _troca_alvo(m, "../../" + alvo)
    return LINK_MD.sub(troca, texto)


ESC_PIPE = "\x00PIPE\x00"  # sentinela interna do split — nunca aparece em markdown


def _celulas(linha: str) -> list:
    """Células de uma linha de tabela, respeitando o escape `\\|` do formato.

    `\\|` é conteúdo, não separador (o formato tabela o exigia para pipe em
    célula — caso real: `fmt=json\\|csv\\|txt` num repo consumidor, DT-041).
    """
    protegida = linha.strip().strip("|").replace("\\|", ESC_PIPE)
    return [c.replace(ESC_PIPE, "|").strip() for c in protegida.split("|")]


def parse_tabela(texto: str) -> list:
    """Linhas da tabela legada (delta-023/template) como dicts — coluna por índice.

    O cabeçalho define o índice de cada coluna (nome normalizado sem acento);
    célula é lida pela posição, nunca por busca de texto (lição 2026-08-01).
    Linha com aridade divergente do cabeçalho **não é adivinhada** (delta-044):
    só id/natureza/descricao são mapeados e o resto vai intacto para a prosa.
    """
    itens, idx, aridade = [], None, 0
    for lt in texto.splitlines():
        s = lt.strip()
        if not s.startswith("|"):
            continue
        celulas = _celulas(s)
        if set("".join(celulas)) <= set("-: "):
            continue
        if idx is None:
            cab = [_ascii(c).lower() for c in celulas]
            if "id" in cab:
                idx = {nome: i for i, nome in enumerate(cab)}
                aridade = len(cab)
            continue

        def cel(nome, _c=celulas):
            i = idx.get(nome)
            return _c[i] if i is not None and i < len(_c) else ""

        ident = cel("id").strip("`* ")
        if not re.fullmatch(r"DT-\d+", ident):
            continue
        if len(celulas) != aridade:
            # aridade divergente: mapear além das 3 primeiras colunas seria chute
            itens.append({"id": ident, "natureza": cel("natureza"),
                          "título": cel("descricao"),
                          "descrição": "Linha original (aridade divergente do cabeçalho — "
                                       "redistribua os campos à mão): " + " · ".join(celulas[3:]),
                          "status": "aberto", "_aridade_divergente": True})
            continue
        status_bruto = cel("status")
        m_st = re.match(r"([a-z]+)", status_bruto.strip().lower())
        item = {"id": ident, "natureza": cel("natureza"), "título": cel("descricao"),
                "descrição": "", "status": m_st.group(1) if m_st else status_bruto,
                "origem": cel("origem"), "aberto em": cel("aberto em"),
                "gatilho": cel("gatilho de correcao") or cel("gatilho")}
        if item["status"] in ESTADOS_FINAIS and (m_par := re.search(r"\((.+)\)", status_bruto)):
            item["encerrado"] = m_par.group(1).replace(",", " ·", 1)
        itens.append(item)
    return itens


def render_item(item: dict):
    """(nome_base, conteúdo, pendências de triagem) do arquivo novo de um item.

    Nada é inventado: chave sem valor recuperável fica ausente e vira pendência —
    a fila subsequente cobra a triagem com erro (ADR-0030).
    """
    ident, pend = item["id"], []
    titulo = item.get("título", "").strip()
    if not titulo:
        primeiras = [l for l in item.get("descrição", "").strip().splitlines() if l.strip()]
        titulo = primeiras[0].strip() if primeiras else ""
    if not titulo:
        pend.append(f"{ident}: sem descrição — preencha 'descricao:' no frontmatter")
    # Link markdown no título vira texto plano (delta-050): descricao/H1 nunca carregam
    # alvo de link — o conteúdo íntegro da célula, com links reescritos, vai ao corpo.
    titulo_bruto, titulo = titulo, re.sub(r"\[([^\]]*)\]\([^)]+\)", r"\1", titulo)
    origem = item.get("origem", "")
    m_ab = re.search(r"aberto em (\d{4}-\d{2}-\d{2})", origem) or DATA.search(item.get("aberto em", ""))
    aberto = m_ab.group(1) if m_ab and m_ab.lastindex else (m_ab.group(0) if m_ab else "")
    if not aberto:
        pend.append(f"{ident}: sem data de abertura — preencha 'aberto:' no frontmatter")
    origem = re.sub(r"\s*·?\s*aberto em \d{4}-\d{2}-\d{2}", "", origem).strip(" ·")
    fila = item.get("fila", "").strip().strip("`").strip()
    if pontuavel(item) and not fila:
        pend.append(f"{ident}: sem fila — triagem dos eixos pendente (P{{1|3|9}}·J·Pr)")
    if pontuavel(item) and item.get("local", "").strip() in VAZIO:
        pend.append(f"{ident}: sem Local — aponte o artefato antes de rodar a fila")
    st = estado(item)
    m_enc = DATA.search(item.get("encerrado", ""))
    if st in ESTADOS_FINAIS and not m_enc:
        pend.append(f"{ident}: estado final sem data no Encerrado — complete e mova para o archive")
    fm = ["---", f"id: {ident}", f"natureza: {item.get('natureza', '').strip()}", f"estado: {st}"]
    if fila and item.get("natureza") != "guarda":
        fm.append(f"fila: {fila}")
    fm.append(f"descricao: {titulo}")
    if aberto:
        fm.append(f"aberto: {aberto}")
    if st in ESTADOS_FINAIS and m_enc:
        fm.append(f"encerrado: {m_enc.group(0)}")
    desc = item.get("descrição", "").strip()
    if titulo_bruto != titulo and titulo_bruto not in desc:
        desc = titulo_bruto + ("\n\n" + desc if desc else "")  # célula íntegra preservada no corpo
    campos = []
    for chave, rotulo in ROTULO_CAMPO:
        valor = (origem if chave == "origem" else item.get(chave, "")).strip()
        if valor in VAZIO or (chave == "ticket" and st in ESTADOS_FINAIS):
            continue
        campos.append(f"- **{rotulo}:** {reescreve_links(valor)}")
    corpo = (reescreve_links(desc) + "\n\n" if desc else "") + "\n".join(campos)
    conteudo = ("\n".join(fm) + "\n---\n\n" + f"# [{ident}] - {titulo}\n\n"
                + corpo.strip() + "\n")
    return f"DEBT_{ident}-{slug(titulo)}", conteudo, pend


def monta_item(ident, natureza, descricao, fila, local, gatilho, origem, ticket,
               corpo, hoje):
    """Dict no formato do parse_blocos, para o render_item escrever o arquivo.

    Chave sem valor fica **ausente**, nunca vazia: é assim que o render_item
    distingue campo não declarado de campo em branco, e é o que faz guarda e item
    incompleto se comportarem diferente (ADR-0030). Nada é inventado aqui — campo
    que falta vira pendência de triagem lá, e o cmd_novo recusa.
    """
    item = {"id": ident, "natureza": natureza, "status": "aberto",
            "título": descricao.strip(), "descrição": (corpo or "").strip(),
            "aberto em": hoje.isoformat()}
    for chave, valor in (("fila", fila), ("local", local), ("gatilho", gatilho),
                         ("origem", origem), ("ticket", ticket)):
        if (valor or "").strip():
            item[chave] = valor.strip()
    return item


def cmd_novo(root: Path, natureza, descricao, fila, local, gatilho, origem, ticket,
             corpo, hoje=None) -> int:
    """Cadastra um item em debts/ativos/ — o arquivo nasce válido ou não nasce.

    A conferência é o próprio parser do script (parse_arquivo_ativo + validar), e
    não uma segunda validação escrita à parte: duas implementações da mesma regra
    divergem, e a que reprova de verdade é a que a fila usa.
    """
    if not modo_novo(root):
        die(f"{DIR_ATIVOS}/ não encontrado — crie o registro pelo template da "
            f"projeto-init, ou converta o legado com `debito.py migrar`")
    if natureza == "guarda" and (fila or "").strip():
        print("[recusado] guarda não tem principal nem juros — não declare a fila")
        return 1
    if len(descricao) > DESCRICAO_LIMITE:
        print(f"[recusado] descricao com {len(descricao)} caracteres, acima do teto de "
              f"{DESCRICAO_LIMITE} — ela vira título do índice, da fila e da issue; "
              f"prosa longa vai no corpo, não na descricao")
        return 1
    disco, remotos = ids_em_disco(root), ids_em_refs_remotas(root)
    print(f"[id] {len(disco)} em disco + {len(remotos)} em refs remotas" if remotos
          else "[id] só o disco — nenhum ref remoto buscado (git fetch --prune)")
    item = monta_item(proximo_id(disco | remotos), natureza, descricao, fila, local,
                      gatilho, origem, ticket, corpo, hoje or date.today())
    nome, conteudo, pendencias = render_item(item)
    destino = root / DIR_ATIVOS / f"{nome}.md"
    if destino.exists():  # slug repetido: sobrescrever apagaria um item existente
        print(f"[recusado] {destino.relative_to(root)} já existe — mude a descrição")
        return 1
    destino.write_text(conteudo, encoding="utf-8")
    lido, erros = parse_arquivo_ativo(destino)
    erros += validar([lido], root) if lido else []
    if pendencias or erros:
        destino.unlink()  # item inválido nunca fica no disco (é o defeito do DT-077)
        for e in pendencias + erros:
            print(f"[recusado] {e}")
        return 1
    print(destino.relative_to(root))
    print(f"regenere o índice: python3 {Path(__file__).name} indice .")
    return 0


TICKET_LINHA = re.compile(r"^-\s+\*\*Ticket:\*\*.*$", re.M)


def cmd_quitar(root: Path, dt_id: str, como: str, ticket_ref: str, hoje=None) -> int:
    """Mecaniza o ritual manual de quitação/descarte (debito.md, 'Quitação/descarte').

    Precondição: o frontmatter já declara `estado: quitado|descartado` — a decisão
    de qual dos dois é de quem chama (edição de 1 linha), não deste comando. O que
    o comando mecaniza é o resto do ritual, que é onde o erro manual acontecia:
    `encerrado:` no frontmatter, a seção `#### Como foi quitado`, `Ticket` virando
    `Encerrado`, e o `git mv` para `_archive/` com a data certa no nome.
    """
    if not como.strip():
        print("[recusado] quitar exige --como descrevendo o que foi feito (2-4 frases)")
        return 1
    achados = sorted((root / DIR_ATIVOS).glob(f"DEBT_{dt_id}-*.md"))
    if not achados:
        print(f"[recusado] {dt_id} não encontrado em {DIR_ATIVOS}/ — já arquivado, ou nunca existiu")
        return 1
    if len(achados) > 1:
        print(f"[recusado] {dt_id} casou mais de um arquivo em {DIR_ATIVOS}/: "
              f"{', '.join(p.name for p in achados)} — numeração deveria ser única")
        return 1
    origem = achados[0]
    texto = origem.read_text(encoding="utf-8")
    m_fm = FRONTMATTER.match(texto)
    if not m_fm:
        print(f"[recusado] {dt_id}: frontmatter ausente ou sem fechamento — corrija antes de quitar")
        return 1
    fm = dict(FM_CHAVE.findall(m_fm.group(1)))
    if fm.get("estado") not in ESTADOS_FINAIS:
        print(f"[recusado] {dt_id}: estado atual '{fm.get('estado', '(vazio)')}' não é final — "
              f"edite o frontmatter para 'estado: quitado' ou 'estado: descartado' antes de rodar quitar")
        return 1
    hoje = hoje or date.today()
    data_iso = hoje.isoformat()

    fm_bruto = m_fm.group(1)
    if not re.search(r"^encerrado:", fm_bruto, re.M):
        fm_bruto = fm_bruto.rstrip("\n") + f"\nencerrado: {data_iso}"
    corpo = texto[m_fm.end():]

    encerrado_linha = (f"- **Encerrado:** {data_iso} · {ticket_ref}\n" if ticket_ref.strip()
                       else f"- **Encerrado:** {data_iso}\n")
    secao_quitado = f"\n#### Como foi quitado\n\n{como.strip()}\n"
    if TICKET_LINHA.search(corpo):
        corpo = TICKET_LINHA.sub(encerrado_linha.rstrip("\n"), corpo, count=1)
    else:
        corpo = corpo.rstrip("\n") + "\n\n" + encerrado_linha if CAMPO.search(corpo) else corpo
    primeiro_campo = CAMPO.search(corpo)
    if primeiro_campo:
        corpo = corpo[:primeiro_campo.start()].rstrip("\n") + "\n" + secao_quitado + "\n" \
                + corpo[primeiro_campo.start():]
    else:
        corpo = corpo.rstrip("\n") + "\n" + secao_quitado

    novo_texto = "---\n" + fm_bruto.rstrip("\n") + "\n---\n" + corpo
    original = texto
    origem.write_text(novo_texto, encoding="utf-8")
    lido, erros = parse_arquivo_ativo(origem)
    erros += validar([lido], root) if lido else []
    if erros:
        origem.write_text(original, encoding="utf-8")  # edição inválida nunca fica no disco
        for e in erros:
            print(f"[recusado] {e}")
        return 1

    destino_dir = root / DIR_ARCHIVE
    destino_dir.mkdir(parents=True, exist_ok=True)
    novo_nome = f"{origem.stem}_{hoje.strftime('%Y_%m_%d')}.md"
    destino = destino_dir / novo_nome
    r = subprocess.run(["git", "-C", str(root), "mv", str(origem.relative_to(root)),
                        str(destino.relative_to(root))], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"[erro] git mv falhou ({r.stderr.strip()}) — a edição ficou em "
              f"{origem.relative_to(root)}, mova à mão com git mv")
        return 1
    print(destino.relative_to(root))
    print(f"regenere o índice: python3 {Path(__file__).name} indice .")
    return 0


def migrar(root: Path) -> int:
    """Converte um DEBT.md legado (blocos ou tabela) para o layout debts/.

    Só transforma arquivos: nunca roda git de mutação nem acessa a rede; um
    `.claude/debts/` existente é reportado para o chamador mover com `git mv`
    (preserva a história). No-op se debts/ativos/ já contém arquivo — nunca
    sobrescreve migração anterior.
    """
    pasta_ativos = root / DIR_ATIVOS
    if pasta_ativos.is_dir() and any(pasta_ativos.glob("*.md")):
        print(f"{DIR_ATIVOS}/ já contém arquivos — nada a migrar (no-op).")
        return 0
    caminho_debt = root / "DEBT.md"
    if not caminho_debt.is_file():
        die(f"DEBT.md não encontrado em {root} — nada para migrar")
    texto = caminho_debt.read_text(encoding="utf-8")
    itens, formato = parse_blocos(texto), "blocos"
    if not itens and TABELA_ANTIGA.search(texto):
        itens, formato = parse_tabela(texto), "tabela"
    if not itens:
        print("Nenhum item DT-NNN encontrado no DEBT.md — nada a migrar.")
        return 0
    pendencias, criados_ativos, criados_arq = [], [], []
    pasta_ativos.mkdir(parents=True, exist_ok=True)
    for item in itens:
        nome, conteudo, pend = render_item(item)
        pendencias += pend
        if item.get("_aridade_divergente"):
            pendencias.append(f"{item['id']}: linha da tabela com aridade divergente do "
                              f"cabeçalho — campos não mapeados foram para a prosa e o estado "
                              f"ficou 'aberto' por conservadorismo; confira estado/datas à mão")
        if estado(item) in ESTADOS_FINAIS and (m := DATA.search(item.get("encerrado", ""))):
            destino = root / DIR_ARCHIVE
            destino.mkdir(parents=True, exist_ok=True)
            alvo = destino / f"{nome}_{m.group(0).replace('-', '_')}.md"
            criados_arq.append(alvo.name)
        else:
            alvo = pasta_ativos / f"{nome}.md"
            criados_ativos.append(alvo.name)
        alvo.write_text(conteudo, encoding="utf-8")
    readme = root / "debts" / "README.md"
    if not readme.is_file():  # nunca sobrescreve um README autoral
        readme.write_text(README_MINIMO, encoding="utf-8")
    itens_novos, _ = parse_ativos(root)
    caminho_debt.write_text(render_indice(root, itens_novos), encoding="utf-8")
    print(f"Migrado ({formato}): {len(criados_ativos)} ativo(s) em {DIR_ATIVOS}/, "
          f"{len(criados_arq)} encerrado(s) em {DIR_ARCHIVE}/; DEBT.md virou o índice gerado.")
    if (root / DEBTS_DIR).is_dir():
        comando = (f"git mv {DEBTS_DIR} {DIR_ARCHIVE}" if not (root / DIR_ARCHIVE).is_dir()
                   else f"git mv {DEBTS_DIR}/*.md {DIR_ARCHIVE}/")
        print(f"> {DEBTS_DIR}/ presente — mova você, preservando a história: {comando}")
    for p in pendencias:
        print(f"[triagem] {p}")
    if pendencias:
        print(f"> {len(pendencias)} pendência(s) de triagem — a fila sai com erro até "
              f"completá-las; nada foi inventado (ADR-0030).")
    print("> Revise o resultado e commite. Seção '## Lições' (se houver) move à mão "
          "para debts/LICOES.md — post-mortem não é item e não migra sozinho.")
    return 0


def main() -> None:
    if "--selftest" in sys.argv[1:]:
        selftest()
        return
    p = argparse.ArgumentParser(description="Fila de dívida técnica e projeção para tickets.")
    p.add_argument("comando", choices=("novo", "quitar", "fila", "exportar", "diff", "migrar", "indice"))
    p.add_argument("root", nargs="?", default=".", help="raiz do repositório (default: .)")
    p.add_argument("dt_id", nargs="?", help="quitar: DT-NNN a quitar")
    p.add_argument("--saida", help="diretório dos arquivos de importação (exportar)")
    p.add_argument("--projeto", default="",
                   help="chave do projeto Jira (exportar); sobrepõe motores.jira.projeto "
                        "do doc-profile.yaml, que é onde o destino deve ser declarado")
    p.add_argument("--externo", help="JSON do `gh issue list --json ...` (diff)")
    # novo: Local e Origem são escritos relativos à RAIZ; o script os reescreve para
    # os 2 níveis de debts/ativos/ (mesma função do migrar) — quem chama não conta '../'
    p.add_argument("--natureza", choices=NATUREZAS_PONTUAVEIS + ("guarda",), help="novo")
    p.add_argument("--descricao", help="novo: uma linha com o sintoma observável")
    p.add_argument("--fila", default="", help="novo: P{1|3|9}·J{1|3|9}·Pr{1|3|9} (guarda não tem)")
    p.add_argument("--local", default="", help="novo: artefato, relativo à raiz")
    p.add_argument("--gatilho", default="", help="novo: quando reavaliar/corrigir")
    p.add_argument("--origem", default="", help="novo: delta, PR ou sessão de origem")
    p.add_argument("--ticket", default="", help="novo: chave do ticket, se já existir")
    p.add_argument("--corpo-arquivo", help="novo: prosa do corpo (default: stdin, se houver)")
    p.add_argument("--como", default="", help="quitar: 2-4 frases do que foi feito")
    p.add_argument("--ticket-ref", default="", help="quitar: referência p/ o campo Encerrado")
    p.add_argument("--faixa", choices=("alta", "media", "baixa"), default="",
                   help="exportar: recorta por faixa de score (default: todos os itens)")
    a = p.parse_args()
    root = Path(a.root).resolve()
    if a.comando == "migrar":
        sys.exit(migrar(root))
    if a.comando == "indice":
        sys.exit(cmd_indice(root))
    if a.comando == "novo":
        if not (a.natureza and a.descricao):
            die("novo exige --natureza e --descricao")
        corpo = (Path(a.corpo_arquivo).read_text(encoding="utf-8") if a.corpo_arquivo
                 else "" if sys.stdin.isatty() else sys.stdin.read())
        sys.exit(cmd_novo(root, a.natureza, a.descricao, a.fila, a.local, a.gatilho,
                          a.origem, a.ticket, corpo))
    if a.comando == "quitar":
        if not a.dt_id:
            die("quitar exige DT-NNN: debito.py quitar [ROOT] DT-NNN --como '...'")
        sys.exit(cmd_quitar(root, a.dt_id, a.como, a.ticket_ref))
    if not (modo_novo(root) or (root / "DEBT.md").is_file()):
        die(f"nem {DIR_ATIVOS}/ nem DEBT.md encontrados em {root}")
    if a.comando == "fila":
        sys.exit(cmd_fila(root))
    if a.comando == "exportar":
        # Destino declarado no repo vence a memória de quem digita (delta-035, DT-033);
        # a flag sobrepõe, para exportação pontual (sandbox) sem editar arquivo versionado.
        _, projeto_perfil = ler_destino_tickets(root)
        projeto = a.projeto or projeto_perfil or ""
        sys.exit(exportar(root, Path(a.saida) if a.saida else root / "docs" / "tickets",
                         projeto, a.faixa))
    if not a.externo:
        die("diff exige --externo ESTADO.json (saída de `gh issue list --json ...`)")
    sys.exit(diff(root, Path(a.externo)))


# ---------------------------------------------------------------- selftest


CABECALHO_FIXTURE = "# DEBT.md\n\n## Registro\n\n"


def linha(ident, natureza="débito", titulo="Título curto", local="[alvo](alvo.py)",
          fila="P3·J9·Pr9", gatilho="quando doer", status="aberto", externo="",
          descricao="descrição do sintoma", encerrado=""):
    """Um bloco de fixture. Campo com valor vazio simplesmente não é declarado —
    é assim que guarda e item encerrado se distinguem de item ativo incompleto."""
    campos = [("Fila", fila), ("Local", local), ("Gatilho", gatilho),
              ("Origem", "[PR #1](../../pull/1) · 2026-01-01"),
              ("Ticket", externo), ("Encerrado", encerrado)]
    corpo = "".join(f"- **{nome}:** {valor}\n" for nome, valor in campos if valor)
    return f"### {ident} · {natureza} · {status}\n**{titulo}**\n\n{descricao}\n\n{corpo}\n"


def selftest() -> None:
    import ast
    import contextlib
    import io
    import tempfile

    def quieto(fn, *args, **kwargs):
        """Roda um subcomando engolindo a saída — o selftest reporta o próprio veredito."""
        with contextlib.redirect_stdout(io.StringIO()):
            return fn(*args, **kwargs)

    def montar(linhas: str, com_alvo=True):
        d = tempfile.mkdtemp()
        root = Path(d)
        (root / "DEBT.md").write_text(CABECALHO_FIXTURE + linhas, encoding="utf-8")
        if com_alvo:
            (root / "alvo.py").write_text("x = 1\n", encoding="utf-8")
        return root

    # score: função pura, sem I/O
    assert score(3, 9, 9) == 27.0 and score(9, 3, 1) == (1 / 3), "fórmula do score mudou"
    assert score(1, 1, 1) == 1.0 and round(score(9, 1, 1), 2) == 0.11, "faixa do score mudou"

    # parse da fila e dos sufixos
    assert parse_fila("P3·J9·Pr9") == (3, 9, 9, False, None)
    assert parse_fila("`P3·J9·Pr9`") == (3, 9, 9, False, None), "crase de formatação quebrou a fila"
    assert parse_fila("P9·J3·Pr9 · trilha")[3] is True
    assert parse_fila("P1·J1·Pr1 · !security(2026-09-01)")[4] == ("security", "2026-09-01")
    for ruim in ("P2·J9·Pr9", "P3-J9-Pr9", "", "P3·J9", "P3·J9·Pr9 · bagunça",
                 "P3·J9·Pr9 · !secutiry(2026-09-01)"):  # typo em 'security' não pode passar
        assert parse_fila(ruim) is None, f"fila malformada aceita: {ruim!r}"

    # precedência: cada override na ordem do enum, depois trilha, depois o resto
    def entrada(trilha=False, override=None):
        return {"trilha": trilha, "override": override}
    ordem_prec = [precedencia(entrada(override=(o, "2026-01-01"))) for o in OVERRIDES]
    assert ordem_prec == sorted(ordem_prec) and len(set(ordem_prec)) == len(OVERRIDES), \
        f"overrides não respeitam a ordem do enum: {ordem_prec}"
    assert max(ordem_prec) < precedencia(entrada(trilha=True)) < precedencia(entrada()), \
        "override deve vir antes de trilha, e trilha antes do resto"

    # registro limpo passa; guarda sem Fila/Local também
    root = montar(linha("DT-001") + linha("DT-002", natureza="guarda", local="", fila="", status="vigente"))
    itens = parse_blocos((root / "DEBT.md").read_text(encoding="utf-8"))
    assert len(itens) == 2, f"parser perdeu bloco: {itens}"
    assert validar(itens, root) == [], f"fixture limpa acusada: {validar(itens, root)}"
    assert itens[0]["descrição"] == "descrição do sintoma", f"descrição mal recortada: {itens[0]}"

    # REGRESSÃO (lição 2026-07-28): a descrição menciona a palavra 'aberto' e cita a
    # própria sintaxe de campo. Busca solta leria o item como ativo e o `- **Fila:**`
    # da prosa como fila real; só a âncora de início de linha do bloco separa os dois.
    prosa = linha("DT-003", local="", fila="", status="quitado",
                  encerrado="2026-07-31 · [#85](../../pull/85) — ficou aberto 7 dias após satisfeito",
                  descricao="A dívida seguia aberto no papel. Exemplo citado: `- **Fila:** P9·J9·Pr9`.")
    root_p = montar(prosa)
    itens_p = parse_blocos((root_p / "DEBT.md").read_text(encoding="utf-8"))
    assert estado(itens_p[0]) == "quitado", f"prosa enganou o estado: {estado(itens_p[0])}"
    assert itens_p[0].get("fila", "") == "", "sintaxe citada na prosa virou campo Fila"
    assert validar(itens_p, root_p) == [], "item quitado com prosa foi cobrado como ativo"
    assert montar_fila(itens_p, root_p) == [], "item quitado entrou na fila"

    # o bloco aceita descrição de várias linhas e caractere que a tabela exigia escapar
    multi = linha("DT-004", titulo="Pipe | e travessão — livres no bloco",
                  descricao="Primeira linha da descrição.\n\nSegundo parágrafo, com `código` e | pipe.")
    itens_multi = parse_blocos(multi)
    assert itens_multi[0]["título"] == "Pipe | e travessão — livres no bloco"
    assert "Segundo parágrafo" in itens_multi[0]["descrição"], "descrição multilinha truncada"

    # validações bloqueantes, uma por campo
    casos = {
        "título": linha("DT-010", titulo=""),
        "Local": linha("DT-011", local=""),
        "Fila": linha("DT-012", fila="P2·J2·Pr2"),
        "Gatilho": linha("DT-013", status="aceito", gatilho=""),
    }
    for campo_esperado, fixture in casos.items():
        r = montar(fixture)
        erros = validar(parse_blocos((r / "DEBT.md").read_text(encoding="utf-8")), r)
        assert any(campo_esperado in e for e in erros), f"{campo_esperado} não acusado: {erros}"
        assert all(e.startswith("DT-") for e in erros), f"erro sem o DT-NNN: {erros}"
    r_morto = montar(linha("DT-014", local="[x](nao-existe.py)"))
    assert any("inexistente" in e for e in
               validar(parse_blocos((r_morto / "DEBT.md").read_text(encoding="utf-8")), r_morto)), \
        "link morto no Local não acusado"
    r_estado = montar(linha("DT-015", status="pendente"))
    assert any("fora do conjunto" in e for e in
               validar(parse_blocos((r_estado / "DEBT.md").read_text(encoding="utf-8")), r_estado)), \
        "status inventado não acusado"
    r_guarda = montar(linha("DT-016", natureza="guarda", status="vigente", fila="P1·J1·Pr1"))
    assert any("guarda" in e for e in
               validar(parse_blocos((r_guarda / "DEBT.md").read_text(encoding="utf-8")), r_guarda)), \
        "guarda com fila preenchida não acusada"
    r_sem_data = montar(linha("DT-017", local="", fila="", status="quitado"))
    assert any("Encerrado" in e for e in
               validar(parse_blocos((r_sem_data / "DEBT.md").read_text(encoding="utf-8")), r_sem_data)), \
        "quitado sem o campo Encerrado não acusado (R18 exige data e ref)"

    # os cinco estados válidos convivem; só o pontuável exige os campos novos
    r_estados = montar(
        linha("DT-050", status="aberto")
        + linha("DT-051", status="aceito", gatilho="quando o motor mudar")
        + linha("DT-052", natureza="guarda", local="", fila="", status="vigente")
        + linha("DT-053", local="", fila="", status="descartado", encerrado="2026-08-01 — virou obsoleto")
        + linha("DT-054", local="", fila="", status="quitado", encerrado="2026-08-01 · [#99](../../issues/99)"))
    itens_e = parse_blocos((r_estados / "DEBT.md").read_text(encoding="utf-8"))
    assert validar(itens_e, r_estados) == [], f"estados válidos acusados: {validar(itens_e, r_estados)}"
    assert {e["item"]["id"] for e in montar_fila(itens_e, r_estados)} == {"DT-050", "DT-051"}, \
        "só item ativo e pontuável entra na fila"

    # registro em tabela (delta-023 ou o template ainda distribuído): avisa, não quebra
    legado_txt = ("## Registro\n\n| ID | Natureza | Descrição | Origem | Aberto em "
                  "| Gatilho de correção | Status |\n|---|---|---|---|---|---|---|\n"
                  "| DT-001 | débito | x | PR #1 | 2026-01-01 | quando doer | aberto |\n")
    r_legado = Path(tempfile.mkdtemp())
    (r_legado / "DEBT.md").write_text(legado_txt, encoding="utf-8")
    assert parse_blocos(legado_txt) == [], "tabela não deveria produzir bloco"
    aviso = io.StringIO()
    with contextlib.redirect_stdout(aviso):
        assert carregar(r_legado) == [], "formato antigo deveria devolver lista vazia"
        assert cmd_fila(r_legado) == 0, "cmd_fila não degradou com registro em tabela"
    assert "formato de tabela" in aviso.getvalue(), "faltou instruir a conversão do formato antigo"

    # ordenação: override → trilha → score desc
    root_o = montar(
        linha("DT-020", fila="P1·J1·Pr1")                                # score 1
        + linha("DT-021", fila="P3·J9·Pr9")                              # score 27
        + linha("DT-022", fila="P9·J9·Pr9 · trilha")                     # trilha
        + linha("DT-023", fila="P9·J1·Pr1 · !contract(2026-12-01)")      # override tardio
        + linha("DT-024", fila="P9·J1·Pr1 · !security(2026-09-01)"))     # override primeiro
    ordem = [e["item"]["id"] for e in montar_fila(itens=parse_blocos(
        (root_o / "DEBT.md").read_text(encoding="utf-8")), root=root_o)]
    assert ordem == ["DT-024", "DT-023", "DT-022", "DT-021", "DT-020"], f"ordem errada: {ordem}"

    # exportar: JSON canônico + .sh unitário do acli, item já projetado é pulado
    root_e = montar(linha("DT-030") + linha("DT-031", externo="[#7](../../issues/7)"))
    saida = root_e / "out"
    assert quieto(exportar, root_e, saida, "PROJ") == 0
    dados = json.loads((saida / "tickets.json").read_text(encoding="utf-8"))
    assert len(dados["items"]) == 2 and dados["version"] == 1
    assert dados["items"][0]["title"].startswith("[DT-0"), "título sem o ID como prefixo"
    assert any(l == "dt:DT-030" for l in dados["items"][0]["labels"]), "etiqueta de idempotência ausente"
    acli_sh = (saida / "tickets-acli.sh").read_text(encoding="utf-8")
    assert "create-bulk" not in acli_sh, "bulk quebrado não pode voltar (DT-021)"
    assert acli_sh.count("acli jira workitem create ") == 1, "item já projetado entrou no roteiro do Jira"
    assert f"--project {shlex.quote('PROJ')}" in acli_sh, "roteiro do Jira sem chave de projeto não roda"
    corpo_dt030 = (saida / "corpo-DT-030.md").read_text(encoding="utf-8")
    assert corpo_dt030 == dados["items"][0]["body"], "corpo do ticket não bateu byte a byte com o canônico"
    assert not (saida / "corpo-DT-031.md").exists(), "item já projetado gerou corpo no roteiro do Jira"
    sem_projeto = root_e / "out2"
    assert quieto(exportar, root_e, sem_projeto) == 0
    assert not (sem_projeto / "tickets-acli.sh").exists(), \
        "sem --projeto o dialeto do Jira deve ser omitido, não emitido quebrado"
    # O módulo não fala com a rede. A checagem lê a árvore sintática, não o texto:
    # uma busca por "import urllib" acharia a própria lista de proibidos abaixo — a
    # lição de 2026-07-28 pegando este selftest pela segunda vez.
    arvore = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    importados = {alias.name.split(".")[0] for no in ast.walk(arvore)
                  if isinstance(no, ast.Import) for alias in no.names}
    importados |= {no.module.split(".")[0] for no in ast.walk(arvore)
                   if isinstance(no, ast.ImportFrom) and no.module}
    rede = importados & {"urllib", "http", "socket", "requests", "httpx", "ftplib", "asyncio"}
    assert not rede, f"módulo passou a acessar a rede: {rede}"
    sh = (saida / "tickets-gh.sh").read_text(encoding="utf-8")
    assert "gh issue create" in sh and "DT-031 já projetado" in sh, "roteiro do gh incorreto"
    # Comando só conta na posição canônica (início da linha, fora de comentário): o
    # próprio roteiro cita 'gh issue create' num comentário, e busca solta acharia
    # ele primeiro — a lição de 2026-07-28 reincidindo dentro do próprio selftest.
    comandos = [l for l in sh.splitlines() if l and not l.lstrip().startswith("#")]
    pos_label = next(i for i, l in enumerate(comandos) if l.startswith("gh label create"))
    pos_issue = next(i for i, l in enumerate(comandos) if l.startswith("gh issue create"))
    assert pos_label < pos_issue, "etiqueta precisa ser criada antes do issue — senão o gh recusa"
    assert "dt:DT-031" not in sh, "etiqueta de item já projetado entrou no roteiro"
    assert (root_e / "DEBT.md").read_text(encoding="utf-8").find("score") == -1, \
        "score foi persistido no DEBT.md"

    # diff: os três casos de divergência + o caso limpo
    estado_ext = root_e / "estado.json"
    estado_ext.write_text(json.dumps([
        {"number": 7, "state": "CLOSED", "labels": [{"name": "dt:DT-031"}]},
        {"number": 9, "state": "OPEN", "labels": [{"name": "dt:DT-099"}]},
    ]), encoding="utf-8")
    saida_diff = io.StringIO()
    with contextlib.redirect_stdout(saida_diff):
        codigo = diff(root_e, estado_ext)
    relatorio = saida_diff.getvalue()
    assert codigo == 1, "diff não acusou divergências"
    for esperado in ("DT-030", "DT-031", "DT-099"):
        assert esperado in relatorio, f"diff não cobriu o caso de {esperado}"
    antes = (root_e / "DEBT.md").read_text(encoding="utf-8")
    quieto(diff, root_e, estado_ext)
    assert (root_e / "DEBT.md").read_text(encoding="utf-8") == antes, "diff alterou o DEBT.md"
    # caso limpo: item projetado e ticket aberto do outro lado → zero divergência
    root_ok = montar(linha("DT-060", externo="[#1](../../issues/1)"))
    sincronizado = root_ok / "estado.json"
    sincronizado.write_text(json.dumps(
        [{"number": 1, "state": "OPEN", "labels": [{"name": "dt:DT-060"}]}]), encoding="utf-8")
    limpo = io.StringIO()
    with contextlib.redirect_stdout(limpo):
        codigo_limpo = diff(root_ok, sincronizado)
    assert codigo_limpo == 0, "diff acusou divergência em registro sincronizado"
    assert "Nenhuma divergência" in limpo.getvalue(), "diff limpo não reportou sincronia"

    # arquivado em .claude/debts/ (ADR-0028): o ID sai do DEBT.md sem virar falso
    # "não existe"; ticket fechado é sincronia, ticket aberto é órfão detectável
    pasta_arq = root_ok / DEBTS_DIR
    pasta_arq.mkdir(parents=True)
    (pasta_arq / "DEBT_DT-070-caso-arquivado_2026_01_01.md").write_text(
        "# DT-070 · débito · quitado\n", encoding="utf-8")
    assert ids_arquivados(root_ok) == {"DT-070"}, "ID arquivado não lido do nome do arquivo"
    estado_arq = root_ok / "estado-arq.json"
    estado_arq.write_text(json.dumps(
        [{"number": 1, "state": "OPEN", "labels": [{"name": "dt:DT-060"}]},
         {"number": 11, "state": "CLOSED", "labels": [{"name": "dt:DT-070"}]}]), encoding="utf-8")
    fechado = io.StringIO()
    with contextlib.redirect_stdout(fechado):
        assert diff(root_ok, estado_arq) == 0, "arquivado com ticket fechado virou divergência"
    assert "DT-070" not in fechado.getvalue(), "arquivado sincronizado apareceu no relatório"
    estado_arq.write_text(json.dumps(
        [{"number": 1, "state": "OPEN", "labels": [{"name": "dt:DT-060"}]},
         {"number": 11, "state": "OPEN", "labels": [{"name": "dt:DT-070"}]}]), encoding="utf-8")
    orfao = io.StringIO()
    with contextlib.redirect_stdout(orfao):
        assert diff(root_ok, estado_arq) == 1, "órfão de item arquivado não mudou o exit"
    rel_orfao = orfao.getvalue()
    assert "DT-070" in rel_orfao and "arquivado" in rel_orfao and "fechar o ticket" in rel_orfao, \
        "ticket aberto de item arquivado não acusado como órfão"
    assert "não existe" not in rel_orfao, "item arquivado tratado como desconhecido"

    # estado final ainda no DEBT.md: a fila avisa o candidato a arquivamento, sem mudar o exit
    r_cand = montar(linha("DT-080") + linha("DT-081", local="", fila="", status="quitado",
                                            encerrado="2026-01-02 · [#5](../../issues/5)"))
    cand = io.StringIO()
    with contextlib.redirect_stdout(cand):
        assert cmd_fila(r_cand) == 0, "aviso de arquivamento não pode mudar o exit"
    assert "candidato" in cand.getvalue() and "DT-081" in cand.getvalue(), \
        "estado final no DEBT.md sem aviso de arquivamento"
    sem_finais = io.StringIO()
    with contextlib.redirect_stdout(sem_finais):
        cmd_fila(montar(linha("DT-082")))
    assert "candidato" not in sem_finais.getvalue(), "aviso de arquivamento sem item em estado final"

    print("selftest: OK (score, parser posicional, regressão de prosa, validações, ordem, exportar, diff, arquivados)")
    selftest_novo()
    selftest_quitar()
    selftest_git()


def selftest_novo() -> None:
    """Layout debts/ (ADR-0030): frontmatter, precedência dual-mode, união e migrar.

    Os asserts usam os literais "debts/ativos"/"debts/_archive", nunca as constantes —
    fixture derivada da constante sob teste é cega ao valor (lição 2026-08-10).
    """
    import contextlib
    import io
    import tempfile

    assert DIR_ATIVOS == "debts/ativos" and DIR_ARCHIVE == "debts/_archive", \
        "constantes de layout divergiram do contrato documentado (R18)"

    def quieto(fn, *args, **kwargs):
        with contextlib.redirect_stdout(io.StringIO()):
            return fn(*args, **kwargs)

    def falado(fn, *args, **kwargs):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            r = fn(*args, **kwargs)
        return r, buf.getvalue()

    def raiz():
        r = Path(tempfile.mkdtemp())
        (r / "alvo.py").write_text("x = 1\n", encoding="utf-8")
        return r

    def arquivo(root, ident="DT-001", topico="caso-teste", natureza="débito",
                estado_item="aberto", fila="P3·J9·Pr9", descricao="Sintoma curto",
                aberto="2026-01-01", prosa="Prosa da descrição.",
                local="[alvo](../../alvo.py)", gatilho="quando doer",
                origem="[PR #1](../../../../pull/1)", ticket="", encerrado="",
                nome=None, sem_id=False, bruto=None):
        pasta = root / "debts/ativos"
        pasta.mkdir(parents=True, exist_ok=True)
        destino = pasta / (nome or f"DEBT_{ident}-{topico}.md")
        if bruto is not None:
            destino.write_text(bruto, encoding="utf-8")
            return root
        fm = ([] if sem_id else [f"id: {ident}"]) + [f"natureza: {natureza}",
                                                     f"estado: {estado_item}"]
        if fila:
            fm.append(f"fila: {fila}")
        if descricao:
            fm.append(f"descricao: {descricao}")
        if aberto:
            fm.append(f"aberto: {aberto}")
        campos = [("Local", local), ("Gatilho", gatilho), ("Origem", origem),
                  ("Ticket", ticket), ("Encerrado", encerrado)]
        corpo = "".join(f"- **{n}:** {v}\n" for n, v in campos if v)
        h1 = f"# [{ident}] - {descricao}\n\n" if descricao else ""
        destino.write_text("---\n" + "\n".join(fm) + "\n---\n\n" + h1 + prosa + "\n\n" + corpo,
                           encoding="utf-8")
        return root

    # arquivo válido: carrega, valida, normaliza o Local e entra na fila
    r = arquivo(raiz())
    itens = quieto(carregar, r)
    assert itens and len(itens) == 1, f"layout novo não carregou: {itens}"
    assert itens[0]["título"] == "Sintoma curto", "descricao não virou título"
    assert "(alvo.py)" in itens[0]["local"], f"Local não normalizado: {itens[0]['local']}"
    fila_nova = montar_fila(itens, r)
    assert len(fila_nova) == 1 and fila_nova[0]["score"] == 27.0, "fila do layout novo errada"

    # paridade com o legado: mesmo item nos dois layouts → mesmo canônico, salvo source
    r_leg = Path(tempfile.mkdtemp())
    (r_leg / "alvo.py").write_text("x = 1\n", encoding="utf-8")
    (r_leg / "DEBT.md").write_text(
        CABECALHO_FIXTURE + linha("DT-001", titulo="Sintoma curto"), encoding="utf-8")
    it_leg = quieto(carregar, r_leg)
    can_leg = canonico(montar_fila(it_leg, r_leg), fonte_de(r_leg))
    can_novo = canonico(fila_nova, fonte_de(r))
    assert can_leg["source"] == "DEBT.md" and can_novo["source"] == "debts/ativos", \
        f"source errado: {can_leg['source']} / {can_novo['source']}"
    for chave in ("id", "title", "labels", "score", "fila", "externo"):
        assert can_leg["items"][0][chave] == can_novo["items"][0][chave], \
            f"paridade quebrou em '{chave}': {can_leg['items'][0][chave]} ≠ {can_novo['items'][0][chave]}"

    # aviso de deprecação só no legado; precedência do novo ignora blocos remanescentes
    _, voz_leg = falado(carregar, r_leg)
    assert "Layout legado" in voz_leg, "caminho legado sem aviso de deprecação"
    (r / "DEBT.md").write_text(CABECALHO_FIXTURE + linha("DT-099"), encoding="utf-8")
    itens_prec = quieto(carregar, r)
    assert [i["id"] for i in itens_prec] == ["DT-001"], "bloco remanescente entrou no layout novo"
    r_vazio = raiz()
    (r_vazio / "debts/ativos").mkdir(parents=True)
    (r_vazio / "DEBT.md").write_text(CABECALHO_FIXTURE + linha("DT-098"), encoding="utf-8")
    codigo, voz_vazio = falado(cmd_fila, r_vazio)
    assert codigo == 0 and "precedência" in voz_vazio, \
        "ativos/ vazio com DEBT.md legado precisa avisar a precedência"

    # malformações estruturais: uma fixture por caso, erro nomeando DT/arquivo
    def erros_de(root):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            assert carregar(root) is None, "malformação passou sem erro"
        return buf.getvalue()

    assert "frontmatter ausente" in erros_de(arquivo(raiz(), bruto="# DT-001 sem frontmatter\n"))
    assert "sem fechamento" in erros_de(arquivo(raiz(), bruto="---\nid: DT-001\n"))
    voz = erros_de(arquivo(raiz(), bruto="---\nid: DT-001\nnatureza: débito\nestado: aberto\n"
                                         "descrição: Com acento\naberto: 2026-01-01\n---\nx\n"))
    assert "sem acento" in voz and "obrigatória 'descricao'" in voz, \
        f"chave acentuada não explicada: {voz}"
    assert "≠ nome" in erros_de(arquivo(raiz(), bruto="---\nid: DT-002\nnatureza: débito\n"
                                                      "estado: aberto\ndescricao: x\n"
                                                      "aberto: 2026-01-01\n---\nx\n"))
    assert "fora do padrão" in erros_de(arquivo(raiz(), nome="DEBT_DT-003_Topico.md"))
    assert "fora do conjunto" in erros_de(arquivo(raiz(), natureza="debito"))
    assert "não declare Fila" in erros_de(arquivo(raiz(), natureza="guarda", estado_item="vigente",
                                                  local="", gatilho="", fila="P1·J1·Pr1"))
    assert "no corpo" in erros_de(arquivo(raiz(), bruto="---\nid: DT-001\nnatureza: débito\n"
                                                        "estado: aberto\ndescricao: x\nfila: P3·J9·Pr9\n"
                                                        "aberto: 2026-01-01\n---\nx\n\n"
                                                        "- **Fila:** P1·J1·Pr1\n"))
    assert "fora do repositório" in erros_de(arquivo(raiz(), local="[x](../../../fora.py)"))
    dup = arquivo(arquivo(raiz(), topico="a"), topico="b")
    assert "duplicado" in erros_de(dup)
    r_dup_arq = arquivo(raiz())
    (r_dup_arq / "debts/_archive").mkdir(parents=True)
    (r_dup_arq / "debts/_archive/DEBT_DT-001-antigo_2026_01_01.md").write_text("x\n", encoding="utf-8")
    assert "nunca é reutilizado" in erros_de(r_dup_arq)

    # regressão de prosa no layout novo: "estado: aberto" no corpo é prosa, não campo
    r_prosa = arquivo(raiz(), estado_item="quitado", fila="", local="", gatilho="",
                      encerrado="2026-01-02 · [#5](../../../../issues/5)",
                      prosa="O relatório dizia\nestado: aberto\ne citava `- **Fila:** P9·J9·Pr9`.")
    it_prosa = quieto(carregar, r_prosa)
    assert it_prosa and estado(it_prosa[0]) == "quitado", "prosa enganou o estado no layout novo"
    assert quieto(cmd_fila, r_prosa) == 0 and montar_fila(it_prosa, r_prosa) == [], \
        "item final entrou na fila no layout novo"

    # TÍTULO H1 (delta-048): primeira linha do corpo é espelho validado do frontmatter
    fm_base = ("---\nid: DT-001\nnatureza: débito\nestado: aberto\nfila: P3·J9·Pr9\n"
               "descricao: Sintoma curto\naberto: 2026-01-01\n---\n\n")
    corpo_base = "Prosa.\n\n- **Local:** [a](../../alvo.py)\n- **Gatilho:** g\n- **Origem:** o\n"
    assert "primeira linha do corpo" in erros_de(arquivo(raiz(), bruto=fm_base + corpo_base)), \
        "H1 ausente não acusado"
    assert "divergente" in erros_de(arquivo(raiz(), bruto=fm_base + "# [DT-002] - Sintoma curto\n\n"
                                            + corpo_base)), "H1 com id divergente não acusado"
    assert "divergente" in erros_de(arquivo(raiz(), bruto=fm_base + "# [DT-001] - Outro texto\n\n"
                                            + corpo_base)), "H1 com texto divergente não acusado"
    it_h1 = quieto(carregar, arquivo(raiz()))
    assert it_h1 and not it_h1[0]["descrição"].startswith("#"), \
        f"H1 vazou para a descrição parseada: {it_h1[0]['descrição']!r}"

    # união dos arquivados: debts/_archive/ e .claude/debts/ contam juntos
    r_uni = raiz()
    (r_uni / "debts/_archive").mkdir(parents=True)
    (r_uni / "debts/_archive/DEBT_DT-070-novo_2026_01_01.md").write_text("x\n", encoding="utf-8")
    (r_uni / ".claude/debts").mkdir(parents=True)
    (r_uni / ".claude/debts/DEBT_DT-071-legado_2026_01_01.md").write_text("x\n", encoding="utf-8")
    assert ids_arquivados(r_uni) == {"DT-070", "DT-071"}, "união das pastas de archive falhou"

    # diff no layout novo: sincronia, órfão de arquivado e nunca o falso "não existe"
    r_diff = arquivo(raiz(), ticket="[#1](../../../../issues/1)")
    (r_diff / "debts/_archive").mkdir(parents=True)
    (r_diff / "debts/_archive/DEBT_DT-070-x_2026_01_01.md").write_text("x\n", encoding="utf-8")
    estado_json = r_diff / "estado.json"
    estado_json.write_text(json.dumps(
        [{"number": 1, "state": "OPEN", "labels": [{"name": "dt:DT-001"}]},
         {"number": 2, "state": "OPEN", "labels": [{"name": "dt:DT-070"}]}]), encoding="utf-8")
    codigo, rel = falado(diff, r_diff, estado_json)
    assert codigo == 1 and "DT-070" in rel and "arquivado" in rel, "órfão de arquivado não acusado"
    assert "não existe" not in rel, "arquivado do layout novo virou 'não existe'"

    # REGRESSÃO (família 2026-08-03): texto do link igual ao alvo — a troca é por
    # span do grupo; um replace de string reescreveria o texto e mataria o alvo.
    assert reescreve_links("[CLAUDE.md](CLAUDE.md)") == "[CLAUDE.md](../../CLAUDE.md)", \
        "reescrita mexeu no texto do link em vez do alvo"
    r_igual = arquivo(raiz(), local="[alvo.py](../../alvo.py)")
    it_igual = quieto(carregar, r_igual)
    assert it_igual and "[alvo.py](alvo.py)" in it_igual[0]["local"], \
        "normalização mexeu no texto do link em vez do alvo"

    # migrar (blocos): paridade de fila, ponteiro, ticket mantido como chave externa
    r_mig = Path(tempfile.mkdtemp())
    (r_mig / "alvo.py").write_text("x = 1\n", encoding="utf-8")
    bloco = linha("DT-001", externo="[#7](../../issues/7)").replace(
        "· 2026-01-01", "· aberto em 2026-01-01")
    (r_mig / "DEBT.md").write_text(CABECALHO_FIXTURE + bloco, encoding="utf-8")
    fila_antes = montar_fila(quieto(carregar, r_mig), r_mig)
    assert quieto(migrar, r_mig) == 0
    assert (r_mig / "debts/ativos/DEBT_DT-001-titulo-curto.md").is_file(), \
        "migrar não criou o arquivo do ativo"
    assert "índice dos débitos ativos" in (r_mig / "DEBT.md").read_text(encoding="utf-8"), \
        "migrar não reescreveu o DEBT.md como índice gerado"
    fila_depois = montar_fila(quieto(carregar, r_mig), r_mig)
    assert [ (e["item"]["id"], e["score"]) for e in fila_antes ] == \
           [ (e["item"]["id"], e["score"]) for e in fila_depois ], "migrar mudou a fila"
    texto_novo = (r_mig / "debts/ativos/DEBT_DT-001-titulo-curto.md").read_text(encoding="utf-8")
    assert "# [DT-001] - Título curto" in texto_novo, "migrar (blocos) não gerou o título H1"
    assert "(../../../../issues/7)" in texto_novo, "ticket não reescrito para a profundidade nova"
    can_mig = canonico(fila_depois, fonte_de(r_mig))
    assert can_mig["items"][0]["externo"], "migrar perdeu a chave externa do Ticket"
    _, voz_noop = falado(migrar, r_mig)
    assert "no-op" in voz_noop, "migrar sobre ativos/ povoado precisa ser no-op"

    # migrar (tabela): coluna por índice, quitado vai ao archive, sem fila = triagem
    r_tab = Path(tempfile.mkdtemp())
    (r_tab / "DEBT.md").write_text(
        "# DEBT.md\n\n## Registro\n\n"
        "| ID | Natureza | Descrição | Origem | Aberto em | Gatilho de correção | Status |\n"
        "|---|---|---|---|---|---|---|\n"
        "| DT-001 | débito | Atalho no parser | PR #1 | 2026-01-01 | quando doer | aberto |\n"
        "| DT-002 | pendência | Doc pendente | PR #2 | 2026-01-02 | — | quitado (2026-02-01, PR #9) |\n",
        encoding="utf-8")
    (r_tab / ".claude/debts").mkdir(parents=True)
    _, voz_tab = falado(migrar, r_tab)
    assert (r_tab / "debts/ativos/DEBT_DT-001-atalho-no-parser.md").is_file(), \
        "linha ativa da tabela não virou arquivo"
    arq_gerados = list((r_tab / "debts/_archive").glob("DEBT_DT-002-*_2026_02_01.md"))
    assert arq_gerados, "quitado da tabela não foi para debts/_archive com a data"
    assert "encerrado: 2026-02-01" in arq_gerados[0].read_text(encoding="utf-8")
    assert "[triagem] DT-001: sem fila" in voz_tab, "tabela sem fila não entrou na triagem"
    # REGRESSÃO (delta-050, caso real de um repo consumidor): link markdown na célula
    # Descrição não pode virar link morto em descricao:/H1 — título vira texto plano
    # e a célula íntegra vai ao corpo com os links reescritos
    r_link = Path(tempfile.mkdtemp())
    (r_link / "DEBT.md").write_text(
        "# DEBT.md\n\n## Registro\n\n"
        "| ID | Natureza | Descrição | Origem | Aberto em | Gatilho de correção | Status |\n"
        "|---|---|---|---|---|---|---|\n"
        "| DT-001 | débito | Capa fora do [doc-profile.yaml](doc-profile.yaml) declarado | PR #1 | 2026-01-01 | quando doer | aberto |\n",
        encoding="utf-8")
    quieto(migrar, r_link)
    t_link = next((r_link / "debts/ativos").glob("DEBT_DT-001-*.md")).read_text(encoding="utf-8")
    fm_link, corpo_link = t_link.split("---\n", 2)[1], t_link.split("---\n", 2)[2]
    assert "](" not in fm_link, f"descricao: levou link markdown: {fm_link}"
    assert corpo_link.lstrip("\n").split("\n")[0] == "# [DT-001] - Capa fora do doc-profile.yaml declarado", \
        f"H1 não virou texto plano: {corpo_link.splitlines()[:2]}"
    assert "](../../doc-profile.yaml)" in corpo_link, \
        "célula íntegra não foi preservada no corpo com o link reescrito"
    assert "git mv" in voz_tab, "migrar não instruiu o move do .claude/debts/"
    assert "estado: aberto" in (r_tab / "debts/ativos/DEBT_DT-001-atalho-no-parser.md")\
        .read_text(encoding="utf-8"), "estado da tabela não migrou"

    # REGRESSÃO (delta-044, caso real do DT-041): `\|` é conteúdo, não separador;
    # linha com aridade divergente do cabeçalho não é adivinhada
    r_borda = Path(tempfile.mkdtemp())
    (r_borda / "DEBT.md").write_text(
        "# DEBT.md\n\n## Registro\n\n"
        "| ID | Natureza | Descrição | Origem | Aberto em | Gatilho de correção | Status |\n"
        "|---|---|---|---|---|---|---|\n"
        "| DT-001 | débito | Export em `/api?fmt=json\\|csv\\|txt` sem dono | PR #1 | 2026-01-03 | quando doer | aberto |\n"
        "| DT-002 | pendência | Linha curta sem a coluna de data | PR #2 | quando o repo subir | quitado (2026-01-04, PR #9) |\n",
        encoding="utf-8")
    _, voz_borda = falado(migrar, r_borda)
    t_pipe = (r_borda / "debts/ativos/DEBT_DT-001-export-em-api-fmt-json-csv.md").read_text(encoding="utf-8")
    assert t_pipe.split("---\n")[2].lstrip("\n").startswith("# [DT-001] - "), \
        "migrar (tabela) não abriu o corpo com o título H1"
    assert "estado: aberto" in t_pipe and "aberto: 2026-01-03" in t_pipe, \
        f"pipe escapado desalinhou as colunas: {t_pipe}"
    assert "json|csv|txt" in t_pipe, "escape do pipe não voltou a ser conteúdo na prosa"
    t_curta = next((r_borda / "debts/ativos").glob("DEBT_DT-002-*.md")).read_text(encoding="utf-8")
    assert "estado: aberto" in t_curta and "quitado (2026-01-04" in t_curta, \
        f"linha curta foi adivinhada em vez de preservada na prosa: {t_curta}"
    assert "aridade divergente" in voz_borda and "DT-002" in voz_borda, \
        "aridade divergente não entrou no relatório de triagem"

    # REGRESSÃO (delta-045, caso real do pre-commit do nao-conformidade): o ponteiro
    # só linka o que existe, e o migrar deixa um README mínimo quando falta
    txt_ponteiro = (r_mig / "DEBT.md").read_text(encoding="utf-8")  # r_mig: só ativos
    assert "debts/_archive" not in txt_ponteiro and "LICOES" not in txt_ponteiro, \
        f"ponteiro linkou alvo inexistente: {txt_ponteiro}"
    assert "(debts/README.md)" in txt_ponteiro, "ponteiro sem link para as regras"
    assert (r_mig / "debts/README.md").is_file() and \
        "deltaspec" in (r_mig / "debts/README.md").read_text(encoding="utf-8"), \
        "migrar não deixou o README mínimo"
    assert "debts/_archive" in (r_tab / "DEBT.md").read_text(encoding="utf-8"), \
        "ponteiro de repo com encerrados deixou de linkar o _archive"
    r_readme = Path(tempfile.mkdtemp())
    (r_readme / "debts").mkdir(parents=True)
    (r_readme / "debts/README.md").write_text("# autoral\n", encoding="utf-8")
    (r_readme / "DEBT.md").write_text(CABECALHO_FIXTURE + linha("DT-001").replace(
        "· 2026-01-01", "· aberto em 2026-01-01"), encoding="utf-8")
    (r_readme / "alvo.py").write_text("x = 1\n", encoding="utf-8")
    quieto(migrar, r_readme)
    assert (r_readme / "debts/README.md").read_text(encoding="utf-8") == "# autoral\n", \
        "migrar sobrescreveu README autoral"

    # ÍNDICE gerado (delta-047, ADR-0031): bandas por valor gravado, na ordem das seções
    r_idx = raiz()
    arquivo(r_idx, ident="DT-001", topico="bloqueia", fila="P1·J9·Pr3", descricao="Bloqueia entrega")
    arquivo(r_idx, ident="DT-002", topico="atrasa", fila="P1·J3·Pr3 · trilha", descricao="Atrasa entrega")
    arquivo(r_idx, ident="DT-003", topico="incomodo", fila="P1·J1·Pr1", descricao="Incomoda")
    arquivo(r_idx, ident="DT-004", topico="impedimento", fila="P9·J1·Pr1 · !security(2026-09-01)",
            descricao="Vaza segredo")
    arquivo(r_idx, ident="DT-005", topico="sem-eixos", fila="", descricao="Ainda sem triagem")
    arquivo(r_idx, ident="DT-006", topico="guarda-x", natureza="guarda", estado_item="vigente",
            fila="", local="", gatilho="", descricao="Não consertar histórico")
    assert quieto(cmd_indice, r_idx) == 0
    idx = (r_idx / "DEBT.md").read_text(encoding="utf-8")
    assert "GERADO por debito.py indice" in idx, "índice sem o aviso de gerado"
    esperadas = ["## Críticos", "## Importantes", "## Médios", "## Não urgentes",
                 "## Sem triagem", "## Guardas"]
    posicoes = [idx.index(s) for s in esperadas]  # todas presentes E na ordem
    assert posicoes == sorted(posicoes), f"seções fora da ordem no índice: {posicoes}"
    assert idx.index("DT-004") < idx.index("DT-001") < idx.index("DT-002") < idx.index("DT-003"), \
        "itens fora das bandas esperadas (override → J9 → J3 → J1)"
    assert "!security(2026-09-01)" in idx and "· trilha" in idx, "marcas ausentes no índice"
    assert "(debts/ativos/DEBT_DT-001-bloqueia.md)" in idx, "linha do índice sem link para o arquivo real"
    assert "score" not in idx.lower() and "stale" not in idx.lower(), \
        "índice materializou score/stale — só valor gravado e ordem entram (ADR-0031)"

    # seção vazia é omitida (render determinístico)
    r_idx2 = arquivo(raiz(), fila="P1·J1·Pr1", descricao="Só um item frio")
    quieto(cmd_indice, r_idx2)
    idx2 = (r_idx2 / "DEBT.md").read_text(encoding="utf-8")
    assert "## Não urgentes" in idx2 and "## Críticos" not in idx2 and "## Guardas" not in idx2, \
        "seção vazia não foi omitida"

    # drift: fila avisa índice desatualizado/ausente e cala quando sincronizado
    r_dr = arquivo(raiz())
    _, voz_sem = falado(cmd_fila, r_dr)
    assert "desatualizado" in voz_sem, "índice ausente não gerou aviso de drift"
    quieto(cmd_indice, r_dr)
    _, voz_ok = falado(cmd_fila, r_dr)
    assert "desatualizado" not in voz_ok, "índice recém-gerado acusou drift"
    (r_dr / "DEBT.md").write_text((r_dr / "DEBT.md").read_text(encoding="utf-8") + "x\n",
                                  encoding="utf-8")
    _, voz_drift = falado(cmd_fila, r_dr)
    assert "desatualizado" in voz_drift, "edição manual do índice não gerou aviso de drift"

    # indice recusa o layout legado — nunca sobrescreve um registro-fonte
    r_leg_idx = Path(tempfile.mkdtemp())
    (r_leg_idx / "DEBT.md").write_text(CABECALHO_FIXTURE + linha("DT-001"), encoding="utf-8")
    try:
        quieto(cmd_indice, r_leg_idx)
        assert False, "indice rodou sobre layout legado"
    except SystemExit as e:
        assert e.code == 2, f"recusa do legado com exit errado: {e.code}"
    assert "## Registro" in (r_leg_idx / "DEBT.md").read_text(encoding="utf-8"), \
        "indice tocou o DEBT.md-fonte do layout legado"

    # item estruturalmente ilegível: reportado e fora do índice, nunca some em silêncio
    r_ileg = arquivo(raiz())
    arquivo(r_ileg, nome="DEBT_DT-099-quebrado.md", bruto="# sem frontmatter\n")
    _, voz_ileg = falado(cmd_indice, r_ileg)
    assert "DT-099" in voz_ileg, "arquivo ilegível não foi reportado pelo indice"
    idx_ileg = (r_ileg / "DEBT.md").read_text(encoding="utf-8")
    assert "DT-099" not in idx_ileg and "DT-001" in idx_ileg, \
        "ilegível entrou no índice (ou o legível ficou de fora)"

    # ---- DT-077: cadastro determinístico (comando `novo`) ----

    # o ID sai da união pronta, e a numeração nunca reutiliza número
    assert proximo_id(set()) == "DT-001", "registro vazio começa em DT-001"
    assert proximo_id({"DT-001", "DT-009"}) == "DT-010", "maior + 1, com zero à esquerda"
    assert proximo_id({"DT-099"}) == "DT-100", "passa de 3 dígitos sem truncar"
    assert proximo_id({"DT-005", "DT-002"}) == "DT-006", "ordem de entrada não importa"
    assert proximo_id({"DT-003", "lixo"}) == "DT-004", "entrada fora do padrão é ignorada"

    # o dict montado é o mesmo que o migrar entrega ao render_item
    it = monta_item("DT-042", "débito", "Sintoma curto", "P3·J9·Pr9",
                    "[alvo](alvo.py)", "quando doer", "delta-079", "", "Prosa.",
                    date(2026, 8, 23))
    nome_it, conteudo_it, pend_it = render_item(it)
    assert pend_it == [], f"item completo não deveria ter pendência de triagem: {pend_it}"
    assert nome_it == "DEBT_DT-042-sintoma-curto", nome_it
    assert "id: DT-042" in conteudo_it and "aberto: 2026-08-23" in conteudo_it, conteudo_it
    assert "# [DT-042] - Sintoma curto" in conteudo_it, "título H1 espelha o descricao"
    assert "- **Local:** [alvo](../../alvo.py)" in conteudo_it, "link não virou relativo ao arquivo"
    assert "fila: P3·J9·Pr9" in conteudo_it and "- **Fila:**" not in conteudo_it, \
        "a fila vive só no frontmatter"

    # cadastro real: o arquivo nasce válido, com o ID seguinte ao que já existe
    r_novo = raiz(); arquivo(r_novo, ident="DT-001")
    rc_novo, voz_novo = falado(cmd_novo, r_novo, natureza="débito",
                               descricao="Gate sem parser", fila="P1·J3·Pr9",
                               local="[alvo](alvo.py)", gatilho="na reincidência",
                               origem="delta-079", ticket="", corpo="Prosa do sintoma.")
    assert rc_novo == 0, voz_novo
    criado = r_novo / "debts/ativos/DEBT_DT-002-gate-sem-parser.md"
    assert criado.is_file(), f"arquivo não foi criado: {voz_novo}"
    item_lido, erros_lidos = parse_arquivo_ativo(criado)
    assert erros_lidos == [] and validar([item_lido], r_novo) == [], \
        f"item nasceu inválido: {erros_lidos} {validar([item_lido], r_novo)}"
    assert "Prosa do sintoma." in criado.read_text(encoding="utf-8"), "corpo não entrou"

    # campo obrigatório ausente: recusa nomeando o campo, sem deixar arquivo para trás
    antes_novo = {p.name for p in (r_novo / "debts/ativos").glob("*.md")}
    rc_falta, voz_falta = falado(cmd_novo, r_novo, natureza="débito",
                                 descricao="Sem gatilho", fila="P1·J3·Pr9",
                                 local="[alvo](alvo.py)", gatilho="", origem="",
                                 ticket="", corpo="")
    assert rc_falta != 0 and "Gatilho" in voz_falta, voz_falta
    assert {p.name for p in (r_novo / "debts/ativos").glob("*.md")} == antes_novo, \
        "recusa deixou arquivo no disco"

    # descricao acima do teto (DT-130): recusa nomeando o limite, nada fica no disco.
    # Raiz própria — não usa r_novo, para não perturbar a numeração sequencial que os
    # testes de guarda logo abaixo esperam (DT-003).
    r_teto = raiz()
    (r_teto / "debts/ativos").mkdir(parents=True)
    rc_teto, voz_teto = falado(cmd_novo, r_teto, natureza="débito",
                               descricao="x" * 101, fila="P1·J3·Pr9",
                               local="[alvo](alvo.py)", gatilho="sempre",
                               origem="", ticket="", corpo="")
    assert rc_teto != 0 and "100" in voz_teto and "101" in voz_teto, voz_teto
    assert list((r_teto / "debts/ativos").glob("*.md")) == [], \
        "descricao acima do teto ficou no disco"

    # descricao exatamente no teto: cadastra normalmente
    rc_ok100, voz_ok100 = falado(cmd_novo, r_teto, natureza="débito",
                                 descricao="x" * 100, fila="P1·J3·Pr9",
                                 local="[alvo](alvo.py)", gatilho="sempre",
                                 origem="", ticket="", corpo="")
    assert rc_ok100 == 0, voz_ok100

    # item já existente acima do teto: fila avisa, sem bloquear (o registro tem casos assim)
    r_fila_teto = raiz()
    arquivo(r_fila_teto, ident="DT-090", topico="descricao-longa", descricao="y" * 120)
    _, voz_fila_teto = falado(cmd_fila, r_fila_teto)
    assert "DT-090" in voz_fila_teto and "100" in voz_fila_teto, \
        f"fila não avisou descricao acima do teto: {voz_fila_teto}"

    # motores.tickets: none (delta-099, R2) — exportar recusa citando a chave, sem gravar nada
    r_none = raiz(); arquivo(r_none, ident="DT-050")
    (r_none / "doc-profile.yaml").write_text("motores:\n  tickets: none\n", encoding="utf-8")
    saida_none = r_none / "saida"
    rc_none, voz_none = falado(exportar, r_none, saida_none)
    assert rc_none != 0 and "none" in voz_none and "motores.tickets" in voz_none, voz_none
    assert not saida_none.exists(), "exportar com destino none não deveria escrever nada"

    # exportar --faixa (delta-099, R3): paridade sem a flag, recorte com ela
    r_faixa = raiz()
    arquivo(r_faixa, ident="DT-060", topico="score-alto", fila="P9·J9·Pr9")   # (9×9)/9=9.00 -> alta
    arquivo(r_faixa, ident="DT-061", topico="score-medio", fila="P3·J3·Pr9")  # (3×9)/3=9.00 -> alta também
    arquivo(r_faixa, ident="DT-062", topico="score-baixo", fila="P9·J1·Pr1")  # (1×1)/9=0.11 -> baixa
    saida_sem_faixa = r_faixa / "sem-faixa"
    rc_sf, _ = falado(exportar, r_faixa, saida_sem_faixa)
    assert rc_sf == 0
    todos = json.loads((saida_sem_faixa / "tickets.json").read_text(encoding="utf-8"))
    assert len(todos["items"]) == 3, "sem --faixa, paridade byte a byte: todos os itens entram"
    saida_alta = r_faixa / "so-alta"
    rc_alta, _ = falado(exportar, r_faixa, saida_alta, "", "alta")
    assert rc_alta == 0
    so_alta = json.loads((saida_alta / "tickets.json").read_text(encoding="utf-8"))
    assert {i["id"] for i in so_alta["items"]} == {"DT-060", "DT-061"}, \
        f"--faixa alta deveria trazer só score >= 9: {so_alta['items']}"

    # fila fora da escala (o caso real do DT-072): recusa antes de entrar no registro
    rc_escala, voz_escala = falado(cmd_novo, r_novo, natureza="débito",
                                   descricao="Fila fora da escala", fila="P2·J3·Pr4",
                                   local="[alvo](alvo.py)", gatilho="nunca",
                                   origem="", ticket="", corpo="")
    assert rc_escala != 0 and "Fila" in voz_escala, voz_escala
    assert {p.name for p in (r_novo / "debts/ativos").glob("*.md")} == antes_novo, \
        "item com fila inválida ficou no disco"

    # guarda não tem principal nem juros
    rc_guarda, _ = falado(cmd_novo, r_novo, natureza="guarda",
                          descricao="Não conserte o histórico", fila="P1·J3·Pr9",
                          local="", gatilho="", origem="", ticket="", corpo="")
    assert rc_guarda != 0, "guarda com fila deveria ser recusada"

    # guarda sem fila: entra, e sem exigir Local/Gatilho
    rc_g_ok, voz_g_ok = falado(cmd_novo, r_novo, natureza="guarda",
                               descricao="Não conserte o histórico", fila="",
                               local="", gatilho="", origem="", ticket="", corpo="")
    assert rc_g_ok == 0, voz_g_ok
    assert (r_novo / "debts/ativos/DEBT_DT-003-nao-conserte-o-historico.md").is_file(), voz_g_ok

    # registro sem layout novo: o comando explica em vez de criar pasta por conta própria
    r_sem = Path(tempfile.mkdtemp())
    try:
        quieto(cmd_novo, r_sem, natureza="débito", descricao="x", fila="P1·J1·Pr1",
               local="", gatilho="", origem="", ticket="", corpo="")
        raise AssertionError("cmd_novo aceitou raiz sem debts/ativos/")
    except SystemExit as e:
        assert e.code == 2, f"saída inesperada sem layout: {e.code}"

    print("selftest novo: OK (frontmatter, paridade, precedência, malformações, união, diff, migrar, índice)")


def selftest_quitar() -> None:
    """`quitar` mecaniza o ritual manual — git real, porque o comando faz `git mv`."""
    import tempfile

    try:
        subprocess.run(["git", "--version"], check=True, capture_output=True)
    except (FileNotFoundError, OSError):
        print("selftest quitar: PULADO (git indisponível)")
        return

    def repo():
        d = Path(tempfile.mkdtemp())
        subprocess.run(["git", "-C", str(d), "init", "-q", "-b", "main"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(d), "config", "user.email", "selftest@deltaspec"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(d), "config", "user.name", "selftest"], check=True, capture_output=True)
        (d / "alvo.py").write_text("x = 1\n", encoding="utf-8")
        return d

    def ativo(root, ident="DT-001", topico="caso-teste", estado_item="quitado", ticket="",
              extra_fm=""):
        pasta = root / "debts/ativos"
        pasta.mkdir(parents=True, exist_ok=True)
        destino = pasta / f"DEBT_{ident}-{topico}.md"
        campos = [("Local", "[alvo](../../alvo.py)"), ("Gatilho", "quando doer"),
                  ("Origem", "[PR #1](../../../../pull/1)"), ("Ticket", ticket)]
        corpo_campos = "".join(f"- **{n}:** {v}\n" for n, v in campos if v)
        destino.write_text(
            f"---\nid: {ident}\nnatureza: débito\nestado: {estado_item}\nfila: P3·J9·Pr9\n"
            f"descricao: Sintoma curto\naberto: 2026-01-01{extra_fm}\n---\n\n"
            f"# [{ident}] - Sintoma curto\n\nProsa da descrição.\n\n{corpo_campos}",
            encoding="utf-8")
        subprocess.run(["git", "-C", str(root), "add", "-A"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(root), "commit", "-qm", "base"], check=True, capture_output=True)
        return destino

    import contextlib
    import io

    def falado(fn, *args, **kwargs):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            r = fn(*args, **kwargs)
        return r, buf.getvalue()

    # feliz: estado já quitado, --ticket-ref presente, Ticket vira Encerrado
    r1 = repo()
    ativo(r1, ticket="JIRA-9")
    codigo, voz = falado(cmd_quitar, r1, "DT-001", "O que doía. O que foi feito.",
                         "delta-999 · #1", date(2026, 3, 1))
    arq_novo = r1 / "debts/_archive/DEBT_DT-001-caso-teste_2026_03_01.md"
    assert codigo == 0, f"quitar feliz devia sair 0: {voz}"
    assert arq_novo.is_file(), f"arquivo não moveu para _archive/: {voz}"
    assert not (r1 / "debts/ativos/DEBT_DT-001-caso-teste.md").exists(), "original não devia sobrar em ativos/"
    texto_novo = arq_novo.read_text(encoding="utf-8")
    assert "encerrado: 2026-03-01" in texto_novo, f"frontmatter sem encerrado: {texto_novo}"
    assert "#### Como foi quitado" in texto_novo and "O que foi feito." in texto_novo, \
        f"seção 'Como foi quitado' ausente: {texto_novo}"
    assert "- **Encerrado:** 2026-03-01 · delta-999 · #1" in texto_novo, \
        f"Ticket não virou Encerrado com a referência: {texto_novo}"
    assert "**Ticket:**" not in texto_novo, "campo Ticket sobrou depois de virar Encerrado"

    # feliz: descartado, sem --ticket-ref, sem Ticket prévio — Encerrado só com a data
    r2 = repo()
    ativo(r2, ident="DT-002", estado_item="descartado")
    codigo2, voz2 = falado(cmd_quitar, r2, "DT-002", "Motivo do descarte.", "", date(2026, 3, 2))
    arq2 = r2 / "debts/_archive/DEBT_DT-002-caso-teste_2026_03_02.md"
    assert codigo2 == 0 and arq2.is_file(), f"quitar descartado devia mover: {voz2}"
    assert "- **Encerrado:** 2026-03-02\n" in arq2.read_text(encoding="utf-8"), \
        "Encerrado sem ticket-ref devia ter só a data"

    # recusa: sem --como
    r3 = repo()
    ativo(r3, ident="DT-003")
    codigo3, voz3 = falado(cmd_quitar, r3, "DT-003", "", "", date(2026, 3, 3))
    assert codigo3 == 1 and "--como" in voz3, f"deveria recusar sem --como: {voz3}"
    assert (r3 / "debts/ativos/DEBT_DT-003-caso-teste.md").exists(), "arquivo não devia mover sem --como"

    # recusa: estado ainda não é final
    r4 = repo()
    ativo(r4, ident="DT-004", estado_item="aberto")
    codigo4, voz4 = falado(cmd_quitar, r4, "DT-004", "Prosa qualquer.", "", date(2026, 3, 4))
    assert codigo4 == 1 and "não é final" in voz4, f"deveria recusar estado não-final: {voz4}"
    assert (r4 / "debts/ativos/DEBT_DT-004-caso-teste.md").exists(), "arquivo não devia mover com estado aberto"

    # recusa: DT inexistente em ativos/
    r5 = repo()
    (r5 / "debts/ativos").mkdir(parents=True)
    subprocess.run(["git", "-C", str(r5), "add", "-A"], check=True, capture_output=True)
    codigo5, voz5 = falado(cmd_quitar, r5, "DT-999", "Prosa qualquer.", "", date(2026, 3, 5))
    assert codigo5 == 1 and "não encontrado" in voz5, f"deveria recusar DT inexistente: {voz5}"

    print("selftest quitar: OK (feliz com/sem ticket-ref, Ticket vira Encerrado, "
          "recusa sem --como, recusa estado não-final, recusa DT inexistente)")


def selftest_git() -> None:
    """Churn e stale com repositório git real — padrão do selftest_c7 do check_cycle."""
    import os
    import tempfile

    try:
        subprocess.run(["git", "--version"], check=True, capture_output=True)
    except (FileNotFoundError, OSError):
        print("selftest git: PULADO (git indisponível)")
        return
    # git presente: daqui em diante toda falha é ruidosa — PULADO não mascara regressão
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)

        def g(*args, quando=None):
            """`--date` só move a data do autor; o stale lê a do committer (%cs),
            que é a que sobrevive ao squash da main — por isso o fixture fixa as duas."""
            env = {**os.environ, "GIT_COMMITTER_DATE": quando, "GIT_AUTHOR_DATE": quando} if quando else None
            subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, env=env)

        g("init", "-q", "-b", "main")
        g("config", "user.email", "selftest@deltaspec")
        g("config", "user.name", "selftest")
        (root / "quente.py").write_text("x = 1\n", encoding="utf-8")
        (root / "frio.py").write_text("y = 1\n", encoding="utf-8")
        (root / "DEBT.md").write_text(
            CABECALHO_FIXTURE
            + linha("DT-040", titulo="Item quente", local="[q](quente.py)", fila="P3·J9·Pr1")
            + linha("DT-041", titulo="Item frio", local="[f](frio.py)", fila="P3·J9·Pr9"),
            encoding="utf-8")
        g("add", "-A")
        g("commit", "-qm", "base", quando="2020-01-01T00:00:00")
        for i in range(5):  # quente.py acumula churn; frio.py não é mais tocado
            (root / "quente.py").write_text(f"x = {i}\n", encoding="utf-8")
            g("add", "-A")
            g("commit", "-qm", f"toca quente {i}")

        contagem = churn(root)
        assert contagem is not None, "churn devolveu None com git presente"
        assert contagem["quente.py"] > contagem["frio.py"], f"churn não ordenou: {contagem}"
        assert prob_do_churn("quente.py", contagem) == 9, "arquivo mais tocado não virou Pr9"
        assert prob_do_churn("nunca-tocado.py", contagem) == 1, "arquivo ausente não virou Pr1"

        itens = parse_blocos((root / "DEBT.md").read_text(encoding="utf-8"))
        fila = montar_fila(itens, root, hoje=date(2020, 1, 2))
        derivadas = {e["item"]["id"]: e["prob_derivada"] for e in fila}
        assert derivadas["DT-040"] == 9, f"divergência de churn não detectada: {derivadas}"
        assert not any(e["stale"] for e in fila), "stale marcado no dia seguinte ao commit"

        # o mesmo registro, avaliado muito depois: juros altos e linha parada → stale
        tarde = montar_fila(itens, root, hoje=date(2021, 1, 1))
        assert all(e["stale"] for e in tarde), f"stale não marcado após {STALE_DIAS} dias"

        # editar só a prosa NÃO é decidir: o relógio do stale não pode reiniciar
        texto = (root / "DEBT.md").read_text(encoding="utf-8")
        (root / "DEBT.md").write_text(texto.replace("**Item quente**", "**Item quente revisado**"),
                                      encoding="utf-8")
        g("add", "-A")
        g("commit", "-qm", "reescreve o título do DT-040", quando="2020-12-31T00:00:00")
        churn.cache_clear()  # o cache é por root; o repo mudou dentro do mesmo processo
        so_prosa = {e["item"]["id"]: e["stale"]
                    for e in montar_fila(parse_blocos((root / "DEBT.md").read_text(encoding="utf-8")),
                                         root, hoje=date(2021, 1, 1))}
        assert so_prosa["DT-040"] is True, "editar prosa reiniciou o relógio de decisão"

        # mudar o ESTADO no cabeçalho é decidir: aí sim o stale sai
        texto = (root / "DEBT.md").read_text(encoding="utf-8")
        (root / "DEBT.md").write_text(texto.replace("### DT-040 · débito · aberto",
                                                    "### DT-040 · débito · aceito"), encoding="utf-8")
        g("add", "-A")
        g("commit", "-qm", "aceita o DT-040", quando="2020-12-31T00:00:00")
        churn.cache_clear()
        depois = {e["item"]["id"]: e["stale"]
                  for e in montar_fila(parse_blocos((root / "DEBT.md").read_text(encoding="utf-8")),
                                       root, hoje=date(2021, 1, 1))}
        assert depois["DT-040"] is False, "stale não sumiu depois da mudança de estado"
        assert depois["DT-041"] is True, "stale de item não tocado sumiu junto"

        sem_git = Path(tempfile.mkdtemp())
        (sem_git / "DEBT.md").write_text(CABECALHO_FIXTURE + linha("DT-050", local="",
                                                                   fila="", natureza="guarda",
                                                                   status="vigente"),
                                         encoding="utf-8")
        assert churn(sem_git) is None, "churn não degradou fora de repositório git"

    # layout novo (ADR-0030): o relógio do stale mede o frontmatter do arquivo do item
    with tempfile.TemporaryDirectory() as d2:
        root = Path(d2)

        def g2(*args, quando=None):
            env = {**os.environ, "GIT_COMMITTER_DATE": quando, "GIT_AUTHOR_DATE": quando} if quando else None
            subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, env=env)

        def escreve(ident, topico, local, fila, estado_item="aberto"):
            pasta = root / "debts/ativos"
            pasta.mkdir(parents=True, exist_ok=True)
            (pasta / f"DEBT_{ident}-{topico}.md").write_text(
                f"---\nid: {ident}\nnatureza: débito\nestado: {estado_item}\nfila: {fila}\n"
                f"descricao: Item {topico}\naberto: 2020-01-01\n---\n\n"
                f"# [{ident}] - Item {topico}\n\nProsa.\n\n"
                f"- **Local:** [x]({local})\n- **Gatilho:** quando doer\n"
                f"- **Origem:** [PR #1](../../../../pull/1)\n", encoding="utf-8")

        g2("init", "-q", "-b", "main")
        g2("config", "user.email", "selftest@deltaspec")
        g2("config", "user.name", "selftest")
        (root / "quente.py").write_text("x = 1\n", encoding="utf-8")
        (root / "frio.py").write_text("y = 1\n", encoding="utf-8")
        escreve("DT-040", "quente", "../../quente.py", "P3·J9·Pr1")
        escreve("DT-041", "frio", "../../frio.py", "P3·J9·Pr9")
        g2("add", "-A")
        g2("commit", "-qm", "base", quando="2020-01-01T00:00:00")
        for i in range(5):
            (root / "quente.py").write_text(f"x = {i}\n", encoding="utf-8")
            g2("add", "-A")
            g2("commit", "-qm", f"toca quente {i}")
        churn.cache_clear()

        def fila_em(hoje):
            import contextlib
            import io
            with contextlib.redirect_stdout(io.StringIO()):
                return montar_fila(carregar(root), root, hoje=hoje)

        cedo = fila_em(date(2020, 1, 2))
        assert {e["item"]["id"]: e["prob_derivada"] for e in cedo}["DT-040"] == 9, \
            "churn não casou o Local normalizado do layout novo"
        assert not any(e["stale"] for e in cedo), "stale novo marcado no dia seguinte"
        assert all(e["stale"] for e in fila_em(date(2021, 1, 1))), \
            f"stale novo não marcado após {STALE_DIAS} dias"

        caminho_40 = root / "debts/ativos/DEBT_DT-040-quente.md"
        caminho_40.write_text(caminho_40.read_text(encoding="utf-8")
                              .replace("Prosa.", "Prosa revisada em detalhe."), encoding="utf-8")
        g2("add", "-A")
        g2("commit", "-qm", "revisa a prosa do DT-040", quando="2020-12-31T00:00:00")
        churn.cache_clear()
        so_prosa = {e["item"]["id"]: e["stale"] for e in fila_em(date(2021, 1, 1))}
        assert so_prosa["DT-040"] is True, "editar prosa do arquivo reiniciou o relógio"

        caminho_40.write_text(caminho_40.read_text(encoding="utf-8")
                              .replace("estado: aberto", "estado: aceito"), encoding="utf-8")
        g2("add", "-A")
        g2("commit", "-qm", "aceita o DT-040", quando="2020-12-31T00:00:00")
        churn.cache_clear()
        depois = {e["item"]["id"]: e["stale"] for e in fila_em(date(2021, 1, 1))}
        assert depois["DT-040"] is False, "mudar estado: no frontmatter não limpou o stale"
        assert depois["DT-041"] is True, "stale de arquivo vizinho sumiu junto"

    # DT-071/DT-077: o ID conta também o que está em branch remota já buscada
    with tempfile.TemporaryDirectory() as d3:
        r3 = Path(d3)

        def g3(*args):
            subprocess.run(["git", "-C", str(r3), *args], check=True, capture_output=True)

        g3("init", "-q", "-b", "main")
        g3("config", "user.email", "selftest@deltaspec")
        g3("config", "user.name", "selftest")
        (r3 / "debts/ativos").mkdir(parents=True)
        (r3 / "debts/ativos/DEBT_DT-001-local.md").write_text("x\n", encoding="utf-8")
        g3("add", "-A")
        g3("commit", "-qm", "base")
        assert ids_em_refs_remotas(r3) == set(), "ref remoto inexistente devolveu ID"

        # branch com um DT maior, publicada e buscada — o cenário do DT-071
        g3("checkout", "-q", "-b", "outra")
        (r3 / "debts/_archive/DEBT_DT-050-remoto_2026_01_01.md").parent.mkdir(parents=True)
        (r3 / "debts/_archive/DEBT_DT-050-remoto_2026_01_01.md").write_text("y\n", encoding="utf-8")
        g3("add", "-A")
        g3("commit", "-qm", "cadastra na outra branch")
        sha = subprocess.run(["git", "-C", str(r3), "rev-parse", "HEAD"],
                             capture_output=True, text=True, check=True).stdout.strip()
        g3("checkout", "-q", "main")
        g3("update-ref", "refs/remotes/origin/outra", sha)
        # o ref carrega o que a branch tem inteiro, inclusive o que veio da main —
        # é união de IDs em uso, não diferença; quem separa é o proximo_id
        assert ids_em_refs_remotas(r3) == {"DT-001", "DT-050"}, \
            f"ID em ref remoto não foi visto: {ids_em_refs_remotas(r3)}"
        assert proximo_id(ids_em_disco(r3) | ids_em_refs_remotas(r3)) == "DT-051", \
            "o próximo ID colidiu com o que existe na branch remota"
        assert proximo_id(ids_em_disco(r3)) == "DT-002", \
            "fixture inútil: sem os refs o cálculo já daria DT-051"

    assert ids_em_refs_remotas(Path(tempfile.mkdtemp())) == set(), \
        "sem repositório git, a leitura de refs deveria degradar para vazio"
    print(f"selftest git: OK (churn real, Pr derivada, stale >{STALE_DIAS}d nos dois layouts, "
          f"ID sobre refs remotos, degradação sem git)")


if __name__ == "__main__":
    main()
