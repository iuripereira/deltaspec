# ADR-0051: Confirmação e busca de falha são artefatos de teste separados

- **Status:** Accepted
- **Data:** 2026-10-24
- **Supersedes:** —
- **Superseded by:** —

## Context

O `test-plan.md` (R38, delta-015) deriva seus casos dos cenários DADO/QUANDO/ENTÃO da spec e proíbe inventar cenário novo. É teste de confirmação, caixa-preta, escrito antes ou junto do código: prova que o requisito foi atendido, e o gate C8 cobra um caso por Rn/RNFn.

A pesquisa de referência (Pereira, 2019 — `skills/busca-falhas/references/referencial-teorico.md`) mediu, numa suíte de sistema de 2.812 casos derivados da especificação, 27% dos arquivos com cobertura zero. Reconfigurar 19% da suíte para seguir a especificação à risca rendeu 0,9% de cobertura e nenhuma falha. **Um** caso novo, escrito para alcançar código que o mapa de cobertura mostrava nunca exercitado, rendeu 0,4% e expôs a única falha grave encontrada (segmentation fault num destrutor). A falha estava adormecida porque a suíte derivada da spec, por construção, não chegava lá.

Medição própria, em 24/10/2026, com subagentes sob pressão ("deixa o CI verde", gate de cobertura em 15 minutos, ordem do PO para ajustar o valor esperado), sem orientação: um esticou o ENTÃO de um requisito para fora do seu DADO e mudou o código para satisfazer um teste sem oráculo; outro subiu a cobertura com testes "de comportamento observado"; os três deixaram dúvidas reais sem registro ("registraria para o lead"). Com a skill `busca-falhas` carregada, os cinco cenários cumpriram a regra.

Há um ponto de tensão real: quem escreve teste depois do código tende a congelar o comportamento atual (caracterização) e a tratar o teste existente como negociável quando a entrega aperta. O framework precisa dizer onde a busca de falha mora e o que pode mudar quando um teste fica vermelho.

## Decision

1. **Dois artefatos, dois momentos, um oráculo.** O `test-plan.md` permanece como está: confirmação, antes do código, derivada da spec. A busca de falha é artefato próprio, `busca-falhas.md`, produzido pela skill `busca-falhas` depois do implement e dirigido pelo mapa de cobertura. O oráculo dos dois é o mesmo: o Rn/RNFn do TRUTH.
2. **Regra do requisito.** Teste vermelho só muda citando o Rn cujo DADO cobre a entrada do teste, ou o `MUDA Rn` da delta. Sem Rn, o teste vira `todo` com pendência registrada por identificador. Nunca se ajusta oráculo ou valor esperado ao que o código devolve; ordem, prazo e opinião de produto não são predicados — viram `MUDA Rn` antes.
3. **Cobertura é entrada, não meta.** O percentual entra no artefato só como registro; o que a skill lê é a lista do não exercitado. Teste que passa de primeira contra código pronto e não cita Rn é caracterização e não conta.
4. **Sem gate novo até o precedente.** Um `C19` nasce quando três deltas tiverem produzido o artefato; até lá, a rubrica do revisor é a trava.
5. **Fora do ciclo, oráculo degradado declarado.** Sem `TRUTH.md`, a fonte cai para PRD/README/docstring citados, e o artefato diz isso no cabeçalho.

Renúncias:

- **Ampliar o `test-plan.md` para aceitar cenário novo** — misturaria confirmação (antes do código) e busca (que só existe depois) no mesmo gate C8, e o "não inventa cenário" é o que mantém a rastreabilidade Rn → CT.
- **Agente `testador` com a disciplina embutida** — um assento a mais por task no subagent-driven-development, e a disciplina não alcançaria quem escreve teste inline nem o revisor. Pode nascer depois, carregando a skill.
- **Hook de pre-commit que reprove `*.test.*` alterado sem Rn na mensagem** — falso positivo em todo refactor de teste; exige script, selftest e CI. Fica como débito se a rubrica não bastar.

## Consequences

- Toda delta de perfil completo em repo consumidor passa a ter um `busca-falhas.md`, arquivado junto com a delta.
- O brief do implementador e a rubrica do revisor do SDD carregam os blocos da skill (`references/brief-implementador.md`, `references/rubrica-revisor.md`); teste alterado sem Rn citado é Critical.
- Mais `it.todo` visíveis nas suítes, cada um com DT ou issue: é o mapa do que a spec cala, não ruído.
- Repo que mede cobertura declara a dependência de medição (ex.: `@vitest/coverage-v8`).
- O gate C19 é dívida assumida com gatilho explícito (três artefatos arquivados).
