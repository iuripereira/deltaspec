# delta-021 — status-pmo
Estado: arquivada · Data: 2026-07-31 · Branch: feat/021-status-pmo · Perfil: enxuto — skill nova aditiva, sem mudança em skill existente nem em gate; clarify já feito no repo cliente (aprovado: 2026-07-31, plano aprovado em plan mode no repo imex)
Test-plan: dispensado — delta declarativa (skill nova sem código executável); validação = CI (frontmatter, JSON, commits) + check_cycle.

## Contexto (≤3 linhas)
O caso IMEX (repo `imex`, deltas 002/003) validou um site de status PMO recorrente (dashboard %/fase/farol, gantt com marcos, one-page por projeto, ata semanal, `dados.json` p/ Jira). O PO decidiu que o padrão "será sempre montado da mesma forma" → vira skill do framework ([ADR-0019](../../docs/adrs/ADR-0019-status-pmo-site-de-status.md)).

## Mudanças
### R48 — ADICIONA: skill `status-pmo`
- DADO um repo do ciclo que precisa de acompanhamento de status QUANDO `/deltaspec:status-pmo` é invocada ENTÃO a SKILL.md conduz o processo em 6 gates (cronograma canônico → ata semanal → gerador no repo cliente → marca por tokens → publicação restrita → integração externa via contrato de dados), com invariantes explícitos (fonte da verdade no repo, saída não versionada, só metadado de gestão, self-contained, coleta separada do render) e tabela de erros comuns.

### R49 — ADICIONA: templates da skill
- DADO o diretório `skills/status-pmo/references/templates/` QUANDO a skill é seguida ENTÃO existem e são utilizáveis: `styles-tokens.css` (design system com paleta placeholder e instrução de troca por marca), `theme.js` (toggle de tema persistido), `cronograma-template.md` (D0 + seções por projeto + `## Marcos` parseáveis), `ata-template.md` (5 seções fixas) e `dados-schema.md` (contrato do `dados.json`, com regra de evolução aditiva).

## Fora de escopo
- Gerador genérico no plugin (renúncia registrada na ADR-0019 — o gerador vive no repo cliente).
- Mudanças em `check_cycle.py`/gates e nas demais skills.
- Automação de publicação/infra (documentada como gate do processo, executada por repo).

## Dependências e riscos
- Caso de referência citado pela SKILL.md: repo `imex` deltas 002/003 (`scripts/gerar-report.py`) — externo a este repo, referência informativa.
- Risco: repetição do gerador por repo cliente é custo assumido (documentado na ADR-0019 e na SKILL.md).
