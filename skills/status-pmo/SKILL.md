---
name: status-pmo
description: Use when a project or portfolio needs a recurring PMO status site — weekly status report, schedule vs. contract deadlines (gantt with milestones), % progress dashboard with per-project phase and traffic light, printable per-project one-page — generated as self-contained HTML from canonical repo files and published behind restricted access, ready to swap the data source for Jira later. Triggers include "/deltaspec:status-pmo", "site de status", "status report semanal", "report para a gestão", "dashboard de projetos", "acompanhamento de portfólio", "one-page do projeto", "cronograma com marcos".
---

# status-pmo

## Overview

Monta o **site de status PMO** de um projeto ou portfólio — sempre da mesma forma, em qualquer repo do ciclo (decisão e renúncias: [ADR-0019](../../docs/adrs/ADR-0019-status-pmo-site-de-status.md)). O produto é um conjunto de páginas HTML **self-contained** (zero recurso externo, zero lib) geradas por script Python stdlib a partir de arquivos canônicos do repo, com a marca do cliente aplicada por tokens de CSS. Caso de referência: um repo de gestão de portfólio (deltas 002/003 — `scripts/gerar-report.py`).

Conteúdo é **estritamente PMO**: cronograma, marcos, prazos, %, fase, farol, visão do produto, semana (realizado/reuniões/decisões/pendências). Arquitetura e diagramas têm dono próprio (doc-profile/ADR-0009) e **não entram** no site de status.

## Invariantes (valem em todo cliente)

- **Repo é a fonte da verdade**; sistema externo (Jira etc.) é enriquecimento — a sincronização troca a **coleta**, nunca o render.
- **Saída gerada não versiona** (gitignore); os **assets-fonte** da marca versionam.
- **Só metadado de gestão** — transcrição de reunião e dado sensível/PII nunca entram no site.
- **Self-contained**: CSS/JS locais copiados na geração, logo em data URI, gantt em CSS grid puro; self-check embutido falha a geração se houver recurso externo ou seção obrigatória vazia.
- **Coleta separada do render**: um dict único (`montar_dados`) serializado em `dados.json` é o contrato — [references/templates/dados-schema.md](references/templates/dados-schema.md).

## Processo (gates na ordem)

1. **Cronograma canônico** — crie `docs/cronograma.md` do [template](references/templates/cronograma-template.md): `**D0:**`, uma seção por projeto (`**Dir:** · **Prazo:** · **Fonte-repo:**` + tabela `| Etapa | Status |` com `feita | em curso | prevista`) e a seção `## Marcos` (`| marco | AAAA-MM-DD | projeto |`). Etapas são **espelho** do roadmap do PRD (duplicação documentada); % e fase são **derivados** (feita=1 · em curso=0,5 · prevista=0; fase = primeira etapa em curso). **Só entram projetos com entrega rastreada** — repositório de apoio (contratos, infra) fica fora.
2. **Épicos e tarefas com dependências** — para cada projeto, `docs/epicos/<dir>.md` do [template](references/templates/epicos-template.md): **um épico por etapa do cronograma, na mesma ordem** (o self-check falha se divergir), cada um com `**Dep:**` e tabela `| ID | Tarefa | Dep | Status |`. Tarefas derivam dos RFs do PRD — nunca invente data por tarefa; sem data no PRD, o gantt fica no nível projeto e a sequência aparece como **grafo de dependências**. Projeto sem detalhamento ainda: a seção mostra "em elaboração" e a geração completa.
3. **Ata semanal** — `relatorios/semanas/AAAA-Www.md` do [template](references/templates/ata-template.md); o gerador ganha `--nova` que pré-preenche o realizado do `git log` da semana. Ata existente nunca é sobrescrita.
4. **Gerador no repo cliente** — script Python stdlib (padrão do `gerar-report.py` do caso de referência): funções puras com `--selftest` (parsers, %, fase, farol, grid, camadas do DAG) · coleta `montar_dados` → `dados.json` · render: `index.html` (dashboard: tiles com farol/%/fase + gantt compacto + tabela status + histórico), `cronograma.html` (gantt semanal com losangos de marco e marcador "hoje"), `projeto-<dir>.html` (one-page imprimível), **`etapa-<dir>-eN.html` (uma por épico: status, tarefas com dependência, depende-de/bloqueia, registros de progresso, chave do sistema externo)** e `semana-AAAA-Www.html`. Farol: vermelho = prazo estourado; verde = % ≥ % de calendário − 10 p.p.; senão amarelo. **Etapa do cronograma é sempre clicável** para a página do épico.
5. **Marca do cliente** — os invariantes de HTML autocontido são de [html-autocontido.md](../spec-feature/references/html-autocontido.md) (dona da regra); o [styles-tokens.css](references/templates/styles-tokens.css) desta skill é a **implementação de referência** dela e segue dono do vocabulário de dashboard (gantt, farol, chips, `.pbar`), que é daqui e não universal. Copie o `styles-tokens.css` + [theme.js](references/templates/theme.js) para `relatorios/site/` do repo e troque **só os tokens de `:root`** pela identidade do cliente (extraia do site/manual da marca; a semântica de cores não muda). Logo do cliente em PNG pequeno ao lado, embutido como data URI pelo gerador. **Tema claro é o padrão** — o escuro entra pelo toggle, não pelo `prefers-color-scheme` (site de gestão é lido e impresso claro).
6. **Publicação restrita** — diretório estático atrás de basic auth (nginx) ou Cloudflare Access; cadência documentada (`relatorios/README.md`): diária p/ painéis vivos, sexta p/ o report semanal.
7. **Sincronização externa** — quando o Jira (ou similar) estiver povoado, substitua campos da coleta mantendo o schema de `dados.json`; o render e o site não mudam. As páginas de épico já são o espelho local do que virá (épico, tarefas, relacionamentos, registros).

## Diagramas de dependência

Grafo em **SVG inline** gerado pelo próprio script (zero lib): profundidade de cada nó = caminho mais longo até uma raiz (define a coluna), nós na mesma coluna correm em paralelo, arestas com marcador de seta, `fill`/`stroke` por **tokens CSS** (funciona nos dois temas), nó clicável (`<a>`) para a página do épico. Ciclo acidental degrada sem quebrar a geração — o self-check acusa dependência inválida à parte. Um grafo por projeto (entre épicos) e um por épico (entre tarefas).

## Erros comuns

| Erro | Correto |
|---|---|
| Lib de gráficos/framework p/ o gantt | CSS grid puro com barras posicionadas por `grid-column` (ADR-0019) |
| Gerador genérico dentro do plugin | O gerador vive no repo cliente (parsers acoplados aos arquivos dele); o plugin dá padrão + templates |
| Versionar a saída `relatorios/html/` | Derivado regenerável — gitignore; versione fonte (`site/`, atas, cronograma) |
| % por tempo decorrido | % por etapas (trabalho), calendário só no farol |
| Diagramas/arquitetura no site | Fora — dono é o doc-profile (ADR-0009); site é PMO estrito |
| Datas de etapa inventadas | Sem data por etapa no PRD → barra só no nível projeto; a sequência vira grafo de dependências |
| Épicos fora de ordem/quantidade vs. cronograma | Épico = etapa, mesma ordem e quantidade (self-check falha); status do épico vive no cronograma |
| Repo de apoio (contratos/infra) como projeto | Só entra quem tem entrega rastreada com prazo |
| Tema escuro por `prefers-color-scheme` | Claro é o padrão do site de gestão; escuro só pelo toggle |
