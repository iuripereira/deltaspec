# Regras canônicas — compilado das melhores práticas

Fonte da verdade das regras do `projeto-init`. Cada módulo abaixo é uma **seção montável** do `CLAUDE.md` gerado. Monte na ordem em que aparecem aqui. Só inclua um módulo se a marca **Incluir quando** casar com o projeto (ver `detection.md` para a matriz por tipo).

Placeholders `{{assim}}` são preenchidos a partir da inspeção do projeto. Texto em PT-BR — é o idioma padrão de todos os projetos do usuário; o cabeçalho boilerplate fica em inglês por convenção.

---

## MÓDULO: header — SEMPRE

```markdown
# CLAUDE.md

> This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**{{nome_do_projeto}}** — {{uma linha: o que é o projeto}}. Stack: {{stack}}. Idioma do projeto: **{{idioma, ex.: PT-BR}}**.
```

---

## MÓDULO: core — SEMPRE (o núcleo inegociável, difundido em todos os projetos)

```markdown
## Princípios inegociáveis

- **Fonte canônica única (regra de ouro):** cada informação tem **um** dono canônico. Referencie, não duplique. Valor concreto (número, regra, tipo) vive no arquivo dono; todo o resto linka. Quando a duplicação for inevitável, **documente-a** com instrução de manter em sincronia.
- **Parar e perguntar em ambiguidade:** o PRD/spec é soberano sobre regras de negócio. Se algo for ambíguo, **pare e pergunte** — não invente regra.
- **Débito honesto:** valores hardcoded, duplicações e anti-padrões conhecidos são **documentados** (com "quando/como corrigir"), nunca escondidos.
- **Idioma:** documentação e mensagens de commit em **{{idioma}}** salvo indicação contrária. {{Se técnico: identificadores e comentários de código em inglês; senão, comentários também em {{idioma}}.}}
- **Atualize a doc no mesmo change:** toda mudança relevante de comportamento atualiza a doc mais próxima (e o `HANDOFF.md`) no mesmo commit, para que sempre reflita a realidade.
```

---

## MÓDULO: release-triad — Incluir quando: projeto versionável (app, lib, site com releases). Pular em workspace de dados.

```markdown
## Versionamento, Changelog e Commits (tríade de release)

- **SemVer 2.0.0** — versões `MAJOR.MINOR.PATCH`. **A tag git `vX.Y.Z` é a fonte da verdade da versão**, não o `package.json` (que fica `private` e pode não ser bumpado a cada PR).
- **Keep a Changelog 1.0.0** — toda mudança notável entra no `CHANGELOG.md` (na raiz), agrupada em `Adicionado / Mudado / Corrigido / Removido / Obsoleto / Segurança`. **A PR não edita o `CHANGELOG.md`**: ela deixa um fragmento em `changelog.d/<slug>.<categoria>.md` com uma linha, e `montar_changelog.py` colide os fragmentos no `## [Não lançado]` no release, apagando-os. Duas PRs vivas editando a mesma seção conflitam a cada merge; dois arquivos com nomes diferentes, nunca. No release, renomeie `[Não lançado]` → `## [X.Y.Z] - AAAA-MM-DD` e abra um `[Não lançado]` novo.
- **O dono do CHANGELOG é um só, e depende da fase** — em `especificação` (o repo ainda não publica release nenhum) o dono é o fragmento curado, e **release-please não é instalado**: com `docs`/`chore` escondidos ele geraria vazio. Em `implementação`, o fragmento continua sendo o dono do texto e o release-please entra só para versão e tag. **Nunca os dois escrevendo o CHANGELOG.**
- **A entrada é uma linha e o PR conta a história** — bullet de uma frase, no máximo 200 caracteres, terminando com a referência do PR: `- Skills de efeito colateral viram manual-only (#227)`. Vários PRs no mesmo parêntese (`(#227, #228)`); quebra de compatibilidade prefixada por `**BREAKING**` e no topo da subseção. A narrativa — porquê, medição, renúncia, IDs de delta/débito/requisito — **fica fora**: o dono canônico é o PR, a delta arquivada e a ADR, e a entrada só referencia. Repositório sem remoto omite a referência. Mudança sem efeito observável para quem consome o projeto não vira entrada.
- **Versões vinculáveis** — o rodapé do arquivo traz um link de comparação por versão (`[1.29.0]: <repo>/compare/v1.28.0...v1.29.0`), como o padrão pede.
- **Release publicado não é intocável quanto à forma** — condensar uma entrada lançada para o formato acima é reprojeção, não reescrita de história; o **nome de época** que ela cita (nome antigo do projeto, arquivo já renomeado, número medido) é que nunca muda.
- **Conventional Commits 1.0.0** — `tipo(escopo): descrição`. Tipos: `feat fix docs refactor chore ci test style perf build revert`. Breaking via `!` ou rodapé `BREAKING CHANGE:`.
- **Correlação commit → bump:** `fix` = PATCH · `feat` = MINOR · `!`/`BREAKING CHANGE` = MAJOR. O maior vence. **Tag = release a cada merge na `main`; PRs só de documentação não geram tag.**
{{se houver CI: - **Valide no CI:** um job reprova PR com commits fora do padrão, e `check_changelog.py` reprova entrada fora do formato (categoria, tamanho, referência de PR, ordenação, rodapé). Repositório cujo fluxo não passa por PR roda o gate com `--sem-pr`.}}
```

---

## MÓDULO: git-workflow — Incluir quando: projeto usa git (quase sempre). Versão "leve" em workspace de dados.

```markdown
## Fluxo de trabalho Git

- **`main` protegida e sempre lançável.** Merge só via PR com checks verdes.
- **Branch por escopo:** `tipo/descrição-curta` em kebab-case (`feat/agenda-recorrente`, `fix/fuso-horario`). **1 sessão = 1 branch — não misture escopos.** Surgiu trabalho de outro escopo? É outra branch.
- **`git pull` antes de ramificar/alterar.** Em checkout compartilhado, isole em `git worktree`.
- **Nunca trabalhe dentro do checkout que um gerenciador de plugins serve** (no Claude Code, `~/.claude/plugins/marketplaces/`). Esse diretório é re-clonado — raso — a cada atualização do plugin: branch, commit não pushado e arquivo não rastreado somem sem aviso, e a reflog fica só com `clone`. Use clone próprio ou `git worktree`.
- **Fim de etapa = commit + PR.** Uma branch por etapa; não acumule etapas num único PR. **PR > 500 linhas é anti-padrão.**
- **Merge por squash** — histórico da base = 1 commit por PR; a mensagem do squash segue Conventional Commits.
- **PR aberto é PR vivo.** Título e descrição valem para o que está na branch **agora**, não para o primeiro commit. Chegou commit que amplia ou desvia o escopo? Acerte os dois **antes de pedir revisão ou mergear** — é releitura no fim, não edição a cada push, que ninguém sustenta. O título é o que tem efeito permanente: com mais de um commit, o squash leva o **título do PR** para a base (com um só, prevalece a mensagem dele). Já as mensagens de commit não se perdem — em `squash_merge_commit_message=COMMIT_MESSAGES`, default do GitHub, elas vão inteiras para o corpo do commit final; o que o PR carrega sozinho é a leitura do conjunto.
- **Higiene pós-merge:** apague a branch mergeada local (`git branch -d`) e remota (`git push origin --delete` + `git fetch --prune`). **Nunca apague a `main`.**
{{se rastreável: - Todo `fix` abre um issue de rastreamento; a PR referencia `Closes #N`.}}
- Cuidado com `[skip ci]`: alguns provedores (Cloudflare Pages/Workers) honram e pulam o build.
```

---

## MÓDULO: co-author — OPCIONAL (toggle). Incluir se o usuário pedir OU se o ambiente exigir Co-Authored-By.

```markdown
### Assinatura de commit (opcional)

- Commits gerados com apoio do Claude podem levar rodapé `Co-Authored-By: Claude <noreply@anthropic.com>`.
- Em PRs, registrar o modelo real (ex.: "Claude Opus 4.x") e um split honesto `<XX>% AI / <YY>% Human` que reflita de fato o balanço de contribuição.
```

---

## MÓDULO: docs-sdd — Incluir quando: projeto com governança (app, backend, site). "leve" em site pequeno; "HANDOFF só" em dados.

```markdown
## Documentação (Spec-Driven Development)

Estrutura em `docs/` (ou `.claude/`): PRD magro + pastas especializadas onde o detalhe cresce.

- **ADRs** (`docs/adrs/ADR-NNNN-titulo.md`) — formato Nygard (Context / Decision / Consequences), numeração de 4 dígitos. **Imutáveis após `Accepted`**: mudou a decisão? crie uma nova ADR com `Supersedes ADR-XXXX` e marque a antiga `Superseded by`. Crie ADR quando a **renúncia de uma alternativa** precisa registrar o *porquê*.
- **Specs** (`docs/specs/`) — contratos técnicos (ports, fluxos, erros). Referenciam o RF/ADR, não duplicam a justificativa. Atualize o `INDEX.md`/`README.md` da pasta **no mesmo PR**.
- **IDs estáveis e citáveis** — `RN-NNN` (regra de negócio), `RNF-NNN`, `DEP-NNN`, `ADR-NNNN`. São referenciados em vários arquivos: mantenha-os estáveis.
- **Regra de propagação:** mudou uma regra de negócio? atualize o `DATA_DICTIONARY.md` **e** o serviço correspondente **na mesma mudança**. Valor concreto duplicado em vários arquivos é governado pelo manifesto `deps.toml` (dono → espelhos sancionados) e validado pela skill `guarding-doc-integrity` como **gate pré-commit** (hook versionado opt-in, oferecido no bootstrap da skill) **e gate de sessão** — grep ad-hoc não é garantia, o script é.
- **`HANDOFF.md`** — diário de bordo em duas camadas (ADR-0025): a raiz é **índice fino** (teto ~30 linhas — "Agora" + links das sessões recentes) e cada sessão com progresso real vira um arquivo em **`.claude/handoffs/HANDOFF_<topico>_<AAAA>_<MM>_<DD>.md`** (template `handoff-sessao.md` da skill `handoff`), focado em intenção e progresso — o arquivo da sessão nunca é podado. Em conflito de merge, mantenha a **união das verdades** — nunca sobrescreva progresso de outra sessão.
- **`debts/`** — registro canônico de débito, pendências e lições, **um arquivo por item** (modelo ADR-0030 do deltaspec): ativo em `debts/ativos/DEBT_DT-NNN-<topico>.md` com frontmatter (`id`, `natureza`, `estado`, `fila` só com os eixos `P·J·Pr` — o score é derivado na leitura, nunca gravado —, `descricao`, `aberto`) e campos `- **Local/Gatilho/Origem/Ticket:**` no corpo. Cadastro é `debito.py novo`, nunca edição à mão: o comando calcula o `DT-NNN`, escreve o formato e relê o que escreveu — item inválido não fica no disco. Item quitado/descartado **muda de lugar, nunca some**: frontmatter ganha o estado final e `encerrado`, e o arquivo move (`git mv`) para `debts/_archive/DEBT_DT-NNN-<topico>_<AAAA>_<MM>_<DD>.md` no mesmo commit (links não mudam — mesma profundidade). IDs `DT-NNN` globais, contando as duas pastas. Lições vivem em `debts/licoes/`, uma por arquivo (`licao.py nova`, nunca à mão), imutável — reincidência é lição nova; `debts/LICOES.md` é índice gerado (`licao.py indice`). Regras de leitura em `debts/README.md`. Issue/ticket referencia o DT, nunca o substitui. Registro legado (`DEBT.md`) converte com `debito.py migrar`.
- **Documentação em camadas:** leia o `CLAUDE.md` mais próximo do que você toca; cada subpasta relevante tem o seu.
```

---

## MÓDULO: sdd-ciclo — Incluir quando: tipo com ciclo (app-web, backend, tooling; reduzido em site-estatico). Pular em workspace-dados.

```markdown
## Ciclo de features (deltaspec)

- **1 feature = 1 delta spec** em `specs/NNN-nome/` (`spec.md`, `plan.md`, `tasks.md`), conduzida pelo comando `/deltaspec:spec-feature`. Numeração `NNN` **global ao repositório, nunca reinicia** — é ID estável citado em ADRs, commits e TRUTH.md.
- **Estados: proposta → aplicada → arquivada.** Delta arquivada move para `specs/_archive/` e consolida no **`TRUTH.md`** — a fonte da verdade do que vige (deltas antigas são histórico, não verdade). Archive faz parte do "pronto".
- **Só o que muda:** a delta declara ADICIONA/MUDA/REMOVE em relação ao TRUTH.md; todo requisito tem cenário DADO/QUANDO/ENTÃO verificável.
- **Planos de implementação: salvar em `specs/NNN-nome/plan.md`** (nunca em `docs/superpowers/plans/` — esta linha é a preferência de local que o writing-plans honra).
{{se ciclo reduzido (site-estatico): - **Ciclo reduzido:** specify → plan → implement → review; clarify e analyze sob demanda.}}
```

---

## MÓDULO: clean-code — SEMPRE (ajuste exemplos ao stack)

```markdown
## Clean Code

- **Regra de negócio fora da UI:** cálculos vivem numa camada de domínio/serviços ({{ex.: `src/core/services/`}}), consumida pela apresentação. A UI não reimplementa nem acessa persistência direto.
- **Não duplicar lógica:** uma função/módulo-fonte por responsabilidade; todos os chamadores passam por ela.
- **Zero valor mágico → tokens/constantes.** {{web: cor/espaçamento/fonte via design tokens em CSS custom properties; nada de valores soltos.}}
- **Zero dependência supérflua (YAGNI/DRY):** prefira stdlib e recursos nativos; não adicione framework/lib onde uma função resolve. "É regex, não Handlebars — mantenha simples."
- **Funções puras separadas de I/O** (testáveis sem mock).
- **Não refatore código vendored/gerado** (ex.: primitivas shadcn/ui) — adicione via CLI, preserve o padrão upstream. **Nunca edite output de build** (será sobrescrito).
- **Corrija a causa, não suprima o warning.** Disable de linter é último recurso, sempre com comentário justificando. **Rode o lint antes do push.**
- **Nomenclatura:** kebab-case descritivo em arquivos/scripts (com shebang quando executável).
```

---

## MÓDULO: testing — Incluir quando: há código testável. Pular em site puro/dados.

```markdown
## Testes

- **Co-localização:** teste ao lado do código ({{`faturaService.test.ts`}}). A camada de dados/domínio é a de **maior ROI** para testes unitários.
- {{se TDD: **TDD** onde a lógica é pura e o contrato é claro (parsers, serviços, formatadores).}}
- **Comandos:** {{`npm run test` (vitest) · `npx playwright test` (e2e) · `tsc --noEmit` · `npm run lint`}}.
- Ao mudar um schema/contrato, atualize consumidores **e** testes juntos.
- Onde não há framework de testes, **o CI valida as convenções** (commits, changelog, formato) e reprova o PR fora do padrão.
```

---

## MÓDULO: security — SEMPRE (subset conforme stack)

```markdown
## Segurança

- **Secrets nunca versionados:** `.env` no `.gitignore` (+ `chmod 600` local) → em produção viram GitHub Secrets / Key Vault / Doppler.
- **Dados sensíveis/PII fora do git** — nunca relaxe esse `.gitignore`. **Nunca cole dado real** em commit, PR, issue ou ferramenta externa. Sem telemetria/cloud-sync não solicitados.
- **Validação nas duas pontas** (ex.: Zod no client e no server); degradação graciosa (persistir o dado mesmo se um efeito colateral secundário falhar).
- {{se auth: senhas com bcrypt ≥ 10 rounds; chaves/API keys criptografadas em repouso (AES-256), nunca expostas ao frontend; rate limiting por IP e por usuário.}}
- **Least privilege / defesa em profundidade:** allowlist de tools MCP só-leitura, `deny` vence, hooks `PreToolUse`/`Stop` para bloquear ações de escrita não previstas.
- **Supply chain:** GitHub Actions **pinadas por SHA** (+ comentário da versão).
- {{se servidor local: bind em `127.0.0.1` + token aleatório por start (`secrets.token_urlsafe`), comparação em tempo constante (`compare_digest`), writes atômicos `0600`, guarda de `Origin`, headers `nosniff`/`X-Frame-Options: DENY`.}}
- {{se web público: consent mode LGPD (analytics só após aceite); scraping respeita `robots.txt`.}}
```

---

## MÓDULO: i18n-format — Incluir quando: há UI ou saída formatada para usuário

```markdown
## Idioma, moeda e datas

- Todo texto de UI, comentário, log e doc em **{{idioma, ex.: PT-BR}}** salvo indicação contrária.
- **Moeda/data via helper único** (ex.: `Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" })`) — nunca formatar `R$` à mão. Datas ISO internas (`AAAA-MM-DD`), exibição `DD/MM/AAAA`.
- Em Markdown, escape valores monetários como `\$` (senão Obsidian/GitHub interpretam como LaTeX).
- **Acessibilidade é requisito** (web): `label` em todo input, `aria-label` em controles, navegação por teclado, `skip-to-content`, alvos de toque ≥ 44px, mobile-first.
```

---

## MÓDULO: architecture — Incluir quando: app/backend com estrutura em camadas

```markdown
## Arquitetura

- **Camadas explícitas** ({{ex.: `core/` domínio · `features/` telas · `shared/` reutilizáveis}}). O `core/` não depende de framework/SDK (estilo Hexagonal / Ports & Adapters quando fizer sentido).
- **Interface + provider** só quando há troca real de implementação (default funcional + stub externo, ativado por env var) — não abstraia por especulação.
- **Efeitos colaterais não-bloqueantes** quando aceitável: `void Promise.allSettled([...])`.
- **Regra de negócio configurável** lida dinamicamente (cache TTL), nunca hardcoded.
- **Fontes vs. derivados:** trate binários/fontes como verdade; leia/derive saídas regeneráveis por script em vez de mutar os originais.
```

---

## MÓDULO: data-workspace — Incluir quando: workspace de análise de dados (substitui release-triad/testing)

```markdown
## Convenções de workspace de dados

- **Fontes vs. derivados:** binários (`assets/`) são a fonte da verdade; o texto derivado (CSV/MD) fica na raiz. **Leia o derivado; trate `assets/` como insumo.** Não reexporte sem necessidade.
- **Economia de tokens:** localize com `grep` nos CSVs e leia só as linhas relevantes em vez de re-parsear milhares de linhas a cada vez.
- **Sem tríade de release / sem suíte de testes** (não há build). Cada camada de dados entra em seu próprio commit.
- Derivados (`*.json` de dashboard) são regeneráveis; `node_modules/`, `dist/` no `.gitignore`.
```
