# ADRs — decisões de arquitetura

Formato Nygard (Context / Decision / Consequences), numeração de 4 dígitos, template em [ADR-TEMPLATE.md](ADR-TEMPLATE.md).

**Imutáveis após `Accepted`.** Mudou a decisão? Crie uma ADR nova com `Supersedes ADR-XXXX` e marque a antiga como `Superseded by`. Nunca reescreva uma aceita. Atualize este índice no mesmo PR.

Escreva uma ADR quando a **renúncia de uma alternativa** precisa registrar o *porquê* — não para documentar o que o código já diz.

| # | Título | Status | Data |
|---|---|---|---|
| [0001](ADR-0001-gates-rodam-local.md) | Gates determinísticos rodam local, não no CI dos projetos gerados | Accepted | 2026-07-18 |
| [0002](ADR-0002-tag-git-fonte-da-versao.md) | Tag git como fonte da verdade da versão | Accepted | 2026-07-19 |
| [0003](ADR-0003-selftest-colocalizado.md) | Verificação co-localizada — todo gate carrega o próprio `--selftest` | Accepted | 2026-07-18 |
| [0004](ADR-0004-degradacao-graciosa-adapters.md) | Degradação graciosa por adapters — motores de terceiros com contrato e fallback | Accepted | 2026-07-18 |
| [0005](ADR-0005-consolidacao-mecanica-archive.md) | Consolidação mecânica do archive — MUDA substitui integralmente, sem inferir intenção | Accepted | 2026-07-18 |
| [0006](ADR-0006-perimetro-dos-gates.md) | Perímetro dos gates determinísticos — o papel, não o implement/review | Accepted | 2026-07-18 |
| [0007](ADR-0007-registros-com-dono.md) | Registros com dono — DEBT.md file-first; Issues não são registro | Superseded by 0021 (só a parte das Issues) | 2026-07-19 |
| [0008](ADR-0008-skill-handoff-propria.md) | Skill handoff própria — nem vendorizada, nem delegada | Accepted | 2026-07-20 |
| [0009](ADR-0009-documentacao-visual-gate-configuravel.md) | Documentação visual como gate configurável — a decisão é obrigatória, os diagramas não | Accepted (2026-07-28, delta-013) | 2026-07-20 |
| [0010](ADR-0010-handoff-renomeia-state.md) | HANDOFF.md renomeia STATE.md — o diário de bordo é o ponto de entrada da retomada | Accepted | 2026-07-24 |
| [0011](ADR-0011-descoberta-skill-propria.md) | A fase de descoberta é uma skill própria pré-specify, com modelo de confiança explícito | Accepted | 2026-07-27 |
| [0012](ADR-0012-recontratacao-motores.md) | Pin do max é fork deliberado — divergência upstream documentada, migração com gatilho | Accepted | 2026-07-28 |
| [0013](ADR-0013-selecao-adaptativa-e-bugfix.md) | Seleção adaptativa por perfil da delta, prototipação opt-in e bugfix de pipeline curto | Accepted | 2026-07-28 |
| [0014](ADR-0014-harness-paralelismo-e-graphify.md) | Grafo de tasks no repo, auditoria distribuída nos artefatos e graphify como motor opcional | Superseded by 0022 (só a cláusula `--code-only` preferido) | 2026-07-28 |
| [0015](ADR-0015-figma-camada-apresentacao.md) | Figma como camada de apresentação — Mermaid permanece a fonte da verdade | Superseded by 0018 | 2026-07-28 |
| [0016](ADR-0016-rename-deltaspec.md) | O framework passa a se chamar `deltaspec` | Accepted | 2026-07-28 |
| [0017](ADR-0017-claude-code-only.md) | Portabilidade multi-agente — Claude Code only, por enquanto | Accepted | 2026-07-30 |
| [0018](ADR-0018-diagram-design-camada-apresentacao.md) | diagram-design + design-sync como camada de apresentação — Mermaid permanece a fonte | Accepted | 2026-07-30 |
| [0019](ADR-0019-status-pmo-site-de-status.md) | status-pmo — site de status PMO como skill do framework | Accepted | 2026-07-31 |
| [0020](ADR-0020-modelo-de-divida-tecnica.md) | Dívida técnica com score determinístico, derivado e nunca gravado | Accepted | 2026-08-01 |
| [0021](ADR-0021-projecao-de-tickets.md) | Ferramenta de ticket é projeção do arquivo — ida mecânica, volta aprovada | Accepted | 2026-08-01 |
| [0022](ADR-0022-backend-do-graphify-registrado-no-perfil.md) | Backend de docs do graphify recomendado e registrado no perfil, não mecanizado no gate | Accepted | 2026-08-02 |

> ADR-0002 a 0006 são **backfill** (2026-07-19): decisões que já vigiam, registradas retroativamente na varredura de registros do repo. A data de cada uma aproxima a decisão real pelo histórico disponível — o histórico pré-plugin foi reescrito (`filter-repo`), então decisões anteriores podem ser mais antigas do que a data registrada.

> `ADR-TEMPLATE.md` deste diretório é a cópia scaffoldada do template distribuído em `skills/projeto-init/references/templates/ADR-TEMPLATE.md` — duplicação sancionada do scaffold; mudou lá, sincronize aqui no mesmo change.
