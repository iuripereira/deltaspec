# ADR-0024: Pin do max reavaliado na delta-017 — fork 0.8.0 mantido

- **Status:** Accepted (2026-08-07, delta-017)
- **Data:** 2026-08-07
- **Supersedes:** —
- **Superseded by:** —

## Context

A [ADR-0012](ADR-0012-recontratacao-motores.md) tornou o pin `max@max4c-skills` 0.8.0 um fork deliberado e amarrou a reavaliação à delta-017 — o momento em que `to-tickets`/`wayfinder` ganhariam consumidor no ciclo. A delta-017 chegou (Fase 4, projeção de tasks para Jira) e a verificação de 2026-08-07 no plugin **distribuído** constatou: a API contratada segue intacta (`grill-me`, `grill-with-docs`, `write-prd` presentes em 0.8.0), e o `to-tickets` upstream existe apenas como flag do `cookoff`, emitindo "Dahso Agent Tickets" para o orquestrador `dahso:go` — um ecossistema próprio, **não** uma projeção Jira. O consumidor previsto pela ADR-0012 não se materializou: o que a delta-017 precisa (tickets no Jira via acli, corpo íntegro, links de bloqueio) o upstream não oferece.

Alternativas consideradas:

1. **Migrar para o upstream (`grilling`/`to-spec`/`to-tickets`):** exigiria MUDA no R30 e retrabalho da `descoberta`, para adotar um formato de ticket que serve outro orquestrador — custo alto, ganho nulo para a projeção Jira.
2. **Manter o fork 0.8.0, com a reavaliação cumprida registrada e gatilho novo:** o contrato segue funcional e o custo do fork permanece visível e datado.

## Decision

Adotamos a alternativa 2, decidida com o usuário em 2026-08-07 (clarify da delta-017): **o fork `max@max4c-skills` 0.8.0 é mantido.** A reavaliação prevista pela ADR-0012 está cumprida; a tabela de política dos adapters recebe a re-verificação datada de 2026-08-07 (implement da delta-017). **Gatilho novo de reavaliação:** breaking do plugin distribuído (skill contratada ausente/renomeada — a detecção da ADR-0004 degrada com aviso e denuncia), ou o upstream passar a oferecer projeção de tickets para ferramenta externa (Jira/GitHub) em vez do formato Dahso.

## Consequences

**Fica mais fácil:** o ciclo segue sobre a API testada; a delta-017 constrói a projeção Jira sem esperar alinhamento upstream; a pergunta da ADR-0012 tem resposta datada em vez de pin silencioso.

**Fica mais difícil:** ganhos do upstream continuam congelados (agora sem prazo novo além do gatilho por evento); a tabela de política exige manter a disciplina de verificação datada a cada delta que toque os adapters.
