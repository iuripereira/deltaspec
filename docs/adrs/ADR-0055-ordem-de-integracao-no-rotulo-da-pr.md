# ADR-0055: A ordem de integração vive no rótulo `fila:N` da PR — sem `FILA.md` versionado e sem ordem só no Jira

- **Status:** Accepted
- **Data:** 2026-11-14
- **Supersedes:** —
- **Superseded by:** —

## Context

Um dev solo trabalha em paralelo em vários repositórios consumidores, com branches, worktrees e PRs empilhadas, e nada declara em que ordem integrar. O relatório de fila de integração de 2026-09-04 mediu três ou mais PRs vivas num mesmo repositório, que era o gatilho declarado para abrir delta. O framework já tinha duas das três peças, mas soltas. O `guarda-sessao.py` sabe quem está em qual branch, e o `changelog.d` evita o conflito mais frequente. Faltava uma ordem declarada e um lugar para olhá-la.

A delta-114 entregou o lugar para olhar: a vista `integracao.py` deriva a ordem de git e GitHub, sem escrever estado, e já consome um rótulo `fila:N` como override (R159). A delta-113 fecha a outra metade, que é onde essa ordem declarada mora. Restou decidir o porquê das alternativas que ficaram de fora.

## Decision

**A ordem declarada vive no rótulo `fila:N` da PR, no GitHub.** O `N` é a posição, e `1` é a próxima. É um override opcional da ordem derivada pela vista. Sem rótulo, vale a ordem derivada, e a falta do rótulo nunca é achado. A ordem fica junto do resto da narrativa da PR (ADR-0035), sobrevive ao squash e não cria arquivo versionado.

**Dependência real entre PRs se expressa pela topologia, não pelo rótulo.** Uma PR cuja base não é a base do repositório, empilhada com `gh stack` ou à mão, já entra logo depois da raiz, e o `fila:N` não é reaplicado por cima da pilha.

**O prefixo `fila:` convive com o da projeção de débitos** (`fila:alta`, R52). O dono decidiu isso em 2026-11-14, porque separar o espaço de nomes para `ordem:N` exigiria um MUDA do R159. O parser só reconhece `fila:<inteiro positivo>`, e o selftest do `integracao.py` garante que `fila:alta` não vira posição.

Renúncias, uma linha cada:

- **`FILA.md` versionado em cada repositório:** criaria mais uma fonte de verdade sobre quem faz o quê e conflitaria em todo merge, que é justamente o sintoma que se quer curar.
- **Ordem só no Jira, arrastando cards:** inverteria a direção da verdade (Jira → repo), e o rank ficaria onde quem abre a PR não olha. O Jira pode ser vista projetada do rótulo, nunca a fonte.
- **GitHub Projects com campo "Fila":** é barato, mas como fonte perde pelo mesmo motivo do Jira, porque a ordem sairia da PR. Como vista, fica de plano B se a projeção no Jira se provar pesada.
- **Empilhar tudo com `gh stack`:** forçaria dependência entre trabalhos independentes, e a pilha não suporta auto-merge. A pilha só vale quando a dependência é real, e entra como caso especial na regra acima.
- **Merge queue do GitHub:** em repositório privado, está bloqueada pelo plano da organização (DT-074). Reavaliar se o plano mudar ou se os repositórios ficarem públicos.
- **Orquestrador de implement paralelo (DT-138):** não concorre com a fila. Ele ordena tasks dentro de uma delta (ADR-0014), e a fila ordena PRs entre deltas.

## Consequences

- **Fica mais fácil:** decidir a ordem é um `gh pr edit <n> --add-label fila:N`, sem commit e sem arquivo para conflitar. A vista da delta-114 já honra o rótulo, e quem não declara nada fica com a ordem derivada, que basta no caso comum.
- **Fica mais difícil:** a ordem não é versionada, e o histórico dela fica só no log de eventos da PR. O `--add-label` falha se o rótulo não existir no repositório, e criar o conjunto de rótulos é passo de infraestrutura do consumidor, não do framework.
- **Continua sem solução:** duas PRs verdes que quebram juntas (só uma merge queue pega), ordem entre repositórios diferentes (a fila é por repositório, como a `develop`) e o HEAD trocado por baixo de uma sessão (DT-093, guarda própria).
- **Impacto em outros módulos:** a regra da fila passa a ter um dono canônico único, o módulo `git-workflow` do `canonical-rules.md` da `projeto-init` (R1 da delta-113). O `cycle.md` da `spec-feature` a referencia e não a copia. A projeção de débitos (R52) não muda.
