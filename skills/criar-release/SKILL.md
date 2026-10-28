---
name: criar-release
description: Use when cutting a release (or a hotfix) in a project that follows the deltaspec release flow — the human decides only the version; the skill validates it against the last tag and the commits since it (immediate SemVer successor, bump paid, PATCH for hotfix), runs the pre-flight (clean tree, no other release/hotfix PR open against main, previous main→develop sync merged, CHANGELOG of the cut base with unreleased bullets or changelog.d fragments), creates release/X.Y.Z from origin/develop (main when the repo has no develop), releases the CHANGELOG section, commits the release with explicit paths (never git add -A), opens the PR to main and watches the checks. A hotfix runs in two phases — the first call creates hotfix/X.Y.Z from origin/main and stops for the fix, the second cuts it. Tag, Release and deploy belong to /deltaspec:release, after the merge. Triggers include "/deltaspec:criar-release", "cortar a release", "cortar a versão", "abrir a PR de release", "preparar o release X.Y.Z", "hotfix X.Y.Z", "fechar a versão".
argument-hint: "<X.Y.Z> [--hotfix]"
disable-model-invocation: true
---

# criar-release

## Visão geral

Corta uma release **sem receita à mão**: o humano decide a versão e invoca `/deltaspec:criar-release X.Y.Z`; a skill valida, cria a branch de release a partir da `develop`, libera o `## [Não lançado]` do CHANGELOG como `## [X.Y.Z]`, abre a PR para a `main` e acompanha os checks. Tag, Release do GitHub, deploy e a volta `main→develop` **não são daqui** — são de `/deltaspec:release`, depois do merge. Decisão, renúncias e o porquê da branch dedicada (a PR `develop→main` republicava dezenas de commits a cada corte num repo consumidor): ADR-0045 (`../../docs/adrs/ADR-0045-release-por-skills-do-plugin-e-merge-commit-na-main.md`).

**Efeito externo:** cria branch, faz push e abre PR no remoto — por isso `disable-model-invocation: true`: só roda quando o humano invoca. Nada aqui mergeia, taggeia nem publica.

**Interface:** um argumento, a versão (`X.Y.Z`, sem `v`). `--hotfix` corta da `main` em vez da `develop`, em **duas fases**: a primeira chamada cria `hotfix/X.Y.Z` e para, esperando o conserto; a segunda, com o conserto commitado na branch, faz o corte.

## Topologia — de onde se corta e como a PR entra

| Situação | Origem do corte | Branch | Merge da PR |
|---|---|---|---|
| Repo com `develop` (padrão) | `origin/develop` | `release/X.Y.Z` | merge commit (ruleset da `main` recusa squash) |
| `--hotfix` | `origin/main` | `hotfix/X.Y.Z` | merge commit |
| Repo sem `develop` (o próprio deltaspec) | `origin/main` | `release/X.Y.Z` | squash |

Detecção do perfil: `git ls-remote --exit-code --heads origin develop` — sem saída, é perfil sem `develop`: base `origin/main`, e a PR entra por squash. **Com `release/*` aberta, o hotfix entra primeiro;** depois, a release recebe a `main` por `git merge origin/main` na própria branch — **nunca rebase**: o ruleset de `release/**` (`non_fast_forward`) recusa o force-push que o rebase exige; que ele barre também o "Update with rebase" da UI é **a provar no piloto**. **A sync não re-dispara o `release-check` da `release/*` aberta:** a PR `sync/X.Y.Z` do hotfix não gera evento nela, e o check vermelho por "sync pendente" fica vermelho — quem atualizar a release (`git merge origin/main`, push) faça isso depois da sync, ou re-rode o `release-check` dela.

## Processo (na ordem — reprovou, para; não contorna)

1. **Pré-voo.** Nada escrito ainda. `git fetch --prune --tags origin` primeiro.
   - **Árvore limpa:** `git status --porcelain` vazio. Não vazio → pare: "árvore suja — commite, guarde ou descarte antes de cortar; o commit do corte leva só o CHANGELOG e o `changelog.d/`".
   - **Base do corte** (`BASE`): `origin/develop` no padrão, `origin/main` no perfil sem `develop`. Com `--hotfix`, a fase decide — `git rev-parse -q --verify refs/heads/hotfix/X.Y.Z || git rev-parse -q --verify refs/remotes/origin/hotfix/X.Y.Z`:
     - **fase 1** (a branch não existe): `BASE=origin/main`; os itens abaixo rodam, menos "há o que lançar" (a `[Não lançado]` da `main` está vazia por construção depois de cada release) — e o passo 2 para depois de criar a branch;
     - **fase 2** (a branch existe): `git switch hotfix/X.Y.Z` (cria a local a partir da remota, se só houver ela); `git rev-list --count origin/main..hotfix/X.Y.Z` tem de ser > 0 — zero → pare: "`hotfix/X.Y.Z` ainda sem conserto — commite o conserto e o bullet nela e rode de novo"; `BASE=hotfix/X.Y.Z`.
   - **Versão:** `python3 ${CLAUDE_PLUGIN_ROOT}/skills/criar-release/scripts/versao_corte.py X.Y.Z --base "$BASE"` (mais `--hotfix` no hotfix). Sai **1** quando a pedida não é maior que a última tag, não é o **sucessor imediato** dela no nível do bump (`X.Y.(Z+1)`, `X.(Y+1).0`, `(X+1).0.0` — sem pular número), não paga o bump que os commits exigem (`feat` → MINOR; `!`/`BREAKING CHANGE` → MAJOR, MINOR em `0.y.z`; a mensagem cita o subject responsável) ou, com `--hotfix`, não é PATCH. Sai **2** em uso inválido (versão fora do SemVer, ref inexistente). Repo sem tag aceita qualquer SemVer (menos no hotfix). A saída diz quantos commits entraram na conta e avisa tag ignorada (fora de `vX.Y.Z`, ou pré-release).
   - **Outro corte em curso:** `gh pr list --base main --state open --json headRefName --jq '.[] | select(.headRefName | test("^(release|hotfix)/")) | .headRefName'`. PR de escopo não conta — no perfil sem `develop` ela é o normal. Sem `--hotfix`: qualquer linha → pare ("corte em curso: `<head>` — publique-o com `/deltaspec:release` antes"). Com `--hotfix`: `hotfix/*` → pare; só `release/*` → siga e avise: "o hotfix entra primeiro; depois a `<release>` recebe a `main` por `git merge origin/main` na própria branch, nunca rebase".
   - **Sync anterior concluído** (só perfil com `develop`, e não no `--hotfix` — o `release-check` também só o cobra de `release/*`): `git merge-base --is-ancestor origin/main origin/develop`. Falso → pare e diga: "sync `main→develop` pendente — rode `/deltaspec:release` de novo (ela retoma a sync pela `sync/X.Y.Z`) antes de cortar".
   - **Há o que lançar — lido da base, não do disco** (a sessão pode estar em outra branch): `git show "$BASE:CHANGELOG.md" | awk '/^## \[Não lançado\]/{f=1;next} /^## \[/{f=0} f&&/^- /{n++} END{exit n==0}'` (bullet no `[Não lançado]`) **ou** `git ls-tree --name-only "$BASE" changelog.d/ | grep -qE '^changelog\.d/[^/]+\.[a-z]+\.md$'` (fragmento; `README.md` e `.gitkeep` não casam). Os dois falham → pare: release sem entrada é release vazia, e o `check_changelog.py` reprova a seção `## [X.Y.Z]` sem bullet.
2. **Cortar.** `git switch -c release/X.Y.Z "$BASE"`. No hotfix, **fase 1**: `git switch -c hotfix/X.Y.Z origin/main` e **pare aqui**, dizendo: "`hotfix/X.Y.Z` criada da `main`. Commite o conserto nela (Conventional Commits `fix`) com o bullet em `## [Não lançado]` → `### Corrigido` (ou o fragmento `changelog.d/<slug>.corrigido.md`) e rode `/deltaspec:criar-release X.Y.Z --hotfix` de novo." Na **fase 2** a branch já é a corrente (passo 1) — siga.
3. **Liberar o CHANGELOG.** `python3 ${CLAUDE_PLUGIN_ROOT}/skills/spec-feature/scripts/montar_changelog.py` (acrescenta os fragmentos ao `[Não lançado]` — mescla: o bullet que já está lá fica — e os apaga; sem `changelog.d/` sai 0 com "nada a montar" — não ponha guarda de diretório na frente, `[ -d changelog.d ] && …` sai 1 no repo que não o tem); depois `python3 ${CLAUDE_PLUGIN_ROOT}/skills/spec-feature/scripts/montar_changelog.py --liberar X.Y.Z` — renomeia a seção para `## [X.Y.Z] - AAAA-MM-DD`, abre um `[Não lançado]` vazio, escreve o rodapé de comparação e valida o resultado com o `check_changelog.py`; sai 1 com `[Não lançado]` vazio ou versão ≤ a última lançada no CHANGELOG, e 2 com versão fora do SemVer. Manifesto de versão (`plugin.json`, `package.json`, `pyproject.toml`) entra **no mesmo commit** quando o repo o espelha da tag — a regra do repo (CLAUDE.md, tríade de release) diz qual.
4. **Commit, push, PR.** Caminhos explícitos, nunca `git add -A`: `git add -- CHANGELOG.md $(git ls-files -- changelog.d)` (mais o caminho do manifesto, se o repo o espelha) — o `ls-files` pega a remoção dos fragmentos e é vazio no repo sem `changelog.d/`. Confira `git diff --cached --name-only` (só esses caminhos) e então `git commit -m 'chore(release): X.Y.Z'` · `git push -u origin <branch>` · `VINCULO="$(python3 ${CLAUDE_PLUGIN_ROOT}/skills/handoff/scripts/debito.py vinculo . --base origin/main --head HEAD --branch "$(git branch --show-current)")"` — as linhas de vínculo dos DTs quitados que a PR leva para a `main`, o mesmo intervalo que o `ci` confere; na `release/*` saem só os `Closes #N` (a chave do Jira já vinculou na PR que quitou o DT), e no hotfix a linha sem `Closes` é chave do Jira e vai no **título** da PR (`chore(release): X.Y.Z (PROJ-12)`), porque o Jira não lê o corpo · `CORPO="$(mktemp -d)/corpo-pr.md"` · `gh pr create --base main --title 'chore(release): X.Y.Z' --body-file "$CORPO"`. Corpo padrão — sem link relativo: ele resolve contra a URL da PR e quebra, e o repo consumidor nem tem a ADR:

   ```markdown
   Corte da vX.Y.Z pelo `/deltaspec:criar-release` (fluxo de release da ADR-0045 do deltaspec).

   ## O que entra
   <seção `## [X.Y.Z]` do CHANGELOG, colada íntegra>

   ## Tickets que fecham no merge
   <saída de "$VINCULO", uma linha por item — omita a seção inteira quando vazia>

   ## Depois do merge
   `/deltaspec:release` — tag `vX.Y.Z` + Release, deploy pela tag (se o perfil declarar), sync `main→develop`.

   Merge por **merge commit** (perfil sem `develop`: squash). Modelo: <modelo real> · <XX>% AI / <YY>% Human
   ```

5. **Acompanhar.** Logo depois do `gh pr create` as check suites ainda não existem, e `gh pr checks --watch` sai 1 com `no checks reported` — o mesmo código de check vermelho. Espere os checks aparecerem, com teto, e só então observe:

   ```bash
   N=<número da PR>; TENTATIVAS=12; INTERVALO=10   # teto: 2 min para a primeira check suite
   for _ in $(seq "$TENTATIVAS"); do
     [ "$(gh pr checks "$N" --json name --jq length 2>/dev/null)" -gt 0 ] 2>/dev/null && break
     sleep "$INTERVALO"
   done
   gh pr checks "$N" --watch
   ```

   `no checks reported` depois do teto **não é check vermelho**: é PR com conflito com a `main` (workflow de `pull_request` não roda em PR com conflito) ou repo sem os workflows — relate esse diagnóstico, não procure conserto no código. Com checks, relate o resultado por check (`ci`, `commits`, `release-check` quando o repo o tem). **Vermelho corrige na branch de release** — commit novo, push, checks de novo — nunca à mão na `main`. Verde: entregue ao humano com o número da PR e o próximo passo (`/deltaspec:release`).

## Primeiro corte depois da adoção

Repo que vinha do fluxo antigo (`develop→main` por squash + back-merge) tem a última tag num commit de pai único: os commits da `develop` nunca viraram ancestrais dela, e `tag..develop` ainda lista o que o squash já lançou — num repo consumidor medido, 83 commits, 76 já publicados. O `versao_corte.py` reconhece o caso e começa a conta no **back-merge que trouxe a tag** para a base, com aviso na saída ("primeiro corte depois da adoção; a conta começa no back-merge `<sha>`"). Confira o número de commits que ele diz ter contado. Se ainda sair inflado — por exemplo, a última tag do fluxo antigo foi um hotfix por squash direto na `main` —, force o início com `--desde <sha>` (o ponto da adoção) e registre o motivo no corpo da PR. Corrija o início da conta, não a versão: MAJOR errada vira tag irreversível. Do segundo corte em diante a tag está no merge commit da release e a conta volta a começar nela.

**Última versão do CHANGELOG sem tag bloqueia o corte.** O `release-check` exige tag na versão anterior à que se lança (a primeira `## [A.B.C]` abaixo da nova) e reprova com "versão A.B.C lançada sem tag". Repo que vinha lançando sem tag — ou cuja última release saiu fora das skills — fica bloqueado até `vA.B.C` existir. Se ela saiu por PR `release/*` ou `hotfix/*`, rode `/deltaspec:release` antes de cortar: sem PR aberta, ela retoma a última mergeada que ainda falta tag e cria `vA.B.C` com `--target` no SHA do merge. Versão lançada sem PR de release/hotfix não tem merge que a skill ache — aí a tag vai no commit que a lançou, uma vez, pelo dono do repo. O `versao_corte.py` também reprova: sem ela a última tag é mais antiga, e a versão pedida deixa de ser o sucessor imediato.

## Erros comuns

| Erro | Correto |
|---|---|
| Pedir `vX.Y.Z` (com `v`), `X.Y` ou `1.03.0` | O argumento é `X.Y.Z` SemVer estrito, sem zero à esquerda; o `v` é da tag, e quem a cria é `/deltaspec:release` |
| Pular número (`1.2.3 → 1.4.0`) ou não zerar os inferiores (`1.3.7`) | Só o sucessor imediato passa: `1.2.4`, `1.3.0` ou `2.0.0` |
| Ignorar o exit 1 do `versao_corte.py` e cortar assim mesmo | O bump é decisão humana, mas o gate reprova bump **menor** que o exigido pelos commits — corrija a versão. Exceção nomeada: conta inflada no primeiro corte depois da adoção — ali se corrige o início (`--desde`), ver a seção acima |
| Hotfix MINOR, ou `feat` dentro do hotfix | Hotfix é PATCH: `--hotfix` reprova qualquer outra versão e commit que exija mais |
| Liberar o hotfix logo depois de cortar da `main` | A `[Não lançado]` da `main` está vazia; é a fase 1 — pare, commite o conserto com o bullet, rode de novo |
| Cortar com árvore suja, ou commitar com `git add -A` | Pré-voo exige `git status --porcelain` vazio; o commit leva caminhos explícitos — arquivo solto não pode ir para a `main` no `chore(release)` |
| Recusar o corte por PR de escopo aberta contra a `main` | Só `release/*` ou `hotfix/*` aberta é corte em curso; no perfil sem `develop` a PR de escopo é o normal |
| Cortar com a sync `sync/X.Y.Z` do release anterior pendente | `is-ancestor` falso é o sinal; conclua o sync antes (`/deltaspec:release` de novo retoma) — senão a release nasce sem os commits da release anterior e o CHANGELOG perde bullets na fusão |
| Editar o `## [Não lançado]` à mão para "renomear" a seção | `montar_changelog.py --liberar` é o dono: mantém a contagem de bullets, abre o `[Não lançado]` novo e escreve o rodapé; edição à mão é o que o C4/C5 do `check_changelog.py` pegam |
| Ler `no checks reported` logo depois do `gh pr create` como vermelho | É o intervalo antes da primeira check suite; espere com teto (passo 5). Depois do teto, é conflito ou workflow ausente |
| Corrigir check vermelho direto na `main` | A `main` é protegida e a branch de release é o lugar do conserto; commit novo nela reroda os checks |
| Rebase da `release/*` depois do hotfix, ou "Update with rebase" na UI | O ruleset de `release/**` recusa o force-push (ADR-0045); atualize por `git merge origin/main` na branch |
| Abrir a PR de release sem a seção de tickets | Com `develop`, as palavras de fechamento das PRs de escopo foram ignoradas pelo GitHub; é a PR de release, contra a `main`, que fecha os tickets — e o `ci` reprova sem elas |
| Mergear, taggear ou publicar daqui | Fora do escopo — a skill termina na PR aberta com checks verdes; `/deltaspec:release` faz o resto |
| Rodar em `~/.claude/plugins/marketplaces/` | Diretório efêmero do harness (CLAUDE.md); clone próprio ou `git worktree` |

## Arquivos da skill

- [scripts/versao_corte.py](scripts/versao_corte.py) — gate da versão pedida: SemVer estrito, maior que a última tag, sucessor imediato, bump ≥ exigido pelos commits desde ela, PATCH com `--hotfix`, início da conta no back-merge da adoção ou em `--desde` (`--selftest` com repos git temporários; puras `eh_semver`/`classificar_tags`/`bump_exigido`/`sucessores`/`validar` separadas do I/O do git). `TIPOS_COMMIT` é espelho da regra canônica de Conventional Commits (`deps.toml`, bloco `commit-tipos`).
- `${CLAUDE_PLUGIN_ROOT}/skills/spec-feature/scripts/montar_changelog.py` — não é desta skill; consumido aqui pelo `--liberar X.Y.Z` e pela montagem dos fragmentos.
