# ADR-0012: Pin do max é fork deliberado — divergência upstream documentada, migração com gatilho

- **Status:** Accepted (2026-07-28, delta-014)
- **Data:** 2026-07-28
- **Supersedes:** —
- **Superseded by:** —

## Context

O contrato dos adapters ([adapters.md](../../skills/spec-feature/references/adapters.md)) ancora o clarify em `max:grill-me`/`max:grill-with-docs` e o PRD da descoberta em `max:write-prd` (R30 do TRUTH). Em 2026-07-28, pesquisa verificada constatou que o repositório-fonte upstream (mattpocock/skills) **removeu `write-prd`** (o fluxo virou `to-spec` + `to-tickets`, ancorado em issue tracker) e **fatorou o loop de entrevista** na skill-motor `grilling` — enquanto o plugin **distribuído** (`max@max4c-skills` 0.8.0, o pin vigente) segue com a API contratada intacta. A política de versões já previa o fork ("forkável — pin na testada"), mas não registrava divergência nem prazo de reavaliação: um pin silencioso envelhece sem denunciar o custo.

Alternativas consideradas:

1. **Migrar já para `grilling`/`to-spec`/`to-tickets`:** alinha com o upstream vivo, mas exige MUDA no R30, retrabalho da fase 6 da `descoberta` e aceita semântica diferente (`to-spec` sintetiza sem entrevistar e publica em tracker — o ciclo não tem tracker até a Fase 4). Custo alto, ganho imediato nulo.
2. **Contrato duplo (detecção do formato novo):** flexibilidade sem consumidor — o plugin distribuído não contém as skills novas; seria manter dois contratos para um caminho que ninguém executa.
3. **Manter o pin 0.8.0 como fork deliberado, com divergência e gatilho registrados:** o contrato continua funcional; o custo (ganhos do upstream congelados) fica visível e datado na tabela de política, com reavaliação amarrada a um evento concreto.

## Decision

Adotamos a alternativa 3, decidida com o usuário em 2026-07-28: **o pin `max@max4c-skills` 0.8.0 passa a ser fork deliberado.** A tabela de política de dependência dos adapters ganha verificação **datada** por motor e a nota de divergência do max, com **gatilho de reavaliação na delta-017 (Fase 4 — plano→ticket)**: é quando `to-tickets`/`wayfinder` passam a ter consumidor no ciclo e a migração ganha valor real. Breaking do fork (plugin distribuído removendo as skills contratadas) antecipa o gatilho — a detecção vigente de skill ausente/renomeada já degrada com aviso (ADR-0004).

Renunciamos a (1) porque pagar MUDA R30 + retrabalho da descoberta agora compraria alinhamento sem função — e a semântica do `to-spec` (sem entrevista) conflita com o clarify entrevistado que o ciclo exige. Renunciamos a (2) porque contrato sem consumidor é a definição de flexibilidade morta.

## Consequences

**Fica mais fácil:** o ciclo segue estável sobre a API testada; o custo do fork é visível (data + nota na tabela, este ADR); a migração tem dono e momento — delta-017 — em vez de "um dia".

**Fica mais difícil:** ganhos do upstream (wayfinder multi-sessão, to-tickets com arestas de bloqueio, melhorias do grilling) ficam congelados até a delta-017; a tabela de política exige disciplina de re-verificação datada a cada delta que toque os adapters.
