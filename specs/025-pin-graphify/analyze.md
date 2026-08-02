# Analyze — delta-025 · 2026-08-02

Metade mecânica: `check_cycle.py specs/025-pin-graphify` → **LIBERADO**, C1–C10 sem achados (aceite, cobertura, estado, archive, tamanho do TRUTH, pendência roteada, split de PR, plano de testes, grafo de tasks, convergência). Metade de juízo (checks 3 e 5) abaixo.

| # | Severidade | Onde | Inconsistência | Ação sugerida |
|---|---|---|---|---|
| 1 | MÉDIO | tasks.md T4 · plan.md Task 4 | Task final registrava só o `CHANGELOG.md`, sem o `HANDOFF.md` — a regra canônica do CLAUDE.md exige que toda mudança relevante atualize a doc mais próxima **e o HANDOFF** no mesmo change; o padrão das deltas 023 e 024 é a task única "Registrar no CHANGELOG e no HANDOFF" | **Corrigido nesta fase**: T4 passou a listar `HANDOFF.md` nos arquivos e o plano ganhou o Step 2 com a linha de diário |
| 2 | BAIXO | spec.md R2 | O contrato do graphify fica repartido entre o MUDA R44 e um Rn novo: o campo `motores.graphify_backend` é parte do contrato do motor e poderia ser mais um cenário do MUDA R44, em vez de requisito próprio | Decisão do usuário. Mantido como Rn próprio porque a fronteira de dado (o que sai da máquina) é preocupação distinta de "motor opcional de contexto" e ganha ID citável independente; o custo é ler dois requisitos para ter o contrato inteiro |

**Verificações de juízo que passaram:**

- **Check 3 (spec × plan):** o resumo do plan cobre R1, R2, R3 — os mesmos da spec. Nada no plano sem base na spec: a proibição de `graphify claude install` (T1 Step 1) está no cenário 2 do R1; o campo do perfil (T2) está nos cenários 2 e 3 do R2. Plano não contradiz nenhum cenário de aceite.
- **Check 4 (TRUTH.md):** o bloco MUDA R44 repete os quatro cenários vigentes (consulta com `arquivo:linha` + tags; contrato do adapter; eixo Spec do review; fallback) e acrescenta o quinto — nenhum cenário se perde na consolidação mecânica. A preferência por `--code-only`, que vivia no cenário 2, migra para o cenário novo com o escopo explicitado, sem sumir. R2 e R3 não duplicam requisito vigente: nenhum Rn do TRUTH é dono do bloco `motores` do `doc-profile.yaml` (o R38 governa a categoria `apresentacao`, outra seção do arquivo).
- **Check 5 (regras canônicas):** CHANGELOG em PT-BR; nenhuma sobrescrita de arquivo existente (as três tasks editam, não recriam); nenhum caminho absoluto de máquina introduzido (`grep -rn "/home/iuri" specs/025-pin-graphify/ docs/adrs/ADR-0022*.md` → vazio); versão continua ancorada na tag git; artefatos somam 73 linhas contra o merge-base, muito abaixo do limiar canônico de PR — sem split (C7 não disparou).
- **TDD:** dispensa registrada no `plan.md` com justificativa por task (tipo `tooling`, coluna `tdd: recomendado`) — nenhuma task escreve código; a verificação é `grep` de âncora mais os gates existentes.

**Veredito:** LIBERADO COM RESSALVAS

Ressalva pendente: achado 2 (fragmentação R44 × R2) aguarda decisão do usuário — o achado 1 já foi corrigido.
