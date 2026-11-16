# ADR-0052: Inbox para fatos user/feedback e hook Stop — emenda a ADR-0050

- **Status:** Accepted
- **Data:** 2026-10-24
- **Amends:** [ADR-0050](ADR-0050-memoria-de-projeto-versionada.md)
- **Supersedes:** —
- **Superseded by:** —

## Context

A [ADR-0050](ADR-0050-memoria-de-projeto-versionada.md) decidiu que "o PR é o inbox" e adiou duas redes de proteção da memória para débitos com gatilho: o inbox explícito de fatos (DT-209), cujo gatilho era o primeiro fato errado que passasse no PR, e o hook `Stop` que cobra o fato (DT-208), cujo gatilho era a primeira sessão que perdeu decisão mesmo com a memória ligada.

Nenhum dos dois gatilhos disparou. O dono do produto decidiu em 2026-10-24 implementar as duas redes **sem que os gatilhos tivessem disparado**: o custo de montar agora é baixo, e esperar o primeiro incidente significa pagar por ele antes de ter a proteção. Esta ADR registra que a antecipação foi decisão, não leitura frouxa do gatilho.

Os dois pontos que a ADR-0050 deixou abertos são de naturezas diferentes. Preferência do usuário (`user`/`feedback`) é o fato que mais custa errar e menos aparece no diff de um PR sobre outro assunto. Já a gravação de qualquer fato depende de alguém lembrar, e é o esquecimento que a ADR-0050 quis matar.

## Decision

- **Fatos `user` e `feedback` esperam em `.claude/memory/inbox/`** até `memoria.py aprovar <name>`, que move o arquivo para `.claude/memory/` e carimba `metadata.aprovado: <data>`. O inbox fica fora de `MEMORY.md` e de `HANDOFF.md`; o `memoria.py check` reprova `user`/`feedback` na raiz sem carimbo e fato de outro tipo no inbox; o `injetar` avisa quantos aguardam; a rota memória da skill `handoff` pergunta o que aprovar. `agora-*`, `project` e `reference` continuam entrando direto: o PR os revisa.
- **O hook `Stop` bloqueia uma vez por sessão** quando houve trabalho (commit ou edição fora de `.claude/memory/` desde o início da sessão) e nenhum fato foi criado, alterado ou apagado, inbox incluso. O bloqueio manda gravar ou atualizar o `agora-<frente>`. O início da sessão vem do registro do `guarda-sessao.py`, e um marcador por `session_id` garante o uma-vez. Qualquer falha de leitura libera (RNF2).

Renúncias, uma linha cada:

- **Marcador no transcript da sessão:** o formato do transcript é interno do harness e muda sem aviso; depender dele quebra em silêncio.
- **Só `git status`, sem início de sessão:** cobraria a sujeira da sessão anterior como se fosse desta.
- **Histórico do git para distinguir fato novo de aprovado:** os dois pousam no mesmo commit, então o histórico não separa um do outro; o carimbo `aprovado` é o sinal explícito.
- **Cobrar a cada parada:** o hook incomodaria em todo turno; uma vez por sessão basta para lembrar sem virar ruído.

## Consequences

- Menos fato perdido no fechamento da sessão, e preferência do usuário só entra no índice depois que ele aprova.
- Atrito para o usuário: cada `user`/`feedback` exige uma aprovação explícita, e um fato esquecido no inbox não chega ao contexto das sessões seguintes.
- O hook depende do `guarda-sessao.py`, que grava o início da sessão; num repo consumidor sem ele o `Stop` é um no-op silencioso, e a ligação ali é da delta-134.
- Um `pull` ou `rebase` durante a sessão traz commits com data posterior ao início e conta como trabalho: o custo é um bloqueio a mais, cortado pelo marcador.
- Um `compact`, `clear` ou `resume` regrava o início da sessão e faz o hook errar para o lado de não cobrar.
- Quita o DT-208 e o DT-209 (delta-137).
