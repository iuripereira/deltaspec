# ADR-0016: o framework passa a se chamar `deltaspec`

- **Status:** Accepted (2026-07-28, delta-019)
- **Data:** 2026-07-28
- **Supersedes:** — (não revoga decisão anterior; renomeia a identidade estabelecida na ADR-0006/delta-008)
- **Superseded by:** —

## Context

O framework nasceu como `sdd-iuri` num contexto de uso pessoal, e o nome do autor no identificador era irrelevante enquanto o único consumidor era ele. Ao abrir o projeto à comunidade, o nome próprio vira atrito: sinaliza ferramenta pessoal em vez de projeto adotável, desincentiva contribuição externa e não descreve o que o framework faz.

O nome é identificador funcional, não rótulo: `plugin.json:name` define o namespace de invocação (`/<nome>:spec-feature`), e `marketplace.json` compõe a string de instalação (`<plugin>@<marketplace>`). Renomear quebra todo consumidor instalado — é breaking change, não cosmética.

Candidatos avaliados (disponibilidade verificada em 2026-07-28):

**1 — `delta-spec`.** Descreve exatamente o conceito central. Rejeitado: `github.com/codebycorey/delta-spec` já existe, é do **mesmo nicho** ("a minimal, Claude Code-native system for spec-driven development. Uses delta specs"), MIT, sem commit desde fev/2026. Nome colidente no mesmo ecossistema confunde busca, adoção e atribuição — mesmo com o projeto vizinho aparentemente inativo.

**2 — `deltaspec`.** Mesmo conceito, uma palavra, sem colisão no nicho. Repo `iuripereira/deltaspec` livre; npm e PyPI livres; sem colisão "delta" no marketplace oficial de plugins do Claude Code. O user GitHub `deltaspec` está ocupado por terceiro sem atividade na área, o que impede uma organização homônima mas não o repositório.

**3 — Manter `sdd-iuri`.** Custo zero de migração; mantém o atrito de adoção que motivou a mudança.

## Decision

Adotamos **`deltaspec`**. O rename atinge os pontos funcionais (manifestos, namespace, URLs de instalação, chave `git config deltaspec.validator` do hook pré-commit) e as descriptions das `SKILL.md`, que são o gatilho de auto-invocação.

Renunciamos à 1 pela colisão de nicho — o custo de compartilhar nome com outro framework de delta specs para Claude Code é permanente, enquanto o ganho de legibilidade do hífen é marginal. Renunciamos à 3 porque o atrito é justamente o que a abertura precisa remover.

O registro histórico **não é reescrito**: `specs/_archive/**`, ADRs já `Accepted` e seções lançadas do `CHANGELOG.md` preservam o nome de época — mesma guarda que a delta-010 aplicou ao renomear `STATE.md` → `HANDOFF.md` (DT-010). Reescrever histórico falsificaria o registro de quando cada decisão foi tomada.

O breaking change corta a **v1.0.0**: o rename é a fronteira entre o framework pessoal e o público, e a versão sinaliza que a partir daqui o namespace é contrato.

## Consequences

**Fica mais fácil:** adoção e contribuição de terceiros — o nome descreve o método (delta specs), não o autor; a organização/nome fica disponível para publicação futura em npm/PyPI se o framework ganhar distribuição fora do marketplace de plugins.

**Fica mais difícil:** todo consumidor instalado precisa reinstalar e trocar os comandos `/sdd-iuri:*` do próprio `CLAUDE.md` — endereçado pela seção de migração do README; projetos bootstrapados antes do rename carregam textos com o nome antigo até serem migrados (o `projeto-init` propaga templates para repos de terceiros); a busca por documentação antiga (issues, PRs, links externos) depende do redirect do GitHub, que sobrevive enquanto ninguém criar um repo `iuripereira/sdd-iuri` novo.
