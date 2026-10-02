# Modelo de dados — {{projeto}}
<!-- Camada conceitual (dona: este arquivo). Contrato: {{saida}}/schema.dbml (dono). Semântica por campo: DATA_DICTIONARY.md (dono). Regra das camadas: skill deltaspec:modelo-dados, references/camadas.md (ADR-0038). -->

## Visão
<!-- derivado do schema.dbml — NÃO edite; regenere: python3 ${CLAUDE_PLUGIN_ROOT}/skills/modelo-dados/scripts/check_data_model.py gerar-erd --escrever -->
```mermaid
erDiagram
  {{regenerado pelo gerar-erd}}
```

## Entidades
<!-- um `### <nome físico da Table>` por tabela do .dbml (regra do heading: camadas.md da skill); nome de negócio vai na frase de propósito -->
### {{tabela}}
{{1 frase de propósito na linguagem ubíqua}}
- Agregado/contexto: {{bounded context ou "—"}}
- Relações: {{outra_tabela — 1:N — porquê em meia frase}}
- Invariantes: {{regra cross-campo; cite RN/Rn}}

## Fora do modelo
- {{o que deliberadamente não se modela — renúncia registrada}}
