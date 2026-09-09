---
name: ticket-to-jira
description: Use when projecting repo artifacts into Jira issues (epics, stories, tasks, debts — any markdown body sent via REST/acli/MCP) or when Jira descriptions show raw markdown (**bold**, backticks, --- as literal text). Enforces the conversion contract — Jira never receives raw Markdown; Git → Jira always goes through the framework's md_para_adf.py — plus Atlassian-grade description templates per issue type, one-way sync discipline (repo owns scope, Jira owns progress) and structural idempotency (normalized ADF comparison; 2nd run = 0 mutations). Triggers include "/deltaspec:ticket-to-jira", "levar ticket para o Jira", "descrição no Jira", "markdown cru no Jira", "povoar/sincronizar backlog no Jira", "converter markdown para ADF", "ADF".
disable-model-invocation: true
---

# ticket-to-jira

## Overview

O Jira **não entende Markdown**: `--description`/`--description-file` (acli) e o campo `description` (REST v3) aceitam só texto puro ou **ADF** (Atlassian Document Format, JSON). Corpo markdown enviado literal chega cru no ticket — `**Local:**`, crases e `---` visíveis (lição DT-015, validada em bancada SBX 2026-08-07). Esta skill é o contrato de qualquer projeção repo → Jira: conversão obrigatória, templates de descrição por tipo, sincronia de mão única e idempotência estrutural.

## Regra de ouro — conversão

- **Git → Jira:** todo corpo markdown passa pelo conversor do framework — `${CLAUDE_PLUGIN_ROOT}/skills/handoff/scripts/md_para_adf.py` (função pura `converter(markdown) -> dict`; `--selftest`). **Dono único: o plugin.** Nunca copie o script para o repo consumidor — a cópia local vira fantasma que envelhece sem os fixes (lição 2026-08-09). Resolução dinâmica no consumidor: env `MD_PARA_ADF` > glob em `~/.claude/plugins/{marketplaces,cache}/deltaspec/**/md_para_adf.py`, com erro instruindo a atualizar o plugin.
- **Jira → Git:** **lacuna declarada** — não existe conversor ADF → md no framework. Texto rico do Jira não volta para o repo; só andamento/status é coletado. O 1º fluxo que precisar trazer descrição/comentário do Jira para artefato do repo cria o inverso (abra DT no repo consumidor referenciando esta lacuna).

## Subset e armadilhas do ADF (aprendidas em execução real)

O conversor cobre: parágrafo · lista `- ` · régua `---` · `**negrito**` · `` `código` `` · `_itálico_` · `[texto](url)`, com aninhamento (marks acumuladas). Fora do subset (headings `#`, tabelas `|`) **não use no corpo** — título de seção vira `**negrito**` em parágrafo próprio; tabela vira lista.

- A mark `code` é **exclusiva**: combinada com `em`/`strong` o Jira recusa o documento inteiro ("not valid ADF"). Só `link` coexiste com ela. O conversor já trata — não reimplemente.
- **Link relativo do repo vira link quebrado** no Jira: projete só o texto como `código` (`[x](docs/a.md)` → `` `x` ``). Link externo `https://` passa inteiro.
- Corpo autoral que alimenta descrição em arquivo canônico: use **bullets `- `** para notas (parsers de épico costumam descartar linhas `**`/`|`), e mantenha nomes de subseção estáveis — são contrato de parser.

## Templates de descrição por tipo (práticas Atlassian)

Toda descrição fecha com rodapé de fonte: `---` + `**Fonte:** \`<arquivo canônico>\` — o repo é a fonte; edição aqui será sobrescrita no próximo sync.`

- **Épico** — objetivo de negócio, critério de pronto/sucesso e janela (datas/sprint), vindos de notas autorais no arquivo canônico de épicos; + status do cronograma e dependências. Épico é entrega com valor mensurável, não categoria.
- **Story** — requisito **integral** (o summary pode truncar; a descrição nunca), cenários **DADO/QUANDO/ENTÃO**, critérios de aceite e Definição de Pronto. Detalhe de story vive em arquivo canônico do produto (ex.: `docs/criterios-aceite.md`, blocos `## RF-NNN` com `### Cenários` / `### Critérios de aceite` / `### DoD`); produto sem o arquivo degrada limpo (requisito + fonte, sem as seções).
- **Task** — nunca sem contexto: épico pai (com objetivo curto), dependências e o que a atividade entrega/coleta.
- **Débito** — descrição íntegra com a marcação original do arquivo do item em `debts/ativos/` + natureza/origem/data/gatilho; a issue **referencia** o DT, nunca o substitui.

## Sincronia e idempotência

- **Mão única:** escopo (summary, descrição, hierarquia) é do repo; andamento (status, transições, comentários) é do Jira. O sync **nunca** rebaixa status nem renomeia summary — summary é a chave de idempotência; mudar o título duplica o backlog inteiro.
- **Atualização sem PUT eterno:** o ADF que o Jira devolve difere estruturalmente do gerado (marks reordenadas, text nodes divididos, `attrs` vazios). Compare por normalização recursiva — descartar `version`/vazios, ordenar marks, fundir text nodes adjacentes de marks iguais — e aplique PUT só quando a forma normalizada difere. **Critério de aceite: 2ª execução = 0 mutações.**
- **Dry-run com diff legível:** extraia texto plano do ADF (um bloco por linha, bullets com `- `) e imprima `difflib.unified_diff`; quando o texto plano é igual e o ADF difere, informe "só formatação difere".
- Ponteiros `arquivo:linha` em campos de fonte derivam com a evolução do arquivo — o modo de atualização os regenera do canônico a cada run.

## Implementação de referência

`_pmo/scripts/povoar-jira.py` do workspace de portfólio de um consumidor (delta-013 de lá, 2026-08-10): templates + `--descricoes` idempotente validados em produção — 149 issues atualizadas em 3 projetos, 0 mutações na reexecução. Use-o como molde ao criar um povoador novo; a lógica de conversão permanece **só** no `md_para_adf.py` do framework.
