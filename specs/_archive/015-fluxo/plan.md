<!-- resumo sdd-iuri · ≤15 linhas · única parte do plano lida pelo analyze e pelo humano -->
**Objetivo:** ciclo com perfil `completo|enxuto`, prototipação opt-in, `test-plan.md` + C8 no gate e tipo `bugfix` (Fase 2 do upgrade). **Cobre:** R1–R6 (da delta-015) **Decisões duráveis → ADRs:** ADR-0013 (gravado no clarify) **Riscos assumidos:** split R17 provável (artefatos em PR próprio); retrocompat garantida por default `completo` e fixtures novas no selftest; TDD dispensado nas tasks de prosa/template (sem lógica executável — verificação = validate_integrity + selftest dos consumidores).

---

# Delta-015 (fluxo) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar os R1–R6 da delta-015: perfil de execução por delta, prototipação opcional, plano de testes com check C8, tipo bugfix, e as mudanças de R12/R35.

**Architecture:** O contrato novo vive nos templates e no `cycle.md` (prosa normativa); a parte mecânica entra como C8 + parsing de cabeçalho no `check_cycle.py` (stdlib pura, selftest co-localizado). Nenhum arquivo novo de script — um check novo no gate existente.

**Tech Stack:** Python 3.11+ stdlib (`re`, `pathlib`, `subprocess`, `tempfile`) · Markdown PT-BR.

## Global Constraints

- Idioma PT-BR em código, comentários, docs e commits (CLAUDE.md).
- Zero dependência externa nos gates — stdlib pura (CLAUDE.md).
- Fonte canônica única: valor concreto vive no dono; espelhos referenciam (CLAUDE.md).
- Template mudou → consumidores **e** fixtures atualizam juntos (CLAUDE.md, Testes).
- ADR-0009 é `Accepted` (imutável): a categoria `prototipo` é registrada pela ADR-0013, nunca editando a 0009.
- Fim de task = commit na branch `feat/015-fluxo` (Conventional Commits, escopo `015-fluxo`).
- TDD: obrigatório nas tasks do `check_cycle.py` (lógica pura, contrato claro — via `--selftest`); **dispensado com justificativa** nas tasks de prosa/template: não há lógica executável, a verificação é `validate_integrity.py` (hook) + selftest dos consumidores.

---

### Task 1: Templates novos + cabeçalho do delta-spec

**Files:**
- Create: `skills/spec-feature/references/templates/test-plan.md`
- Create: `skills/spec-feature/references/templates/bugfix-spec.md`
- Modify: `skills/spec-feature/references/templates/delta-spec.md` (linha 2, cabeçalho)

**Interfaces:**
- Produces: formato de caso de teste `- [ ] CTn — <cenário> · cobre: Rn|RNFn · tipo: auto|manual · verificação: <comando|passos>` (o C8 da Task 2 parseia exatamente este formato); campos de cabeçalho `Perfil:`, `Test-plan:`, `Tipo:` (parseados por `campo()`).

- [ ] **Step 1: Criar `test-plan.md`** com este conteúdo:

```markdown
# Test plan — delta-{{NNN}}
<!-- derivado dos cenários DADO/QUANDO/ENTÃO da spec e das verificações do tasks.md — não inventa cenário novo (R3, delta-015) -->
<!-- teste manual roteirizado conta como cobertura; todo Rn/RNFn da spec precisa de ≥1 caso (C8) -->
- [ ] CT1 — {{cenário verificável}} · cobre: {{Rn|RNFn}} · tipo: {{auto|manual}} · verificação: {{comando (auto) | passos numerados (manual)}}
- [ ] CT2 — ...
```

- [ ] **Step 2: Criar `bugfix-spec.md`** com este conteúdo:

```markdown
# delta-{{NNN}} — {{nome-curto-do-fix}}
Estado: proposta | aplicada | arquivada · Data: {{AAAA-MM-DD}} · Branch: fix/{{NNN}}-{{nome}} · Tipo: bugfix

## Sintoma (≤3 linhas)
{{o que o usuário observa; onde; desde quando}}

## Reprodução
- DADO {{estado inicial}} QUANDO {{ação}} ENTÃO {{comportamento errado observado}} — esperado: {{comportamento correto}}

## Causa-raiz
{{a causa, não o sintoma — arquivo:linha quando couber; "em investigação" enquanto aberta}}

## Teste de regressão
- {{onde vive o teste que falha antes do fix e passa depois — obrigatório (R4, delta-015)}}

## Mudanças
<!-- só quando o fix altera requisito vigente; senão a linha abaixo fica como está -->
- nenhuma (correção sem mudança de requisito)

## Dependências e riscos
- {{pendências `- [ ]` seguem a regra do C6}}
```

- [ ] **Step 3: Atualizar o cabeçalho de `delta-spec.md`** — linha 2 vira:

```markdown
Estado: proposta | aplicada | arquivada · Data: {{AAAA-MM-DD}} · Branch: {{tipo}}/{{NNN}}-{{nome}} · Perfil: {{completo|enxuto — proposto pela IA, vale só com aprovação do usuário: "aprovado: AAAA-MM-DD"}}
```

E logo abaixo do título, adicionar o comentário:

```markdown
<!-- Perfil enxuto (R1, delta-015): clarify sob demanda; test-plan dispensável com "Test-plan: dispensado — <motivo>" no cabeçalho; review com eixos fundidos. Sem campo Perfil = completo. -->
```

- [ ] **Step 4: Verificação** — TDD dispensado (template markdown, sem lógica; justificativa: a verificação executável é o selftest da Task 2, que consome este formato). Rodar:

Run: `python3 skills/spec-feature/scripts/check_cycle.py --selftest`
Expected: OK (fixtures atuais ainda passam — nada do script mudou)

- [ ] **Step 5: Commit**

```bash
git add skills/spec-feature/references/templates/
git commit -m "feat(015-fluxo): templates test-plan e bugfix-spec; campo Perfil no delta-spec"
```

---

### Task 2: C8 no `check_cycle.py` (cobertura do plano de testes) — TDD

**Files:**
- Modify: `skills/spec-feature/scripts/check_cycle.py`
- Test: o próprio `--selftest` (co-localização, RNF4)

**Interfaces:**
- Consumes: formato de caso `CTn` e campos de cabeçalho da Task 1; helpers existentes `campo()`, `blocos()`, `checar()`.
- Produces: `CASO = re.compile(r"^\s*-\s*\[[ xX]\]\s*(CT\d+)")`; `def c8_testplan(delta: Path, bs, spec_txt: str, v: list) -> None`; chamada em `checar()` após `c7_split`; docstring/saída passam de C1–C7 a C1–C8.

- [ ] **Step 1: Escrever as fixtures que falham** — em `selftest()`, após o bloco do C6, adicionar:

```python
    # C8 — plano de testes (delta-015)
    limpa_testplan = "- [ ] CT1 — login ok · cobre: R1 · tipo: auto · verificação: pytest -k login\n" \
                     "- [ ] CT2 — latência · cobre: RNF1 · tipo: manual · verificação: roteiro k6 em docs\n"

    def rodar_c8(spec_txt, testplan_txt=None):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            delta = root / "specs" / "001-x"
            delta.mkdir(parents=True)
            (delta / "spec.md").write_text(spec_txt, encoding="utf-8")
            if testplan_txt is not None:
                (delta / "test-plan.md").write_text(testplan_txt, encoding="utf-8")
            v: list = []
            c8_testplan(delta, blocos(spec_txt), spec_txt, v)
            return v

    assert rodar_c8(limpa_spec, limpa_testplan) == [], "C8: delta com plano completo deveria passar"
    ausente = rodar_c8(limpa_spec)  # sem test-plan.md, perfil completo (default)
    assert any(s == "ALTO" and "test-plan.md ausente" in q for s, o, q, _ in ausente), f"C8 ausente: {ausente}"
    spec_dispensa = limpa_spec.replace(
        "Estado: proposta · Data: 2026-01-01 · Branch: feat/001-x",
        "Estado: proposta · Data: 2026-01-01 · Branch: feat/001-x · Perfil: enxuto (aprovado: 2026-01-01) · Test-plan: dispensado — delta só de prosa")
    dispensada = rodar_c8(spec_dispensa)
    assert len(dispensada) == 1 and dispensada[0][0] == "BAIXO", f"C8 dispensa: {dispensada}"
    orfao = rodar_c8(limpa_spec, "- [ ] CT1 — login ok · cobre: R1 · tipo: auto · verificação: pytest\n")
    assert any(s == "ALTO" and "RNF1" in q for s, _, q, _ in orfao), f"C8 órfão: {orfao}"
    morta = rodar_c8(limpa_spec, limpa_testplan + "- [ ] CT3 — x · cobre: R9 · tipo: auto · verificação: pytest\n")
    assert any(s == "ALTO" and "R9" in q for s, _, q, _ in morta), f"C8 referência morta: {morta}"
    caso_sem_campos = rodar_c8(limpa_spec, "- [ ] CT1 — login ok · cobre: R1\n- [ ] CT2 — lat · cobre: RNF1 · tipo: auto · verificação: k6\n")
    assert any(s == "MÉDIO" and "CT1" in o for s, o, q, _ in caso_sem_campos), f"C8 caso incompleto: {caso_sem_campos}"
```

E atualizar a linha final de contagem: `print("selftest: OK (...)")` — ajustar o texto para incluir o C8.

- [ ] **Step 2: Rodar para ver falhar**

Run: `python3 skills/spec-feature/scripts/check_cycle.py --selftest`
Expected: `NameError: name 'c8_testplan' is not defined`

- [ ] **Step 3: Implementar o C8** — após `c7_split`, adicionar:

```python
CASO = re.compile(r"^\s*-\s*\[[ xX]\]\s*(CT\d+)")  # junto dos outros regex no topo


def c8_testplan(delta: Path, bs, spec_txt: str, v: list) -> None:
    """Cobertura Rn/RNFn → caso de teste (espelho do C2). Ausência: ALTO no perfil
    completo; BAIXO com dispensa declarada (enxuto) ou em bugfix sem tasks (delta-015)."""
    cabecalho = spec_txt.split("\n## ", 1)[0]
    tp = delta / "test-plan.md"
    if not tp.is_file():
        dispensa = campo(cabecalho, "Test-plan")
        bugfix = (campo(cabecalho, "Tipo") or "").lower() == "bugfix" and not (delta / "tasks.md").is_file()
        if dispensa and "dispensado" in dispensa.lower():
            v.append(("BAIXO", "test-plan.md", f"dispensado no cabeçalho: {dispensa}", "ok se o perfil enxuto foi aprovado (R1)"))
        elif bugfix:
            v.append(("BAIXO", "test-plan.md", "bugfix sem tasks — test-plan sob demanda", "teste de regressão obrigatório cobre (R4)"))
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
        cobre = campo(line, "cobre")
        if not cobre or not campo(line, "tipo") or not campo(line, r"verifica[çc][ãa]o"):
            v.append(("MÉDIO", f"test-plan.md {cid}", "caso sem 'cobre:'/'tipo:'/'verificação:' completos", "cobre: Rn · tipo: auto|manual · verificação: comando ou passos"))
        if cobre:
            for alvo in re.split(r"[,/]", cobre):
                alvo = alvo.strip()
                cobertos.add(alvo)
                if alvo not in ids_spec:
                    v.append(("ALTO", f"test-plan.md {cid}", f"cobre '{alvo}', que não existe no spec.md", "corrigir a referência ou adicionar o requisito"))
    for rid in sorted(ids_spec - cobertos):
        v.append(("ALTO", f"spec.md {rid}", "requisito sem caso no test-plan.md", f"adicionar caso com 'cobre: {rid}' (manual roteirizado conta)"))
```

Na função `checar()`, após `c7_split(root, delta, v)`:

```python
    c8_testplan(delta, bs, spec.read_text(encoding="utf-8"), v)
```

(reutilize a leitura já feita: `spec_txt = spec.read_text(...)` uma vez, passada a `blocos` e ao C8).

- [ ] **Step 4: Atualizar docstring e saída** — no docstring, adicionar `C8  cobertura do plano de testes — Rn/RNFn sem caso; ausência sem dispensa (delta-015)`; na saída de `main()`, trocar `"Parcial: cobre C1–C7; ..."` por `"Parcial: cobre C1–C8; ..."`.

- [ ] **Step 5: Rodar até passar**

Run: `python3 skills/spec-feature/scripts/check_cycle.py --selftest`
Expected: `selftest: OK (... C8 ...)` + `selftest C4: OK` + `selftest C7: OK`

- [ ] **Step 6: Commit**

```bash
git add skills/spec-feature/scripts/check_cycle.py
git commit -m "feat(015-fluxo): C8 — cobertura do plano de testes no check_cycle (TDD)"
```

---

### Task 3: suporte a `Tipo: bugfix` no gate — TDD

**Files:**
- Modify: `skills/spec-feature/scripts/check_cycle.py` (função `checar()` e fixtures)

**Interfaces:**
- Consumes: `campo()`, cabeçalho `Tipo: bugfix` (Task 1), C8 já tratando bugfix (Task 2).
- Produces: em `checar()`, spec `Tipo: bugfix` sem blocos Rn **e** com a linha `nenhuma (correção sem mudança de requisito)` não dispara o ALTO "nenhum bloco"; exige `## Reprodução` com DADO/QUANDO/ENTÃO e seção `## Teste de regressão` não vazia (ALTO se faltar).

- [ ] **Step 1: Fixtures que falham** — em `selftest()`:

```python
    # bugfix (delta-015): sem bloco Rn é válido; repro e teste de regressão são obrigatórios.
    # Runner próprio: NÃO grava tasks.md (o rodar() comum grava, e o C2 acusaria "nenhuma task").
    def rodar_bugfix(spec_txt):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            delta = root / "specs" / "002-parse"
            delta.mkdir(parents=True)
            (delta / "spec.md").write_text(spec_txt, encoding="utf-8")
            return checar(root, delta)

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
    v_bugfix = rodar_bugfix(bugfix_ok)
    assert not any("nenhum bloco" in q for _, _, q, _ in v_bugfix), f"bugfix não exige bloco Rn: {v_bugfix}"
    assert not any(s == "ALTO" for s, _, _, _ in v_bugfix), f"bugfix sem tasks/test-plan é válido (só BAIXO do C8): {v_bugfix}"
    sem_regressao = bugfix_ok.replace("## Teste de regressão\n- fixture bugfix_ok no selftest\n\n", "")
    v_sem = rodar_bugfix(sem_regressao)
    assert any(s == "ALTO" and "regressão" in q for s, _, q, _ in v_sem), f"bugfix sem teste de regressão: {v_sem}"
```

(As fixtures rodam `checar()` inteiro: o contrato é C2 pulado sem tasks.md, C8 rebaixado a BAIXO — Task 2 — e nenhum ALTO na fixture limpa.)

- [ ] **Step 2: Rodar para ver falhar**

Run: `python3 skills/spec-feature/scripts/check_cycle.py --selftest`
Expected: AssertionError nas fixtures novas (o "nenhum bloco" e o "nenhuma task" disparam)

- [ ] **Step 3: Implementar em `checar()`** — substituir o miolo por:

```python
    spec_txt = spec.read_text(encoding="utf-8")
    bs = blocos(spec_txt)
    cabecalho = spec_txt.split("\n## ", 1)[0]
    bugfix = (campo(cabecalho, "Tipo") or "").lower() == "bugfix"
    v: list = []
    if not bs and not bugfix:
        v.append(("ALTO", "spec.md", "nenhum bloco '### Rn — ADICIONA|MUDA|REMOVE'", "usar templates/delta-spec.md"))
    if bugfix:
        repro = re.search(r"^##\s+Reprodu[çc][ãa]o\s*$(.*?)(?=^##\s|\Z)", spec_txt, re.M | re.S)
        alto = (repro.group(1).upper() if repro else "")
        if not repro or any(k not in alto for k in ("DADO", "QUANDO", "ENTÃO")):
            v.append(("ALTO", "spec.md", "bugfix sem Reprodução DADO/QUANDO/ENTÃO", "usar templates/bugfix-spec.md"))
        regressao = re.search(r"^##\s+Teste de regress[ãa]o\s*$(.*?)(?=^##\s|\Z)", spec_txt, re.M | re.S)
        if not regressao or not re.search(r"^\s*-\s*\S", regressao.group(1), re.M) or "{{" in (regressao.group(1)):
            v.append(("ALTO", "spec.md", "bugfix sem teste de regressão declarado", "apontar o teste que falha antes e passa depois do fix (R4)"))
    c1_aceite(bs, v)
    if not (bugfix and not tasks.is_file()):
        c2_cobertura(bs, tasks.read_text(encoding="utf-8") if tasks.is_file() else "", v)
    c3_estado(root, v)
    c4_archive(root, bs, v)
    c5_tamanho(root, v)
    c6_pendencias(root, v)
    c7_split(root, delta, v)
    c8_testplan(delta, bs, spec_txt, v)
    return v
```

(Um bugfix **com** blocos MUDA continua passando por C1/C4 normalmente — R4 último cenário.)

- [ ] **Step 4: Rodar até passar**

Run: `python3 skills/spec-feature/scripts/check_cycle.py --selftest`
Expected: OK em todas as fixtures (limpa, RF-NN, suja, C6, C8, bugfix, C4, C7)

- [ ] **Step 5: Commit**

```bash
git add skills/spec-feature/scripts/check_cycle.py
git commit -m "feat(015-fluxo): gate reconhece Tipo bugfix — repro e teste de regressão obrigatórios (TDD)"
```

---

### Task 4: prosa normativa — cycle.md, SKILL.md, adapters.md, analyze.md

**Files:**
- Modify: `skills/spec-feature/references/cycle.md`
- Modify: `skills/spec-feature/SKILL.md`
- Modify: `skills/spec-feature/references/adapters.md`
- Modify: `skills/spec-feature/references/analyze.md`

**Interfaces:**
- Consumes: campos/templates da Task 1, comportamento do gate das Tasks 2–3.
- Produces: tabela "Estágios por perfil" no cycle.md (fonte única — SKILL.md e adapters referenciam).

- [ ] **Step 1: `cycle.md`** — (a) na tabela de fases, adicionar a linha `test-plan` após `tasks`: entrada `tasks.md pronto`, saída `test-plan.md derivado dos cenários da spec e verificações das tasks (template; C8 valida)`, motor `nativo (template)`; (b) nova seção após "Triagem do clarify":

```markdown
## Perfil de execução da delta (R1, delta-015 — ADR-0013)

No specify, a IA propõe `Perfil: completo|enxuto` no cabeçalho com justificativa de 1 linha (escopo/risco); **só vale com aprovação explícita do usuário** registrada no cabeçalho (`aprovado: AAAA-MM-DD`). Sem o campo → `completo` (retrocompatível). O perfil opera **dentro** do ciclo do tipo (R10) — não reintroduz fase que o tipo exclui.

| Estágio | completo | enxuto |
|---|---|---|
| clarify | roda | sob demanda (só com ambiguidade apontada) |
| test-plan | obrigatório (C8: ALTO se ausente) | dispensável — `Test-plan: dispensado — <motivo>` no cabeçalho (C8: BAIXO) |
| review | dois eixos em subagentes paralelos (R35) | eixos fundidos num único subagente, achados classificados por eixo |
| plan · tasks · analyze · archive | integrais | integrais |

## Prototipação opcional (R2, delta-015 — estágio CONDITIONAL)

Delta cujo escopo toca interface ou fluxo que o stakeholder precisa ver → no specify a IA **propõe** o estágio com justificativa; executa só com aprovação (mesma regra do gate visual, ADR-0009). Forma: categoria `prototipo` do `doc-profile.yaml`; perfil ausente ou sem a categoria → HTML estático navegável em `docs/prototypes/NNN-nome/`, versionado e referenciado no Contexto da delta. Sem gatilho → o estágio se omite com no máximo 1 linha.

## Delta bugfix (R4, delta-015)

`Tipo: bugfix` no cabeçalho, template `templates/bugfix-spec.md` (sintoma, reprodução DADO/QUANDO/ENTÃO, causa-raiz, teste de regressão obrigatório), numeração NNN global. Pipeline: specify → plan curto → implement → review; clarify, tasks e test-plan sob demanda; analyze roda (read-only). Archive: sem mudança de requisito → move para `_archive/` sem consolidar no TRUTH.md; com bloco MUDA → consolidação normal (R6).
```

(c) Na tabela de fases, linha `review`, apontar também a fusão do enxuto: "(perfil enxuto: eixos fundidos — tabela acima)".

- [ ] **Step 2: `SKILL.md`** — (a) pipeline ganha os estágios novos:

```
specify → clarify → [prototipação?] → plan → tasks → test-plan → analyze → implement → review → archive → PR
```

(b) No "Processo", item 1: mencionar o campo `Perfil` proposto no cabeçalho (aprovação do usuário) e o tipo `bugfix` (template próprio, pipeline curto — detalhe em cycle.md); (c) na lista "Arquivos da skill", linha do check: `... C7 split de PR · C8 plano de testes`; adicionar os templates novos; (d) "Erros comuns": adicionar linha `| Perfil enxuto sem aprovação registrada | o perfil é proposta da IA — só vale com "aprovado: data" do usuário |`.

- [ ] **Step 3: `adapters.md`** — na seção "Review em dois eixos (delta-014)", após a frase da execução paralela, adicionar: `Perfil enxuto aprovado (R1, delta-015): os dois eixos podem rodar fundidos num único subagente, achados ainda classificados por eixo, mesma regra de convergência.`

- [ ] **Step 4: `analyze.md`** — linha 13: trocar "e a medição do split de PR (C7, ver abaixo)" por "a medição do split de PR (C7, ver abaixo) e a cobertura do plano de testes (C8, delta-015)".

- [ ] **Step 5: Verificação** — TDD dispensado (prosa normativa; justificativa: sem lógica executável — a verificação é o validador de integridade no hook + leitura no review):

Run: `python3 skills/guarding-doc-integrity/scripts/validate_integrity.py .`
Expected: RESULTADO: PASS

- [ ] **Step 6: Commit**

```bash
git add skills/spec-feature/
git commit -m "feat(015-fluxo): cycle/SKILL/adapters/analyze — perfil, prototipação, test-plan e bugfix"
```

---

### Task 5: categoria `prototipo` no doc-profile + README do gate

**Files:**
- Modify: `skills/projeto-init/references/templates/doc-profile.yaml`
- Modify: `README.md` (se citar a lista de checks C1–C7 — conferir com grep)

**Interfaces:**
- Consumes: decisão 2-c do ADR-0013.

- [ ] **Step 1: `doc-profile.yaml`** — no bloco `artefatos:`, adicionar após `explicativos`:

```yaml
  prototipo:    { obrigatorio: false }   # ferramenta: html-estatico — estágio CONDITIONAL do ciclo (delta-015, ADR-0013); default: docs/prototypes/NNN-nome/
```

- [ ] **Step 2: `README.md`** — rodar `grep -n "C7\|C1–C" README.md`; se a lista de checks aparecer, incluir o C8 na mesma notação do texto existente.

- [ ] **Step 3: Verificação** (TDD dispensado — YAML/prosa sem lógica; a sintaxe YAML é validada pelo job `ci`):

Run: `python3 skills/guarding-doc-integrity/scripts/validate_integrity.py .`
Expected: RESULTADO: PASS

- [ ] **Step 4: Commit**

```bash
git add skills/projeto-init/references/templates/doc-profile.yaml README.md
git commit -m "feat(015-fluxo): categoria prototipo no doc-profile; C8 no README"
```

---

### Task 6: dogfood + CHANGELOG

**Files:**
- Create: `specs/015-fluxo/test-plan.md` (dogfood do artefato novo na própria delta)
- Modify: `CHANGELOG.md` (`[Não lançado]`)

**Interfaces:**
- Consumes: template da Task 1, C8 das Tasks 2–3 (o gate precisa passar na própria delta).

- [ ] **Step 1: `specs/015-fluxo/test-plan.md`** — casos derivados dos cenários R1–R6 e das verificações das tasks (todo Rn coberto; `tipo: auto` aponta o selftest, `manual` aponta roteiro). Conteúdo mínimo:

```markdown
# Test plan — delta-015
- [ ] CT1 — spec sem campo Perfil vale completo (retrocompat) · cobre: R1 · tipo: auto · verificação: fixture C8 "ausente → ALTO" no selftest
- [ ] CT2 — dispensa declarada no enxuto rebaixa C8 a BAIXO · cobre: R1, R3 · tipo: auto · verificação: fixture C8 "dispensa" no selftest
- [ ] CT3 — proposta de prototipação só executa com aprovação · cobre: R2 · tipo: manual · verificação: roteiro — abrir delta com escopo de UI num repo de teste e conferir que o estágio só roda após aprovação registrada
- [ ] CT4 — requisito sem caso e caso com referência morta acusam ALTO · cobre: R3, R5 · tipo: auto · verificação: fixtures C8 "órfão" e "referência morta" no selftest
- [ ] CT5 — bugfix sem bloco Rn passa; sem teste de regressão acusa ALTO · cobre: R4 · tipo: auto · verificação: fixtures bugfix no selftest
- [ ] CT6 — review fundido no enxuto mantém classificação por eixo · cobre: R6 · tipo: manual · verificação: roteiro — rodar review de delta enxuta e conferir relatório com achados rotulados Spec/Qualidade
```

- [ ] **Step 2: `CHANGELOG.md`** — sob `## [Não lançado]` → `### Adicionado`: perfil de execução (R1), prototipação opcional (R2), test-plan + C8 (R3/R5), tipo bugfix (R4), ADR-0013; `### Mudado`: R12 (C8 na lista), R35 (fusão no enxuto), templates.

- [ ] **Step 3: Verificação final da delta**

Run: `python3 skills/spec-feature/scripts/check_cycle.py specs/015-fluxo && python3 skills/spec-feature/scripts/check_cycle.py --selftest && python3 skills/guarding-doc-integrity/scripts/validate_integrity.py --selftest`
Expected: veredito LIBERADO (ou ressalvas BAIXO/MÉDIO aceitas) + selftests OK

- [ ] **Step 4: Commit**

```bash
git add specs/015-fluxo/test-plan.md CHANGELOG.md
git commit -m "feat(015-fluxo): test-plan da própria delta (dogfood) + CHANGELOG"
```
