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
2. Rode `python3 ${CLAUDE_PLUGIN_ROOT}/skills/inicio-de-sessao/scripts/sessao.py <projeto> [foco]`. O foco é texto livre ("continua no estoque"); omitido, o script herda o da última sessão daquele projeto, e a palavra `sem` limpa.
3. Ele faz `git fetch` em cada repositório da config; se o fetch falhar, sai **sem estado** — repasse o erro, nunca um estado.
4. **Saída 2 sem fila:** o projeto ainda não tem fila. Rode `sessao.py <projeto> --semear`, mostre o YAML, peça o `depende_de` de cada item, e **pare**.
5. **Saída 2 com lista de erros:** a config está inválida. Repasse os erros como vieram — eles nomeiam o campo e o arquivo.
6. **Saída 1:** ciclo em `depende_de`. Erro no topo, sem fila, pare.
7. Componha a resposta com a receita abaixo.
8. Pare. Nenhum código, commit ou comando fora de `git`/`gh` sem o "pode ir".

Regras de estado, ordem, foco e bancada: `scripts/fila.py`. Esquema e validação da config: `scripts/config.py`. **Não as reescreva aqui.**

## A resposta (o que ela É, nesta ordem)

**Sessão DD/MM — <título do projeto>**

⚠️ **Divergências** — só se o script listou; copie as linhas dele.

*Desde <data da última sessão>:* 3 linhas, condensando o log do script.

**Estado agora** — a tabela do script, sem editar.

**Bancada** — o bloco `## Bancada` do script, sem editar: worktree e branch com trabalho não salvo (SUJA), parado fora da base sem PR (REPRESADA) ou sem nada a preservar (LIBERÁVEL). Uma SUJA no topo vira frase na sua resposta — trabalho não commitado se perde primeiro. Laudo por branch e limpeza são das skills de auditoria e remoção de branches, nunca à mão aqui.

**Grafo** — o bloco `mermaid` do script.

**Próximo passo (1 só):** o item 1 da seção "Próximo": o que é, por que é esse (estado, trava e foco, quando o foco o escolheu), o comando para começar, e `~N min` para a **próxima tarefa** que o script imprimiu.

**Na fila depois dele:** os itens 2 e 3, uma linha cada.

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
