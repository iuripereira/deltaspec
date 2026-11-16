# Destinos de captura — mecânica

Rotas de captura quando o **repositório de origem do artefato** não tem registro `debts/`/`DEBT.md` alcançável **e** não declara `deltaspec.registro: proprio` — declarado, o `debito.py novo` cria o registro lá e a captura não sai do lugar. Se o repo do artefato **tem** registro, nada aqui se aplica: a pendência vai direto para ele (SKILL.md, "Destino das pendências"), mesmo vinda de uma sessão em outro diretório. A rota é decidida pela regra, não por pergunta: **local** é o padrão; **obsidian** só quando pedirem ("salva no obsidian"). Os caminhos de máquina vivem no `CLAUDE.md` do usuário — a skill nomeia as rotas, os caminhos não moram aqui.

| Rota | Destino |
|---|---|
| local (padrão) | `debito.py novo <raiz do registro de captura>` — a raiz declarada no `CLAUDE.md` do usuário. Ela pode ser um `debts/` dentro de uma **subpasta** de repositório git (um vault, por exemplo), e a mecânica não muda: `git -C <subpasta>` resolve `check-ignore`, `ls-tree` e `mv` relativos a ela. A pendência nasce `DT-NNN`, com fila e envelhecimento; `Origem` guarda o diretório da sessão e `Local` o caminho do artefato como texto puro. Várias de uma vez → `--lote`. Um ledger de linhas anterior, se houver, fica **congelado**: não recebe linha nova |
| obsidian (só a pedido) | append no arquivo de inbox do vault declarado no `CLAUDE.md` do usuário, como a linha `- [ ] AAAA-MM-DD — <descrição do sintoma> — origem: <repo, pasta ou tarefa>` |
| nada declarado, ou nada alcançável | entregue o mesmo texto como artefato (onde o cliente suportar) ou bloco pronto para colar, **e diga que nada foi gravado** |

As duas rotas têm formas diferentes de propósito: a local carrega dívida técnica, que ganha fila e envelhece até cobrar decisão; a obsidian carrega o que não é dívida técnica e não deve ganhar nenhuma das duas.

Na captura, o `Local` vai **como texto puro** — `outro-repo/src/foo.py:42`, sem link: o `validar` exige o campo e só confere alvo de link, e um link resolveria contra a raiz do registro de captura e reprovaria.

No vault, arquivo inexistente nasce com um título H1, e com o frontmatter que ele exigir.

Se o destino declarado estiver dentro de um repositório git, a captura fecha com `git commit` desse arquivo e **nenhum `push`** — publicar é decisão de quem opera, deixar o repositório sujo não é. Destino fora de git: nada de git roda.

O registro de captura é **primeira parada só do que não tem repo com registro, nunca destino final**: pendência que virar trabalho de um repositório com registro próprio migra para o `debts/` dele, ganha `DT-NNN` novo lá, e o item de origem é quitado apontando o destino. Captura que caiu aqui quando o repo de origem já tinha registro é caso de retroalimentação (SKILL.md, "Destino das pendências").

Confirme em uma linha o que foi gravado e onde — registro, não convite.
