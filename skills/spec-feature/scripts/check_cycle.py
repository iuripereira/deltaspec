#!/usr/bin/env python3
"""Gate determinístico do ciclo deltaspec — checa o que é mecânico numa delta spec.
Saída parcial: os checks 3 e 5 do analyze (scope creep, regra canônica) continuam humanos.

Automatiza os checks 1 e 2 do analyze (references/analyze.md), o estado ×
localização da delta, a verificação obrigatória do archive (references/cycle.md,
regra 6), o limiar de particionamento do TRUTH.md, a pendência roteada
(cycle.md, regra 7) e a medição do split de PR (cycle.md, split condicional). Os
checks 3 e 5 do analyze (scope creep spec×plan, violação de regra canônica)
continuam com o modelo — são juízo, não regex.

  C1  aceite verificável — Rn com DADO/QUANDO/ENTÃO; RNFn com Métrica + Verificação
  C2  cobertura spec ↔ tasks — órfãos nos dois sentidos; task sem verificação
  C3  estado × localização — delta 'aplicada' fora de _archive/ é trabalho inacabado
  C4  archive sem perda — requisito sumido do TRUTH.md sem MUDA/REMOVE que o declare
  C5  tamanho do TRUTH.md — acima de 800 linhas, particionar em truth/<dominio>.md
  C6  pendência roteada — '- [ ]' em "Dependências e riscos" de delta arquivada
  C7  split de PR — artefatos da delta acima do limiar de PR recomendam split (BAIXO)
  C8  cobertura do plano de testes — Rn/RNFn sem caso; ausência sem dispensa (delta-015)
  C9  grafo de tasks — `(dep: Tn)` inexistente ou ciclo entre tasks (delta-016)
  C10 convergência mínima — task '- [ ]' remanescente em delta arquivada (delta-016)
  C11 doc-profile — núcleo ausente, YAML inválido, obrigatório sem justificativa (delta-026)
  C12 trilha do clarify — perfil completo sem canal humano declarado (delta-026)

Uso: check_cycle.py [DELTA_DIR]   (default: a única delta não arquivada em ./specs)
     check_cycle.py --selftest
Exit 0 = sem ALTO/CRÍTICO · 1 = corrigir antes de seguir · 2 = erro de uso.
"""
import graphlib
import re
import subprocess
import sys
from pathlib import Path

try:
    import yaml  # única dependência externa admitida nos gates (ADR-0023)
except ModuleNotFoundError:  # mensagem acionável em vez de traceback cru (review da delta-026)
    sys.exit("ERRO: PyYAML ausente — rode 'pip install pyyaml' (ADR-0023)")

TRUTH_LIMITE = 800
PR_LIMITE = 500  # espelho da regra canônica de tamanho de PR (dono: canonical-rules.md; sancionado no deps.toml)
ORDEM = {"CRÍTICO": 0, "ALTO": 1, "MÉDIO": 2, "BAIXO": 3}

# C11 (delta-026): núcleo do doc-profile, medido nos 7 perfis reais em 2026-08-02. A cauda
# (explicativos, prototipo, apresentacao, ...) é opcional por desenho: categoria que uma delta
# acrescenta ao template nunca propaga retroativamente aos projetos já inicializados.
NUCLEO_TOPO = ("version", "decisao", "publico", "artefatos")
NUCLEO_ARTEFATOS = ("arquitetura", "modelo-dados", "fluxos", "casos-de-uso")
# Perfil mínimo válido — fixture compartilhada pelos selftests (uma fonte, não uma cópia por teste).
PERFIL_NUCLEO = (
    'version: 1\n'
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
ALVO = re.compile(rf"\b({REQ_ID})\s*\((?:Δ\s*|delta-)\d+\)")  # aceita (ΔNNN) legado e (delta-NNN)
TAREFA = re.compile(r"^\s*-\s*\[[ xX]\]\s*(T\d+)")
CASO = re.compile(r"^\s*-\s*\[[ xX]\]\s*(CT\d+)")  # caso de teste do test-plan.md (delta-015)
DEP = re.compile(r"\(dep:\s*([^)]*)\)")  # arestas de bloqueio do tasks.md (delta-016)
SECAO_RISCOS = re.compile(r"^##\s+Depend[êe]ncias e riscos\s*$(.*?)(?=^##\s|\Z)", re.M | re.S)
PENDENCIA_ABERTA = re.compile(r"^\s*-\s*\[ \]", re.M)
TAREFA_ABERTA = re.compile(r"^\s*-\s*\[ \]\s*T\d+", re.M)  # task não concluída (C10, delta-016)
# C12 (delta-026): trilha do clarify. Âncora de início de linha — a mesma sintaxe citada em
# prosa é texto, não campo (lições de 2026-07-28 e 2026-08-01, três falsos positivos).
CLARIFY = re.compile(r"^Clarify:\s*(entrevistado|auto-avaliado)\b", re.M)
# ponytail: um requisito por bloco ###; spec que fuja do template não é parseada


def die(msg: str) -> None:
    print(f"ERRO: {msg}")
    sys.exit(2)


def campo(texto: str, nome: str):
    """Valor de 'nome: valor' até '·' ou fim de linha. None se ausente ou placeholder."""
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


def cobre_alvos(linha: str, ids_spec: set, onde: str, cobertos: set, v: list, ignora: tuple = ()):
    """Núcleo comum do C2 (tasks) e do C8 (test-plan): parseia 'cobre:', acumula os
    alvos em `cobertos` e acusa referência morta (ALTO). Retorna o valor bruto de
    'cobre:' (None se ausente) para o check de completude de cada chamador."""
    cobre = campo(linha, "cobre")
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


def c1_aceite(bs, v: list) -> None:
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
    achou_task = False
    for line in tasks_txt.splitlines():
        m = TAREFA.match(line)
        if not m:
            continue
        achou_task, tid = True, m.group(1)
        if cobre_alvos(line, ids_spec, f"tasks.md {tid}", cobertos, v, ignora=("infra",)) is None:
            v.append(("MÉDIO", f"tasks.md {tid}", "task sem 'cobre:'", "mapear a um Rn/RNFn ou declarar 'cobre: infra'"))
        if not campo(line, r"verifica[çc][ãa]o"):
            v.append(("ALTO", f"tasks.md {tid}", "task sem 'verificação:'", "declarar comando ou critério de pronto"))
    if not achou_task:
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


def base_c4(root: Path) -> tuple[str, bool]:
    """Merge-base da branch com a main → (ref, True); sem base → ('HEAD', False)."""
    for ref in ("origin/main", "main"):
        r = subprocess.run(["git", "-C", str(root), "merge-base", "HEAD", ref],
                           capture_output=True, text=True)
        if r.returncode == 0:
            return r.stdout.strip(), True
    return "HEAD", False


def c4_archive(root: Path, bs, v: list) -> None:
    """Requisito removido do TRUTH.md tem que estar declarado como alvo de MUDA/REMOVE."""
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


def c5_tamanho(root: Path, v: list) -> None:
    truth = root / "specs" / "TRUTH.md"
    if truth.is_file():
        n = len(truth.read_text(encoding="utf-8").splitlines())
        if n > TRUTH_LIMITE:
            v.append(("BAIXO", "specs/TRUTH.md", f"{n} linhas (limiar {TRUTH_LIMITE})", "particionar em truth/<dominio>.md e virar índice"))


def c6_pendencias(root: Path, v: list) -> None:
    """Pendência aberta (`- [ ]` em riscos) não sobrevive ao archive sem rotear pro DEBT.md."""
    for p in sorted((root / "specs" / "_archive").glob("*/spec.md")):
        m = SECAO_RISCOS.search(p.read_text(encoding="utf-8"))
        if not m:
            continue
        n = len(PENDENCIA_ABERTA.findall(m.group(1)))
        if n:
            v.append(("ALTO", str(p.relative_to(root)),
                      f"{n} pendência(s) aberta(s) '- [ ]' em delta arquivada",
                      "registrar como DT-NNN no DEBT.md (natureza: pendência) e marcar '- [x]'"))


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
    for line in tp.read_text(encoding="utf-8").splitlines():
        m = CASO.match(line)
        if not m:
            continue
        cid = m.group(1)
        cobre = cobre_alvos(line, ids_spec, f"test-plan.md {cid}", cobertos, v)
        if not cobre or not campo(line, "tipo") or not campo(line, r"verifica[çc][ãa]o"):
            v.append(("MÉDIO", f"test-plan.md {cid}", "caso sem 'cobre:'/'tipo:'/'verificação:' completos", "cobre: Rn · tipo: auto|manual · verificação: comando ou passos"))
    for rid in sorted(ids_spec - cobertos):
        v.append(("ALTO", f"spec.md {rid}", "requisito sem caso no test-plan.md", f"adicionar caso com 'cobre: {rid}' (manual roteirizado conta)"))


def c9_grafo(tasks_txt: str, v: list) -> None:
    """Arestas de bloqueio (delta-016): `(dep: Tn[, Tm])` por task; task sem `dep:` é
    livre. Dep inexistente ou ciclo → ALTO. Arquivo sem nenhum `dep:` → cadeia linear
    implícita pela ordem (retrocompatível, R1)."""
    arestas: dict[str, list[str]] = {}
    for line in tasks_txt.splitlines():
        m = TAREFA.match(line)
        if not m:
            continue
        resto = line[m.end():].lstrip()
        if m.group(1) in arestas:
            v.append(("ALTO", f"tasks.md {m.group(1)}", "ID de task duplicado no arquivo", "renumerar — ID duplicado engole aresta do grafo (C9)"))
            continue
        d = DEP.match(resto)  # só a aresta colada ao ID é aresta — "(dep: Tn)" em prosa não conta (achado do dogfood da delta-016)
        arestas[m.group(1)] = [a.strip() for a in d.group(1).split(",") if a.strip()] if d else []
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
        n = len(TAREFA_ABERTA.findall(p.read_text(encoding="utf-8")))
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
    c1_aceite(bs, v)
    if not (bugfix and not tasks.is_file()):  # bugfix sem tasks.md é válido — tasks é sob demanda (delta-015)
        tasks_txt = tasks.read_text(encoding="utf-8") if tasks.is_file() else ""
        c2_cobertura(bs, tasks_txt, v)
        c9_grafo(tasks_txt, v)
    c3_estado(root, v)
    c4_archive(root, bs, v)
    c5_tamanho(root, v)
    c6_pendencias(root, v)
    c10_convergencia(root, v)
    c7_split(root, delta, v)
    c8_testplan(delta, bs, spec_txt, v)
    c11_perfil(root, v)
    c12_clarify(spec_txt, v)
    return v


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
    print("\nParcial: cobre C1–C12; os checks 3 e 5 do analyze.md (scope creep, regra canônica) são juízo humano e não rodaram.")
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
- [x] pendência já roteada para o DEBT.md (DT-NNN)
"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        arq = root / "specs" / "_archive" / "001-x"
        arq.mkdir(parents=True)
        (arq / "spec.md").write_text(arquivada_pendente, encoding="utf-8")
        v: list = []
        c6_pendencias(root, v)
        assert len(v) == 1 and v[0][0] == "ALTO" and "1 pendência" in v[0][2], f"C6: {v}"
        assert "DEBT.md" in v[0][3], f"C6 deve rotear para o DEBT.md (delta-007): {v}"

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
    selftest_c7()
    selftest_c11()
    selftest_c12()


def selftest_c11() -> None:
    """C11: núcleo exigido, cauda tolerada, YAML inválido reportado sem estourar."""
    import tempfile

    nucleo = PERFIL_NUCLEO
    casos = [
        (nucleo, 0, "perfil de núcleo íntegro não acusa nada"),
        (nucleo + "  explicativos: { obrigatorio: false }\n", 0, "cauda presente é aceita"),
        (nucleo + "  prototipo: { obrigatorio: false }\n  apresentacao: { obrigatorio: false }\n", 0,
         "cauda inteira presente é aceita"),
        (nucleo.replace("version: 1\n", ""), 1, "chave de núcleo ausente acusa ALTO"),
        (nucleo.replace("version: 1", "version:"), 1, "chave de núcleo declarada sem valor acusa ALTO"),
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
        ("version: 1\n  isto: : não é yaml\n", 1, "YAML inválido acusa ALTO, sem exceção"),
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

    def rodar(resultante: str, spec: str = "", particoes: dict | None = None, base: str | None = None):
        """TRUTH base legado (Δ000) → estado `resultante` num commit; roda o C4 sobre `spec`.
        `particoes`: {nome: conteúdo} gravado em specs/truth/<nome>.md no estado resultante."""
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
            git("commit", "-qm", "consolida")  # commitado: a antiga janela cega do diff HEAD
            v: list = []
            c4_archive(root, blocos(spec), v)
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
    # particionamento (C5): TRUTH.md vira índice e os requisitos passam a viver em
    # specs/truth/<dominio>.md — ler só o índice acusaria perda que não houve
    particiona = rodar("# Índice\n- ver truth/dominio.md\n",
                       particoes={"dominio": "- R1 (Δ000) — a\n- R2 (Δ000) — b\n"})
    assert particiona == [], f"C4 acusou particionamento do TRUTH como perda: {particiona}"
    # notação RF-NN/RNF-NN (corpus legado) tem o mesmo tratamento que Rn/RNFn
    rf_perdido = rodar("- RF-02 (delta-000) — b\n", base="- RF-01 (delta-000) — a\n- RF-02 (delta-000) — b\n")
    assert any(s == "CRÍTICO" and "RF-01" in q for s, _, q, _ in rf_perdido), \
        f"C4 não acusou perda na notação RF-NN: {rf_perdido}"
    rf_declara = rodar("- RF-02 (delta-000) — b\n",
                       "### RF-09 — MUDA RF-01 (delta-000): a\n- DADO a QUANDO b ENTÃO c\n",
                       base="- RF-01 (delta-000) — a\n- RF-02 (delta-000) — b\n")
    assert rf_declara == [], f"C4 acusou falso positivo com MUDA declarado em RF-NN: {rf_declara}"
    print("selftest C4: OK (git real; perda acusada em Rn e RF-NN, MUDA/sufixo/partição liberados)")


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


if __name__ == "__main__":
    main()
