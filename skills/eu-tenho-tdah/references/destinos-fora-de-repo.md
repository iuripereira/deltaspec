# Destinos de captura — mecânica

Rotas de captura quando não há registro `debts/` ou `DEBT.md` alcançável — o gatilho é a ausência do registro, não a ausência de repositório: um repo git sem `debts/` cai aqui. A rota é decidida pela regra, não por pergunta: **local** é o padrão; **obsidian** só quando o Iuri pedir ("salva no obsidian"). Os caminhos de máquina vivem no `CLAUDE.md` do usuário — a skill nomeia as rotas, os caminhos não moram aqui.

| Rota | Destino |
|---|---|
| local (padrão) | append no ledger local declarado no `CLAUDE.md` do usuário |
| obsidian (só a pedido) | append no arquivo de inbox do vault declarado no `CLAUDE.md` do usuário |
| nada alcançável | o mesmo texto como artefato (onde o cliente suportar) ou bloco pronto para colar, dizendo que nada foi gravado |

A captura é sempre a mesma linha, e o arquivo é append-only:

    - [ ] AAAA-MM-DD — <descrição do sintoma> — origem: <repo, pasta ou tarefa>

Se o destino declarado estiver dentro de um repositório git, a captura fecha com `git commit` desse arquivo e **nenhum `push`** — publicar é decisão do Iuri, deixar o repositório sujo não é. Destino fora de git: nada de git roda.

Arquivo inexistente nasce com um título H1; no vault, também com o frontmatter que ele exigir. Nenhum caminho declarado, ou nenhum alcançável → caia no bloco colável e diga que nada foi gravado.

O ledger é **captura, não registro canônico**: pendência que virar trabalho de verdade migra para o `debts/` do repo dono, onde ganha `DT-NNN`, fila e gate.

Confirme em uma linha o que foi gravado e onde — registro, não convite.
