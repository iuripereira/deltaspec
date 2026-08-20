# Dicionário de dados

> Dono canônico do shape dos dados/contratos. Ao mudar uma regra de negócio, atualize este arquivo **e** o serviço correspondente na mesma mudança (regra de propagação).

## Entidades

### {{Entidade}}
| Campo | Tipo | Regras / invariantes | RN |
|---|---|---|---|
| {{campo}} | {{tipo}} | {{ex.: `amount` sempre positivo; nunca comparar float com `==`, usar tolerância < 0.01}} | {{RN-NNN}} |

## Contratos entre módulos
- {{ex.: `posts.json` — shape produzido por `build.js`, consumido por `blog.js`/`search.js`. Mudou o shape? ajuste os consumidores no mesmo PR.}}
