# ADR-0042: lições em arquivo por item, com índice gerado e cadastro por comando

- **Status:** Accepted (2026-09-04, delta-107)
- **Data:** 2026-09-04
- **Supersedes:** [ADR-0030](ADR-0030-registro-de-debitos-em-pasta-na-raiz.md) — **apenas na cláusula 1**, onde `debts/LICOES.md` era o dono dos post-mortems. Tudo o mais da 0030 (pasta `debts/` dona, um arquivo por item, quitação por `git mv`, "nunca deletado") segue vigente e é o molde desta decisão.
- **Superseded by:** —

## Context

Até esta delta, `debts/LICOES.md` guardava 42 post-mortems como bullets de prosa densa num único arquivo. Quatro fatos motivaram a mudança, todos medidos no repositório em 2026-09-04:

1. **Citação ambígua.** As lições se citam por data ("a lição de 2026-08-16") e nove datas colidem — três entradas em 2026-08-16, três em 2026-08-03. Nenhum link entre lições existe, então o C3 do `validate_integrity.py` não confere nada.
2. **As perguntas que importam só se respondem lendo tudo.** Qual é a regra que fica, gerou algum `DT-NNN`, veio de qual PR ou commit, o que impede a reincidência — cada resposta estava enterrada em parágrafos de 9 linhas.
3. **Uma entrada carregava duas lições fundidas por conflito de merge** (a de 2026-08-13 sobre worktrees continha, sem separação, a colisão de numeração de 2026-08-11) — arquivo único com edição concorrente é exatamente a família de problema que a ADR-0030 já tinha resolvido para o débito.
4. **A pesquisa em fontes primárias converge.** SRE Book (cap. 15 e Apêndice D), SRE Workbook, Etsy/Allspaw, Salesforce, PMI (Rowe & Sikes) e Télios pedem ID estável, origem rastreável, causa separada de sintoma e gatilho, e ação preventiva com dono e número de rastreio; a doc da Anthropic para memória de agente pede literalmente "one lesson per file with a one-line summary at the top". Fontes e citações: `specs/_archive/107-licoes-por-arquivo/research.md` (ou `specs/107-…` enquanto a delta está aberta).

O débito já tinha o molde: um arquivo por item com frontmatter validado, ID global, cadastro por comando (`debito.py novo`) e índice gerado (`DEBT.md`, ADR-0031). A pergunta era se a lição merecia o mesmo tratamento ou um arranjo mais leve.

## Decision

1. **`debts/licoes/` é o dono canônico das lições**; `debts/LICOES.md` passa a ser **projeção gerada** (índice), nunca fonte — o mesmo par dono/projeção que `debts/ativos/` e `DEBT.md` formam.
2. **Uma lição é `debts/licoes/LICAO_L-NNN-<topico>.md`**, com frontmatter flat de chaves ASCII — `id`, `data` (do incidente), `descricao` (a **regra que fica**, uma linha, teto do R141), `familia` (kebab-case livre), `deteccao` (`gate|revisao|humano|sorte`), `prevencao` (`gate|debito|disciplina`), `origem`, `gerou` (DTs), `reincide` (lições) — e corpo em quatro seções fixas: O que aconteceu · Causa (um fator por linha; "erro humano" não é causa — descreve-se a lacuna do sistema ou do processo) · Desfecho · Prevenção, fechando com Origem e Registro.
3. **Cadastro só por `licao.py nova`**, que calcula o `L-NNN` (união do disco com os refs remotos já buscados, sem rede), valida enums, arestas (`gerou` contra DTs existentes, `reincide` contra lições existentes), a ordem das seções e o teto da `descricao`, e apaga o que não passa — o arquivo nasce válido ou não nasce.
4. **`licao.py indice .` regenera o `LICOES.md`** (determinístico; contagens por `deteccao` e `prevencao`; "reincidiu em" derivado das lições posteriores; famílias com reincidência) e **`--verificar` é step do CI**: eleger uma cópia como fonte é meia consolidação, a outra metade é o check que a vigia.
5. **A lição é imutável** após o commit: o hook `guarda-imutaveis.py` pede confirmação em `debts/licoes/`; reincidência é lição nova com `reincide:`; lição errada é corrigida por lição nova que a cita, nunca apagada.
6. **A lição nasce quando o desfecho já existe** (correção mergeada, configuração aplicada, ou DT aberto para o que sobrou), no fechamento da sessão, e sobe à `main` pelo PR dessa sessão — sem esperar um PR: 30 dos 43 incidentes registrados não eram PR.
7. **Os dois enums são valores governados** no `deps.toml` (dono: a gramática em `skills/handoff/references/licoes.md`), e a decisão se propaga aos templates da `projeto-init`, ao passo 1 da `handoff` e aos READMEs. As 42 entradas deste repositório migram na mesma delta (43 lições); os consumidores migram em rodada posterior.

## Alternativas recusadas

- **Arquivo único com blocos estruturados** (`### L-NNN · data · regra` em `LICOES.md`): daria IDs sem custo de script, mas sem checagem mecânica — o arquivo passaria de 57 para ~600 linhas de prosa, a edição concorrente continuaria colidindo, e nenhum gate conferiria links nem enums.
- **Enum fechado de `familia`**: família nova exigiria mudar o script; a reincidência é descoberta lendo, e o índice já agrupa por valor igual — kebab-case livre basta, e divergência de grafia é pega no review.
- **`estado` e `dono` na lição** (SRE, Télios): a lição só existe quando a ação já tem destino — o estado vive no DT que ela gerou, e o dono é o repositório. Estado na lição criaria uma segunda máquina de estados para o mesmo trabalho.
- **Editar ou apagar lições** (doc Anthropic, *Construct a memory system*: "update an existing note rather than creating a duplicate; delete notes that turn out to be wrong"): recusado em favor do registro de época da ADR-0007 — a história de como se aprendeu vale tanto quanto a regra, e a reincidência citando a lição antiga é o que torna a família visível.
- **`licao.py` como subcomando do `debito.py`**: o script já tem 2235 linhas e uma responsabilidade (fila, projeção, cadastro de dívida); a lição é entidade distinta — um módulo por responsabilidade (CLAUDE.md, Clean Code), importando do `debito.py` o que é comum em vez de reimplementar.
- **Conversor `licao.py migrar` mecânico**: a reescrita das 42 entradas é editorial (extrair regra, separar causa de sintoma, classificar detecção e prevenção) — um conversor produziria 42 arquivos com a prosa antiga dentro de campos vazios.

## Consequences

- **Custo:** um script novo com selftest co-localizado, uma gramática, um template, um bloco no `deps.toml`, propagação em quatro skills e dois READMEs, e 43 corpos reescritos à mão — pagos em quatro PRs (artefatos, mecanismo, doc, migração) mais o archive.
- **Ganho:** citação estável (`L-NNN`) checada pelo C3; as contagens de `deteccao` medem quanto os gates do framework realmente pegam (insumo do DT-017), e a lista de `prevencao: disciplina` é o backlog de mecanização visível; `gerou`/`reincide` tornam a família de um incidente uma aresta, não uma frase.
- **O que fica mais difícil:** registrar uma lição custa um comando com nove campos em vez de um bullet — é o preço de a lição ser consultável; o teto de palavras avisa quando a narrativa vaza para dentro dela.
- **Reabre quando:** o índice por família deixar de bastar para ler o registro (aí a pergunta é se lição precisa de fila, e a resposta hoje é não), ou quando um consumidor mostrar que a migração editorial não escala — nesse dia o `migrar` mecânico volta à mesa com o custo medido.
