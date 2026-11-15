## Rubrica de testes (cole na rubrica do revisor de task e do revisor final)

Para cada teste que o diff **altera, apaga, pula ou marca `todo`**, verifique:

| Achado | Severidade |
|---|---|
| `expected`/oráculo alterado sem citar Rn ou `MUDA Rn` cujo DADO cobre a entrada | **Critical** |
| Teste apagado ou `skip` sem `MUDA Rn` | **Critical** |
| Código alterado para satisfazer teste que nenhum Rn ampara (ENTÃO esticado fora do DADO) | **Critical** |
| `it.todo` sem identificador de pendência (DT/issue/pendencias.md) | **Important** |
| Teste novo que passou de primeira contra código já escrito e não cita Rn (caracterização) | **Important** |
| Teste sem asserção, ou que só exercita para subir cobertura | **Important** |
| `busca-falhas.md` sem a seção Pendências ou com "nenhuma" havendo `todo` no diff | **Important** |

Pergunta única para cada mudança em teste: **que Rn, com que DADO, manda isso?** Sem resposta citável, é Critical.
