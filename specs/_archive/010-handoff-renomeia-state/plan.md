<!-- resumo-plan: cabeçalho ≤15 linhas para humanos e para o analyze -->
# Resumo do plano — delta-010

- **Objetivo:** renomear `STATE.md` → `HANDOFF.md` em todo o framework, eliminando o conceito STATE. Digest que roteia (mantém a regra de ouro). MUDA R19, MUDA R20.
- **Abordagem:** renomeação mecânica (`grep -rn "STATE.md"` guia), poupando `specs/_archive/**` e ADRs Accepted (imutáveis). A skill `handoff` ganha prompt de retomada de uma linha + auto-migração `git mv` para repos legados.
- **Núcleo:** `skills/handoff/SKILL.md` (reescrita), `templates/STATE.md`→`HANDOFF.md`, `canonical-rules.md`, `detection.md`, `projeto-init/SKILL.md`, `CLAUDE.md`, `deps.toml`, `README.md`, `STATE.md`→`HANDOFF.md` da raiz.
- **Já feito:** spec.md, ADR-0010 (renúncia), índice de ADRs.
- **Verificação:** `grep -rn "STATE.md"` só sobra em imutáveis; selftests dos dois gates verdes; `validate_integrity.py` não reprova o HANDOFF.md; `check_cycle.py specs/010-*` verde.
- **Débito:** DT-010 (guarda: referências mortas a STATE.md em archive/ADRs — não migrar).
- **TDD:** dispensado — mudança é renomeação de convenção em docs/markdown, sem lógica pura nova. Os gates (`check_cycle`, `validate_integrity`) já cobrem a verificação por CI. (justificativa registrada, per CLAUDE.md/tooling.)

---

## Detalhe por task

### T1 — Reescrever a skill `handoff` (cobre R20)
[skills/handoff/SKILL.md](../../skills/handoff/SKILL.md):
- `description` (frontmatter): `STATE.md (diário de bordo)` → `HANDOFF.md (diário de bordo)`.
- Overview: "o andamento vai para o `STATE.md`" → `HANDOFF.md`; menção R18/R19 mantida (R19 vira HANDOFF no TRUTH via archive).
- Passo 2: "Atualizar o `STATE.md`" → `HANDOFF.md`.
- Passo 5: colapsar o prompt de retomada para uma linha apontando `HANDOFF.md`; variante multi-repo idem. Texto: `Leia o HANDOFF.md deste repo e continue de onde paramos. Foco: <primeiro item de "Próximos passos imediatos">.`
- **Novo passo (migração):** antes de escrever, "se houver `STATE.md` legado e não houver `HANDOFF.md`, `git mv STATE.md HANDOFF.md` e siga".
- Tabela "Erros comuns": trocar `STATE.md` → `HANDOFF.md` nas 2 linhas que o citam.

### T2 — Renomear o template do scaffold (cobre R19)
- `git mv skills/projeto-init/references/templates/STATE.md skills/projeto-init/references/templates/HANDOFF.md`.
- Reframe do cabeçalho do template: título `# HANDOFF.md — diário de bordo` e blockquote (auto-referências STATE→HANDOFF). Seções internas ("Agora"…) **inalteradas**.

### T3 — Regras canônicas e matriz de detecção (cobre R19)
- [skills/projeto-init/references/canonical-rules.md](../../skills/projeto-init/references/canonical-rules.md): módulo `docs-sdd` (~linha 88) — def do STATE.md → HANDOFF.md.
- [skills/projeto-init/references/detection.md](../../skills/projeto-init/references/detection.md): matriz "Arquivos de scaffold × tipo" (~79–91) — linha/coluna `STATE.md` → `HANDOFF.md` (mantendo `✅`/`❌ (HANDOFF só)`).
- [skills/projeto-init/SKILL.md](../../skills/projeto-init/SKILL.md): lista de templates (linha 57) e notas de scaffold — `STATE` → `HANDOFF`.

### T4 — Registros da raiz + governança (cobre R19)
- [CLAUDE.md](../../CLAUDE.md): def do STATE.md (linha 44) e menção "no mesmo change" (linha 15) → HANDOFF.md.
- [deps.toml](../../deps.toml): `exclude_globs` (linha 16) `STATE.md` → `HANDOFF.md` **e** o comentário da linha 11 ("diário de bordo (STATE.md)"). **Crítico.**
- [README.md](../../README.md): linhas 87, 92, 122 + qualquer diagrama mermaid que cite STATE.md.
- `git mv STATE.md HANDOFF.md` (raiz); atualizar o blockquote e os auto-links do arquivo. Conteúdo (janela rolante) preservado.

### T5 — DEBT.md: guarda das referências mortas (cobre infra)
[DEBT.md](../../DEBT.md): nova linha `DT-010` (guarda) — "referências a STATE.md em `specs/_archive/**` e ADRs Accepted (0001/0007/0008) — imutáveis; não corrigir, não migrar", origem `delta-010`, aberto 2026-07-24, gatilho `—` (guarda permanente).

### T6 — CHANGELOG (cobre infra)
[CHANGELOG.md](../../CHANGELOG.md): sob `[Não lançado]` — `Mudado`: renomeação STATE→HANDOFF; nota `BREAKING CHANGE:` com caminho de migração (auto-`git mv` na skill).

### Verificação de fechamento (antes do archive)
- `grep -rn "STATE.md" .` → só `specs/_archive/**` e ADRs 0001/0007/0008.
- `python3 skills/spec-feature/scripts/check_cycle.py --selftest` e `python3 skills/guarding-doc-integrity/scripts/validate_integrity.py --selftest` verdes.
- `python3 skills/guarding-doc-integrity/scripts/validate_integrity.py` (repo) não reprova HANDOFF.md.
- `python3 skills/spec-feature/scripts/check_cycle.py specs/010-handoff-renomeia-state` verde.
- Sem caminho de máquina (RNF5): `! grep -rnE '(~|\$HOME|/home/[^/ ]+)/[.]claude/skills' skills/ .github/`.
