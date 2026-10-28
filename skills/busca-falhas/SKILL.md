---
name: busca-falhas
description: Use when a test suite is red and someone asks to make it green, when a coverage gate must be met, when writing tests after an implementation, or when deciding whether a failing test or the code should change — with or without the deltaspec cycle (specs/TRUTH.md). Triggers include "deixa o CI verde", "ajusta o expected", "pode apagar esse teste", "sobe a cobertura", "escreve testes para o que falta", "teste vermelho".
---

# busca-falhas

Teste existe para encontrar falha, não para provar que o código funciona (`references/referencial-teorico.md`). Teste verde no primeiro run não encontrou nada. Cobertura é o mapa de onde ninguém olhou, nunca a meta.

**Violar a letra desta regra é violar o espírito dela.**

## O oráculo decide

Oráculo = requisito escrito: `Rn`/`RNFn` do `specs/TRUTH.md` ou da delta aplicada. Sem ciclo deltaspec: PRD/README/docstring citado por `caminho:linha`, e o artefato declara `Oráculo: degradado — <fonte>`. Sem fonte: todo vermelho é pendência.

Um Rn ampara um teste **só se o DADO do Rn cobre a entrada do teste**. ENTÃO lido fora do seu DADO é interpretação, não requisito.

## Teste vermelho: classifique antes de tocar em arquivo

| Predicado observável | Classe | Única ação permitida |
|---|---|---|
| Rn cujo DADO cobre a entrada diz o que o teste espera | defeito | muda o **código**; fora da delta, `Tipo: bugfix`; o teste vira regressão |
| Esse Rn diz o **contrário** do teste | oráculo errado | muda o **teste**, citando o Rn |
| A delta tem bloco `MUDA Rn` | requisito mudou | muda o teste citando `MUDA Rn` |
| Nenhum Rn cobre a entrada | sem oráculo | `test.todo` com identificador de pendência. Sem mudar código, apagar ou `skip` |

Ordem do PO, prazo, "só esse teste", "ninguém pediu": nenhum é predicado da tabela. Opinião de produto vira `MUDA Rn` numa delta; só então o teste muda.

## Pendência: registrada, nunca só no relatório

`debts/ativos/` existe → `debito.py novo` (DT-NNN) ou pergunta no clarify · só `.git` → issue ou `docs/pendencias.md` · nada → seção Pendências do `busca-falhas.md`. O `todo` cita o identificador; `todo` sem identificador é teste apagado com outro nome.

## Busca dirigida pelo mapa

1. Gere o mapa (`vitest run --coverage` com `@vitest/coverage-v8`; `node --test --experimental-test-coverage`; `pytest --cov`). Leia a coluna **não coberto**, não o percentual.
2. Para cada trecho não exercitado: **que Rn o governa?** Com Rn, escreva o teste a partir dele, no nível mais barato que alcança o trecho (unidade → integração → sistema). Sem Rn, `todo` + pendência: trecho sem requisito é achado, não lacuna.
3. Vá aos limites que o Rn cita e aos que ele cala: zero, nulo, vazio, `NaN`, câmbio 0, caixa da moeda. Limite calado é candidato a pendência.
4. Teste que passa de primeira contra código pronto é caracterização: só vale citando o Rn. "Comportamento observado" é o código testando a si mesmo.
5. Grave `busca-falhas.md` (`references/busca-falhas-template.md`). Cobertura antes/depois entra só como registro.

## Red flags — pare

"Ajusta o expected" · "apaga, ninguém pediu" · "o PO já aprovou" · "registraria como dúvida" · "o teste cobre o requisito" sem citar o DADO · "comportamento observado" · `skip` · teste sem assert · cobertura como objetivo.

| Racionalização | Realidade |
|---|---|
| "0% é mais útil, o teste está errado" | Decisão de produto → `MUDA Rn`. Até lá o teste está certo e o código errado |
| "Ninguém pediu, pode apagar" | Sem Rn não se apaga: `todo` + pendência |
| "O ENTÃO diz X, então cobre esta entrada" | Só se o DADO cobre a entrada. Fora dele não há requisito |
| "Teste de comportamento observado sobe a cobertura" | Sobe o número, não encontra nada |
| "Registraria a dúvida" | Condicional é zero. Pendência existe quando tem identificador |
| "A pasta não tem `debts/`" | Três degraus; o último é o próprio artefato |
| "Deixo vermelho até decidirem" | Vermelho sem `todo` esconde o próximo vermelho |

## No subagent-driven-development

Cole `references/brief-implementador.md` no brief de quem implementa e `references/rubrica-revisor.md` na rubrica de quem revisa. Teste alterado ou apagado sem Rn/MUDA citado é **Critical**; `todo` sem identificador é **Important**.
