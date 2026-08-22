# ADR-0005: Consolidação mecânica do archive — MUDA substitui integralmente, sem inferir intenção

- **Status:** Accepted
- **Data:** 2026-07-18
- **Supersedes:** —
- **Superseded by:** —

## Context

> Registrada retroativamente em 2026-07-19, no backfill de ADRs da varredura de registros.
> A decisão vige desde o desenho do archive (`cycle.md`, regra 2) e está consolidada no R7 do
> `specs/TRUTH.md`; o custo dela foi observado nas deltas 001 e 006.

No archive, a delta é consolidada no `TRUTH.md`: blocos ADICIONA entram, blocos MUDA trocam o
requisito vigente, blocos REMOVE o retiram. A pergunta de desenho: quando um MUDA altera só uma
parte do requisito (uma palavra do título, um cenário), o que acontece com o resto?

Alternativas consideradas:

1. **Merge semântico:** o agente compara o bloco da delta com o requisito vigente e mescla,
   preservando o que a delta "obviamente não quis mudar".
2. **Substituição integral:** o requisito vigente é trocado **por inteiro** pelo bloco da delta;
   o que não for repetido no bloco se perde.

## Decision

Adotamos a alternativa 2: **a consolidação é mecânica e não infere intenção** (R7). O bloco MUDA
carrega o requisito íntegro como deve vigorar; o cenário que não for repetido deixa de existir. O
gate C4 protege o outro lado: requisito que suma do `TRUTH.md` sem MUDA/REMOVE que o declare é
CRÍTICO.

Renunciamos ao merge semântico (1) porque ele devolveria juízo exatamente ao ponto que o framework
quis tornar determinístico: dois agentes (ou o mesmo em dias diferentes) mesclariam diferente, e um
"obviamente não quis mudar" errado corrompe a fonte da verdade em silêncio — o pior lugar possível
para um falso confiante.

## Consequences

**Fica mais fácil:** a consolidação é auditável (diff do TRUTH = blocos da delta, literal),
reproduzível e verificável por gate; o `TRUTH.md` nunca contém texto que nenhuma delta escreveu.

**Fica mais difícil:** renomear um termo citado em N requisitos custa **N blocos MUDA completos**,
cada um repetindo o requisito íntegro — observado na delta-001 (5 blocos para renomear a forma de
citar as skills) e na delta-006 (renotação `delta-NNN`). A delta-006 mitigou o caso específico de
sufixo: o C4 passou a medir perda por presença de ID, liberando reescrita de sufixo em massa sem
falso CRÍTICO.

**Reabre quando:** o custo do renome em massa se repetir fora do caso de sufixo já mitigado — a
candidata é uma operação mecânica de renome (find/replace declarado na delta e verificado pelo
gate), nunca a volta do merge semântico.
