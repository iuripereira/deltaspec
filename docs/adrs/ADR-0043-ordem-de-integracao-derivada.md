# ADR-0043: Ordem de integração derivada, vista regenerada, sem arquivo nem hook

- **Status:** Accepted
- **Data:** 2026-09-07
- **Supersedes:** —
- **Superseded by:** —

## Context

Trabalho paralelo em 9 repos + deltaspec (sessões e worktrees) sem uma vista de quem está em voo. A delta-113 declarou a ordem por rótulo `fila:N`; faltava derivá-la e exibi-la — o que a delta-114 faz.

## Decision

1. A ordem é **derivada** (marco do cronograma → pilha → `fila:N` → PR mais antiga → tip mais antigo); o rótulo é override, não fonte.
2. A vista é **regenerada por comando** (`integracao.py`), nunca editada nem versionada; fonte da verdade = git + GitHub.
3. **Sem hook** para exibir: o gatilho é uma task `runOn: folderOpen` do workspace do consumidor.
4. GitLens Launchpad **descartado** como vista: em 07/09 omitiu PRs do `_pmo` e listou 15 PRs pessoais desde abril.

## Alternativas renunciadas

`FILA.md` versionado, ordem só no Jira, GitHub Projects, `gh stack` para tudo, orquestrador do DT-138, merge queue (DT-074) — tabela de alternativas no [relatório de 04/09](../relatorios/2026-09-04-fila-de-integracao-multi-repo.md#alternativas-consideradas-e-por-que-perderam) (PR #415).

## Consequences

- \+ Zero conflito de merge por fila; funciona offline (colunas `?`).
- − Dois níveis de ordem exigem cronograma do `_pmo` para o nível entre repos; sem ele, só idade.

<!--
Imutável após "Accepted". Mudou a decisão? Crie uma NOVA ADR com "Supersedes ADR-0043" e marque esta como "Superseded by ADR-YYYY". Nunca reescreva uma ADR aceita. Atualize o índice docs/adrs/README.md no mesmo PR. -->
