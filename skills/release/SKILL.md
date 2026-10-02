---
name: release
description: Use when the release (or hotfix) PR against main is green and it is time to publish, or when a previous publication stopped halfway — merges it by merge commit, creates the tag + GitHub Release from the CHANGELOG section, dispatches the deploy declared in doc-profile.yaml, syncs main back into develop through sync/X.Y.Z with a CHANGELOG guard and verifies main ⊆ develop; on the framework itself it also runs publica-dist.sh. Resumable by state — each step checks whether it is already done and moves on. Triggers include "/deltaspec:release", "publicar a release", "lançar a versão", "mergear a PR de release", "cortar a tag", "fazer o sync main→develop", "rodar o deploy da tag", "retomar a release". Needs gh CLI authenticated. Not for cutting the release branch — that is /deltaspec:criar-release.
disable-model-invocation: true
---

# release

## Overview

Publica a versão que `/deltaspec:criar-release X.Y.Z` cortou: **sem argumento** — a versão vem do nome da branch da PR (`release/X.Y.Z` ou `hotfix/X.Y.Z`), conferido com o primeiro `## [X.Y.Z]` do CHANGELOG da `main` depois do merge; nunca de quem digita. O humano decide só o momento; a skill executa em sequência fixa, com os scripts do plugin rodando **local** (`${CLAUDE_PLUGIN_ROOT}`), sem Python no runner e sem workflow criando tag. Tag e Release nascem juntas numa chamada do `gh`. Efeito colateral externo em cada passo — por isso `disable-model-invocation: true`: só o dono invoca, e o merge é autorizado porque ele invocou.

**Retomada pelo estado:** a skill não lembra onde parou — ela olha. Cada passo confere se já foi feito (PR mergeada, tag, Release, run de deploy com sucesso, sync, derivado) e segue para o primeiro que falta. Tag existente não encerra a rodada; rodar duas vezes nunca duplica.

**Não troca a branch da sessão.** `git switch main` falha quando a `main` está presa noutro worktree, que é o arranjo que o CLAUDE.md prescreve para checkout compartilhado. A skill lê `origin/*` depois de `git fetch`, e a árvore de que a sync precisa é um worktree temporário.

## Pré-requisitos (verificar antes de qualquer passo)

```bash
gh auth status && gh repo view --json nameWithOwner --jq .nameWithOwner
git fetch --prune --tags origin
T="$(mktemp -d)"                                   # nunca "$TMPDIR/…": vem vazio fora do sandbox
git show origin/main:CHANGELOG.md > "$T/cl-main.md"
```

- `gh` sem autenticação ou sem remote → **pare e reporte**.
- **Topologia**, que decide os passos (b), (e) e (f): `git rev-parse -q --verify origin/develop` → existe = perfil `completo`, com `develop` (release por **merge commit**, sync obrigatória); ausente = perfil `mínimo` (release por **squash**, sem sync). O próprio framework é o segundo caso.
- **Deploy declarado:** leitura explícita de `release.deploy` no `doc-profile.yaml` da `origin/main`. Arquivo ou chave ausente = sem deploy, com aviso; erro de leitura (PyYAML faltando, YAML inválido, `release:` que não é mapa) = **pare** — um deploy declarado que não foi lido não pode virar "sem deploy".

```bash
if git cat-file -e origin/main:doc-profile.yaml 2>/dev/null; then
  git show origin/main:doc-profile.yaml > "$T/doc-profile.yaml"
  WF="$(python3 -c 'import sys, yaml
d = yaml.safe_load(open(sys.argv[1])) or {}
print((d.get("release") or {}).get("deploy") or "")' "$T/doc-profile.yaml")" \
    || { echo "erro lendo release.deploy do doc-profile.yaml — pare"; exit 1; }
  [ -n "$WF" ] || echo "aviso: doc-profile.yaml sem release.deploy — sem deploy automático"
else
  WF=""; echo "aviso: sem doc-profile.yaml na main — sem deploy automático"
fi
```

## Processo

### (a) Localizar o que publicar

```bash
gh pr list --base main --state open --json number,headRefName \
  --jq '.[] | select(.headRefName | test("^(release|hotfix)/")) | "\(.number) \(.headRefName)"'
```

- Uma → é ela.
- Duas (uma `release/*` e uma `hotfix/*`) → **regra de ordem: o hotfix entra primeiro.** Publique o hotfix por este processo inteiro (inclusive a sync) e só depois volte à `release/*`, que antes precisa receber a `main` por `git merge origin/main` na própria branch — nunca rebase: o `non_fast_forward` do ruleset `release-hotfix` recusa o push forçado que o rebase exige (que ele também barre o "Update with rebase" da UI está **a provar no piloto**). Duas do mesmo tipo é erro de processo: pare e pergunte qual.
- Nenhuma aberta → **retomada**: a última PR mergeada de release/hotfix.

```bash
gh pr list --base main --state merged --limit 20 --json number,headRefName,mergedAt \
  --jq '[.[] | select(.headRefName | test("^(release|hotfix)/"))] | sort_by(.mergedAt) | last // empty | "\(.number) \(.headRefName)"'
```

  Ela está pendente se falta qualquer um dos passos abaixo: tag `v$V`, Release, run de deploy com sucesso (quando `WF` foi declarado), sync (com `develop`: `git merge-base --is-ancestor origin/main origin/develop` falso) ou derivado (só no framework). Nada falta, ou nenhuma PR → **pare**: "nada a lançar — corte com `/deltaspec:criar-release X.Y.Z`".

Daqui em diante: `N=<número>`, `HEAD_REF=<headRefName>`, `V="${HEAD_REF#*/}"`.

### (b) Checks e merge

`gh pr view "$N" --json state --jq .state` já `MERGED` → pule direto para o `SHA`. `OPEN` → `gh pr checks "$N"`: qualquer check vermelho ou pendente → **pare e relate** o nome do check. Não mergeie "para adiantar": o `release-check` é a defesa em profundidade da `criar-release`, e é ele quem pega PR aberta à mão.

```bash
gh pr merge "$N" --merge      # com develop: o ruleset da main só aceita merge commit
gh pr merge "$N" --squash     # sem develop (perfil mínimo, o próprio framework)
git push origin --delete "$HEAD_REF" 2>/dev/null || echo "$HEAD_REF já não existe no remoto"
SHA="$(gh pr view "$N" --json mergeCommit --jq .mergeCommit.oid)"
git fetch --prune --tags origin && git show origin/main:CHANGELOG.md > "$T/cl-main.md"
```

Sem `--delete-branch` no merge: com a sessão parada na própria `release/X.Y.Z`, o `gh` tenta trocar para a `main` depois de mergear, falha num worktree e sai com erro com o merge já feito. A branch remota sai à parte; a local, se houver, fica para a higiene pós-merge.

### (c) Tag e Release

```bash
[ "$(grep -m1 -oE '^## \[[0-9]+\.[0-9]+\.[0-9]+\]' "$T/cl-main.md" | tr -d '#[] ')" = "$V" ] \
  || { echo "o primeiro ## [X.Y.Z] do CHANGELOG da main não é $V — pare"; exit 1; }
python3 "${CLAUDE_PLUGIN_ROOT}/skills/release/scripts/secao_changelog.py" "$V" --changelog "$T/cl-main.md" > "$T/notas.md" \
  && grep -q '^- ' "$T/notas.md" || { echo "seção ## [$V] ausente ou sem bullet no CHANGELOG da main — pare"; exit 1; }
TAG_SHA="$(git rev-parse -q --verify "refs/tags/v$V^{commit}")"
if [ -z "$TAG_SHA" ]; then
  gh release create "v$V" --target "$SHA" --title "v$V" --notes-file "$T/notas.md"
elif [ "$TAG_SHA" != "$SHA" ]; then
  echo "tag v$V aponta para $TAG_SHA, não para o merge $SHA — pare"; exit 1
elif ! gh release view "v$V" >/dev/null 2>&1; then
  gh release create "v$V" --verify-tag --title "v$V" --notes-file "$T/notas.md"
else
  echo "tag e Release v$V já existem — segue"
fi
git fetch --tags origin
```

- Seção ausente (exit 1 do script), vazia ou só com cabeçalhos `### ` → **pare antes do `gh`**: a Release não nasce com notas vazias.
- Tag no SHA do merge é passo feito, não fim de rodada: a skill segue para (d)–(g). Tag em outro SHA é o único caso de parada.
- `--target <sha do merge>` cria a tag e a Release numa chamada, sem `git tag -a` nem push de tag da sessão. Que a tag criada assim seja **leve** está **a provar no piloto**. O `git fetch --tags` traz a tag para o disco — o `publica-dist.sh` a exige local (passo g).
- **A tag dispara `on: push: tags`.** Ela nasce com o token do humano, e só push/tag feitos com o `GITHUB_TOKEN` deixam de disparar workflow. O workflow de `release.deploy` não pode ouvir `push: tags` além do `workflow_dispatch`, ou o deploy roda duas vezes — uma pela tag, outra pelo passo (d).

### (d) Deploy pela tag — só com `WF`

Antes de despachar, confira que o workflow não ouve a tag por conta própria. A tag nasce com o token do humano e dispara `on: push`; se o workflow também a ouvir, o deploy roda duas vezes.

```bash
git show "origin/main:.github/workflows/$WF" > "$T/wf.yml" || { echo "workflow $WF ausente na main — pare"; exit 1; }
python3 -c 'import sys, yaml
d = yaml.safe_load(open(sys.argv[1])) or {}
on = d.get("on", d.get(True))                 # YAML 1.1 lê a chave "on" como True
on = {on: None} if isinstance(on, str) else ({e: None for e in on} if isinstance(on, list) else (on or {}))
p = on.get("push", "ausente")
tag = p is None or (isinstance(p, dict) and ("tags" in p or "tags-ignore" in p or not {"branches", "branches-ignore"} & set(p)))
ruim = (["push (inclui tags)"] if tag else []) + (["release"] if "release" in on else [])
sys.exit("o deploy também ouve " + ", ".join(ruim) + " além do dispatch — rodaria duas vezes; pare" if ruim else 0)' "$T/wf.yml"
```

```bash
FEITO="$(gh run list --workflow "$WF" --event workflow_dispatch --branch "v$V" --status success \
  --limit 1 --json databaseId --jq '.[0].databaseId // empty')"
if [ -n "$FEITO" ]; then
  echo "deploy de v$V já feito (run $FEITO)"
else
  SAIDA="$(gh workflow run "$WF" --ref "v$V" -f dry_run=false)"
  ID="$(printf '%s\n' "$SAIDA" | grep -oE '/actions/runs/[0-9]+' | tail -n1 | grep -oE '[0-9]+$')"
fi
```

- A run vem da URL que o próprio dispatch devolve — nunca de `gh run list --limit 1`, que pega a run anterior ou uma concorrente e relata o destino de outro deploy. Sem URL (servidor que responde ao dispatch sem corpo): `gh run list --workflow "$WF" --event workflow_dispatch --branch "v$V" --limit 5 --json databaseId,createdAt` e use a run criada depois do dispatch; se ainda não apareceu, liste de novo em alguns segundos. Nunca adivinhe.
- `gh run watch "$ID" --exit-status` → vermelho: **pare e relate** (rodar a skill de novo redespacha; rollback abaixo). Verde: `gh run view "$ID" --log | grep -i destino` e **relate a linha de destino**.
- O filtro `--branch "v$V"` casando a run disparada numa tag e o `dry_run=false` chegando ao input como o workflow espera estão **a provar no piloto**.
- O contrato do workflow apontado é do consumidor (`workflow_dispatch` com input `dry_run`, aceita `--ref` de tag, imprime no log a linha com o destino); o framework só lê o nome do arquivo em `release.deploy`. `WF` vazio = sem deploy automático; tag e Release continuam.

### (e) Sync `main → develop` — só com develop, sempre por `sync/X.Y.Z`

`git merge-base --is-ancestor origin/main origin/develop` verdadeiro → sync já feita, no-op. PR `sync/$V` já aberta (`gh pr list --base develop --head "sync/$V" --state open --json number --jq '.[0].number // empty'`) → é ela: pule para os checks.

Nunca a PR `main → develop` crua: o merge **limpo** do CHANGELOG é justamente o que empurra bullet não lançado para baixo de `## [X.Y.Z]`, e nada no GitHub o recusa.

```bash
git show origin/develop:CHANGELOG.md > "$T/cl-develop.md"          # o [Não lançado] de antes
git worktree add -B "sync/$V" "$T/sync" origin/develop              # árvore temporária; a da sessão não muda
git -C "$T/sync" merge --no-ff --no-commit origin/main              # 0 = limpo · 1 = conflito
```

- Conflito fora do `CHANGELOG.md` → **pare e relate**: resolução de código é do humano. No CHANGELOG, resolva pela regra única: **bullet que caiu sob `## [X.Y.Z]` mas não foi lançado volta ao `## [Não lançado]`** — o lançado é o que está na seção da `main`.
- **Sempre**, com ou sem conflito, confira por conjunto antes de commitar:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/release/scripts/secao_changelog.py" --sync "$V" \
  --antes "$T/cl-develop.md" --main "$T/cl-main.md" --depois "$T/sync/CHANGELOG.md"
```

  Exit 1 lista cada bullet **perdido** (estava no `[Não lançado]` da develop e não está nem no `[Não lançado]` do resultado nem na `## [$V]` da main), cada um **fora do lançado** (está na `## [$V]` do resultado e não na da main) e marcador de conflito que sobrou. Os bullets voltam ao `[Não lançado]` em `$T/sync/CHANGELOG.md`; rode de novo até sair 0. Nunca apague bullet para passar.

```bash
git -C "$T/sync" add CHANGELOG.md && git -C "$T/sync" commit -m "chore(sync): v$V"
git -C "$T/sync" push -u origin "sync/$V" && git worktree remove "$T/sync"
N_SYNC="$(gh pr create --base develop --head "sync/$V" --title "chore(sync): v$V" \
  --body "Sync pós-release: main ⊆ develop (ADR-0045)." | grep -oE '[0-9]+$')"
gh pr checks "$N_SYNC" --watch && gh pr merge "$N_SYNC" --merge   # merge commit: o único que mantém main ⊆ develop
git push origin --delete "sync/$V" 2>/dev/null; git branch -D "sync/$V" 2>/dev/null
```

- O merge só vem **depois** dos checks — o `ci` é exigido pelo `develop.json`, e o `sync-check` repete a conferência por conjunto na PR: vermelho ali é bullet perdido, não ruído. Check vermelho → **pare e relate**. "no checks reported" logo depois do `pr create` é check que ainda não registrou: rode o `gh pr checks` de novo em alguns segundos.
- Com uma `release/*` aberta (o hotfix entrou primeiro), a sync não re-dispara o `release-check` dela. Quem atualizar a release com `git merge origin/main` dispara de novo; se ninguém atualizar, re-rode o check da PR da release depois da sync.
- `sync/$V` presa num worktree de rodada anterior faz o `worktree add -B` falhar: `git worktree list` mostra o caminho, e `git worktree remove --force <caminho>` o libera.

### (f) Invariante — só com develop

```bash
git fetch origin
git merge-base --is-ancestor origin/main origin/develop && echo "main ⊆ develop: ok"
git rev-list --count --no-merges origin/main..origin/develop   # informativo
```

- `is-ancestor` falso → **pare e relate**: a sync não entrou. Não corrija à mão.
- A contagem é trabalho da `develop` ainda não lançado — no hotfix ela é maior que zero sempre que a `develop` andou. Relate o número; nunca pare por ele.

### (g) Derivado público — só no framework

Só onde `scripts/publica-dist.sh` existe (o repositório do deltaspec). `gh release view "v$V" --repo <dono>/<repo-publico>` já responde → derivado publicado, pule.

```bash
export DELTASPEC_REMOTE_PUBLICO=git@github.com:<dono>/<repo-publico>.git
scripts/publica-dist.sh --dry-run "v$V"   # árvore, gate de confidencialidade, integridade — nada enviado
scripts/publica-dist.sh "v$V"             # commit órfão, tag, Release no derivado
```

O script exige a tag local (por isso o `git fetch --tags` do passo c) e recusa alvo igual ao `origin`. Falha de assinatura SSH → o diagnóstico é do próprio script; não troque a chave.

### Relatório final

Liste: PR mergeada (número, método) ou "já mergeada" · tag + Release (`gh release view v$V --json url`) · deploy (workflow, run, linha de destino), "já feito (run N)" ou "sem deploy declarado" · sync (PR, conflito resolvido ou não, bullets devolvidos ao `[Não lançado]`) · invariante (`is-ancestor` e a contagem informativa) · derivado (publicado ou "não é o framework"). Na retomada, diga de que passo a rodada partiu.

## Rollback — fora da skill

Gatilho: o deploy da tag quebrou em produção. Um comando, sem reverter tag nem Release (história publicada não se reescreve):

```bash
gh workflow run <workflow de release.deploy> --ref v<anterior> -f dry_run=false
```

Vale para tags posteriores à adoção do contrato de deploy pelo consumidor. Quando reincidir, é candidato a `/deltaspec:release --rollback v<anterior>`.

## Erros comuns

| Erro | Correto |
|---|---|
| Passar a versão como argumento | A versão é o nome da branch da PR, conferido com o CHANGELOG da `main`; quem decide é a `criar-release` |
| `gh pr merge --squash` com develop | Merge commit — squash quebra `main ⊆ develop` e o ruleset recusa |
| `git switch main` na sessão | Falha num worktree; leia `git show origin/main:CHANGELOG.md` e use worktree temporário para a sync |
| `git tag -a` + `git push --tags` na sessão | `gh release create --target <sha>` cria tag e Release juntas; a sessão só faz `git fetch --tags` |
| Encerrar porque a tag já existe | Tag no SHA do merge é passo feito: siga para deploy, sync e invariante |
| Mergear com check pendente "porque é só o commits" | Vermelho ou pendente = parar; `release-check` existe para isso |
| Pegar a run do deploy com `gh run list --limit 1` | O id vem da URL que o `gh workflow run` devolve |
| Publicar a `release/*` com um `hotfix/*` aberto | Hotfix primeiro; depois `git merge origin/main` na `release/*` (nunca rebase) |
| Mergear a PR `main → develop` porque o merge saiu limpo | Merge limpo é o que empurra bullet não lançado para baixo da versão; sempre `sync/X.Y.Z` + `--sync` |
| Resolver o CHANGELOG da sync apagando bullets | O `--sync` lista perdido e fora do lançado; os dois voltam ao `[Não lançado]` |
| Mergear a PR de sync logo depois de criá-la | `gh pr checks --watch` primeiro; o `ci` é exigido e o `sync-check` é a segunda conferência |
| Parar porque `main..develop` > 0 | A contagem é informativa; só o `is-ancestor` falso para |
| Temporário em `"$TMPDIR/…"` | `T="$(mktemp -d)"` nos pré-requisitos |
| `publica-dist.sh` antes do `git fetch --tags` | O script lê a tag local e recusa sem ela |
| Rodar `publica-dist.sh` num repo consumidor | Passo (g) é só do framework; consumidor não tem derivado |

## Arquivos da skill

- `scripts/secao_changelog.py` — recorte de `## [rótulo]` do CHANGELOG sem comentários HTML (função pura `secao()`), `bullets()`, `conferir_sync()` com `--sync` (a guarda por conjunto do passo e) e `--selftest`; dono do recorte que alimenta `--notes-file`. A `conferir_sync()` tem gêmeo em awk no `sync-check.yml` do `projeto-infra` — mudou um, mude o outro.
