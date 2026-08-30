# Modos `auditar` e `padronizar` — regra canônica

Dona única dos dois modos da skill `modelo-dados` (delta-075). `SKILL.md` linka este arquivo e não reproduz o contrato abaixo.

## `auditar` — repo atual

1. **Rode `check`.** Os achados M4 (órfão/duplicado/tipo), M5 (célula decorativa) e M6 (tautologia, BAIXO) viram a pauta — cada um é uma pergunta, não uma reescrita silenciosa.
2. **Entrevista.** Motor: `mattpocock-skills:grilling`, com `mattpocock-skills:domain-modeling` unido pelo gatilho já vigente "modelo de dados persistente" (`adapters.md`) — sem motor de terceiro novo (não é `max:grill-with-docs`; esse virou stub de `grilling` na recontratação da [ADR-0026](../../../docs/adrs/ADR-0026-recontratacao-hibrida-clarify-no-oficial.md)). Enquadramento: *"o dicionário é o glossário do projeto; atualize inline conforme as decisões"*. Sem `mattpocock-skills` instalado → fallback nativo, roteiro pergunta a pergunta pelos mesmos achados, com o aviso *"auditoria de dicionário degradada: mattpocock-skills/grilling não instalado"* (escada [ADR-0004](../../../docs/adrs/ADR-0004-degradacao-graciosa-adapters.md)).
3. **Pergunta sem resposta na sessão** → a célula fica `[lacuna]` explícita (vocabulário da `descoberta`, R25/R26) e a sessão **encerra assim mesmo** — é melhoria incremental, não gate; o próximo `check` reapresenta a mesma lacuna como pauta.
4. **Reescrita.** Só as células que a entrevista respondeu — texto correto já existente nunca é tocado. Fim de fase = commit do `DATA_DICTIONARY.md`.

## `padronizar` — cross-repo

1. **Detecte o escopo** com `repos_com_dicionario(base)` (`check_data_model.py`) — reaproveita `find_repo_roots`/`detect_mode` do `audit-workspace` (que não é estendido, é read-only por contrato): workspace → todo repo-membro com `DATA_DICTIONARY.md`; repo único → ele mesmo, se tiver o arquivo.
2. **Por repo devolvido**: rode `check` → conduza o modo `auditar` (acima) sobre as lacunas → proponha a reescrita.
3. **1 branch e 1 PR por repo, com confirmação explícita do usuário antes de cada PR.** Nunca em lote — cada repo é uma decisão própria, mesmo que a lacuna se repita entre eles.
4. **PR grande na própria delta que introduz `padronizar`** (C7 do `check_cycle.py` acusando): o modo se desmembra como delta seguinte, sem retrabalho — é isolado do resto da skill, não bloqueia `auditar` nem o gate M1–M6.

## Erros comuns

| Erro | Correto |
|---|---|
| Reescrever o dicionário inteiro no modo `auditar` | Só as células que M4–M6 acusaram; o resto já está correto |
| Aplicar a mesma resposta em todos os repos do `padronizar` sem confirmar cada um | Confirmação por repo, mesmo que a lacuna se repita |
| `padronizar` em lote, 1 PR para todos os repos | 1 branch/PR por repo |
| Travar a sessão de `auditar` até zerar toda lacuna | Fecha com `[lacuna]` residual — é honesto, não é defeito |
| Invocar `max:grill-with-docs` como motor | O motor vigente é `mattpocock-skills:grilling` + `domain-modeling` (ADR-0026) |
