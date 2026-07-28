<!-- resumo sdd-iuri · ≤15 linhas · única parte do plano lida pelo analyze e pelo humano -->
**Objetivo:** implementar a delta-016 — arestas `dep:` no tasks.md com C9/C10 no gate, execução paralela por worktree, vocabulário de harness, trilha de auditoria e graphify como 4º motor opcional. **Cobre:** R1, R2 (MUDA R12), R3, R4, R5, R6 (da delta-016) **Decisões duráveis → ADRs:** ADR-0014 (gravada no clarify) **Riscos assumidos:** graphify entra sem teste real (pin definido na primeira adoção; linha de política honesta "não testada"); higiene sancionada nos `tasks.md` de 6 deltas arquivadas (checkboxes de trabalho comprovadamente concluído — exigência do C10); TDD dispensado nas tasks só-documentação (T3–T6), justificativa por task abaixo.

# delta-016 (harness) — Plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** grafo de bloqueio explícito no `tasks.md` validado pelo gate (C9), archive sem trabalho aberto (C10), paralelização por worktree documentada no ciclo, vocabulário de harness canônico, trilha de auditoria e adapter do graphify.

**Architecture:** tudo dentro do padrão vigente — checks novos como funções puras em `check_cycle.py` (TDD via `--selftest`, fixtures co-localizadas), regras de processo em `references/cycle.md`, contratos de motor em `references/adapters.md`, vocabulário novo em reference próprio (`references/harness.md`, fonte canônica única).

**Tech Stack:** Python 3.11+ stdlib pura (`re`, `pathlib`) · Markdown PT-BR · sem dependência nova.

## Global Constraints

- Idioma PT-BR em identificadores, comentários, docs e commits (padrão vigente de `check_cycle.py`).
- Stdlib pura — zero pacote externo (regra canônica do CLAUDE.md).
- Zero valor mágico: C9/C10 não introduzem limiar numérico novo — nada a adicionar no `deps.toml`.
- Fonte canônica única: regra vive num arquivo; os demais linkam (harness.md é o dono novo dos termos).
- Commits Conventional: `feat(016-harness): <descrição>` (ou `docs`/`fix`), rodapé `Co-Authored-By: Claude <noreply@anthropic.com>`.
- Fim de cada task = commit. Não editar `specs/_archive/**` fora da higiene sancionada da T2.
- Scripts referenciados por `${CLAUDE_PLUGIN_ROOT}` — nunca caminho absoluto de máquina.

---

### Task 1: C9 — grafo de tasks no `check_cycle.py` (TDD)

**Files:**
- Modify: `skills/spec-feature/scripts/check_cycle.py`

**Interfaces:**
- Consumes: `TAREFA` (regex existente, linha 42), `checar()` (linha 279), padrão de achado `(severidade, onde, o_que, acao)`.
- Produces: regex módulo `DEP`, função `c9_grafo(tasks_txt: str, v: list) -> None` — a T4 cita "C9 grafo de tasks" nos espelhos.

- [ ] **Step 1: Escrever as fixtures que falham (selftest)**

Em `selftest()`, logo após o bloco do C8 (após a fixture `comentado`, ~linha 447), inserir:

```python
    # C9 — grafo de tasks (delta-016): dep válido passa; dep morta e ciclo acusam ALTO
    dep_ok = limpa_tasks.replace("- [ ] T2 — cache", "- [ ] T2 (dep: T1) — cache")
    assert rodar(limpa_spec, dep_ok, limpa_testplan) == [], "C9: dep válido deveria passar sem achados"
    dep_morta = rodar(limpa_spec, limpa_tasks.replace("- [ ] T2 — cache", "- [ ] T2 (dep: T9) — cache"), limpa_testplan)
    assert any(s == "ALTO" and "T9" in q for s, _, q, _ in dep_morta), f"C9 dep inexistente: {dep_morta}"
    ciclo_tasks = ("- [ ] T1 (dep: T2) — form · arquivos: a.py · cobre: R1 · verificação: pytest\n"
                   "- [ ] T2 (dep: T1) — cache · arquivos: b.py · cobre: RNF1 · verificação: k6\n")
    com_ciclo = rodar(limpa_spec, ciclo_tasks, limpa_testplan)
    assert any(s == "ALTO" and "ciclo" in q for s, _, q, _ in com_ciclo), f"C9 ciclo: {com_ciclo}"
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python3 skills/spec-feature/scripts/check_cycle.py --selftest`
Expected: `AssertionError` na fixture `dep_morta` (o gate atual ignora `dep:`).

- [ ] **Step 3: Implementar o C9**

Regex ao lado de `CASO` (~linha 43):

```python
DEP = re.compile(r"\(dep:\s*([^)]*)\)")  # arestas de bloqueio do tasks.md (delta-016)
```

Função após `c8_testplan` (~linha 277):

```python
def c9_grafo(tasks_txt: str, v: list) -> None:
    """Arestas de bloqueio (delta-016): `(dep: Tn[, Tm])` por task; task sem `dep:` é
    livre. Dep inexistente ou ciclo → ALTO. Arquivo sem nenhum `dep:` → cadeia linear
    implícita pela ordem (retrocompatível, R1)."""
    arestas: dict[str, list[str]] = {}
    for line in tasks_txt.splitlines():
        m = TAREFA.match(line)
        if not m:
            continue
        d = DEP.search(line)
        arestas[m.group(1)] = [a.strip() for a in d.group(1).split(",") if a.strip()] if d else []
    if not any(arestas.values()):
        return  # nenhum dep: no arquivo — cadeia linear implícita
    for tid, deps in arestas.items():
        for dep in deps:
            if dep not in arestas:
                v.append(("ALTO", f"tasks.md {tid}", f"dep '{dep}' cita task inexistente", "corrigir a aresta ou criar a task (C9)"))
    # Kahn: task que sobra com grau > 0 está num ciclo (dep morta já acusada não conta)
    grau = {t: sum(1 for d in deps if d in arestas) for t, deps in arestas.items()}
    dependentes: dict[str, list[str]] = {t: [] for t in arestas}
    for tid, deps in arestas.items():
        for dep in deps:
            if dep in dependentes:
                dependentes[dep].append(tid)
    fila = [t for t, g in grau.items() if g == 0]
    while fila:
        t = fila.pop()
        for depte in dependentes[t]:
            grau[depte] -= 1
            if grau[depte] == 0:
                fila.append(depte)
    ciclo = sorted(t for t, g in grau.items() if g > 0)
    if ciclo:
        v.append(("ALTO", "tasks.md", f"ciclo de dependências envolvendo {', '.join(ciclo)}", "remover a aresta que fecha o ciclo (C9)"))
```

Registrar em `checar()` dentro do guard existente do C2 (linhas 299–300), passando o mesmo texto:

```python
    if not (bugfix and not tasks.is_file()):  # bugfix sem tasks.md é válido — tasks é sob demanda (delta-015)
        tasks_txt = tasks.read_text(encoding="utf-8") if tasks.is_file() else ""
        c2_cobertura(bs, tasks_txt, v)
        c9_grafo(tasks_txt, v)
```

Docstring do módulo: adicionar após a linha do C8 (linha 19):

```
  C9  grafo de tasks — `(dep: Tn)` inexistente ou ciclo entre tasks (delta-016)
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python3 skills/spec-feature/scripts/check_cycle.py --selftest`
Expected: `selftest: OK ...` (as três fixtures novas passam; nenhuma antiga quebra).

- [ ] **Step 5: Commit**

```bash
git add skills/spec-feature/scripts/check_cycle.py
git commit -m "feat(016-harness): C9 — grafo de tasks no gate (dep inexistente e ciclo, TDD)"
```

---

### Task 2: C10 — convergência mínima no archive (TDD) + higiene dos arquivados

**Files:**
- Modify: `skills/spec-feature/scripts/check_cycle.py`
- Modify: `specs/_archive/{001-plugin,002-gates,009-split-pr-mecanico,010-handoff-renomeia-state,012-descoberta,015-fluxo}/tasks.md`

**Interfaces:**
- Consumes: padrão de varredura do `c6_pendencias` (linha 208).
- Produces: regex módulo `TAREFA_ABERTA`, função `c10_convergencia(root: Path, v: list) -> None`.

- [ ] **Step 1: Escrever a fixture que falha**

Em `selftest()`, após as fixtures do C9 (Task 1), inserir:

```python
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
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python3 skills/spec-feature/scripts/check_cycle.py --selftest`
Expected: `NameError: c10_convergencia`.

- [ ] **Step 3: Implementar o C10**

Regex ao lado de `PENDENCIA_ABERTA` (~linha 45):

```python
TAREFA_ABERTA = re.compile(r"^\s*-\s*\[ \]\s*T\d+", re.M)  # task não concluída (C10, delta-016)
```

Função após `c9_grafo`:

```python
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
```

Registrar em `checar()` logo após `c6_pendencias(root, v)` (linha 304): `c10_convergencia(root, v)`.

Docstring do módulo, após a linha do C9:

```
  C10 convergência mínima — task '- [ ]' remanescente em delta arquivada (delta-016)
```

Linha do rodapé de saída em `main()` (linha 339): trocar `cobre C1–C8` por `cobre C1–C10`.

- [ ] **Step 4: Rodar e ver passar**

Run: `python3 skills/spec-feature/scripts/check_cycle.py --selftest`
Expected: `selftest: OK ...`.

- [ ] **Step 5: Higiene sancionada dos 6 arquivados**

O trabalho dessas deltas está comprovadamente concluído (PRs mergeados, deltas arquivadas, TRUTH consolidado) — só o checkbox ficou para trás. Sem esta correção o C10 acusaria 6 falsos históricos em toda execução.

```bash
sed -i 's/^- \[ \] T/- [x] T/' \
  specs/_archive/001-plugin/tasks.md specs/_archive/002-gates/tasks.md \
  specs/_archive/009-split-pr-mecanico/tasks.md specs/_archive/010-handoff-renomeia-state/tasks.md \
  specs/_archive/012-descoberta/tasks.md specs/_archive/015-fluxo/tasks.md
git diff --stat   # conferir: só linhas '- [ ] T' viraram '- [x] T', nada mais
```

- [ ] **Step 6: Verificar o gate no repo real**

Run: `python3 skills/spec-feature/scripts/check_cycle.py specs/016-harness`
Expected: nenhum achado C10 (os 6 arquivados limpos); achados C2/C8 sobre a própria 016 são esperados nesta altura (tasks.md/test-plan.md ainda não existem — fase tasks vem depois do plan).

- [ ] **Step 7: Commit**

```bash
git add skills/spec-feature/scripts/check_cycle.py specs/_archive/
git commit -m "feat(016-harness): C10 — archive sem task aberta (TDD) + higiene dos tasks.md arquivados"
```

---

### Task 3: arestas `dep:` no template e execução paralela no cycle.md (R1 + R3)

TDD dispensado: task só de documentação/template — sem lógica executável; verificação = selftest inalterado + `validate_integrity.py`.

**Files:**
- Modify: `skills/spec-feature/references/templates/tasks.md`
- Modify: `skills/spec-feature/references/cycle.md`
- Modify: `skills/spec-feature/references/adapters.md` (1 bullet na seção Superpowers)

**Interfaces:**
- Consumes: sintaxe `(dep: Tn[, Tm])` definida na Task 1 (C9 é o validador).
- Produces: seção `## Execução paralela por unidades (delta-016)` no cycle.md — a T5 insere a trilha de auditoria DEPOIS dela (ordem estável das seções).

- [ ] **Step 1: Substituir o conteúdo de `templates/tasks.md` por:**

```markdown
# Tasks — delta-{{NNN}}
<!-- ordenado por dependência; cada task executável sem contexto extra.
     Arestas de bloqueio (delta-016): `(dep: Tn[, Tm])` logo após o ID — task sem
     `dep:` é livre. Duas tasks sem caminho entre si no grafo são paralelizáveis
     (execução por worktree: cycle.md); o C9 valida existência e aciclicidade.
     Arquivo sem nenhum `dep:` = cadeia linear implícita pela ordem (retrocompatível). -->
- [ ] T1 — {{ação}} · arquivos: {{caminhos}} · cobre: {{Rn|RNFn|infra}} · verificação: {{comando/critério}}
- [ ] T2 (dep: T1) — {{ação}} · arquivos: {{caminhos}} · cobre: {{Rn}} · verificação: {{comando}}
```

- [ ] **Step 2: cycle.md — tabela de fases**

Na linha da fase `tasks` (tabela "Fases — critérios de entrada/saída"), trocar o critério de saída para citar as arestas: `` `tasks.md`: cada task com arquivos, `cobre:` e verificação, ordenada por dependência, com arestas `(dep: Tn)` explícitas quando há bloqueio (C9 valida) ``. Na linha da fase `implement`, acrescentar ao critério: `unidades paralelizáveis podem rodar em worktrees (seção abaixo)`.

- [ ] **Step 3: cycle.md — seção nova**

Inserir após a seção "## Perfil de execução da delta" (antes de "## Prototipação opcional"):

```markdown
## Execução paralela por unidades (delta-016)

O grafo do `tasks.md` (arestas `(dep: Tn[, Tm])`; task sem `dep:` é livre) define as
unidades de execução: **duas tasks sem caminho entre si são paralelizáveis**. No
implement, harness com subagentes → cada unidade pode rodar num subagente com
worktree isolada (motor `superpowers:using-git-worktrees`, contrato em adapters.md),
com convergência (merge das worktrees) antes do review. Harness sem subagentes ou
sem worktree → execução sequencial na ordem topológica, com aviso de degradação
(RNF2). O C9 valida o grafo — dep existente e aciclicidade; arquivo sem nenhum
`dep:` vale como cadeia linear implícita pela ordem (retrocompatível).
```

- [ ] **Step 4: adapters.md — bullet do implement**

Na seção "## Superpowers", bullet `implement`, acrescentar ao final: `Unidades paralelizáveis (cycle.md, "Execução paralela por unidades") → um subagente com worktree por unidade (superpowers:using-git-worktrees); sem subagentes/worktree → sequencial topológico com aviso.`

- [ ] **Step 5: Verificar e commitar**

Run: `python3 skills/guarding-doc-integrity/scripts/validate_integrity.py . && python3 skills/spec-feature/scripts/check_cycle.py --selftest`
Expected: exit 0 nos dois.

```bash
git add skills/spec-feature/references/
git commit -m "feat(016-harness): arestas dep: no template de tasks e execução paralela por worktree no ciclo"
```

---

### Task 4: vocabulário de harness canônico (R4) — dep: T1, T2

TDD dispensado: documentação pura; verificação = links vivos (`validate_integrity.py` C3) + leitura.

**Files:**
- Create: `skills/spec-feature/references/harness.md`
- Modify: `skills/spec-feature/SKILL.md` (linha 64 + lista "Arquivos da skill")
- Modify: `README.md` (linha 37 e nós do mermaid)

**Interfaces:**
- Consumes: nomes "C9 grafo de tasks" e "C10 convergência no archive" (Tasks 1–2).
- Produces: `references/harness.md` — dono único dos termos; T7 confere que CHANGELOG o cita.

- [ ] **Step 1: Criar `skills/spec-feature/references/harness.md` com este conteúdo:**

```markdown
# Harness — vocabulário canônico do framework

<!-- Dono único dos termos de harness engineering que o sdd-iuri pratica (delta-016).
     Skills e docs citam o termo e linkam este arquivo; não redefinem (regra de ouro). -->

O sdd-iuri é um **harness**: a estrutura determinística — skills, gates, registros
com dono — que envolve o agente e torna o trabalho verificável, auditável e
retomável entre sessões. Termos canônicos:

- **Initializer** — skill que prepara o ambiente antes do trabalho incremental
  (`projeto-init`, `projeto-infra`); padrão initializer + agentes incrementais (Anthropic).
- **Agente incremental** — sessão que executa exatamente uma delta (1 feature =
  1 delta spec); deltas pequenas são o ponto crítico validado do padrão.
- **Gate determinístico** — verificação mecânica versionada no repo com selftest
  (`check_cycle.py` C1–C10, `validate_integrity.py`), distinta de gate por prompt:
  o que é juízo permanece humano (ADR-0006, ADR-0014).
- **Degradação graciosa** — motor externo ausente → fallback com aviso, nunca
  quebra (ADR-0004; RNF2; contratos em adapters.md).
- **Human-in-the-loop** — a IA propõe, o humano aprova; toda aprovação exigida pelo
  ciclo tem registro citável (trilha de auditoria, cycle.md).
- **Trilha de auditoria** — o conjunto das aprovações registradas nos artefatos das
  próprias fases; sobrevive ao archive em `specs/_archive/` (ADR-0014).
- **Unidade paralelizável** — subconjunto de tasks sem caminho entre si no grafo do
  `tasks.md`; pode executar em subagente com worktree isolada (cycle.md,
  "Execução paralela por unidades").
```

- [ ] **Step 2: SKILL.md — dois edits**

Linha 64, trocar o parêntese dos checks por: `(C1 aceite · C2 cobertura · C3 estado · C4 archive sem perda · C5 tamanho do TRUTH · C6 pendência roteada · C7 split de PR · C8 plano de testes · C9 grafo de tasks · C10 convergência no archive)`.
Na lista "Arquivos da skill", após a linha do `adapters.md`, inserir: `- \`references/harness.md\` — vocabulário canônico de harness (initializer, gate determinístico, unidade paralelizável, ...); os demais docs linkam, não redefinem.`

- [ ] **Step 3: README.md — dois edits**

Linha 37: trocar `checks C1–C8` por `checks C1–C10`. No mermaid (linhas ~24–35): trocar o nó `tasks` por `tasks["tasks<br>(grafo dep: — C9)"]` e o nó `archive` por `archive["archive<br>(TRUTH.md; C10)"]`.

- [ ] **Step 4: Verificar e commitar**

Run: `python3 skills/guarding-doc-integrity/scripts/validate_integrity.py .`
Expected: exit 0 (links vivos).

```bash
git add skills/spec-feature/ README.md
git commit -m "feat(016-harness): harness.md — vocabulário canônico; espelhos C1–C10 no README e SKILL"
```

---

### Task 5: trilha de auditoria de aprovação (R5) — dep: T3

TDD dispensado: documentação pura; verificação = `validate_integrity.py` + leitura. (dep: T3 porque edita o mesmo cycle.md — evita conflito de seção.)

**Files:**
- Modify: `skills/spec-feature/references/cycle.md`

**Interfaces:**
- Consumes: seção "Execução paralela por unidades" (T3) como âncora de posição.
- Produces: seção "Trilha de auditoria de aprovação" — citada pelo harness.md (T4) e pelo CHANGELOG (T7).

- [ ] **Step 1: Inserir no cycle.md, após a seção "## Execução paralela por unidades (delta-016)":**

```markdown
## Trilha de auditoria de aprovação (delta-016)

Toda aprovação humana que o ciclo exige fica registrada como linha citável no
artefato da própria fase — sem arquivo de auditoria separado (renúncia ao audit.md
do AI-DLC: ADR-0014). A trilha sobrevive ao archive junto com os artefatos.

| Aprovação | Artefato (dono) | Sintaxe |
|---|---|---|
| Perfil da delta (R36) | cabeçalho do `spec.md` | `Perfil: <perfil> — <justificativa> (aprovado: AAAA-MM-DD)` |
| Prototipação (R37) | seção Contexto do `spec.md` | `Protótipo: aprovado AAAA-MM-DD — <caminho>` |
| Ressalvas do analyze | `analyze.md`, linha após o veredito | `Ressalvas aceitas: AAAA-MM-DD — <resumo>` |
| Achados do review | `analyze.md`, apêndice do review | `Review: convergentes tratados / recusas justificadas — AAAA-MM-DD` |
```

- [ ] **Step 2: Verificar e commitar**

Run: `python3 skills/guarding-doc-integrity/scripts/validate_integrity.py .`
Expected: exit 0.

```bash
git add skills/spec-feature/references/cycle.md
git commit -m "feat(016-harness): trilha de auditoria de aprovação no ciclo (registro nos artefatos das fases)"
```

---

### Task 6: graphify como 4º motor opcional (R6)

TDD dispensado: contrato/documentação; verificação = `validate_integrity.py` + leitura. O motor NÃO é instalado nesta delta — a linha de política declara "não testada" (mesma honestidade do R34 com o superpowers 6.2.0).

**Files:**
- Modify: `skills/spec-feature/references/adapters.md` (tabela de contrato + seção nova + política de pins)
- Modify: `skills/projeto-init/references/templates/doc-profile.yaml`
- Modify: `skills/descoberta/SKILL.md` (1 parágrafo-ponte)

**Interfaces:**
- Consumes: modelo `confirmado`/`inferido`/`lacuna` (R25 do TRUTH); padrão de seção dos adapters.
- Produces: seção "## graphify" em adapters.md — referenciada por descoberta/SKILL.md e cycle.md sem duplicar.

- [ ] **Step 1: adapters.md — linha na tabela de contrato (após a linha `review`):**

```markdown
| contexto de codebase (descoberta · specify/plan · review) — opcional | `graphify` (CLI/MCP externo, não é plugin Claude) | nomes dos comandos `query`/`path`/`explain`; formato das tags de confiança; instalador (escreve hook/CLAUDE.md — nunca usar) |
```

- [ ] **Step 2: adapters.md — seção nova antes de "## Política de dependência":**

```markdown
## graphify (contexto de codebase — delta-016, opcional)

Camada de contexto para as fases que leem código em projeto-alvo grande/brownfield:
`descoberta`, `specify`/`plan` e o eixo Spec do `review` (impacto do diff da delta).
**Não** é motor de grafo de tarefas — o `tasks.md` continua dono das arestas (ADR-0014).

- **Habilitação dupla e manual:** binário instalado **e** `motores.graphify: true` no
  `doc-profile.yaml` do projeto-alvo. **Nunca rode `graphify install`** — o instalador
  escreve hook `PreToolUse` e CLAUDE.md do projeto, interferindo no harness (renúncia:
  ADR-0014). Instalação manual consciente; preferir `--code-only` (AST local
  determinístico, zero LLM).
- **Invocação:** `graphify query`/`path`/`explain` como insumo fundamentado — toda
  aresta citada entra com `arquivo:linha`. Tags de confiança mapeiam no modelo da
  descoberta (R25): `EXTRACTED` → `confirmado` · `INFERRED` → `inferido` ·
  `AMBIGUOUS` → `lacuna` (requer validação humana).
- **Verificação pós-fase:** claim vindo do graphify sem fonte `arquivo:linha` + tag
  mapeada não entra no artefato (mesma regra do R25).
- **Fallback (ausente ou desabilitado):** fluxo atual (grep/Explore) com no máximo
  1 linha de aviso — degradação graciosa (RNF2).
```

- [ ] **Step 3: adapters.md — linha na tabela de política de dependência:**

```markdown
| `graphify` (CLI externo) | — (não testada — contrato definido pela doc upstream) | pin por tag na primeira adoção real | 2026-07-28 (release quase diária, bus factor = 1) | opcional com degradação total: ausente, nada do ciclo quebra; a primeira adoção real define o pin e valida o contrato |
```

- [ ] **Step 4: doc-profile.yaml — bloco novo após `artefatos:`:**

```yaml
# Motores externos opcionais que o ciclo consulta neste projeto (contrato e avisos:
# spec-feature/references/adapters.md, seção graphify — instalação manual, ADR-0014).
motores:
  graphify: false   # true = descoberta/specify/plan/review consultam o grafo de codebase (requer binário instalado; NUNCA use `graphify install`)
```

- [ ] **Step 5: descoberta/SKILL.md — parágrafo-ponte**

Ao final da seção "## Processo (6 fases)", inserir: `Projeto com graphify habilitado (doc-profile \`motores.graphify: true\`): as consultas ao grafo de codebase entram como insumo da mineração com fonte \`arquivo:linha\` e tag mapeada no modelo de confiança — contrato, avisos de instalação e fallback na seção graphify de \`spec-feature/references/adapters.md\`. Ausente → mineração atual, com 1 linha de aviso.`

- [ ] **Step 6: Verificar e commitar**

Run: `python3 skills/guarding-doc-integrity/scripts/validate_integrity.py .`
Expected: exit 0.

```bash
git add skills/spec-feature/references/adapters.md skills/projeto-init/ skills/descoberta/
git commit -m "feat(016-harness): graphify como 4º motor opcional — contrato, pins e toggle no doc-profile"
```

---

### Task 7: fechamento — CHANGELOG, HANDOFF e verificação completa — dep: T1, T2, T3, T4, T5, T6

**Files:**
- Modify: `CHANGELOG.md` (`[Não lançado]`)
- Modify: `HANDOFF.md` (seção Agora)

- [ ] **Step 1: CHANGELOG — sob `## [Não lançado]`:**

```markdown
### Adicionado
- **Arestas de bloqueio no tasks.md** (delta-016, R1): sintaxe `(dep: Tn[, Tm])` no template; unidades paralelizáveis derivadas do grafo; **C9** valida existência e aciclicidade. Sem `dep:` → cadeia linear implícita (retrocompatível).
- **C10 — convergência mínima no archive** (delta-016, R2): delta arquivada com task `- [ ]` remanescente → ALTO; auditoria semântica codebase×spec segue humana (ADR-0014).
- **Execução paralela por worktree** (delta-016, R3): unidades sem caminho entre si rodam em subagentes com worktree isolada (`superpowers:using-git-worktrees`); degradação sequencial topológica.
- **`references/harness.md`** (delta-016, R4): vocabulário canônico de harness — initializer, agente incremental, gate determinístico, degradação graciosa, human-in-the-loop, trilha de auditoria, unidade paralelizável.
- **Trilha de auditoria de aprovação** (delta-016, R5): toda aprovação humana registrada como linha citável no artefato da própria fase; sem audit.md separado (ADR-0014).
- **graphify como 4º motor externo opcional** (delta-016, R6): contrato nos adapters (instalação manual consciente, `--code-only`, tags → `confirmado`/`inferido`/`lacuna`), toggle `motores.graphify` no doc-profile, fallback grep/Explore.
- **ADR-0014**: renúncias das quatro decisões (audit.md, converge semântico, grafo de tarefas no graphify, auto-install).

### Mudado
- `check_cycle.py` passa a C1–C10 (MUDA R12 no archive) com fixtures novas no selftest; templates `tasks.md` com `dep:`; `cycle.md`/`adapters.md`/`SKILL.md`/README refletem grafo, worktrees, trilha e graphify; `tasks.md` de 6 deltas arquivadas receberam a higiene de checkbox exigida pelo C10 (trabalho já concluído nos merges).
```

- [ ] **Step 2: HANDOFF — atualizar "Agora"** para "delta-016 implementada na `feat/016-harness` — próxima: test-plan + analyze + review" (1–2 linhas, referenciando a delta).

- [ ] **Step 3: Verificação completa**

Run: `python3 skills/spec-feature/scripts/check_cycle.py --selftest && python3 skills/guarding-doc-integrity/scripts/validate_integrity.py --selftest && python3 skills/guarding-doc-integrity/scripts/validate_integrity.py .`
Expected: exit 0 nos três.

- [ ] **Step 4: Commit**

```bash
git add CHANGELOG.md HANDOFF.md
git commit -m "docs(016-harness): CHANGELOG e HANDOFF da implementação"
```

---

## Pós-implement (fases seguintes do ciclo — não são tasks deste plano)

1. **tasks**: gerar `specs/016-harness/tasks.md` das Tasks 1–7 acima **usando a sintaxe `dep:` nova** (dogfood: T2 dep T1; T4 dep T1,T2; T5 dep T3; T7 dep de todas).
2. **test-plan**: derivar `test-plan.md` dos cenários da spec + verificações das tasks (perfil completo — obrigatório, C8).
3. **analyze**: `check_cycle.py specs/016-harness` + juízo do analyze.md.
4. **implement → review em 2 eixos paralelos (R35) → PR (split R17 provável) → archive** (consolida R40–R44 + MUDA R12 no TRUTH; tag `v0.12.0`).
