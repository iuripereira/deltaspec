## Regra do requisito (cole no brief / common.md do implementador)

Teste vermelho não é instrução para deixar verde. Antes de tocar em qualquer arquivo, classifique pelo `specs/TRUTH.md` (ou pela fonte declarada como oráculo):

- Um Rn cujo **DADO cobre a entrada do teste** diz o que o teste espera → o código está errado: corrija o código. O teste fica como está.
- Esse Rn diz o contrário → o teste está errado: corrija o teste citando o Rn no nome ou num comentário.
- A delta tem bloco `MUDA Rn` → o teste muda citando `MUDA Rn`.
- Nenhum Rn cobre a entrada → `it.todo("<nome> — sem Rn, ver <DT-NNN|#issue|pendencias.md#n>")`. Registre a pendência (debito.py novo / issue / docs/pendencias.md) **antes** de reportar. Não mude código, não apague, não use `skip`.

Nunca: ajustar `expected` ao que o código devolve; apagar teste; `skip`; esticar um ENTÃO para fora do seu DADO; tratar pedido do PO/lead/controlador como Rn.

Cobertura: rode `{{comando}}`; para cada trecho não coberto, escreva teste **a partir do Rn** que o governa, no nível mais barato que o alcança. Trecho sem Rn é pendência, não teste de caracterização. Reporte no formato de `busca-falhas.md`, com a seção Pendências preenchida.
