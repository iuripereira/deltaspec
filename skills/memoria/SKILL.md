---
name: memoria
description: Use when deciding what to remember across sessions in a project that follows the deltaspec records — writes one fact per file to .claude/memory/ (state of an open front as agora-<front>, discarded path with evidence, user preference, external pointer), keeps MEMORY.md and HANDOFF.md as generated projections (memoria.py indice) and validates facts with memoria.py check. Triggers include "/deltaspec:memoria", "lembre disso", "salve na memória", "onde parei", "registre o estado da frente", or whenever a durable fact would otherwise live only in the conversation.
---

# Memória de projeto

Um fato por arquivo em `.claude/memory/`, versionado e revisado em PR ([ADR-0050](../../docs/adrs/ADR-0050-memoria-de-projeto-versionada.md)). O hook `SessionStart` do plugin injeta o índice na abertura; o fato é gravado por você, com a ferramenta Write, **no momento em que nasce** — não no fim da sessão.

## Formato do fato

`.claude/memory/<name>.md`, `name` igual ao nome do arquivo:

```markdown
---
name: agora-delta-132
description: delta-132 em implement, task 3 de 6; falta o selftest do indice
metadata:
  type: project
---

Corpo livre.
```

## Convenções

- `type` ∈ `user | feedback | project | reference`; chaves extras são toleradas; `project`/`feedback` levam linhas **Why:** e **How to apply:**; `description` numa linha, sem `: ` fora de aspas.
- **`agora-<frente>`**: um fato por frente aberta (delta, release, decisão pendente), **atualizado no lugar** e apagado quando a frente fecha. É o que a projeção lista em "Agora".
- **Inbox para `user` e `feedback`:** preferência do usuário e correção de rumo nascem em `.claude/memory/inbox/<name>.md` e ficam fora de `MEMORY.md` e `HANDOFF.md` até o usuário aprovar. `memoria.py aprovar <name> .` move o fato para `.claude/memory/` e carimba `aprovado: AAAA-MM-DD` em `metadata`. `agora-*`, `project` e `reference` vão direto para `.claude/memory/`, porque o PR os revisa.
- Segredo/PII nunca; nome real de terceiro pode (fora do allowlist de publicação).

## Fronteira com os registros com dono

Decisão com renúncia → ADR · débito ou pendência → `debito.py novo` · lição → `licao.py nova` · requisito → delta/TRUTH.

A memória guarda o que nenhum deles guarda: estado da frente, caminho descartado com evidência, preferência do usuário, ponteiro externo.

## Comandos

- `python3 ${CLAUDE_PLUGIN_ROOT}/skills/memoria/scripts/memoria.py check .` — gate: frontmatter, teto do índice e segredo, na raiz e no inbox. Reprova `user`/`feedback` na raiz sem `aprovado` e fato de outro tipo no inbox.
- `python3 ${CLAUDE_PLUGIN_ROOT}/skills/memoria/scripts/memoria.py indice .` — regenera `MEMORY.md` e `HANDOFF.md` (`--check` só compara). O inbox fica de fora.
- `python3 ${CLAUDE_PLUGIN_ROOT}/skills/memoria/scripts/memoria.py injetar .` — imprime o índice (o que o hook `SessionStart` roda) e, com fato no inbox, fecha com `N fato(s) aguardando aprovação em .claude/memory/inbox/`.
- `python3 ${CLAUDE_PLUGIN_ROOT}/skills/memoria/scripts/memoria.py aprovar <name> .` — move `inbox/<name>.md` para `.claude/memory/` com o carimbo `aprovado`. Recusa (sai 1) fato ausente, destino existente, fato com achado ou `name` com separador de caminho ou começado por ponto. Aceita `<name>` com ou sem `.md`.
- `python3 ${CLAUDE_PLUGIN_ROOT}/skills/memoria/scripts/parada.py .` — hook `Stop`. Se a sessão teve commit ou edição e nenhum fato foi gravado (inbox conta), bloqueia a parada pedindo o `agora-<frente>`. Bloqueia uma vez por sessão: depois disso, deixa parar.
- `python3 ${CLAUDE_PLUGIN_ROOT}/skills/memoria/scripts/parada.py --registrar .` — hook `SessionStart`. Grava o início da sessão que o `Stop` mede, em `sessoes/memoria/<session_id>.json` do diretório de estado. Não reescreve registro existente, nem o do `guarda-sessao.py`.
- `python3 ${CLAUDE_PLUGIN_ROOT}/skills/memoria/scripts/semear.py .` — migra um `HANDOFF.md` escrito à mão. Grava em `.claude/memoria-semente/` um rascunho `agora-<slug>` por bullet do "Agora", com os links recalculados. As decisões dos handoffs antigos não entram. Recusa (sai 1) se `.claude/memory/` ou o rascunho já existem, ou se o `HANDOFF.md` está ausente, sem `## Agora` ou sem bullets. O `--aplicar` também recusa se `.claude/memory/` está no `.gitignore` ou se o `HANDOFF.md` tem alteração não commitada. O humano apaga o que não entra; `semear.py . --aplicar` move o resto para `.claude/memory/`, grava `"autoMemoryEnabled": false` no `.claude/settings.json` (preservando as outras chaves) e roda o `indice`. `semear.py . --so-settings` grava só a chave — é o que a `projeto-init` roda no repo novo.

## Ligar num repo

O plugin liga sozinho, pelo [`hooks/hooks.json`](../../hooks/hooks.json): no `SessionStart` roda o `injetar` e o `parada.py --registrar`, e no `Stop` roda o `parada.py`, todos sobre `$CLAUDE_PROJECT_DIR`. Os três saem 0 em silêncio onde não há `.claude/memory/`: repo sem memória não sente o plugin. Não registre esses hooks no `.claude/settings.json` do repo, senão rodam duas vezes. O repositório do próprio deltaspec é a exceção temporária: mantém os seus até a release com `hooks/` e o `/plugin update`, e a remoção é uma pendência registrada.

- **Repo novo:** a `projeto-init` cria `.claude/memory/`, as projeções e `"autoMemoryEnabled": false` (`semear.py . --so-settings`).
- **Repo com `HANDOFF.md` escrito à mão:** `semear.py .`, o humano revisa `.claude/memoria-semente/`, depois `semear.py . --aplicar`. A skill `handoff` oferece esse caminho.

`"autoMemoryEnabled": false` desliga a memória nativa global do repo; é reversível apagando a chave. Não declare `autoMemoryDirectory`: só aceita caminho absoluto ou `~`.

O `Stop` mede "nesta sessão" a partir do `iniciado` do mesmo `session_id`. Quem grava é o `guarda-sessao.py --registrar`, onde esse hook existe (este repositório), ou o `parada.py --registrar` do plugin.

## Erros comuns

- Narrar o diff ("editei X, rodei Y"): o git já conta; grave o estado e o porquê.
- Copiar spec ou ADR para dentro do fato: referencie por link.
- Deixar o `agora-*` vivo depois que a frente fecha.
- Gravar preferência do usuário direto em `.claude/memory/`: `user` e `feedback` vão para `inbox/` e esperam o `aprovar`.
- Editar `MEMORY.md` ou `HANDOFF.md` à mão: são projeção; rode `memoria.py indice`.
