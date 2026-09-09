# ADR-0010: HANDOFF.md renomeia STATE.md — o diário de bordo é o ponto de entrada da retomada

- **Status:** Accepted
- **Data:** 2026-07-24
- **Supersedes:** — <!-- não supersede a ADR-0007: a arquitetura de registros com dono fica intacta; só o quarto registro (o diário) muda de nome -->
- **Superseded by:** —

## Context

A delta-007 ([ADR-0007](ADR-0007-registros-com-dono.md)) fixou quatro registros com dono: CHANGELOG (histórico), `specs/TRUTH.md` (o que vige), ADRs (decisões com renúncia) e `STATE.md` (diário de bordo — andamento em janela rolante). O `STATE.md` já concentra "onde paramos / o que falta / próximos passos" nas suas quatro seções — ou seja, **já é** o documento de handoff da sessão.

Duas fricções, porém, apareceram no uso: (1) o nome "STATE" não comunica que aquele é o arquivo a ler para retomar; (2) o prompt de retomada da skill `handoff` (R20) manda "Leia o STATE.md (e o DEBT.md)", e retomar de fato exige cruzar vários registros. O pedido concreto foi poder dizer só "leia o handoff e continue de onde paramos".

A saída ingênua — criar um `HANDOFF.md` **ao lado** do `STATE.md` — recria dois donos de "onde paramos", exatamente o acumulador que a delta-007 desmontou (regra de ouro: uma informação, um dono).

## Decision

Renomeamos `STATE.md` → `HANDOFF.md` em todo o framework e **eliminamos o conceito STATE**. O `HANDOFF.md` preserva integralmente a natureza do STATE.md: diário de bordo, janela rolante, "união das verdades" no merge, e **digest que roteia** — referencia DEBT/TRUTH/delta por ID/caminho, nunca copia conteúdo de dono alheio. "Handoff" nomeia o *propósito* (o que a próxima sessão lê); "diário de bordo" continua descrevendo a *natureza*.

Renúncias registradas:
- **Manter o nome `STATE`** — rejeitado: o valor da mudança é justamente o nome falar "handoff", que é como o trabalho é retomado.
- **Adicionar um `HANDOFF.md` ao lado do `STATE.md`** — rejeitado: dois donos de "onde paramos" violam a regra de ouro e ressuscitam o acumulador que a delta-007 matou.
- **`HANDOFF.md` como brief autocontido** (copiar DEBT/TRUTH/delta para dentro) — rejeitado: mesma violação, mais disciplina de sincronização manual. O ponto de entrada único se obtém porque o `HANDOFF.md` *roteia*, não porque duplica.

Esta ADR **não supersede** a ADR-0007 nem a ADR-0008 ([skill handoff própria](ADR-0008-skill-handoff-propria.md)): a arquitetura de registros com dono e a existência da skill continuam; só o nome do quarto registro muda. Consolidada no TRUTH via MUDA R19 e MUDA R20 (delta-010).

## Consequences

Fica mais fácil: a retomada tem um ponto de entrada com nome autoexplicativo — "Leia o `HANDOFF.md` e continue de onde paramos" — e o prompt da skill vira uma linha só.

Fica mais difícil / custo aceito:
- **Breaking para repos consumidores** já scaffoldados (têm `STATE.md`). A skill `handoff` passa a migrar em runtime (`git mv STATE.md HANDOFF.md` quando há legado e não há `HANDOFF.md`); o CHANGELOG e o commit registram `BREAKING CHANGE:` com o caminho de migração.
- **Referências mortas** a `STATE.md` em `specs/_archive/**` e nos ADRs Accepted (0001, 0007, 0008) permanecem — são imutáveis. Catalogadas como guarda `DT-010` no `DEBT.md` ("não corrigir, não migrar"), no mesmo espírito da DT-006.
- Raio de alcance da renomeação: skill, template, `canonical-rules.md`, `detection.md`, `CLAUDE.md`, `TRUTH.md`, `deps.toml` (o `exclude_globs` precisa acompanhar) e `README.md`.
