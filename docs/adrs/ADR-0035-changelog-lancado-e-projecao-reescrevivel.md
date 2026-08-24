# ADR-0035: A entrada lançada do CHANGELOG é projeção reescrevível — o nome de época que ela cita não é

- **Status:** Accepted (2026-08-14, delta-062)
- **Data:** 2026-08-14
- **Supersedes:** ADR-0032
- **Superseded by:** —

## Context

A [ADR-0032](ADR-0032-erro-mecanico-de-caminho-e-corrigivel-no-imutavel.md) recortou a imutabilidade do registro **por classe de achado**: erro mecânico de caminho é corrigível; conteúdo de época — "nome histórico, número medido, decisão como foi tomada, prosa do requisito vigente à época" — é intocável. Ela tratou três diretórios sob a mesma regra: `specs/_archive/**`, `docs/adrs/**` e as seções lançadas do `CHANGELOG.md`, essa última herdada do [DT-028](../../debts/_archive/DEBT_DT-028-c3-em-changelog-lancado_2026_08_03.md), que justificou a proteção com o Keep a Changelog — "não se reescreve release publicado".

A medição de 2026-08-14 mostrou o custo de manter o CHANGELOG nessa classe. As 191 entradas deste repositório têm mediana de 323 caracteres e máximo de 1588; cada uma carrega título em negrito, ID da delta, escopo de requisito, origem na auditoria, a medição que decidiu e o porquê da renúncia. É a narrativa inteira — e ela já existe, completa, no PR que a mergeou, na delta que vive em `specs/_archive/` e na ADR que registrou a renúncia. O `CHANGELOG.md` estava duplicando conteúdo que tem dono canônico, o que a regra de ouro do repositório proíbe em qualquer outro arquivo.

O padrão que o repositório declara seguir diz o oposto do que a prática virou. O Keep a Changelog separa explicitamente os dois propósitos — "o propósito de um commit é documentar a etapa na evolução do código fonte; o propósito de uma entrada de changelog é documentar as **diferenças notáveis**" — e pede que versões e seções sejam vinculáveis, coisa que este CHANGELOG nunca teve. A prática da comunidade convergiu para `- <frase curta> (#PR)`, com a história do lado de lá do link.

Encurtar as entradas exige reescrever seção lançada. Sob a ADR-0032, isso é proibido — e a proibição não distingue **a forma da entrada** do **conteúdo que ela cita**. Essa indistinção é o defeito: o `sdd-iuri` de antes do rename e o `STATE.md` de antes da delta-010 aparecem 9 vezes cada no CHANGELOG, e esses **são** conteúdo de época; a frase de 1588 caracteres que os envolve não é.

## Decision

Recortamos a classe uma segunda vez, agora dentro do CHANGELOG:

- **A forma da entrada lançada é reescrevível.** Condensar a prosa de uma entrada publicada para a forma canônica — uma frase mais a referência do PR — não apaga registro, porque nada morava só ali: o PR, a delta arquivada e a ADR continuam sendo os donos da narrativa, e a entrada passa a **referenciá-los** em vez de duplicá-los. A entrada lançada é **projeção**, na mesma acepção em que o `DEBT.md` é projeção dos arquivos de `debts/` ([ADR-0031](ADR-0031-debt-md-como-indice-gerado.md)) e a Release do GitHub é projeção da tag.
- **O nome de época citado na entrada permanece intocável.** `sdd-iuri`, `STATE.md`, o número que valia naquela época: a reescrita condensa a narrativa e **nunca renomeia o passado**. A guarda do [DT-010](../../debts/ativos/DEBT_DT-010-referencias-a-state-md.md) e o R47 sobrevivem sem emenda.

O limite entre as duas: se a edição muda **o que se lê sobre o que aconteceu**, é conteúdo de época e não se toca; se ela apenas troca a duplicação da narrativa por uma referência ao seu dono canônico, é reprojeção e se faz.

**O que a ADR-0032 decidiu e continua valendo, reafirmado aqui integralmente:**

- `specs/_archive/**` e `docs/adrs/**` seguem sendo registro imutável, sem qualquer recorte novo — esta ADR não os toca.
- Erro mecânico de caminho — link relativo cuja profundidade foi quebrada pelo próprio move do archive — segue corrigível no registro imutável, porque o conteúdo pretendido não muda e a correção é decidível por máquina.
- A garantia da fronteira segue mecânica: o **C13** do `check_cycle.py` confere os links relativos das deltas arquivadas e o **C3** do `validate_integrity.py` segue cego ao archive. Nenhum gate ganha licença genérica para auditar registro imutável.

O C3 continua parando na primeira seção lançada do CHANGELOG, mas **por outra razão**: não mais imutabilidade, e sim porque a entrada lançada cita caminho de época, que resolve contra a árvore daquele release e não contra a de hoje. O comportamento é o mesmo; a justificativa registrada muda, e o R13 é atualizado no mesmo archive.

Renunciamos a três alternativas. **Manter a ADR-0032 intacta e aplicar a forma nova só daqui em diante** foi recusada porque produz um arquivo com duas gramáticas — 58 versões verbosas e as futuras curtas — e a inconsistência custaria mais na leitura do que a reescrita custa uma vez. **Reescrever sem ADR**, tratando o caso como exceção pontual, foi recusada pela razão que a própria ADR-0032 registra: a garantia da imutabilidade não sobrevive a exceções julgadas caso a caso. **Reescrever também o nome de época**, uniformizando o texto antigo, foi recusada porque é exatamente o que a ADR-0032 existe para impedir, e nada no problema medido pedia isso.

## Consequences

Fica mais fácil: o CHANGELOG volta a ser legível em segundos por versão, com a história a um clique; a regra de ouro deixa de ter uma exceção não declarada; e o formato ganha o gate `check_changelog.py`, que fecha a reincidência registrada na [LICOES.md](../../debts/LICOES.md) ("o plano esquece o CHANGELOG" — três reincidências, com a decisão "se reincidir, mecanizar").

Fica mais difícil: "registro imutável" passa a ter duas ADRs recortando-o em vez de uma, e a distinção entre *forma da entrada* e *nome citado na entrada* é sutil o bastante para precisar ser apontada sempre que alguém propuser editar histórico. A mitigação é a mesma da ADR-0032: a licença é estreita e nomeada — vale para o `CHANGELOG.md` e só para a forma da entrada; qualquer outra classe continua sem cobertura e sem respaldo.

Trade-off aceito: a reescrita das 58 versões deste repositório é pagamento único, sai em PRs próprios (o limiar de tamanho de PR não admite fazê-la junto da regra) e o casamento entrada↔PR é dirigido, não automático — 207 dos 215 commits da `main` carregam `(#NNN)` do squash, mas escolher qual PR corresponde a qual bullet exige ler o escopo do commit.

Fora do recorte, e sem cobertura: a **presença** da entrada (PR que muda comportamento e não toca o CHANGELOG) continua por disciplina. O gate desta delta valida forma, não cobertura — medir cobertura exige ler o diff e é outra conta, registrada como fora de escopo na delta-062.

<!--
Imutável após "Accepted". Mudou a decisão? Crie uma NOVA ADR com "Supersedes ADR-0035" e marque esta como "Superseded by ADR-YYYY". Nunca reescreva uma ADR aceita. Atualize o índice docs/adrs/README.md no mesmo PR. -->
