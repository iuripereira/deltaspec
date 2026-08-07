# Fila de dívida técnica e projeção para tickets

## Gramática do registro

Cada item é um bloco. Os campos valem **na âncora de início de linha** — a mesma sintaxe citada dentro da descrição é prosa, não campo:

```markdown
### DT-001 · débito · aberto
**Parser do check_cycle acoplado ao formato dos templates**

Descrição em prosa, quantas linhas precisar.

- **Fila:** `P3·J3·Pr9`
- **Local:** [check_cycle.py]({caminho/do/artefato.py})
- **Gatilho:** template mudar de forma
- **Origem:** [PR #{N}](../../pull/{N}) · [delta-{NNN}](specs/_archive/{NNN-nome}/) · aberto em {AAAA-MM-DD}
- **Ticket:** [#{N}](../../issues/{N})
```

> Os `{…}` acima são placeholders do exemplo — no arquivo real vão os valores. A chave também faz o validador de integridade pular estes links, que são de exemplo e não apontam arquivo.

`guarda` dispensa **Fila** e **Local**. Item `quitado` ou `descartado` troca **Ticket** por **Encerrado**, que carrega data e referência. Referências a PR, issue e delta são links relativos (`../../pull/N`, `../../issues/N`, `specs/_archive/NNN-*/`) — resolvem no GitHub e sobrevivem a fork. A legenda dos estados vive no cabeçalho do próprio `DEBT.md`, não aqui.


Regra canônica de **como priorizar dívida** e **como projetá-la** numa ferramenta de ticket. O registro em si tem dono próprio: o `DEBT.md` da raiz ([ADR-0007](../../../docs/adrs/ADR-0007-registros-com-dono.md)). As decisões e renúncias estão na [ADR-0020](../../../docs/adrs/ADR-0020-modelo-de-divida-tecnica.md) (modelo) e na [ADR-0021](../../../docs/adrs/ADR-0021-projecao-de-tickets.md) (projeção).

Os limiares numéricos (janela de churn, dias até `stale`, percentis, escala) vivem como **constantes nomeadas** no `scripts/debito.py` — este documento os cita pelo nome, nunca pelo valor.

## O score

```
score = (juros × probabilidade) / principal
```

Os três eixos usam a mesma escala de três degraus — baixo, médio, alto (`ESCALA` no script):

| Eixo | Baixo | Médio | Alto |
|---|---|---|---|
| **Principal** — custo de pagar | menos de um dia | cerca de um ciclo | mais de um ciclo |
| **Juros** — atrito já observado | incômodo | atrasa entregas | bloqueia entrega |
| **Probabilidade** — chance de incidir | artefato frio | morno | tocado toda semana |

**Juros é atrito observado, não hipótese.** Se ninguém tropeçou, o juro é baixo — dívida que não cobra não tem pressa.

**Probabilidade não se chuta.** O script deriva a estimativa do churn do arquivo apontado em `Local` (percentil sobre o `git log` da janela configurada) e reporta divergência contra o valor declarado. Quem manda é o valor declarado; a derivação existe para desmentir otimismo.

> **Viés conhecido:** churn mede atividade **no arquivo**, não frequência com que **a dívida** incide, e superestima defeito de borda em arquivo movimentado. Por isso a derivação **informa e não decide**: divergir dela é legítimo, ignorá-la sem olhar não é. (Caso concreto na seção Lições do `DEBT.md`.)

O score é **derivado na leitura e nunca gravado**. Persistir o cálculo criaria uma segunda fonte da verdade — exatamente o que a regra de ouro proíbe.

**Proibições:** não converter score em dinheiro (falsa precisão que muda a conversa para a planilha); não priorizar por principal isolado (barato e inofensivo continua sendo trabalho sem retorno); não reordenar a fila a cada sessão — a revisão acontece quando o gatilho dispara ou quando o aging cobra.

## A. Override — impedimento, não prioridade alta

Quatro casos furam a fila, nesta ordem de precedência: **security** (risco de vazamento ou comprometimento) · **compliance** (não conformidade com exposição legal) · **eol** (fim de suporte com data marcada) · **contract** (bloqueio de entrega contratada).

Sintaxe na coluna `Fila`: `P?·J?·Pr? · !<caso>(AAAA-MM-DD)`.

Override **ignora o principal** e entra como escopo obrigatório do ciclo, fora da competição por score. **Exige prazo**: sem data, não é impedimento — é opinião, e o item volta a disputar por score. O script recusa a sintaxe sem prazo.

## B. Trilha planejada — o anti-starvation da dívida cara

O problema que isto resolve: dividir por principal enterra permanentemente o item grande. Justamente o que trava a arquitetura nunca alcança o topo.

Item com **principal alto e juros ao menos médios** sai da competição por score e entra na trilha: sufixo ` · trilha` na coluna `Fila`.

- A trilha **não compete** — ela é agendada, não sorteada pelo score.
- **A trilha é uma delta própria.** O fatiamento não inventa mecanismo: é o `tasks.md` com arestas `(dep: Tn)` que o framework já usa (R40/R41). O item do `DEBT.md` vira o agregador e cita a delta.
- Fatia acoplada a uma feature que já toca a mesma `Local` custa menos que refatoração isolada — pagamento oportunista é o barato.
- **No máximo uma trilha ativa por repositório.** Duas trilhas simultâneas significam que nenhuma termina.

## C. Aging — a decisão que não pode ser adiada para sempre

Item com juros ao menos médios cuja linha não muda há mais que o limiar (`STALE_DIAS`) é marcado **`stale`** na saída do script. A marca é **derivada do git** (`git log -1 -S"DT-NNN"`), nunca escrita no arquivo — o histórico já sabe a data; gravá-la seria duplicação.

`stale` não é um estado: é uma cobrança. Ele força escolher entre **agendar** (abrir a delta), **aceitar** (com gatilho) ou **descartar** (com motivo). Permanecer indefinidamente em `aberto` é falha de gestão, não backlog.

## D. Aceitação — decisão legítima, não fracasso

`aceito` é dívida deliberada e prudente: você sabe que ela existe, mediu o custo e escolheu conviver. **Exige gatilho de reavaliação** — o script recusa `aceito` sem gatilho. A diferença entre dívida aceita e dívida esquecida é exatamente essa linha.

## Matriz de decisão

| | Principal baixo | Principal alto |
|---|---|---|
| **Juros altos** | **Pague agora** — topo do score | **Trilha planejada** — fatie e acople a features |
| **Juros baixos** | Oportunístico — regra do escoteiro | **Aceite** com gatilho; não gaste hora |

## Projeção para ferramenta de ticket

O `DEBT.md` é a fonte; GitHub Issues e Jira são **projeção para gestão humana**. Quem executa os comandos é a skill — o script apenas emite arquivos e **nunca acessa a rede** (mesmo padrão do `projeto-infra`, roteiro sem script instalável).

**Ida (mecânica).** `debito.py exportar` produz o JSON canônico (`tickets.json`) e os dois dialetos: `.sh` de `acli jira workitem create` **unitários** (`tickets-acli.sh` — um create por item, corpo em `corpo-DT-NNN.md`, mesmo padrão do `tickets-gh.sh`) e as linhas de criação do GitHub. O dialeto Jira era um lote `create-bulk` até a primeira execução real contra projeto Jira de verdade (DT-021, 2026-08-07): o `create-bulk` rejeita `\n` na `description` — até quebra simples de linha — então o lote saiu e o unitário, que preserva o corpo multi-linha, entrou. Revise o corpo antes de executar — o conteúdo vai para uma ferramenta que pode ser pública. Criado o ticket, **grave a chave na coluna `Externo`**: é ela, e não o título, que evita duplicata na próxima execução.

**Volta (sempre avaliada).** Colete o estado e rode `debito.py diff`:

```bash
gh issue list --search "label:deltaspec:debito,deltaspec:pendencia" --state all \
  --json number,title,state,labels > estado.json
```

A vírgula no `--search` é **OR**; `--label` seria AND e não serve, e filtrar por `--label dt` não funciona porque a etiqueta de identidade é `dt:DT-NNN`, não `dt` (verificado na primeira projeção real, 2026-08-01). Leia então a tabela *DEBT.md diz × ferramenta diz × impacto × ação proposta*. A IA **propõe**; o humano aprova; só então o `DEBT.md` muda. A ferramenta externa nunca sobrescreve o arquivo.

**Degradação.** Sem `gh`/`acli`, sem autenticação ou sem projeto configurado, o `DEBT.md` segue valendo sozinho — no máximo uma linha de aviso (RNF2).

**Limitação conhecida:** os *issue fields* do GitHub (número, data) só existem em repositório de organização; em repositório pessoal os valores são **descartados em silêncio**. Por isso o score vai no corpo do ticket e em etiqueta de faixa, não em campo estruturado.
