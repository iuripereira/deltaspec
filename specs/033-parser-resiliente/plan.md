<!-- resumo deltaspec · ≤15 linhas · única parte do plano lida pelo analyze e pelo humano -->
**Objetivo:** tirar o parser do gate da forma exata dos templates — item multi-linha deixa de gerar achado falso e heading fora da forma deixa de sumir em silêncio — com um dono canônico do formato de item. **Cobre:** R1 (MUDA R12), R2 (da delta-033) **Decisões duráveis → ADRs:** nenhuma (o desenho segue regras canônicas já vigentes: fonte canônica única e âncora de início de linha) **Riscos assumidos:** sobre-captura de prosa pela continuação (mitigada pela parada em linha em branco/heading e coberta por caso de teste); o `dep:` mantém a âncora colada ao ID (R40), então a tolerância vale só para os campos depois do travessão.

---

# delta-033 — Plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** um módulo dono do formato de item (`itens.py`), consumido pelo `check_cycle.py` (C2/C8/C9/C10) e pelo `tickets.py`, tolerando continuação de linha; e um detector no C1 que acusa heading `###` fora da forma canônica em vez de deixar o requisito desaparecer.

**Architecture:** `skills/spec-feature/scripts/itens.py` expõe `itens(texto, prefixo)` → lista de itens com `id`, `feito`, `texto` (linhas do item já juntas por espaço), `linha` (nº da primeira linha) e `resto` (o que vem colado depois do ID, onde o `dep:` é lido). Os consumidores param de casar regex própria e passam a iterar essa lista. `check_cycle.py` e `tickets.py` moram no mesmo diretório — import direto, sem `sys.path` (diferente do caso `projecao.py`, que é de outra skill).

**Tech Stack:** Python 3.11+ stdlib (`re`), sem dependência nova. Selftests co-localizados (`--selftest`).

## Global Constraints

- Identificadores, comentários e mensagens em **PT-BR**; stdlib apenas (PyYAML só onde já existe, ADR-0023).
- **Parsing por âncora de início de linha, nunca busca de texto** — a regra que a delta reforça, não afrouxa.
- **Zero duplicação da regex de item:** depois desta delta, `^\s*-\s*\[[ xX]\]\s*(T|CT)\d+` existe em **um** arquivo (o review mede isso por grep).
- Funções puras separadas de I/O; constantes nomeadas; zero valor mágico.
- **Retrocompatibilidade medida:** 40 artefatos arquivados varridos em 2026-08-07 — 0 itens multi-linha e 0 conteúdo após a lista; nenhum comportamento vigente pode mudar (o selftest do C2/C8/C9/C10 existente é a rede).
- **`(dep: Tn)` continua colado ao ID** (R40/delta-016): a tolerância não vale para a aresta.
- Ao mudar o parser, atualizar consumidores **e** fixtures juntos.

---

### Task 1: módulo `itens.py` — dono do formato de item

**Files:**
- Create: `skills/spec-feature/scripts/itens.py`
- Test: selftest embutido (`python3 skills/spec-feature/scripts/itens.py --selftest`)

**Interfaces:**
- Consumes: nada (folha).
- Produces (usado por T2 e T3):
  - `ITEM = re.compile(r"^\s*-\s*\[([ xX])\]\s*((?:T|CT)\d+)\b")` — **única** âncora de item do framework.
  - `itens(texto: str, prefixo: str) -> list[dict]` — cada item: `{"id", "feito": bool, "texto": str, "linha": int, "resto": str}`. `texto` = linha do item + continuações unidas por espaço; `resto` = trecho colado depois do ID **na primeira linha** (onde o C9 lê a aresta); `linha` = nº (1-based) da linha do item. Filtra por `prefixo` (`"T"` ou `"CT"`).
  - Regra de continuação (constante `PARADAS` documentando o porquê): a continuação começa na linha seguinte e para na **primeira** ocorrência de — linha em branco, novo item, ou linha iniciando com `#`. Motivo: parágrafo separado por linha em branco é prosa, não continuação (mede o risco de sobre-captura do plano).

- [ ] **Step 1: escrever o selftest que falha**

```python
def selftest():
    txt = ("# Tasks — delta-900\n"
           "- [ ] T1 — ação curta · arquivos: a.py · cobre: R1 · verificação: pytest\n"
           "- [x] T2 (dep: T1) — ação longa que o autor quebrou\n"
           "      · arquivos: b.py · cobre: R2 · verificação: ruff\n"
           "\n"
           "Prosa depois da lista que NÃO pode entrar em nenhuma task.\n")
    its = itens(txt, "T")
    assert [i["id"] for i in its] == ["T1", "T2"], its
    assert its[0]["feito"] is False and its[1]["feito"] is True
    assert "verificação: ruff" in its[1]["texto"], "continuação precisa entrar no texto"
    assert "Prosa depois" not in its[1]["texto"], "linha em branco corta a continuação"
    assert its[1]["resto"].startswith("(dep: T1)"), its[1]["resto"]
    assert its[0]["linha"] == 2 and its[1]["linha"] == 3
    # heading corta a continuação
    txt2 = "- [ ] CT1 — caso · cobre: R1 · tipo: auto · verificação: x\n## Outra seção\nprosa\n"
    assert len(itens(txt2, "CT")) == 1 and "Outra seção" not in itens(txt2, "CT")[0]["texto"]
    # prefixo filtra
    assert itens(txt, "CT") == []
    print("selftest itens: OK (continuação, paradas, resto, prefixo)")
```

- [ ] **Step 2: rodar e ver falhar** — `python3 skills/spec-feature/scripts/itens.py --selftest` → NameError.
- [ ] **Step 3: implementar**

```python
def itens(texto: str, prefixo: str) -> list[dict]:
    """Itens `- [ ] T1 — ...` de tasks.md/test-plan.md, com continuação de linha.

    Dono canônico do formato (delta-033): quem precisa de item do ciclo chama aqui,
    nunca reimplementa a âncora — dois parsers divergentes é como o `dep:` sumiria
    da projeção de tickets em silêncio.
    """
    linhas = texto.splitlines()
    out, atual = [], None
    for n, linha in enumerate(linhas, 1):
        m = ITEM.match(linha)
        if m:
            if atual:
                out.append(atual)
            atual = {"id": m.group(2), "feito": m.group(1).lower() == "x",
                     "texto": linha, "linha": n, "resto": linha[m.end():].lstrip()}
        elif atual is not None:
            if not linha.strip() or linha.lstrip().startswith("#"):
                out.append(atual)
                atual = None
            else:
                atual["texto"] += " " + linha.strip()
    if atual:
        out.append(atual)
    return [i for i in out if i["id"].startswith(prefixo) and i["id"][len(prefixo):].isdigit()]
```

- [ ] **Step 4: selftest verde.**
- [ ] **Step 5: commit** — `feat(033-parser-resiliente): itens.py vira o dono do formato de item`.

### Task 2 (dep: T1): `check_cycle.py` consome o módulo (C2, C8, C9, C10)

**Files:**
- Modify: `skills/spec-feature/scripts/check_cycle.py` — remove `TAREFA`, `CASO`, `TAREFA_ABERTA`; `c2_cobertura`, `c8_test_plan`, `c9_grafo`, `c10_convergencia` passam a iterar `itens(...)`; `campo()` passa a ser chamado sobre `item["texto"]` (não sobre a linha crua)
- Test: `python3 skills/spec-feature/scripts/check_cycle.py --selftest`

**Interfaces:**
- Consumes: `from itens import itens` (mesmo diretório).
- Produces: nada novo para fora; o comportamento de todos os checks fica idêntico para entrada de linha única.

- [ ] **Step 1: casos novos no selftest, antes de mexer no código** — a fixture `limpa_tasks` ganha uma gêmea multi-linha (mesma task, quebrada em duas) que deve produzir **os mesmos achados que a versão em linha única**; e um caso com prosa depois da lista que não pode virar `verificação:`. Rodar → FAIL.
- [ ] **Step 2: implementar** — em `c9_grafo`, a aresta sai de `item["resto"]` (mantém a âncora colada ao ID, R40); em `c10_convergencia`, o contador vira `sum(1 for i in itens(txt, "T") if not i["feito"])`.
- [ ] **Step 3: selftest verde** — inclusive os casos antigos, que provam a retrocompatibilidade.
- [ ] **Step 4: rodar o gate contra as 33 deltas arquivadas** (`for d in specs/_archive/*/; do check_cycle.py $d; done`) e conferir que nenhum veredito mudou em relação ao registrado em cada `analyze.md`.
- [ ] **Step 5: commit** — `fix(033-parser-resiliente): C2/C8/C9/C10 toleram item multi-linha (MUDA R12)`.

### Task 3 (dep: T1): `tickets.py` consome o mesmo módulo

**Files:**
- Modify: `skills/spec-feature/scripts/tickets.py` — `PADRAO_TASK` sai; `parse_tasks` passa a montar seu retorno a partir de `itens(texto, "T")`, lendo `dep:` do `resto` e os campos do `texto`
- Test: `python3 skills/spec-feature/scripts/tickets.py --selftest`

**Interfaces:**
- Consumes: `from itens import itens`.
- Produces: `parse_tasks` mantém a assinatura e o formato de retorno atuais (o `tickets.md` gerado não muda) — só a fonte do parsing muda.

- [ ] **Step 1: caso novo no selftest** — `tasks.md` com task multi-linha cuja `(dep: T1)` está na primeira linha: o `tickets.md` gerado precisa trazer a dep e a ação completa. Rodar → FAIL.
- [ ] **Step 2–4: implementar, selftest verde (incluindo os casos da delta-017 intactos), commit** — `fix(033-parser-resiliente): tickets.py usa o parser canônico de item (R2)`.

### Task 4: C1 acusa heading fora da forma canônica

**Files:**
- Modify: `skills/spec-feature/scripts/check_cycle.py` — `blocos()`/`c1_aceite` ganham a detecção de heading `###` órfão
- Test: `python3 skills/spec-feature/scripts/check_cycle.py --selftest`

**Interfaces:** independente das T1–T3 (paralelizável).

- [ ] **Step 1: caso novo no selftest** — spec com `### R1 — ADICIONA:` válido **e** `### R2 — Adiciona:` (verbo minúsculo): precisa sair 1 ALTO nomeando a linha e o texto do heading; spec só com headings válidos → 0 achados novos (a varredura de 2026-08-07 mediu 92 headings em 32 deltas arquivadas, **0** fora da forma — o check não pode acusar nenhum deles). Rodar → FAIL.
- [ ] **Step 2: implementar** — `HEADING_QUALQUER = re.compile(r"^###\s+(.*)$")`; heading que casa `HEADING_QUALQUER` mas não `CABECALHO` → `("ALTO", f"spec.md l.{n}", f"heading '### {texto}' fora da forma canônica", "usar '### Rn — ADICIONA|MUDA|REMOVE' (templates/delta-spec.md) — requisito fora da forma some do gate")`.
- [ ] **Step 3: selftest verde + varredura das 33 deltas arquivadas sem novo achado. Step 4: commit** — `fix(033-parser-resiliente): C1 acusa heading fora da forma em vez de perder o requisito`.

### Task 5 (dep: T2, T3, T4): documentação e quito do DT-001

**Files:**
- Modify: `DEBT.md` — DT-001 → `quitado` (Encerrado com data, evidência dos dois modos e ref do PR); **corrigir o texto que diz "falha ruidosa, não silenciosa"** é proibido (o registro é de época) — a correção entra na linha do Encerrado
- Modify: `skills/spec-feature/references/analyze.md` — o C1 passa a citar o heading órfão; o C2 cita a tolerância a multi-linha
- Modify: `CHANGELOG.md` — `[Não lançado] > Corrigido`
- Test: `python3 skills/guarding-doc-integrity/scripts/validate_integrity.py .` → PASS; `python3 skills/handoff/scripts/debito.py fila .` → PASS

- [ ] **Step 1: editar os 3. Step 2: rodar os dois gates. Step 3: commit** — `docs(033-parser-resiliente): analyze.md, CHANGELOG e DT-001 quitado`.

---

## Self-review (executado na escrita)

1. **Cobertura:** R1 → T1+T2+T4 (multi-linha e heading órfão); R2 → T1+T2+T3 (parser único). T5 é documentação/quito.
2. **Placeholders:** nenhum — código central e casos de teste presentes.
3. **Consistência de tipos:** `itens(texto, prefixo) -> list[dict]` com as mesmas 5 chaves em T1/T2/T3; `resto` é o campo que preserva a âncora do `dep:` nos dois consumidores.
