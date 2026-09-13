# Modelo de dados em três camadas — regra canônica

Dona única das regras da skill `modelo-dados` (delta-073 · delta-075, [ADR-0038](../../../docs/adrs/ADR-0038-modelo-de-dados-em-tres-camadas-com-dono-unico.md)). `SKILL.md`, o template e o `cycle.md` linkam este arquivo; nenhum deles reproduz as tabelas abaixo.

## Donos

Modelo responde **"como as coisas se relacionam"**; dicionário responde **"o que exatamente é este campo, quem é dono, o que é valor válido, de onde veio"**.

| Camada | Pergunta que responde | Arquivo dono | Quem escreve | Quem lê |
|---|---|---|---|---|
| 1 · conceitual | o que cada entidade é, por que se relaciona, que invariantes valem | `docs/data-model.md` | a skill com o usuário, na linguagem ubíqua | spec, plan, revisor humano |
| 2 · semântica | o que é este campo, domínio de valores, steward, sensibilidade, origem, qualidade | `DATA_DICTIONARY.md` | descoberta (append/merge) e o modo `auditar` | dicionário por campo, LGPD, integração |
| 3 · contrato | tabelas, colunas, tipos físicos, chaves, relações | `<artefatos.modelo-dados.saida>/schema.dbml` (`saida` ausente → `docs/diagrams/`; outro `.dbml` na pasta é ignorado) | quem modela o banco; ferramenta decidida na [ADR-0009](../../../docs/adrs/ADR-0009-documentacao-visual-gate-configuravel.md) | `gerar-erd`, DDL, ORM |

Camada 1 **cobre as três por composição**: o `data-model.md` carrega o ERD derivado da camada 3 e linka a camada 2 — não contém tipo por campo nem definição de negócio por campo.

## Unidirecionalidade

A informação flui **só** `.dbml → erDiagram`. O bloco ```` ```mermaid ```` de `## Visão` é regenerado por `check_data_model.py gerar-erd --escrever` e conferido byte a byte pelo M3; edição à mão nele é drift, não contribuição. Significado, invariante e renúncia não são deriváveis do contrato — nascem na camada 1 e nunca voltam ao `.dbml` por script. Mesma regra da camada de apresentação no `cycle.md` (fonte versionado governa).

## Subconjunto DBML que o parser lê

O parser é regex stdlib (`parse_dbml`, função pura importável). Antes de ler, faz **blanking**: apaga comentários (`//`, `/* */`) e strings (`'…'` com `\'` escapado, `'''…'''`, `` `…` ``) preservando a contagem de linhas, para que `{`/`}` dentro de `Note` ou comentário não contem. **Aspas duplas ficam** — em DBML delimitam identificador (`Table "itens do pedido"`, tipo `"double precision"`), não string.

| Entra | Ignorado sem erro | Cai em M1 |
|---|---|---|
| `Table [schema.]nome [as alias] [settings] { … }` — nome emitido é o físico (último segmento, sem aspas, sem schema) | `Project`, `Enum`, `TableGroup`, `TablePartial`, `Ref { }` em bloco (pulados por profundidade) | `{`/`}` desbalanceada (acusa a linha de abertura) |
| coluna `nome tipo [settings]`; settings brutos preservados (`pk`/`primary key` → `pk`, `not null`, `unique`, `default`, `note`, `ref`) | `indexes { }` e `Note { }` dentro da `Table`; linha `Note: …` | `Table` sem `{` na mesma linha |
| `Ref [nome]: a.x <op> b.y [settings]` com `<op>` em `>` `<` `-` `<>`; `ref: <op> b.y` inline na coluna | `Ref` composta `(x,y)` e qualquer linha fora de bloco que o parser não reconhece | linha dentro de `Table` que não é coluna do subconjunto |
| alias resolve para a tabela (`Ref: pedidos.cliente_id > C.id`) | | `Ref` citando tabela ou coluna inexistente |

Ampliar o subconjunto é `fix` (PATCH) com fixture nova no `--selftest`; não pede ADR.

## ERD derivado — sanitização e arestas

Medido no validador oficial do Mermaid (2026-08-20): `erDiagram` rejeita vírgula e aspas no atributo (`decimal(10,2)` quebra o parse). Por isso tipo, nome de atributo, nome de entidade e rótulo passam pela mesma regra determinística:

1. aspas removidas;
2. parâmetros entre parênteses descartados — `varchar(255)` → `varchar`, `decimal(10,2)` → `decimal` (o contrato com parâmetros é o `.dbml`; o ERD é visão de estrutura);
3. todo caractere fora de `[A-Za-z0-9_]` vira `_` — `"double precision"` → `double_precision`, `itens do pedido` → `itens_do_pedido`.

`Table` sem coluna sai só como nome, sem bloco `{}`. `PK` vem do setting `pk`; `FK` é inferido da aresta. Ordem das entidades e das arestas = ordem do arquivo (inline primeiro, na linha da coluna; `Ref:` soltas na ordem em que aparecem).

| `Ref` | Aresta emitida (`um <conector> muitos : rótulo`) | FK marcada em |
|---|---|---|
| `a.x > b.y` | `b \|\|--o{ a : x` | `a.x` |
| `a.x < b.y` | `a \|\|--o{ b : y` | `b.y` |
| `a.x - b.y` | `a \|\|--\|\| b : x` | `a.x` |
| `a.x <> b.y` | `a }o--o{ b : x` | nenhuma |

Cardinalidade mínima é fixa (o DBML não declara opcionalidade).

## Heading da entidade no `data-model.md`

Sob `## Entidades`, cada `### Nome` é **o nome físico da `Table`** — o texto inteiro após `### `, comparado sem distinção de maiúsculas e sem aspas, **sem tolerância a sufixo**. Nome de negócio (`Pedido` para `pedidos`) vai na frase de propósito; alias no heading é extensão futura. O M2 é um set-diff honesto porque essa regra é estrita.

Ao atualizar um `data-model.md` existente, a skill **acrescenta** um stub para cada `Table` sem heading e **nunca remove** heading sem `Table`: o órfão é achado do M2 e decisão humana.

## Dicionário (camada 2)

`DATA_DICTIONARY.md`, na raiz do projeto (nome fixo). Cada entidade é um heading `## Nome` (sem `## Entidades` envolvente — diferente do `data-model.md`), seguido de uma linha de metadados `Origem: <sistema de registro> · Steward: <papel/pessoa> · Atualização: <transacional | carga diária>` e de uma tabela de 6 colunas por campo: `Campo (canônico · físico)` (formato "Nome · `nome_físico`"), `Definição de negócio`, `Domínio de valores`, `Tipo · obrig. · default`, `Sens.` (taxonomia: `pública | interna | pessoal (PII) | pessoal sensível`), `Qualidade`. `## Contratos entre módulos` é o único heading que **não** é entidade — mantido do template legado, descolamento de camada conhecido e não resolvido.

**Anti-circularidade é regra de autoria, não gate**: o nome canônico não deveria aparecer dentro da própria Definição, mas o M6 só verifica igualdade exata normalizada — substring falso-positivaria qualquer definição legítima que cite o termo.

`parse_dicionario` (função pura, `check_data_model.py`) lê o formato: célula com `|` literal escapa `\|`; linha de cabeçalho e a separadora `|---|` nunca viram campo; heading `## Nome` duplicado — só a primeira ocorrência é lida, a segunda vira erro que o M5 consome.

Limites conhecidos, aceitos na v1: linha de tabela com número de células diferente de 6, ou sem o campo físico entre crases, é descartada em silêncio — nenhum achado a denuncia. Campo duplicado só é detectado quando a entidade também existe no `.dbml` (M4); em projeto dicionário-only ou entidade órfã, duas linhas com o mesmo campo físico passam sem aviso.

## Severidades

| Check | O que acusa | Severidade | Correção sugerida |
|---|---|---|---|
| M1 | `.dbml` não parseia no subconjunto | ALTO (M2/M3/M4 se omitem) | corrigir o `.dbml` na linha apontada |
| M2 | `### Entidade` sem `Table`, ou `Table` sem `### Entidade` (data-model.md × .dbml) | ALTO | stub via skill / remover seção / acrescentar `Table` |
| M3 | bloco `erDiagram` ausente ou divergente do derivado | ALTO | `gerar-erd --escrever` |
| M4 | entidade/campo órfão nos dois sentidos (dicionário × `.dbml`), campo duplicado, tipo divergente | ALTO (se omite sem `.dbml`) | descrever no dicionário / corrigir o `.dbml` / corrigir a célula Tipo |
| M5 | Definição/Sens. vazias ou placeholder por campo; Steward vazio ou placeholder por entidade; entidade duplicada; dicionário sem nenhuma entidade | ALTO | preencher a célula / unir entidades duplicadas / documentar ao menos uma entidade |
| M6 | Definição normalizada igual ao nome canônico ou físico (tautologia) | **BAIXO, sempre** | descrever o que o campo representa, não repetir o nome |
| — | `modelo-dados` obrigatório sem `data-model.md` ou sem `.dbml` (exceto projeto **dicionário-only**: nem um nem outro, com `DATA_DICTIONARY.md` presente — roda só M5/M6, linha M4 acima) | ALTO | criar o artefato que falta |

Nunca CRÍTICO na v1: o gate nasce sem uso real em projeto consumidor. O gatilho de promoção (≈5 deltas de uso real sem falso positivo) e a exigência de ADR nova estão na ADR-0038. Perfil ausente ou categoria não obrigatória → o `check` se omite em 1 linha e sai 0 (RNF2); `--forcar` roda assim mesmo. Saída no formato do `check_cycle.py`, para colar no `analyze.md`.
