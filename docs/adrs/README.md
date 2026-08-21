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
| [0018](ADR-0018-diagram-design-camada-apresentacao.md) | diagram-design + design-sync como camada de apresentação — Mermaid permanece a fonte | Superseded by 0029 | 2026-07-30 |
| [0019](ADR-0019-status-pmo-site-de-status.md) | status-pmo — site de status PMO como skill do framework | Accepted | 2026-07-31 |
| [0020](ADR-0020-modelo-de-divida-tecnica.md) | Dívida técnica com score determinístico, derivado e nunca gravado | Accepted | 2026-08-01 |
| [0021](ADR-0021-projecao-de-tickets.md) | Ferramenta de ticket é projeção do arquivo — ida mecânica, volta aprovada | Accepted | 2026-08-01 |
| [0022](ADR-0022-backend-do-graphify-registrado-no-perfil.md) | Backend de docs do graphify recomendado e registrado no perfil, não mecanizado no gate | Accepted | 2026-08-02 |
| [0023](ADR-0023-pyyaml-como-dependencia-admitida.md) | PyYAML é dependência externa admitida nos gates — exceção declarada, não erosão do princípio | Accepted | 2026-08-02 |
| [0024](ADR-0024-pin-do-max-reavaliado-fork-mantido.md) | Pin do max reavaliado na delta-017 — fork 0.8.0 mantido | Superseded | 2026-08-07 |
| [0025](ADR-0025-handoff-por-sessao.md) | Handoff por sessão — o diário de bordo vira índice fino + arquivos por sessão | Accepted | 2026-08-09 |
| [0026](ADR-0026-recontratacao-hibrida-clarify-no-oficial.md) | Recontratação híbrida — clarify no mattpocock-skills oficial, write-prd permanece no fork max | Accepted | 2026-08-09 |
| [0027](ADR-0027-tokenizador-real-recusado-nos-gates.md) | Tokenizador real (tiktoken) recusado nos gates — a heurística stdlib mede melhor o que importa | Accepted | 2026-08-09 |
| [0028](ADR-0028-arquivamento-de-debitos-encerrados.md) | Débitos encerrados arquivam em `.claude/debts/` — DEBT.md fica com os ativos e um índice | Accepted | 2026-08-10 |
| [0029](ADR-0029-apresentacao-como-modo-e-html-autocontido-canonico.md) | Apresentação é modo por categoria, com motor nativo — e o HTML autocontido ganha dono único | Accepted | 2026-08-10 |
| [0030](ADR-0030-registro-de-debitos-em-pasta-na-raiz.md) | Registro de débitos em pasta `debts/` na raiz — split total com um arquivo por item | Superseded by 0031 (só o ponteiro fino) | 2026-08-11 |
| [0031](ADR-0031-debt-md-como-indice-gerado.md) | DEBT.md da raiz é índice gerado dos ativos — projeção, nunca fonte | Accepted | 2026-08-11 |
| [0032](ADR-0032-erro-mecanico-de-caminho-e-corrigivel-no-imutavel.md) | Erro mecânico de caminho é corrigível no registro imutável — conteúdo de época não é | Superseded by 0035 (só a forma da entrada de CHANGELOG) | 2026-08-11 |
| [0033](ADR-0033-rodada-insumos-skill-propria.md) | A conciliação de insumo novo é uma skill própria do ciclo, não um comando de workspace | Accepted | 2026-08-12 |
| [0034](ADR-0034-truth-como-indice-e-particoes-com-heading-por-requisito.md) | TRUTH como índice + partições, com requisito como heading e cenário atômico | Accepted | 2026-08-13 |
| [0035](ADR-0035-changelog-lancado-e-projecao-reescrevivel.md) | A entrada lançada do CHANGELOG é projeção reescrevível — o nome de época que ela cita não é | Accepted | 2026-08-14 |
| [0036](ADR-0036-publicacao-derivada-como-gate-de-confidencialidade.md) | O repositório público é derivado por allowlist, e é a publicação — não o CI — que porta o gate de confidencialidade | Accepted | 2026-08-15 |
| [0037](ADR-0037-identificador-de-terceiro-e-substituivel-no-imutavel.md) | Identificador de terceiro é substituível no registro imutável — o fato que ele acompanha não é | Accepted | 2026-08-15 |
| [0038](ADR-0038-modelo-de-dados-em-tres-camadas-com-dono-unico.md) | Modelo de dados em três camadas com dono único, ERD derivado do contrato e gate que nasce ALTO | Accepted | 2026-08-20 |

> ADR-0002 a 0006 são **backfill** (2026-07-19): decisões que já vigiam, registradas retroativamente na varredura de registros do repo. A data de cada uma aproxima a decisão real pelo histórico disponível — o histórico pré-plugin foi reescrito (`filter-repo`), então decisões anteriores podem ser mais antigas do que a data registrada.

> `ADR-TEMPLATE.md` deste diretório é a cópia scaffoldada do template distribuído em `skills/projeto-init/references/templates/ADR-TEMPLATE.md` — duplicação sancionada do scaffold; mudou lá, sincronize aqui no mesmo change.
