# Analyze — delta-016 · 2026-07-28
| # | Severidade | Onde | Inconsistência | Ação sugerida |
|---|---|---|---|---|
| 1 | BAIXO | specs/016-harness | 568 linhas adicionadas (limiar 500) — C7 | split R17: PR só dos artefatos primeiro (branch `docs/016-harness`), implementação em PR separado |
| 2 | MÉDIO | plan.md Task 2 | edição de `specs/_archive/*/tasks.md` (higiene de checkbox exigida pelo C10) — `_archive/` é histórico | sancionada: precedente do C6 (roteamento em spec arquivado), trabalho comprovadamente concluído nos merges; conferir no diff que só `- [ ] T` vira `- [x] T` |

Checks 3 e 5 (juízo humano, rodados nesta sessão): **3 — scope creep:** o resumo do plan cobre R1–R6 sem item fora da Fase 3 (fidelidade verificada também por lente adversarial dedicada no specify); a higiene do T2 é consequência direta do C10 aprovado no clarify, não escopo novo. **5 — regra canônica:** split R17 será honrado (achado 1); sem clobber; CHANGELOG PT-BR; versão por tag; fonte canônica única preservada (harness.md dono novo, demais linkam). Sem achado CRÍTICO.

Ressalvas aceitas: 2026-07-28 — achado 1 — a ação sugerida é executada nesta sessão (split); achado 2 — decisão tomada no clarify (C10, ADR-0014), diff conferido na Task 2.

**Veredito:** LIBERADO COM RESSALVAS

Review (2 eixos, R35): eixo Spec sem lacuna (20/20 cenários); delete-list do eixo Qualidade — 2 tratados (Kahn→graphlib; bullet da trilha no harness.md vira link), 2 recusados com justificativa: reusar PENDENCIA_ABERTA no C10 (a restrição `T\d+` é a precisão que o cenário exige — checkbox de prosa não é task) e cortar o footprint do graphify (mandado pela spec R6/ADR-0014, decisão de clarify) — 2026-07-28
