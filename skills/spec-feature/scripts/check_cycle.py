#!/usr/bin/env python3
"""Gate determinístico do ciclo deltaspec — checa o que é mecânico numa delta spec.
Saída parcial: os checks 3 e 5 do analyze (scope creep, regra canônica) continuam humanos.

Automatiza os checks 1 e 2 do analyze (references/analyze.md), o estado ×
localização da delta, a verificação obrigatória do archive (references/cycle.md,
regra 6), o limiar de particionamento do TRUTH.md, a pendência roteada
(cycle.md, regra 7), a medição do split de PR (cycle.md, split condicional) e a
higiene do checkout onde a delta foi aberta (CLAUDE.md, Fluxo de trabalho Git). Os
checks 3 e 5 do analyze (scope creep spec×plan, violação de regra canônica)
continuam com o modelo — são juízo, não regex.

  C1  aceite verificável — Rn com DADO/QUANDO/ENTÃO; RNFn com Métrica + Verificação;
      heading '###' fora da forma canônica (delta-033)
  C2  cobertura spec ↔ tasks — órfãos nos dois sentidos; task sem verificação
  C3  estado × localização — delta 'aplicada' fora de _archive/ é trabalho inacabado
  C4  archive sem perda — requisito sumido do TRUTH.md sem MUDA/REMOVE que o declare
  C5  custo de contexto do TRUTH.md — linhas, tokens aproximados e domínios (delta-040)
  C6  pendência roteada — '- [ ]' em "Dependências e riscos" de delta arquivada
  C7  split de PR — artefatos da delta acima do limiar de PR recomendam split (BAIXO)
  C8  cobertura do plano de testes — Rn/RNFn sem caso; ausência sem dispensa (delta-015)
  C9  grafo de tasks — `(dep: Tn)` inexistente ou ciclo entre tasks (delta-016)
  C10 convergência mínima — task '- [ ]' remanescente em delta arquivada (delta-016)
  C11 doc-profile — núcleo ausente, YAML inválido, obrigatório sem justificativa (delta-026)
  C12 trilha do clarify — perfil completo sem canal humano declarado (delta-026)
  C13 links relativos vivos em delta arquivada — profundidade quebrada no move (delta-047)
  C14 checkout volátil ou raso — delta aberta sob plugins/marketplaces/ (delta-082)

Uso: check_cycle.py [DELTA_DIR]         (default: a única delta não arquivada em ./specs)
     check_cycle.py --proximo-numero [ROOT]   (default: cwd) — NNN livre p/ abrir a delta (R5)
     check_cycle.py --selftest
Exit 0 = sem ALTO/CRÍTICO · 1 = corrigir antes de seguir · 2 = erro de uso.
"""
import graphlib
import re
import subprocess
import sys
from pathlib import Path

from itens import itens  # dono do formato de item (delta-033) — C2/C8/C9/C10 consomem daqui

# Import do módulo da skill irmã guarding-doc-integrity — mesmo padrão do W1 do
# audit-workspace (audit_workspace.py) e do tickets.py → projecao.py: o layout
# skills/<nome>/scripts/ é estável tanto no repo quanto no cache do plugin instalado,
# por isso o caminho é relativo ao próprio arquivo, nunca absoluto de máquina.
# scan_links_c3 é dona canônica da resolução de link (R60) — nunca duplicar aqui.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "guarding-doc-integrity" / "scripts"))
from validate_integrity import scan_links_c3  # noqa: E402

try:
    import yaml  # única dependência externa admitida nos gates (ADR-0023)
except ModuleNotFoundError:  # mensagem acionável em vez de traceback cru (review da delta-026)
    sys.exit("ERRO: PyYAML ausente — rode 'pip install pyyaml' (ADR-0023)")

TRUTH_LIMITE = 800  # linhas
# Custo de contexto do TRUTH.md em tokens (delta-040, DT-035): linha é proxy fraco sob
# soft-wrap. Divisor medido em 2026-08-09 contra o TRUTH.md deste repo como estava em
# 8277b1d (67.445 chars) — tiktoken cl100k 20.631, o200k 18.398, len//3 22.481: a
# heurística stdlib erra +9% para o lado de acusar cedo, e os dois encodings reais
# divergem 11% entre si. Tokenizador real recusado na ADR-0027.
CHARS_POR_TOKEN = 3
TRUTH_LIMITE_TOKENS = 40_000
# Segundo gatilho de particionamento: acima de 12 domínios o TRUTH.md particiona. Conta
# todas as seções `##`, sem excluir nenhuma por nome — lista de exceção por nome não
# sobrevive a projeto que chame as suas de outro jeito.
TRUTH_LIMITE_DOMINIOS = 12
PR_LIMITE = 500  # espelho da regra canônica de tamanho de PR (dono: canonical-rules.md; sancionado no deps.toml)
# C14 (delta-082, DT-043): diretório que o harness serve e re-clona (shallow) a cada
# `/plugin update`. Não é workspace: quem trabalha ali perde branch e commit não pushados.
DIR_MARKETPLACE = "plugins/marketplaces/"
ORDEM = {"CRÍTICO": 0, "ALTO": 1, "MÉDIO": 2, "BAIXO": 3}

# C11 (delta-026): núcleo do doc-profile, medido nos 7 perfis reais em 2026-08-02. A cauda
# (explicativos, prototipo, apresentacao, ...) é opcional por desenho: categoria que uma delta
# acrescenta ao template nunca propaga retroativamente aos projetos já inicializados.
NUCLEO_TOPO = ("decisao", "publico", "artefatos")
NUCLEO_ARTEFATOS = ("arquitetura", "modelo-dados", "fluxos", "casos-de-uso")
# Perfil mínimo válido — fixture compartilhada pelos selftests (uma fonte, não uma cópia por teste).
PERFIL_NUCLEO = (
    'decisao: { data: "2026-01-01", justificativa: "" }\n'
    'publico: { interno: true, cliente: false }\n'
    'artefatos:\n'
    '  arquitetura:  { obrigatorio: true }\n'
    '  modelo-dados: { obrigatorio: false }\n'
    '  fluxos:       { obrigatorio: false }\n'
    '  casos-de-uso: { obrigatorio: false }\n'
)

# Duas notações de ID aceitas: Rn/RNFn (default do framework) e RF-NN/RNF-NN com
# numeração hierárquica opcional (RF-01.1). A segunda existe porque projeto com
# corpus legado cita o ID em massa — renomear centenas de citações para chegar ao
# mesmo lugar é churn, e o tabela_cliente.py do doc-entregavel já exige RF-NN.
REQ_ID = r"R(?:NF|F)?-?\d+(?:\.\d+)*"

CABECALHO = re.compile(rf"^###\s+({REQ_ID})\s*[—-]\s*(ADICIONA|MUDA|REMOVE)\b(.*)$")
# Qualquer '###' — usado só para achar o heading que casa isto mas não CABECALHO (delta-033):
# blocos() descarta esse heading em silêncio, e o requisito some do gate sem nenhum achado.
HEADING_QUALQUER = re.compile(r"^###\s+(.*)$")
# Seções que hospedam heading '###' de requisito (R1, delta-033): 'Mudanças' e a segunda
# leva de RNFn, 'Requisitos não funcionais'. Fora delas, '### algo' é subtítulo comum
# (ex.: '### Detalhamento' dentro de 'Dependências e riscos') — não é requisito perdido,
# então HEADING_QUALQUER não se aplica lá. Tolerante a caixa e à falta do acento.
SECAO_REQUISITO = re.compile(r"^##\s+(mudan[çc]as|requisitos n[ãa]o funcionais)\s*$", re.I)
# Aceita (ΔNNN) legado, (delta-NNN) e a anotação de proveniência que o archive acumula no
# requisito-alvo de um MUDA parcial — '(delta-003; farol por forecast: delta-011)'. Sem o
# `[^)]*`, requisito anotado ficava fora do C4 inteiro: perda real nele passava batido, e
# anotar um requisito antes simples virava CRÍTICO falso (delta-052).
ALVO = re.compile(rf"\b({REQ_ID})\s*\((?:Δ\s*|delta-)\d+[^)]*\)")
# C4-cenário (delta-082, DT-075): a regra 2 do archive opera sobre cenário, não sobre
# requisito. Um bloco MUDA com 3 dos 7 cenários vigentes deixa o `### Rn` de pé e o C4
# saía silencioso — foi o R95 na delta-077, pego por leitura humana, não por gate.
CENARIO = re.compile(r"^\s*-\s*DADO\b", re.M)
DEP = re.compile(r"\(dep:\s*([^)]*)\)")  # arestas de bloqueio do tasks.md (delta-016)
SECAO_RISCOS = re.compile(r"^##\s+Depend[êe]ncias e riscos\s*$(.*?)(?=^##\s|\Z)", re.M | re.S)
PENDENCIA_ABERTA = re.compile(r"^\s*-\s*\[ \]", re.M)
# C12 (delta-026): trilha do clarify. Âncora de início de linha — a mesma sintaxe citada em
# prosa é texto, não campo (lições de 2026-07-28 e 2026-08-01, três falsos positivos).
CLARIFY = re.compile(r"^Clarify:\s*(entrevistado|auto-avaliado)\b", re.M)
# ponytail: um requisito por bloco ###; spec que fuja do template não é parseada

# Qualquer citação de delta solta em prosa — mais frouxo que ALVO (não exige Rn na frente),
# porque aqui o alvo é o número em si, não o requisito. Cobre tanto '(delta-016)' quanto
# 'delta-016' fora de parênteses, como o CHANGELOG.md cita merge sem specs/NNN-*/ (delta-053).
NUM_DELTA = re.compile(r"(?:Δ\s*|delta-)0*(\d+)")

# DT-039 (_pmo, 2026-08-13): CHANGELOG citando delta de OUTRO repo ("corrigido no
# framework (deltaspec v1.24.1, delta-052)") inflava a numeração local de 018 para 053.
# A sequência local é contígua — o maior salto legítimo é uma reserva explícita (R5) —,
# então menção que salte mais que isto acima da sequência já aceita é estrangeira.
SALTO_MENCAO = 10
# A2 do DT-071 (delta-082): branch `tipo/NNN-nome` no remoto ocupa NNN como pasta local
# ocupa. Casa tanto `refs/heads/feat/082-x` (ls-remote) quanto
# `refs/remotes/origin/feat/082-x` (fallback em disco) — o NNN é o primeiro segmento
# numerado depois do tipo.
REF_NUMERADA = re.compile(r"refs/(?:heads|remotes)/(?:[^/\s]+/)*?[^/\s]+/(\d+)-")
LS_REMOTE_TIMEOUT = 5  # segundos — consulta informativa nunca trava o comando


def die(msg: str) -> None:
    print(f"ERRO: {msg}")
    sys.exit(2)


def campo(texto: str, nome: str):
    """Valor de 'nome: valor' até '·' ou fim de `texto`. `texto` pode ser a junção de
    várias linhas de um item (itens.py) — não é garantido ser uma única linha física;
    reintroduzir `.splitlines()` aqui quebraria esse contrato (DT-001). None se ausente
    ou placeholder."""
    m = re.search(rf"{nome}\s*:\s*([^·\n]*)", texto, re.IGNORECASE)
    if not m:
        return None
    v = m.group(1).strip()
    return None if not v or "{{" in v else v


def eh_bugfix(cab: str) -> bool:
    """Tipo da delta lido do cabeçalho — um dono só para o predicado que o C8, o C12 e o
    checar() consultam (review da delta-026: estava em três cópias)."""
    return (campo(cab, "Tipo") or "").lower() == "bugfix"


def cabecalho(spec_txt: str) -> str:
    """Cabeçalho da spec (antes da primeira seção ##), sem comentários HTML —
    comentário de template citando 'Test-plan:'/'Tipo:' não pode enganar o campo()
    (falso negativo pego no review da delta-015)."""
    return re.sub(r"<!--.*?-->", "", spec_txt, flags=re.S).split("\n## ", 1)[0]


def cobre_alvos(texto: str, ids_spec: set, onde: str, cobertos: set, v: list, ignora: tuple = ()):
    """Núcleo comum do C2 (tasks) e do C8 (test-plan): parseia 'cobre:', acumula os
    alvos em `cobertos` e acusa referência morta (ALTO). `texto` é `item["texto"]`
    (itens.py) — a junção de todas as linhas do item, não uma linha física isolada.
    Retorna o valor bruto de 'cobre:' (None se ausente) para o check de completude
    de cada chamador."""
    cobre = campo(texto, "cobre")
    if not cobre:
        return None
    for alvo in re.split(r"[,/]", cobre):
        alvo = alvo.strip()
        if alvo.lower() in ignora:
            continue
        cobertos.add(alvo)
        if alvo not in ids_spec:
            v.append(("ALTO", onde, f"cobre '{alvo}', que não existe no spec.md", "corrigir a referência ou adicionar o requisito"))
    return cobre


def blocos(spec_txt: str) -> list[tuple[str, str, str, str]]:
    """[(id, verbo, resto-do-cabeçalho, corpo)] dos ### Rn/RNFn do spec.md."""
    out: list[tuple[str, str, str, str]] = []
    atual, corpo = None, []
    for line in spec_txt.splitlines():
        m = CABECALHO.match(line)
        if m:
            if atual:
                out.append((*atual, "\n".join(corpo)))
            atual, corpo = (m.group(1), m.group(2), m.group(3)), []
        elif atual and line.startswith("## "):
            out.append((*atual, "\n".join(corpo)))
            atual, corpo = None, []
        elif atual:
            corpo.append(line)
    if atual:
        out.append((*atual, "\n".join(corpo)))
    return out


def c1_aceite(spec_txt: str, bs, v: list) -> None:
    em_secao_requisito = False
    for n, line in enumerate(spec_txt.splitlines(), 1):
        if line.startswith("## "):
            em_secao_requisito = bool(SECAO_REQUISITO.match(line))
            continue
        if not em_secao_requisito:
            continue  # '### algo' fora de 'Mudanças'/'Requisitos não funcionais' é subtítulo comum, não requisito perdido
        m = HEADING_QUALQUER.match(line)
        if m and not CABECALHO.match(line):
            v.append(("ALTO", f"spec.md l.{n}", f"heading '### {m.group(1)}' fora da forma canônica",
                      "usar '### Rn — ADICIONA|MUDA|REMOVE' (templates/delta-spec.md) — "
                      "requisito fora da forma some do gate"))
    for rid, verbo, _, corpo in bs:
        if verbo == "REMOVE":
            continue  # REMOVE não precisa de cenário — está saindo
        onde = f"spec.md {rid}"
        if rid.startswith("RNF"):
            if not campo(corpo, r"M[ée]trica"):
                v.append(("ALTO", onde, "RNF sem Métrica preenchida", "limiar verificável (ex.: p95 < 300ms) ou vira pendência em riscos"))
            if not campo(corpo, r"Verifica[çc][ãa]o"):
                v.append(("ALTO", onde, "RNF sem Verificação preenchida", "declarar como medir (teste de carga, axe-core, ...)"))
            continue
        alto = corpo.upper()
        faltam = [k for k in ("DADO", "QUANDO", "ENTÃO") if k not in alto]
        if faltam:
            v.append(("ALTO", onde, f"cenário de aceite sem {'/'.join(faltam)}", "todo Rn tem DADO/QUANDO/ENTÃO"))
        elif not re.search(r"ENTÃO\s+\S", corpo) or "{{" in corpo:
            v.append(("ALTO", onde, "cenário de aceite vazio ou não preenchido", "ENTÃO com resultado verificável"))


def c2_cobertura(bs, tasks_txt: str, v: list) -> None:
    ids_spec = {rid for rid, _, _, _ in bs}
    cobertos: set[str] = set()
    tasks = itens(tasks_txt, "T")
    for item in tasks:
        tid, texto = item["id"], item["texto"]
        if cobre_alvos(texto, ids_spec, f"tasks.md {tid}", cobertos, v, ignora=("infra",)) is None:
            v.append(("MÉDIO", f"tasks.md {tid}", "task sem 'cobre:'", "mapear a um Rn/RNFn ou declarar 'cobre: infra'"))
        if not campo(texto, r"verifica[çc][ãa]o"):
            v.append(("ALTO", f"tasks.md {tid}", "task sem 'verificação:'", "declarar comando ou critério de pronto"))
    if not tasks:
        v.append(("ALTO", "tasks.md", "nenhuma task encontrada", "gerar tasks.md a partir do template"))
        return
    for rid in sorted(ids_spec - cobertos):
        v.append(("ALTO", f"spec.md {rid}", "requisito sem task que o cubra", f"adicionar task com 'cobre: {rid}'"))


def c3_estado(root: Path, v: list) -> None:
    for p in sorted((root / "specs").glob("*/spec.md")):
        if re.search(r"^Estado:\s*aplicada\b", p.read_text(encoding="utf-8"), re.M):
            v.append(("ALTO", str(p.relative_to(root)), "delta 'aplicada' fora de _archive/", "consolidar no TRUTH.md e mover — archive faz parte do pronto"))
    for p in sorted((root / "specs" / "_archive").glob("*/spec.md")):
        if not re.search(r"^Estado:\s*arquivada\b", p.read_text(encoding="utf-8"), re.M):
            v.append(("MÉDIO", str(p.relative_to(root)), "delta em _archive/ sem 'Estado: arquivada'", "corrigir o cabeçalho do spec.md"))


def cenarios_por_requisito(texto: str) -> dict[str, int]:
    """{Rn: nº de cenários '- DADO'} — fatia o texto do TRUTH pelos headings '### Rn'.

    Granularidade que faltava ao C4 (DT-075): ele compara o **conjunto de IDs**, e a
    regra 2 do archive manda o bloco MUDA trazer a versão **completa** do requisito.
    Requisito que sobrevive com metade dos cenários passa no conjunto e some no detalhe.

    Formato legado (bullets '- Rn (Δ000) — a', pré-ADR-0034) não tem heading e portanto
    não entra na contagem — ali cada requisito é uma linha só, sem cenário a perder.
    """
    contagem: dict[str, int] = {}
    atual = None
    for linha in texto.splitlines():
        if linha.startswith("### "):
            ids = ALVO.findall(linha) or re.findall(rf"^###\s+({REQ_ID})\b", linha)
            atual = ids[0] if ids else None
            if atual:
                contagem.setdefault(atual, 0)
        elif atual and CENARIO.match(linha):
            contagem[atual] += 1
    return contagem


def truth_no_commit(root: Path, ref: str) -> str:
    """Texto do TRUTH (índice + partições atuais) num ref git — vazio no que não existir.

    Lê as partições pelo nome que elas têm **hoje**: partição criada nesta delta
    simplesmente não existe na base, e `git show` devolvendo != 0 já cobre o caso.
    """
    partes = []
    rels = ["specs/TRUTH.md", *[f"specs/truth/{p.name}"
                                for p in sorted((root / "specs" / "truth").glob("*.md"))]]
    for rel in rels:
        r = subprocess.run(["git", "-C", str(root), "show", f"{ref}:{rel}"],
                           capture_output=True, text=True)
        if r.returncode == 0:
            partes.append(r.stdout)
    return "\n".join(partes)


def base_c4(root: Path) -> tuple[str, bool]:
    """Merge-base da branch com a main → (ref, True); sem base → ('HEAD', False)."""
    for ref in ("origin/main", "main"):
        r = subprocess.run(["git", "-C", str(root), "merge-base", "HEAD", ref],
                           capture_output=True, text=True)
        if r.returncode == 0:
            return r.stdout.strip(), True
    return "HEAD", False


def c4_archive(root: Path, bs, v: list, arquivada: bool = True) -> None:
    """Requisito removido do TRUTH.md tem que estar declarado como alvo de MUDA/REMOVE.

    `arquivada` é o `Estado:` da spec: a comparação contra o que o bloco MUDA declara só
    faz sentido depois da consolidação (DT-090) — antes dela, toda delta que **cresce** um
    requisito satisfaz a desigualdade sem ter nada de errado. Default conservador: quem
    não declara o estado recebe o check inteiro, nunca o silêncio."""
    alvos = {a for _, verbo, head, _ in bs if verbo in ("MUDA", "REMOVE") for a in ALVO.findall(head)}
    for _, verbo, head, _ in bs:
        if verbo in ("MUDA", "REMOVE") and not ALVO.findall(head):
            v.append(("ALTO", "spec.md", f"bloco {verbo} sem citar o alvo vigente", "declarar o alvo (ex.: 'MUDA R2 (delta-001)')"))
    alvo_git = ["specs/TRUTH.md", "specs/truth"]
    try:
        base, com_base = base_c4(root)
        diff = subprocess.run(
            ["git", "-C", str(root), "diff", base, "--", *alvo_git],
            capture_output=True, text=True, check=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return  # sem git ou TRUTH não versionado — o check não se aplica
    if not com_base:
        v.append(("BAIXO", "C4", "sem merge-base com origin/main ou main — comparando contra HEAD (janela cega pós-commit)",
                  "rodar numa branch criada a partir da main"))
    perdidos = set()
    for line in diff.splitlines():
        if line.startswith("-") and not line.startswith("---"):
            perdidos.update(r for r in ALVO.findall(line) if r not in alvos)
    # ID ainda presente no TRUTH resultante não é perda — cobre reescrita de sufixo em massa
    # (ex.: (ΔNNN)→(delta-NNN)), que remove a linha antiga no diff mas mantém o requisito.
    # Lê o TRUTH particionado também: com specs/truth/<dominio>.md, o requisito vive na
    # partição e ler só o índice acusaria perda que não houve.
    presentes: set[str] = set()
    for t in [root / "specs" / "TRUTH.md", *sorted((root / "specs" / "truth").glob("*.md"))]:
        if t.is_file():
            presentes |= set(ALVO.findall(t.read_text(encoding="utf-8")))
    perdidos -= presentes
    for rid in sorted(perdidos):
        v.append(("CRÍTICO", "specs/TRUTH.md", f"{rid} sumiu do TRUTH.md sem MUDA/REMOVE que o declare", "restaurar o requisito ou declarar o alvo na delta"))
    # O ID sobreviveu; falta olhar se o requisito sobreviveu inteiro (DT-075). Só alvos de
    # MUDA: REMOVE encolher é o que ele declara, e requisito intocado que perde cenário é
    # outro defeito — o C4-requisito já o pega por ID quando o heading some.
    alvos_muda = {a for _, verbo, head, _ in bs if verbo == "MUDA" for a in ALVO.findall(head)}
    if not (alvos_muda and com_base):
        return
    antes = cenarios_por_requisito(truth_no_commit(root, base))
    agora: dict[str, int] = {}
    for t in [root / "specs" / "TRUTH.md", *sorted((root / "specs" / "truth").glob("*.md"))]:
        if t.is_file():
            agora.update(cenarios_por_requisito(t.read_text(encoding="utf-8")))
    # O que o bloco MUDA da própria delta declara, por alvo. Comparar só contra o
    # merge-base é cego quando a delta **cresce** o requisito e ainda assim perde um
    # cenário declarado no caminho da consolidação — os dois lados do mesmo defeito.
    declarado: dict[str, int] = {}
    for _, verbo, head, corpo in bs:
        if verbo != "MUDA":
            continue
        for a in ALVO.findall(head):
            declarado[a] = declarado.get(a, 0) + len(CENARIO.findall(corpo))
    for rid in sorted(alvos_muda):
        de, para, dito = antes.get(rid, 0), agora.get(rid, 0), declarado.get(rid, 0)
        if de and para < de:
            v.append(("ALTO", "specs/TRUTH.md",
                      f"{rid} foi de {de} para {para} cenários no bloco MUDA",
                      "repetir na delta os cenários vigentes que continuam valendo "
                      "(cycle.md, regra 2) ou declarar a remoção do cenário"))
        # `rid in agora` é a guarda do formato legado: TRUTH em bullets não tem heading,
        # a contagem é 0 para tudo, e sem isso todo MUDA sobre TRUTH legado sairia falso.
        # Requisito que sumiu de vez já é o CRÍTICO acima, não este ALTO.
        elif arquivada and dito and rid in agora and para < dito:
            v.append(("ALTO", "specs/TRUTH.md",
                      f"{rid} tem {para} cenários no TRUTH e a delta declarou {dito}",
                      "consolidar o bloco MUDA integralmente — a regra 2 substitui o "
                      "requisito pelo bloco da delta, sem editar no caminho"))


def c5_tamanho(root: Path, v: list) -> None:
    """Custo de contexto do TRUTH.md: linhas, tokens aproximados e domínios — sempre BAIXO.

    Particionado (specs/truth/*.md), mede cada arquivo isoladamente: o particionamento
    existe para carregar um domínio por vez, então o custo relevante é o da maior
    partição, nunca a soma. O sinal de domínios se omite aí — já cumpriu o propósito.
    """
    truth = root / "specs" / "TRUTH.md"
    if not truth.is_file():
        return
    particoes = sorted((root / "specs" / "truth").glob("*.md"))
    for arq in [truth, *particoes]:
        texto = arq.read_text(encoding="utf-8")
        onde = str(arq.relative_to(root))
        acao = ("dividir esta partição em domínios menores" if arq in particoes
                else "particionar em truth/<dominio>.md e virar índice")
        n = len(texto.splitlines())
        if n > TRUTH_LIMITE:
            v.append(("BAIXO", onde, f"{n} linhas (limiar {TRUTH_LIMITE})", acao))
        tokens = len(texto) // CHARS_POR_TOKEN
        if tokens > TRUTH_LIMITE_TOKENS:
            v.append(("BAIXO", onde, f"~{tokens} tokens (limiar {TRUTH_LIMITE_TOKENS})", acao))
        if arq is truth and not particoes:
            dominios = sum(l.startswith("## ") for l in texto.splitlines())
            if dominios > TRUTH_LIMITE_DOMINIOS:
                v.append(("BAIXO", onde, f"{dominios} domínios (limiar {TRUTH_LIMITE_DOMINIOS})", acao))


def c6_pendencias(root: Path, v: list) -> None:
    """Pendência aberta (`- [ ]` em riscos) não sobrevive ao archive sem rotear pro registro de débitos."""
    for p in sorted((root / "specs" / "_archive").glob("*/spec.md")):
        m = SECAO_RISCOS.search(p.read_text(encoding="utf-8"))
        if not m:
            continue
        n = len(PENDENCIA_ABERTA.findall(m.group(1)))
        if n:
            v.append(("ALTO", str(p.relative_to(root)),
                      f"{n} pendência(s) aberta(s) '- [ ]' em delta arquivada",
                      "registrar como arquivo novo DT-NNN em debts/ativos/ (natureza: pendência) e marcar '- [x]'"))


def c7_split(root: Path, delta: Path, v: list) -> None:
    """Mede as linhas adicionadas em specs/NNN-nome/ vs merge-base; BAIXO acima do
    limiar de PR — recomenda o split condicional (R17/cycle.md). Informa, não bloqueia
    (BAIXO não altera o código de saída). Sem git ou sem merge-base, se omite como o C4."""
    try:
        rel = delta.relative_to(root)
    except ValueError:
        return  # delta fora do root — o diff por caminho não se aplica
    base, com_base = base_c4(root)
    if not com_base:
        return  # sem merge-base com origin/main/main — medir contra HEAD enganaria; omite
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "diff", base, "--numstat", "--", str(rel)],
            capture_output=True, text=True, check=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return  # sem git ou caminho não versionado — o check não se aplica
    adicionadas = 0
    for line in out.splitlines():
        col = line.split("\t", 1)[0]
        if col.isdigit():  # binário aparece como '-' no numstat — ignorado
            adicionadas += int(col)
    if adicionadas > PR_LIMITE:
        v.append(("BAIXO", str(rel), f"{adicionadas} linhas adicionadas (limiar {PR_LIMITE})",
                  "abrir primeiro o PR só dos artefatos — split condicional (cycle.md)"))


def c8_testplan(delta: Path, bs, spec_txt: str, v: list) -> None:
    """Cobertura Rn/RNFn → caso de teste (espelho do C2). Ausência: ALTO no perfil
    completo (default sem campo Perfil — retrocompat); BAIXO com dispensa declarada
    (perfil enxuto) ou em bugfix sem tasks (delta-015)."""
    cab = cabecalho(spec_txt)
    tp = delta / "test-plan.md"
    if not tp.is_file():
        dispensa = campo(cab, "Test-plan")
        bugfix = eh_bugfix(cab) and not (delta / "tasks.md").is_file()
        if dispensa and "dispensado" in dispensa.lower():
            v.append(("BAIXO", "test-plan.md", f"dispensado no cabeçalho: {dispensa}", "ok se o perfil enxuto foi aprovado (R1, delta-015)"))
        elif bugfix:
            v.append(("BAIXO", "test-plan.md", "bugfix sem tasks — test-plan sob demanda", "teste de regressão obrigatório cobre (delta-015)"))
        else:
            v.append(("ALTO", "test-plan.md", "test-plan.md ausente sem dispensa declarada", "gerar do template ou declarar 'Test-plan: dispensado — <motivo>' (perfil enxuto)"))
        return
    ids_spec = {rid for rid, _, _, _ in bs}
    cobertos: set[str] = set()
    for item in itens(tp.read_text(encoding="utf-8"), "CT"):
        cid, texto = item["id"], item["texto"]
        cobre = cobre_alvos(texto, ids_spec, f"test-plan.md {cid}", cobertos, v)
        if not cobre or not campo(texto, "tipo") or not campo(texto, r"verifica[çc][ãa]o"):
            v.append(("MÉDIO", f"test-plan.md {cid}", "caso sem 'cobre:'/'tipo:'/'verificação:' completos", "cobre: Rn · tipo: auto|manual · verificação: comando ou passos"))
    for rid in sorted(ids_spec - cobertos):
        v.append(("ALTO", f"spec.md {rid}", "requisito sem caso no test-plan.md", f"adicionar caso com 'cobre: {rid}' (manual roteirizado conta)"))


def c9_grafo(tasks_txt: str, v: list) -> None:
    """Arestas de bloqueio (delta-016): `(dep: Tn[, Tm])` por task; task sem `dep:` é
    livre. Dep inexistente ou ciclo → ALTO. Arquivo sem nenhum `dep:` → cadeia linear
    implícita pela ordem (retrocompatível, R1)."""
    arestas: dict[str, list[str]] = {}
    for item in itens(tasks_txt, "T"):
        tid, resto = item["id"], item["resto"]
        if tid in arestas:
            v.append(("ALTO", f"tasks.md {tid}", "ID de task duplicado no arquivo", "renumerar — ID duplicado engole aresta do grafo (C9)"))
            continue
        d = DEP.match(resto)  # só a aresta colada ao ID é aresta — "(dep: Tn)" em prosa não conta (achado do dogfood da delta-016)
        arestas[tid] = [a.strip() for a in d.group(1).split(",") if a.strip()] if d else []
    if not any(arestas.values()):
        return  # nenhum dep: no arquivo — cadeia linear implícita
    for tid, deps in arestas.items():
        for dep in deps:
            if dep not in arestas:
                v.append(("ALTO", f"tasks.md {tid}", f"dep '{dep}' cita task inexistente", "corrigir a aresta ou criar a task (C9)"))
    # ciclo via graphlib (stdlib) — delete-list do review da delta-016
    ts = graphlib.TopologicalSorter(arestas)
    try:
        ts.prepare()
    except graphlib.CycleError as e:
        ciclo = sorted(set(e.args[1]))
        v.append(("ALTO", "tasks.md", f"ciclo de dependências envolvendo {', '.join(ciclo)}", "remover a aresta que fecha o ciclo (C9)"))


def c10_convergencia(root: Path, v: list) -> None:
    """Convergência mínima no archive (delta-016): delta arquivada com task '- [ ]'
    remanescente no tasks.md → ALTO. A auditoria semântica codebase×spec segue
    juízo humano do review (renúncia por design, ADR-0014)."""
    for p in sorted((root / "specs" / "_archive").glob("*/tasks.md")):
        n = sum(1 for i in itens(p.read_text(encoding="utf-8"), "T") if not i["feito"])
        if n:
            v.append(("ALTO", str(p.relative_to(root)),
                      f"{n} task(s) '- [ ]' em delta arquivada",
                      "concluir ou marcar '- [x]' — archive não fecha com trabalho aberto (C10)"))


def c11_perfil(root: Path, v: list) -> None:
    """Schema do doc-profile.yaml (DT-013, delta-026): exige o núcleo estável e tolera a
    cauda opcional. Nunca CRÍTICO — perfil malformado reporta, não bloqueia (ADR-0006)."""
    perfil = root / "doc-profile.yaml"
    if not perfil.is_file():
        v.append(("BAIXO", "doc-profile.yaml", "perfil ausente na raiz",
                  "criar do template do projeto-init para registrar a decisão de documentação (ADR-0009)"))
        return
    try:
        d = yaml.safe_load(perfil.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        v.append(("ALTO", "doc-profile.yaml", f"YAML inválido: {str(e).splitlines()[0]}",
                  "corrigir a sintaxe do perfil"))
        return
    if not isinstance(d, dict):
        v.append(("ALTO", "doc-profile.yaml", "raiz do perfil não é um mapa",
                  "usar o template do projeto-init"))
        return
    for chave in NUCLEO_TOPO:
        if d.get(chave) is None:  # chave declarada sem valor vira None em YAML — vale por ausente
            v.append(("ALTO", "doc-profile.yaml", f"chave de núcleo ausente ou vazia: {chave}",
                      "copiar do template do projeto-init"))
    dec = d.get("decisao") if isinstance(d.get("decisao"), dict) else {}
    for sub in ("data", "justificativa"):
        if sub not in dec:
            v.append(("ALTO", "doc-profile.yaml", f"decisao.{sub} ausente",
                      "toda decisão de documentação é datada e justificada (ADR-0009)"))
    pub = d.get("publico") if isinstance(d.get("publico"), dict) else {}
    for sub in ("interno", "cliente"):
        if not isinstance(pub.get(sub), bool):
            v.append(("ALTO", "doc-profile.yaml", f"publico.{sub} ausente ou não booleano",
                      "declarar true/false"))
    art = d.get("artefatos") if isinstance(d.get("artefatos"), dict) else {}
    for cat in NUCLEO_ARTEFATOS:
        if cat not in art:
            v.append(("ALTO", "doc-profile.yaml", f"categoria de núcleo ausente: {cat}",
                      "copiar do template — a cauda é opcional, o núcleo não"))
    obrigatorios = [k for k, s in art.items() if isinstance(s, dict) and s.get("obrigatorio") is True]
    justificativa = str(dec.get("justificativa") or "").strip()
    if not obrigatorios and not justificativa:
        v.append(("ALTO", "doc-profile.yaml", "nenhum artefato obrigatório e decisao.justificativa vazia",
                  "perfil sem obrigatório só vale com justificativa preenchida (cycle.md)"))
    mot = d.get("motores") if isinstance(d.get("motores"), dict) else {}
    if mot.get("graphify") and not str(mot.get("graphify_backend") or "").strip():
        v.append(("ALTO", "doc-profile.yaml", "motores.graphify ligado sem motores.graphify_backend",
                  "declarar o backend, ou pare e pergunte ao usuário (R44, ADR-0022)"))
    jira = mot.get("jira")
    if jira not in (None, False):  # ligado: true ou dict (mesmo vazio) — ausente/false é desligado
        projeto = jira.get("projeto") if isinstance(jira, dict) else None
        if not str(projeto or "").strip():
            v.append(("ALTO", "doc-profile.yaml", "motores.jira ligado sem motores.jira.projeto",
                      "declarar a chave do projeto Jira (delta-017), ou desligar o motor"))


def c12_clarify(spec_txt: str, v: list) -> None:
    """Trilha do clarify (DT-023, delta-026): no perfil completo a fase não fecha sem
    declarar se houve canal humano. Perfil enxuto e delta bugfix dispensam — nos dois
    o clarify é sob demanda (cycle.md)."""
    cab = cabecalho(spec_txt)
    if (campo(cab, "Perfil") or "").lower().startswith("enxuto"):
        return
    if eh_bugfix(cab):
        return
    if not CLARIFY.search(cab):  # cabeçalho, não o documento: linha no corpo não é trilha (review da delta-026)
        v.append(("ALTO", "spec.md", "sem a trilha do clarify no cabeçalho",
                  "declarar 'Clarify: entrevistado (AAAA-MM-DD) — <N> decisões do usuário' "
                  "ou 'Clarify: auto-avaliado (AAAA-MM-DD) — sem canal humano' (R8)"))


def c13_links_archive(root: Path, v: list) -> None:
    """Links relativos mortos em delta arquivada (delta-047). O move para `_archive/`
    muda a profundidade dos links dos artefatos e a regra 5 do archive manda recalcular
    — aqui é conferido. Passa o conjunto de arquivos explicitamente para contornar **de
    propósito** o `exclude_links_globs`, que mantém o archive fora do C3: a fronteira
    entre os dois gates é por classe de achado, não por diretório (R13, ADR-0032).
    O atalho do GitHub segue ignorado — quem corta por forma é o próprio scan_links_c3."""
    arquivos = set((root / "specs" / "_archive").glob("*/*.md"))
    if not arquivos:
        return
    _checados, mortos = scan_links_c3(root, arquivos)
    for p, i, alvo in mortos:
        v.append(("ALTO", f"{p.relative_to(root)}:{i}",
                  f"link relativo morto em delta arquivada → {alvo}",
                  "recalcular a profundidade a partir do destino em _archive/ (regra 5 do archive)"))


def checar(root: Path, delta: Path) -> list:
    spec, tasks = delta / "spec.md", delta / "tasks.md"
    if not spec.is_file():
        die(f"spec.md não encontrado em {delta}")
    spec_txt = spec.read_text(encoding="utf-8")
    bs = blocos(spec_txt)
    bugfix = eh_bugfix(cabecalho(spec_txt))
    v: list = []
    if not bs and not bugfix:
        v.append(("ALTO", "spec.md", "nenhum bloco '### Rn — ADICIONA|MUDA|REMOVE'", "usar templates/delta-spec.md"))
    if bugfix:
        # bugfix (delta-015): repro e teste de regressão são o aceite; bloco Rn só quando muda requisito
        repro = re.search(r"^##\s+Reprodu[çc][ãa]o\s*$(.*?)(?=^##\s|\Z)", spec_txt, re.M | re.S)
        alto = repro.group(1).upper() if repro else ""
        if not repro or any(k not in alto for k in ("DADO", "QUANDO", "ENTÃO")):
            v.append(("ALTO", "spec.md", "bugfix sem Reprodução DADO/QUANDO/ENTÃO", "usar templates/bugfix-spec.md"))
        regressao = re.search(r"^##\s+Teste de regress[ãa]o\s*$(.*?)(?=^##\s|\Z)", spec_txt, re.M | re.S)
        if not regressao or not re.search(r"^\s*-\s*\S", regressao.group(1), re.M) or "{{" in regressao.group(1):
            v.append(("ALTO", "spec.md", "bugfix sem teste de regressão declarado", "apontar o teste que falha antes e passa depois do fix (delta-015)"))
    c1_aceite(spec_txt, bs, v)
    if not (bugfix and not tasks.is_file()):  # bugfix sem tasks.md é válido — tasks é sob demanda (delta-015)
        tasks_txt = tasks.read_text(encoding="utf-8") if tasks.is_file() else ""
        c2_cobertura(bs, tasks_txt, v)
        c9_grafo(tasks_txt, v)
    c3_estado(root, v)
    c4_archive(root, bs, v, bool(re.search(r"^Estado:\s*arquivada\b", spec_txt, re.M)))
    c5_tamanho(root, v)
    c6_pendencias(root, v)
    c10_convergencia(root, v)
    c7_split(root, delta, v)
    c8_testplan(delta, bs, spec_txt, v)
    c11_perfil(root, v)
    c12_clarify(spec_txt, v)
    c13_links_archive(root, v)
    c14_checkout(root, v)
    return v


def numeros_de_refs(saida: str) -> set[int]:
    """NNN citados em branches `tipo/NNN-nome` — pura, testável sem rede nem remote."""
    return {int(n) for n in REF_NUMERADA.findall(saida)}


def numeros_do_remoto(root: Path) -> set[int]:
    """NNN ocupados por branch no remoto — fecha a colisão entre checkouts (DT-071, A2).

    Duas fontes que falham de formas opostas, nesta ordem: `ls-remote` é fresco mas
    precisa de rede; os refs de rastreio já em disco são grátis mas envelhecem sem
    `fetch`. O fallback é a mesma fonte que o `ids_em_refs_remotas()` do `debito.py` usa
    para o `DT-NNN` — um padrão só no repositório, em vez de dois.

    Exceção declarada à fronteira "gate não acessa rede" da delta-053: escolher número
    não é emitir veredito. Nada aqui reprova, levanta ou trava — sem nenhuma fonte, o
    comando segue com o disco local e avisa (RNF2).
    """
    try:
        r = subprocess.run(["git", "-C", str(root), "ls-remote", "--heads", "origin"],
                           capture_output=True, text=True, timeout=LS_REMOTE_TIMEOUT)
        if r.returncode == 0:
            return numeros_de_refs(r.stdout)
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    try:
        r = subprocess.run(["git", "-C", str(root), "for-each-ref", "--format=%(refname)",
                            "refs/remotes/"], capture_output=True, text=True)
    except (FileNotFoundError, OSError):
        r = None
    if r is None or r.returncode != 0:
        print("aviso: sem origin nem refs de rastreio — NNN calculado só com o disco local; "
              "confira à mão se houver sessão paralela", file=sys.stderr)
        return set()
    print("aviso: origin inacessível — NNN calculado sobre os refs de rastreio já buscados; "
          "branch criada depois do último fetch fica invisível", file=sys.stderr)
    return numeros_de_refs(r.stdout)


def c14_checkout(root: Path, v: list) -> None:
    """Checkout volátil ou raso — o primeiro destrói trabalho, o segundo cega C4 e C7.

    Duas severidades de propósito (DT-043). Trabalhar sob `plugins/marketplaces/` é
    **erro**: o diretório é re-clonado sem aviso e a reflog fica só com `clone`, sem
    ORIG_HEAD para resgatar — na delta-047 foi re-clonado três vezes e levou uma branch
    com 3 commits. Clone **raso** é legítimo (o próprio `ci.yml` roda em
    `actions/checkout` sem `fetch-depth`), e só explica por que o C4 e o C7 se calaram.
    """
    if DIR_MARKETPLACE in root.resolve().as_posix():
        v.append(("ALTO", str(root), "delta aberta dentro do checkout do marketplace",
                  "trabalhar num clone próprio ou em `git worktree` — este diretório é "
                  "re-clonado a cada /plugin update e leva branch e commit não pushados"))
        return
    r = subprocess.run(["git", "-C", str(root), "rev-parse", "--is-shallow-repository"],
                       capture_output=True, text=True)
    if r.returncode == 0 and r.stdout.strip() == "true":
        v.append(("BAIXO", str(root), "clone raso — C4 e C7 se omitem por falta de merge-base",
                  "`git fetch --unshallow` para recuperar a proteção contra perda de requisito"))


def numero_delta_livre(root: Path) -> int:
    """Próximo NNN livre para abrir uma delta (R5) — max() de três fontes, não só o
    diretório. Duas colisões reais provaram que 'max(specs/, specs/_archive/) + 1' sozinho
    não basta: a LIÇÃO de 2026-08-11 (archive da delta-047 duplicado por duas sessões vivas
    em paralelo) e o DT-036 do repo `_pmo` em 2026-08-12 (delta consumida por merge sem
    nunca ganhar `specs/NNN-*/`, só citada em `TRUTH.md`/`CHANGELOG.md`) — mecanismos
    diferentes, mesmo sintoma. Cobre o segundo caso aqui: soma às pastas toda citação
    'delta-NNN'/'ΔNNN' no TRUTH.md (índice e, se particionado, `specs/truth/*.md`) e no
    CHANGELOG.md. O primeiro (concorrência entre checkouts) reincidiu em 2026-08-20 — duas
    deltas 072 no mesmo dia — e passou a ser coberto na delta-082: `numeros_do_remoto()`
    soma os NNN das branches do remoto, com degradação para o disco local (A2 do DT-071).

    Menção NÃO conta quando é citação de delta de outro repo (DT-039 do `_pmo`): a
    sequência local é contígua, então as menções são aceitas em ordem crescente e só
    enquanto não saltarem mais que SALTO_MENCAO acima da sequência já aceita — pasta é
    sempre local e conta incondicionalmente."""
    nums: set[int] = set()
    for base in (root / "specs", root / "specs" / "_archive"):
        for p in base.glob("*"):
            if p.is_dir() and (m := re.match(r"(\d+)-", p.name)):
                nums.add(int(m.group(1)))
    # Branch no remoto ocupa NNN como pasta local ocupa: incondicional, sem a tolerância
    # de contiguidade das menções — nome de branch deste repositório não é citação
    # estrangeira (DT-039), é reserva de fato de outra sessão.
    nums |= numeros_do_remoto(root)
    mencoes: set[int] = set()
    fontes = [root / "specs" / "TRUTH.md", root / "CHANGELOG.md",
              *sorted((root / "specs" / "truth").glob("*.md"))]
    for f in fontes:
        if f.is_file():
            mencoes.update(int(n) for n in NUM_DELTA.findall(f.read_text(encoding="utf-8")))
    atual = max(nums, default=0)
    for n in sorted(mencoes):
        if n <= atual + SALTO_MENCAO:
            atual = max(atual, n)
    return atual + 1


def achar_delta(root: Path) -> Path:
    deltas = [p for p in sorted((root / "specs").glob("*/spec.md"))]
    if not deltas:
        die("nenhuma delta em ./specs — passe o diretório explicitamente")
    if len(deltas) > 1:
        die("mais de uma delta aberta: " + ", ".join(str(p.parent.name) for p in deltas))
    return deltas[0].parent


def main() -> None:
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    if arg == "--selftest":
        selftest()
        return
    if arg == "--proximo-numero":
        root = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else Path.cwd()
        print(f"{numero_delta_livre(root):03d}")
        return
    if arg:
        delta = Path(arg).resolve()
        if not delta.is_dir():
            die(f"não é diretório: {delta}")
        root = delta.parent.parent if delta.parent.name == "specs" else delta.parent.parent.parent
    else:
        root = Path.cwd()
        delta = achar_delta(root)
    v = sorted(checar(root, delta), key=lambda f: ORDEM.get(f[0], 2))

    print(f"# Analyze (mecânico, parcial) — {delta.name}")
    print("| # | Severidade | Onde | Inconsistência | Ação sugerida |")
    print("|---|---|---|---|---|")
    for i, (sev, onde, o_que, acao) in enumerate(v, 1):
        print(f"| {i} | {sev} | {onde} | {o_que} | {acao} |")
    print("\nParcial: cobre C1–C14; os checks 3 e 5 do analyze.md (scope creep, regra canônica) são juízo humano e não rodaram.")
    sevs = {f[0] for f in v}
    veredito = "BLOQUEADO" if "CRÍTICO" in sevs else "LIBERADO COM RESSALVAS" if v else "LIBERADO"
    print(f"\n**Veredito:** {veredito}")
    sys.exit(1 if sevs & {"CRÍTICO", "ALTO"} else 0)


def selftest() -> None:
    import tempfile

    limpa_spec = """# delta-001 — x
Estado: proposta · Data: 2026-01-01 · Branch: feat/001-x
Clarify: entrevistado (2026-01-01) — 2 decisões do usuário

## Mudanças
### R1 — ADICIONA: login
- DADO usuário anônimo QUANDO envia credencial válida ENTÃO recebe sessão

## Requisitos não funcionais
### RNF1 — ADICIONA: latência
- Métrica: p95 < 300ms sob 100 req/s
- Verificação: teste de carga no CI
"""
    limpa_tasks = "- [ ] T1 — form · arquivos: a.py · cobre: R1 · verificação: pytest\n" \
                  "- [ ] T2 — cache · arquivos: b.py · cobre: RNF1 · verificação: k6\n"
    suja_spec = limpa_spec.replace(
        "- DADO usuário anônimo QUANDO envia credencial válida ENTÃO recebe sessão", "- deve funcionar bem"
    ).replace("- Métrica: p95 < 300ms sob 100 req/s", "- Métrica: {{...}}") + \
        "\n### R2 — ADICIONA: logout\n- DADO sessão ativa QUANDO sai ENTÃO sessão encerra\n"
    suja_tasks = "- [ ] T1 — form · arquivos: a.py · cobre: R9 · verificação: pytest\n" \
                 "- [ ] T2 — cache · arquivos: b.py · cobre: RNF1\n"

    limpa_testplan = "- [ ] CT1 — login ok · cobre: R1 · tipo: auto · verificação: pytest -k login\n" \
                     "- [ ] CT2 — latência · cobre: RNF1 · tipo: manual · verificação: roteiro k6 em docs\n"

    def rodar(spec_txt, tasks_txt=None, testplan_txt=None):
        """Runner único das fixtures: arquivo None não é gravado (bugfix roda sem tasks.md)."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            delta = root / "specs" / "001-x"
            delta.mkdir(parents=True)
            (root / "doc-profile.yaml").write_text(PERFIL_NUCLEO, encoding="utf-8")  # C11 (delta-026)
            (delta / "spec.md").write_text(spec_txt, encoding="utf-8")
            if tasks_txt is not None:
                (delta / "tasks.md").write_text(tasks_txt, encoding="utf-8")
            if testplan_txt is not None:
                (delta / "test-plan.md").write_text(testplan_txt, encoding="utf-8")
            return checar(root, delta)

    assert rodar(limpa_spec, limpa_tasks, limpa_testplan) == [], "delta limpa deveria passar sem achados"

    # mesma delta na notação RF-NN/RNF-NN (corpus legado, numeração hierárquica)
    limpa_spec_rf = limpa_spec.replace("### R1 —", "### RF-01.1 —").replace("### RNF1 —", "### RNF-01 —")
    limpa_tasks_rf = limpa_tasks.replace("cobre: R1", "cobre: RF-01.1").replace("cobre: RNF1", "cobre: RNF-01")
    limpa_testplan_rf = limpa_testplan.replace("cobre: R1", "cobre: RF-01.1").replace("cobre: RNF1", "cobre: RNF-01")
    assert rodar(limpa_spec_rf, limpa_tasks_rf, limpa_testplan_rf) == [], "delta limpa em notação RF-NN deveria passar sem achados"

    # heading '###' fora da forma canônica (delta-033): blocos() descarta esse heading em
    # silêncio — sem este check, o requisito some do gate sem nenhum achado (o caso medido:
    # '### R2 — Adiciona:' em minúsculo, veredito saía LIBERADO). A varredura é escopada às
    # seções de requisito ('Mudanças' e 'Requisitos não funcionais') — review da Task 4.
    spec_mudancas_invalida = limpa_spec.replace(
        "### R1 — ADICIONA: login\n- DADO usuário anônimo QUANDO envia credencial válida ENTÃO recebe sessão\n",
        "### R1 — ADICIONA: login\n- DADO usuário anônimo QUANDO envia credencial válida ENTÃO recebe sessão\n"
        "### R2 — Adiciona: outra coisa\n- DADO a QUANDO b ENTÃO c\n")
    heading_mudancas = [a for a in rodar(spec_mudancas_invalida, limpa_tasks, limpa_testplan) if "fora da forma canônica" in a[2]]
    assert len(heading_mudancas) == 1 and heading_mudancas[0][1] == "spec.md l.8" and "R2 — Adiciona" in heading_mudancas[0][2], \
        f"heading minúsculo em 'Mudanças' deveria virar 1 ALTO nomeando a linha e o texto: {heading_mudancas}"

    spec_rnf_invalido = limpa_spec + "### RNF2 — Adiciona: outra coisa\n- Métrica: x\n- Verificação: y\n"
    heading_rnf = [a for a in rodar(spec_rnf_invalido, limpa_tasks, limpa_testplan) if "fora da forma canônica" in a[2]]
    assert len(heading_rnf) == 1 and heading_rnf[0][1] == "spec.md l.13" and "RNF2 — Adiciona" in heading_rnf[0][2], \
        f"heading minúsculo em 'Requisitos não funcionais' deveria virar 1 ALTO (prova que a 2ª seção é varrida): {heading_rnf}"

    spec_detalhamento = limpa_spec + "\n## Dependências e riscos\n### Detalhamento\nprosa qualquer\n"
    achados_detalhamento = rodar(spec_detalhamento, limpa_tasks, limpa_testplan)
    assert not any("fora da forma canônica" in a[2] for a in achados_detalhamento), \
        f"'### Detalhamento' fora das seções de requisito não pode virar achado: {achados_detalhamento}"

    assert rodar(limpa_spec, limpa_tasks, limpa_testplan) == [], \
        "spec só com headings válidos não pode ganhar achado de heading (calibração 2026-08-07: 0/92 no corpus real)"

    # caso preexistente: spec sem nenhum '###' continua acusando 'nenhum bloco' (não é
    # engolido pela detecção nova de heading fora da forma)
    sem_blocos = rodar("# delta-003 — x\nEstado: proposta · Data: 2026-01-01 · Branch: feat/003-x\n\n"
                       "## Contexto\nprosa sem heading de requisito\n")
    assert any("nenhum bloco" in q for _, _, q, _ in sem_blocos), f"spec sem headings deveria acusar 'nenhum bloco': {sem_blocos}"
    assert not any("fora da forma canônica" in q for _, _, q, _ in sem_blocos), f"spec sem headings não inventa achado de heading: {sem_blocos}"

    achados = " · ".join(f"{o} {q}" for _, o, q, _ in rodar(suja_spec, suja_tasks))
    for esperado in (
        "spec.md R1 cenário de aceite sem DADO/QUANDO/ENTÃO",  # C1 Rn
        "spec.md RNF1 RNF sem Métrica preenchida",             # C1 RNF placeholder
        "tasks.md T1 cobre 'R9', que não existe",              # C2 referência morta
        "tasks.md T2 task sem 'verificação:'",                 # C2 task sem verificação
        "spec.md R2 requisito sem task",                       # C2 órfão
    ):
        assert esperado in achados, f"não pegou: {esperado}\nachados: {achados}"

    arquivada_pendente = """# delta-001 — x
Estado: arquivada · Data: 2026-01-01 · Branch: feat/001-x

## Mudanças
### R1 — ADICIONA: login
- DADO a QUANDO b ENTÃO c

## Dependências e riscos
- risco informativo comum, sem checkbox
- [ ] pendência aberta: limiar de X não fechado
- [x] pendência já roteada para o registro (DT-NNN)
"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        arq = root / "specs" / "_archive" / "001-x"
        arq.mkdir(parents=True)
        (arq / "spec.md").write_text(arquivada_pendente, encoding="utf-8")
        v: list = []
        c6_pendencias(root, v)
        assert len(v) == 1 and v[0][0] == "ALTO" and "1 pendência" in v[0][2], f"C6: {v}"
        assert "debts/ativos" in v[0][3], f"C6 deve rotear para debts/ativos/ (delta-043): {v}"

    # C8 — plano de testes (delta-015); fixtures passam pelo checar() completo
    ausente = rodar(limpa_spec, limpa_tasks)  # sem test-plan.md, perfil completo (default)
    assert any(s == "ALTO" and "test-plan.md ausente" in q for s, o, q, _ in ausente), f"C8 ausente: {ausente}"
    spec_dispensa = limpa_spec.replace(
        "Estado: proposta · Data: 2026-01-01 · Branch: feat/001-x",
        "Estado: proposta · Data: 2026-01-01 · Branch: feat/001-x · Perfil: enxuto (aprovado: 2026-01-01) · Test-plan: dispensado — delta só de prosa")
    dispensada = rodar(spec_dispensa, limpa_tasks)
    assert len(dispensada) == 1 and dispensada[0][0] == "BAIXO", f"C8 dispensa: {dispensada}"
    orfao = rodar(limpa_spec, limpa_tasks, "- [ ] CT1 — login ok · cobre: R1 · tipo: auto · verificação: pytest\n")
    assert any(s == "ALTO" and o == "spec.md RNF1" and "sem caso" in q for s, o, q, _ in orfao), f"C8 órfão: {orfao}"
    morta = rodar(limpa_spec, limpa_tasks, limpa_testplan + "- [ ] CT3 — x · cobre: R9 · tipo: auto · verificação: pytest\n")
    assert any(s == "ALTO" and "R9" in q for s, _, q, _ in morta), f"C8 referência morta: {morta}"
    caso_sem_campos = rodar(limpa_spec, limpa_tasks, "- [ ] CT1 — login ok · cobre: R1\n- [ ] CT2 — lat · cobre: RNF1 · tipo: auto · verificação: k6\n")
    assert any(s == "MÉDIO" and "CT1" in o for s, o, q, _ in caso_sem_campos), f"C8 caso incompleto: {caso_sem_campos}"
    # comentário HTML de template citando as sintaxes não pode enganar o campo() (review delta-015)
    spec_comentario = limpa_spec.replace(
        "Estado: proposta · Data: 2026-01-01 · Branch: feat/001-x",
        "Estado: proposta · Data: 2026-01-01 · Branch: feat/001-x\n"
        "<!-- exemplo: dispensa é 'Test-plan: dispensado — <motivo>'; bugfix usa 'Tipo: bugfix' -->")
    comentado = rodar(spec_comentario, limpa_tasks)
    assert any(s == "ALTO" and "test-plan.md ausente" in q for s, _, q, _ in comentado), \
        f"C8 enganado por comentário de template: {comentado}"

    # C9 — grafo de tasks (delta-016): dep válido passa; dep morta e ciclo acusam ALTO
    dep_ok = limpa_tasks.replace("- [ ] T2 — cache", "- [ ] T2 (dep: T1) — cache")
    assert rodar(limpa_spec, dep_ok, limpa_testplan) == [], "C9: dep válido deveria passar sem achados"
    dep_morta = rodar(limpa_spec, limpa_tasks.replace("- [ ] T2 — cache", "- [ ] T2 (dep: T9) — cache"), limpa_testplan)
    assert any(s == "ALTO" and "T9" in q for s, _, q, _ in dep_morta), f"C9 dep inexistente: {dep_morta}"
    ciclo_tasks = ("- [ ] T1 (dep: T2) — form · arquivos: a.py · cobre: R1 · verificação: pytest\n"
                   "- [ ] T2 (dep: T1) — cache · arquivos: b.py · cobre: RNF1 · verificação: k6\n")
    com_ciclo = rodar(limpa_spec, ciclo_tasks, limpa_testplan)
    assert any(s == "ALTO" and "ciclo" in q for s, _, q, _ in com_ciclo), f"C9 ciclo: {com_ciclo}"
    # prosa com (dep: ...) não é aresta — dep: só conta colado ao ID (dogfood delta-016)
    prosa_dep = limpa_tasks + "- [ ] T3 — documenta a sintaxe `(dep: T1)` no template · arquivos: c.py · cobre: R1 · verificação: leitura\n"
    v_prosa = rodar(limpa_spec, prosa_dep, limpa_testplan)
    assert not any("dep" in q for _, _, q, _ in v_prosa), f"C9 falso positivo em prosa: {v_prosa}"
    # ID de task duplicado sobrescreve arestas[id] e engole aresta/ciclo — falso negativo (review delta-016)
    dup_id = ("- [ ] T1 (dep: T2) — a · arquivos: a.py · cobre: R1 · verificação: pytest\n"
              "- [ ] T1 — b · arquivos: b.py · cobre: R1 · verificação: pytest\n"
              "- [ ] T2 (dep: T1) — cache · arquivos: c.py · cobre: RNF1 · verificação: k6\n")
    v_dup = rodar(limpa_spec, dup_id, limpa_testplan)
    assert any(s == "ALTO" and "duplicad" in q for s, _, q, _ in v_dup), f"C9 ID duplicado: {v_dup}"

    # C10 — convergência mínima no archive (delta-016)
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        arq = root / "specs" / "_archive" / "001-x"
        arq.mkdir(parents=True)
        (arq / "spec.md").write_text(limpa_spec.replace("Estado: proposta", "Estado: arquivada"), encoding="utf-8")
        (arq / "tasks.md").write_text("- [x] T1 — feito · cobre: R1 · verificação: ok\n"
                                      "- [ ] T2 — esquecida · cobre: RNF1 · verificação: k6\n", encoding="utf-8")
        v10: list = []
        c10_convergencia(root, v10)
        assert len(v10) == 1 and v10[0][0] == "ALTO" and "1 task" in v10[0][2], f"C10 task aberta: {v10}"
        (arq / "tasks.md").write_text("- [x] T1 — feito · cobre: R1 · verificação: ok\n", encoding="utf-8")
        v10 = []
        c10_convergencia(root, v10)
        assert v10 == [], f"C10 falso positivo com tudo concluído: {v10}"

    # item multi-linha (delta-033, DT-001): C2/C8/C9 consomem itens.py — task/caso quebrado
    # em duas linhas não pode virar achado falso, e prosa/continuação não pode virar campo.
    tasks_multi = "- [ ] T1 — form · arquivos: a.py · cobre: R1 · verificação: pytest\n" \
                  "- [x] T2 (dep: T1) — cache · arquivos: b.py\n" \
                  "      · cobre: RNF1 · verificação: k6\n"
    achados_uma = rodar(limpa_spec, limpa_tasks.replace("- [ ] T2", "- [x] T2 (dep: T1)"), limpa_testplan)
    achados_multi = rodar(limpa_spec, tasks_multi, limpa_testplan)
    assert achados_uma == achados_multi, \
        f"fixture gêmea: linha única {achados_uma} vs quebrada em duas {achados_multi}"

    tasks_com_prosa = "- [ ] T1 — form · arquivos: a.py · cobre: R1\n" \
                      "\n" \
                      "Prosa solta depois da lista, contém verificação: pytest mas não é da task.\n"
    achados_prosa = rodar(limpa_spec, tasks_com_prosa, limpa_testplan)
    assert any(s == "ALTO" and o == "tasks.md T1" and "verificação" in q for s, o, q, _ in achados_prosa), \
        f"prosa após linha em branco não pode virar 'verificação:' de T1: {achados_prosa}"

    testplan_multi = "- [ ] CT1 — login ok · cobre: R1 · tipo: auto\n" \
                     "      · verificação: pytest -k login\n" \
                     "- [ ] CT2 — latência · cobre: RNF1 · tipo: manual · verificação: roteiro k6 em docs\n"
    achados_tp_multi = rodar(limpa_spec, limpa_tasks, testplan_multi)
    assert achados_tp_multi == [], f"CT quebrado em duas linhas deveria ser lido inteiro: {achados_tp_multi}"

    tasks_dep_continuacao = "- [ ] T1 — form · arquivos: a.py · cobre: R1 · verificação: pytest\n" \
                            "- [ ] T2 — cache · arquivos: b.py\n" \
                            "      · cobre: RNF1 · verificação: k6 (dep: T1)\n"
    v_dep_cont = rodar(limpa_spec, tasks_dep_continuacao, limpa_testplan)
    assert not any("dep" in q for _, _, q, _ in v_dep_cont), \
        f"(dep: T1) na continuação não é aresta — só conta colado ao ID (R40): {v_dep_cont}"

    # bugfix (delta-015): sem bloco Rn é válido; repro e teste de regressão são obrigatórios
    bugfix_ok = """# delta-002 — fix parse
Estado: proposta · Data: 2026-01-01 · Branch: fix/002-parse · Tipo: bugfix

## Sintoma (≤3 linhas)
gate aceita spec vazia

## Reprodução
- DADO spec sem blocos QUANDO o gate roda ENTÃO passa — esperado: acusar

## Causa-raiz
regex não cobre o caso

## Teste de regressão
- fixture bugfix_ok no selftest

## Mudanças
- nenhuma (correção sem mudança de requisito)
"""
    v_bugfix = rodar(bugfix_ok)
    assert not any("nenhum bloco" in q for _, _, q, _ in v_bugfix), f"bugfix não exige bloco Rn: {v_bugfix}"
    assert not any(s == "ALTO" for s, _, _, _ in v_bugfix), f"bugfix sem tasks/test-plan é válido (só BAIXO do C8): {v_bugfix}"
    sem_regressao = bugfix_ok.replace("## Teste de regressão\n- fixture bugfix_ok no selftest\n\n", "")
    v_sem = rodar(sem_regressao)
    assert any(s == "ALTO" and "regressão" in q for s, _, q, _ in v_sem), f"bugfix sem teste de regressão: {v_sem}"

    print("selftest: OK (3 fixtures + C8 + C9 + bugfix, defeitos detectados nos dois lados da cobertura)")
    selftest_c4()
    selftest_c5()
    selftest_c7()
    selftest_c11()
    selftest_c12()
    selftest_c13()
    selftest_c14()
    selftest_numero_delta_livre()


def selftest_c11() -> None:
    """C11: núcleo exigido, cauda tolerada, YAML inválido reportado sem estourar."""
    import tempfile

    nucleo = PERFIL_NUCLEO
    casos = [
        (nucleo, 0, "perfil de núcleo íntegro não acusa nada"),
        (nucleo + "  explicativos: { obrigatorio: false }\n", 0, "cauda presente é aceita"),
        (nucleo + "  prototipo: { obrigatorio: false }\n  apresentacao: { obrigatorio: false }\n", 0,
         "cauda inteira presente é aceita"),
        ("version: 2\n" + nucleo, 0, "perfil que ainda traga `version` continua válido, em qualquer valor"),
        (nucleo.replace('publico: { interno: true, cliente: false }', "publico:"), 3,
         "chave de núcleo declarada sem valor acusa ALTO (a chave e os dois booleanos)"),
        (nucleo.replace('decisao: { data: "2026-01-01", justificativa: "" }', 'decisao: { data: "2026-01-01" }'), 1,
         "decisao.justificativa ausente acusa ALTO"),
        (nucleo.replace("publico: { interno: true", 'publico: { interno: "true"'), 1,
         "publico.interno não booleano acusa ALTO"),
        (nucleo.replace("obrigatorio: true", 'obrigatorio: "false"'), 1,
         "obrigatorio como string não conta como obrigatório"),
        (nucleo.replace("  casos-de-uso: { obrigatorio: false }\n", ""), 1, "categoria de núcleo ausente acusa ALTO"),
        (nucleo.replace("obrigatorio: true", "obrigatorio: false"), 1,
         "nenhum obrigatório com justificativa vazia acusa ALTO"),
        (nucleo.replace('justificativa: ""', 'justificativa: "só prosa, sem diagrama"')
               .replace("obrigatorio: true", "obrigatorio: false"), 0,
         "nenhum obrigatório com justificativa preenchida é válido"),
        (nucleo + "motores: { graphify: true, graphify_backend: '' }\n", 1,
         "graphify ligado sem backend acusa ALTO"),
        (nucleo + "motores: { graphify: true, graphify_backend: claude-cli }\n", 0,
         "graphify ligado com backend declarado é válido"),
        (nucleo + "motores: { graphify: false }\n", 0, "graphify desligado dispensa o backend"),
        (nucleo + "motores: { jira: { projeto: SBX } }\n", 0, "jira ligado com projeto declarado é válido"),
        (nucleo + "motores: { jira: {} }\n", 1, "jira ligado sem projeto (dict vazio) acusa ALTO"),
        (nucleo + "motores: { jira: true }\n", 1, "jira ligado como booleano acusa ALTO"),
        (nucleo + "motores: { jira: false }\n", 0, "jira desligado dispensa o projeto"),
        (nucleo, 0, "sem chave jira não acusa nada (já coberto pelo caso de núcleo íntegro)"),
        ("isto: : não é yaml\n", 1, "YAML inválido acusa ALTO, sem exceção"),
        ("- isto é uma lista, não um mapa\n", 1, "raiz que não é mapa acusa ALTO"),
    ]
    for texto, esperado, desc in casos:
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            (raiz / "doc-profile.yaml").write_text(texto, encoding="utf-8")
            v: list = []
            c11_perfil(raiz, v)
            altos = [s for s, *_ in v if s == "ALTO"]
            assert len(altos) == esperado, f"{desc}: esperado {esperado} ALTO, veio {v}"
            assert "CRÍTICO" not in {s for s, *_ in v}, f"{desc}: C11 nunca é CRÍTICO ({v})"
    with tempfile.TemporaryDirectory() as d:  # perfil ausente = BAIXO, nunca ALTO
        v = []
        c11_perfil(Path(d), v)
        assert len(v) == 1 and v[0][0] == "BAIXO", f"perfil ausente deve ser BAIXO: {v}"
    print("selftest C11: OK (núcleo exigido, cauda tolerada, YAML inválido tratado)")


def selftest_c12() -> None:
    """C12: trilha exigida no perfil completo, dispensada no enxuto, imune a prosa."""
    base = "# delta-999 — x\nEstado: proposta · Data: 2026-08-02 · Perfil: {perfil}\n{trilha}\n\n## Contexto\n"
    casos = [
        ("completo", "Clarify: entrevistado (2026-08-02) — 3 decisões do usuário", 0, "entrevistado passa"),
        ("completo", "Clarify: auto-avaliado (2026-08-02) — sem canal humano", 0,
         "auto-avaliado passa — declarar é o ponto, não fingir entrevista"),
        ("completo", "", 1, "perfil completo sem trilha acusa ALTO"),
        ("enxuto — escopo pequeno (aprovado: 2026-08-02)", "", 0, "perfil enxuto dispensa (clarify sob demanda)"),
        ("", "", 1, "sem campo Perfil vale como completo (retrocompatível)"),
        ("completo", "esta linha menciona Clarify: entrevistado no meio da prosa", 1,
         "sintaxe citada em prosa não conta — só vale na âncora de início de linha"),
    ]
    v_bugfix: list = []
    c12_clarify("# delta-999 — x\nEstado: proposta · Tipo: bugfix · Perfil: completo\n\n## Contexto\n", v_bugfix)
    assert v_bugfix == [], f"delta bugfix dispensa a trilha — clarify sob demanda (cycle.md): {v_bugfix}"
    v_corpo: list = []  # trilha fora do cabeçalho não conta (review da delta-026)
    c12_clarify("# delta-999 — x\nEstado: proposta · Perfil: completo\n\n## Contexto\n"
                "Clarify: entrevistado (2026-08-02) — 3 decisões do usuário\n", v_corpo)
    assert len(v_corpo) == 1, f"linha no corpo não é trilha — a âncora é o cabeçalho: {v_corpo}"
    for perfil, trilha, esperado, desc in casos:
        v: list = []
        c12_clarify(base.format(perfil=perfil, trilha=trilha), v)
        altos = [s for s, *_ in v if s == "ALTO"]
        assert len(altos) == esperado, f"{desc}: esperado {esperado} ALTO, veio {v}"
    print("selftest C12: OK (trilha exigida no completo, dispensada no enxuto, prosa não engana)")


def selftest_c4() -> None:
    """C4 com git real: perda já commitada é acusada; alvo declarado em MUDA não é."""
    import tempfile

    def rodar(resultante: str, spec: str = "", particoes: dict | None = None, base: str | None = None,
              arquivada: bool = True):
        """TRUTH base legado (Δ000) → estado `resultante` num commit; roda o C4 sobre `spec`.
        `particoes`: {nome: conteúdo} gravado em specs/truth/<nome>.md no estado resultante.
        A base default fica de propósito no formato legado de bullets — retrocompatibilidade
        garantida pela delta-055 (ADR-0034); o formato vigente (heading por requisito)
        é exercitado na fixture de particionamento."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)

            def git(*args):
                subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)

            git("init", "-q", "-b", "main")
            git("config", "user.email", "selftest@sdd")
            git("config", "user.name", "selftest")
            (root / "specs").mkdir()
            (root / "specs" / "TRUTH.md").write_text(
                base if base is not None else "- R1 (Δ000) — a\n- R2 (Δ000) — b\n", encoding="utf-8")
            git("add", "-A")
            git("commit", "-qm", "base")
            git("checkout", "-qb", "docs/archive")
            (root / "specs" / "TRUTH.md").write_text(resultante, encoding="utf-8")
            for nome, conteudo in (particoes or {}).items():
                (root / "specs" / "truth").mkdir(exist_ok=True)
                (root / "specs" / "truth" / f"{nome}.md").write_text(conteudo, encoding="utf-8")
            git("add", "-A")
            # --allow-empty: a delta ainda proposta não mexeu no TRUTH, e é justamente
            # esse estado que o caso do DT-090 exercita
            git("commit", "-qm", "consolida", "--allow-empty")  # commitado: a antiga janela cega do diff HEAD
            v: list = []
            c4_archive(root, blocos(spec), v, arquivada)
            return v

    try:
        subprocess.run(["git", "--version"], check=True, capture_output=True)
    except (FileNotFoundError, OSError):
        print("selftest C4: PULADO (git indisponível)")
        return
    # git presente: daqui em diante toda falha é ruidosa — PULADO não mascara regressão
    perdidos = rodar("- R2 (Δ000) — b\n")  # R1 removido de fato, sem MUDA
    assert any(s == "CRÍTICO" and "R1" in q for s, _, q, _ in perdidos), \
        f"C4 não acusou perda commitada: {perdidos}"
    declara = rodar("- R2 (Δ000) — b\n", "### R9 — MUDA R1 (Δ000): a\n- DADO a QUANDO b ENTÃO c\n")
    assert declara == [], "C4 acusou falso positivo com MUDA declarado"
    # reescrita de sufixo (Δ→delta) preserva os IDs no arquivo → não é perda, sem MUDA
    reescreve = rodar("- R1 (delta-000) — a\n- R2 (delta-000) — b\n")
    assert reescreve == [], f"C4 acusou reescrita de sufixo como perda: {reescreve}"
    # anotação de proveniência do MUDA parcial ('(delta-000; nota: delta-052)') preserva o ID
    anotado = rodar("- R1 (delta-000; nota: delta-052) — a\n- R2 (Δ000) — b\n")
    assert anotado == [], f"C4 acusou anotação multi-delta como perda: {anotado}"
    # e o inverso, que é o lado grave: requisito já anotado tem que seguir dentro do C4
    perda_anotada = rodar("- R2 (Δ000) — b\n", base="- R1 (delta-000; nota: delta-052) — a\n- R2 (Δ000) — b\n")
    assert any(s == "CRÍTICO" and "R1" in q for s, _, q, _ in perda_anotada), \
        f"C4 não acusou perda de requisito anotado: {perda_anotada}"
    # particionamento (C5): TRUTH.md vira índice e os requisitos passam a viver em
    # specs/truth/<dominio>.md — ler só o índice acusaria perda que não houve; a partição
    # sai no formato vigente (### Rn (delta-NNN), ADR-0034), que a âncora ALVO casa igual
    particiona = rodar("# Índice\n- ver truth/dominio.md\n",
                       particoes={"dominio": "### R1 (Δ000) — a\n- DADO a QUANDO b ENTÃO c\n\n### R2 (Δ000) — b\n"})
    assert particiona == [], f"C4 acusou particionamento do TRUTH como perda: {particiona}"
    # notação RF-NN/RNF-NN (corpus legado) tem o mesmo tratamento que Rn/RNFn
    rf_perdido = rodar("- RF-02 (delta-000) — b\n", base="- RF-01 (delta-000) — a\n- RF-02 (delta-000) — b\n")
    assert any(s == "CRÍTICO" and "RF-01" in q for s, _, q, _ in rf_perdido), \
        f"C4 não acusou perda na notação RF-NN: {rf_perdido}"
    rf_declara = rodar("- RF-02 (delta-000) — b\n",
                       "### RF-09 — MUDA RF-01 (delta-000): a\n- DADO a QUANDO b ENTÃO c\n",
                       base="- RF-01 (delta-000) — a\n- RF-02 (delta-000) — b\n")
    assert rf_declara == [], f"C4 acusou falso positivo com MUDA declarado em RF-NN: {rf_declara}"
    # granularidade de cenário (DT-075): o ID sobrevive ao MUDA, o requisito encolhe.
    # Reprodução da delta-077, onde o R95 foi de 7 cenários para 3 com veredito LIBERADO.
    tres = ("### R1 (Δ000) — a\n- DADO a QUANDO b ENTÃO c\n"
            "- DADO d QUANDO e ENTÃO f\n- DADO g QUANDO h ENTÃO i\n")
    um = "### R1 (Δ000) — a\n- DADO a QUANDO b ENTÃO c\n"
    encolhe = rodar(um, "### R9 — MUDA R1 (Δ000): a\n- DADO a QUANDO b ENTÃO c\n", base=tres)
    assert any(s == "ALTO" and "cenário" in q and "R1" in q for s, _, q, _ in encolhe), \
        f"C4 não acusou encolhimento de requisito alvo de MUDA: {encolhe}"
    assert not any(s == "CRÍTICO" for s, *_ in encolhe), \
        f"encolhimento é ALTO, não CRÍTICO (o autor pode ter declarado a remoção): {encolhe}"
    # MUDA integral: o sufixo passa à delta nova e os 3 cenários são repetidos — caso
    # legítimo e o mais comum. Reescrever o sufixo é o que um MUDA de verdade faz.
    integral = rodar(tres.replace("(Δ000)", "(delta-082)"),
                     "### R9 — MUDA R1 (Δ000): a\n- DADO a QUANDO b ENTÃO c\n", base=tres)
    assert integral == [], f"C4 acusou MUDA integral como encolhimento: {integral}"
    # requisito fora de MUDA que encolhe segue fora do C4-cenário: quem cuida dele é o
    # C4-requisito, por ID, e ele não sumiu
    sem_muda = rodar(um, base=tres)
    assert not any("cenário" in q for _, _, q, _ in sem_muda), \
        f"C4 contou cenário de requisito que não é alvo de MUDA: {sem_muda}"
    # O outro lado do mesmo defeito, achado ao exercitar o check na própria delta-082:
    # a delta declara N cenários e a consolidação aterrissa N-1. Comparar só contra o
    # merge-base é cego a isso quando a delta **cresce** o requisito — 35 na base, 42
    # declarados, 41 no disco: cresceu, e mesmo assim um cenário declarado se perdeu.
    quatro = tres + "- DADO j QUANDO k ENTÃO l\n"
    engole = rodar(tres,  # aterrissou 3 dos 4 que o bloco MUDA declara
                   "### R9 — MUDA R1 (Δ000): a\n- DADO a QUANDO b ENTÃO c\n"
                   "- DADO d QUANDO e ENTÃO f\n- DADO g QUANDO h ENTÃO i\n"
                   "- DADO j QUANDO k ENTÃO l\n",
                   base=um)
    assert any(s == "ALTO" and "declarou" in q for s, _, q, _ in engole), \
        f"C4 não acusou consolidação aterrissando menos que o bloco MUDA declara: {engole}"
    # DT-090: antes da consolidação, `para` é sempre o número antigo, então toda delta que
    # CRESCE o requisito satisfaz `para < dito`. Correto como profecia, falso como
    # diagnóstico — e é na fase analyze, com a delta ainda proposta, que o gate é
    # consultado para decidir se o implement começa. Medido nas deltas 086 e 087.
    profecia = rodar(um,
                     "### R9 — MUDA R1 (Δ000): a\n- DADO a QUANDO b ENTÃO c\n"
                     "- DADO d QUANDO e ENTÃO f\n- DADO g QUANDO h ENTÃO i\n"
                     "- DADO j QUANDO k ENTÃO l\n",
                     base=um, arquivada=False)
    assert profecia == [], f"C4 acusou delta ainda não consolidada que cresce o requisito: {profecia}"
    # e o encolhimento real segue acusado em delta proposta: ele não é profecia, mede o
    # TRUTH que a branch já mexeu contra o merge-base
    encolhe_proposta = rodar(um, "### R9 — MUDA R1 (Δ000): a\n- DADO a QUANDO b ENTÃO c\n",
                             base=tres, arquivada=False)
    assert any(s == "ALTO" and "cenário" in q for s, _, q, _ in encolhe_proposta), \
        f"C4 deixou passar encolhimento real por a delta ainda estar proposta: {encolhe_proposta}"
    fiel = rodar(quatro,
                 "### R9 — MUDA R1 (Δ000): a\n- DADO a QUANDO b ENTÃO c\n"
                 "- DADO d QUANDO e ENTÃO f\n- DADO g QUANDO h ENTÃO i\n"
                 "- DADO j QUANDO k ENTÃO l\n",
                 base=um)
    assert fiel == [], f"C4 acusou consolidação fiel ao bloco declarado: {fiel}"
    print("selftest C4: OK (git real; perda acusada em Rn, RF-NN e requisito anotado, "
          "MUDA/sufixo/anotação/partição liberados; encolhimento de cenário em MUDA acusado)")


def selftest_c5() -> None:
    """C5 com os três sinais: cada limiar estourado acusa BAIXO; partição é medida isolada."""
    import tempfile

    def rodar(truth: str, particoes: dict | None = None):
        """TRUTH.md (e partições opcionais em specs/truth/) num repo temporário; roda só o C5."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "specs").mkdir()
            (root / "specs" / "TRUTH.md").write_text(truth, encoding="utf-8")
            for nome, txt in (particoes or {}).items():
                (root / "specs" / "truth").mkdir(exist_ok=True)
                (root / "specs" / "truth" / f"{nome}.md").write_text(txt, encoding="utf-8")
            v: list = []
            c5_tamanho(root, v)
            return v

    # 0. repositório sem TRUTH.md (greenfield, pré-primeiro archive): o C5 se omite
    with tempfile.TemporaryDirectory() as d:
        vazio: list = []
        c5_tamanho(Path(d), vazio)
        assert vazio == [], f"C5 acusou repo sem TRUTH.md: {vazio}"

    # 1. linhas: o sinal histórico continua valendo, e o achado nomeia valor e limiar
    linhudo = rodar("x\n" * (TRUTH_LIMITE + 1))
    assert [q for s, _, q, _ in linhudo
            if s == "BAIXO" and f"{TRUTH_LIMITE + 1} linhas" in q and f"limiar {TRUTH_LIMITE}" in q], \
        f"C5 não acusou por linhas com valor e limiar: {linhudo}"
    assert rodar("x\n" * TRUTH_LIMITE) == [], "C5 acusou no limiar exato de linhas"

    # 2. tokens: arquivo curto em linhas e pesado em caracteres (soft-wrap — o caso do DT-035).
    # O valor esperado é literal de propósito: fixture derivada da constante mede a lógica e
    # é cega ao divisor — com ela, trocar CHARS_POR_TOKEN passaria despercebido.
    gordo = rodar("x" * 150_003 + "\n")
    assert [q for s, _, q, _ in gordo
            if s == "BAIXO" and "~50001 tokens" in q and f"limiar {TRUTH_LIMITE_TOKENS}" in q], \
        f"C5 não acusou 150.004 chars como ~50001 tokens — divisor ou mensagem mudou: {gordo}"
    assert not [q for s, _, q, _ in gordo if "linhas" in q], \
        f"C5 acusou linhas num arquivo de 1 linha: {gordo}"
    assert rodar("x" * (TRUTH_LIMITE_TOKENS * CHARS_POR_TOKEN)) == [], \
        "C5 acusou no limiar exato de tokens"

    # 3. domínios: uma seção ## além do limiar; subseção ### não é domínio
    dominioso = rodar("".join(f"## d{i}\n" for i in range(TRUTH_LIMITE_DOMINIOS + 1)))
    assert [q for s, _, q, _ in dominioso
            if s == "BAIXO" and f"{TRUTH_LIMITE_DOMINIOS + 1} domínios" in q
            and f"limiar {TRUTH_LIMITE_DOMINIOS}" in q], \
        f"C5 não acusou por domínios com valor e limiar: {dominioso}"
    no_limite = rodar("".join(f"## d{i}\n" for i in range(TRUTH_LIMITE_DOMINIOS))
                      + "### subseção não é domínio\n" * 5)
    assert no_limite == [], f"C5 contou subseção ### como domínio: {no_limite}"

    # 4. particionado: índice e cada partição contra os limiares, sem somar; domínios se omitem
    part = rodar("x\n" * (TRUTH_LIMITE + 1), particoes={"a": "x\n" * (TRUTH_LIMITE + 1)})
    assert [a for s, a, q, _ in part if a.endswith("TRUTH.md") and "linhas" in q], \
        f"C5 deixou de medir o índice quando há partições: {part}"
    assert [a for s, a, q, _ in part if "truth/a.md" in a and "linhas" in q], \
        f"C5 não acusou a partição estourada: {part}"

    part_tokens = rodar("- R1 (delta-000) — a\n",
                        particoes={"a": "x" * (TRUTH_LIMITE_TOKENS * CHARS_POR_TOKEN + CHARS_POR_TOKEN)})
    assert [a for s, a, q, _ in part_tokens if "truth/a.md" in a and "tokens" in q], \
        f"C5 não mediu tokens da partição: {part_tokens}"

    somado = rodar("- R1 (delta-000) — a\n",
                   particoes={f"d{i}": "x\n" * 400 for i in range(3)})
    assert somado == [], f"C5 somou as partições em vez de medir cada uma: {somado}"

    ja_particionado = rodar("".join(f"## d{i}\n" for i in range(TRUTH_LIMITE_DOMINIOS + 5)),
                            particoes={"a": "### R1 (delta-000) — a\n"})
    assert not [q for _, _, q, _ in ja_particionado if "domínios" in q], \
        f"C5 pediu particionamento a um TRUTH já particionado: {ja_particionado}"

    print("selftest C5: OK (linhas, tokens, domínios; partição medida isolada)")


def selftest_c7() -> None:
    """C7 com git real: artefato acima do limiar acusa BAIXO; abaixo, liberado."""
    import tempfile

    def rodar(n_linhas: int):
        """Repo com base na main; delta com `n_linhas` de artefato numa branch; roda o C7."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)

            def git(*args):
                subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)

            git("init", "-q", "-b", "main")
            git("config", "user.email", "selftest@sdd")
            git("config", "user.name", "selftest")
            (root / "specs").mkdir()
            (root / "specs" / "TRUTH.md").write_text("- R1 (delta-000) — a\n", encoding="utf-8")
            git("add", "-A")
            git("commit", "-qm", "base")
            git("checkout", "-qb", "feat/009-x")
            delta = root / "specs" / "009-x"
            delta.mkdir()
            (delta / "spec.md").write_text("linha de artefato\n" * n_linhas, encoding="utf-8")
            git("add", "-A")
            git("commit", "-qm", "artefatos")
            v: list = []
            c7_split(root, delta, v)
            return v

    try:
        subprocess.run(["git", "--version"], check=True, capture_output=True)
    except (FileNotFoundError, OSError):
        print("selftest C7: PULADO (git indisponível)")
        return
    # git presente: daqui em diante toda falha é ruidosa — PULADO não mascara regressão
    grande = rodar(PR_LIMITE + 1)
    assert any(s == "BAIXO" and "linhas adicionadas" in q for s, _, q, _ in grande), \
        f"C7 não acusou artefato acima do limiar: {grande}"
    pequeno = rodar(10)
    assert pequeno == [], f"C7 acusou artefato abaixo do limiar: {pequeno}"
    print("selftest C7: OK (git real; acima do limiar acusado, abaixo liberado)")


def selftest_c13() -> None:
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        arq = root / "specs" / "_archive" / "001-x"
        arq.mkdir(parents=True)
        (root / "DEBT.md").write_text("x", encoding="utf-8")
        (arq / "spec.md").write_text(
            "# delta-001\n"
            "[profundidade certa](../../../DEBT.md)\n"
            "[profundidade quebrada pelo move](../../DEBT.md)\n"
            "[atalho do GitHub, fora do recorte](../../issues/9)\n"
            "[externo](https://exemplo.dev)\n", encoding="utf-8")
        v: list = []
        c13_links_archive(root, v)
        assert len(v) == 1, f"C13 deveria acusar só o link morto: {v}"
        assert v[0][0] == "ALTO", f"C13 não é CRÍTICO (exclusivo do C4): {v}"
        assert "../../DEBT.md" in v[0][2], f"C13 deve nomear o alvo morto: {v}"
        assert "spec.md:3" in v[0][1], f"C13 deve nomear arquivo e linha: {v}"
    with tempfile.TemporaryDirectory() as d:
        v = []
        c13_links_archive(Path(d), v)
        assert v == [], f"C13 sem specs/_archive/ deve se omitir: {v}"
    print("selftest C13: OK (morto acusado com linha, profundidade certa liberada, "
          "atalho ignorado, projeto sem archive omitido)")


def selftest_c14() -> None:
    """C14: marketplace é ALTO, clone raso é BAIXO, checkout próprio é silêncio."""
    import tempfile

    # Fixture em tempdir, nunca com caminho de home escrito à mão: o RNF5 reprova caminho
    # absoluto de máquina em artefato publicado, e pegou esta linha na primeira tentativa.
    with tempfile.TemporaryDirectory() as d:
        falso = Path(d) / ".claude" / "plugins" / "marketplaces" / "deltaspec"
        falso.mkdir(parents=True)
        marketplace: list = []
        c14_checkout(falso, marketplace)
        assert any(s == "ALTO" for s, *_ in marketplace), \
            f"C14 não acusou delta no checkout do marketplace: {marketplace}"
        assert not any(s == "CRÍTICO" for s, *_ in marketplace), \
            f"C14 é ALTO, não CRÍTICO (CRÍTICO é exclusivo do C4): {marketplace}"
        # sob o marketplace o check retorna cedo: não vale gastar git perguntando profundidade
        assert len(marketplace) == 1, f"C14 deveria parar no achado do marketplace: {marketplace}"

    try:
        subprocess.run(["git", "--version"], check=True, capture_output=True)
    except (FileNotFoundError, OSError):
        print("selftest C14: PARCIAL (git indisponível; só o caso do marketplace rodou)")
        return

    with tempfile.TemporaryDirectory() as d:
        origem, raso = Path(d) / "origem", Path(d) / "raso"

        def git(*args, cwd=None):
            subprocess.run(["git", *(["-C", str(cwd)] if cwd else []), *args],
                           check=True, capture_output=True)

        origem.mkdir()
        git("init", "-q", "-b", "main", cwd=origem)
        git("config", "user.email", "selftest@sdd", cwd=origem)
        git("config", "user.name", "selftest", cwd=origem)
        (origem / "a.txt").write_text("1\n", encoding="utf-8")
        git("add", "-A", cwd=origem)
        git("commit", "-qm", "um", cwd=origem)
        (origem / "a.txt").write_text("2\n", encoding="utf-8")
        git("commit", "-qam", "dois", cwd=origem)

        proprio: list = []
        c14_checkout(origem, proprio)
        assert proprio == [], f"C14 acusou checkout próprio e completo: {proprio}"

        # o CI roda em actions/checkout sem fetch-depth, ou seja, raso: se raso fosse ALTO,
        # o gate reprovaria o próprio CI no dia em que ele rodasse sobre uma delta
        git("clone", "-q", "--depth", "1", f"file://{origem}", str(raso))
        v_raso: list = []
        c14_checkout(raso, v_raso)
        assert any(s == "BAIXO" and "raso" in q for s, _, q, _ in v_raso), \
            f"C14 não reportou clone raso: {v_raso}"
        assert not any(s in ("ALTO", "CRÍTICO") for s, *_ in v_raso), \
            f"clone raso é BAIXO informativo, nunca reprovador: {v_raso}"
    print("selftest C14: OK (marketplace ALTO e curto-circuitado, clone raso BAIXO, "
          "checkout próprio livre)")


def selftest_numero_delta_livre() -> None:
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        assert numero_delta_livre(root) == 1, "repo vazio — primeira delta é 001"

        (root / "specs" / "_archive" / "003-x").mkdir(parents=True)
        (root / "specs" / "005-y").mkdir(parents=True)
        assert numero_delta_livre(root) == 6, "só pastas: max(3, 5) + 1"

        # DT-036 (_pmo, 2026-08-12): delta consumida por merge sem specs/NNN-*/, só citada
        # no TRUTH.md — pasta sozinha ficaria cega a ela e reabriria o mesmo número.
        (root / "specs" / "TRUTH.md").write_text(
            "- R1 (delta-005; nota: delta-009) — x\n", encoding="utf-8")
        assert numero_delta_livre(root) == 10, "citação (delta-009) no TRUTH sem pasta própria"

        # Menção solta em prosa (sem parênteses) — como o CHANGELOG cita merge sem pasta.
        (root / "CHANGELOG.md").write_text(
            "A delta-012, que entrou por merge sem specs/012-*/, foi consolidada no R9.\n",
            encoding="utf-8")
        assert numero_delta_livre(root) == 13, "menção solta 'delta-012' no CHANGELOG sem pasta"

        # TRUTH particionado (specs/truth/<dominio>.md) — não pode ficar cego por ler só o índice.
        (root / "specs" / "truth").mkdir(parents=True)
        (root / "specs" / "truth" / "auth.md").write_text("- R2 (delta-020) — y\n", encoding="utf-8")
        assert numero_delta_livre(root) == 21, "TRUTH particionado também conta"

        # (ΔNNN) legado, com zero à esquerda.
        (root / "specs" / "truth" / "auth.md").write_text("- R2 (Δ007) — y\n", encoding="utf-8")
        assert numero_delta_livre(root) == 13, "voltou a valer o CHANGELOG (12) — Δ007 é menor"

        # DT-039 (_pmo, 2026-08-13): citação de delta de OUTRO repo no CHANGELOG (o quita
        # DT-031 citava "deltaspec v1.24.1, delta-052") não pode consumir numeração local.
        (root / "CHANGELOG.md").write_text(
            "A delta-012 foi consolidada no R9.\n"
            "Corrigido no framework (deltaspec v1.24.1, delta-052) e recebido por update.\n",
            encoding="utf-8")
        assert numero_delta_livre(root) == 13, "delta-052 estrangeira salta a sequência e é ignorada"

        # A tolerância acompanha a sequência: menções em cadeia contígua seguem valendo.
        (root / "CHANGELOG.md").write_text(
            "A delta-012 e a delta-019 entraram por merge sem pasta.\n", encoding="utf-8")
        assert numero_delta_livre(root) == 20, "cadeia contígua 12→19 dentro do salto continua contando"

    # A2 do DT-071: o parse das refs é puro, e é o que o selftest exercita — o CI não tem
    # rede, e testar `ls-remote` de verdade acoplaria o gate a um remote existir.
    saida = ("abc123\trefs/heads/main\n"
             "def456\trefs/heads/feat/082-gates-do-ciclo\n"
             "789abc\trefs/heads/docs/073-modelo-dados\n"
             "000fff\trefs/heads/fix/sem-numero\n"
             "111222\trefs/heads/renovacao-2026\n")
    assert numeros_de_refs(saida) == {82, 73}, numeros_de_refs(saida)
    assert numeros_de_refs("") == set(), "remoto vazio não inventa número"
    # `refs/remotes/origin/feat/082-x` é a forma do fallback: o prefixo do remote entra
    # antes do tipo, e o NNN continua sendo o primeiro segmento numerado
    assert numeros_de_refs("refs/remotes/origin/feat/091-x\n") == {91}, \
        "fallback em refs/remotes precisa casar a mesma forma"
    print("selftest número livre: OK (pasta só, citação sem pasta no TRUTH, menção solta no "
          "CHANGELOG, TRUTH particionado, notação Δ legada, citação estrangeira ignorada, "
          "NNN de branch remota)")


if __name__ == "__main__":
    main()
