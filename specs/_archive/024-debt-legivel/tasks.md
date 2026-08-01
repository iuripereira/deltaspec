# Tasks — delta-024
<!-- ordenado por dependência; cada task executável sem contexto extra.
     Arestas de bloqueio (delta-016): `(dep: Tn[, Tm])` logo após o ID — task sem
     `dep:` é livre. Duas tasks sem caminho entre si no grafo são paralelizáveis
     (execução por worktree: cycle.md); o C9 valida existência e aciclicidade.
     Arquivo sem nenhum `dep:` = cadeia linear implícita pela ordem (retrocompatível). -->
- [x] T1 — Trocar `parse_tabela` por `parse_blocos` (cabeçalho, título, campos por âncora canônica) e detectar formato antigo com aviso · arquivos: skills/handoff/scripts/debito.py · cobre: R2 · verificação: `python3 skills/handoff/scripts/debito.py --selftest` sai 0
- [x] T2 (dep: T1) — Migrar as fixtures do selftest para blocos, incluindo a regressão de prosa e o caso de formato antigo · arquivos: skills/handoff/scripts/debito.py · cobre: R2 · verificação: o selftest cobre bloco válido, campo faltando, prosa com sintaxe e tabela antiga
- [x] T3 (dep: T1) — Converter as 22 linhas do DEBT.md para blocos, com ticket, PR, issue, delta e artefato como links · arquivos: DEBT.md · cobre: R1 · verificação: `debito.py fila .` sai 0 e lista os mesmos 11 pontuáveis de antes, na mesma ordem
- [x] T4 (dep: T3) — Escrever a legenda do cabeçalho: cada estado (com `stale` derivado) e os três eixos da fila, sem repetir limiares · arquivos: DEBT.md · cobre: R1 · verificação: os 5 estados + `stale` explicados; nenhum número de limiar materializado
- [x] T5 (dep: T1, T4) — Atualizar a gramática na política e na SKILL do handoff, sem duplicar a legenda · arquivos: skills/handoff/references/debito.md, skills/handoff/SKILL.md · cobre: R1 · verificação: a política mostra o bloco-exemplo e a SKILL aponta para ela
- [x] T6 (dep: T3) — Conferir que a projeção segue idempotente: exportar não recria ticket já existente · arquivos: — (leitura) · cobre: R2 · verificação: `debito.py exportar` reporta "0 sem projeção" e o roteiro só tem comentários de item já projetado
- [x] T7 (dep: T5, T6) — Registrar no CHANGELOG e no HANDOFF · arquivos: CHANGELOG.md, HANDOFF.md · cobre: infra · verificação: entrada em `[Não lançado]` citando delta-024
