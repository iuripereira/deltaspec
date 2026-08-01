# Tasks — delta-021
- [x] T1 — ADR-0019 (decisão + renúncias) · arquivos: docs/adrs/ADR-0019-status-pmo-site-de-status.md · cobre: R48 · verificação: formato Nygard, Status Accepted
- [x] T2 — SKILL.md da status-pmo (frontmatter 2 campos, corpo com 6 gates, invariantes e erros comuns) · arquivos: skills/status-pmo/SKILL.md · cobre: R48 · verificação: CI de frontmatter passa; links relativos válidos
- [x] T3 — Templates (styles-tokens.css neutro, theme.js, cronograma, ata, dados-schema) · arquivos: skills/status-pmo/references/templates/* · cobre: R49 · verificação: CSS sem hex da marca IMEX; templates com placeholders; schema cobre os campos do caso de referência
- [x] T4 — Citar a skill nos 2 manifestos · arquivos: .claude-plugin/plugin.json, .claude-plugin/marketplace.json · cobre: R48 · verificação: job "Inventário de skills nos manifestos" do CI passa
- [x] T5 — CHANGELOG [Não lançado] + HANDOFF · arquivos: CHANGELOG.md, HANDOFF.md · cobre: infra · verificação: entrada em Adicionado
- [x] T6 (dep: T1, T2, T3, T4, T5) — PR + CI verde + squash-merge; depois PR de archive (TRUTH.md, _archive, release 1.2.0 + tag) · arquivos: specs/TRUTH.md, specs/_archive/021-status-pmo/ · cobre: infra · verificação: check_cycle sem BLOQUEADO; tag v1.2.0
