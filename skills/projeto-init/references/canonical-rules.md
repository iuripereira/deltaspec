# Regras canônicas — compilado das melhores práticas

Fonte da verdade das regras do `projeto-init`. Cada módulo abaixo é uma **seção montável** do `CLAUDE.md` gerado. Monte na ordem em que aparecem aqui. Só inclua um módulo se a marca **Incluir quando** casar com o projeto (ver `detection.md` para a matriz por tipo).

Placeholders `{{assim}}` são preenchidos a partir da inspeção do projeto. Os toggles `{{se houver develop: ...}}` e `{{se não houver develop: ...}}` resolvem-se pela **topologia planejada** — a decidida na detecção e confirmada no plano —, não pela existência da branch naquele momento: a `develop` só nasce depois, no `projeto-infra` (regra no passo 3 da `SKILL.md`). Texto em PT-BR — é o idioma padrão de todos os projetos do usuário; o cabeçalho boilerplate fica em inglês por convenção.

---

## MÓDULO: header — SEMPRE

<!-- teste de poda: sem este módulo o CLAUDE.md gerado não diz o que o projeto é, em que stack nem em que idioma responder — o agente adivinha os três na primeira linha de código. O `# CLAUDE.md` é o único h1 do arquivo gerado: sem ele, todo consumidor acende o MD041 do markdownlint; os demais módulos param no `##`. -->

```markdown
# CLAUDE.md

> This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**{{nome_do_projeto}}** — {{uma linha: o que é o projeto}}. Stack: {{stack}}. Idioma do projeto: **{{idioma, ex.: PT-BR}}**.
```

---

## MÓDULO: core — SEMPRE (o núcleo inegociável, difundido em todos os projetos)

<!-- teste de poda: sem este módulo o agente duplica o mesmo número em três arquivos, inventa regra de negócio onde a spec cala, esconde o atalho em vez de registrá-lo — e trata este arquivo como trava, prometendo o que nenhum gate impõe. -->

```markdown
## Princípios inegociáveis

- **Este arquivo orienta, não trava:** regra que precisa ser garantida vira hook em `.claude/hooks/` ou gate de CI. O que está escrito aqui é lido a cada sessão, não imposto — e por isso promete só o que algum gate cobra.
- **Fonte canônica única (regra de ouro):** cada informação tem **um** dono. Referencie, não duplique: valor concreto (número, regra, tipo) vive no arquivo dono, todo o resto linka. Duplicação inevitável é **documentada**, com instrução de manter em sincronia.
- **Parar e perguntar em ambiguidade:** o PRD/spec é soberano sobre regra de negócio. Ambíguo? **Pare e pergunte** — não invente regra.
- **Débito honesto:** valor hardcoded, duplicação e anti-padrão conhecido são **documentados** (com "quando/como corrigir"), nunca escondidos.
- **Idioma:** documentação e mensagens de commit em **{{idioma}}** salvo indicação contrária. {{Se técnico: identificadores e comentários de código em inglês; senão, comentários também em {{idioma}}.}}
- **Doc no mesmo change:** mudança relevante de comportamento atualiza a doc mais próxima e o fato `agora-*` em `.claude/memory/` (regenerando a projeção com `memoria.py indice`; rota legada: o índice `HANDOFF.md` à mão) no mesmo commit, para que sempre reflitam a realidade.
```

---

## MÓDULO: release-triad — Incluir quando: projeto versionável (app, lib, site com releases). Pular em workspace de dados.

<!-- teste de poda: sem este módulo o agente bumpa a versão no package.json, redige o CHANGELOG a partir dos commits e cria a tag à mão — três fontes de verdade disputando cada release. Dono de duas âncoras do deps.toml (`200 caracteres` e a linha `Tipos:`): frase-âncora se cola, não se redige. -->

```markdown
## Versionamento, Changelog e Commits (tríade de release)

- **SemVer 2.0.0:** versões `MAJOR.MINOR.PATCH`. **A tag git `vX.Y.Z` é a fonte da verdade da versão**, não o `package.json` (fica `private` e pode não ser bumpado a cada PR).
- **Keep a Changelog 1.0.0:** toda mudança notável entra no `CHANGELOG.md` da raiz, agrupada em `Adicionado / Mudado / Corrigido / Removido / Obsoleto / Segurança`.
- **A PR não edita o `CHANGELOG.md`:** ela deixa um fragmento de uma linha em `changelog.d/<slug>.<categoria>.md`. O fragmento é o dono do texto em qualquer fase; `montar_changelog.py` acrescenta os fragmentos ao `## [Não lançado]` (o bullet que já estava fica) e os apaga. Dois arquivos com nomes diferentes nunca conflitam; uma seção editada por duas PRs conflita a cada merge.
- **A liberação é do `montar_changelog.py --liberar X.Y.Z`,** chamado por `/deltaspec:criar-release` na branch de release: renomeia `[Não lançado]` → `## [X.Y.Z] - AAAA-MM-DD`, abre um `[Não lançado]` novo e escreve o link de comparação por versão no rodapé (`[1.29.0]: <repo>/compare/v1.28.0...v1.29.0`). Mesma contagem de bullets antes e depois.
- **A versão é input humano:** o argumento de `/deltaspec:criar-release X.Y.Z` tem de ser o sucessor imediato da última tag no nível de bump que os commits desde ela exigem (hotfix = PATCH; `versao_corte.py` valida). Nenhuma ferramenta gera texto de CHANGELOG a partir de commits. **Nunca dois escrevendo o CHANGELOG.**
- **A entrada é uma linha e o PR conta a história:** bullet de uma frase, no máximo 200 caracteres, terminando com a referência do PR — `- Skills de efeito colateral viram manual-only (#227)`; vários PRs no mesmo parêntese (`(#227, #228)`); quebra de compatibilidade abre com `**BREAKING**` e fica no topo da subseção. Porquê, medição, renúncia e IDs de delta/débito/requisito **ficam fora** — o dono é o PR, a delta arquivada e a ADR. Repositório sem remoto omite a referência; mudança sem efeito observável para quem consome não vira entrada.
- **Release publicado só muda de forma:** condensar uma entrada lançada para o formato acima é reprojeção, não reescrita de história; o **nome de época** que ela cita (nome antigo do projeto, arquivo já renomeado, número medido) nunca muda.
- **Conventional Commits 1.0.0:** `tipo(escopo): descrição`. Tipos: `feat fix docs refactor chore ci test style perf build revert`. Breaking via `!` ou rodapé `BREAKING CHANGE:`.
- **Correlação commit → bump:** `fix` = PATCH · `feat` = MINOR · `!`/`BREAKING CHANGE` = MAJOR; o maior vence. PR só de documentação não gera tag.
- **Tag e Release são da skill `/deltaspec:release`, no merge da PR de release/hotfix{{se houver develop: , que também faz a sync `main → develop` por `sync/X.Y.Z` com a guarda do CHANGELOG por conjunto de bullets}} — nunca à mão.** Única exceção: a versão lançada antes da adoção, sem PR de release, que o dono taggeia no commit que a lançou (a `/deltaspec:criar-release` documenta).
{{se houver develop: - **Origem do corte:** `/deltaspec:criar-release X.Y.Z` corta `release/X.Y.Z` da `develop`; `--hotfix` corta da `main`.}}
{{se não houver develop: - **Origem do corte:** `/deltaspec:criar-release X.Y.Z` corta da `main`; a PR de release entra por squash.}}
{{se houver CI: - **Valide no CI:** um job reprova PR com commit fora do padrão; `check_changelog.py` reprova entrada fora do formato (categoria, tamanho, referência de PR, ordenação, rodapé). Fluxo sem PR roda o gate com `--sem-pr`.}}
```

---

## MÓDULO: git-workflow — Incluir quando: projeto usa git (quase sempre). Versão "leve" em workspace de dados. A assinatura de commit é o toggle `{{se co-author}}` — ligue se o usuário pedir ou se o ambiente exigir `Co-Authored-By`.

<!-- teste de poda: sem este módulo o agente commita direto na main, mistura escopos numa branch, abre PR gigante e deixa branch morta no remoto; o bullet squash × merge commit é o que mantém `main ⊆ develop`. Dono da âncora `500` do deps.toml: a frase do limiar se cola, não se redige. -->

```markdown
## Fluxo de trabalho Git

- **`main` protegida e sempre lançável.** Merge só via PR com checks verdes.
{{se houver develop: - **Topologia com `develop`:** `feature/*`, `fix/*` e `bugfix/*` saem da `develop` e voltam a ela por PR; `release/X.Y.Z` sai da `develop` e entra na `main`; `hotfix/*` sai da `main`. A sync `main → develop` é da skill `/deltaspec:release`, nunca à mão — só ela mantém `main ⊆ develop`.}}
{{se não houver develop: - **Topologia sem `develop`:** PR de escopo direto na `main`, por squash; o corte de release parte da `main`.}}
- **Branch por escopo:** `tipo/descrição-curta` em kebab-case (`feat/agenda-recorrente`, `fix/fuso-horario`). **1 sessão = 1 branch** — trabalho de outro escopo é outra branch.
- **`git pull` antes de ramificar ou alterar.** Checkout compartilhado? Isole em `git worktree`.
- **Nunca trabalhe no checkout que um gerenciador de plugins serve** (no Claude Code, `~/.claude/plugins/marketplaces/`): ele é re-clonado, raso, a cada atualização do plugin — branch, commit não pushado e arquivo não rastreado somem sem aviso, e a reflog fica só com `clone`. Use clone próprio ou `git worktree`.
- **Fim de etapa = commit + PR.** Uma branch por etapa; não acumule etapas num único PR. **PR > 500 linhas é anti-padrão.**
- **Merge por squash na PR de escopo:** a base ganha 1 commit por PR, com mensagem em Conventional Commits.{{se houver develop:  `release/*`, `hotfix/*` e `sync/*` entram por **merge commit** (ADR-0045 do deltaspec) — o squash apagaria a delimitação do release e a ancestralidade que mantém `main ⊆ develop`.}}
- **PR aberto é PR vivo:** título e descrição valem para o que está na branch **agora**. Commit que amplia ou desvia o escopo → releia os dois **antes de pedir revisão ou mergear**, não a cada push. Com mais de um commit, o squash leva o **título do PR** para a base; as mensagens de commit sobrevivem no corpo (`squash_merge_commit_message=COMMIT_MESSAGES`, default do GitHub).
- **Higiene pós-merge:** apague a branch mergeada local (`git branch -d`) e remota (`git push origin --delete` + `git fetch --prune`). **Nunca apague a `main`{{se houver develop:  nem a `develop`}}.**
{{se rastreável: - **Todo `fix` abre um issue de rastreamento;** a PR referencia `Closes #N`.}}
- **Cuidado com `[skip ci]`:** alguns provedores (Cloudflare Pages/Workers) honram e pulam o build.
{{se co-author: - **Assinatura de commit:** commit gerado com apoio do Claude leva o rodapé `Co-Authored-By: Claude <noreply@anthropic.com>`; a PR registra o modelo real (nome e versão) e um split honesto `<XX>% AI / <YY>% Human` que reflita o balanço de contribuição.}}
```

---

## MÓDULO: mapa-docs — Incluir quando: as mesmas células do `docs-sdd`. Cada bullet entra só se o arquivo que ele linka existe depois do scaffold (matriz de scaffold do `detection.md`): link sem alvo não entra.

<!-- teste de poda: sem este módulo o agente procura a verdade no lugar errado — varre a delta antiga em vez do TRUTH, recria decisão que já tem ADR, cadastra débito sem ler o registro — e, ao documentar algo novo, usa `@import`, que carrega o arquivo inteiro em toda sessão. -->

```markdown
## Onde vive cada verdade

Cada assunto tem um arquivo dono: leia-o antes de agir sobre o assunto. Doc nova entra aqui como link markdown comum, nunca `@import` — import carrega o arquivo inteiro em toda sessão.

- **Requisito vigente:** [specs/TRUTH.md](specs/TRUTH.md)
- **Decisão e a alternativa renunciada:** [docs/adrs/](docs/adrs/)
- **Débito, pendência e lição:** [debts/README.md](debts/README.md)
- **Onde cada frente parou:** [HANDOFF.md](HANDOFF.md), projeção gerada de `.claude/memory/`
- **O que mudou em cada versão:** [CHANGELOG.md](CHANGELOG.md)
- **Termo de domínio:** [GLOSSARY.md](GLOSSARY.md)
- **Campo de dado:** [DATA_DICTIONARY.md](DATA_DICTIONARY.md)
- **Documentação visual exigida:** [doc-profile.yaml](doc-profile.yaml)
- **Regra por tipo de arquivo:** [.claude/rules/](.claude/rules/)
```

---

## MÓDULO: docs-sdd — Incluir quando: projeto com governança (app, backend, site). "leve" em site pequeno; "HANDOFF só" em dados. O registro de débitos e lições é o módulo `debitos`, logo abaixo.

<!-- teste de poda: sem este módulo o agente edita ADR aceita em vez de supersedê-la, renumera ID que outros arquivos citam, propaga regra de negócio só no código e guarda o estado da frente na conversa, onde a próxima sessão não o acha. -->

```markdown
## Documentação (Spec-Driven Development)

Estrutura em `docs/` (ou `.claude/`): PRD magro + pastas especializadas onde o detalhe cresce.

- **ADRs** (`docs/adrs/ADR-NNNN-titulo.md`) — formato Nygard (Context / Decision / Consequences), numeração de 4 dígitos. **Imutáveis após `Accepted`**: mudou a decisão? crie uma nova ADR com `Supersedes ADR-XXXX` e marque a antiga `Superseded by`. Crie ADR quando a **renúncia de uma alternativa** precisa registrar o *porquê*.
- **Specs** (`docs/specs/`) — contratos técnicos (ports, fluxos, erros). Referenciam o RF/ADR, não duplicam a justificativa. Atualize o `INDEX.md`/`README.md` da pasta **no mesmo PR**.
- **IDs estáveis e citáveis** — `RN-NNN` (regra de negócio), `RNF-NNN`, `DEP-NNN`, `ADR-NNNN`. São referenciados em vários arquivos: mantenha-os estáveis.
- **Regra de propagação:** mudou uma regra de negócio? atualize o `DATA_DICTIONARY.md` **e** o serviço correspondente **na mesma mudança**. Valor concreto duplicado em vários arquivos é governado pelo manifesto `deps.toml` (dono → espelhos sancionados) e validado pela skill `guarding-doc-integrity` como **gate pré-commit** (hook versionado opt-in, oferecido no bootstrap da skill) **e gate de sessão** — grep ad-hoc não é garantia, o script é.
- **Memória de projeto** (`.claude/memory/`, ADR-0050 do deltaspec) — um arquivo por fato; **grave o fato com a ferramenta Write em `.claude/memory/<name>.md` no momento em que ele nasce — não no fim da sessão**. `MEMORY.md` e `HANDOFF.md` são **projeções geradas** (`memoria.py indice`, nunca à mão). Um fato `agora-<frente>` por frente aberta, atualizado no lugar e apagado quando a frente fecha. Fronteira: decisão com renúncia → ADR; débito/lição → `debts/`; requisito → delta (formato e convenções na skill `memoria`). `.claude/handoffs/`, se existir, é histórico congelado (nunca podado). Em conflito de merge na memória, regenere o índice. Repo sem `.claude/memory/` (índice `HANDOFF.md` escrito à mão): a skill `handoff` oferece a migração por `semear.py`; recusada, siga a rota legada e não crie a pasta à mão.
- **Documentação em camadas:** leia o `CLAUDE.md` mais próximo do que você toca; cada subpasta relevante tem o seu.
```

---

## MÓDULO: debitos — Incluir quando: o scaffold cria `debts/` (herda as células do `docs-sdd`). Pular em workspace de dados.

<!-- teste de poda: sem este módulo o agente pega o atalho sem registrá-lo, inventa o `DT-NNN` à mão, edita o índice gerado, refatora área estável por gosto em vez de quitar onde já está mexendo — e fecha a PR sem o vínculo com o ticket. -->

```markdown
## Débitos e lições

- **Atalho vira DT no mesmo commit:** valor hardcoded, duplicação, teste pulado ou contorno entram no registro no commit que os introduz, não "depois".
- **Consulte `debts/` antes de mexer numa área:** item ativo naquela área é quitado ali, de carona na mudança — pagamento oportunista é o barato. Área estável e ruim fica quieta, sem refatoração por gosto.
- **Classifique pelo quadrante, com juro em unidade concreta:** o corpo do item diz se o débito foi deliberado ou inadvertido, prudente ou imprudente. O juro é atrito já observado (dias a mais numa feature, incidente, retrabalho), não hipótese, e é ele que sustenta o eixo `J` da `fila`.
- **Um arquivo por item:** débito e pendência vivem em `debts/ativos/DEBT_DT-NNN-<topico>.md`, com frontmatter (`id`, `natureza`, `estado`, `fila` só com os eixos `P·J·Pr` — o score é derivado na leitura, nunca gravado —, `descricao`, `aberto`). Cadastro é `debito.py novo`, nunca edição à mão: o comando calcula o `DT-NNN` (global, contando ativos e arquivados), escreve o formato e relê o que escreveu.
- **Encerrado muda de lugar, nunca some:** item quitado ou descartado vai para `debts/_archive/` por comando, no mesmo commit. A PR que quita DT com Ticket carrega o vínculo que o `debito.py quitar` imprime (`Closes #N`, ou a chave do Jira), conferido no CI pelo `debito.py vinculo` — que também exige uma linha `Quita DT-NNN` (ou `Descarta DT-NNN`) por DT arquivado e reprova citação sem arquivo movido.
- **Lições:** vivem em `debts/licoes/`, uma por arquivo (`licao.py nova`, nunca à mão), imutáveis — reincidência é lição nova.
- **Índice é projeção:** `DEBT.md` (`debito.py indice`) e `debts/LICOES.md` (`licao.py indice`) são gerados. Regenere depois de cadastrar ou quitar; nunca edite à mão.
- **Ticket é projeção:** issue ou chave do Jira referencia o DT, nunca o substitui.
- **Detalhe no `debts/README.md`:** naturezas, estados, formato da lição e regra de leitura vivem lá, não aqui. Registro legado (blocos `### DT-NNN` no `DEBT.md`) converte com `debito.py migrar`.
```

---

## MÓDULO: sdd-ciclo — Incluir quando: tipo com ciclo (app-web, backend, tooling; reduzido em site-estatico). Pular em workspace-dados.

<!-- teste de poda: sem este módulo o agente implementa o pedido de feature direto, sem delta, salva o plano fora de `specs/NNN-nome/` e trata delta antiga como regra vigente. As frases do bloco são o gatilho de invocação da `spec-feature` e do `writing-plans`: copie byte a byte, nunca resuma. -->

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

<!-- teste de poda: sem este módulo o agente põe cálculo no componente, repete o mesmo número em quatro arquivos, instala lib para uma função e silencia o linter em vez de corrigir a causa. -->

```markdown
## Clean Code

- **Regra de negócio fora da UI:** cálculo vive na camada de domínio/serviços ({{ex.: `src/core/services/`}}); a apresentação consome, não reimplementa nem acessa persistência direto.
- **Não duplicar lógica:** uma função/módulo-fonte por responsabilidade; todos os chamadores passam por ela.
- **Zero valor mágico → constantes nomeadas.** Nenhum número solto repetido. {{web: cor/espaçamento/fonte via design tokens em CSS custom properties.}}
- **Zero dependência supérflua (YAGNI/DRY):** stdlib e recurso nativo primeiro; não adicione framework/lib onde uma função resolve.
- **Funções puras separadas de I/O** — testáveis sem mock.
- **Não refatore código vendored/gerado** (ex.: primitivas shadcn/ui): adicione via CLI e preserve o padrão upstream. **Nunca edite output de build** — será sobrescrito.
- **Corrija a causa, não suprima o warning:** disable de linter é último recurso, sempre com comentário justificando. **Lint antes do push.**
- **Nomenclatura:** kebab-case descritivo em arquivos/scripts (com shebang quando executável).
```

---

## MÓDULO: testing — Incluir quando: há código testável. Pular em site puro/dados.

<!-- teste de poda: sem este módulo o agente cria `tests/` longe do código, muda o contrato sem tocar o teste e dá o PR por pronto sem rodar a suíte. -->

```markdown
## Testes

- **Co-localização:** teste ao lado do código ({{`faturaService.test.ts`}}); a camada de dados/domínio é a de **maior ROI** para teste unitário.
{{se TDD: - **TDD** onde a lógica é pura e o contrato é claro (parsers, serviços, formatadores).}}
- **Comandos:** {{`npm run test` (vitest) · `npx playwright test` (e2e) · `tsc --noEmit` · `npm run lint`}}.
- **Schema/contrato mudou? Consumidores e testes mudam juntos**, no mesmo change.
- **Sem framework de testes, o CI valida as convenções** (commits, changelog, formato) e reprova o PR fora do padrão.
```

---

## MÓDULO: security — SEMPRE (subset conforme stack)

<!-- teste de poda: sem este módulo o agente commita o `.env`, cola dado real num issue "para ilustrar" e aponta a Action por tag mutável. -->

```markdown
## Segurança

- **Secrets nunca versionados:** `.env` no `.gitignore` (+ `chmod 600` local); em produção viram GitHub Secrets / Key Vault / Doppler.
- **Dados sensíveis/PII fora do git:** nunca relaxe esse `.gitignore`; **nunca cole dado real** em commit, PR, issue ou ferramenta externa; sem telemetria/cloud-sync não solicitados.
- **Validação nas duas pontas** (ex.: Zod no client e no server); degradação graciosa — o dado persiste mesmo se um efeito colateral secundário falhar.
{{se auth: - **Auth:** senha com bcrypt ≥ 10 rounds; chave/API key criptografada em repouso (AES-256) e nunca exposta ao frontend; rate limiting por IP e por usuário.}}
- **Least privilege / defesa em profundidade:** allowlist de tools MCP só-leitura, `deny` vence, hooks `PreToolUse`/`Stop` bloqueiam escrita não prevista.
- **Supply chain:** GitHub Actions **pinadas por SHA** (+ comentário da versão).
{{se servidor local: - **Servidor local:** bind em `127.0.0.1` + token aleatório por start (`secrets.token_urlsafe`), comparação em tempo constante (`compare_digest`), writes atômicos `0600`, guarda de `Origin`, headers `nosniff`/`X-Frame-Options: DENY`.}}
{{se web público: - **Web público:** consent mode LGPD (analytics só após aceite); scraping respeita `robots.txt`.}}
```

---

## MÓDULO: architecture — Incluir quando: app/backend com estrutura em camadas

<!-- teste de poda: sem este módulo o agente importa o SDK dentro do domínio, cria interface com uma implementação só e hardcoda a regra que o negócio muda toda semana. -->

```markdown
## Arquitetura

- **Camadas explícitas** ({{ex.: `core/` domínio · `features/` telas · `shared/` reutilizáveis}}); o `core/` não depende de framework/SDK (Hexagonal / Ports & Adapters quando fizer sentido).
- **Interface + provider só com troca real de implementação** (default funcional + stub externo, ativado por env var) — não abstraia por especulação.
- **Efeito colateral não bloqueia** quando aceitável: `void Promise.allSettled([...])`.
- **Regra de negócio configurável é lida dinamicamente** (cache com TTL), nunca hardcoded.
- **Fontes vs. derivados:** binários/fontes são a verdade; saída regenerável se deriva por script, nunca mutando o original.
```

---

## MÓDULO: data-workspace — Incluir quando: workspace de análise de dados (substitui release-triad/testing)

<!-- teste de poda: sem este módulo o agente re-parseia a planilha inteira a cada pergunta, edita o binário em vez do derivado e pede CHANGELOG a um repositório de dados. -->

```markdown
## Convenções de workspace de dados

- **Fontes vs. derivados:** binários (`assets/`) são a fonte da verdade; o texto derivado (CSV/MD) fica na raiz. **Leia o derivado; trate `assets/` como insumo.** Não reexporte sem necessidade.
- **Economia de tokens:** localize com `grep` nos CSVs e leia só as linhas relevantes — nunca re-parseie milhares de linhas a cada vez.
- **Sem tríade de release nem suíte de testes** (não há build); cada camada de dados entra no próprio commit.
- **Derivados são regeneráveis** (`*.json` de dashboard); `node_modules/` e `dist/` no `.gitignore`.
```
