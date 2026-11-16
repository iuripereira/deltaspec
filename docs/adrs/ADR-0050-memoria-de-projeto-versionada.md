# ADR-0050: Memória de projeto versionada — fatos em `.claude/memory/`, `HANDOFF.md` vira projeção

- **Status:** Accepted
- **Data:** 2026-10-19
- **Supersedes:** [ADR-0025](ADR-0025-handoff-por-sessao.md)
- **Superseded by:** —

## Context

A [ADR-0025](ADR-0025-handoff-por-sessao.md) separou "onde estamos" (índice fino) de "como cada sessão chegou lá" (um arquivo por sessão). O formato acertou, o gatilho não: tudo depende de alguém lembrar de rodar o handoff no fim da sessão, e é o que morre — esquecimento de rodar mais a tendência de narrar o diff em vez de registrar o estado (entrevista de 2026-10-19, registrada em `specs/_archive/132-memoria-de-projeto/plan.md`). O custo aparece na sessão seguinte, que redescobre o que a anterior já sabia.

A evidência pesa para um híbrido, não para uma troca de registro: memória automática sem revisão é rejeitada em cerca de 80% dos casos e é superfície de poisoning (agentes que escrevem e leem memória de forma mais agressiva são mais exploráveis). Por isso o registro continua versionado, lido por mim, por agentes e por pessoas via `git pull`, e passa por diff de PR.

A [ADR-0008](ADR-0008-skill-handoff-propria.md) previu reabrir a decisão "se o contrato convergir para registros versionados" — é o caso. O spike de 2026-10-19 (Task 1 da delta-132) testou o mecanismo nativo, `autoMemoryDirectory` apontado ao repo, e **reprovou**: a chave só aceita caminho absoluto ou `~`, não honra caminho relativo nem `$CLAUDE_PROJECT_DIR` em settings de projeto, então não serve para memória versionada.

## Decision

O registro versionado continua canônico. Muda o gatilho (contínuo: o fato é gravado quando nasce, não no fim da sessão) e o formato (fato, não narrativa).

- **Fatos em `.claude/memory/<name>.md`**, um por arquivo, frontmatter como o do harness (`name`, `description`, `metadata.type` ∈ `user|feedback|project|reference`). Um fato `agora-<frente>` por frente aberta, atualizado no lugar e apagado quando a frente fecha.
- **Mecanismo:** o hook `SessionStart` (`startup|resume|clear|compact`) roda `memoria.py injetar` e põe o índice no contexto; `"autoMemoryEnabled": false` no `.claude/settings.json` desliga a memória nativa global deste repo. **A gravação é por instrução no `CLAUDE.md`** (Write em `.claude/memory/<name>.md` no momento em que o fato nasce), não automação do harness.
- **`MEMORY.md` e `HANDOFF.md` são projeções geradas** por `memoria.py indice` (precedente: ADR-0031 e ADR-0042) — idempotentes, o que mata o conflito de merge. `.claude/handoffs/` congela como histórico, nunca podado.
- **O PR é o inbox:** fato errado aparece no diff. O gate `memoria.py check` (frontmatter, teto do índice, segredo) roda no CI.
- **Fronteira:** decisão com renúncia → ADR; débito → `debito.py novo`; lição → `licao.py nova`; requisito → delta. A memória guarda o resto: estado da frente, caminho descartado com evidência, preferência do usuário, ponteiro externo.

Renúncias, uma linha cada:

- **Vetor/cloud (Mem0, Letta Cloud, claude-mem, Graphiti, Supermemory):** dependência externa, vazamento para serviço, superfície de poisoning maior; claude-mem ainda exige LLM para comprimir e não versiona.
- **ai-memory do Akita (Rust, MIT):** data dir global por máquina, então a memória não chega via `git pull`; binário, daemon HTTP, 9 hooks (um em toda tool call) e MCP; captura toda saída de tool fora do `guarda-confidencialidade`, com sanitização best-effort e sem criptografia (risco de confidencialidade contratual com cliente-A (NDA)); nada passa por diff de PR. Resolve só o "esqueço de rodar", que a captura contínua já resolve. Decisão do dono do produto em 2026-10-19.
- **`autoMemoryDirectory` apontado ao repo:** reprovado no spike (só absoluto/`~`).
- **Memória local nativa como fonte:** some no `/plugin update`, não chega a outro clone e fica fora do guarda; a doc a chama de machine-local.
- **`@modelcontextprotocol/server-memory`:** adiado — sem caso de uso que `grep` em `.claude/memory/` e `debts/` não cubra; reabrível.
- **Inbox explícito de fatos** (`.claude/memory/inbox/` + `memoria.py aprovar`): o PR já revisa; vira DT com gatilho no primeiro fato errado que passar.
- **`Stop` hook de cobrança:** vira DT; só entra se uma sessão perder decisão mesmo com a memória ligada.
- **Memória de subagente (`memory: project`):** não agora; vira DT.
- **Converter os 87 handoffs em fatos:** inventa decisões retroativas — mesma renúncia da ADR-0025.

## Consequences

- Ganha captura contínua e um índice barato de carregar (teto de 200 linhas, vigiado pelo gate).
- Custa manter e apagar um fato `agora-*` por frente aberta; fato esquecido vivo é ruído.
- `autoMemoryEnabled: false` faz este repo perder a memória pessoal nativa; reversível apagando a chave.
- A gravação depende de o modelo seguir o `CLAUDE.md`; daí o gate no CI e a revisão em PR como rede de proteção.
- `type: user` e `feedback` entram no repo privado e nunca no derivado público (fora do allowlist de publicação).
- O C16 continua valendo sobre a projeção `HANDOFF.md`; a skill `handoff` e a `projeto-init` só se ajustam na delta-133.
