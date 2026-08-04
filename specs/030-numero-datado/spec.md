# delta-030 — número medido em cenário entra datado
Estado: proposta · Data: 2026-08-04 · Branch: docs/030-numero-datado · Perfil: enxuto — mudança de regra de escrita mais datação de números em 3 requisitos, sem código (aprovado: 2026-08-04)

Clarify: entrevistado (2026-08-04) — 2 decisões do usuário
<!-- trilha do clarify (R8): forma da correção (ilustração datada, contra "número sai do cenário" e "check que recalcula") e perfil da delta -->
Test-plan: dispensado — delta docs sem código; a verificação é dos próprios gates (check_cycle + validate_integrity) e do diff do archive

## Contexto (≤3 linhas)
Cenário do TRUTH pode citar número que era verdadeiro no dia da medição e deixa de ser depois, sem que nada acuse ([DT-029](../../DEBT.md)): o R13 diz "acusaria 19 links vivos do `DEBT.md`" — eram 23 na medição de 2026-08-03 (DT-029) e 24 em 2026-08-04, porque o ticket do próprio DT entrou no meio.
O agravante é mecânico: o MUDA repete o cenário vigente byte a byte (R7), que é o que impede perda silenciosa — e é exatamente o que carrega o número defasado adiante, delta após delta.
Datado, o número vira fato histórico ("eram 19 em 2026-08-02") que permanece verdadeiro para sempre, e a repetição mecânica passa a carregar uma afirmação que não apodrece.

## Mudanças

### R1 — MUDA R6 (delta-006): a delta declara só o que muda em relação ao TRUTH.md, e número medido em cenário entra datado
- DADO o `TRUTH.md` vigente QUANDO a spec é redigida ENTÃO cada bloco é ADICIONA, MUDA ou REMOVE, e blocos MUDA/REMOVE citam o alvo vigente (ex.: "MUDA R2 (delta-001)")
- DADO um requisito na delta QUANDO a spec é validada ENTÃO ele tem cenário DADO/QUANDO/ENTÃO verificável; qualidade sem limiar fechado vira pendência em riscos, não RNF
- DADO um cenário que cita número medido — contagem, medição ou estado observado do repositório ou do mundo — QUANDO ele é redigido na delta ou consolidado no TRUTH.md ENTÃO o número entra como **ilustração datada**, com a data (ou a delta) da medição junto do valor (ex.: "19 links (medição de 2026-08-02)"); afirmação de estado corrente sem data NÃO DEVE entrar em cenário, porque a consolidação mecânica do MUDA (R7) a repete adiante depois de ela deixar de ser verdade — valor normativo (limiar, teto, versão pinada, configuração sancionada) não é medição e segue sem data

### R2 — MUDA R13 (delta-029): valor de negócio duplicado entre arquivos é governado por manifesto e validado por script, e o check de links tem escopo próprio e recorte por conteúdo
- DADO um repo com `deps.toml` QUANDO `validate_integrity.py` roda ENTÃO verifica espelhos em sincronia (C1), materialização fora dos sancionados (C2) e links relativos vivos (C3), saindo 1 em qualquer violação
- DADO uma delta ainda aberta propondo valor novo QUANDO o validador roda ENTÃO ela não é acusada — as deltas abertas (`specs/NNN-*/`) ficam fora dos `scan_globs`; dentro de `specs/`, só o `TRUTH.md` consolidado (e `truth/`) entra na varredura
- DADO o `templates/deps.toml` da skill QUANDO um `exclude_globs` mira conteúdo de diretório ENTÃO o glob termina em `**/*.md` (nunca em `**` solto), com comentário no template explicando o porquê — `pathlib` ≤ 3.12 casa só diretórios num `**` final e o exclude viraria no-op
- DADO um arquivo dispensado de citar valor pelo `exclude_globs` QUANDO o C3 roda ENTÃO ele **é varrido mesmo assim** — a dispensa é de materialização (C2), nunca de link vivo; os dois checks passam a ter conjuntos próprios
- DADO um registro imutável — `specs/_archive/**` e `docs/adrs/**` — QUANDO o C3 roda ENTÃO ele fica fora, por chave própria `exclude_links_globs` no `deps.toml`: são registro de época (R47) e apontar rot que a política proíbe corrigir seria ruído
- DADO um `deps.toml` sem a chave `exclude_links_globs` QUANDO o C3 roda ENTÃO vale o **default nomeado do script** — os dois globs de histórico imutável acima —, nunca lista vazia e nunca o `exclude_globs` do C2: vazia despejaria os achados do archive num projeto que nunca pediu (26 só neste repo, medição de 2026-08-02), e herdar o do C2 manteria o ponto cego em todo projeto que não migrar o manifesto (DT-025)
- DADO um link no formato `../../issues/N`, `../../pull/N` ou `../../discussions/N` QUANDO o C3 o encontra ENTÃO ele o ignora como já ignora `http://` e `/` — é atalho relativo ao repositório do GitHub, não caminho de arquivo, e resolvê-lo como caminho acusaria os links vivos do `DEBT.md` (19 na medição de 2026-08-02)
- DADO um link que apenas sobe dois níveis ou mais (`../../docs/...`, `../../../docs/...`) QUANDO o C3 o encontra ENTÃO ele **é verificado normalmente** — o corte casa a **forma** do atalho, nunca o prefixo `../../`; cortar por prefixo silenciava 10 links de `SKILL.md`/`references` para ADR neste repo (medição de 2026-08-03), a classe que mais apodrece em rename
- DADO um arquivo com seção de versão lançada no padrão Keep a Changelog (`## [X.Y.Z]`) QUANDO o C3 o varre ENTÃO ele para na **primeira** dessas seções — release publicado é histórico imutável, a mesma razão que já mantém `_archive/` e ADRs fora; a seção `[Não lançado]`, que vem antes, continua verificada, e foi nela que estava o link quebrado real que motivou a delta-027
- DADO um link markdown dentro de crase simples (`` `[x](y.md)` ``) ou de bloco cercado por ``` QUANDO o C3 varre a linha ENTÃO ele o ignora — é sintaxe citada, não referência; sem isso, todo documento que **documenta** como escrever link é acusado por citá-lo, e a evidência é o `docs/CLAUDE.md` do `imex-travelplanner`, com 4 exemplos literais (medição de 2026-08-03)
- DADO o recorte por seção QUANDO ele decide se aplica ENTÃO olha o **conteúdo** do arquivo, não o nome — repo que chame o changelog de outro jeito recebe a mesma proteção, e arquivo sem seção lançada é varrido inteiro, como hoje

### R3 — MUDA R31 (delta-013): inventário de skills validado mecanicamente no CI
- DADO os manifestos `.claude-plugin/plugin.json` e `.claude-plugin/marketplace.json` QUANDO o job `ci` roda ENTÃO um step compara cada diretório `skills/<nome>/` com as descrições dos dois manifestos (case-insensitive, conforme lição de 2026-07-20) e falha nomeando a skill ausente e o manifesto omisso
- DADO os dois manifestos citando todas as skills existentes (10 na medição de 2026-08-04) QUANDO o check roda ENTÃO passa sem achado

## Fora de escopo
- **Check que recalcula o número** — renúncia por decisão do usuário (2026-08-04): cada medição é um comando ad-hoc de época; o check exigiria versionar a receita junto de cada número, mecanismo caro para as 5 ocorrências vivas (4 no R13, 1 no R31 — esta com o inventário de skills já recalculado pelo CI, que valida a realidade sem tocar o número do TRUTH). Se a disciplina de escrita falhar repetidamente, o DT reabre com essa opção.
- **Registros de época** (CHANGELOG lançado, `specs/_archive/**`, ADRs `Accepted`, itens quitados do `DEBT.md`): números lá permanecem como estão — histórico imutável (R47), não recebe data retroativa.
- **Número defasado fora de cenário do TRUTH** (HANDOFF, README, prosa de skill): doc viva de janela rolante, corrigida no uso — o problema do DT-029 é específico da consolidação mecânica.
- Números em **tempo passado** que narram um estado histórico (ex.: "o template declarava `1`", R12) não são afirmação de estado corrente — já são registro de época dentro do cenário e ficam como estão.

## Dependências e riscos
- A regra depende de disciplina de escrita: sem check mecânico (renúncia acima), a rede que resta é o review de spec/archive — mesmo perímetro dos checks 3 e 5 do analyze, que são juízo por design (ADR-0006).
- Varredura de 2026-08-04 no TRUTH vigente: as ocorrências de número medido sem data são as 4 do R13 e a contagem de skills do R31 — os três MUDA desta delta cobrem todas. Valores normativos (limiares do RNF1, espelhos do RNF6, pins do R34) não são medição e ficam fora por definição da regra.
