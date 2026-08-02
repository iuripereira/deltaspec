<!-- resumo deltaspec · ≤15 linhas · única parte do plano lida pelo analyze e pelo humano -->
**Objetivo:** Levar ao contrato do adapter o que a primeira execução real do graphify (0.9.32, imex-travelplanner, 2026-08-02) ensinou: pin verificado, escopo do `--code-only`, backend de docs registrado no perfil e claim sobre arquivo inexistente. **Cobre:** R1 (bloco único MUDA R44 — da delta-025) **Decisões duráveis → ADRs:** ADR-0022 (gravada no clarify) **Riscos assumidos:** a recomendação de backend é datada e envelhece com o upstream (release quase diária, bus factor = 1); o campo novo do `doc-profile.yaml` precisa propagar ao template distribuído, dívida já registrada no DT-022.

**Dispensa de TDD (tipo `tooling`, coluna `tdd: recomendado`):** nenhuma task escreve código — a delta muda 4 arquivos de documentação/contrato e um YAML de template. Não há função a testar; a verificação de cada task é `grep` de âncora + os gates existentes (`validate_integrity.py`, `check_cycle.py`), que já rodam no CI. Dispensa registrada por task abaixo.

---

# Pin do graphify verificado por execução real — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Atualizar o contrato do graphify em `adapters.md`, o schema do `doc-profile.yaml` e a ponte na `descoberta` para refletir a primeira adoção real, sem tornar o motor obrigatório.

**Architecture:** Mudança só de artefatos declarativos. A seção graphify do `adapters.md` é a fonte canônica do contrato; `descoberta/SKILL.md` e o template do `doc-profile.yaml` **referenciam**, nunca reimplementam o texto da regra (regra de ouro: fonte canônica única). O pin vive exclusivamente na tabela de política de dependência.

**Tech Stack:** Markdown + YAML. Zero código novo. Verificação por `grep` e pelos gates em Python já existentes.

## Global Constraints

- Idioma PT-BR em documentação e commits (CLAUDE.md).
- Fonte canônica única: valor concreto vive no arquivo dono; o resto linka. O pin `0.9.32` aparece **uma vez**, na tabela de política de `adapters.md`.
- Nenhuma linha nova pode citar caminho absoluto de máquina — o job `ci` reprova o PR.
- O graphify segue **opcional**: `motores.graphify: false` continua o default do template (ADR-0014).
- Commits Conventional Commits com escopo da delta: `feat(025-pin-graphify):`.

---

### Task 1: Contrato do graphify em `adapters.md`

**Files:**
- Modify: `skills/spec-feature/references/adapters.md:50-68` (seção graphify) e `:86` (linha da tabela de política)

**Interfaces:**
- Consumes: nada (task livre).
- Produces: a seção graphify canônica que a T3 referencia por link, e a linha de pin `0.9.32 · verificado em 2026-08-02` que nenhuma outra task duplica.

- [x] **Step 1: Reescrever o bullet "Habilitação dupla e manual"** — acrescentar que a proibição vale também para o alvo por plataforma `graphify claude install` (verificado: escreve seção no CLAUDE.md + hook `PreToolUse`), e mover a preferência por `--code-only` para o bullet novo do Step 2.

- [x] **Step 2: Inserir o bullet "Modos e o que cada um enxerga"** (cobre R1 — escopo de modo), com o texto:

```markdown
- **Modos — escolha informada, não default:** `--code-only` entrega AST local por
  tree-sitter (determinístico, zero LLM, nada sai da máquina) e **cega todo
  arquivo não-código** (`.md`, PDF, DOCX, XLSX, imagem são pulados; a tag
  `AMBIGUOUS` nunca aparece). Projeto-alvo cujo valor está na documentação
  precisa do modo completo — leia o bullet seguinte antes de rodá-lo.
```

- [x] **Step 3: Inserir o bullet "Backend do modo docs"** (cobre R1 — backend registrado), com o texto:

```markdown
- **Backend do modo docs (exige LLM):** prefira os dois que **não** criam
  fronteira nova de confiança — `claude-cli` (roteia pelo CLI já autenticado,
  cobrado na assinatura, sem API key) e `ollama` (`localhost`, nada sai da
  máquina). API paga só como decisão consciente. A escolha é **registrada** em
  `motores.graphify_backend` do `doc-profile.yaml` (ADR-0022); campo vazio com
  indexação de docs pedida → **pare e pergunte**, nunca assuma um default.
  Projeto com `publico.cliente: true`: a escolha é do usuário, sempre.
```

- [x] **Step 4: Inserir o bullet "Arquivo citado que não existe"** (cobre R1 — arquivo inexistente), com o texto:

```markdown
- **Arquivo citado que não existe:** grafo que indexou documentação cita código
  descrito em spec mas ainda não escrito. Antes de o claim entrar em artefato do
  ciclo, confira a existência do arquivo — inexistente marca o claim como
  `inferido` (código planejado), nunca `confirmado`.
```

- [x] **Step 5: Atualizar a linha do graphify na tabela de política de dependência** (`:86`), substituindo `— (não testada — contrato definido pela doc upstream)` e a data por:

| coluna | valor |
|---|---|
| Versão testada | `0.9.32` |
| Faixa aceita | pin na testada — release quase diária, bus factor = 1 |
| Verificado em | `2026-08-02` (execução real: `imex-travelplanner`, 235 docs, 1.053 nós) |

- [x] **Step 6: Verificar**

Run: `grep -c "graphify_backend\|AMBIGUOUS nunca aparece\|0.9.32" skills/spec-feature/references/adapters.md`
Expected: ≥ 3 (um por bullet novo + o pin)

Run: `python3 skills/guarding-doc-integrity/scripts/validate_integrity.py .`
Expected: `RESULTADO: PASS`

- [x] **Step 7: Commit**

```bash
git add skills/spec-feature/references/adapters.md
git commit -m "feat(025-pin-graphify): pin 0.9.32, escopo do --code-only e backend de docs no contrato"
```

---

### Task 2: Campo `graphify_backend` no template do `doc-profile.yaml`

**Files:**
- Modify: `skills/projeto-init/references/templates/doc-profile.yaml:44-45` (bloco `motores`)

**Interfaces:**
- Consumes: nada (task livre — arquivo distinto da T1, paralelizável com ela).
- Produces: o campo `motores.graphify_backend`, citado pela T1 Step 3 e pela T3.

- [x] **Step 1: Acrescentar o campo ao bloco `motores`**

```yaml
motores:
  graphify: false          # true = descoberta/specify/plan/review consultam o grafo de codebase (requer binário instalado; NUNCA use `graphify install`)
  graphify_backend: ""     # obrigatório quando a indexação inclui docs (exige LLM): claude-cli | ollama | gemini | openai | ... — vazio com docs pedidos faz a IA parar e perguntar (ADR-0022); dispensável em --code-only
```

- [x] **Step 2: Verificar que o YAML segue válido**

Run: `python3 -c "import yaml,sys; d=yaml.safe_load(open('skills/projeto-init/references/templates/doc-profile.yaml')); print(d['motores'])"`
Expected: `{'graphify': False, 'graphify_backend': ''}`

- [x] **Step 3: Commit**

```bash
git add skills/projeto-init/references/templates/doc-profile.yaml
git commit -m "feat(025-pin-graphify): campo motores.graphify_backend no template do doc-profile"
```

---

### Task 3 (dep: T1): Ponte da `descoberta` aponta para o contrato novo

**Files:**
- Modify: `skills/descoberta/SKILL.md:30`

**Interfaces:**
- Consumes: a seção graphify da T1 (o texto da regra vive lá; aqui só o ponteiro) e o nome do campo da T2.
- Produces: nada que outra task consuma.

- [x] **Step 1: Reescrever a linha 30** — hoje ela cita só `motores.graphify: true`. Passa a citar também o backend e o modo, **sem repetir a regra** (fonte canônica única):

```markdown
Projeto com graphify habilitado (doc-profile `motores.graphify: true`): as consultas ao grafo de codebase entram como insumo da mineração com fonte `arquivo:linha` e tag mapeada no modelo de confiança. Mineração de **documentação** exige o modo completo e um backend declarado em `motores.graphify_backend` — contrato, escolha de modo, avisos de instalação e fallback na seção graphify de `spec-feature/references/adapters.md`. Ausente → mineração atual, com 1 linha de aviso.
```

- [x] **Step 2: Verificar que a skill aponta, não duplica**

Run: `grep -c "claude-cli\|ollama\|0.9.32" skills/descoberta/SKILL.md`
Expected: `0` — nenhum valor concreto materializado fora do dono

Run: `python3 skills/guarding-doc-integrity/scripts/validate_integrity.py .`
Expected: `RESULTADO: PASS`

- [x] **Step 3: Commit**

```bash
git add skills/descoberta/SKILL.md
git commit -m "docs(025-pin-graphify): ponte da descoberta cita modo e backend do graphify"
```

---

### Task 4 (dep: T1, T2, T3): CHANGELOG e HANDOFF

**Files:**
- Modify: `CHANGELOG.md` (seção `## [Não lançado]`)
- Modify: `HANDOFF.md` (diário de bordo — regra canônica do CLAUDE.md: toda mudança relevante atualiza o HANDOFF no mesmo change)

**Interfaces:**
- Consumes: as mudanças das T1–T3.
- Produces: nada.

- [x] **Step 1: Registrar sob `## [Não lançado]`**

```markdown
### Adicionado
- Campo `motores.graphify_backend` no template do `doc-profile.yaml`: registra o backend LLM usado na indexação de documentação (delta-025, ADR-0022).

### Mudado
- Contrato do graphify em `adapters.md`: pin verificado por execução real (0.9.32, 2026-08-02), escopo do `--code-only` explícito (cega arquivos não-código), backend de docs recomendado e registrado, e regra do arquivo citado inexistente (delta-025).
```

- [x] **Step 2: Registrar no `HANDOFF.md`** — uma linha no diário de bordo, no topo da lista datada, no padrão das deltas anteriores:

```markdown
- 2026-08-02 — **delta-025 (pin do graphify)**: primeira adoção real do motor (0.9.32, `imex-travelplanner`, 235 docs indexados via `claude-cli`). MUDA R44 (pin verificado + `--code-only` cega documentação), ADICIONA backend registrado em `motores.graphify_backend` e a regra do arquivo citado inexistente; renúncias na ADR-0022. Clarify entrevistado com o usuário — perfil `completo` aprovado.
```

- [x] **Step 3: Verificar**

Run: `python3 skills/spec-feature/scripts/check_cycle.py specs/025-pin-graphify`
Expected: sem CRÍTICO; C2 com todos os Rn cobertos

- [x] **Step 4: Commit**

```bash
git add CHANGELOG.md HANDOFF.md
git commit -m "docs(025-pin-graphify): CHANGELOG e HANDOFF da delta-025"
```
