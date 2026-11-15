# ADR-0013: Seleção adaptativa por perfil da delta, prototipação opt-in e bugfix de pipeline curto

- **Status:** Accepted (2026-07-28, delta-015)
- **Data:** 2026-07-28
- **Supersedes:** —
- **Superseded by:** —

## Context

A economia de tokens do ciclo era só limite de linhas (RNF1): toda delta pagava o pipeline inteiro — entrevista de clarify, review em dois subagentes — mesmo quando o escopo era pequeno e o risco baixo. O estado da arte pesquisado no plano de upgrade (2026-07-28) valida seleção adaptativa de estágios (AI-DLC: ALWAYS/CONDITIONAL/SKIPPED), tipo de spec `bugfix` (Kiro) e profundidade calibrada pela complexidade (BMAD). A delta-015 desenha os três; três decisões tiveram alternativas reais em jogo.

**1 — Composição do perfil `enxuto`.** Alternativas: (a) pular só o clarify (conservador, economia menor); (b) reusar o ciclo reduzido do R10 — specify → plan → implement → review, analyze sob demanda (economia máxima, mas abre mão do gate determinístico por padrão); (c) clarify sob demanda + test-plan dispensável com justificativa + review com eixos fundidos num único subagente, mantendo plan, tasks, analyze e archive integrais.

**2 — Forma do protótipo.** Alternativas: (a) sempre HTML estático (simples, inflexível); (b) wireframe nas categorias existentes do ADR-0009 (zero ferramenta nova, não navegável); (c) categoria `prototipo` no `doc-profile.yaml` como dona da decisão, com default HTML estático em `docs/prototypes/NNN-nome/` quando o perfil não declara.

**3 — Pipeline do `bugfix`.** Alternativas: (a) delta completa com template distinto (uniforme, pesado demais para correção); (b) bugfix não vira delta — fluxo git normal (mais enxuto, mas perde repro DADO/QUANDO/ENTÃO, causa-raiz e teste de regressão como artefato citável); (c) pipeline curto — specify (template bugfix) → plan curto → implement com teste de regressão obrigatório → review — com analyze mantido e TRUTH consolidado só quando um requisito muda.

## Decision

Decididas com o usuário em 2026-07-28 (clarify da delta-015): **1-c, 2-c e 3-c.**

O perfil (`completo|enxuto`) é proposto pela IA com justificativa de escopo/risco e **só vale com aprovação explícita do usuário registrada no cabeçalho da spec** — the agent proposes, the human approves. Os gates não se adaptam: analyze e archive rodam em qualquer perfil; o que flexiona é o custo em tokens (entrevista, artefato de teste, subagentes de review). Renunciamos a 1-a porque a economia não justificaria o mecanismo, e a 1-b porque gate determinístico opcional deixa de ser gate.

A prototipação segue o padrão do gate visual (ADR-0009): opt-in com aprovação, ferramenta decidida pelo `doc-profile.yaml`. Renunciamos a 2-a para não criar segunda fonte de decisão visual fora do doc-profile, e a 2-b porque protótipo que o stakeholder não navega não cumpre o papel do estágio.

O `bugfix` mantém a numeração NNN global e o archive, mas não exige bloco Rn nem consolidação quando nenhum requisito muda. Renunciamos a 3-b porque a correção perderia a trilha (repro, causa-raiz, regressão) que é justamente o valor do tipo; a 3-a morreria por atrito — ninguém abre pipeline inteiro para um fix.

## Consequences

**Fica mais fácil:** delta pequena custa pouco (enxuto), correção tem trilha própria (bugfix), stakeholder vê antes de especificar (protótipo) — tudo com human-in-the-loop e os gates intactos; o C8 novo fecha o elo requisito → caso de teste.

**Fica mais difícil:** o cabeçalho da spec vira contrato lido por script (campos `Perfil`, `Test-plan`, `Tipo` — retrocompatíveis por default `completo`); o cycle.md carrega uma tabela de estágios por perfil que precisa manter-se em sincronia com os templates; review fundido no enxuto abre exceção ao R35 (MUDA registrado na delta-015).
