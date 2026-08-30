# CLAUDE.md

> This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**deltaspec** — plugin do Claude Code com as skills do framework: Spec-Driven Development por delta specs, com gates determinísticos. Stack: Markdown (skills) + Python 3.11+ (scripts de gate) + GitHub Actions. Idioma do projeto: **PT-BR**.

> **Layout.** As skills vivem em `skills/<nome>/`, o manifesto em `.claude-plugin/plugin.json`, e elas são invocadas sob o namespace `deltaspec:`. Script do framework é referenciado por `${CLAUDE_PLUGIN_ROOT}`, nunca por caminho absoluto de máquina — o job `ci` reprova o PR que introduzir um.

## Princípios inegociáveis

- **Fonte canônica única (regra de ouro):** cada informação tem **um** dono canônico. Referencie, não duplique. Valor concreto (número, regra, tipo) vive no arquivo dono; todo o resto linka. Quando a duplicação for inevitável, **documente-a** com instrução de manter em sincronia.
- **Parar e perguntar em ambiguidade:** o PRD/spec é soberano sobre regras de negócio. Se algo for ambíguo, **pare e pergunte** — não invente regra.
- **Débito honesto:** valores hardcoded, duplicações e anti-padrões conhecidos são **documentados** (com "quando/como corrigir"), nunca escondidos.
- **Idioma:** documentação e mensagens de commit em **PT-BR** salvo indicação contrária. Identificadores e comentários dos scripts também em PT-BR — é o padrão já vigente em `check_cycle.py` e `validate_integrity.py`; não misture idiomas dentro de um script.
- **Atualize a doc no mesmo change:** toda mudança relevante de comportamento atualiza a doc mais próxima (e o `HANDOFF.md`) no mesmo commit, para que sempre reflita a realidade.

## Versionamento, Changelog e Commits (tríade de release)

- **SemVer 2.0.0** — versões `MAJOR.MINOR.PATCH`. **A tag git `vX.Y.Z` é a fonte da verdade da versão**; o `.claude-plugin/plugin.json` é **espelho** dela (duplicação documentada no `deps.toml`), vigiado pelo job `ci` (`versao_manifesto.py` reprova manifesto atrás da maior tag). O PR de archive que corta a tag bumpa o `plugin.json` no mesmo commit.
- **Keep a Changelog 1.0.0** — toda mudança notável entra em `CHANGELOG.md` (na raiz), primeiro sob `## [Não lançado]`, agrupada em `Adicionado / Mudado / Corrigido / Removido / Obsoleto / Segurança`. No release, renomeie `[Não lançado]` → `## [X.Y.Z] - AAAA-MM-DD` e abra um `[Não lançado]` novo.
- **A entrada é uma linha e o PR conta a história** — bullet de uma frase, no máximo 200 caracteres, terminando com a referência do PR (`(#227)`; vários no mesmo parêntese). A narrativa — porquê, medição, renúncia, `delta-NNN`, `DT-NNN`, `Rn` — **fica fora**: o dono é o PR, a delta arquivada e a ADR ([ADR-0035](docs/adrs/ADR-0035-changelog-lancado-e-projecao-reescrevivel.md)). Quebra de compatibilidade leva `**BREAKING**` no início. O rodapé traz um link de comparação por versão. Reprovado pelo `check_changelog.py` no job `ci`.
- **Conventional Commits 1.0.0** — `tipo(escopo): descrição`. Tipos: `feat fix docs refactor chore ci test style perf build revert`. Breaking via `!` ou rodapé `BREAKING CHANGE:`. Escopo = nome da skill (`feat(spec-feature):`, `fix(projeto-init):`); artefatos do ciclo usam o escopo da delta (`feat(001-plugin):`, `docs(006-notacao-delta):`).
- **Correlação commit → bump:** `fix` = PATCH · `feat` = MINOR · `!`/`BREAKING CHANGE` = MAJOR. O maior vence. **A tag corta no merge que conclui a delta — normalmente o PR de archive, porque o "pronto" inclui o archive. PRs de documentação fora do ciclo não geram tag.**
- **Release publicado = processo e README revisados:** o mesmo change que corta a tag confere se o `README.md` (e o espelho `README.en.md`, sincronizado junto) ainda descrevem o processo real — comandos, etapas, contagens (skills, checagens). O README **não materializa a versão corrente**: a tag é a fonte; linke a página de tags. (Regra pedida pelo Iuri em 2026-08-04, quando o README foi pego anunciando `v1.3.0` com o repo na `v1.10.1`.)
- **Tag cortada = Release publicada:** depois do push da tag, `gh release create vX.Y.Z --title "vX.Y.Z" --notes` com a seção correspondente do CHANGELOG. A Release do GitHub é **projeção** da tag (a tag continua a fonte), mas é a vitrine que o visitante lê — sem ela a página anuncia versão velha como "Latest" (decisão do Iuri em 2026-08-04, DT-030; disciplina monitorada pelo DT-031).
- **Valide no CI:** o job `commits` reprova PR com commits fora do padrão.

## Fluxo de trabalho Git

- **`main` protegida e sempre lançável.** Merge só via PR com checks verdes (`ci` + `commits`).
- **Branch por escopo:** `tipo/descrição-curta` em kebab-case (`feat/check-cycle`, `docs/projeto-init`). **1 sessão = 1 branch — não misture escopos.** Surgiu trabalho de outro escopo? É outra branch. Delta do ciclo usa `tipo/NNN-nome`.
- **`git pull` antes de ramificar/alterar.** Em checkout compartilhado, isole em `git worktree`.
- **Nunca trabalhe em `~/.claude/plugins/marketplaces/`.** O harness serve o plugin desse diretório e o **re-clona (shallow) a cada `/plugin update`**: branch, commit não pushado e arquivo não rastreado somem sem aviso, e a reflog fica só com `clone`, sem `ORIG_HEAD` para resgatar. Pior, sendo raso, o C4 e o C7 se omitem — a delta perde justamente a proteção contra perda de requisito. Use clone próprio ou `git worktree`; o **C14** acusa.
- **Fim de etapa = commit + PR.** Uma branch por etapa; não acumule etapas num único PR. **PR > 500 linhas é anti-padrão.**
- **Merge por squash** — histórico da `main` = 1 commit por PR; a mensagem do squash segue Conventional Commits.
- **PR aberto é PR vivo.** Título e descrição valem para o que está na branch **agora**. Commit que amplia o escopo → releia os dois **antes de pedir revisão ou mergear** (não a cada push). Com mais de um commit, o squash leva o **título do PR** para a `main` — título velho fica no histórico; descrição velha engana quem revisa. As mensagens de commit sobrevivem (`COMMIT_MESSAGES`).
- **Higiene pós-merge:** apague a branch mergeada local (`git branch -d`) e remota (`git push origin --delete` + `git fetch --prune`). **Nunca apague a `main`.**
- Cuidado com `[skip ci]`: alguns provedores (Cloudflare Pages/Workers) honram e pulam o build.

### Assinatura de commit

- Commits gerados com apoio do Claude levam rodapé `Co-Authored-By: Claude <noreply@anthropic.com>`.
- Em PRs, registrar o modelo real (ex.: "Claude Opus 4.x") e um split honesto `<XX>% AI / <YY>% Human` que reflita de fato o balanço de contribuição.

## Documentação (Spec-Driven Development)

- **ADRs** (`docs/adrs/ADR-NNNN-titulo.md`) — formato Nygard (Context / Decision / Consequences), numeração de 4 dígitos. **Imutáveis após `Accepted`**: mudou a decisão? crie uma nova ADR com `Supersedes ADR-XXXX` e marque a antiga `Superseded by`. Crie ADR quando a **renúncia de uma alternativa** precisa registrar o *porquê*.
- **IDs estáveis e citáveis** — `Rn`/`RNFn` no TRUTH (particionado desde a delta-055: `specs/TRUTH.md` é **índice enxuto** e os requisitos vivem em `specs/truth/<dominio>.md`, um heading por requisito — ADR-0034), `delta-NNN` por delta, `ADR-NNNN`. São referenciados em vários arquivos: mantenha-os estáveis.
- **`HANDOFF.md`** — diário de bordo em duas camadas (ADR-0025): a raiz é **índice fino** (teto ~30 linhas — "Agora" + links das sessões recentes) e cada sessão com progresso real vira um arquivo em **`.claude/handoffs/HANDOFF_<topico>_<AAAA>_<MM>_<DD>.md`** (template `handoff-sessao.md` da projeto-init), focado em intenção e progresso — o arquivo da sessão nunca é podado. Versionar `.claude/handoffs/` é **convenção própria do framework** (a doc oficial do `.claude/` não prevê handoffs; o precedente é o `agent-memory/` versionado) — o porquê vive na ADR-0025. Em conflito de merge, mantenha a **união das verdades** — nunca sobrescreva progresso de outra sessão.
- **`debts/`** — registro canônico de débito, pendências e lições, **um arquivo por item** (ADR-0030): ativo em `debts/ativos/DEBT_DT-NNN-<topico>.md` (frontmatter com `id`/`natureza`/`estado`/`fila`/`descricao`/`aberto`). Cadastro é `debito.py novo`, nunca edição à mão: o comando calcula o `DT-NNN`, escreve o formato e relê o que escreveu — item inválido não fica no disco. Item que muda para `quitado`/`descartado` **arquiva no mesmo commit** — frontmatter ganha o estado final e `encerrado`, e o arquivo move (`git mv`) para `debts/_archive/DEBT_DT-NNN-<topico>_<AAAA>_<MM>_<DD>.md` — muda de lugar, **nunca some** (arquivado não é podado; links não mudam, mesma profundidade). Lições em `debts/LICOES.md`; regras em `debts/README.md`; `DEBT.md` da raiz é o **índice gerado** dos ativos (`debito.py indice`, projeção — ADR-0031; regenere após cadastrar/quitar). IDs `DT-NNN` globais e estáveis, contando as duas pastas. A `fila` grava só os eixos (`P·J·Pr`); o score é derivado na leitura, nunca gravado. Issue/ticket é **projeção** do DT, nunca o substitui. (ADR-0007 · ADR-0020 · ADR-0021 · ADR-0030)
- **Documentação em camadas:** leia o `CLAUDE.md` mais próximo do que você toca; cada subpasta relevante tem o seu. Numa skill, a `SKILL.md` orquestra e o detalhe vive em `references/`.

## Ciclo de features (deltaspec)

- **1 feature = 1 delta spec** em `specs/NNN-nome/` (`spec.md`, `plan.md`, `tasks.md`), conduzida pelo comando `/deltaspec:spec-feature`. Numeração `NNN` **global ao repositório, nunca reinicia** — é ID estável citado em ADRs, commits e TRUTH.md.
- **Estados: proposta → aplicada → arquivada.** Delta arquivada move para `specs/_archive/` e consolida no **TRUTH** — a fonte da verdade do que vige (deltas antigas são histórico, não verdade), na partição `specs/truth/<dominio>.md` do domínio correspondente. Archive faz parte do "pronto".
- **Mudança pequena não paga pipeline completo:** a spec-feature tem trilha reduzida — perfil `enxuto` (liga/desliga clarify, test-plan e a forma do review) e **`Tipo: bugfix`** (template próprio, pipeline curto: specify → plan curto → implement → review). Regras na tabela "Perfil de execução" e na seção "Delta bugfix" do `cycle.md` da skill.
- **Só o que muda:** a delta declara ADICIONA/MUDA/REMOVE em relação ao TRUTH.md; todo requisito tem cenário DADO/QUANDO/ENTÃO verificável.
- **Planos de implementação: salvar em `specs/NNN-nome/plan.md`** (nunca em `docs/superpowers/plans/` — esta linha é a preferência de local que o writing-plans honra).
- **Este repo é o próprio framework.** Mudança em qualquer skill de `skills/` passa pelo ciclo — inclusive quando a mudança é no que o ciclo diz sobre si mesmo.

## Clean Code

- **Regra fora da orquestração:** as regras canônicas vivem em `references/` (ex.: `skills/projeto-init/references/canonical-rules.md`), consumidas pela `SKILL.md`. A SKILL.md não reimplementa nem duplica o texto da regra — aponta para ele.
- **Não duplicar lógica:** uma função/módulo-fonte por responsabilidade; todos os chamadores passam por ela.
- **Zero valor mágico → constantes nomeadas.** Todo limiar vive como constante nomeada no script (ex.: `TRUTH_LIMITE` em `check_cycle.py`) ou como linha única na regra canônica dona; nada de número solto repetido — inclusive aqui, por isso esta linha não os reproduz.
- **Zero dependência supérflua (YAGNI/DRY):** prefira stdlib e recursos nativos; não adicione framework/lib onde uma função resolve. Os gates usam stdlib (`re`, `pathlib`, `subprocess`, `tomllib`, `sys`) mais **uma única dependência externa admitida: `PyYAML`**, para validar o `doc-profile.yaml` — a renúncia ao parser próprio está na [ADR-0023](docs/adrs/ADR-0023-pyyaml-como-dependencia-admitida.md). Dependência nova exige o mesmo grau de justificativa, nunca um aceno para essa ADR.
- **Funções puras separadas de I/O** (testáveis sem mock).
- **Não refatore conteúdo vendored** (skills de terceiros neste diretório) — elas não são do framework. **Nunca edite output de build** (será sobrescrito).
- **Corrija a causa, não suprima o warning.** Disable de linter é último recurso, sempre com comentário justificando.
- **Nomenclatura:** kebab-case descritivo em arquivos/scripts (com shebang quando executável); snake_case nos módulos Python.

## Testes

- **Co-localização:** a verificação mora junto do código — cada script de gate carrega o próprio `--selftest` com fixtures, em vez de um diretório de testes à parte.
- **TDD** onde a lógica é pura e o contrato é claro (parsers, checks). Recomendado, não obrigatório: dispensa por task exige justificativa registrada no `plan.md`.
- **Comandos do dia a dia:**
  - `python3 skills/spec-feature/scripts/check_cycle.py specs/NNN-nome` (gate da delta em curso)
  - `python3 skills/spec-feature/scripts/check_cycle.py --selftest`
  - A **lista completa** de selftests vive no README (§7, "As checagens automáticas") e é o que o job `ci` executa — não a duplique aqui: a cópia parcial desta seção foi o drift pego pela auditoria 01 (P0-2).
- Ao mudar um template (`references/templates/`), atualize os consumidores **e** as fixtures juntos.
- Onde não há framework de testes, **o CI valida as convenções** (JSON/TOML/YAML, frontmatter das `SKILL.md`, Conventional Commits) e reprova o PR fora do padrão.

## Segurança

- **Secrets nunca versionados:** `.env` no `.gitignore` (+ `chmod 600` local) → em produção viram GitHub Secrets / Key Vault / Doppler.
- **Dados sensíveis/PII fora do git** — nunca relaxe esse `.gitignore`. **Nunca cole dado real** em commit, PR, issue ou ferramenta externa. Sem telemetria/cloud-sync não solicitados.
- **Validação nas duas pontas**; degradação graciosa (o ciclo degrada com aviso quando um plugin falta, nunca quebra).
- **Least privilege / defesa em profundidade:** allowlist de tools MCP só-leitura, `deny` vence, hooks `PreToolUse`/`Stop` para bloquear ações de escrita não previstas. Neste repo a regra está materializada: `.claude/settings.json` registra o hook `guarda-imutaveis.py` (escrita em `_archive/` pede confirmação), e skill com efeito colateral externo tem `disable-model-invocation: true` (delta-061).
- **Identificador de terceiro não entra no que é publicado.** Este repositório é **privado e é a fonte canônica**; o repositório público é **derivado** dele por allowlist ([ADR-0036](docs/adrs/ADR-0036-publicacao-derivada-como-gate-de-confidencialidade.md)). O escopo da regra é o **allowlist de publicação** declarado em `scripts/publica-dist.sh` — `skills/`, `docs/adrs/`, `CHANGELOG.md`, README e manifestos. Ali, nome de organização, de projeto de terceiro, de site interno (Jira/org) ou dado de negócio dele (volume, sistema em uso, prazo, estágio contratual) entram **sob pseudônimo** — `cliente-A`, `caso de referência`, `um repo consumidor` —, e o **fato técnico é o que importa e deve ser preservado** ("validado em produção", "149 issues", "defeito real medido"); o identificador é que sai. Fora do allowlist — `specs/`, `debts/`, `.claude/handoffs/` — o registro segue com **nome real**: ele nunca é publicado, e é o que mantém o registro honesto.
- **O gate roda nas duas pontas, com degradação oposta.** `guarda-confidencialidade.py` lê `.claude/nomes-confidenciais.txt` (**gitignored de propósito**: versionar a lista anularia o propósito dela). Como hook `PreToolUse` é a primeira ponta — `deny` na escrita, e sem o arquivo avisa e libera (degradação graciosa, padrão RNF2). Como `--varre <dir>`, chamado por `publica-dist.sh`, é a segunda — e ali **lista ausente reprova**: publicar é porta de mão única, e sem gate não se atravessa. A defesa principal, porém, é o allowlist, que não depende de a lista estar completa.
- **Supply chain:** GitHub Actions **pinadas por SHA** (+ comentário da versão).
