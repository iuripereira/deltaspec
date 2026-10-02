# One page do projeto — layout, regras e mapa de detalhe

> Dono do layout de `projeto-<dir>.html` e das regras que ele exibe: saúde, tendência, criticidade, objetivos e % da entrega. A [SKILL.md](../SKILL.md) só aponta para cá. O vocabulário visual (classes e tokens) é do [styles-tokens.css](templates/styles-tokens.css); os campos que alimentam cada bloco, do [dados-schema.md](templates/dados-schema.md). Molde: o "Project Status One Pager" — o projeto inteiro numa página, lido em 30 segundos, com o total ao lado dos poucos itens que importam.

## Princípios

- **Uma página, trinta segundos.** Sem rolar, a página responde: está saudável? piorou? quanto falta? o que vence? o que está com o cliente? Tudo que não responde a uma dessas perguntas mora numa página de detalhe.
- **Top 5 + total, nunca a lista inteira.** Cada tabela mostra os 5 itens mais críticos (`TOP_N = 5`, constante nomeada no gerador) e o total no cabeçalho; o total é link para a lista completa.
- **Todo bloco é porta de entrada.** Cabeçalho de bloco e linha de tabela são links para o detalhe (mapa abaixo) — e só viram link se a página de destino foi gerada. Sem link morto.
- **Regra calcula, pessoa narra.** Saúde, tendência, criticidade e % saem de regra; o único texto livre é o status atual, que vem da ata da semana.
- **Legível sem cor.** Saúde tem forma além de cor; atraso tem texto ("Atrasada +N dias") além do vermelho.

## Faixas, na ordem

| # | Faixa | Blocos | Fonte |
|---|---|---|---|
| 1 | Cabeçalho | eyebrow "Relatório de status" · nome do projeto · à direita, **Previsão de término** e **Prazo contratual** (a previsão fica em âmbar quando passa do prazo) | `prazo`, previsão do gerador |
| 2 | Sinais vitais | **Saúde** (forma + cor + seta de tendência) · **% concluído** (donut com o % de trabalho; % de calendário decorrido abaixo) · **Responsáveis** (papel e lado — quem conduz e quem patrocina) · **Escopo cumprido** (requisitos N/M e entregas N/M numa barra: verde = cumprido, vermelho = vencido sem cumprir, neutro = a cumprir) · **Status atual** (2–3 frases da ata + veredicto calculado + data da ata) | `saude`, `pct`, `cal_pct`, `responsaveis`, `escopo`, ata |
| 3 | Objetivos | 1 a 4 cartões `On` com glifo de situação (`●` atingido · `◐` em andamento · `○` não iniciado), a dor e o impacto numa linha; ou a frase de dispensa | `objetivos` |
| 4 | Execução | **Entregas em curso** (`Total N · Atrasadas N`; status · entrega · prazo) e **Tarefas em curso** (`Total N · Atrasadas N`; status · tarefa · entrega · barra de progresso) | `marcos`, `epicos[*].tarefas` |
| 5 | Top 5 | **Entregas** (status · entrega · data) · **Defeitos** (nível · item · idade) · **Pendências do cliente** (nível · item · prazo · responder) · **Impedimentos e riscos** (nível · item · prazo) — cada uma com `Total: N` | `marcos`, `defeitos`, `pendencias_cliente`, `impedimentos`, `riscos` |

**Escopo cumprido substitui o bloco financeiro do molde.** O site de status não mostra valor monetário; o que se cumpre ou se descumpre, aqui, são requisitos e entregas.

**O que não entra no one page** (vive no detalhe): tempos de ciclo, previsão probabilística, débitos técnicos internos, grade de objetivos × etapas, custos, visão do produto.

**Impressão e celular.** A4 paisagem em uma página (`@page { size: A4 landscape }`; faixas em grid). Abaixo de 720 px as faixas empilham, sem rolagem horizontal; as tabelas "Top 5" ficam uma por linha.

**Classes** (do [styles-tokens.css](templates/styles-tokens.css), seção "One page do projeto"): faixa 2 = `.vitais` com `.vital` (o status atual é `.vital.narr`), saúde `.saude.ok|.warn|.crit` + `.tend.up|.down`, `.donut` com `style="--p:NN"`, `.escopo-bar` com `<i class="ok">` e `<i class="venc">`; faixa 3 = `.mgrid`/`.mcard` já existentes; faixa 4 = `.duas`; faixa 5 = `.top5`; cada tabela é um `.bloco` (`header` com `h3` e `.tot`; data vencida em `.atras`; lista vazia em `.vazio`); situação e nível em `.chip`.

## Mapa de detalhe

| Bloco | Destino | O que o destino mostra |
|---|---|---|
| Saúde | `#saude` no próprio one page | a regra que disparou e o valor que a disparou |
| % concluído · Escopo cumprido | página de escopo do produto → página de cada requisito | requisitos com situação; texto do requisito |
| Objetivos | `objetivos-<dir>.html` | por objetivo: dor · impacto · evidência · entregas que o atendem e a situação de cada |
| Entregas (faixa 4 e Top 5) | `etapa-<dir>-eN.html` — **a página da entrega** | ver "Página da entrega" |
| Tarefas em curso | `etapa-<dir>-eN.html#tarefas` | tarefas da entrega |
| Defeitos | `defeitos-<dir>.html` | todos os defeitos, pela ordem de criticidade |
| Pendências do cliente | página da área do cliente do projeto | pendências com prazo e o link para responder |
| Impedimentos e riscos | `debitos-<dir>.html#impedimentos` | impedimentos e riscos, pela ordem de criticidade |

## Página da entrega

Entrega = etapa do cronograma = épico (1 para 1; o marco casa com a etapa pelo prefixo `M1`, `S2`…). A página de épico, `etapa-<dir>-eN.html`, passa a abrir como página da entrega:

1. **"M1 — nome da entrega"**, situação (Entregue · Aguardando aceite · Atrasada +N dias · Prevista), prazo e data de entrega.
2. **O que é a entrega** — a frase da coluna `Entrega` da tabela de marcos; sem ela, "—".
3. **Objetivos que a entrega atende** (`Atende: On`).
4. **Tarefas**: `ID · Tarefa · Esperado · Entregue`. O esperado é o texto do requisito quando a tarefa cita `RF-NN`/`RNF-NN` (extraído do PRD, com link para a página do requisito); sem requisito, a coluna `Esperado` do arquivo de épicos; sem as duas, "—". Entregue = `Sim` quando a tarefa está `feita`, `Não` nos demais.
5. **Issues no sistema externo**, **defeitos** e **pendências** ligados à entrega.
6. Dependências (grafo) e registros de progresso, como já descritos na SKILL.md.

**% da entrega**: tarefas feitas ÷ tarefas, quando há tarefas; sem tarefas, o peso da etapa (`feita = 1 · em curso = 0,5 · prevista = 0`). É o "marco como micro-projeto": cada etapa concluída soma a sua fração.

## Saúde

O pior valor entre três regras, cada uma com nome — a seção `#saude` mostra qual disparou:

| Regra | Vermelho | Amarelo |
|---|---|---|
| **Prazo e ritmo** (farol vigente da SKILL.md) | prazo estourado; ou previsão probabilística passa do prazo | % de trabalho abaixo do % de calendário − 10 p.p. |
| **Marcos** | marco de base contratual atrasado | outro marco atrasado |
| **Itens abertos** | algum item de nível Crítica aberto | algum item de nível Alta vencido |

| Nível | Forma | Classe |
|---|---|---|
| verde | `●` | `.saude.ok` |
| amarelo | `▲` | `.saude.warn` |
| vermelho | `◆` | `.saude.crit` |
| não iniciado | `○` | `.saude` |

**Tendência.** Compara a saúde desta semana com a última linha do histórico versionado (uma linha por projeto por semana, anexada quando o report semanal é aprovado): `↑` melhorou · `→` estável · `↓` piorou · `—` sem histórico. O histórico é fonte versionada, não saída gerada — a saída continua fora do git.

## Criticidade

Quatro níveis — **Crítica · Alta · Média · Baixa** — com uma única regra de ordenação para todas as tabelas.

| Origem do item | De onde sai o nível |
|---|---|
| Defeito (issue do tipo bug) | prioridade do sistema externo: mais alta → Crítica · alta → Alta · média → Média · baixa e mais baixa → Baixa |
| Débito e pendência | a `fila` do registro de débitos, pela mesma faixa que o repo já usa para projetar a prioridade no sistema externo (reusar a função, não redefinir a tabela) |
| Impedimento | prioridade declarada na pergunta em aberto (alta → Alta · média → Média · baixa → Baixa) |
| Item parado em andamento | Média; os dias parado contam como atraso |
| Risco | nível declarado na seção `### Riscos` do bloco do projeto no cronograma |

- **Vencido sobe um nível**, com teto em Crítica.
- **Ordem**: nível decrescente → dias de atraso decrescentes → id.
- Item sem nível na origem fica Média — nunca some da tabela.

## Objetivos

De 1 a 4 por projeto, no bloco do projeto no cronograma ([template](templates/cronograma-template.md)): o **objetivo é o critério de sucesso que o projeto declara para si** — que dor resolve, que impacto traz, que evidência mostra que foi atingido. Não é OKR e não depende de um.

- Situação do objetivo: `●` quando todas as entregas que o atendem estão feitas · `◐` quando alguma está feita ou em curso · `○` nos demais (inclusive quando nenhuma entrega o atende).
- **Projeto sem objetivo de impacto** — entrega operacional, regulatória ou de infraestrutura — declara a frase de dispensa; a faixa mostra a frase. Objetivo inventado para preencher a faixa é erro.
- Mais de 4 objetivos, ou nenhum sem a frase de dispensa: o self-check reprova a geração.

## Canal do cliente

Linha que aguarda o cliente (pendência, homologação, aceite de marco) traz **"Responder no help center"** quando o repo declara a URL do help center JSM do cliente: link pré-preenchido com o projeto e o item de origem. A resposta nasce no sistema externo e volta ao site pela coleta — o render não escreve em sistema externo (invariante "coleta separada do render").
