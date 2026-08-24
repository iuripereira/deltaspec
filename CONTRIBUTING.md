# Contribuindo com o deltaspec

Obrigado pelo interesse! Este guia cabe numa leitura de 3 minutos. *(English summary at the end.)*

## Idioma

- **Documentação, commits e identificadores de script são em PT-BR** — é convenção registrada no [CLAUDE.md](CLAUDE.md) e vale para todo o repositório. O [README em inglês](README.en.md) é a exceção sancionada, mantido em sincronia com o [README.md](README.md).
- Issues e PRs podem ser abertos **em PT-BR ou EN** — responda-se na língua em que a conversa começou.

## O fluxo

1. **Fork + branch por escopo:** `tipo/descricao-curta` em kebab-case (`feat/check-cycle`, `docs/typo-readme`). Um escopo por branch.
2. **Commits em [Conventional Commits 1.0.0](https://www.conventionalcommits.org/pt-br/v1.0.0/)** — o job `commits` do CI reprova PR fora do padrão. Tipos: `feat fix docs refactor chore ci test style perf build revert`.
3. **PR contra a `main`** com os dois checks verdes (`ci` + `commits`). Merge é por squash. PR acima do limiar canônico de tamanho (ver CLAUDE.md) será pedido para dividir.

## A regra que muda tudo aqui

**Este repositório é o próprio framework, aplicado a si mesmo.** Mudança em qualquer skill de `skills/` passa pelo ciclo de delta specs (`/deltaspec:spec-feature`): spec com blocos ADICIONA/MUDA/REMOVE contra o `specs/TRUTH.md`, gate `check_cycle.py`, archive que consolida. Para mudanças assim, **abra uma issue antes** descrevendo o incremento — a delta é conduzida em conjunto.

Mudanças fora de `skills/` (docs, CI, correções pontuais) seguem o fluxo normal de PR.

O repositório publicado em `iuripereira/deltaspec` é **derivado** da fonte canônica ([ADR-0036](docs/adrs/ADR-0036-publicacao-derivada-como-gate-de-confidencialidade.md)): cada release o regenera por completo, então edição direta nele se perde na publicação seguinte. Os registros de processo citados neste guia (`specs/`, `debts/`, `DEBT.md`, `.githooks/`) vivem só no canônico — a contribuição chega lá via issue + PR, conduzida em conjunto.

## Verifique antes de abrir o PR

```bash
python3 skills/spec-feature/scripts/check_cycle.py --selftest
python3 skills/guarding-doc-integrity/scripts/validate_integrity.py --selftest
# sem deps.toml na raiz (repo derivado), troque a linha abaixo por: … --links-only .
python3 skills/guarding-doc-integrity/scripts/validate_integrity.py .
```

Ative também o gate pré-commit, uma vez por clone: `git config core.hooksPath .githooks`

## Onde cada coisa mora

Antes de propor algo, confira se já tem dono: débito e pendências em `DEBT.md` (IDs `DT-NNN`), decisões e renúncias em [docs/adrs/](docs/adrs/), o que vige em `specs/TRUTH.md`, convenções no [CLAUDE.md](CLAUDE.md). **Cada informação tem um dono: referencie, não duplique.**

## Segurança e conduta

- Vulnerabilidades: reporte privado conforme [SECURITY.md](SECURITY.md) — nunca em issue pública.
- Convivência: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) (Contributor Covenant 2.1).

---

## English summary

**deltaspec** is a Claude Code plugin for Spec-Driven Development via delta specs. The project language is **Brazilian Portuguese** (docs, commits, script identifiers — a recorded convention in `CLAUDE.md`); the [English README](README.en.md) is the sanctioned exception. Issues and PRs in English are welcome.

To contribute: fork → scope branch (`type/short-description`) → [Conventional Commits](https://www.conventionalcommits.org) → PR against `main` with both CI checks green (`ci` + `commits`); merges are squashed. **Any change under `skills/` must go through the framework's own delta-spec cycle** (this repo dogfoods itself) — open an issue first and the delta will be driven together. Run the self-tests above before opening a PR. Security reports go through [SECURITY.md](SECURITY.md), never public issues; the [Contributor Covenant 2.1](CODE_OF_CONDUCT.md) applies.
