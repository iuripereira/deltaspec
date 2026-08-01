# Tasks — delta-023
<!-- ordenado por dependência; cada task executável sem contexto extra.
     Arestas de bloqueio (delta-016): `(dep: Tn[, Tm])` logo após o ID — task sem
     `dep:` é livre. Duas tasks sem caminho entre si no grafo são paralelizáveis
     (execução por worktree: cycle.md); o C9 valida existência e aciclicidade.
     Arquivo sem nenhum `dep:` = cadeia linear implícita pela ordem (retrocompatível). -->
- [ ] T1 — Escrever `debito.py` por TDD: parser posicional, validação, score, churn/stale, exportar, diff, `--selftest` com fixture de regressão de prosa · arquivos: skills/handoff/scripts/debito.py · cobre: R2 · verificação: `python3 skills/handoff/scripts/debito.py --selftest` sai 0
- [ ] T2 — Escrever a política de fila (A override · B trilha · C aging · D aceitação) + matriz de decisão + contrato da projeção · arquivos: skills/handoff/references/debito.md · cobre: R1 · verificação: as 4 seções existem e nenhum limiar numérico é materializado fora do script
- [ ] T3 — Escrever ADR-0020 (modelo) e ADR-0021 (projeção, supersede a 0007), marcar a 0007 e atualizar o índice · arquivos: docs/adrs/ADR-0020-modelo-de-divida-tecnica.md, docs/adrs/ADR-0021-projecao-de-tickets.md, docs/adrs/ADR-0015-figma-camada-apresentacao.md, docs/adrs/README.md · cobre: R3 · verificação: `grep "Superseded by: \[ADR-0021\]" docs/adrs/ADR-0007-registros-com-dono.md` e índice com as duas linhas novas
- [ ] T4 (dep: T2) — Migrar o `DEBT.md`: 4 colunas novas, cabeçalho com estados e link para a política, 10 abertos preenchidos e 9 quitados com `—` · arquivos: DEBT.md · cobre: R1 · verificação: `python3 skills/handoff/scripts/debito.py fila .` sai 0 e lista os 8 pontuáveis
- [ ] T5 (dep: T3) — Apontar a citação da ADR na linha do DEBT do CLAUDE.md para a ADR-0021 · arquivos: CLAUDE.md · cobre: R3 · verificação: `grep -n "ADR-0021" CLAUDE.md`
- [ ] T6 (dep: T1, T2) — Documentar na SKILL.md do handoff o script e o roteiro de ida/volta, referenciando a política sem duplicar · arquivos: skills/handoff/SKILL.md · cobre: R3 · verificação: a SKILL cita os 3 subcomandos e linka o reference
- [ ] T7 (dep: T1, T4) — Validar a ida no GitHub: exportar, conferir o corpo, criar os issues das dívidas abertas e gravar as chaves em `Externo` · arquivos: DEBT.md · cobre: R3 · verificação: `gh issue list --label dt --json number` devolve um issue por dívida aberta e a coluna `Externo` está preenchida
- [ ] T8 (dep: T7) — Validar a volta: coletar o estado do GitHub e rodar o `diff`, conferindo que ele não acusa divergência falsa · arquivos: — (leitura) · cobre: R3 · verificação: `debito.py diff . --externo <estado>` sai sem divergência não explicada
- [ ] T9 (dep: T5, T6, T8) — Registrar no CHANGELOG e no HANDOFF · arquivos: CHANGELOG.md, HANDOFF.md · cobre: infra · verificação: entrada em `[Não lançado]` citando delta-023 e as duas ADRs
