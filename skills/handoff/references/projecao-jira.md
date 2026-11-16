# Projeção repo → Jira (ex-`ticket-to-jira`)

## Overview

O Jira **não entende Markdown**: `--description`/`--description-file` (acli) e o campo `description` (REST v3) aceitam só texto puro ou **ADF** (Atlassian Document Format, JSON). Corpo markdown enviado literal chega cru no ticket — `**Local:**`, crases e `---` visíveis (lição DT-015, validada em bancada SBX 2026-08-07). Esta referência é o contrato de qualquer projeção repo → Jira: conversão obrigatória, templates de descrição por tipo, sincronia de mão única e idempotência estrutural.

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
- **Débito** — descrição íntegra com a marcação original do arquivo do item em `debts/ativos/` + **Causa / Correção / Recorrência derivadas do molde** (`**Corrigir:**` → Correção; bullets do corpo → Causa; Gatilho + Local → Recorrência — a gramática do DT não muda) + natureza/origem/data; a issue **referencia** o DT, nunca o substitui. Summary com **prefixo do projeto** (`KEY · DT-NNN — título`): `DT-NNN` colide entre ledgers numa visão cross-projeto. Campos **`Score`** ((J×Pr)/P da `fila:`, 2 casas) e **`Fila`** (texto cru, com sufixos) **sobrescritos a cada sync** — o Jira Cloud não tem campo só-leitura, o rodapé avisa; `Score` ordena o filtro cross-projeto, Priority segue como desempate. `natureza: guarda` não projeta.

## Sincronia e idempotência

- **Mão única:** escopo (summary, descrição, hierarquia, prioridade, Score/Fila) é do repo; andamento (status, transições, comentários) é do Jira. O sync **nunca** rebaixa status nem apaga. A chave de idempotência é o **mapa** (`jira-map.json`) ou uma **label `dt-nnn`** — nunca o summary, que segue o repo; ao mudar o formato do summary, o povoador procura também o formato antigo e o dry-run tem de mostrar 0 criações antes da primeira rodada.
- **Transição no merge (ADR-0032 do consumidor `_pmo`):** PR mergeada na `develop` com `Closes KEY-NN` leva a issue a `Em validação` + label `entregue-por-pr`, pelo **workflow do GitHub do repo de produto** (token do PO no 1Password) — nunca Jira Automation (token do GitHub fora do cofre) e nunca a sessão do agente. `Closed` é humano (homologação). Débito: `estado:`/quitação no repo → o povoador transiciona por nome (`Aceitar`/`Quitar`/`Descartar`), nunca uma automação do Jira. A PR carrega a chave no título ou na branch porque o `debito.py quitar` a imprime e o `debito.py vinculo` a confere no CI; chave só no corpo não vincula e reprova. O comentário de fechamento em nível de negócio segue manual.
- **Atualização sem PUT eterno:** o ADF que o Jira devolve difere estruturalmente do gerado (marks reordenadas, text nodes divididos, `attrs` vazios). Compare por normalização recursiva — descartar `version`/vazios, ordenar marks, fundir text nodes adjacentes de marks iguais — e aplique PUT só quando a forma normalizada difere. **Critério de aceite: 2ª execução = 0 mutações.**
- **Dry-run com diff legível:** extraia texto plano do ADF (um bloco por linha, bullets com `- `) e imprima `difflib.unified_diff`; quando o texto plano é igual e o ADF difere, informe "só formatação difere".
- Ponteiros `arquivo:linha` em campos de fonte derivam com a evolução do arquivo — o modo de atualização os regenera do canônico a cada run.

## Implementação de referência

`_pmo/scripts/povoar-jira.py` do workspace de portfólio de um consumidor (delta-013 de lá, 2026-08-10; Score/Fila, prefixo e seções do Débito pela ADR-0033 de lá, 2026-10-28): templates + `--descricoes` idempotente validados em produção — 149 issues atualizadas em 3 projetos, 0 mutações na reexecução; o `jira-map.json` é commitado por workflow a cada push de escopo do produto. Use-o como molde ao criar um povoador novo; a lógica de conversão permanece **só** no `md_para_adf.py` do framework.
