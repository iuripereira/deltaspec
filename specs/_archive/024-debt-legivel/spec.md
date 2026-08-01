# delta-024 — DEBT.md legível: bloco por item e referências navegáveis
Estado: arquivada · Data: 2026-08-01 · Branch: feat/024-debt-legivel · Perfil: completo — muda o formato do registro canônico (MUDA R18/R51) e o parser que o lê (aprovado: 2026-08-01)
<!-- Clarify: conduzido em 3 perguntas fechadas (2026-08-01) sobre formato, links e onde a regra é explicada — decisões no bloco Contexto; não re-entrevistar. -->

## Contexto (≤3 linhas)
A delta-023 deixou o `DEBT.md` com 11 colunas e linhas de até 1.549 caracteres; o campo `Título` repete literalmente o início da `Descrição` e as chaves de ticket (`gh#88`) e as referências de origem (`PR #2`, `delta-004`) são texto morto. O usuário reportou que "as colunas estão confusas" e "não ficou claro como a regra é aplicada" — feedback de usabilidade sobre o que acabou de ser entregue.

## Mudanças
<!-- só o que muda; um bloco por requisito; ADICIONA/MUDA/REMOVE em relação ao TRUTH.md -->

### R1 — MUDA R18 (delta-023): o registro é um bloco por item, não uma linha de tabela
- DADO um débito, pendência ou guarda QUANDO registrado ENTÃO ele é um bloco iniciado por `### DT-NNN · <natureza> · <estado>`, seguido do título em negrito, da descrição em prosa livre e dos campos na forma `- **Campo:** valor` — a numeração `DT-NNN` segue global e nunca reutilizada
- DADO um item de natureza `débito` ou `pendência` ativo QUANDO ele é registrado ENTÃO tem os campos **Fila**, **Local**, **Gatilho** e **Origem**; `guarda` dispensa Fila e Local, por não ter principal nem juros
- DADO um item encerrado (`quitado` ou `descartado`) QUANDO o bloco é escrito ENTÃO a data e a referência saem do rótulo de estado e vivem no campo **Encerrado**, que é obrigatório — o estado no cabeçalho fica escaneável e a justificativa cabe em prosa
- DADO o cabeçalho do arquivo QUANDO alguém o abre ENTÃO encontra uma legenda curta que explica **cada estado** (incluindo o `stale` derivado) e os três eixos da fila, sem reproduzir os limiares que pertencem ao script
- DADO o registro no formato de tabela da delta-023 ou anterior QUANDO o script o lê ENTÃO reporta que o formato é antigo e como converter, sem quebrar — o registro segue válido

### R2 — MUDA R51 (delta-023): a fila é calculada sobre blocos, com referências navegáveis
- DADO um `DEBT.md` no formato do R1 QUANDO `debito.py fila` roda ENTÃO ele produz a mesma fila de antes (override → trilha → score decrescente, score derivado e nunca gravado), lendo os campos pela **âncora canônica** de cada linha — prosa que mencione a sintaxe não vira campo
- DADO uma referência a ticket, PR, issue ou delta QUANDO ela aparece num bloco ENTÃO é um link navegável: ticket e PR por caminho relativo do próprio repositório (`../../issues/N`, `../../pull/N`), delta para o diretório em `specs/_archive/`, e `Local` para o artefato — o link do `Local` continua validado
- DADO um item já projetado QUANDO o script exporta ENTÃO a chave do ticket é lida do campo **Ticket** do bloco e o item é pulado, preservando a idempotência por chave

## Fora de escopo
- Mudança no cálculo do score, na política de fila ou no contrato da projeção — a delta-023 os fixou e eles não estão em questão.
- Propagação ao template distribuído do `projeto-init` (segue no DT-022, depois do dogfood).
- Reclassificar naturezas ou revisar os valores de `Fila` já atribuídos.

## Dependências e riscos
- O parser muda de tabela para blocos: todo o selftest da delta-023 precisa migrar junto, incluindo a fixture de regressão de prosa.
- Links relativos `../../issues/N` dependem da convenção de resolução do GitHub para arquivos na raiz; em outra forja o link não resolve — aceito, porque a alternativa (URL absoluta) quebraria em fork.
- A conversão das 22 linhas existentes é mecânica e será feita por script, não à mão.
