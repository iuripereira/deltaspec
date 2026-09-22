# ADR-0026: Recontratação híbrida — clarify no mattpocock-skills oficial, write-prd permanece no fork max

- **Status:** Accepted
- **Data:** 2026-08-09
- **Supersedes:** ADR-0024
- **Superseded by:** —

## Context

O ADR-0024 manteve o fork integral do `max@max4c-skills` 0.8.0 e deixou dois gatilhos de reavaliação: breaking change do plugin distribuído, ou o upstream ganhar projeção de tickets. O segundo disparou: o plugin oficial `mattpocock-skills@claude-plugins-official` v1.2.3 (instalado e verificado em 2026-08-09) traz `to-tickets` publicando no tracker do repositório, além de uma reorganização relevante dos motores que o deltaspec contrata:

- `grill-me` e `grill-with-docs` viraram stubs de **`grilling`** — entrevista por rodadas em lote (fronteira de perguntas desbloqueadas, formato `❓ Q1` com resposta recomendada), com fatos delegados a subagentes em vez de perguntados ao usuário. Sem o relatório quantificado de ambiguidade do fork.
- A substância domain-aware do `grill-with-docs` (glossário, CONTEXT.md, teste de ADR) foi extraída para a skill reutilizável **`domain-modeling`**.
- **`write-prd` segue sem equivalente**: o upstream `to-spec` é síntese sem entrevista, publicada no tracker — o oposto do motor de PRD entrevistado que a `descoberta` oferece (R30).
- `to-tickets` gera tickets tracer-bullet no tracker do repositório (GitHub), não a projeção Jira declarativa do deltaspec (`tickets.py`, ADR-0021: repo como fonte, Jira como projeção idempotente por chave, escada de automação com degradação graciosa).

Decisões do usuário em 2026-08-09 (entrevista da delta-039): estratégia híbrida; execução como delta no próprio ciclo.

## Decision

Recontratamos o clarify no plugin oficial e reduzimos o escopo do fork:

1. **Motor do clarify:** `mattpocock-skills:grilling`; com gatilho durável (contrato externo · modelo de dados persistente · dependência nova · segurança), `grilling` + `mattpocock-skills:domain-modeling`. O critério de saída passa a ser **fronteira vazia** com decisões consolidadas na spec — substituto declarado do gate quantificado do grill-me (R8/delta-039). A trilha do clarify (C12), a marcação `entrevistado`/`auto-avaliado` e o contrato de ADR na invocação permanecem intactos.
2. **Fork do max reduzido a `write-prd`:** pin 0.8.0 mantido exclusivamente como motor do PRD entrevistado da `descoberta` (R30). Gatilho de reavaliação novo: o upstream ganhar um motor de PRD **entrevistado** (não `to-spec`), ou breaking no 0.8.0 distribuído.
3. **`to-tickets` avaliado e não adotado:** cumpre o gatilho do ADR-0024, mas serve tracker do repositório; a projeção Jira do ADR-0021 continua no `tickets.py`. Projetos com tracker GitHub podem avaliá-lo por conta própria — fora do contrato do ciclo.
4. **Renúncia a `to-spec` como consolidador:** a consolidação entrevista→spec segue passo nativo (cycle.md), mesma razão do ADR-0012 — o formato delta-spec é do framework, não do motor.
5. Os demais candidatos do oficial (`research`, `to-questionnaire`, `wizard`, `code-review`) ficam **analisados, não adotados** (`specs/_archive/039-recontratacao-motores/analise-skills.md` após o archive); cada adoção exige delta própria com contrato e fallback nos adapters.

## Consequences

- Clarify passa a acompanhar o upstream ativo (changesets, releases frequentes) em vez de um fork parado desde 2026-06; rodadas em lote custam menos tokens que entrevista pergunta-a-pergunta e a regra "fatos são trabalho do agente" reduz perguntas desnecessárias ao usuário.
- Perde-se o relatório quantificado de ambiguidade; o viés de auto-avaliação muda de forma (grau otimista → resposta recomendada que induz carimbo) e o contrato do adapter passa a nomeá-lo assim. Primeira delta real conduzida pelo `grilling` valida o critério substituto na prática (risco registrado na delta-039).
- Dependência nova no caminho do clarify (`mattpocock-skills@claude-plugins-official`, testada 1.2.3); mitigada pelo fallback nativo já existente nos adapters — plugin ausente degrada com aviso, como sempre (ADR-0004).
- O fork do max encolhe para uma única skill contratada: menos superfície exposta a divergência upstream; `instala-motores.sh` e o passo 6 do projeto-init passam a verificar os dois plugins.
