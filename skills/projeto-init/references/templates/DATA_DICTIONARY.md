# Dicionário de dados
<!-- Camada semântica (dona: definição, domínio, steward, sensibilidade, origem, qualidade). Estrutura/relações: docs/data-model.md · tipo físico: docs/diagrams/schema.dbml (dono — a coluna Tipo aqui é espelho conferido pelo gate, M4). Sensibilidade: pública | interna | pessoal (PII) | pessoal sensível (LGPD art. 5º II). Regra das camadas: skill deltaspec:modelo-dados, references/camadas.md (ADR-0038). -->

## {{Entidade}}
Origem: {{sistema de registro}} · Steward: {{papel/pessoa}} · Atualização: {{transacional | carga diária}}

| Campo (canônico · físico) | Definição de negócio | Domínio de valores | Tipo · obrig. · default | Sens. | Qualidade |
| --- | --- | --- | --- | --- | --- |
| {{Nome}} · `{{nome_fisico}}` | {{sem usar o próprio nome — anti-circularidade}} | {{enum a\|b\|c · faixa 0–100 · livre}} | {{tipo}} · {{sim/não}} · {{val ou —}} | {{taxonomia}} | {{regra verificável}} |

## Contratos entre módulos
- {{mantido do template atual — shape produzido/consumido; mudou o shape? ajuste os consumidores no mesmo PR}}
