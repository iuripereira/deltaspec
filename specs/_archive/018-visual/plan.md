<!-- resumo sdd-iuri · ≤15 linhas · única parte do plano lida pelo analyze e pelo humano -->
**Objetivo:** implementar a delta-018 — Mermaid fonte + Figma/FigJam como camada de apresentação (categoria `apresentacao`), contrato do Figma MCP nos adapters, ADR-0015 complementando a 0009, e reserva de número no R5. **Cobre:** R1, R2, R3 (MUDA R5) (da delta-018) **Decisões duráveis → ADRs:** ADR-0015 (nova, nesta delta) **Riscos assumidos:** `generate_diagram` beta/pago futuro fica fora do caminho crítico (pendência de preço → DT no archive); claim do export FigJam entra na ADR marcado **não verificado**; TDD dispensado em todas as tasks — delta só de documentação/contrato, sem lógica executável (verificação = validate_integrity + selftests inalterados + leitura).

# delta-018 (visual) — Plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** o veredito híbrido da pesquisa vira contrato: Mermaid em git é a fonte; Figma/FigJam materializa para cliente via `generate_diagram`; entregável congelado segue no pipeline CLI; numeração ganha a regra de reserva.

**Architecture:** padrão vigente — categoria nova só no template do doc-profile + ADR própria (precedente `prototipo`/ADR-0013, sem tocar a ADR-0009 imutável); motor externo entra por adapters com fallback (ADR-0004); regra operacional da reserva na SKILL.md da spec-feature.

**Tech Stack:** Markdown PT-BR + YAML · zero código Python · zero dependência nova.

## Global Constraints

- Idioma PT-BR em docs e commits; commits `feat(018-visual): ...` com rodapé `Co-Authored-By: Claude <noreply@anthropic.com>`.
- Fonte canônica única: o papel do Figma é definido na ADR-0015; os demais arquivos linkam sem redefinir.
- **Nunca editar ADR-0009** (Accepted, imutável) — a ADR-0015 complementa.
- Fim de cada task = commit. Nenhum valor mágico novo; nada no `deps.toml`.

---

### Task 1: ADR-0015 + índice

**Files:**
- Create: `docs/adrs/ADR-0015-figma-camada-apresentacao.md`
- Modify: `docs/adrs/README.md` (linha nova no índice)

**Interfaces:**
- Produces: o arquivo ADR-0015 — T2/T3/T4 o referenciam por caminho relativo.

- [ ] **Step 1: Criar a ADR com este conteúdo:**

```markdown
# ADR-0015: Figma como camada de apresentação — Mermaid permanece a fonte da verdade

- **Status:** Accepted (2026-07-28, delta-018)
- **Data:** 2026-07-28
- **Supersedes:** — (complementa a ADR-0009, imutável — mesmo mecanismo da categoria `prototipo`, ADR-0013)
- **Superseded by:** —

## Context

A pesquisa do plano de upgrade (2026-07-28, 2 workflows com verificação adversarial) confrontou Figma e Mermaid para a documentação visual do framework. Resultados-chave: versionamento git e automação por agente são do Mermaid, por margem larga — o próprio caminho oficial do Figma prova (o `generate_diagram` do Figma MCP **só aceita Mermaid como input**, gera só em FigJam, ~6 tipos, sem ajuste fino); a qualidade visual para cliente é do Figma/FigJam, por margem menor que o senso comum (o claim "Mermaid perde por não ter ícones cloud" foi refutado — architecture-beta tem 200k+ ícones iconify); o C4 do Mermaid é experimental (confirmado). Três alternativas reais:

**1 — Figma como fonte principal.** Não se sustenta: quebra o versionamento git (regra de ouro do repo), a automação por agente e o pipeline headless do entregável congelado — e até o caminho oficial do Figma consome Mermaid como fonte.

**2 — Só Mermaid, sem camada Figma.** Mantém o status quo; renuncia ao acabamento de apresentação que stakeholder de contrato espera (validado nos projetos IMEX).

**3 — Híbrido unidirecional.** Mermaid em git como única fonte; Figma/FigJam como camada de **apresentação a cliente** (categoria `apresentacao` do doc-profile), materializada do `.mmd` via `generate_diagram` + retoque manual; entregável congelado segue no pipeline CLI; C4 segue no Structurizr (tabela da ADR-0009).

## Decision

Adotamos a **3**, com o fluxo deliberadamente unidirecional: o `.mmd` muda → re-materializa; edição feita no Figma **nunca retorna ao git como fonte** — em divergência, o `.mmd` governa. A categoria `apresentacao` entra no template do doc-profile como opcional (`obrigatorio: false`), e o Figma MCP entra nos adapters como motor opcional com fallback (ADR-0004): ausente/não autenticado → pipeline CLI com 1 linha de aviso.

Renunciamos à 1 pelos três vetos acima (git, automação, headless); à 2 porque a camada custa pouco (um toggle + um contrato) e cobre um gap real de apresentação. Renunciamos também ao round-trip Figma→git: sincronização bidirecional criaria segunda fonte da verdade — exatamente o que a regra de ouro proíbe.

**Limitações registradas:** (a) `generate_diagram` é beta e "will eventually be a usage-based paid feature" — fora do caminho crítico por design; pendência de reavaliação com gatilho no preço (DT roteado no archive da delta-018); (b) tipos de `.mmd` não suportados (~6 aceitos) → fallback render CLI + imagem colada no FigJam; (c) **não verificado** (fonte única, 2026-07-28): FigJam sem export SVG confiável — se o cliente exigir acabamento FigJam no documento congelado, o caminho é retoque/export manual; verificar na primeira materialização real.

## Consequences

**Fica mais fácil:** apresentação com acabamento para stakeholder sem abrir mão do git como fonte; o agente automatiza a materialização (Mermaid é o input que o MCP aceita); nada muda para projeto que não declara a categoria.

**Fica mais difícil:** um motor remoto a mais na tabela de adapters (verificação datada, R34) — e ele é beta com preço futuro; a materialização pode divergir do fonte até alguém re-materializar (mitigado pela regra "o `.mmd` governa"); o retoque manual não é reprodutível — aceito por ser camada de apresentação, nunca contrato.
```

- [ ] **Step 2: Índice** — em `docs/adrs/README.md`, após a linha da 0014, inserir:

```markdown
| [0015](ADR-0015-figma-camada-apresentacao.md) | Figma como camada de apresentação — Mermaid permanece a fonte da verdade | Accepted | 2026-07-28 |
```

- [ ] **Step 3: Verificar e commitar**

Run: `python3 skills/guarding-doc-integrity/scripts/validate_integrity.py .`
Expected: PASS, exit 0.

```bash
git add docs/adrs/ && git commit -m "feat(018-visual): ADR-0015 — Figma camada de apresentação, Mermaid fonte da verdade"
```

---

### Task 2: categoria `apresentacao` no doc-profile + espelhos do ciclo

**Files:**
- Modify: `skills/projeto-init/references/templates/doc-profile.yaml` (linha na lista de ferramentas do cabeçalho + linha no bloco `artefatos:`)
- Modify: `skills/spec-feature/references/cycle.md` (linha 40 — frase "A ferramenta segue a categoria")
- Modify: `skills/spec-feature/SKILL.md` (linha 33 — regra de numeração ganha a reserva do R3)

**Interfaces:**
- Consumes: caminho `docs/adrs/ADR-0015-figma-camada-apresentacao.md` (Task 1).

- [ ] **Step 1: doc-profile.yaml** — no comentário de ferramentas do cabeçalho (após a linha do `excalidraw`), inserir:

```yaml
#   figma-figjam materializa .mmd para apresentação a cliente via generate_diagram (MCP) [opcional]
```

No bloco `artefatos:`, após a linha `prototipo:`, inserir:

```yaml
  apresentacao: { obrigatorio: false }   # ferramenta: figma-figjam — camada de APRESENTAÇÃO a cliente (delta-018, ADR-0015): materializa o .mmd fonte via generate_diagram + retoque; unidirecional, o .mmd governa; nunca entra no caminho do entregável congelado
```

- [ ] **Step 2: cycle.md linha 40** — acrescentar ao final da frase (antes de "Não reaproveite"): `; apresentação a cliente → Figma/FigJam materializado do Mermaid fonte (ADR-0015, unidirecional)`. A frase "Não reaproveite diagrama pronto de outra categoria" permanece intacta.

- [ ] **Step 3: SKILL.md linha 33** — após "— **global ao repositório, nunca reinicia**", acrescentar: `(reserva explícita do usuário pode saltar/consumir um número, citada no spec — R5)`.

- [ ] **Step 4: Verificar e commitar**

Run: `python3 -c "import yaml; yaml.safe_load(open('skills/projeto-init/references/templates/doc-profile.yaml')); print('yaml ok')" && python3 skills/guarding-doc-integrity/scripts/validate_integrity.py .`
Expected: `yaml ok` + PASS. (Sem módulo yaml no host: validar por leitura e registrar.)

```bash
git add skills/projeto-init/ skills/spec-feature/ && git commit -m "feat(018-visual): categoria apresentacao no doc-profile; espelhos no ciclo e regra de reserva na SKILL"
```

---

### Task 3: Figma MCP nos adapters (contrato + política de versões)

**Files:**
- Modify: `skills/spec-feature/references/adapters.md` (linha na tabela de contrato + seção curta + linha na política de versões)

**Interfaces:**
- Consumes: ADR-0015 (Task 1); padrão da seção graphify (delta-016) como modelo.

- [ ] **Step 1: tabela de contrato** — após a linha do graphify, inserir:

```markdown
| apresentação a cliente (categoria `apresentacao`) — opcional | Figma MCP (`generate_diagram`, serviço remoto) | `generate_diagram` é beta e "will eventually be a usage-based paid feature"; só FigJam, ~6 tipos de `.mmd` |
```

- [ ] **Step 2: seção nova** — após a seção "## graphify", antes de "## Política de dependência":

```markdown
## Figma MCP (apresentação a cliente — delta-018, opcional)

Materializa o `.mmd` fonte no FigJam para acabamento de apresentação (categoria `apresentacao` do doc-profile — ADR-0015). **Unidirecional por design:** o `.mmd` em git é a única fonte; edição no Figma nunca retorna; em divergência, o `.mmd` governa e re-materializa.

- **Invocação:** `generate_diagram` com o conteúdo do `.mmd` versionado; retoque manual depois, só na cópia de apresentação. Tipo de `.mmd` não suportado (~6 aceitos) → render CLI + imagem colada no FigJam.
- **Fora do caminho crítico:** o entregável congelado (doc-entregavel) segue exclusivamente no pipeline CLI — a camada Figma nunca entra no export assinável.
- **Fallback (MCP ausente/não autenticado ou categoria não declarada):** fluxo atual com no máximo 1 linha de aviso (RNF2).
```

- [ ] **Step 3: política de versões** — após a linha do graphify na tabela de pins, inserir:

```markdown
| Figma MCP (`generate_diagram`) | n/a — serviço remoto (beta, sem versão pinável) | acompanhar anúncio de preço (gatilho no DT roteado pela delta-018) | 2026-07-28 (contrato pela doc primária do MCP) | opcional com degradação total: ausente, o pipeline CLI cobre; breaking/preço → reavaliar a categoria |
```

- [ ] **Step 4: Verificar e commitar**

Run: `python3 skills/guarding-doc-integrity/scripts/validate_integrity.py .`
Expected: PASS.

```bash
git add skills/spec-feature/references/adapters.md && git commit -m "feat(018-visual): Figma MCP nos adapters — contrato, fallback e política sem pin (serviço remoto)"
```

---

### Task 4: doc-entregavel + CHANGELOG + HANDOFF — dep: T1, T2, T3

**Files:**
- Modify: `skills/doc-entregavel/SKILL.md` (nota do papel do Figma na seção "## Processo")
- Modify: `CHANGELOG.md` (`[Não lançado]`) · `HANDOFF.md` (seção Agora)

- [ ] **Step 1: doc-entregavel/SKILL.md** — ao final da seção "## Processo", inserir o parágrafo:

```markdown
**Figma/FigJam (ADR-0015):** camada de apresentação a cliente — nunca entra no caminho do export. O documento congelado renderiza sempre pelo pipeline CLI desta skill; se o cliente exigir acabamento FigJam no congelado, o caminho é retoque/export manual (limitação não verificada — ver ADR-0015). Contrato e fallback do motor: `spec-feature/references/adapters.md`, seção Figma MCP.
```

- [ ] **Step 2: CHANGELOG** — sob `## [Não lançado]`:

```markdown
### Adicionado
- **Figma/FigJam como camada de apresentação a cliente** (delta-018, R1 — ADR-0015): categoria `apresentacao` no doc-profile; fluxo unidirecional Mermaid fonte → `generate_diagram` → retoque (o `.mmd` governa); tipo não suportado → render CLI + imagem no FigJam.
- **Figma MCP nos adapters** (delta-018, R2): linha de contrato com ponto sensível (beta → pago), seção com fallback (RNF2) e política sem pin ("n/a — serviço remoto", verificação datada); entregável congelado permanece exclusivo do pipeline CLI, documentado também na `doc-entregavel`.
- **Reserva explícita de número de delta** (delta-018, R3 — MUDA R5 no archive): o usuário pode reservar/saltar um número, com a reserva citada nos specs (caso real: 017 reservada para a Fase 4/Jira, preservando o gatilho da ADR-0012).
- **ADR-0015**: veredito híbrido com renúncias (Figma como fonte; round-trip) e limitações registradas (beta/preço → DT; export FigJam **não verificado**).
```

- [ ] **Step 3: HANDOFF seção Agora** — substituir o item da delta-018 (ou a linha vigente de "próxima") por: delta-018 implementada na `feat/018-visual` (perfil enxuto — 1º dogfood do R36); próxima: review fundido → PR único → archive (R45–R46 + MUDA R5, DT novo do preço, tag v0.13.0).

- [ ] **Step 4: Verificação completa e commit**

Run: `python3 skills/spec-feature/scripts/check_cycle.py --selftest && python3 skills/guarding-doc-integrity/scripts/validate_integrity.py --selftest && python3 skills/guarding-doc-integrity/scripts/validate_integrity.py . && python3 skills/spec-feature/scripts/check_cycle.py specs/018-visual; echo exit=$?`
Expected: selftests OK, PASS, gate LIBERADO ou só achados BAIXO (C8 BAIXO da dispensa é o esperado), exit 0.

```bash
git add skills/doc-entregavel/ CHANGELOG.md HANDOFF.md && git commit -m "docs(018-visual): papel do Figma na doc-entregavel; CHANGELOG e HANDOFF"
```

---

## Pós-implement (fases seguintes do ciclo — não são tasks deste plano)

1. **tasks**: `tasks.md` com `dep:` (T4 dep T1–T3); test-plan dispensado (cabeçalho).
2. **analyze**: gate + juízo; C8 deve reportar BAIXO (dispensa sancionada pelo perfil aprovado).
3. **implement → review fundido num único subagente (perfil enxuto, R35/R36) → PR único (estimativa ~325 linhas < limiar; sem split) → archive** (consolida R45–R46 + MUDA R5; roteia a pendência do preço como DT-NNN; tag `v0.13.0`).
