# ADR-0048: O deltaspec passa ao perfil com `develop`

- **Status:** Accepted
- **Data:** 2026-09-13
- **Supersedes:** [ADR-0045](ADR-0045-release-por-skills-do-plugin-e-merge-commit-na-main.md) (em uma cláusula: o deltaspec como perfil sem `develop`)
- **Superseded by:** —

## Context

A [ADR-0045](ADR-0045-release-por-skills-do-plugin-e-merge-commit-na-main.md) desenhou o fluxo de release para a topologia com `develop` — é nela que o 83/76 foi medido, num repo consumidor — e deixou o deltaspec no perfil sem `develop`: corte da `main`, PR de release por squash, tag no merge. Com isso, o caminho que os consumidores usam (merge commit na `main`, sync `main→develop` por `sync/X.Y.Z`, `main ⊆ develop`) nunca roda no próprio framework, e erro de skill nesse caminho aparece primeiro no consumidor. E o deltaspec fica sem o gate que a alternativa 3 da ADR-0045 recusou tirar dos outros: a `develop` é onde o dono homologa antes do merge na `main`.

O PO decidiu em 2026-09-13 que o deltaspec passa a ter `develop`, pelos dois motivos: homologar antes da `main` e exercitar no framework o perfil que os consumidores usam.

A plataforma passou a permitir a proteção no mesmo dia: com o GitHub Pro assinado em 2026-09-13, a API de rulesets deste repositório (privado) deixou de responder 403 (DT-166), e os rulesets da ADR-0045 valem aqui como nos consumidores.

## Decision

- **A `develop` nasce da `main` no commit da tag `v1.59.0`**, a última release do perfil sem `develop`. Nasce idêntica: não há rebase, porque não há nada divergente.
- **A rota é a da ADR-0045**, sem exceção para o framework: `feature|fix|bugfix → develop` por squash → `release/X.Y.Z` → `main` por merge commit → sync `main→develop` por `sync/X.Y.Z`; `hotfix/*` sai da `main`. As skills detectam a topologia pelo remoto e não mudam.
- **A branch default continua `main`** — premissa da ADR-0045: rulesets, gatilho do `release-check` e skills a nomeiam literalmente.
- **PR aberta contra a `main` na criação da `develop` passa a ter a `develop` como base**, menos `release/*` e `hotfix/*`.
- **A proteção é o perfil completo da `/deltaspec:projeto-infra`**: `sdd-protect-main` (só merge commit; `ci` + `commits` + `release-check`; `strict`), `sdd-protect-develop` (merge ou squash; `ci` + `commits`; sem `strict`) e `sdd-protect-release-hotfix` (`non_fast_forward`), sem liberação para admin, mais os workflows `release-check` e `sync-check`. A ruleset criada à mão antes deles, uma só para `main` e `develop`, saiu: com dois rulesets na mesma branch vale a versão mais restritiva de cada regra, e ela manteria o `strict` na `develop`, o `claude-review` exigido e a liberação para admin.
- **Vigência a partir da `v1.59.0`.** O próximo corte é o primeiro com `develop`; a tag `v1.59.0` é ancestral da `develop` desde o nascimento, e o `versao_corte.py` conta a partir dela, sem o caso de adoção.

## Alternativas renunciadas

1. **Manter o deltaspec sem `develop`.** Preserva o único exercício real do perfil sem `develop`, ao custo dos dois motivos do Context: sem gate de homologação, e o perfil dos consumidores sem exercício no framework.
2. **Criar a `develop` antes de publicar a `v1.59.0`.** A `release/1.59.0` foi cortada da `main` no perfil sem `develop`; criada a `develop` no meio, a `/deltaspec:release` a publicaria no outro perfil (merge commit e `sync/1.59.0`), com os dois perfis misturados numa release só.
3. **`develop` como branch default.** O `Closes #N` passaria a fechar a issue no merge da PR de escopo, mas a premissa da ADR-0045 cai: rulesets, `release-check` e skills nomeiam a `main`.

## Consequences

- \+ Gate de homologação antes da `main`, como nos consumidores.
- \+ Merge commit na `main`, `sync/X.Y.Z` e a verificação `main ⊆ develop` rodam no framework antes de rodarem no consumidor.
- − O perfil sem `develop` perde o único exercício real; erro de skill nesse caminho volta a aparecer só no consumidor.
- − Toda release passa a ter duas PRs a mais, a `release/*` e a `sync/*`.
- − `Closes #N` só fecha a issue quando o commit chega à `main`, na release; o `debito.py vinculo` avisa "alvo ≠ default" em toda PR que quita DT com Ticket contra a `develop`.
- \+ O servidor recusa squash e rebase na `main`: `main ⊆ develop` deixa de depender só da skill.
- − O `claude-review` deixa de ser exigido: roda em toda PR e comenta, mas não bloqueia — o gate é o determinístico (`ci`, `commits`, `release-check`).
- − Hotfix cortado antes da primeira release com `develop` nasce da `main` sem o `release-check.yml`: traga os workflows para a `hotfix/*` (`git checkout origin/develop -- .github/workflows/`), ou o check exigido nunca reporta.
