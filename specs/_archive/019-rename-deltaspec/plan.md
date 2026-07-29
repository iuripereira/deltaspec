<!-- resumo deltaspec · ≤15 linhas · única parte do plano lida pelo analyze e pelo humano -->
**Objetivo:** renomear o framework `sdd-iuri` → `deltaspec` nos pontos funcionais e vivos, preservando o registro histórico. **Cobre:** R1, R2, R3, R4, R5, RNF1 (da delta-019) **Decisões duráveis → ADRs:** [ADR-0016](../../docs/adrs/ADR-0016-rename-deltaspec.md) **Riscos assumidos:** consumidor instalado perde `/sdd-iuri:*` até reinstalar (custo aceito do breaking change, mitigado pelo guia de migração e pelo corte da v1.0.0); URLs antigas dependem do redirect do GitHub durante a transição.

## Abordagem

Rename em três camadas, da que quebra para a que só informa:

1. **Funcional** — `plugin.json:name` (define o namespace), `marketplace.json` (`name` raiz + `plugins[0].name`, compõem `deltaspec@deltaspec`), URLs de repositório/homepage, comandos de instalação do README, e a chave `git config deltaspec.validator` no template `pre-commit` da `guarding-doc-integrity`.
2. **Gatilho de auto-invocação** — o `description:` do frontmatter das `SKILL.md` cita `/sdd-iuri:<skill>` como trigger; description desatualizada = skill que não dispara sozinha. Tratada como funcional, não como texto.
3. **Vivo, não funcional** — namespace citado em README, `TRUTH.md`, `CLAUDE.md`, references das skills (com atenção a `projeto-init/references/`, cujo texto é **copiado para o `CLAUDE.md` de repos de terceiros**), títulos, comentários de script e docstrings.

**Fora do rename por design:** `specs/_archive/**`, ADRs `Accepted` (0001–0015) e seções lançadas do `CHANGELOG.md` — registro congelado (R6). `${CLAUDE_PLUGIN_ROOT}` não codifica o nome em nenhum dos usos: resolve sozinho, zero mudança.

**Sem camada de compatibilidade.** O hook `pre-commit` já instalado num projeto é uma cópia com a chave antiga embutida — mudar o template não o toca, então um fallback `sdd-iuri.validator` no template novo só serviria a um caso que a migração já cobre (reconfigurar a chave). Complexidade especulativa: fica de fora.

## Ordem

Repo renomeado no GitHub e `git remote set-url` **antes** do conteúdo (feito): o redirect mantém remote e marketplace vivos durante a transição. Depois camada 1 → 2 → 3 → CHANGELOG + guia de migração. Archive e tag `v1.0.0` em PR próprio (regra do repo: a tag corta no merge que conclui a delta).

## Testes

TDD dispensado: não há lógica nova — o diff é substituição de identificador em manifesto e prosa. A verificação é mecânica e vive nas tasks: `--selftest` dos dois gates (garante que nenhuma docstring/fixture tocada quebrou o script), `check_cycle.py` na delta, grep de resíduo excluindo `_archive/`, e reinstalação real do plugin com invocação de `/deltaspec:*`.
