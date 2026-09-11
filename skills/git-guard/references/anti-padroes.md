# Anti-padrões de git — catálogo canônico

> **Dono canônico.** Este arquivo é a fonte da verdade dos anti-padrões de git do framework: o identificador `Gn`, a severidade, o que detecta e o que trava. A `SKILL.md` orquestra e aponta para cá; o `audit_workspace.py` implementa os checks; a `projeto-infra` consome a coluna *servidor* ao montar o ruleset. Nenhum dos três reimplementa o texto da regra.
>
> **Nenhum limiar numérico nasce aqui.** Onde o catálogo precisa de um teto, ele referencia o limiar canônico já existente — hoje só o de tamanho de PR, cujo dono é [canonical-rules.md](../../projeto-init/references/canonical-rules.md) e cuja propagação o `deps.toml` governa.

## As três camadas

Uma trava só vale onde consegue interceptar. Toda entrada do catálogo declara em qual camada ela vive, porque a escolha errada de camada produz a sensação de proteção sem a proteção.

| Camada | O que é | Contornável? |
|---|---|---|
| **local** | hook de git versionado (`.githooks/` + `core.hooksPath`) | Sim — `--no-verify` desliga tudo de uma vez. É feedback rápido, não garantia. |
| **servidor** | ruleset do GitHub, proteção de push | Não, quando o bypass está desabilitado. É a garantia. |
| **agente** | hook `PreToolUse` do harness | Não pelo modelo — a decisão é do harness, não do prompt. |

A consequência de desenho: **hook local e CI têm de invocar o mesmo código.** Duplicar a regra nos dois é como o gate documentado passa a divergir do gate executado.

E a consequência que mais surpreende: **três dos anti-padrões mais graves não têm camada local nem servidor.** Nem hook de git nem ruleset chegam neles a tempo. Estão marcados com **(só agente)** abaixo.

## Ranking

Duas ordenações diferentes, porque *dano* e *frequência* não coincidem. `⚠` marca quem aparece nas duas — é a fila de prioridade real.

**Por dano quando ocorre**

| # | Anti-padrão | Dano |
|---|---|---|
| 1 | ⚠ G1 segredo commitado | credencial viva em história imutável; `revert` não resolve, exige rotação |
| 2 | ⚠ G12 force-push em branch compartilhada | apaga commit alheio; o `pull` seguinte de quem estava na branch destrói o trabalho local dele |
| 3 | ⚠ G13 descarte de árvore suja | trabalho não commitado não tem reflog — é a única categoria do git sem rede de segurança |
| 4 | G14 remoção forçada de worktree/branch não integrada | mesma irrecuperabilidade, agravada por o `--force` silenciar exatamente o aviso que era a proteção |
| 5 | ⚠ G4 main desprotegida | quebra o tronco para todos ao mesmo tempo |
| 6 | G7 binário grande na história | inchaço permanente do clone; remover exige reescrever a história de todos |
| 7 | G15 action não pinada por SHA | conta comprometida do mantenedor injeta código com acesso aos segredos do repo |
| 8 | ⚠ G11 `--no-verify` | não causa dano sozinho: desliga todas as travas locais de uma vez, e por isso multiplica 1, 4 e 5 |

**Por frequência de ocorrência**

| # | Anti-padrão | Por que é tão comum |
|---|---|---|
| 1 | ⚠ G6 mensagem genérica | é o default do humano cansado e do modelo — que resume o *diff*, não a *intenção* |
| 2 | ⚠ G16 `git add -A` | caminho de menor resistência, e o que quase todo tutorial ensina |
| 3 | ⚠ G5 commit gigante | uma sessão de agente toca dezenas de arquivos; sem teto, o commit natural é o de fim de sessão |
| 4 | ⚠ G4 main desprotegida | é o estado inicial de todo repositório até alguém configurar |
| 5 | G2 gate local desligado | hook não se propaga por clone; basta ninguém rodar o comando de ativação uma vez |
| 6 | G9 branch morto | apagar branch é trabalho manual que ninguém prioriza |
| 7 | G8 ausência de `.gitattributes`/CODEOWNERS | ninguém cria por iniciativa própria |
| 8 | ⚠ G11 `--no-verify` | assim que um hook falha sob pressão de terminar a tarefa, é a saída óbvia e documentada em toda a internet |

**Interseção (⚠) — a fila:** G1 · G11 · G4 · G12 · G13 · G16 · G5 · G6.

## Catálogo

Coluna **estado**: `check` = auditado hoje pelo `audit_workspace.py` · `trava` = tem mecanismo instalável hoje (`git-guard instalar`: hooks nativos, hook do harness, `.gitattributes`/CODEOWNERS) · `catalogado` = descrito e ranqueado, sem mecanismo ainda. A coluna diz o que existe, não o que se pretende.

### G1 — segredo versionado
**Dano:** máximo · **Frequência:** baixa por evento, catastrófica por consequência · **Camada:** local + servidor · **Estado:** trava

Arquivo rastreado cujo conteúdo casa um padrão de credencial conhecido, ou `.env` não rastreado num repositório sem `.gitignore` — um `git add -A` o versiona.

*Detecção:* casamento de padrão sobre arquivos rastreados, ignorando `*.example`. Sem esse recorte a maioria esmagadora dos casamentos é ruído de arquivo de exemplo, e auditoria ruidosa é auditoria ignorada.
*Trava:* casamento no `pre-commit` (bloqueia) e o mesmo código no CI (reprova, e o CI não conhece `--no-verify`). No servidor, proteção de push do GitHub — mas ela só é gratuita em repositório público.
*Achado nunca imprime o trecho casado*, apenas arquivo e padrão.

### G2 — gate local desligado
**Dano:** alto (indireto: desliga todos os outros checks locais) · **Frequência:** alta · **Camada:** local · **Estado:** check

`core.hooksPath` ausente, apontando para diretório inexistente, ou com hooks não executáveis.

*Detecção:* **resolver** o caminho contra o disco, nunca só ler a configuração — ler a config responde "tem hook" enquanto nada roda. Caminho absoluto é o modo de falha dominante: não sobrevive a mover a pasta do repositório, e como a configuração local não é versionada, nenhum gate acusa.
*Trava:* forma relativa, gravada na instalação. Não há trava real — a configuração é por clone e não se propaga; o que existe é a detecção.

### G3 — camada de agente ausente
**Dano:** alto · **Frequência:** altíssima (é o estado inicial de todo repositório) · **Camada:** agente · **Estado:** trava

Repositório sem hook do harness que alcance comandos `Bash` e sem regra de negação de git. Sem essa camada, G11, G12 e G13 ficam **sem trava alguma**.

*Detecção:* `.claude/settings.json` sem matcher que alcance `Bash` e sem `permissions.deny` de git.
*Trava:* hook `PreToolUse`. A regra de negação entra junto, como primeira linha barata — mas ela sozinha é furada (ver G12).

### G4 — main desprotegida
**Dano:** alto · **Frequência:** altíssima · **Camada:** servidor · **Estado:** check

Commit direto no tronco, sem review e sem CI verde.

*Detecção:* perfil que tem servidor (`rigido`/`cliente`) sem CI e sem proteção de branch detectável.
*Trava:* ruleset exigindo PR, **com bypass desabilitado** — bypass ligado devolve o buraco inteiro para quem tem papel de admin, inclusive um agente rodando com esse papel.

### G5 — commit gigante
**Dano:** médio (review superficial, `revert` impraticável, `bisect` inútil) · **Frequência:** altíssima · **Camada:** local + servidor · **Estado:** trava

*Detecção:* tamanho dos últimos commits, **ignorando merge commits** — sem esse recorte um merge infla a medição e produz achado falso.
*Limiar:* o canônico de tamanho de PR, sob a leitura "um commit que sozinho estoura o teto do PR é mudança não relacionada empacotada junto". Nenhum número novo.
*Trava:* **aviso** no `pre-commit`, nunca bloqueio — hook que bloqueia estilo é precisamente o que produz G11, e G11 desliga também G1. O bloqueio real fica no PR.

### G6 — mensagem de commit genérica
**Dano:** médio · **Frequência:** máxima · **Camada:** local + servidor · **Estado:** trava

*Detecção:* taxa de aderência a Conventional Commits nos últimos commits, contra o piso do perfil.
*Trava:* `commit-msg` local avisa; o *padrão de mensagem de commit* do ruleset reprova no servidor — é a única variante imune a `--no-verify`.

### G7 — arquivo grande rastreado
**Dano:** alto e diferido · **Frequência:** média · **Camada:** local + servidor · **Estado:** trava

*Detecção:* tamanho dos arquivos rastreados.
*Trava:* limite no `pre-commit`; *restrição de tamanho de arquivo* no ruleset.

### G8 — ausência de `.gitattributes` e CODEOWNERS
**Dano:** baixo (diff poluído por normalização de fim de linha; review sem dono definido) · **Frequência:** altíssima · **Camada:** local + servidor · **Estado:** trava

*Trava:* os dois arquivos, duas linhas cada. O check nasce junto com a instalação que o torna acionável — cobrar arquivo que o framework ainda não instala falha em todo lugar sem ação possível.

### G9 — branch morto e branch de sessão que nunca morre
**Dano:** baixo · **Frequência:** alta · **Camada:** nenhuma · **Estado:** check

Com agente o volume multiplica: cada sessão cria a sua e ninguém apaga.

*Trava:* **não existe, e é deliberado.** Apagar branch é destrutivo e já custou um PR dependente fechado por engano neste projeto. Fica como alerta, nunca como ação automática.

### G10 — árvore de trabalho suja
**Dano:** baixo, mas é sintoma · **Frequência:** alta · **Camada:** nenhuma · **Estado:** check

Lixo de ferramenta não ignorado, e o caso que importa: `.gitignore` *modificado e não commitado* — a correção foi feita e nunca salva.

### G11 — `--no-verify` ⚠ (só agente)
**Dano:** multiplicador · **Frequência:** máxima sob pressão · **Camada:** agente · **Estado:** trava

*Detecção:* **impossível localmente** — o hook simplesmente não roda, e não deixa rastro.
*Trava:* hook do harness, mais a réplica da mesma checagem no CI. É por isso que o catálogo insiste que hook e CI chamem o mesmo código: o CI é o que sobrevive ao bypass.

### G12 — force-push ⚠ (só agente, na prática)
**Dano:** máximo · **Frequência:** alta (push recusado → o modelo "resolve" com força) · **Camada:** servidor + agente · **Estado:** trava

*Trava:* *bloquear force push* no ruleset resolve no servidor. Na máquina, a regra de negação por padrão de comando **não basta** — ela casa a forma longa e deixa passar a flag curta, a flag global antes do subcomando e a refspec com prefixo `+`. Só o hook do harness vê o comando inteiro, com composições e wrappers, e por isso é ele que fecha o furo.

### G13 — descarte de árvore suja ⚠ (só agente)
**Dano:** máximo e irrecuperável · **Frequência:** alta · **Camada:** agente · **Estado:** trava

Descartar mudanças não commitadas para "limpar o estado e reexecutar". Não existe reflog para árvore suja: **não há trava possível no servidor nem no git.**

*Trava:* pedir confirmação na camada do agente. É a única que existe.

### G14 — remoção forçada de worktree ou branch não integrada
**Dano:** máximo · **Frequência:** média · **Camada:** agente · **Estado:** trava

A recusa do git *é* o aviso; `--force` silencia exatamente a proteção. Regra: recusa significa que aquele conteúdo só existe ali — mostrar ao humano e perguntar.

### G15 — action não pinada por SHA
**Dano:** alto (cadeia de suprimentos) · **Frequência:** máxima (é o que todo README de action mostra) · **Camada:** servidor · **Estado:** catalogado

Tag e branch são referências mutáveis: o mantenedor pode repontá-las a qualquer momento.

### G16 — `git add -A` ⚠
**Dano:** médio a alto (varia com o que estava fora do `.gitignore`) · **Frequência:** máxima · **Camada:** agente · **Estado:** trava

Já engoliu worktree de subagente como gitlink neste projeto, e já pulou arquivo em silêncio por causa de `.gitignore` por lista branca. O contorno é caminho explícito no `git add`.

## O que fica sem trava — e por quê

Débito honesto: o catálogo declara o buraco em vez de fingir cobertura.

- **Segredo sem prefixo reconhecível.** O casamento por padrões conhecidos alcança credencial com forma característica. Não alcança valor genérico — uma chave em base64 dentro de um manifesto sobreviveu exatamente assim num repositório auditado. A alternativa seria um scanner externo, recusado por política de dependência; a renúncia e o gatilho de reabertura estão em [ADR-0039](../../../docs/adrs/ADR-0039-recusa-de-scanner-de-segredo-externo.md).
- **Proteção de push do GitHub em repositório privado.** É a única trava de segredo verdadeiramente não contornável, e é paga fora de repositório público. Enquanto não for adquirida, G1 depende do par `pre-commit` + CI.
- **`git` chamado de dentro de um script que o próprio agente escreveu.** O hook do harness vê o comando de shell, não a chamada embutida em código. Só isolamento de sistema operacional alcançaria isso.
- **Repositório sem remoto** (existe só num disco). Nenhuma camada de servidor se aplica; por isso o perfil `rascunho` cobra apenas G1 e trata o resto como informativo.
- **Corpo e título de PR desatualizados** em relação aos commits que entraram depois da abertura. A regra é canônica (módulo `git-workflow`), mas a verificação exigiria falar com a API do GitHub — fronteira que esta skill não cruza (camada local é git-guard; servidor é projeto-infra). O dado existe (`userContentEdits` na API GraphQL) e um workflow conseguiria reprovar; a decisão de mecanizar é da delta-091, que a deixou fora de escopo.
- **G9 e G10 não ganham trava por decisão**, não por esquecimento: a ação corretiva é destrutiva e fica com o humano.
