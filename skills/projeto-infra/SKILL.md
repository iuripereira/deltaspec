---
name: projeto-infra
description: Use when setting up or auditing repository infrastructure on GitHub — branch protection rulesets, CI workflows, Conventional Commits enforcement (husky/commitlint), release-please, CodeRabbit or claude-code-action review. Triggers include "/deltaspec:projeto-infra", "proteger a main", "configurar branch protection", "setup de CI", "automação de release", or the optional infra step offered by projeto-init. Requires gh CLI authenticated and a GitHub remote.
disable-model-invocation: true
---

# projeto-infra

## Overview

Aplica infraestrutura de repositório por perfil de projeto (herança de um bootstrap interno, descontinuado): rulesets de branch protection, CI, Conventional Commits, release-please e review assistido. **Roteiro em markdown — sem scripts instaláveis**; os comandos `gh api`/`git` são executados diretamente a partir dos templates em `references/infra/`. **Idempotência defensiva:** consulte o que já existe antes de aplicar cada item; segunda rodada = no-op relatado, nunca duplicação ou sobrescrita.

## Pré-requisitos (verificar antes do gate)

- `gh auth status` ok e remote GitHub presente (`gh repo view`). Sem um dos dois → **pare e reporte**; não aplique nada às cegas.
- **Rulesets exigem repo público ou GitHub Pro** (403 em repo privado no plano free). Detecte cedo: `gh api repos/{owner}/{repo}/rulesets` retornou 403 → ofereça ao usuário tornar o repo público, assinar Pro, ou seguir sem proteção (CI continua valendo) — a escolha é dele.
- Invocada avulsa (brownfield) ou pelo `projeto-init` (greenfield) — o processo é o mesmo.

## Processo

1. **Detectar perfil** — classifique o tipo (matriz do `projeto-init/references/detection.md`; na dúvida, pergunte):

| Tipo | Perfil | Conteúdo |
|---|---|---|
| app-web, backend | **completo** | rulesets `main`+`develop`, fluxo `feature/fix → develop → main`, husky+commitlint (se Node), release-please, CI, CodeRabbit + claude-code-action (opcionais) |
| tooling, site-estatico | **mínimo** | ruleset `main` only (fluxo simplificado, sem `develop`), CI lint/test |
| workspace-dados | **nenhum** | recuse com explicação (não há build/release a proteger) |

2. **Gate único** — confirme com o usuário: perfil (override manual é permitido), itens opcionais (CodeRabbit/claude-code-action) e se **review de code owner** será exigido (só faz sentido com 2+ pessoas; solo = PRs obrigatórios com 0 aprovações). Espere o "ok".
3. **Aplicar na ordem do roteiro** — a ordem importa (ver cada passo).
4. **Verificar e reportar** — liste: aplicado · já existia (no-op) · pulado com o porquê.

## Roteiro (ordem de execução)

### 1. CODEOWNERS — só se review de code owner foi exigido no gate
Crie `.github/CODEOWNERS` (`* @{{owner}}`) — se a `git-guard instalar` já deixou o mínimo, edite em vez de recriar — e commite **direto na main, antes de qualquer ruleset** — depois do ruleset o próprio commit do CODEOWNERS ficaria bloqueado. Em seguida, troque no `main.json`: `require_code_owner_review: true` e `required_approving_review_count: 1`.

### 2. Branch develop — só perfil completo
`git rev-parse --verify origin/develop` falhou? → `git branch develop main && git push -u origin develop`.

### 3. Workflows de CI — antes dos rulesets
Sem check de CI existente, o ruleset com `required_status_checks` bloquearia todo PR para sempre.
- Copie de `references/infra/workflows/` para `.github/workflows/` (só os que **não existem**): `ci-node.yml` (projetos com `package.json`) ou `ci-python.yml` (pyproject/requirements) + `conventional-commits.yml` (todos os tipos — valida os commits do PR sem depender de Node local).
- **Pinagem por SHA (regra canônica):** resolva cada `{{SHA:...}}` com `gh api repos/<owner>/<action>/commits/<tag> --jq .sha` e mantenha o comentário `# vX`.
- Commite na main (ainda desprotegida) e confirme o run verde antes de seguir.

### 4. Rulesets de branch protection
Idempotência: `gh api repos/{owner}/{repo}/rulesets --jq '.[].name'` — nome já existe → no-op. A consulta falhou (403/404)? **Pare** — não tente o POST às cegas (403 = plano free em repo privado; ver pré-requisitos).
```bash
gh api repos/{owner}/{repo}/rulesets --method POST --input references/infra/rulesets/main.json
gh api repos/{owner}/{repo}/rulesets --method POST --input references/infra/rulesets/develop.json  # só completo
```
O contexto exigido pelos rulesets é o job `ci` — não renomeie o job nos workflows sem ajustar o JSON.

### 5. husky + commitlint — só se o projeto tem Node (perfil completo)
```bash
npm i -D husky @commitlint/cli @commitlint/config-conventional
npx husky init && echo 'npx --no -- commitlint --edit' > .husky/commit-msg
# (sem argumento, o commitlint --edit lê .git/COMMIT_EDITMSG; não use "$ 1" literal aqui —
#  o carregador de skills substitui placeholders posicionais no conteúdo do SKILL.md)
echo "export default { extends: ['@commitlint/config-conventional'] };" > commitlint.config.js
```
Sem Node: a regra Conventional Commits já vive no CLAUDE.md e o `conventional-commits.yml` valida no CI — não instale Node só para isso.

### 6. release-please — só perfil completo
- Copie `workflows/release-please.yml` (resolva o SHA) e `release-please-config.json` → `.release-please-config.json` na raiz (seções do changelog já traduzidas para PT-BR).
- Crie `.release-please-manifest.json` com a versão vigente: `{".": "X.Y.Z"}` a partir de `git describe --tags --abbrev=0` (sem tag → `0.1.0`). **A tag git segue como fonte da verdade.**
- Se a tradução das seções falhar em alguma versão futura da action, degrade: release-please só gera release/tag e o CHANGELOG PT-BR segue manual — registre a limitação no relatório.

### 7. Review assistido — opcionais confirmados no gate
- **CodeRabbit:** instalar o app em https://github.com/apps/coderabbitai (ação do usuário — dê o link e aguarde). Opcional: `.coderabbit.yaml` na raiz com `language: "pt-BR"`.
- **claude-code-action:** copie `workflows/claude-code-review.yml` (resolva o SHA); requer o secret `CLAUDE_CODE_OAUTH_TOKEN` (ou `ANTHROPIC_API_KEY`) — instrua o usuário a criá-lo.

## Erros comuns

| Erro | Correto |
|---|---|
| Ruleset exigindo review antes do CODEOWNERS existir na main | CODEOWNERS → commit na main → só então o ruleset (passo 1) |
| Ruleset com status check antes do workflow de CI existir | CI verde primeiro (passo 3), ruleset depois (passo 4) |
| Reaplicar ruleset/workflow que já existe | Consultar antes; existente = no-op relatado |
| `uses: action@v4` sem SHA | Pinar por SHA + comentário da versão (supply chain) |
| Instalar husky em projeto sem Node | CLAUDE.md + `conventional-commits.yml` no CI cobrem |
| Aplicar `develop.json` em tooling/site-estatico | Perfil mínimo é main-only |
| Rodar sem `gh` autenticado "para adiantar" | Pré-requisito falhou = parar e reportar |

## Arquivos da skill

- `references/infra/rulesets/` — `main.json`, `develop.json` (payloads `gh api`).
- `references/infra/workflows/` — `ci-node.yml`, `ci-python.yml`, `conventional-commits.yml`, `release-please.yml`, `claude-code-review.yml`.
- `references/infra/release-please-config.json` — seções de changelog em PT-BR.
