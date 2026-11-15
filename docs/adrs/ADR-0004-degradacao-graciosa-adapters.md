# ADR-0004: Degradação graciosa por adapters — motores de terceiros com contrato e fallback

- **Status:** Accepted
- **Data:** 2026-07-18
- **Supersedes:** —
- **Superseded by:** —

## Context

> Registrada retroativamente em 2026-07-19, no backfill de ADRs da varredura de registros.
> A decisão vige desde o desenho do ciclo (backfill delta-000) e está consolidada em
> R8/R9/RNF2 do `specs/TRUTH.md` e em `skills/spec-feature/references/adapters.md`.

O ciclo do sdd-iuri não reimplementa as fases que outros plugins já fazem bem: clarify delega ao
grill-me (max), plan/implement/review ao superpowers, e o anti-over-engineering ao ponytail. Isso
cria dependência de código de terceiros que **não controlamos**: pode faltar na máquina do
usuário, pode mudar de contrato num upgrade, pode ser abandonado.

Alternativas consideradas:

1. **Forkar/vendorizar os motores** dentro do framework, congelando versões conhecidas.
2. **Dependência dura:** fase sem motor aborta o ciclo com erro.
3. **Contrato por fase + fallback nativo:** `adapters.md` declara, para cada fase, o motor, o
   contrato de formato/destino, o ponto sensível a breaking change e um fallback nativo; plugin
   ausente degrada a fase com aviso explícito.

## Decision

Adotamos a alternativa 3. `adapters.md` é a tabela de contrato: uma linha por fase, com
verificação pós-fase e **uma seção de fallback para cada motor** (RNF2). Plugin ausente degrada a
fase — nunca quebra o ciclo (R9). O superpowers é aceito como **dependência não forkável**: a
disciplina dele (brainstorm antes de plan, TDD no implement) é o valor que justifica a delegação.

Renunciamos ao fork/vendor (1) porque congelaria os motores no estado do fork — perdendo as
correções deles — e duplicaria manutenção de código que não é nosso, violando a regra do repo de
não refatorar conteúdo vendored. Renunciamos à dependência dura (2) porque o custo de um plugin
ausente cairia na pior hora (meio do ciclo, trabalho em andamento) e por motivo alheio ao usuário.

## Consequences

**Fica mais fácil:** o ciclo nunca trava por ambiente; instalar um motor é opcional e o ganho é
incremental; upgrade de motor é uma linha na tabela de política de versões; o ponto sensível de
cada integração está nomeado antes de quebrar.

**Fica mais difícil:** o fallback nativo é honestamente **mais fraco** que o motor (uma
conferência inline não é um grill-me) — a degradação é real, só que anunciada; breaking change de
motor só se descobre no uso, porque não há teste de integração contra os plugins de terceiros.

**Reabre quando:** um motor for abandonado ou quebrar contrato em sequência — aí vendorizar a
versão estável (1) volta à mesa para aquele motor específico, via nova ADR.
