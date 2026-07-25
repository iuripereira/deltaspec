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
| [0007](ADR-0007-registros-com-dono.md) | Registros com dono — DEBT.md file-first; Issues não são registro | Accepted | 2026-07-19 |
| [0008](ADR-0008-skill-handoff-propria.md) | Skill handoff própria — nem vendorizada, nem delegada | Accepted | 2026-07-20 |
| [0009](ADR-0009-documentacao-visual-gate-configuravel.md) | Documentação visual como gate configurável — a decisão é obrigatória, os diagramas não | Proposed (experimental — piloto imex-travelplanner) | 2026-07-20 |
| [0010](ADR-0010-handoff-renomeia-state.md) | HANDOFF.md renomeia STATE.md — o diário de bordo é o ponto de entrada da retomada | Accepted | 2026-07-24 |

> ADR-0002 a 0006 são **backfill** (2026-07-19): decisões que já vigiam, registradas retroativamente na varredura de registros do repo. A data de cada uma aproxima a decisão real pelo histórico disponível — o histórico pré-plugin foi reescrito (`filter-repo`), então decisões anteriores podem ser mais antigas do que a data registrada.

> `ADR-TEMPLATE.md` deste diretório é a cópia scaffoldada do template distribuído em `skills/projeto-init/references/templates/ADR-TEMPLATE.md` — duplicação sancionada do scaffold; mudou lá, sincronize aqui no mesmo change.
