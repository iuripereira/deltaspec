# Test plan — delta-024
<!-- derivado dos cenários DADO/QUANDO/ENTÃO da spec e das verificações do tasks.md — não inventa cenário novo (R3, delta-015) -->
<!-- teste manual roteirizado conta como cobertura; todo Rn/RNFn da spec precisa de ≥1 caso (C8) -->
- [x] CT1 — Bloco bem formado é lido com natureza, estado, título, descrição e campos · cobre: R1 · tipo: auto · verificação: fixture do `--selftest` compara o dicionário devolvido com o esperado
- [x] CT2 — Item ativo sem `Fila`, `Local`, `Gatilho` ou título é recusado nomeando o `DT-NNN` e o campo · cobre: R1 · tipo: auto · verificação: quatro fixtures no `--selftest`, cada uma assertando exit ≠ 0
- [x] CT3 — `guarda` sem Fila e sem Local passa; `guarda` com Fila é recusada · cobre: R1 · tipo: auto · verificação: duas fixtures no `--selftest`
- [x] CT4 — Item encerrado exige o campo `Encerrado` com data · cobre: R1 · tipo: auto · verificação: fixture com `quitado` sem o campo, assertando a mensagem
- [x] CT5 — A legenda explica os cinco estados e o `stale`, sem materializar limiar · cobre: R1 · tipo: manual · verificação: (1) abrir o `DEBT.md`; (2) conferir um parágrafo por estado + `stale`; (3) `grep -E "90|6 months"` no cabeçalho não acha nada
- [x] CT6 — Registro no formato de tabela antigo avisa como converter e não quebra · cobre: R1 · tipo: auto · verificação: fixture com tabela da delta-023, assertando exit 0 e a menção ao formato antigo
- [x] CT7 — A fila sai igual à da delta-023: mesma ordem, mesmos pontuáveis, score não gravado · cobre: R2 · tipo: auto · verificação: `debito.py fila .` lista os 11 na ordem override → trilha → score desc, e `git diff --quiet DEBT.md`
- [x] CT8 — Campo só vale na âncora canônica: prosa citando `- **Fila:**` na descrição não vira campo · cobre: R2 · tipo: auto · verificação: fixture de regressão com a sintaxe mencionada no meio da descrição
- [x] CT9 — Ticket, PR, delta e artefato são links navegáveis · cobre: R2 · tipo: manual · verificação: (1) abrir o `DEBT.md` no GitHub; (2) clicar num `#NN` de ticket, num `PR #N`, numa `delta-NNN` e num `Local`; (3) confirmar que os quatro resolvem
- [x] CT10 — Exportar depois da conversão não recria ticket existente · cobre: R2 · tipo: auto · verificação: `debito.py exportar` reporta "0 sem projeção" e o roteiro só tem linhas de comentário
