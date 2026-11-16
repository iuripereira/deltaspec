# ADR-0047: O registro de captura é um repositório com `debts/`, não um ledger de linha

- **Status:** Accepted
- **Data:** 2026-09-10
- **Supersedes:** —
- **Superseded by:** —

## Context

A [delta-067](../../specs/_archive/067-destino-pendencias/) deu destino gravável à pendência que nasce sem registro `debts/`/`DEBT.md` alcançável, e a [delta-077](../../specs/_archive/077-tdah-captura-versionada/) fixou a rota local como padrão. As duas trataram a captura como **linha**: `- [ ] AAAA-MM-DD — <descrição> — origem: <origem>`, anexada a um arquivo append-only. A delta-067 declarou isso em "Fora de escopo", com a razão: *"Versionar, indexar ou colocar gate no ledger local — é captura; o registro canônico segue sendo o `debts/` do repo dono"*. A delta-077 acrescentou o commit sem push, e registrou como risco aceito que o ledger não tem versionamento nem backup.

Passados 24 dias, o ledger de uma máquina real acumulou mais de cem linhas. Nenhuma tem fila, nenhuma tem score, nenhuma envelhece: o `stale`, que existe para cobrar decisão sobre item de juros altos parado, não alcança arquivo que não é registro. O efeito medido: uma pendência de 2026-08-28 sobre um `git init` acidental ficou doze dias parada e só foi retomada porque uma sessão de reorganização tropeçou nela por acaso. Captura que ninguém revisa não é captura — é esquecimento com carimbo de data.

Ao mesmo tempo, o [DT-098](../../debts/_archive/DEBT_DT-098-repo-sem-debts-o-truth-manda_2026_09_13.md) registrou que a fronteira estava escrita duas vezes e em direções opostas: o R16 e a `handoff` mandam criar `debts/` num repositório que não tem, e o `destinos-fora-de-repo.md` mandava desviar a captura para fora dele. A raiz não era o texto: o passo "criar o registro" **não tinha mecanismo** — o comando de cadastro recusava, e o scaffold era prosa. Três skills discordavam sobre algo que nenhuma delas executava.

## Decision

O destino padrão da captura passa a ser um **registro** — um repositório com `debts/ativos/` — e não mais um arquivo de linhas. A pendência capturada nasce `DT-NNN`, com fila, envelhecimento e gate, pelo mesmo comando que serve o repositório dono.

A fronteira que o DT-098 acusou é resolvida **no mecanismo, não na prosa**: o comando de cadastro cria o registro quando o repositório declara `deltaspec.registro: proprio`, é idempotente por descrição e origem, e recusa antes de escrever quando o caminho está ignorado pelo git. Onde o mecanismo decide, três textos não têm como divergir — e foi a divergência entre textos, não a regra em si, que produziu o defeito.

Isso **reverte** uma decisão registrada em outro repositório. O `.gitignore` do repositório de configuração do usuário documentava, em comentário, que ele não teria pasta `debts/` justamente para não ser classificado como registro canônico, e o ledger na raiz era a rota escolhida para evitá-lo. A premissa era que captura e registro são naturezas diferentes. O que mudou não é a natureza — é a evidência de que "captura" sem fila e sem envelhecimento não sobrevive ao próprio volume.

Renunciamos a quatro alternativas:

- **Esticar o R16 para além do archive** — recusada porque a [delta-080](../../specs/_archive/080-reconcilia-cadastro-debito/) já o havia recusado nominalmente: *"sequestraria o requisito para fora do domínio dele"*. O R16 fica intacto, e o conflito morre do outro lado.
- **`specs/TRUTH.md` como marcador de registro próprio** — recusada porque amarra "tem registro" a "escreve delta specs", e o repositório que motivou esta decisão é o contraexemplo: ele quer registro e não quer ciclo.
- **Criação por flag explícita no comando** — recusada porque devolveria à prosa a decisão de *quando* passar a flag, que é exatamente o defeito em questão. Mecanismo que precisa de combinação prévia não substituiu o texto: só mudou o lugar do desacordo.
- **Aposentar a rota obsidian** — recusada porque ela separa natureza (dívida técnica × segundo cérebro), não backup, e nada nesta decisão produz motivo novo. As duas rotas passam a ter formas diferentes de propósito, e o texto diz por quê.

## Consequences

Fica mais fácil: pendência capturada passa a ter fila, score e `stale`, então o item parado cobra decisão em vez de esperar tropeço; a captura ganha o mesmo gate que o registro do repositório dono; e a fronteira do DT-098 deixa de depender de três textos concordarem.

Fica mais difícil: a captura deixa de ser uma linha que qualquer editor escreve e passa a exigir o comando; e o repositório que hospeda o registro de captura ganha um `debts/` que o comentário do `.gitignore` dele dizia não querer — quem ler aquele comentário sem esta ADR vai encontrar contradição, e a mitigação é o comentário passar a citá-la.

Trade-off aceito: um registro de captura acumula item de naturezas muito diferentes — ambiente de máquina, configuração, tangente de sessão — sob a mesma numeração e a mesma fila. É menos homogêneo que o registro de um produto, e a fila vai refletir isso. O ganho é que nada mais fica sem cobrança; o custo é que a triagem daquele registro exige mais julgamento que a de um repositório de código.

Impacto declarado em outros módulos: toda skill que roteia captura passa a **nomear a rota**, nunca o formato — a `git-guard` foi ajustada no mesmo change, porque mantinha cópia própria da regra. Duas prosas descrevendo o mesmo destino é a origem do DT-098, e a segunda envelhece sem que ninguém perceba.

Fora do recorte: a validação do campo `Local` ancora o caminho na raiz do registro, então captura vinda de outro repositório aponta o artefato como texto puro, sem link — legível, mas não clicável a partir do registro. Um link que resolva fora dele segue como pendência roteada desta delta; esta ADR não a decide.

<!--
Imutável após "Accepted". Mudou a decisão? Crie uma NOVA ADR com "Supersedes ADR-0047" e marque esta como "Superseded by ADR-YYYY". Nunca reescreva uma ADR aceita. Atualize o índice docs/adrs/README.md no mesmo PR. -->
