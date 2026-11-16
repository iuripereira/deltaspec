# ADR-0049: A issue fecha no merge da PR na `develop`, e a release carimba a versão

- **Status:** Accepted
- **Data:** 2026-09-22
- **Supersedes:** [ADR-0048](ADR-0048-deltaspec-no-perfil-com-develop.md) (em uma cláusula: "`Closes #N` só fecha a issue quando o commit chega à `main`, na release")
- **Superseded by:** —

## Context

- O GitHub só lê a palavra de fechamento em merge na branch default. Na topologia com `develop` ([ADR-0045](ADR-0045-release-por-skills-do-plugin-e-merge-commit-na-main.md), ADR-0048), a PR de escopo mergeia na `develop` e o `Closes #N` dela é ignorado.
- A rede era a PR de release: o `/deltaspec:criar-release` cola nela os `Closes #N` que o `debito.py vinculo` deriva. O `vinculo` só enxerga DT com `Ticket`, então issue de `fix` e DT projetado sem `Ticket` nunca chegavam à release.
- Medido em 2026-09-21: dois repos consumidores com `develop` tinham 7 issues resolvidas por PR mergeada e ainda abertas — 3 de `fix` com `Closes #N` na PR e 4 de DT já quitado ou descartado.
- O usuário definiu, em 2026-09-22, que "fechada" é "resolvida na `develop`" e que a release é a segunda camada, a que diz em que versão a issue saiu. Reincidência depois disso é falha de processo.

## Decision

- Um molde novo do `projeto-infra`, `fechar-issues-no-merge.yml`, instalado no perfil com `develop`: shell puro com o `gh` do runner, sem framework ([ADR-0001](ADR-0001-gates-rodam-local.md)).
- Leitura ou escrita que falha vira `::warning::`: o job trata o resto e sai vermelho no fim. Estado de DT fora de `quitado`/`descartado` avisa em vez de fechar; arquivo que só nasce em `debts/_archive/` (migração) não conta como quitação.
- **Camada 1, merge na `develop`:** fecha as issues que a PR resolve — palavra de fechamento no corpo e DT que ela moveu para `debts/_archive/`, achado pelo `Ticket` da versão ativa ou pelo título `[DT-NNN]`/`DT-NNN — `. Quitado fecha como concluída; descartado, como não planejada. O comentário cita a PR, que segue como citação técnica da quitação.
- **Camada 2, merge da `release/*` ou `hotfix/*` na `main`:** para cada PR de escopo que a release leva e para ela própria, comenta "lançada na vX.Y.Z" nas issues concluídas e fecha o que a camada 1 deixou aberto.
- Issue fechada nunca é reaberta. Reincidência abre issue nova citando a antiga e a versão; se afeta o cliente, sai por hotfix; se não, vira DT novo na fila. A regra mora no `references/debito.md` da `handoff`.
- O `debito.py vinculo` continua só avisando na PR contra a `develop`, com o texto do aviso atualizado. A seção de tickets da PR de release continua como rede onde o molde não está instalado.

## Alternativas renunciadas

1. **`develop` como branch default.** Faria o `Closes #N` agir na PR de escopo, mas derruba a premissa da ADR-0045 (rulesets, `release-check` e skills nomeiam a `main`) — a mesma renúncia da ADR-0048.
2. **Fechar só na release, com a label `na-develop` até lá.** "Aberta" passaria a significar "não lançada", mas a issue resolvida ficaria aberta até o corte e a camada 1 viraria rótulo; o carimbo com a versão responde "já saiu?" sem isso. Decisão do usuário.
3. **`vinculo` exigir `Closes #N` na PR contra a `develop`.** Obrigaria o script a saber se o molde está instalado no repo, e o workflow lê o corpo de qualquer jeito. Decisão do usuário.
4. **`pull_request_target`.** Daria token de escrita à PR de fork, ao custo de rodar com as permissões da base a partir de evento disparado por terceiro; nenhum consumidor trabalha por fork.
5. **Workflow escrito à mão em cada consumidor.** Infra de repositório sai do `projeto-infra`; a cópia à mão diverge do molde na primeira correção.

## Consequences

- \+ A issue fecha no merge que a resolve, com a PR citada: o `Closes #N` da PR de escopo volta a ter efeito na topologia com `develop`.
- \+ Cada issue diz em que versão saiu, e a reincidência tem um ponto de partida citável.
- − Primeiro molde com `issues: write`, fora do `contents: read` dos demais (delta-066); PR de fork falha sem fechar.
- − A leitura do `Ticket` fica duplicada em shell (ESPELHO da `chave_ticket()` do `debito.py`): mudou uma, muda a outra.
- − Achar o DT pelo título pede uma listagem de até 1000 issues por execução; repo com mais perde as mais antigas.
- − Re-rodar o job na `main` repete o carimbo; release com mais de 250 commits carimba só parte.
- − Só vale onde o `/deltaspec:projeto-infra` rodou depois do release que traz o molde.
