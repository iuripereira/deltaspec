# Tasks — delta-033
<!-- ordenado por dependência; cada task executável sem contexto extra (detalhe: plan.md).
     Arestas de bloqueio (delta-016): `(dep: Tn[, Tm])`. -->
- [ ] T1 — criar `itens.py`: dono canônico do formato de item, com continuação de linha e paradas · arquivos: skills/spec-feature/scripts/itens.py · cobre: R2 · verificação: python3 skills/spec-feature/scripts/itens.py --selftest
- [ ] T2 (dep: T1) — C2/C8/C9/C10 do `check_cycle.py` passam a iterar o módulo; `dep:` segue colado ao ID · arquivos: skills/spec-feature/scripts/check_cycle.py · cobre: R1 · verificação: python3 skills/spec-feature/scripts/check_cycle.py --selftest + varredura das deltas arquivadas sem mudança de veredito
- [ ] T3 (dep: T1) — `tickets.py` troca o `PADRAO_TASK` próprio pelo parser canônico, preservando o formato do tickets.md · arquivos: skills/spec-feature/scripts/tickets.py · cobre: R2 · verificação: python3 skills/spec-feature/scripts/tickets.py --selftest
- [ ] T4 — C1 acusa heading `###` fora da forma canônica em vez de perder o requisito em silêncio · arquivos: skills/spec-feature/scripts/check_cycle.py · cobre: R1 · verificação: python3 skills/spec-feature/scripts/check_cycle.py --selftest + 0 achado novo nas 32 deltas arquivadas
- [ ] T5 (dep: T2, T3, T4) — docs no mesmo change e quito do DT-001 · arquivos: DEBT.md, skills/spec-feature/references/analyze.md, CHANGELOG.md · cobre: R1, R2 · verificação: validate_integrity.py . → PASS e debito.py fila . → PASS
