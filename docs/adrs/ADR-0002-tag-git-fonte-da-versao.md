# ADR-0002: Tag git como fonte da verdade da versão

- **Status:** Accepted
- **Data:** 2026-07-19
- **Supersedes:** —
- **Superseded by:** —

## Context

> Registrada retroativamente em 2026-07-19, no backfill de ADRs da varredura de registros.
> A decisão vige desde a data acima (PR #10, primeiro release).

Este repositório não tem manifesto de pacote com campo de versão: é Markdown + dois scripts. O
`.claude-plugin/plugin.json` existe para o plugin, mas nasceu **sem** campo `version` — e o plano
da delta-001 (`specs/_archive/001-plugin/plan.md`) deixou em aberto "decidir se o manifesto passa a
espelhar a tag" quando o débito de release (zero tags em cinco merges) fosse quitado.

O débito foi quitado no PR #10 (`v0.1.0`, baseline SemVer). A decisão latente precisava fechar:
onde mora a versão?

Alternativas consideradas:

1. **Campo `version` no `plugin.json`**, bumpado a cada release.
2. **Arquivo `VERSION`** na raiz.
3. **Só a tag git `vX.Y.Z`** — nenhum arquivo versionado materializa a versão.

## Decision

Adotamos a alternativa 3: **a tag git é a única fonte da verdade da versão**. O `plugin.json`
segue sem campo `version`; o bump é derivado dos commits da delta (`fix`=PATCH, `feat`=MINOR,
`!`=MAJOR — o maior vence) e a tag corta no merge que conclui a delta.

Renunciamos ao campo no manifesto (1) e ao arquivo `VERSION` (2) pelo mesmo motivo: ambos criam
**um espelho a sincronizar a cada release** — exatamente a duplicação que a regra de ouro do
`CLAUDE.md` proíbe — sem nenhum consumidor que o exija: o marketplace do Claude Code instala o
plugin a partir do repositório, não de um número no manifesto.

## Consequences

**Fica mais fácil:** zero sincronia no release — cortar a tag *é* lançar; nenhum commit de "bump
version" poluindo o histórico; impossível a versão declarada divergir da real.

**Fica mais difícil:** a versão não é legível num checkout sem `git` (ex.: download de zip), e
ferramentas que esperem `version` no manifesto não a encontram. Aceito: hoje nenhum consumidor
assim existe.

**Reabre quando:** o marketplace do Claude Code (ou outro distribuidor) passar a exigir `version`
no `plugin.json`. Aí o campo entra como **espelho sancionado da tag**, documentado no `deps.toml`,
e esta ADR é substituída — não editada.
