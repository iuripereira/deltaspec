# Δ002 — tasks
<!-- ordenadas por dependência; detalhe executável no plan.md -->

- [x] T1 — C4 contra merge-base + selftest git real · arquivos: skills/spec-feature/scripts/check_cycle.py · cobre: R1, RNF1 · verificação: check_cycle.py --selftest (novo selftest_c4 falha antes, passa depois)
- [x] T2 — C6 pendência aberta em delta arquivada · arquivos: skills/spec-feature/scripts/check_cycle.py · cobre: R1, R2 · verificação: check_cycle.py --selftest (fixture C6)
- [x] T3 — saída do script declarada parcial · arquivos: skills/spec-feature/scripts/check_cycle.py · cobre: R1 · verificação: rodar check_cycle.py specs/002-gates e conferir título/nota (TDD dispensado: I/O de apresentação — justificativa no plan.md)
- [x] T4 — convenção checkbox no template + regras 6/7 do cycle.md + analyze.md + SKILL.md · arquivos: skills/spec-feature/references/templates/delta-spec.md, skills/spec-feature/references/cycle.md, skills/spec-feature/references/analyze.md, skills/spec-feature/SKILL.md · cobre: R2 · verificação: grep 'diff HEAD' skills/ vazio; grep C6 acha os 4 consumidores
- [x] T5 — grep de portabilidade ampliado no CI · arquivos: .github/workflows/ci.yml · cobre: RNF2 · verificação: grep novo roda local com zero ocorrência; job ci verde no PR
- [x] T6 — CHANGELOG + STATE.md (débitos resolvidos) · arquivos: CHANGELOG.md, STATE.md · cobre: infra · verificação: selftests + gate da delta sem ALTO/CRÍTICO
