<!-- resumo sdd-iuri · ≤15 linhas · única parte do plano lida pelo analyze e pelo humano -->
**Objetivo:** fechar a Fase 0 do plano de upgrade — inventário de skills sincronizado e validado no CI, hook pré-commit real (DT-005), ADR-0009 promovida com MUDA RNF1, `eu-tenho-tdah` reconhecida. **Cobre:** R1, R2, R3, RNF1 (da delta-013) **Decisões duráveis → ADRs:** nenhuma nova — promoção de status da ADR-0009 (Proposed → Accepted, lifecycle previsto) **Riscos assumidos:** promoção da ADR-0009 apoiada no piloto doc-profile/doc-entregavel (4 repos IMEX), não na delta externa com gate (segue DT-004); `core.hooksPath` exige ativação por clone (documentada).

---

## Contexto para execução sem sessão

Repo: framework sdd-iuri (plugin Claude Code). 9 skills em `skills/`; manifestos em `.claude-plugin/`. Gates: `check_cycle.py` (spec-feature) e `validate_integrity.py` (guarding-doc-integrity), stdlib pura, `--selftest` no CI. Regras: PT-BR, Conventional Commits com escopo `013-higiene`, fim de fase = commit, zero dependência nova, RNF5 proíbe caminho de máquina em `skills/**` e `.github/**`.

## Passo 1 — Sincronizar manifestos (R1, parte)

- `.claude-plugin/plugin.json` → `description` passa a citar as 9 skills: `projeto-init, projeto-infra, descoberta, spec-feature, spec-review, guarding-doc-integrity, handoff, doc-entregavel e eu-tenho-tdah`.
- `.claude-plugin/marketplace.json` → `plugins[0].description` idem (hoje omite `eu-tenho-tdah`).

## Passo 2 — Check de inventário no CI (R1)

Novo step no job `ci` de `.github/workflows/ci.yml`, após "Validar frontmatter": python inline (padrão dos steps existentes) que monta o set de diretórios `skills/*/` com `SKILL.md` e falha se algum nome não aparecer (case-insensitive — lição de 2026-07-20) na `description` do `plugin.json` **e** na `plugins[0].description` do `marketplace.json`, nomeando skill e manifesto omisso.

## Passo 3 — Hook pré-commit versionado (R2)

- **Neste repo:** `.githooks/pre-commit` (bash, executável): se o staged (`git diff --cached --name-only --diff-filter=ACMR`) não toca `.md` nem `deps.toml`, exit 0; senão roda `python3 skills/guarding-doc-integrity/scripts/validate_integrity.py .` e bloqueia com mensagem (inclui a existência do bypass consciente `--no-verify`) em exit ≠ 0. Ativação local (não versionável): `git config core.hooksPath .githooks` — documentada no README.
- **Para projetos de usuário:** `skills/guarding-doc-integrity/templates/pre-commit` — mesma lógica, mas o caminho do validador vem de `git config --get sdd-iuri.validator` (gravado pelo bootstrap com o caminho da instalação do plugin; config local, não versionada → RNF5 preservado). Config ausente → warning de 1 linha e exit 0 (nunca quebra commit de quem não instalou).
- **Bootstrap da skill (SKILL.md, fluxo 1):** novo passo — *oferecer* a instalação: copia o template para `.githooks/pre-commit` do projeto, `chmod +x`, `git config core.hooksPath .githooks` + `git config sdd-iuri.validator <caminho>`. Nunca sobrescreve `.githooks/pre-commit` ou hook ativo existente (RNF3); recusa do usuário = segue sem hook, sem insistir.

## Passo 4 — Reescrever as promessas do DT-005 (R2)

Alinhar promessa ↔ mecanismo nos promissores (varrer com `grep -riE 'pr[eé][- ]commit'`, lição do grep case-sensitive):
- `skills/guarding-doc-integrity/SKILL.md` — visão geral e fluxo 3 passam a descrever o gate como **hook versionado opt-in + gate de sessão** (o comando manual continua para quem não instalou).
- `skills/projeto-init/references/canonical-rules.md` (linha da regra de propagação) — idem, 1 frase.
- `README.md` linha ~35 — mantém "pré-commit" agora verdadeiro e documenta a ativação por clone.
- `deps.toml` (raiz) — conferir se o comentário promete pré-commit; ajustar se sim.
- `specs/TRUTH.md` — a menção em "Não implementado" fica **verdadeira** com o hook; revisar a frase no archive (TRUTH só muda no archive).

## Passo 5 — Promover ADR-0009 (RNF1)

`docs/adrs/ADR-0009-documentacao-visual-gate-configuravel.md`: `Status: Proposed` → `Accepted (2026-07-28, delta-013)`; remover o comentário "experimental"; nota curta na seção Status com a base de evidência (piloto doc-profile+doc-entregavel nos 4 repos IMEX, 8 exports, 2026-07-20) e o que permanece adiado (check mecânico do doc-profile — pendência roteada na delta-013). README: remover o marcador "**Experimental**" da linha da `doc-entregavel` (promoção prevista na própria ADR). O MUDA RNF1 consolida no archive.

## Passo 6 — CHANGELOG + HANDOFF (infra)

- `CHANGELOG.md` `[Não lançado]`: Adicionado (check de inventário no CI; hook pré-commit versionado + template/bootstrap; R3 eu-tenho-tdah no TRUTH) / Mudado (manifestos com 9 skills; ADR-0009 Accepted; MUDA RNF1; promessas do DT-005 alinhadas). Lição vigente: o CHANGELOG é task explícita.
- `HANDOFF.md`: "Agora" = delta-013 em curso (fase); corrigir o stale "Próxima delta livre: 012" → 014 ao fim.

## Verificação de conjunto

`python3 skills/spec-feature/scripts/check_cycle.py specs/013-higiene` · selftests dos 2 gates · `validate_integrity.py .` · simulação do step de inventário local · teste manual do hook (commit tocando `.md` com violação induzida → bloqueia; commit sem `.md` → passa; `--no-verify` documenta o bypass).

## Archive (pós-merge — faz parte do "pronto")

R1→próximo R livre do TRUTH (R31...), R2, R3 idem; MUDA RNF1 substitui o bloco integral; frase do "Não implementado" sobre pré-commit revisada; DT-005 → quitado (data, ref); pendência aberta (check do doc-profile) → novo DT; mover para `specs/_archive/013-higiene/`; rodar `check_cycle.py` pós-consolidação; tag `v0.9.0` no merge do archive (feat = MINOR).
