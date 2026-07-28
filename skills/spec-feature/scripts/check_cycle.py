#!/usr/bin/env python3
"""Gate determinístico do ciclo sdd-iuri — checa o que é mecânico numa delta spec.
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

Uso: check_cycle.py [DELTA_DIR]   (default: a única delta não arquivada em ./specs)
     check_cycle.py --selftest
Exit 0 = sem ALTO/CRÍTICO · 1 = corrigir antes de seguir · 2 = erro de uso.
"""
import re
import subprocess
import sys
from pathlib import Path

TRUTH_LIMITE = 800
PR_LIMITE = 500  # espelho da regra canônica de tamanho de PR (dono: canonical-rules.md; sancionado no deps.toml)
ORDEM = {"CRÍTICO": 0, "ALTO": 1, "MÉDIO": 2, "BAIXO": 3}

# Duas notações de ID aceitas: Rn/RNFn (default do framework) e RF-NN/RNF-NN com
# numeração hierárquica opcional (RF-01.1). A segunda existe porque projeto com
# corpus legado cita o ID em massa — renomear centenas de citações para chegar ao
# mesmo lugar é churn, e o tabela_cliente.py do doc-entregavel já exige RF-NN.
REQ_ID = r"R(?:NF|F)?-?\d+(?:\.\d+)*"

CABECALHO = re.compile(rf"^###\s+({REQ_ID})\s*[—-]\s*(ADICIONA|MUDA|REMOVE)\b(.*)$")
ALVO = re.compile(rf"\b({REQ_ID})\s*\((?:Δ\s*|delta-)\d+\)")  # aceita (ΔNNN) legado e (delta-NNN)
TAREFA = re.compile(r"^\s*-\s*\[[ xX]\]\s*(T\d+)")
CASO = re.compile(r"^\s*-\s*\[[ xX]\]\s*(CT\d+)")  # caso de teste do test-plan.md (delta-015)
SECAO_RISCOS = re.compile(r"^##\s+Depend[êe]ncias e riscos\s*$(.*?)(?=^##\s|\Z)", re.M | re.S)
PENDENCIA_ABERTA = re.compile(r"^\s*-\s*\[ \]", re.M)
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
        bugfix = (campo(cab, "Tipo") or "").lower() == "bugfix" and not (delta / "tasks.md").is_file()
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


def checar(root: Path, delta: Path) -> list:
    spec, tasks = delta / "spec.md", delta / "tasks.md"
    if not spec.is_file():
        die(f"spec.md não encontrado em {delta}")
    spec_txt = spec.read_text(encoding="utf-8")
    bs = blocos(spec_txt)
    bugfix = (campo(cabecalho(spec_txt), "Tipo") or "").lower() == "bugfix"
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
        c2_cobertura(bs, tasks.read_text(encoding="utf-8") if tasks.is_file() else "", v)
    c3_estado(root, v)
    c4_archive(root, bs, v)
    c5_tamanho(root, v)
    c6_pendencias(root, v)
    c7_split(root, delta, v)
    c8_testplan(delta, bs, spec_txt, v)
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
    print("\nParcial: cobre C1–C8; os checks 3 e 5 do analyze.md (scope creep, regra canônica) são juízo humano e não rodaram.")
    sevs = {f[0] for f in v}
    veredito = "BLOQUEADO" if "CRÍTICO" in sevs else "LIBERADO COM RESSALVAS" if v else "LIBERADO"
    print(f"\n**Veredito:** {veredito}")
    sys.exit(1 if sevs & {"CRÍTICO", "ALTO"} else 0)


def selftest() -> None:
    import tempfile

    limpa_spec = """# delta-001 — x
Estado: proposta · Data: 2026-01-01 · Branch: feat/001-x

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

    print("selftest: OK (3 fixtures + C8 + bugfix, defeitos detectados nos dois lados da cobertura)")
    selftest_c4()
    selftest_c7()


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
