# delta-022 — status-pmo-epicos
Estado: arquivada · Data: 2026-07-31 · Branch: feat/status-pmo-epicos · Perfil: enxuto — incremento declarativo na skill recém-criada, sem código executável nem mudança de gate (aprovado: 2026-07-31)
Test-plan: dispensado — delta declarativa (skill/templates); validação = CI (frontmatter, JSON, commits) + check_cycle.

## Contexto (≤3 linhas)
A 1ª revisão do PO no caso de referência (repo imex, delta-003) pediu o nível **épico/tarefa com dependências** por projeto, etapas clicáveis e três correções de padrão (tema claro, escopo rastreado, espaçamento). O padrão validado precisa refletir no dono ([R48](../TRUTH.md)).

## Mudanças
### R50 — ADICIONA: gate de épicos e tarefas com dependências
- DADO a skill `status-pmo` QUANDO o processo é seguido ENTÃO existe o gate "Épicos e tarefas com dependências" (`docs/epicos/<dir>.md`: um épico por etapa do cronograma, mesma ordem e quantidade, com `**Dep:**` e tabela `| ID | Tarefa | Dep | Status |`), o gerador produz `etapa-<dir>-eN.html` por épico (tarefas, depende-de/bloqueia, registros, chave do sistema externo) com a etapa do cronograma clicável, e a seção "Diagramas de dependência" descreve o grafo em SVG inline (camadas por profundidade, tokens CSS, nó clicável, ciclo degrada sem quebrar).
- DADO um projeto sem `docs/epicos/<dir>.md` QUANDO o site é gerado ENTÃO a seção mostra "em elaboração" e a geração completa.

### R51 — MUDA R49 (delta-021): templates cobrem épicos e fixam o tema claro
- DADO `skills/status-pmo/references/templates/` QUANDO a skill é seguida ENTÃO existe `epicos-template.md` (com as regras de status, dep e paralelismo), o `styles-tokens.css` **não** tem bloco `prefers-color-scheme: dark` (claro é o padrão; escuro só por `data-theme`) com o espaçamento do `.topnav` corrigido, o `theme.js` não consulta `prefers-color-scheme`, e o `dados-schema.md` inclui `jira` e `epicos[]` (com `tarefas[]`).

### R52 — MUDA R48 (delta-021): escopo rastreado explícito
- DADO o gate do cronograma QUANDO ele é aplicado ENTÃO só entram projetos com **entrega rastreada** — repositório de apoio (contratos, infra) fica fora do site, e a tabela de erros comuns registra isso junto com as demais lições da revisão.

## Fora de escopo
- Gerador genérico no plugin (renúncia vigente da ADR-0019).
- Automação de sincronização com Jira (o schema já prevê; a implementação é do repo cliente).

## Dependências e riscos
- Caso de referência: repo `imex` delta-003 (`scripts/gerar-report.py`, 32 páginas geradas) — externo a este repo.
- Risco: templates de CSS/JS são cópia do caso IMEX; divergência futura entre template e caso é duplicação documentada (SKILL.md + ADR-0019).
