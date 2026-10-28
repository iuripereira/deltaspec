# Tasks — delta-{{NNN}}
<!-- ordenado por dependência; cada task executável sem contexto extra.
     Arestas de bloqueio (delta-016): `(dep: Tn[, Tm])` logo após o ID — task sem
     `dep:` é livre. Duas tasks sem caminho entre si no grafo são paralelizáveis
     (execução por worktree: cycle.md); o C9 valida existência e aciclicidade.
     Arquivo sem nenhum `dep:` = cadeia linear implícita pela ordem (retrocompatível). -->
- [ ] T1 — {{ação}} · arquivos: {{caminhos}} · cobre: {{Rn|RNFn|infra}} · verificação: {{comando/critério}}
- [ ] T2 (dep: T1) — {{ação}} · arquivos: {{caminhos}} · cobre: {{Rn}} · verificação: {{comando}}
