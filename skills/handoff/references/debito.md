# Fila de dívida técnica e projeção para tickets

## Gramática do registro (layout `debts/`, ADR-0030)

Cada item ativo é **um arquivo** `debts/ativos/DEBT_DT-NNN-<topico>.md` (topico em kebab-case, sem data). O frontmatter é flat, com chaves ASCII sem acento; o corpo mantém os campos `- **Campo:** valor` **na âncora de início de linha** — a mesma sintaxe citada dentro da prosa não é campo:

```markdown
---
id: DT-001
natureza: débito
estado: aberto
fila: P3·J3·Pr9
descricao: Parser do check_cycle acoplado ao formato dos templates
aberto: {AAAA-MM-DD}
---

# [DT-001] - Parser do check_cycle acoplado ao formato dos templates

Descrição em prosa, quantas linhas precisar (seções `####` opcionais são prosa livre).

- **Local:** [check_cycle.py]({caminho/do/artefato.py})
- **Gatilho:** template mudar de forma
- **Origem:** [PR #{N}](../../../../pull/{N}) · [delta-{NNN}](../../specs/_archive/{NNN-nome}/)
- **Ticket:** [#{N}](../../../../issues/{N})
```

> Os `{…}` acima são placeholders do exemplo — no arquivo real vão os valores. A chave também faz o validador de integridade pular estes links, que são de exemplo e não apontam arquivo.

O `id` do frontmatter duplica o do nome de propósito e o script **valida a igualdade** (o nome é a fonte); a primeira linha do corpo é o **título humano** `# [DT-NNN] - <descricao>`, espelho do frontmatter igualmente validado (delta-048). `guarda` dispensa **Local** e **não pode** ter `fila`. `- **Fila:**` no corpo é erro: a fila vive só no frontmatter. Links são relativos ao arquivo (2 níveis: repo = `../../x`, atalho GitHub = `../../../../issues/N`) — e como `ativos/` e `_archive/` têm a mesma profundidade, **a quitação nunca reescreve link**.

**Cadastro = `debito.py novo`, não edição à mão.** O comando calcula o `DT-NNN` e escreve o arquivo já no formato acima:

```bash
debito.py novo . --natureza {débito|pendência|guarda} --descricao "sintoma observável" \
  [--fila P·J·Pr] [--local "[artefato](caminho/da/raiz.py)"] [--gatilho "quando reavaliar"] \
  [--origem "delta-NNN"] [--ticket CHAVE] [--corpo-arquivo prosa.md]   # ou a prosa por stdin
```

Três garantias que a edição manual não dá. **O ID sai da união** de `debts/ativos/`, `debts/_archive/`, `.claude/debts/` **e dos refs de rastreio remotos já buscados** (`refs/remotes/*`, lidos em disco — o script não acessa a rede), lidos do **nome** dos arquivos: cadastro em duas branches deixa de gerar o mesmo número, e ativo malformado não derruba a conta. **Nada é inventado:** campo que a natureza exige e não veio faz o comando recusar nomeando o campo. **O arquivo nasce válido ou não nasce:** o comando relê o que escreveu com o próprio parser e o `validar` da fila, e apaga o arquivo se não passar — a conferência acontece no cadastro, não semanas depois quando o `fila` reprova (DT-077). `--local` e `--origem` são escritos **relativos à raiz**; o comando os reescreve para os 2 níveis. Depois de cadastrar, regenere o índice.

**Quitação/descarte = `debito.py quitar`, não edição à mão** (delta-097 mecanizou o ritual manual que existia até então). Pré-condição: o frontmatter **já** declara `estado: quitado` ou `estado: descartado` — decidir qual dos dois é de quem chama (é a única edição manual que sobra, 1 linha); o comando faz o resto, no mesmo commit:

```bash
debito.py quitar . DT-NNN --como "2-4 frases: o que doía, o que foi feito, o que muda" \
  [--ticket-ref "delta-NNN · #{PR}"]
```

Grava `encerrado: {AAAA-MM-DD}` no frontmatter, injeta a seção **`#### Como foi quitado`** no corpo (linguagem amigável, sem jargão de implementação — isso fica no commit/PR e no comentário do issue), troca **Ticket** por `- **Encerrado:** data[ · referência]` (referência só quando `--ticket-ref` é passado), e move o arquivo com `git mv` para `debts/_archive/DEBT_DT-NNN-<topico>_<AAAA>_<MM>_<DD>.md`. Mesma garantia de "nada é inventado" do `novo`: recusa sem `--como`, recusa se o estado não é final ainda, recusa se o `DT-NNN` não existe em `ativos/` — e a edição só fica no disco depois de reler com o próprio parser e o `validar` da fila (edição inválida nunca persiste). O `debito.py` lê os IDs arquivados do **nome** dos arquivos, na união de `debts/_archive/` e `.claude/debts/` (legado): a fila avisa candidato a arquivamento esquecido em `ativos/`, e o `diff` trata ID arquivado como estado final. A legenda completa dos estados vive em `debts/README.md`, não aqui.

**Índice da raiz (ADR-0031).** O `DEBT.md` é a projeção gerada dos ativos — `debito.py indice` o reescreve com seções por **valor gravado** (Críticos = override com prazo · Importantes = J9 · Médios = J3 · Não urgentes = J1 · Sem triagem = pontuável sem `fila` · Guardas), ordem interna por score derivado na geração, seção vazia omitida e `stale` de fora (marca temporal não entra em arquivo gerado). Nunca edite o índice à mão: editar não muda item nenhum, e o `fila` avisa quando ele diverge do render atual. Regenere após cadastrar/quitar.

**Layout legado** (blocos `### DT-NNN · natureza · estado` no `DEBT.md`, ADR-0028): segue lido integralmente pelo dual-mode, com aviso de deprecação; `debito.py migrar` converte blocos ou a tabela pré-delta-024 para o layout novo — sem inventar julgamento: fila e datas ausentes viram relatório de triagem. `debts/ativos/` presente tem precedência e blocos remanescentes no `DEBT.md` são ignorados (com aviso quando a pasta está vazia).

Regra canônica de **como priorizar dívida** e **como projetá-la** numa ferramenta de ticket. O registro em si tem dono próprio: a pasta `debts/` da raiz ([ADR-0030](../../../docs/adrs/ADR-0030-registro-de-debitos-em-pasta-na-raiz.md), herdeira do file-first da [ADR-0007](../../../docs/adrs/ADR-0007-registros-com-dono.md)). As decisões e renúncias estão na [ADR-0020](../../../docs/adrs/ADR-0020-modelo-de-divida-tecnica.md) (modelo) e na [ADR-0021](../../../docs/adrs/ADR-0021-projecao-de-tickets.md) (projeção).

Os limiares numéricos (janela de churn, dias até `stale`, percentis) vivem como **constantes nomeadas** no `scripts/debito.py` — este documento os cita pelo nome, nunca pelo valor.

## O score

```
score = (juros × probabilidade) / principal
```

Os três eixos usam a mesma escala de três degraus — baixo (1), médio (3), alto (9):

| Eixo | Baixo | Médio | Alto |
|---|---|---|---|
| **Principal** — custo de pagar | menos de um dia | cerca de um ciclo | mais de um ciclo |
| **Juros** — atrito já observado | incômodo | atrasa entregas | bloqueia entrega |
| **Probabilidade** — chance de incidir | artefato frio | morno | tocado toda semana |

**Juros é atrito observado, não hipótese.** Se ninguém tropeçou, o juro é baixo — dívida que não cobra não tem pressa.

**Probabilidade não se chuta.** O script deriva a estimativa do churn do arquivo apontado em `Local` (percentil sobre o `git log` da janela configurada) e reporta divergência contra o valor declarado. Quem manda é o valor declarado; a derivação existe para desmentir otimismo.

> **Viés conhecido:** churn mede atividade **no arquivo**, não frequência com que **a dívida** incide, e superestima defeito de borda em arquivo movimentado. Por isso a derivação **informa e não decide**: divergir dela é legítimo, ignorá-la sem olhar não é. (Caso concreto em `debts/LICOES.md`.)

O score é **derivado na leitura e nunca gravado**. Persistir o cálculo criaria uma segunda fonte da verdade — exatamente o que a regra de ouro proíbe.

**Proibições:** não converter score em dinheiro (falsa precisão que muda a conversa para a planilha); não priorizar por principal isolado (barato e inofensivo continua sendo trabalho sem retorno); não reordenar a fila a cada sessão — a revisão acontece quando o gatilho dispara ou quando o aging cobra.

## A. Override — impedimento, não prioridade alta

Quatro casos furam a fila, nesta ordem de precedência: **security** (risco de vazamento ou comprometimento) · **compliance** (não conformidade com exposição legal) · **eol** (fim de suporte com data marcada) · **contract** (bloqueio de entrega contratada).

Sintaxe na chave `fila:` do frontmatter: `P?·J?·Pr? · !<caso>(AAAA-MM-DD)`.

Override **ignora o principal** e entra como escopo obrigatório do ciclo, fora da competição por score. **Exige prazo**: sem data, não é impedimento — é opinião, e o item volta a disputar por score. O script recusa a sintaxe sem prazo.

## B. Trilha planejada — o anti-starvation da dívida cara

O problema que isto resolve: dividir por principal enterra permanentemente o item grande. Justamente o que trava a arquitetura nunca alcança o topo.

Item com **principal alto e juros ao menos médios** sai da competição por score e entra na trilha: sufixo ` · trilha` na chave `fila:`.

- A trilha **não compete** — ela é agendada, não sorteada pelo score.
- **A trilha é uma delta própria.** O fatiamento não inventa mecanismo: é o `tasks.md` com arestas `(dep: Tn)` que o framework já usa (R40/R41). O item do registro vira o agregador e cita a delta.
- Fatia acoplada a uma feature que já toca a mesma `Local` custa menos que refatoração isolada — pagamento oportunista é o barato.
- **No máximo uma trilha ativa por repositório.** Duas trilhas simultâneas significam que nenhuma termina.

## C. Aging — a decisão que não pode ser adiada para sempre

Item com juros ao menos médios cujo cabeçalho não muda há mais que o limiar (`STALE_DIAS`) é marcado **`stale`** na saída do script. A marca é **derivada do git** (`git log -1 -G` sobre as chaves `natureza:`/`estado:` do arquivo do item; no legado, sobre o `DT-NNN` no `DEBT.md`), nunca escrita no arquivo — o histórico já sabe a data; gravá-la seria duplicação. Editar prosa não reinicia o relógio; mudar estado ou natureza reinicia.

`stale` não é um estado: é uma cobrança. Ele força escolher entre **agendar** (abrir a delta), **aceitar** (com gatilho) ou **descartar** (com motivo). Permanecer indefinidamente em `aberto` é falha de gestão, não backlog.

## D. Aceitação — decisão legítima, não fracasso

`aceito` é dívida deliberada e prudente: você sabe que ela existe, mediu o custo e escolheu conviver. **Exige gatilho de reavaliação** — o script recusa `aceito` sem gatilho. A diferença entre dívida aceita e dívida esquecida é exatamente essa linha.

## Matriz de decisão

| | Principal baixo | Principal alto |
|---|---|---|
| **Juros altos** | **Pague agora** — topo do score | **Trilha planejada** — fatie e acople a features |
| **Juros baixos** | Oportunístico — regra do escoteiro | **Aceite** com gatilho; não gaste hora |

## Projeção para ferramenta de ticket

O registro (`debts/`) é a fonte; GitHub Issues e Jira são **projeção para gestão humana**. Quem executa os comandos é a skill — o script apenas emite arquivos e **nunca acessa a rede** (mesmo padrão do `projeto-infra`, roteiro sem script instalável).

**Destino declarado (`motores.tickets`, delta-099).** Vocabulário fechado `none | github-issues | jira` no `doc-profile.yaml`. Ausente → deriva pela regra legada (`motores.jira.projeto` presente → `jira`; senão → `github-issues`) — nenhum repositório sem a chave muda de comportamento. `none` faz `exportar` recusar, citando a chave a declarar. Dono único da leitura: `ler_destino_tickets` em `projecao.py` — `debito.py` e `tickets.py` chamam a mesma função, nunca releem o campo por conta própria (DT-033).

**Ida (mecânica).** `debito.py exportar [--faixa alta|media|baixa]` produz o JSON canônico (`tickets.json`) e os dois dialetos: `.sh` de `acli jira workitem create` **unitários** (`tickets-acli.sh` — um create por item, corpo em `corpo-DT-NNN.md`, mesmo padrão do `tickets-gh.sh`) e as linhas de criação do GitHub. Unitário, não `create-bulk`: o bulk rejeita `\n` na `description` (DT-021, primeira execução real). `--faixa` recorta os dois dialetos pela mesma faixa de score da etiqueta `fila:*` — sem a flag, todos os itens pontuáveis entram (comportamento de sempre). Revise o corpo antes de executar — o conteúdo vai para uma ferramenta que pode ser pública. Criado o ticket, **grave a chave no campo `Ticket` do item**: é ela, e não o título, que evita duplicata na próxima execução.

**Volta (sempre avaliada).** Colete o estado e rode `debito.py diff`:

```bash
gh issue list --search "label:deltaspec:debito,deltaspec:pendencia" --state all \
  --json number,title,state,labels > estado.json
```

A vírgula no `--search` é **OR**; `--label` seria AND e não serve, e filtrar por `--label dt` não funciona porque a etiqueta de identidade é `dt:DT-NNN`, não `dt` (verificado na primeira projeção real, 2026-08-01). Leia então a tabela *registro diz × ferramenta diz × impacto × ação proposta*. A IA **propõe**; o humano aprova; só então o registro muda. A ferramenta externa nunca sobrescreve o arquivo.

**Fechamento de ticket na quitação (delta-049):** feche citando a quitação — **no GitHub** o comentário pode ser técnico, com links de commit/PR (é onde os detalhes moram); **no Jira** o comentário é em **nível de negócio**: o que foi resolvido e o impacto para o projeto, sem detalhe de implementação. O *como* em linguagem amigável vive na seção `#### Como foi quitado` do arquivo arquivado.

**Degradação.** Sem `gh`/`acli`, sem autenticação ou sem projeto configurado, o registro segue valendo sozinho — no máximo uma linha de aviso (RNF2).

**Limitação conhecida:** os *issue fields* do GitHub (número, data) só existem em repositório de organização; em repositório pessoal os valores são **descartados em silêncio**. Por isso o score vai no corpo do ticket e em etiqueta de faixa, não em campo estruturado.
