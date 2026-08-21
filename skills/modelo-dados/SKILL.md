---
name: modelo-dados
description: Use when a project needs its data model documented or audited in the deltaspec cycle — the skill keeps three layers with a single owner each (conceptual docs/data-model.md, field-level DATA_DICTIONARY.md, executable schema.dbml), derives the Mermaid ERD from the .dbml and runs the deterministic gate check_data_model.py (M1 parseable contract, M2 orphan entities, M3 ERD drift). Triggers include "/deltaspec:modelo-dados", "modelo de dados", "data model", "modelar entidades", "auditar dicionário", or the doc-profile category `modelo-dados` being mandatory in a spec.
---

# modelo-dados

## Overview

Mantém o modelo de dados em **três camadas com dono único** — conceitual (`docs/data-model.md`), semântica (`DATA_DICTIONARY.md`) e contrato (`schema.dbml`) — e o gate que as mantém coerentes. A regra das camadas, o subconjunto DBML que o parser lê, a sanitização do ERD e as severidades vivem em [references/camadas.md](references/camadas.md): esta SKILL.md orquestra, não repete.

Esta delta (073) cobre a camada conceitual e o gate M1–M3. **A camada semântica — template novo do dicionário, checks M4–M6 e os modos `auditar`/`padronizar` — chega na delta-074.** Pedido de auditar ou padronizar o dicionário antes disso: avise em 1 linha e encerre.

## Fluxo

1. **Ler o `doc-profile.yaml`.** `artefatos.modelo-dados.obrigatorio: true` é o caso normal (gate de doc visual do specify, `cycle.md`). Perfil ausente ou categoria opcional → avise em 1 linha que o perfil não exige o artefato e siga (RNF2).
2. **Resolver o contrato**: `<artefatos.modelo-dados.saida>/schema.dbml` (`saida` ausente → `docs/diagrams/`). Sem `.dbml` → modele com o usuário primeiro (entidades, cardinalidades, chaves — o gatilho `domain-modeling` do clarify continua valendo) e escreva o contrato antes de qualquer outra coisa.
3. **Gerar o ERD** na fence de `## Visão`:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/skills/modelo-dados/scripts/check_data_model.py gerar-erd --escrever
   ```
   `docs/data-model.md` inexistente → crie-o de [references/templates/data-model.md](references/templates/data-model.md) (nome fixo) e rode de novo. O script nunca cria o artefato conceitual.
4. **Sincronizar entidades**: para cada `Table` sem `### <nome físico>` sob `## Entidades`, acrescente o stub do template ao fim da seção. Heading sem `Table` **fica** — é achado do M2 e decisão do usuário (regra do heading: camadas.md).
5. **Preencher a camada conceitual com o usuário**: propósito em uma frase na linguagem ubíqua, agregado/contexto, relações com o porquê, invariantes cross-campo citando `Rn`/`RN`. Tipo de coluna e definição por campo **não** entram aqui — são camadas 3 e 2.
6. **Rodar o gate** e colar a tabela no `analyze.md`, abaixo da do `check_cycle.py`:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/skills/modelo-dados/scripts/check_data_model.py check
   ```
   Exit 1 = há ALTO (M1–M3 ou artefato ausente); a coluna "Ação sugerida" diz o que fazer. Severidade máxima ALTO na v1 ([ADR-0038](../../docs/adrs/ADR-0038-modelo-de-dados-em-tres-camadas-com-dono-unico.md)).

Fim de fase = commit do `.dbml` e do `data-model.md` juntos — o M3 acusa qualquer um dos dois que andar sozinho.

## Erros comuns

| Erro | Correto |
|---|---|
| Editar o `erDiagram` à mão para "ajustar" | Mude o `.dbml` e rode `gerar-erd --escrever`; o M3 acusa drift |
| `### Pedido` para a `Table pedidos` | Heading = nome físico; "Pedido" vai na frase de propósito (camadas.md) |
| Listar tipos e campos no `data-model.md` | Tipo é do `.dbml`; definição por campo é do dicionário (camadas 3 e 2) |
| Apagar a seção de uma `Table` removida | Deixe o M2 acusar; remover é decisão humana |
| `.dbml` fora do subconjunto e "ajustar" o parser para passar | Corrija na linha que o M1 aponta; ampliação do subconjunto é `fix` com fixture |

## Arquivos da skill

- `references/camadas.md` — **dona** das regras: donos das camadas, unidirecionalidade, subconjunto DBML, sanitização e arestas do ERD, heading da entidade, severidades.
- `references/templates/data-model.md` — template do artefato vivo `docs/data-model.md`.
- `scripts/check_data_model.py` — `gerar-erd` (ERD determinístico, `--escrever`), `check` (M1–M3, formato do `check_cycle.py`), `--selftest`. `parse_dbml` é função pura, importável pela delta-074.
