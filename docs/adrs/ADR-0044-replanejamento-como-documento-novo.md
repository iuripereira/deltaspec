# ADR-0044: Replanejamento é documento novo com fatos rastreados, não edição do plano vigente

- **Status:** Accepted
- **Data:** 2026-09-05
- **Supersedes:** —
- **Superseded by:** —

## Context

Um plano em execução — arquivo datado em `.claude/plans/`, plano salvo pelo agente fora do repo, prompt ou anotações, `plan.md`/`tasks.md` de uma delta — envelhece à medida que o repo aprende: dossiês de rodada de insumos, perguntas respondidas no registro vivo, saída de grilling, handoffs, débitos abertos ou quitados, lições, deltas novas ou arquivadas, correções pontuais do usuário. Replanejar era prompt digitado a cada sessão, sem método. Num repo consumidor, o baseline observado sem skill mostrou os cinco modos de falha: o agente varre o repositório inteiro quando os alvos são conhecidos; toma o handoff como verdade (o handoff dizia "fase não iniciada" enquanto três PRs daquela fase já estavam mergeadas); reescreve o plano no lugar e perde a trajetória; reabre decisões marcadas "não reabrir"; e escreve tarefas sem escopo nem verificação.

Nenhuma skill do ciclo cobre "plano vigente × fatos novos": a `rodada-insumos` concilia insumo em requisitos e PRD; a `writing-plans` do superpowers escreve plano do zero; a `handoff` registra o estado da sessão.

## Decision

Criamos a skill **`replan-doc`** (delta-109). Ela ancora o plano vigente (materializado antes como arquivo datado no repo quando vem de fora; a data no nome é o pivô), coleta **só pelo mapa de alvos** do template — um único `git log --since=<pivô>` separado em *fonte de fato* (abre) e *evidência* (caminho + PR) —, tabula fatos novos com fonte rastreável e efeito sobre o plano, abre o gate de decisões **só quando um fato bloqueia** (formato e motor da fase 4 da `rodada-insumos`, com o fallback da ADR-0004), escreve o replan como **arquivo novo datado** em `.claude/plans/` com IDs de tarefa estáveis e cada tarefa aberta com `arquivos:`, `verificação:` e `fonte:`, deixa no plano anterior uma única linha de banner, e para no PR aberto. **Git vence handoff nos dois sentidos**: `[x]` só com verificação passando ou commit/PR; "não iniciado" com commit vira `evidência parcial`. Plano de delta como entrada gera tarefas para a `spec-feature`; a skill não edita `specs/NNN-*/`.

Renúncias registradas:

- **Editar o plano no lugar** — rejeitado: perde a trajetória (o que mudou, por quê, com que fonte) e contraria a regra da casa de append sobre reescrita; o registro é a cadeia de planos datados ligados por `Substitui:`.
- **Ampliar a `rodada-insumos` ou reusar a `writing-plans`** — rejeitado: objetos diferentes (insumo → PRD; plano do zero). O replanejamento tem pivô de data e fato novo como unidade, e nenhuma das duas tem esse eixo.
- **Script de coleta** — rejeitado por ora: um `git log --since` e o inventário fixo do template bastam; script só quando três repos consumidores pedirem o mesmo filtro.
- **Fonte fora do git como fato** — rejeitado: fato exige fonte rastreável no repositório; reunião não minerada vira tarefa `rodada-insumos`, senão a skill vira uma segunda descoberta.
- **Handoff como evidência de conclusão** — rejeitado: handoff é relato e intenção; evidência é verificação passando ou commit/PR, e a regra vale nos dois sentidos.
- **Gate de decisões em toda execução** — rejeitado pelo usuário na aprovação do plano (2026-09-05): travaria sessões autônomas; o gate abre só quando um fato contradiz decisão congelada, fontes conflitam ou tarefa nova não tem dono. Decisão congelada sem fato contrário é herdada por ID + link, nunca copiada.

## Consequences

- O ciclo ganha um regime de replanejamento nomeado, com custo de leitura previsível: o agente abre o que o mapa aponta, não o repositório.
- A trajetória de um plano fica auditável por arquivos datados encadeados; a `handoff` continua sendo quem aponta o `HANDOFF.md` para o plano novo.
- Custo aceito: um arquivo a mais por replanejamento; repo consumidor que não versiona `.claude/plans/` fica com arquivo local e aviso, sem PR.
- Custo aceito: delta como entrada produz tarefas em vez de edição direta — um passo a mais, em troca de fronteira limpa com a `spec-feature`.
