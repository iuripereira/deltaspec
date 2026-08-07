# Analyze — delta-017 · 2026-08-07
| # | Severidade | Onde | Inconsistência | Ação sugerida |
|---|---|---|---|---|

**Veredito:** LIBERADO

Registro do gate: metade mecânica (`check_cycle.py specs/017-jira-tickets`) LIBERADO sem achados — C1 aceite, C2 cobertura (R1→T3/T5, R2→T1/T2, R3→T4; T6/T7 mapeados), C8 test-plan (CT1–CT8, todo Rn com ≥1 caso), C9 grafo (deps existentes, acíclico), C7 sem estouro do limiar de PR. Dois ALTOs de sintaxe no `cobre:` do test-plan (parêntese na referência) corrigidos antes deste registro.

Juízo (checks 3 e 5 do analyze.md):
- **Consistência spec × plan:** o resumo cobre exatamente R1/R2/R3; sem scope creep — o módulo comum `projecao.py` e o C11 estendido derivam de decisão registrada no clarify e do cenário de gate do R1.
- **TRUTH.md:** o MUDA R52 repete integralmente os 5 cenários vigentes e substitui só a forma do dialeto — nada se perde no archive.
- **Regras canônicas:** PT-BR nos scripts ✓ · zero dependência nova (stdlib + PyYAML/ADR-0023) ✓ · sem rede nos scripts (R52) ✓ · sem caminho absoluto de máquina ✓ · template alterado (doc-profile) com fixtures atualizadas na mesma task (T5) ✓.
