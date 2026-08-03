# Analyze — delta-027 · 2026-08-02

Metade mecânica: `check_cycle.py specs/027-c3-links-nos-registros` → **LIBERADO COM RESSALVAS**, único achado o BAIXO do test-plan dispensado, que é a forma sancionada do perfil enxuto (R38).

| # | Severidade | Onde | Inconsistência | Ação sugerida |
|---|---|---|---|---|
| 1 | BAIXO | test-plan.md | dispensado no cabeçalho | Aceito: perfil enxuto aprovado pelo usuário em 2026-08-02; os 6 cenários do R1 mapeiam 1:1 nas fixtures do `--selftest` |

**Verificações de juízo que passaram:**

- **Check 3 (spec × plan):** o resumo do plan cobre R1 e só ele. Cada passo do plano sai de um cenário: os dois conjuntos e o default nomeado saem dos cenários 4–6, o corte do `../../` sai do cenário 7, a propagação ao template sai da consequência de a chave ser nova. Nada no plano sem base na spec, e nenhum cenário sem passo que o realize.
- **Check 4 (TRUTH.md) — conferido por comparação programática:** `MUDA R13` traz os **3 cenários vigentes byte-idênticos** e acrescenta 4. Zero perda; nenhum cenário vigente reescrito.
- **Check 5 (regras canônicas):** PT-BR em prosa e identificadores; o default do C3 vira constante nomeada (`EXCLUDE_LINKS_PADRAO`), não lista solta no meio da função; stdlib pura nesta skill (o PyYAML da ADR-0023 é do `check_cycle`, não deste script); nenhuma duplicação — a exclusão do C2 continua com um dono só e a do C3 ganha o seu, que é justamente o ponto. CHANGELOG é task explícita (T4).

**Escopo decidido com o usuário, não inferido (clarify de 2026-08-02, 2 decisões):** `specs/_archive/**` fica fora do C3 e o perfil é enxuto. A primeira decisão evita 13 achados em registro que a política (R47, e a guarda DT-006) proíbe corrigir; ela é do usuário porque tem contrapartida real — link de archive apodrece e ninguém saberá.

**Risco que o gate não mede:** a chave `exclude_links_globs` propaga por **default nomeado**, não por migração de manifesto. Projeto-alvo cujo histórico imutável não more em `_archive/`/`docs/adrs/` recebe achados na primeira execução — são links quebrados de verdade, mas chegam sem aviso. É a mesma classe do DT-025, que segue aberto; esta delta escolhe o default menos ruidoso, não resolve a propagação.

**Medição que sustenta o desenho (2026-08-02, mesma semântica do C3 — `path.parent / target`):** registros vivos e ADRs com **zero** link quebrado, então o check nasce verde e todo achado futuro é regressão real; `specs/_archive/**` com 13, todos fora de escopo por decisão; `DEBT.md` com **19** links no atalho `../../` do GitHub, que sem o corte do cenário 7 virariam 19 falsos FAIL na primeira execução.

**Veredito:** LIBERADO
