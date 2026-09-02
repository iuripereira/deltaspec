# ADR-0041: A entrada de CHANGELOG nasce como fragmento por PR, e o perfil do repo é a fase

- **Status:** Accepted
- **Data:** 2026-08-31
- **Supersedes:** —
- **Superseded by:** —

## Context

A [ADR-0035](ADR-0035-changelog-lancado-e-projecao-reescrevivel.md) fixou a **forma** da entrada — uma frase mais a referência do PR — e deixou duas coisas de fora, uma delas por escrito: *"a **presença** da entrada continua por disciplina. O gate valida forma, não cobertura"*, declarado fora de escopo na delta-062. A outra nem chegou a ser nomeada: toda PR viva edita o mesmo `## [Não lançado]`, e cada merge faz as demais conflitarem. É reincidência registrada na [LICOES.md](../../debts/LICOES.md) como conflito de squash em PR empilhada.

Em paralelo, o repositório entrega **dois donos do CHANGELOG e não arbitra entre eles**. O módulo `release-triad` de `canonical-rules.md` manda curar a entrada à mão; a skill `projeto-infra` instala release-please no perfil completo. Nenhum documento diz quem manda quando os dois estão no mesmo repo.

A medição de 2026-08-31 em 6 repositórios consumidores mostrou o custo. O template de release-please marca `docs`, `chore`, `ci`, `test`, `style` e `build` como `hidden` — e nesses repos essas categorias são **68% a 88%** dos commits das últimas 60 revisões da `main`. Num deles o gerador produziria **zero** entradas em 60 commits. Sem nada a dizer, o gerador ficou mudo e os humanos passaram a escrever a seção à mão, em prosa longa, violando a ADR-0035 em ~525 bullets. Prova de que o repositório não acredita no gerador para o próprio caso: **ele nunca instalou release-please em si mesmo**, publica pelo `publica-dist.sh` e seu CHANGELOG passa no gate.

A causa é anterior ao release-please. O `detection.md` classifica pela **forma do artefato** e roda no `projeto-init` — exatamente quando um repo de produto se parece ao máximo com um repo de documentação, porque o código ainda não começou. A classificação congela o instante de sinal mais fraco e vale para sempre.

## Decision

- **A PR não edita o `CHANGELOG.md`.** Ela deixa um fragmento `changelog.d/<slug>.<categoria>.md` com uma linha; `montar_changelog.py` colide os fragmentos no `## [Não lançado]` no release e os apaga. Nomes de arquivo distintos = zero conflito entre PRs vivas.
- **A forma da entrada não muda** — esta ADR **não** supersede a 0035. O fragmento é validado pelo mesmo `check_changelog.checar()`, então C1/C2/C3 valem para ele sem uma linha de regra duplicada, e `LIMITE_CHARS` segue com dono único.
- **O perfil do repositório é a FASE, não a categoria.** `especificação` (o repo ainda não publica release nenhum) não recebe release-please; `implementação` recebe, e só para versão e tag. A promoção é avisada pelo **C18** e aplicada pelo usuário; não há despromoção automática.
- **A fase governa o release-please, não a topologia de branch.** A `develop` existe nas duas: ela é o ambiente de homologação, e isso independe de haver código de produto.
- **"Já publica release" se lê do repositório, não de um arquivo declarado**: presença de `.release-please-config.json` **ou** de qualquer tag. Estado declarado diverge do real; estado lido não pode.
- **Um dono do CHANGELOG por fase**, escrito no `release-triad`. Nunca dois escrevendo.
- **`changelog.d/` fica fora do allowlist do `publica-dist.sh`**: fragmento é efêmero e some no release; o repositório derivado recebe o `CHANGELOG.md` já montado.

## Alternativas renunciadas

1. **Derivar do commit** (release-please, semantic-release, git-cliff). Zero trabalho humano, e é a prática dominante em produto de software com CI/CD. Recusada porque produz vazio na fase de especificação e exigiria **trocar de ferramenta na promoção** — o mecanismo precisa atravessar a transição sem troca.
2. **Criar uma categoria fixa "documentação versionada"** na matriz, em vez de fase. Recusada porque arquivaria errado os repos com código congelado hoje e os que entram em implementação em semanas: seria congelar uma fase como categoria.
3. **Declarar a fase num arquivo** (`fase:` em `doc-profile.yaml` ou manifesto novo). Recusada porque estado declarado diverge do real e ninguém percebe; a presença do release-please e das tags já **é** a fase, e não pode mentir.
4. **Congelar o passivo** e aplicar a forma só daqui em diante. Recusada pelo motivo que a ADR-0035 já escreveu: produz um arquivo com duas gramáticas, e a inconsistência custa mais na leitura do que a reescrita custa uma vez.
5. **Tirar a `develop` na fase de especificação**, o que dissolveria na origem a divergência de ancestralidade que o squash produz. Recusada porque a `develop` não é artefato de release: é o ambiente onde o dono homologa antes do merge. Some com ela e some o gate humano.
6. **Gate de presença junto** — reprovar PR que muda comportamento e não deixa fragmento. Recusada por escopo: medir cobertura exige ler o diff e é outra conta.

## Consequences

- \+ O conflito de `CHANGELOG.md` entre PRs vivas some por construção, e com ele uma reincidência da `LICOES.md`.
- \+ `check_changelog.py` e o montador têm **um** dono para `LIMITE_CHARS` e `CATEGORIAS`; o fragmento não trouxe gramática nova.
- \+ A ambiguidade "quem escreve o CHANGELOG" deixa de ser decisão por repositório e passa a ser regra canônica com fase declarada.
- \+ O C18 mecaniza um passo que antes dependia de alguém lembrar — mesma linha da decisão "se reincidir, mecanizar" registrada na `LICOES.md`.
- − A **cobertura** segue fora de escopo: PR que muda comportamento e não deixa fragmento continua passando. Mesma declaração da ADR-0035, repetida aqui de propósito para não se perder de novo.
- − Fragmento sem `(#NNN)` no momento do commit é o estado **normal** — o número só existe depois de abrir a PR —, e `--preencher-pr` vira um passo a mais no fluxo. O comando roda antes da validação justamente por isso; validar primeiro trancava o único comando capaz de resolver.
- − O C18 depende de uma lista de negação de prefixos de ferramenta (`scripts/`, `docs/`, `.claude/`, …). Produto em caminho imprevisto dispara o aviso, que é o lado seguro; ferramenta nova sai da lista com uma linha.
