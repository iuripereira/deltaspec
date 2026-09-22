---
name: inicio-de-sessao
description: Use when opening the day or resuming work on a configured project and asking what to do next, where things stopped, or what the current state is — the panel derives every delta's state from git (never from a status field), lists worktrees and branches that hold unsaved or stalled work, and names ONE next step. Takes the project name and an optional focus ("which side to look at first"), inherited from the previous session. Triggers include "/deltaspec:inicio-de-sessao", "bom dia", "o que eu faço hoje", "onde eu parei", "estado do projeto", "início de sessão", "abrir a sessão".
---

# inicio-de-sessao

## Visão geral

Painel de abertura de sessão de um projeto: o estado real de cada delta, derivado do git a cada execução. A fila do projeto declara **intenção e dependência**, nunca status — quando as duas versões divergem, o git ganha e a divergência vai para o topo.

**O painel vem só do script.** Ler handoff, branches e PRs à mão custou, na medição que originou esta skill, 10 a 17 comandos por agente e seis respostas diferentes para a mesma manhã.

**O foco dirige o olhar, não o estado.** O argumento de foco escolhe o lado que ganha o desempate do próximo passo e o detalhe da bancada; ele nunca muda estado, nunca esconde item e nunca silencia divergência. Foco sem item pendente é alerta do script, não silêncio.

## Passos (nesta ordem, sem pular)

1. **Descubra o projeto.** O primeiro argumento é o nome da config (`~/.claude/sessoes/<projeto>.toml`). Veio só "bom dia", sem projeto? **Pergunte qual** — `sessao.py` lista os configurados e recusa adivinhar pelo diretório corrente, e você também não adivinha.
2. Rode `python3 ${CLAUDE_PLUGIN_ROOT}/skills/inicio-de-sessao/scripts/sessao.py <projeto> [foco] --gravar`. O foco é texto livre ("continua no estoque"); omitido, o script herda o da última sessão daquele projeto, e a palavra `sem` limpa. O `--gravar` escreve a nota do dia no vault da config e fecha a saída com `> nota: <caminho>` — mais uma linha `>` quando decidiu algo que precisa ser dito, como nome mantido ou diagrama só no formato embutido.
3. Ele faz `git fetch` em cada repositório da config; se o fetch falhar, sai **sem estado** — repasse o erro, nunca um estado.
4. **Saída 2 sem fila:** o projeto ainda não tem fila. Rode `sessao.py <projeto> --semear`, mostre o YAML, peça o `depende_de` de cada item, e **pare**.
5. **Saída 2 com lista de erros:** a config está inválida. Repasse os erros como vieram — eles nomeiam o campo e o arquivo.
6. **Saída 1:** ciclo em `depende_de`. Erro no topo, sem fila, pare.
7. **Processe as anotações da nota** (seção abaixo). É o único passo que grava fora do script — o usuário o pediu ao escrevê-las.
8. Componha a resposta com a receita abaixo.
9. Pare. Nenhum outro código, commit ou comando fora de `git`/`gh` sem o "pode ir".

Regras de estado, ordem, foco e bancada: `scripts/fila.py`. Esquema e validação da config: `scripts/config.py`. O que da nota sobrevive à regravação: `scripts/nota.py`. **Não as reescreva aqui.**

## A resposta (o que ela É, nesta ordem)

**Sessão DD/MM — <título do projeto>**

⚠️ **Divergências** — só se o script listou; copie as linhas dele.

*Desde <data da última sessão>:* 3 linhas, condensando o log do script.

**Estado agora** — a tabela do script, sem editar.

**Bancada** — o bloco `## Bancada` do script, sem editar: worktree e branch com trabalho não salvo (SUJA), parado fora da base sem PR (REPRESADA) ou sem nada a preservar (LIBERÁVEL). Uma SUJA no topo vira frase na sua resposta — trabalho não commitado se perde primeiro. Laudo por branch e limpeza são das skills de auditoria e remoção de branches, nunca à mão aqui.

**Grafo** — o bloco `mermaid` do script.

**Nota** — o caminho do `> nota:` e a linha de motivo, se veio.

**Sua nota, processada** — só se houve anotação nova: as linhas que você acrescentou ao rastro.

**Próximo passo (1 só):** o item 1 da seção "Próximo": o que é, por que é esse (estado, trava e foco, quando o foco o escolheu), o comando para começar, e `~N min` para a **próxima tarefa** que o script imprimiu.

**Na fila depois dele:** os itens 2 e 3, uma linha cada.

## As anotações da nota

A nota tem duas seções que o script não escreve: `## Minhas anotações`, do usuário, e `## Sua nota, processada`, o rastro que você deixa. As duas voltam intactas a cada regravação — por isso nada se perde, e por isso a mesma anotação chega de novo em toda execução do dia.

1. Leia a nota do caminho do `> nota:`. Sem essa linha o script não gravou: pule este passo e diga por quê na resposta.
2. Cada item de lista ou parágrafo de `## Minhas anotações` é uma anotação. **Já citada no rastro = já processada** — pule. Sem essa conferência, a segunda execução do dia transforma o mesmo item em dois débitos.
3. Grave cada anotação nova no destino da classe dela:

| A anotação é | Destino | Linha no rastro |
|---|---|---|
| débito ou pendência de um repositório da config | `python3 ${CLAUDE_PLUGIN_ROOT}/skills/handoff/scripts/debito.py novo <raiz do repositório>` | `- "<trecho>" → DT-NNN (<sigla>)` |
| pendência sem repositório da config | a rota **local** da skill `eu-tenho-tdah` (`references/destinos-fora-de-repo.md`) | `- "<trecho>" → <o que a rota gravou>` |
| contexto — decisão, fato do dia, lembrete já resolvido | nenhum: ela fica na nota, verbatim | `- "<trecho>" → contexto` |
| não sabe classificar | a rota **local**, como pendência — anotação nunca fica sem destino | `- "<trecho>" → <o que a rota gravou> (sem classe)` |

4. Acrescente as linhas ao fim de `## Sua nota, processada`. Nada acima desse heading é seu, e linha antiga do rastro não se reescreve.

`<trecho>` é o começo da anotação, o bastante para achá-la. A gramática dos campos do débito é a do `debts/README.md` do repositório de destino. O `debito.py novo` escreve e não commita: o item aparece na **Bancada** como SUJA até entrar na próxima PR daquele repositório — visível, nunca perdido.

## Sinais de alerta — pare e volte ao script

| Pensamento | Realidade |
|---|---|
| "fetch fica fora do escopo de só-leitura" | Fetch é leitura; sem ele o estado é de ontem. O script já o faz. |
| "vou ler o handoff e as branches para confirmar" | Handoff é intenção; o painel é evidência. Custa 2–3 min e diverge a cada leitura. |
| "dá para deduzir o projeto pela pasta em que estou" | O painel não adivinha, e você também não. Pergunte. |
| "três coisas, nesta ordem" | Um passo. O resto já está na tabela. |
| "mergear ou fechar", "decidir se…", "vale rever se…" | Opção não é próximo passo. O script escolheu; diga qual. |
| "rápido", "logo" | Minutos: `~15 min`. |
| `nginx -t`, `ssh`, deploy | Ritual de abertura não propõe comando fora de `git`/`gh`. |
| "eu faço, você aprova" | Só depois do "pode ir". |
| "o script foi negado, refaço à mão" | Repasse a negação e pare. |
| "o foco manda, então ignoro o resto do painel" | Foco desempata; divergência, SUJA e trava aparecem sempre. |
| "vou rodar `git worktree list` para conferir a bancada" | A bancada já é evidência do script. Comando à mão diverge a cada leitura. |
| "essa branch dá para apagar agora" | LIBERÁVEL é diagnóstico. Remoção é da skill que executa, com prova reexecutada. |
| "rodo sem `--gravar`, é só para ver o painel" | Sem a nota, as anotações do dia não têm onde chegar. `--dry-run` é o ensaio. |
| "essa anotação já está no rastro, mas reprocesso por garantia" | Citada no rastro = feita. Reprocessar duplica o débito. |
| "não sei onde vai, deixo na nota" | Sem classe vai para a rota local. Contexto é uma classe, não falta de destino. |
| "vou arrumar o texto da anotação" | `## Minhas anotações` é do usuário. Na nota, você só escreve o rastro. |

## Regras

- Nunca edite a fila sozinho; item novo sai de `sessao.py <projeto> --semear --so-novos` e entra por PR no repositório que a config declara dono.
- Alerta de `delta ativa fora da fila` não morre sozinho: ou vira PR na mesma sessão, ou a resposta diz que ficou de fora e por quê.
- Tudo `MERGED` → "fila vazia, precisa de spec nova". Pare.
- A config mora fora do plugin, e é lá que ficam os nomes reais dos repositórios. Nenhum deles entra nos arquivos desta skill.

## Arquivos da skill

- `scripts/sessao.py` — CLI `<projeto> [foco]`, orquestração e carimbo por projeto; `--selftest` agrega os módulos puros.
- `scripts/config.py` — dono do esquema da config e da validação que recusa sem produzir painel.
- `scripts/fila.py` — dono das regras: estado da delta, ordem topológica, foco, bancada e grafo como dado. 100% puro.
- `scripts/evidencia.py` — tudo que toca `git`, `gh` e disco; devolve dado cru, não decide.
- `scripts/contexto.py` — parsers puros do que a evidência traz: fila de débitos e recortes por janela.
- `scripts/nota.py` — dono da nota do dia: nome, composição, gravação atômica e o que do usuário sobrevive à regravação.
