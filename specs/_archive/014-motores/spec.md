# delta-014 — motores
Estado: arquivada · Data: 2026-07-28 · Branch: feat/014-motores

## Contexto (≤3 linhas)
Fase 1 do plano de upgrade: o upstream do max (mattpocock/skills) removeu `write-prd` e fatorou o loop de entrevista na skill-motor `grilling` — o contrato dos adapters está ancorado numa API que só sobrevive no plugin distribuído (0.8.0). Decisão com o usuário (2026-07-28): **manter o pin como fork deliberado** e registrar divergência + gatilho de migração. Aproveita para formalizar o review em dois eixos paralelos (padrão Pocock/superpowers, já exercitado na delta-013).

## Mudanças

### R1 — ADICIONA: política de pins com verificação datada e divergência upstream registrada
- DADO a tabela de política de dependência em `adapters.md` QUANDO a delta consolida ENTÃO cada motor declara versão testada, faixa aceita, **data da última verificação** e, quando houver, **nota de divergência upstream com gatilho de reavaliação** — para o max: fork deliberado da 0.8.0 (upstream removeu `write-prd` e fatorou `grilling`), gatilho na delta-017 (ADR-0012)
- DADO o superpowers verificado em 2026-07-28 QUANDO a tabela é lida ENTÃO ela registra a última upstream verificada (6.2.0, dentro da faixa 6.x) sem alegar teste que não ocorreu (testada segue 6.1.1)

### R2 — ADICIONA: review em dois eixos independentes, paralelos quando houver subagentes
- DADO uma delta na fase review num harness com subagentes QUANDO o review roda ENTÃO os dois estágios executam como **eixos independentes em subagentes paralelos** — eixo **Spec** (conformidade: cada Rn/RNFn confrontado com o diff) e eixo **Qualidade** (ponytail-review/delete-list) — cada um cego ao contexto do outro, e os achados convergentes dos dois eixos são tratados antes do PR
- DADO um harness sem subagentes ou motor ausente QUANDO o review roda ENTÃO os estágios rodam inline em sequência com os fallbacks e avisos vigentes dos adapters (RNF2 preservado)

## Fora de escopo
- Migrar o contrato para `grilling`/`to-spec`/`to-tickets` — renúncia registrada na ADR-0012; reavaliação na delta-017 (Fase 4, tickets).
- Contrato duplo (detecção do formato novo do max) — flexibilidade sem consumidor: o plugin distribuído segue 0.8.0.
- Atualizar o plugin superpowers local (6.0.3 → 6.2.0) — ação de ambiente do usuário (`/plugin update`), não do framework.

## Dependências e riscos
- ADR-0012 (recontratação dos motores) gravada nesta delta — decisão durável com renúncias explícitas.
- Risco aceito: o fork do max congela ganhos do upstream (wayfinder, to-tickets) até a delta-017; mitigado pelo gatilho registrado.
- A verificação de versão upstream é pontual (2026-07-28) — repos fast-moving; a data na tabela existe para denunciar staleness.
