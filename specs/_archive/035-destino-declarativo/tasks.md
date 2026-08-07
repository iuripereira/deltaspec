# Tasks — delta-035
<!-- ordenado por dependência; cada task executável sem contexto extra (detalhe: plan.md).
     Arestas de bloqueio (delta-016): `(dep: Tn[, Tm])`. -->
- [x] T1 — `ler_projeto_jira` vira dono único no `projecao.py`, com degradação por aviso em perfil ilegível e em PyYAML ausente · arquivos: skills/handoff/scripts/projecao.py · cobre: R1 · verificação: python3 skills/handoff/scripts/projecao.py
- [x] T2 (dep: T1) — `debito.py exportar` lê o perfil, com `--projeto` sobrepondo, e a mensagem de omissão nomeia o perfil em vez da flag · arquivos: skills/handoff/scripts/debito.py · cobre: R1 · verificação: python3 skills/handoff/scripts/debito.py --selftest + E2E dos 3 cenários (perfil sem flag → dialeto Jira; sem perfil nem flag → só tickets-gh.sh; flag contra perfil → flag vence)
- [x] T3 (dep: T1) — `tickets.py` perde a cópia própria da função e o `import yaml` que virou órfão · arquivos: skills/spec-feature/scripts/tickets.py · cobre: R1 · verificação: python3 skills/spec-feature/scripts/tickets.py --selftest
- [x] T4 (dep: T2, T3) — docs no mesmo change, consolidação do MUDA R52 e quito do DT-033 · arquivos: specs/TRUTH.md, DEBT.md, CHANGELOG.md, HANDOFF.md · cobre: R1 · verificação: validate_integrity.py . → PASS e check_cycle.py na delta → sem ALTO/CRÍTICO
