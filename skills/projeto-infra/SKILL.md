---
name: projeto-infra
description: Use when setting up or auditing repository infrastructure on GitHub — branch protection rulesets (main, develop, release/hotfix), CI workflows, Conventional Commits enforcement (husky/commitlint), the release-check and sync-check gates of the release flow, CodeRabbit or claude-code-action review. Triggers include "/deltaspec:projeto-infra", "proteger a main", "configurar branch protection", "setup de CI", "automação de release", or the optional infra step offered by projeto-init. Requires gh CLI authenticated and a GitHub remote.
disable-model-invocation: true
---

# projeto-infra

## Overview

Aplica infraestrutura de repositório por **topologia de branch**: rulesets de branch protection, CI, Conventional Commits, os dois gates do fluxo de release (`release-check`, `sync-check`) e review assistido. **Roteiro em markdown — sem scripts instaláveis**; os comandos `gh api`/`git`/`jq` são executados diretamente a partir dos templates em `references/infra/`. **Idempotência defensiva:** consulte o que já existe antes de aplicar cada item; segunda rodada = no-op relatado, nunca duplicação ou sobrescrita.

**O release não mora aqui.** Esta skill deixa o repo pronto; quem corta e publica são `/deltaspec:criar-release` e `/deltaspec:release`, na sessão, com os scripts do plugin ([ADR-0045](../../docs/adrs/ADR-0045-release-por-skills-do-plugin-e-merge-commit-na-main.md)). Nenhum workflow cria tag.

## Pré-requisitos (verificar antes do gate)

- `gh auth status` ok e remote GitHub presente (`gh repo view`). Sem um dos dois → **pare e reporte**; não aplique nada às cegas.
- **Rulesets exigem repo público ou GitHub Pro** (403 em repo privado no plano free). Detecte cedo: `gh api repos/{owner}/{repo}/rulesets` retornou 403 → ofereça ao usuário tornar o repo público, assinar Pro, ou seguir sem proteção (CI continua valendo) — a escolha é dele.
- `jq` instalado — o passo 4 edita rulesets com ele.
- **A branch default é `main`** (`gh repo view --json defaultBranchRef -q .defaultBranchRef.name`). O fluxo nomeia a `main` literalmente — `main.json` protege `refs/heads/main`, o `release-check` filtra `branches: [main]` e as skills leem `origin/main` — e um ruleset antigo com `~DEFAULT_BRANCH` só equivale a isso enquanto a default for `main`. Outra default → **pare e pergunte**; renomear a branch é decisão do dono do repo.
- Invocada avulsa (brownfield) ou pelo `projeto-init` (greenfield) — o processo é o mesmo.

## Processo

1. **Detectar perfil** — classifique o tipo (matriz do `projeto-init/references/detection.md`; na dúvida, pergunte). O que decide o perfil é **a topologia**: o repo tem (ou vai ter) `develop` como homologação, ou não. O tipo só sugere a topologia pela tabela abaixo; a palavra final é do gate (passo 2), e é essa topologia que o passo 4 do roteiro recebe.

| Tipo | Topologia | Perfil | Conteúdo |
|---|---|---|---|
| app-web, backend | **com develop** — `feature/fix → develop`, `release/* → main` | **completo** | rulesets `main` (merge-only, `ci` + `commits` + `release-check`) + `develop` (strict desligado, `ci` + `commits`) + `release-hotfix`; CI + `conventional-commits` + `release-check` + `sync-check`; husky+commitlint (se Node); CodeRabbit + claude-code-action (opcionais) |
| tooling, site-estatico | **sem develop** — `feature/fix → main` por squash, release corta da própria `main` | **mínimo** | ruleset `main` derivado por `jq` (squash, `ci` + `commits`, sem `release-check`); CI + `conventional-commits` |
| workspace-dados | — | **nenhum** | recuse com explicação (não há build/release a proteger) |

**A fase não escolhe o perfil.** O dono do CHANGELOG é o fragmento de `changelog.d/` nas duas fases (módulo `release-triad`), e a tag nasce na skill `release` quando houver o que lançar — repo em especificação simplesmente não corta release. Na topologia com `develop`, ela existe desde o início: é o ambiente de homologação e não depende de haver código de produto.

2. **Gate único** — confirme com o usuário: perfil (override manual é permitido), itens opcionais (CodeRabbit/claude-code-action) e se **review de code owner** será exigido (só faz sentido com 2+ pessoas; solo = PRs obrigatórios com 0 aprovações). Espere o "ok".
3. **Aplicar na ordem do roteiro** — a ordem importa (ver cada passo).
4. **Verificar e reportar** — liste: aplicado · já existia (no-op) · pulado com o porquê.

## Roteiro (ordem de execução)

### 1. CODEOWNERS — só se review de code owner foi exigido no gate
Crie `.github/CODEOWNERS` (`* @{{owner}}`) — se a `git-guard instalar` já deixou o mínimo, edite em vez de recriar — e commite **direto na main, antes de qualquer ruleset** — depois do ruleset o próprio commit do CODEOWNERS ficaria bloqueado. Com a `main` já protegida (brownfield), o commit segue a regra de **onde commitar** do passo 3. Em seguida, troque no `main.json`: `require_code_owner_review: true` e `required_approving_review_count: 1`.

### 2. Branches — perfil completo
`git rev-parse --verify origin/develop` falhou? → `git branch develop main && git push -u origin develop`.

As branches de vida curta do fluxo (`release/X.Y.Z`, `hotfix/X.Y.Z`, `sync/X.Y.Z`) **não se criam aqui** — nascem e morrem nas skills. O que esta skill garante é o chão delas:

- **Rota:** `/deltaspec:criar-release X.Y.Z` corta `release/X.Y.Z` da `develop`, libera o CHANGELOG (`[Não lançado]` → `## [X.Y.Z]`), abre a PR para a `main` e espera os checks; `/deltaspec:release` mergeia por merge commit, cria tag + Release, dispara o deploy pela tag e sincroniza `main→develop`.
- **Hotfix:** `/deltaspec:criar-release X.Y.Z --hotfix` roda duas vezes. Sem a branch, corta `hotfix/X.Y.Z` da `main` e para esperando o conserto; de novo, com commits além da `main`, libera o CHANGELOG e abre a PR — a versão tem de ser o sucessor de patch da última tag. Com `release/*` aberta, o hotfix entra primeiro; a release depois se atualiza por `git merge origin/main`, nunca por rebase (o `non_fast_forward` do `release-hotfix.json` recusa o push), e o `release-check` a reprova enquanto a sync `main→develop` estiver pendente.
- **Sync:** a volta à `develop` é sempre a PR `sync/X.Y.Z` — `origin/main` mergeada sobre a `develop` num worktree temporário —, por merge commit (única forma de manter `main ⊆ develop`), nunca a PR `main→develop` crua: o merge limpo do CHANGELOG empurra bullet não lançado para baixo da versão lançada. A skill confere o CHANGELOG por conjunto de bullets antes de commitar (bullet perdido, bullet fora do lançado, marcador de conflito), e o `sync-check` repete a regra na PR.
- **Rollback:** `gh workflow run <release.deploy> --ref v<anterior> -f dry_run=false` — o deploy anterior é uma tag; só vale para tags criadas depois de o deploy aceitar `--ref` de tag (passo 6).

**Cuidado com `delete_branch_on_merge`.** Com a flag ligada, mergear uma PR apaga a branch **head** — numa PR `main→develop` crua, aberta à mão, é a própria `main` (o ruleset `deletion` a segura; a `develop` só está segura pelo `develop.json`). Confira antes de qualquer merge de release: `gh api repos/OWNER/REPO -q .delete_branch_on_merge`. Defeito real medido em 2026-08-31 em dois repos consumidores, quando a release ainda ia `develop→main` e a `develop` foi restaurada do clone local. Automação de apagar branch e branch de vida longa não convivem — ou a flag é `false`, ou as duas branches longas são protegidas.

### 3. Workflows de CI — antes dos rulesets
Sem check de CI existente, o ruleset com `required_status_checks` bloquearia todo PR para sempre.
- Copie de `references/infra/workflows/` para `.github/workflows/` (só os que **não existem**):
  - **todos os perfis:** `ci-node.yml` (projetos com `package.json`) ou `ci-python.yml` (pyproject/requirements) + `conventional-commits.yml` (valida os commits do PR sem depender de Node local);
  - **só com develop:** `release-check.yml` (gate da PR para a `main`: head do próprio repo em `release/*|hotfix/*`, CHANGELOG lançou a versão da branch, versão anterior com tag, tag inédita e maior que a última, sync pendente reprova a release) e `sync-check.yml` (sentinela da PR para a `develop`, por conjunto: bullet do `[Não lançado]` perdido, bullet fora do lançado e marcador de conflito reprovam; não exigido pelo ruleset). Os dois **repetem** o que as skills já checaram local — são a rede para PR aberta à mão.
- **Pinagem por SHA (regra canônica):** resolva cada `{{SHA:...}}` com `gh api repos/<owner>/<action>/commits/<tag> --jq .sha` e mantenha o comentário `# vX`.
- **Onde commitar** (vale também para os passos 1 e 6). `main` ainda sem ruleset (greenfield): direto nela, antes do passo 4. `main` já protegida (brownfield): por PR, com a base da topologia. **Com develop**, PR para a `develop`: os workflows chegam à `main` na primeira `release/*`, e o `release-check` já roda nela, porque o `pull_request` executa o workflow do merge ref. **Sem develop**, PR para a `main` por squash. Hotfix antes da primeira release nasce da `main` sem os workflows novos: traga-os para a `hotfix/*` (`git checkout origin/develop -- .github/workflows/`), ou os checks exigidos nunca reportam.
- Confirme o run verde antes do passo 4. O `release-check` só fica verde numa PR `release/*` — na `main` recém-provisionada ele não roda; basta o `ci`.

### 4. Rulesets de branch protection
Um laço só para greenfield e brownfield, parametrizado pela topologia do gate. Para cada ruleset: nome ausente → `POST` do **modelo**; nome presente → `GET` → **mescla** → `diff` → `PUT` só se mudou, senão `já conforme (no-op)`. A consulta inicial falhou (403/404)? **Pare** — não tente o POST às cegas (403 = plano free em repo privado; ver pré-requisitos).

O **modelo** é o template ajustado à topologia:
- `main.json` (com develop, cru): merge commit como único método — o squash é recusado pela plataforma, não por disciplina — e três contextos, `ci` + `commits` + `release-check`. Sem develop, o `jq` do bloco troca o método por `squash` e tira o `release-check`, que esse perfil não instala — receita, não arquivo `main-minimo.json`.
- `develop.json`: `strict_required_status_checks_policy: false` de propósito — nasceu para a PR de sync com head `main`, que **nunca** fica à frente da `develop`; com a sync por `sync/X.Y.Z`, que nasce da `develop`, esse bloqueio sumiu, e o `false` segue para a sync não pedir "update branch" a cada PR de escopo que entre na `develop` antes do merge dela.
- `release-hotfix.json`: uma regra só, `non_fast_forward`, sem `deletion` — bloqueia o force-push, logo o rebase local e o push dele; que o "Update with rebase" da UI também cai nela é **a provar no piloto**. A branch precisa poder morrer no merge.
- **`commits` é exigido nas duas branches longas** (decisão da delta-117, DT-103): o `conventional-commits.yml` é instalado em todos os perfis, e check que roda sem ser exigido não bloqueia nada — era a divergência entre o template, o exemplo brownfield e a promessa "checks verdes (`ci` + `commits`)".

A **mescla** parte do ruleset vivo, nunca do template cru (que apagaria bypass, regras extras e `integration_id` acrescentados pela UI), e só alinha ao modelo o que o fluxo usa:
- regra do modelo que o vivo não tem entra inteira — é assim que um `release-hotfix` defasado ganha `non_fast_forward` e um ruleset sem `pull_request` passa a proteger;
- `enforcement`, `allowed_merge_methods` e `strict_required_status_checks_policy` ficam iguais aos do modelo — o `strict: true` de uma `develop` provisionada antes cai aqui;
- `required_status_checks` é **união**: os checks vivos ficam como estão, com `integration_id` e os contextos que o repo já exige, e os do modelo que faltam entram no fim. Sem develop, `release-check` sai da união.

```bash
develop=sim   # topologia do gate: sim (perfil completo) | nao (perfil mínimo)
T=$(mktemp -d); R="${CLAUDE_PLUGIN_ROOT}/skills/projeto-infra/references/infra/rulesets"
if [ "$develop" = sim ]; then nomes="main develop release-hotfix"; metodos='["merge"]'; fora='[]'
else nomes="main"; metodos='["squash"]'; fora='["release-check"]'; fi
jq --argjson m "$metodos" --argjson fora "$fora" '
    (.rules[] | select(.type == "pull_request") | .parameters.allowed_merge_methods) = $m
  | (.rules[] | select(.type == "required_status_checks") | .parameters.required_status_checks)
      |= map(select(.context as $c | $fora | index($c) | not))' "$R/main.json" > "$T/main-modelo.json"
cp "$R/develop.json" "$T/develop-modelo.json"; cp "$R/release-hotfix.json" "$T/release-hotfix-modelo.json"
gh api repos/{owner}/{repo}/rulesets > "$T/lista.json" || { echo "consulta de rulesets falhou — pare"; exit 1; }
for nome in $nomes; do
  id=$(jq --arg n "sdd-protect-$nome" '.[] | select(.name == $n) | .id' "$T/lista.json")
  if [ -z "$id" ]; then
    gh api repos/{owner}/{repo}/rulesets --method POST --input "$T/$nome-modelo.json" > /dev/null && echo "$nome: criado"
    continue
  fi
  gh api "repos/{owner}/{repo}/rulesets/$id" | jq '{name, target, enforcement, bypass_actors, conditions, rules}' > "$T/$nome-atual.json"
  jq --argjson alvo "$(cat "$T/$nome-modelo.json")" --argjson fora "$fora" '
      .enforcement = $alvo.enforcement
    | reduce $alvo.rules[] as $r (.;
        if any(.rules[]; .type == $r.type) | not then .rules += [$r]
        elif $r.type == "pull_request" then
          (.rules[] | select(.type == "pull_request") | .parameters.allowed_merge_methods) = $r.parameters.allowed_merge_methods
        elif $r.type == "required_status_checks" then
          (.rules[] | select(.type == "required_status_checks") | .parameters) |= (
              .strict_required_status_checks_policy = $r.parameters.strict_required_status_checks_policy
            | .required_status_checks as $vivos
            | .required_status_checks = ($vivos + [$r.parameters.required_status_checks[] | select(.context as $c | all($vivos[]; .context != $c))]
                | map(select(.context as $c | $fora | index($c) | not))))
        else . end)' "$T/$nome-atual.json" > "$T/$nome-novo.json"
  if diff <(jq -S . "$T/$nome-atual.json") <(jq -S . "$T/$nome-novo.json"); then echo "$nome: já conforme (no-op)"; continue; fi
  gh api "repos/{owner}/{repo}/rulesets/$id" --method PUT --input "$T/$nome-novo.json" > /dev/null && echo "$nome: atualizado (diff acima)"
done
```
**Verificação = segunda rodada:** rode o bloco de novo; todo nome sai `já conforme (no-op)`. A projeção `{name, target, …}` deixa de fora os campos somente-leitura do GET (`id`, `_links`, datas). A mescla não mexe em `conditions`: ruleset com `include: []` **não protege nada** e pede o `PUT` do template — decisão do dono do repo, não da mescla. Antes da primeira rodada brownfield, confira o que a união vai exigir: contexto que nenhum workflow produz bloqueia todo PR para sempre, e `commits` exigido na `main` reprova a primeira `release/*` se a `develop` já carrega commit fora do padrão (`git log --no-merges --format=%s origin/main..origin/develop`).

### 5. husky + commitlint — só se o projeto tem Node (perfil completo)
```bash
npm i -D husky @commitlint/cli @commitlint/config-conventional
npx husky init && echo 'npx --no -- commitlint --edit' > .husky/commit-msg
# (sem argumento, o commitlint --edit lê .git/COMMIT_EDITMSG; não use "$ 1" literal aqui —
#  o carregador de skills substitui placeholders posicionais no conteúdo do SKILL.md)
echo "export default { extends: ['@commitlint/config-conventional'] };" > commitlint.config.js
```
Sem Node: a regra Conventional Commits já vive no CLAUDE.md e o `conventional-commits.yml` valida no CI — não instale Node só para isso.

### 6. Release pela máquina — perfil completo
A tag e a Release nascem em `/deltaspec:release`, na sessão, com o token do `gh` do humano — o `GITHUB_TOKEN` só existe dentro do runner. Evento criado com o token do humano **dispara** workflow: a tag criada pela skill aciona `on: push: tags` e a Release publicada aciona `on: release`; só push e tag feitos com o `GITHUB_TOKEN` não disparam. O deploy é despachado pela skill por escolha — um só dono do disparo —, não por limitação da plataforma.

- **Contrato do deploy:** o workflow de publicação aceita `workflow_dispatch` com o input `dry_run` (boolean) e roda a partir de `--ref vX.Y.Z` (tag) — é isso que torna o rollback um `gh workflow run --ref v<anterior>` — e **não** tem `on: push: tags` nem `on: release`: com eles, a tag da skill dispara um deploy de produção e o dispatch, outro. Que `-f dry_run=false` chega como boolean `false` no dispatch é **a provar no piloto**. O mapa ref→ambiente (tag = produção, `develop` = homologação) é do repo consumidor, não do framework.
- **Declare o nome do arquivo** em `doc-profile.yaml`: `release: { deploy: publicar.yml }`. Sem a chave, a skill `release` pula o deploy e diz que pulou.
- **Brownfield com release-please:** feche a PR aberta do bot, apague a branch `release-please--branches--main` e faça `git rm` dos três arquivos (`.github/workflows/release-please.yml`, `.release-please-config.json`, `.release-please-manifest.json`) no mesmo commit, que entra pela regra de **onde commitar** do passo 3. A tag git segue como fonte da verdade; a última tag do bot é a base da próxima versão — a skill `criar-release` a lê.

### 7. Review assistido — opcionais confirmados no gate
- **CodeRabbit:** instalar o app em https://github.com/apps/coderabbitai (ação do usuário — dê o link e aguarde). Opcional: `.coderabbit.yaml` na raiz com `language: "pt-BR"`.
- **claude-code-action:** copie `workflows/claude-code-review.yml` (resolva o SHA); requer o secret `CLAUDE_CODE_OAUTH_TOKEN` (ou `ANTHROPIC_API_KEY`) — instrua o usuário a criá-lo.

## Erros comuns

| Erro | Correto |
|---|---|
| Ruleset exigindo review antes do CODEOWNERS existir na main | CODEOWNERS → commit na main → só então o ruleset (passo 1) |
| Ruleset com status check antes do workflow de CI existir | CI verde primeiro (passo 3), ruleset depois (passo 4) |
| Reaplicar ruleset/workflow que já existe | Consultar antes; workflow existente = no-op relatado; ruleset existente = mescla, e sem diferença = `já conforme (no-op)` (passo 4) |
| Aplicar num repo sem develop a mescla do perfil completo | O laço do passo 4 recebe a topologia do gate: sem develop, squash e nada de `release-check` — exigido sem workflow que o produza, ele trava todo PR |
| Push direto na `main` já protegida (brownfield) | PR com a base da topologia (passo 3, "onde commitar") |
| `uses: action@v4` sem SHA | Pinar por SHA + comentário da versão (supply chain) |
| Instalar husky em projeto sem Node | CLAUDE.md + `conventional-commits.yml` no CI cobrem |
| Aplicar `develop.json` em tooling/site-estatico | Perfil mínimo é main-only |
| Rodar sem `gh` autenticado "para adiantar" | Pré-requisito falhou = parar e reportar |
| PR de escopo (`feat/*`) aberta direto contra a `main` com develop | Nenhum ruleset restringe a head; é o `release-check` que reprova — base da PR de escopo é a `develop` |
| PUT do ruleset com o template cru em repo já provisionado | Apaga bypass, regras e `integration_id` que a UI acrescentou; GET → mescla → `diff` → PUT só se mudou (passo 4) |
| `## [X.Y.Z]` acima do `## [Não lançado]` no CHANGELOG | O `release-check` lê o primeiro `## [X.Y.Z]` e acusa versão errada; `[Não lançado]` é sempre a primeira seção |
| `allow_merge_commit=false` no repo com `allowed_merge_methods: ["merge"]` | A PR fica sem botão de merge; `gh api repos/{owner}/{repo} --method PATCH -f allow_merge_commit=true` antes do ruleset |
| Ruleset criado pela UI com `enforcement: disabled` e dado como protegido | `disabled` não protege; a mescla do passo 4 o alinha ao `active` do modelo |
| Tag criada à mão antes de `/deltaspec:release` | No SHA do merge, a skill a trata como passo feito e segue; em outro commit, para — apague a tag local e remota e rode a skill de novo, que cria tag e Release juntas |

## Arquivos da skill

- `references/infra/rulesets/` — `main.json` (`refs/heads/main`, merge-only, `ci` + `commits` + `release-check`), `develop.json` (strict `false`, `ci` + `commits`), `release-hotfix.json` (`non_fast_forward` em `release/**` e `hotfix/**`). São o modelo do passo 4: corpo do `POST` quando o nome não existe, alvo da mescla quando existe; o perfil sem develop deriva do `main.json` por `jq`.
- `references/infra/workflows/` — `ci-node.yml`, `ci-python.yml`, `conventional-commits.yml`, `release-check.yml`, `sync-check.yml`, `claude-code-review.yml`.
