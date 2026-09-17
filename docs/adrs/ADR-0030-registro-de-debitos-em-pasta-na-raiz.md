# ADR-0030: registro de débitos em pasta `debts/` na raiz — split total com um arquivo por item

- **Status:** Accepted (2026-08-11, delta-043)
- **Data:** 2026-08-11
- **Supersedes:** [ADR-0028](ADR-0028-arquivamento-de-debitos-encerrados.md) — integralmente: o arquivamento em `.claude/debts/` e a tabela `## Arquivados` dão lugar à pasta `debts/`; a renúncia ao "split total" cai. Também [ADR-0020](ADR-0020-modelo-de-divida-tecnica.md) **apenas nas renúncias a "arquivo por item" e a "front-matter"**, que caem de vez (agora também para ativos) — o modelo de fila (score derivado e nunca gravado, três eixos, `stale` calculado) segue integralmente vigente. E [ADR-0007](ADR-0007-registros-com-dono.md) **apenas na leitura de trajetória** (`git log DEBT.md` / `grep -c`): a trajetória passa a ser por arquivo. O file-first, os IDs `DT-NNN` e o "quitado muda de status, nunca some" seguem vigentes.
- **Superseded by:** [ADR-0031](ADR-0031-debt-md-como-indice-gerado.md) (2026-08-11, delta-047) — **apenas na cláusula 4** ("ponteiro fino"): o `DEBT.md` da raiz passa a ser o índice **gerado** dos ativos (projeção via `debito.py indice`, nunca fonte). A cláusula "Reabre quando" abaixo disparou por decisão de produto. Pasta `debts/` dona, um arquivo por item, quitação por `git mv` e "nunca deletado" seguem vigentes.

## Context

A ADR-0028 (2026-08-10, delta-041) tirou os encerrados do `DEBT.md` e **renunciou ao split total** ("todo DT em arquivo próprio exigiria reescrever `carregar`/`montar_fila`/`dias_parado` por ganho marginal"). Um dia depois, o Iuri pediu exatamente o split — como decisão de produto, não de custo: o registro de dívida deve ser uma **pasta de primeira classe na raiz**, no mesmo padrão do `specs/` (camada vigente + `_archive/`), com um arquivo por item, frontmatter legível por máquina e regras num README próprio — e **aplicado retroativamente aos 10 repos consumidores** (varredura de filesystem de 2026-08-11: 11 registros, 9 ainda no formato tabela pré-delta-024, nenhum com `.claude/debts/`).

Dois fatos novos baratearam o que a 0028 considerou caro: **(a)** `debts/ativos/` e `debts/_archive/` têm a mesma profundidade de `.claude/debts/` (2 níveis) — a migração dos 25 arquivados é `git mv` puro e a quitação passa a ser mover+renomear **sem nunca reescrever um link** (mata, para débitos, a família de apodrecimento do DT-040); **(b)** a retroatividade exige um conversor mecânico de qualquer forma (9 consumidores em tabela), e o mesmo `migrar` paga a migração deste repo.

## Decision

1. **`debts/` na raiz é o dono canônico** do registro: `README.md` (regras de cadastro, estados, fila e quitação), `LICOES.md` (post-mortems), `ativos/` (um arquivo por item vivo), `_archive/` (encerrados: `quitado` e `descartado`).
2. **Ativo = `debts/ativos/DEBT_DT-NNN-<topico>.md`** (sem data no nome), com frontmatter flat de chaves ASCII (`id`, `natureza`, `estado`, `fila`, `descricao`, `aberto`) parseado por regex stdlib ancorada — **não** PyYAML (opcional no repo, ADR-0023) — e corpo na gramática vigente de campos `- **Campo:** valor`. O `id` duplica o nome de propósito e o parser **valida a igualdade** (duplicação sancionada com check mecânico). A `fila` grava **só os eixos**; o score segue derivado e nunca persistido (ADR-0020).
3. **Quitação = editar + mover no mesmo commit:** `estado`/`encerrado` no frontmatter, campo **Encerrado** no corpo, `git mv` para `debts/_archive/DEBT_DT-NNN-<topico>_<AAAA>_<MM>_<DD>.md`. A data no nome espelha o frontmatter (duplicação documentada, conferida no review). Links intactos por construção.
4. **`DEBT.md` da raiz vira ponteiro fino e nunca é deletado** — preserva os links históricos (mesma razão da ADR-0025 para manter o `HANDOFF.md`). A tabela `## Arquivados` deixa de existir: a listagem da pasta e o `descricao:` grepável assumem a visibilidade.
5. **Dual-mode no `debito.py`:** `debts/ativos/` tem precedência; repo no layout de blocos segue funcionando com aviso de deprecação; `ids_arquivados` lê a **união** de `debts/_archive/` e `.claude/debts/`. O subcomando **`migrar`** converte blocos e tabela para o layout novo, preservando o campo **Ticket byte a byte** (chave de idempotência da ADR-0021) e **nunca inventando julgamento** — fila/data ausentes viram relatório de triagem.
6. **Gates:** `debts/**/*.md` entra em `scan_globs` e `exclude_globs` do `deps.toml`; `debts/_archive/**` fica fora do C3 pela exclusão default de histórico imutável (`**/_archive/**`), mesma classe de `specs/_archive/` — a conferência de links no arquivamento é humana, no review, e o move nem reescreve links.
7. **Propagação:** o template do `projeto-init` e a `canonical-rules.md` passam ao formato novo nesta mesma delta (o DT-022, que guardava essa propagação, é quitado) e a versão nova é aplicada **retroativamente** nos consumidores em rodada pós-release (`migrar` + triagem de eixos + verificação da projeção por repo).
8. Os 25 arquivos arquivados antes desta ADR **não são convertidos** — duas gerações coexistem no `_archive/`, documentadas no README.

## Alternativas recusadas

- **Manter as duas camadas da ADR-0028** (ativos como blocos): recusada por decisão de produto — o Iuri quer item endereçável por arquivo, com frontmatter, e a pasta como unidade visível do registro.
- **Score materializado no frontmatter:** recusada — segunda fonte da verdade; a proibição da ADR-0020 permanece (o frontmatter carrega os eixos, que já eram a fonte).
- **Ativos soltos em `debts/`** (sem `ativos/`): recusada — um nível a menos de pasta, mas cada quitação reescreveria os links do arquivo (+1 nível); com a subpasta, ativo e arquivado têm a mesma profundidade e o link escrito uma vez vale a vida inteira do item.
- **Data de abertura no nome do ativo:** recusada — nome instável (rename na quitação com troca de semântica da data); as datas vivem no frontmatter.
- **Manter a tabela-índice de arquivados:** recusada — duplicação a sincronizar a cada quitação; com um arquivo por item, o arquivo É a visibilidade.
- **Deletar o `DEBT.md` da raiz:** recusada — quebraria dezenas de links históricos (mesma razão da ADR-0025).
- **PyYAML para o frontmatter:** recusada — a fila é caminho obrigatório e a dependência é opcional/degradável no repo (ADR-0023); YAML interpretaria valores (`estado: no` → `False`); regex ancorada é determinística e segue a lição "verificação lê estrutura".

## Consequences

- O custo que a 0028 evitou é pago de uma vez: `carregar`/`dias_parado`/guardas do `debito.py` ganham o ramo de diretório, e o selftest dobra de fixtures (legado + novo). Em troca, a quitação deixa de reescrever links e o registro fica endereçável por arquivo (frontmatter grepável, diff por item, `git log` por item).
- `git log DEBT.md` deixa de contar a história — a trajetória de um item é `git log --follow` do arquivo dele; a tendência abertos×quitados sai de `ls debts/ativos | wc -l` × `ls debts/_archive | wc -l`.
- O relógio do `stale` zera na migração (o histórico por arquivo começa no commit dela) — custo real medido em 2026-08-11: zero itens com J≥3 perto do limiar.
- Consumidores migrados de tabela ficam com a fila **exigindo triagem de eixos** (o formato antigo não os tinha) — o exit ≠ 0 é a cobrança, nunca se inventa valor.
- Reabre quando: o volume de arquivos em `ativos/` tornar a listagem inútil como visão (aí a discussão é agrupamento/índice gerado), ou a leitura por arquivo se provar pior que a promessa de linha única da ADR-0007.
