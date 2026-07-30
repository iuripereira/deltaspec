# Tasks — delta-020
<!-- ordenado por dependência; cada task executável sem contexto extra.
     Arestas de bloqueio (delta-016): `(dep: Tn[, Tm])` logo após o ID — task sem
     `dep:` é livre. Duas tasks sem caminho entre si no grafo são paralelizáveis
     (execução por worktree: cycle.md); o C9 valida existência e aciclicidade.
     Arquivo sem nenhum `dep:` = cadeia linear implícita pela ordem (retrocompatível). -->
- [x] T1 — Criar ADR-0018 (supersede ADR-0015), marcar a 0015 `Superseded by` e atualizar o índice · arquivos: docs/adrs/ADR-0018-diagram-design-camada-apresentacao.md, docs/adrs/ADR-0015-figma-camada-apresentacao.md, docs/adrs/README.md · cobre: R2 · verificação: grep "Superseded by: ADR-0018" na 0015; índice com linha 0018
- [x] T2 (dep: T1) — Reescrever o contrato do motor de apresentação nos adapters (tabela, seção, política de versões) · arquivos: skills/spec-feature/references/adapters.md · cobre: R2 · verificação: grep -i figma no arquivo → 0; linhas diagram-design e design-sync presentes nas 3 partes
- [x] T3 (dep: T1) — Apontar a categoria `apresentacao` do template doc-profile para diagram-design/design-sync · arquivos: skills/projeto-init/references/templates/doc-profile.yaml · cobre: R1 · verificação: grep figma-figjam → 0; comentário cita ADR-0018
- [x] T4 (dep: T1) — Substituir o bloco Figma da doc-entregavel pelo papel da nova camada + caminho reprodutível de embutir no congelado · arquivos: skills/doc-entregavel/SKILL.md · cobre: R2 · verificação: grep -i figma → 0; bloco cita diagram-design:export
- [x] T5 (dep: T1) — Atualizar a tabela ferramenta-por-categoria do cycle.md · arquivos: skills/spec-feature/references/cycle.md · cobre: R1 · verificação: grep -i figma → 0; linha cita diagram-design e ADR-0018
- [x] T6 (dep: T2, T3, T4, T5) — Registrar a mudança no CHANGELOG (`[Não lançado]` → Mudado) · arquivos: CHANGELOG.md · cobre: R1, R2 · verificação: entrada citando delta-020 e ADR-0018 presente
- [x] T7 (dep: T6) — Varredura final anti-resíduo e gates · arquivos: — (leitura) · cobre: R1, R2 · verificação: `grep -ri figma skills/` → 0 vivas; `check_cycle.py specs/020-apresentacao-diagram-design` e `validate_integrity.py .` saem 0
