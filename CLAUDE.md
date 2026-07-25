# CLAUDE.md

> This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**sdd-iuri** — plugin do Claude Code com as skills do framework: Spec-Driven Development por delta specs, com gates determinísticos. Stack: Markdown (skills) + Python 3.11+ (scripts de gate) + GitHub Actions. Idioma do projeto: **PT-BR**.

> **Layout.** As skills vivem em `skills/<nome>/`, o manifesto em `.claude-plugin/plugin.json`, e elas são invocadas sob o namespace `sdd-iuri:`. Script do framework é referenciado por `${CLAUDE_PLUGIN_ROOT}`, nunca por caminho absoluto de máquina — o job `ci` reprova o PR que introduzir um.

## Princípios inegociáveis

- **Fonte canônica única (regra de ouro):** cada informação tem **um** dono canônico. Referencie, não duplique. Valor concreto (número, regra, tipo) vive no arquivo dono; todo o resto linka. Quando a duplicação for inevitável, **documente-a** com instrução de manter em sincronia.
- **Parar e perguntar em ambiguidade:** o PRD/spec é soberano sobre regras de negócio. Se algo for ambíguo, **pare e pergunte** — não invente regra.
- **Débito honesto:** valores hardcoded, duplicações e anti-padrões conhecidos são **documentados** (com "quando/como corrigir"), nunca escondidos.
- **Idioma:** documentação e mensagens de commit em **PT-BR** salvo indicação contrária. Identificadores e comentários dos scripts também em PT-BR — é o padrão já vigente em `check_cycle.py` e `validate_integrity.py`; não misture idiomas dentro de um script.
- **Atualize a doc no mesmo change:** toda mudança relevante de comportamento atualiza a doc mais próxima (e o `HANDOFF.md`) no mesmo commit, para que sempre reflita a realidade.

## Versionamento, Changelog e Commits (tríade de release)

- **SemVer 2.0.0** — versões `MAJOR.MINOR.PATCH`. **A tag git `vX.Y.Z` é a fonte da verdade da versão**, não um manifesto de pacote (este repo não tem `package.json`).
- **Keep a Changelog 1.0.0** — toda mudança notável entra em `CHANGELOG.md` (na raiz), primeiro sob `## [Não lançado]`, agrupada em `Adicionado / Mudado / Corrigido / Removido / Obsoleto / Segurança`. No release, renomeie `[Não lançado]` → `## [X.Y.Z] - AAAA-MM-DD` e abra um `[Não lançado]` novo.
- **Conventional Commits 1.0.0** — `tipo(escopo): descrição`. Tipos: `feat fix docs refactor chore ci test style perf build revert`. Breaking via `!` ou rodapé `BREAKING CHANGE:`. Escopo = nome da skill (`feat(spec-feature):`, `fix(projeto-init):`); artefatos do ciclo usam o escopo da delta (`feat(001-plugin):`, `docs(006-notacao-delta):`).
- **Correlação commit → bump:** `fix` = PATCH · `feat` = MINOR · `!`/`BREAKING CHANGE` = MAJOR. O maior vence. **A tag corta no merge que conclui a delta — normalmente o PR de archive, porque o "pronto" inclui o archive. PRs de documentação fora do ciclo não geram tag.**
- **Valide no CI:** o job `commits` reprova PR com commits fora do padrão.

## Fluxo de trabalho Git

- **`main` protegida e sempre lançável.** Merge só via PR com checks verdes (`ci` + `commits`).
- **Branch por escopo:** `tipo/descrição-curta` em kebab-case (`feat/check-cycle`, `docs/projeto-init`). **1 sessão = 1 branch — não misture escopos.** Surgiu trabalho de outro escopo? É outra branch. Delta do ciclo usa `tipo/NNN-nome`.
- **`git pull` antes de ramificar/alterar.** Em checkout compartilhado, isole em `git worktree`.
- **Fim de etapa = commit + PR.** Uma branch por etapa; não acumule etapas num único PR. **PR > 500 linhas é anti-padrão.**
- **Merge por squash** — histórico da `main` = 1 commit por PR; a mensagem do squash segue Conventional Commits.
- **Higiene pós-merge:** apague a branch mergeada local (`git branch -d`) e remota (`git push origin --delete` + `git fetch --prune`). **Nunca apague a `main`.**
- Cuidado com `[skip ci]`: alguns provedores (Cloudflare Pages/Workers) honram e pulam o build.

### Assinatura de commit

- Commits gerados com apoio do Claude levam rodapé `Co-Authored-By: Claude <noreply@anthropic.com>`.
- Em PRs, registrar o modelo real (ex.: "Claude Opus 4.x") e um split honesto `<XX>% AI / <YY>% Human` que reflita de fato o balanço de contribuição.

## Documentação (Spec-Driven Development)

- **ADRs** (`docs/adrs/ADR-NNNN-titulo.md`) — formato Nygard (Context / Decision / Consequences), numeração de 4 dígitos. **Imutáveis após `Accepted`**: mudou a decisão? crie uma nova ADR com `Supersedes ADR-XXXX` e marque a antiga `Superseded by`. Crie ADR quando a **renúncia de uma alternativa** precisa registrar o *porquê*.
- **IDs estáveis e citáveis** — `Rn`/`RNFn` no `specs/TRUTH.md`, `delta-NNN` por delta, `ADR-NNNN`. São referenciados em vários arquivos: mantenha-os estáveis.
- **`HANDOFF.md`** — diário de bordo: o que está em curso **agora**, feito recente, problemas atuais e próximos passos imediatos; atualizado com frequência na própria sessão, janela rolante (histórico permanente = CHANGELOG + git). Em conflito de merge, mantenha a **união das verdades** — nunca sobrescreva progresso de outra sessão.
- **`DEBT.md`** — registro canônico de débito, pendências e lições, com IDs `DT-NNN` estáveis: natureza, descrição, origem, data de abertura, gatilho de correção e status. Item quitado **muda de status para `quitado (data, ref)`, nunca some**. Issue/ticket referencia o DT, nunca o substitui. (ADR-0007)
- **Documentação em camadas:** leia o `CLAUDE.md` mais próximo do que você toca; cada subpasta relevante tem o seu. Numa skill, a `SKILL.md` orquestra e o detalhe vive em `references/`.

## Ciclo de features (sdd-iuri)

- **1 feature = 1 delta spec** em `specs/NNN-nome/` (`spec.md`, `plan.md`, `tasks.md`), conduzida pelo comando `/sdd-iuri:spec-feature`. Numeração `NNN` **global ao repositório, nunca reinicia** — é ID estável citado em ADRs, commits e TRUTH.md.
- **Estados: proposta → aplicada → arquivada.** Delta arquivada move para `specs/_archive/` e consolida no **`TRUTH.md`** — a fonte da verdade do que vige (deltas antigas são histórico, não verdade). Archive faz parte do "pronto".
- **Só o que muda:** a delta declara ADICIONA/MUDA/REMOVE em relação ao TRUTH.md; todo requisito tem cenário DADO/QUANDO/ENTÃO verificável.
- **Planos de implementação: salvar em `specs/NNN-nome/plan.md`** (nunca em `docs/superpowers/plans/` — esta linha é a preferência de local que o writing-plans honra).
- **Este repo é o próprio framework.** Mudança em qualquer skill de `skills/` passa pelo ciclo — inclusive quando a mudança é no que o ciclo diz sobre si mesmo.

## Clean Code

- **Regra fora da orquestração:** as regras canônicas vivem em `references/` (ex.: `skills/projeto-init/references/canonical-rules.md`), consumidas pela `SKILL.md`. A SKILL.md não reimplementa nem duplica o texto da regra — aponta para ele.
- **Não duplicar lógica:** uma função/módulo-fonte por responsabilidade; todos os chamadores passam por ela.
- **Zero valor mágico → constantes nomeadas.** Todo limiar vive como constante nomeada no script (ex.: `TRUTH_LIMITE` em `check_cycle.py`) ou como linha única na regra canônica dona; nada de número solto repetido — inclusive aqui, por isso esta linha não os reproduz.
- **Zero dependência supérflua (YAGNI/DRY):** prefira stdlib e recursos nativos; não adicione framework/lib onde uma função resolve. Os gates usam stdlib pura (`re`, `pathlib`, `subprocess`, `tomllib`, `sys`) — zero pacote externo.
- **Funções puras separadas de I/O** (testáveis sem mock).
- **Não refatore conteúdo vendored** (skills de terceiros neste diretório) — elas não são do framework. **Nunca edite output de build** (será sobrescrito).
- **Corrija a causa, não suprima o warning.** Disable de linter é último recurso, sempre com comentário justificando.
- **Nomenclatura:** kebab-case descritivo em arquivos/scripts (com shebang quando executável); snake_case nos módulos Python.

## Testes

- **Co-localização:** a verificação mora junto do código — cada script de gate carrega o próprio `--selftest` com fixtures, em vez de um diretório de testes à parte.
- **TDD** onde a lógica é pura e o contrato é claro (parsers, checks). Recomendado, não obrigatório: dispensa por task exige justificativa registrada no `plan.md`.
- **Comandos:**
  - `python3 skills/spec-feature/scripts/check_cycle.py --selftest`
  - `python3 skills/guarding-doc-integrity/scripts/validate_integrity.py --selftest`
  - `python3 skills/spec-feature/scripts/check_cycle.py specs/NNN-nome` (gate da delta em curso)
- Ao mudar um template (`references/templates/`), atualize os consumidores **e** as fixtures juntos.
- Onde não há framework de testes, **o CI valida as convenções** (JSON/TOML/YAML, frontmatter das `SKILL.md`, Conventional Commits) e reprova o PR fora do padrão.

## Segurança

- **Secrets nunca versionados:** `.env` no `.gitignore` (+ `chmod 600` local) → em produção viram GitHub Secrets / Key Vault / Doppler.
- **Dados sensíveis/PII fora do git** — nunca relaxe esse `.gitignore`. **Nunca cole dado real** em commit, PR, issue ou ferramenta externa. Sem telemetria/cloud-sync não solicitados.
- **Validação nas duas pontas**; degradação graciosa (o ciclo degrada com aviso quando um plugin falta, nunca quebra).
- **Least privilege / defesa em profundidade:** allowlist de tools MCP só-leitura, `deny` vence, hooks `PreToolUse`/`Stop` para bloquear ações de escrita não previstas.
- **Supply chain:** GitHub Actions **pinadas por SHA** (+ comentário da versão).
