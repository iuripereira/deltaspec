# ADR-0053: Memória de projeto ligada pelo hook do plugin — emenda a ADR-0050 e a ADR-0052

- **Status:** Accepted
- **Data:** 2026-10-27
- **Amends:** [ADR-0050](ADR-0050-memoria-de-projeto-versionada.md), [ADR-0052](ADR-0052-inbox-para-fatos-user-feedback-e-hook-stop.md)
- **Supersedes:** —
- **Superseded by:** —

## Context

A [ADR-0050](ADR-0050-memoria-de-projeto-versionada.md) ligou a injeção do índice no `.claude/settings.json` deste repositório, e a [ADR-0052](ADR-0052-inbox-para-fatos-user-feedback-e-hook-stop.md) fez o mesmo com o hook `Stop`, que mede "nesta sessão" pelo registro do `guarda-sessao.py`. Num repo consumidor, nada disso existe: o `settings.json` não tem os hooks, e o `guarda-sessao.py` é hook deste repositório, não do plugin. O consumidor com `HANDOFF.md` à mão também não tinha como migrar, a não ser refazendo à mão o seed da delta-132, que deixou 26 links mortos.

## Decision

- **Os hooks da memória vêm do plugin**, em `hooks/hooks.json`: `SessionStart` (`startup|resume|clear|compact`) roda `memoria.py injetar` e `parada.py --registrar`; `Stop` roda `parada.py`. Os comandos apontam o script por `${CLAUDE_PLUGIN_ROOT}` e passam `$CLAUDE_PROJECT_DIR` como raiz. A guarda é a pasta `.claude/memory/`: sem ela, os três saem 0 em silêncio, e o repo sem memória não sente o plugin.
- **Este repositório mantém os seus hooks locais até a release com `hooks/`.** O harness carrega o plugin do cache instalado, nunca do worktree, e o instalado ainda não traz `hooks/`. A remoção é a pendência DT-217, com gatilho na release e no `/plugin update` deste checkout.
- **O início da sessão nos consumidores** é gravado pelo `parada.py --registrar` em `sessoes/memoria/<session_id>.json` do diretório de estado. O registro tem só `session_id` e `iniciado`, no formato do `guarda-sessao.py`, e nunca reescreve um registro existente.
- **`semear.py` migra o "Agora"** de um `HANDOFF.md` à mão: um rascunho `agora-*` por bullet, em `.claude/memoria-semente/`, com os links recalculados. O humano aprova apagando o que não entra, e o `--aplicar` move os rascunhos, grava `autoMemoryEnabled: false` e regenera as projeções. As decisões dos handoffs antigos ficam no histórico. A mesma edição do `settings.json` serve o scaffold da `projeto-init` (`--so-settings`).

Renúncias, uma linha cada:

- **Snippet de hook no `settings.json` de cada consumidor:** o caminho do cache muda a cada versão, e `${CLAUDE_PLUGIN_ROOT}` só existe em hook de plugin; cada repo teria de editar e manter o próprio arquivo.
- **Tirar já os hooks locais deste repositório:** deixaria o repo sem injeção nem `Stop` até o update, porque o plugin instalado ainda não tem `hooks/`.
- **Raiz pelo `cwd` do payload:** acompanha o diretório corrente da sessão, que pode ser subpasta; `$CLAUDE_PROJECT_DIR` é a raiz onde a sessão abriu.
- **Levar o `guarda-sessao.py` inteiro para o plugin:** traria a pergunta de colisão de branch a todo consumidor, o que ninguém pediu.
- **Registro do início no `memoria.py`:** quem lê o registro é o `parada.py`; gravar no mesmo módulo evita uma terceira cópia do formato.
- **Seed dentro do `memoria.py`:** o levaria a ~760 linhas; script irmão, como o `parada.py`.
- **Rascunho em `.claude/memory/` ou em `$TMPDIR`:** a pasta da memória existir já liga a rota memória, o `injetar` e o `Stop` antes da aprovação; o `$TMPDIR` do sandbox muda entre comandos e some no reboot, e o humano não o vê no editor.
- **Seed também das decisões dos handoffs antigos:** decisão do dono do produto, elas ficam no histórico congelado.

## Consequences

- Um consumidor ganha a memória ao atualizar o plugin e aceitar a migração. Nenhum muda sem aceitar.
- Entre o `/plugin update` e a quitação do DT-217, este repositório roda `injetar` e `Stop` em dobro.
- O plugin não tem `SessionEnd`: os registros `sessoes/memoria/*.json` acumulam, como os marcadores do `Stop`.
- Em `resume` e `compact`, o registro do plugin não é regravado (`clear` abre sessão nova, com `session_id` e registro próprios). Uma sessão retomada mede desde a abertura original e pode cobrar uma vez a mais, e o marcador corta a repetição.
