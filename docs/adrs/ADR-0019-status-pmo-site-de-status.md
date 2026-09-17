# ADR-0019: status-pmo — site de status PMO como skill do framework

- **Status:** Accepted (2026-07-31, delta-021)
- **Data:** 2026-07-31
- **Supersedes:** —
- **Superseded by:** —

## Context

O caso de referência (um repo de gestão de portfólio, deltas 002/003) produziu um site de status PMO recorrente para a gestão do cliente: dashboard com % · fase · farol por projeto, gantt com marcos e prazos contratuais, one-page imprimível por projeto, report semanal alimentado por ata versionada, publicação restrita e um contrato de dados (`dados.json`) preparado para o Jira assumir a coleta. O PO decidiu que esse acompanhamento "será sempre montado da mesma forma" para qualquer projeto/portfólio sob o ciclo — o que pede um dono no framework, não uma solução por repo. O design system veio de um repo consumidor (`orcamento-fase1/`): ~180 linhas de CSS com tokens de tema triplo, gantt em CSS grid puro e ~30 linhas de JS, tudo self-contained.

Alternativas:

**1 — Ferramenta pronta de status page / BI (SaaS ou lib).** Resolveria gráficos e hospedagem, mas quebra invariantes do ciclo: dado de gestão saindo do repo p/ serviço externo (sensibilidade), dependência e custo recorrentes, e o cliente sem licença de Jira continuaria sem visão. Renunciada.

**2 — Gerador genérico dentro do plugin.** Um script único parametrizável parece DRY, mas os parsers são acoplados aos arquivos de cada repo (STATE/HANDOFF, PRD, cronograma) e cada portfólio tem campos próprios; um gerador universal viraria framework de configuração — exatamente o que o ciclo evita (YAGNI). Renunciada.

**3 — Skill com processo + templates; gerador vive no repo cliente.** O plugin fornece o **padrão** (processo em gates, invariantes, design system com tokens de marca trocáveis, templates de cronograma/ata e o schema do contrato de dados); cada repo materializa seu gerador stdlib seguindo o caso de referência. Repetição controlada e documentada, com o mínimo de acoplamento.

## Decision

Adotar a alternativa 3: skill **`status-pmo`** em `skills/status-pmo/`, com `references/templates/` (styles-tokens.css, theme.js, cronograma-template.md, ata-template.md, dados-schema.md). Invariantes fixados pela skill: repo é fonte da verdade (integração externa troca a coleta, nunca o render); saída gerada não versiona; só metadado de gestão (sem PII/transcrição); páginas self-contained com gantt em **CSS grid puro** (zero lib de gráfico, zero framework); % derivado de etapas (feita=1 · em curso=0,5), farol comparando % real × % de calendário. Escopo estritamente PMO — arquitetura/diagramas permanecem com o doc-profile (ADR-0009).

## Consequences

- Qualquer repo do ciclo monta o mesmo site trocando só tokens de marca e parsers locais; o caso de referência é citado pela skill.
- O contrato `dados.json` isola a futura sincronização Jira (ou similar) do render — evolução sem retrabalho visual.
- Custo assumido: o gerador se repete por repo (padrão, não código compartilhado); mudanças estruturais no padrão exigem delta aqui + réplica nos repos clientes (duplicação documentada na SKILL.md).
- O design system portado de um repo consumidor passa a ter dono no framework; melhorias visuais fluem via template, não por cópia ad-hoc entre repos.
