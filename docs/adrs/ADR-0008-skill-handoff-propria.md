# ADR-0008: Skill handoff própria — nem vendorizada, nem delegada

- **Status:** Accepted
- **Data:** 2026-07-20
- **Supersedes:** —
- **Superseded by:** —

## Context

A delta-008 precisava de um executor de fim de sessão que gravasse o andamento nos registros com
dono (STATE.md diário de bordo, DEBT.md — delta-007/ADR-0007). Existia uma skill de handoff
madura e minimalista em mattpocock/skills (MIT, ~15 linhas, EN), e o ambiente do usuário já tem a
`max:handoff` com contrato parecido.

Alternativas consideradas:

1. **Vendorizar** a skill externa como está (EN, grava em diretório temporário do SO).
2. **Adaptar/traduzir** o arquivo vendorizado.
3. **Delegar** à `max:handoff` já instalada, como as fases do ciclo delegam aos motores.
4. **Skill própria**, PT-BR, inspirada na externa.

## Decision

Adotamos a alternativa 4: `sdd-iuri:handoff` própria, herdando da externa só os dois princípios
que se traduzem sem atrito (referencie artefatos por caminho em vez de duplicar; redija
segredos/PII), com crédito de cortesia no corpo — a MIT não exige atribuição para texto novo
apenas inspirado.

Renunciamos ao vendoring (1) porque a regra do repo ("não refatore conteúdo vendored") tornaria o
arquivo EN intocável dentro de um plugin PT-BR, congelado fora do ciclo de deltas que governa
`skills/`. Renunciamos à adaptação (2) porque editar vendored viola a mesma regra e borra
autoria sem ganho: o conteúdo aproveitável são seis frases. Renunciamos à delegação (3) porque o
contrato da `max:handoff` é o **oposto** do necessário: grava brief efêmero em `/tmp`, invisível
para outro clone/máquina, e ignora delta em curso, TRUTH e DEBT — o handoff do sdd-iuri precisa
ser o próprio repositório.

## Consequences

**Fica mais fácil:** o handoff é versionado e chega junto do `git pull`; a skill conhece o ciclo
(cita delta, fase, gate) e alimenta o DEBT.md antes de fechar o diário; sem dependência nova.

**Fica mais difícil:** mantemos texto próprio em vez de herdar evolução da skill externa; a
diferenciação com a `max:handoff` precisa ficar explícita para o usuário que tem as duas (ela =
brief efêmero de sessão; a nossa = registro persistente do repo — dito na SKILL.md).

**Reabre quando:** o contrato da skill externa convergir para registros versionados, ou o
framework passar a vendorizar skills de terceiros como política — aí vendoring volta à mesa, via
nova ADR.
