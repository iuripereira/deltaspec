<!-- resumo deltaspec · ≤15 linhas · única parte do plano lida pelo analyze e pelo humano -->
**Objetivo:** dar ao `DEBT.md` priorização determinística (score) e projeção para GitHub Issues/Jira, com o arquivo permanecendo a fonte da verdade. **Cobre:** R1, R2, R3 (da delta-023) **Decisões duráveis → ADRs:** ADR-0020 (modelo de dívida técnica) · ADR-0021 (projeção de tickets, supersede a ADR-0007) **Riscos assumidos:** o script nasce fora do gate bloqueante (formato ainda não estabilizado, cautela do DT-013); o caminho Jira é emitido sem execução real por falta de credencial; a projeção cria issues públicos num repo público, com conteúdo já publicado hoje.

---

# Plano — delta-023

## Ordem de construção

O script é o coração e nasce por TDD (lógica pura, contrato claro — é onde o CLAUDE.md manda usar TDD). O resto é texto normativo.

1. **`skills/handoff/scripts/debito.py`** — stdlib pura (`re`, `json`, `sys`, `subprocess`, `pathlib`, `datetime`), identificadores em PT-BR, constantes nomeadas no topo (`STALE_DIAS`, `JANELA_CHURN`, `PERCENTIL_QUENTE`, `PERCENTIL_MORNO`, `ESCALA`).
   - `parse_tabela()` — **posicional por índice de coluna** (R2), tolerante a `\|` escapado; devolve dicionários por `DT-NNN`.
   - `validar()` — Local ausente/morto, Título ausente, Fila malformada, `aceito` sem gatilho.
   - `score()` — `(J × Pr) / P`, função pura, sem I/O.
   - `churn()` e `stale()` — subprocess git, com a mesma degradação silenciosa do C7 quando não há git/histórico.
   - `exportar()` — JSON canônico + dialeto bulk do Jira + linhas `gh issue create`.
   - `diff()` — DEBT × estado externo, no formato de divergências do R27.
   - `--selftest` no padrão do `selftest_c7`: fixtures em tmpdir + repositório git real, incluindo a **fixture de regressão "sintaxe mencionada em prosa"** (célula de status contendo a palavra "aberto"), que é a lição de 2026-07-28.
2. **`skills/handoff/references/debito.md`** — política de fila: A override (enum + justificativa + prazo) · B trilha planejada (item caro vira delta própria, fatiada em tasks com `dep:`; máximo 1 ativa) · C aging (`stale` e a decisão forçada) · D aceitação (dívida deliberada é instrumento, não fracasso) + matriz de decisão + contrato da projeção (ida, volta, idempotência).
3. **ADR-0020** (modelo) e **ADR-0021** (projeção, supersede a ADR-0007), com o índice `docs/adrs/README.md` atualizado no mesmo PR e a 0007 marcada `Superseded by`.
4. **`DEBT.md`** — 4 colunas novas, cabeçalho com os estados e link para a política, migração das 19 linhas (10 abertos preenchidos; 9 quitados com `—`).
5. **`skills/handoff/SKILL.md`** — passo que roda o script e o roteiro da ida/volta, referenciando a política sem duplicá-la.
6. **`CLAUDE.md`** — a citação `(ADR-0007)` da linha do DEBT passa a apontar a ADR-0021.
7. **`CHANGELOG.md`** e **`HANDOFF.md`**.
8. **Validação de ponta a ponta** no GitHub: exportar → criar os issues das dívidas abertas → gravar as chaves em `Externo` → coletar o estado → `diff` limpo.

## TDD por task

Obrigatório em T1 (parser, score, validação, diff — lógica pura com contrato fechado). Dispensado no restante: são texto normativo e migração de dados, verificados por gate e por leitura. Justificativa registrada aqui conforme a coluna `tdd: recomendado` do tipo `tooling`.

## Split de PR

Artefatos (`specs/023-*`) no primeiro PR; implementação no segundo; archive no terceiro. O C7 mede e confirma.
