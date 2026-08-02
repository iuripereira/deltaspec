# Analyze — delta-025 · 2026-08-02

Metade mecânica: `check_cycle.py specs/025-pin-graphify` → **LIBERADO**, C1–C10 sem achados (aceite, cobertura, estado, archive, tamanho do TRUTH, pendência roteada, split de PR, plano de testes, grafo de tasks, convergência). Metade de juízo (checks 3 e 5) abaixo.

| # | Severidade | Onde | Inconsistência | Ação sugerida |
|---|---|---|---|---|
| 1 | MÉDIO | tasks.md T4 · plan.md Task 4 | Task final registrava só o `CHANGELOG.md`, sem o `HANDOFF.md` — a regra canônica do CLAUDE.md exige que toda mudança relevante atualize a doc mais próxima **e o HANDOFF** no mesmo change; o padrão das deltas 023 e 024 é a task única "Registrar no CHANGELOG e no HANDOFF" | **Corrigido nesta fase**: T4 passou a listar `HANDOFF.md` nos arquivos e o plano ganhou o Step 2 com a linha de diário |
| 2 | BAIXO | spec.md R2, R3 | O contrato do graphify ficava repartido entre o MUDA R44 e dois Rn novos: backend registrado e arquivo inexistente são parte do contrato do motor e cabiam como cenários do próprio R44 | **Corrigido nesta fase**: R2 e R3 fundidos no bloco MUDA R44 — a delta passa a ter um requisito só e não consome número novo no TRUTH. Decisão do usuário em 2026-08-02, com a premissa "quanto menos artefato gerar ou derivar, melhor para gerenciar"; a renúncia aos Rn próprios está em "Fora de escopo" |

**Verificações de juízo que passaram:**

- **Check 3 (spec × plan):** o resumo do plan cobre R1 — o mesmo da spec. Nada no plano sem base na spec; plano não contradiz nenhum cenário de aceite.
- **Check 4 (TRUTH.md):** o bloco MUDA R44 repete os quatro cenários vigentes (consulta com `arquivo:linha` + tags; contrato do adapter; eixo Spec do review; fallback) — três byte-idênticos, o do contrato do adapter alterado de propósito — e acrescenta os novos. Nenhum cenário se perde na consolidação mecânica. **Atenção (corrigido após o review):** a preferência por `--code-only` do cenário vigente **não migra — ela é revertida**. Os fatos ("determinístico, zero LLM") sobrevivem no cenário de modos, mas a preferência normativa deixa de existir, e isso é reversão de decisão de ADR `Accepted` — daí a trilha de supersede exigida pelo CRÍTICO-1 do review. Nenhum cenário novo duplica requisito vigente: nenhum Rn do TRUTH é dono do bloco `motores` do `doc-profile.yaml` (o R38 governa a categoria `apresentacao`, outra seção do arquivo). Após a fusão, a delta **não consome número novo** no TRUTH.
- **Check 5 (regras canônicas):** CHANGELOG em PT-BR; nenhuma sobrescrita de arquivo existente (as três tasks editam, não recriam); nenhum caminho absoluto de máquina introduzido (`grep -rn "/home/iuri" specs/025-pin-graphify/ docs/adrs/ADR-0022*.md` → vazio); versão continua ancorada na tag git; artefatos somam 73 linhas contra o merge-base, muito abaixo do limiar canônico de PR — sem split (C7 não disparou).
- **TDD:** dispensa registrada no `plan.md` com justificativa por task (tipo `tooling`, coluna `tdd: recomendado`) — nenhuma task escreve código; a verificação é `grep` de âncora mais os gates existentes.

**Veredito:** LIBERADO

Os dois achados foram corrigidos na própria fase. Gate mecânico re-executado após as correções: LIBERADO, C1–C10 limpos.

---

## Apêndice — review em dois eixos (2026-08-02)

Perfil `completo` → eixos independentes em subagentes paralelos (R35), cada um cego ao contexto do outro. Eixo Spec: **APROVADO COM RESSALVAS**, 8/8 cenários ATENDE. Eixo Qualidade: delete-list de 14 cortes, ~3.700 caracteres.

**Convergente (apontado pelos dois eixos — tratado antes do PR, sempre):**

| Achado | Tratamento |
|---|---|
| Bullet do DT-023 no `HANDOFF.md` é escopo de outra branch (PR #102); o `DEBT.md` desta branch não tem DT-023, então o link fica oco | Removido |
| `analyze.md` se contradizia (citava R1/R2/R3 depois da fusão; descrevia a reversão como "migração") | Check 3 e Check 4 reescritos |

**CRÍTICO do eixo Spec — bloqueava o merge, corrigido:**

Derrubar a preferência por `--code-only` reverte a decisão **4-b da ADR-0014**, que está `Accepted` e portanto imutável — a regra canônica exige nova ADR com `Supersedes` e a antiga marcada `Superseded by`. Nada disso existia. Corrigido no padrão de supersede parcial da ADR-0021/ADR-0007: `Supersedes` na ADR-0022, `Superseded by` na ADR-0014 (só a cláusula), linha do índice atualizada, e a reversão promovida a **decisão 0-b** da ADR-0022 com a alternativa renunciada registrada. Verificado pelo CT8.

**Demais achados do eixo Spec, corrigidos:** regra do modo duplicada na `descoberta/SKILL.md` contra a instrução do próprio plano (MÉDIO-2); link markdown da ADR-0014 no adapter (BAIXO-1); critério da CT1 que descrevia um mundo abolido pela delta (BAIXO-2); enumeração de backends no YAML fora do alcance do gate (BAIXO-3); 3 cenários sem CT, agora cobertos pela CT7 (BAIXO-4).

**Delete-list aplicada:** cortes 1–14, com duas recusas justificadas pelo próprio eixo — a ADR-0022 não encolhe (é a dona canônica do porquê; encolher quebraria o mecanismo de referência) e o bullet do que o `--code-only` cega fica (parece justificativa, é instrução operacional que evita a escolha errada antes de rodar). O corte de maior consequência: o cenário `publico.cliente: true` saiu do R44 — é instância da regra universal "campo vazio → pare e pergunte, nunca assuma default", escrita duas linhas acima, e cenário cortado pesa para sempre no TRUTH. **8 → 7 cenários.**

**BAIXO-5 (informativo, sem ação):** os números da execução externa (235 docs, 1.053 nós, 16 de 27 fantasmas, 2,7M tokens) não são verificáveis deste repo — vêm do `imex-travelplanner`, sem log commitado. O enquadramento é honesto: o adapter data e nomeia a execução, não alega teste automatizado.

Review: convergentes tratados / recusas justificadas — 2026-08-02
