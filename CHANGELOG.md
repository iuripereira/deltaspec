# Changelog

Todas as mudanças notáveis deste projeto são documentadas aqui.

O formato segue [Keep a Changelog 1.0.0](https://keepachangelog.com/pt-BR/1.0.0/) e o projeto adere ao [Versionamento Semântico 2.0.0](https://semver.org/lang/pt-BR/). A versão canônica vive nas tags git `vX.Y.Z`.

<!-- Este arquivo nasceu na aplicação do projeto-init ao próprio repo. Mudanças anteriores à sua criação vivem no histórico git; abaixo estão as notáveis ainda não lançadas. -->

## [Não lançado]

### Corrigido

- **O C3 acusava histórico imutável e sintaxe citada** (delta-029, MUDA R13): o check de links passou a **parar na primeira seção de versão lançada** — release publicado é imutável pelo Keep a Changelog, a mesma razão que já mantinha `_archive/` e ADRs fora — e a **ignorar link dentro de crase ou de bloco cercado**, que é sintaxe citada e não referência. Os dois recortes olham o **conteúdo** do arquivo, nunca o nome, então repositório que chame o changelog de outro jeito recebe a mesma proteção. A seção `[Não lançado]` continua verificada: foi nela que estava o link quebrado real que motivou a delta-027. Medido no `imex-travelplanner`, que originou o débito: **96 → 3** links mortos, e os 3 restantes são rot legítimo daquele repositório. Quita **DT-028**, que bloqueava a replicação nos consumidores.

## [1.8.0] - 2026-08-03

### Mudado

- **O `version` saiu do `doc-profile.yaml`** (delta-028, MUDA R12): nenhum consumidor lia o campo e ele já nascera incoerente — o template declarava `version: 1` com as sete categorias, enquanto o único perfil real que tem as sete declarava `version: 2`. Sai do template distribuído e do núcleo que o C11 exige; perfil que ainda o traga **continua válido**, porque chave fora do núcleo nunca foi erro. O `projeto-init` passa a **relatar** perfil atrás do template — categoria de cauda e bloco `motores` ausentes — e só escreve com aprovação explícita, sem tocar em `decisao`, `publico` ou `obrigatorio` já declarados (RNF3).
- **A política de dependência passou a ser verificada pelo mecanismo do próprio framework** (delta-028, MUDA RNF6): o `deps.toml` ganhou `[[owner]]` com dono `CLAUDE.md` e três espelhos, conferido pelo C1 do `validate_integrity.py` no CI **e no pré-commit** — antes era um `grep` à mão no CI, enquanto o repo recomendava o manifesto aos projetos. Coube no teto de 2–3 espelhos porque o `SECURITY.md` passou a apontar para o dono em vez de repetir o identificador da ADR. A metade negativa (nenhum arquivo promete zero-dep) continua como `grep`, agora **declarada como exceção**: o validador não tem check de padrão proibido.

## [1.7.1] - 2026-08-03

### Corrigido

- **O C3 do `validate_integrity.py` deixava `CHANGELOG.md`, `HANDOFF.md`, `DEBT.md` e as ADRs sem verificação de link** (delta-027, MUDA R13): os dois checks compartilhavam o conjunto varrido, então a dispensa de *citar valor* (motivo do C2) virava dispensa de *link vivo* por tabela. Agora cada um tem o seu — `exclude_links_globs` no `deps.toml`, com default nomeado para o histórico imutável (`_archive/`, ADRs), que propaga sem exigir migração de manifesto. Neste repositório o C3 saltou de **105 para 171** links verificados. Junto: o atalho `../../issues/N` do GitHub passou a ser ignorado como `http://` já era — sem isso, os 19 links de issue e PR do `DEBT.md` virariam falso FAIL na primeira execução. O corte casa a **forma** do atalho e não o prefixo `../../`: a primeira versão cortava por prefixo e silenciava 10 links de `SKILL.md`/`references` para ADR, trocando o sinal da mesma patologia que a correção ataca — pego no review.

### Adicionado

- **`doc-profile.yaml` na raiz deste repositório** (DT-024): o framework exigia dos projetos-alvo a decisão registrada de documentação visual ([ADR-0009](docs/adrs/ADR-0009-documentacao-visual-gate-configuravel.md)) e não tinha registrado a sua — dogfood faltando que o próprio C11 acusou na primeira execução. Perfil sem artefato obrigatório, com justificativa preenchida: plugin de skills mais gates, sem UI, sem persistência e sem entregável de cliente; os fluxos do ciclo vivem como Mermaid inline no README.

## [1.7.0] - 2026-08-02

### Adicionado

- **C11 e C12 no gate determinístico** (delta-026): o **C11** valida o schema do `doc-profile.yaml` — exige o núcleo (`version`, `decisao`, `publico`, `artefatos` com as quatro categorias presentes em 7/7 dos perfis reais) e **tolera a cauda opcional**, porque categoria que uma delta acrescenta ao template nunca propaga retroativamente aos projetos já inicializados; também acusa YAML inválido, perfil sem obrigatório e sem justificativa, e `motores.graphify` ligado sem backend. O **C12** exige a trilha do clarify no perfil completo, lida por âncora de início de linha. Nenhum dos dois é CRÍTICO: reportam, não bloqueiam (ADR-0006). Quita **DT-013** e **DT-023**.

### Mudado

- **O clarify não fecha mais sem declarar se teve canal humano** (delta-026, MUDA R8): o `spec.md` passa a carregar `Clarify: entrevistado (data) — N decisões do usuário` ou `Clarify: auto-avaliado (data) — sem canal humano`. Ambiguidade resolvida por exploração do repositório **não conta como resposta do usuário** — o `grill-me` manda explorar em vez de perguntar, e num repo com TRUTH e ADRs isso responde quase tudo, produzindo uma entrevista que nunca acontece. O contrato passou a registrar também o viés de quem redige a spec ser quem pontua o próprio relatório.
- **`PyYAML` passa a ser dependência externa admitida dos gates** (delta-026, [ADR-0023](docs/adrs/ADR-0023-pyyaml-como-dependencia-admitida.md)) — a única. Renunciamos ao parser próprio porque o modo de falha dele é silencioso (um `LIBERADO` falso, exatamente o risco que manteve o DT-013 aberto por cinco semanas) e à degradação graciosa porque ela é contrato para motor opcional, não para o gate. Os **quatro** espelhos da promessa foram atualizados — o `SECURITY.md`, que usava a superfície de cadeia de dependências igual a zero como argumento de modelo de ameaça, só apareceu no review — e o CI passou a instalar a dependência antes do primeiro step que a importa e a verificar a política nos quatro. Sem o pacote, o gate para com mensagem acionável nomeando o comando e a ADR, nunca com traceback; `pip install pyyaml` entrou na seção de instalação do README.

## [1.6.0] - 2026-08-02

### Adicionado

- **Campo `motores.graphify_backend` no template do `doc-profile.yaml`** (delta-025, [ADR-0022](docs/adrs/ADR-0022-backend-do-graphify-registrado-no-perfil.md)): registra qual backend LLM indexa a documentação quando o graphify roda fora do modo só-código. Vazio com indexação de docs pedida faz a IA **parar e perguntar**, nunca assumir um default; em `--code-only` o campo é dispensável.

### Mudado

- **Contrato do graphify passa a ter pin verificado por execução real** (delta-025, MUDA R44 — [ADR-0022](docs/adrs/ADR-0022-backend-do-graphify-registrado-no-perfil.md)): a primeira adoção real aconteceu em 2026-08-02 no `imex-travelplanner`, e a política de versões sai de "não testada" para `0.9.32` com verificação datada. O contrato de proveniência se confirmou; o uso expôs o que a doc upstream não dizia, e o adapter agora declara: o que cada modo entrega **e o que cega**, quais backends indexam documentação sem criar fronteira nova de confiança, e que claim sobre arquivo inexistente entra como `inferido`. A proibição de instalador passou a nomear também o alvo por plataforma `graphify claude install`.
- **A ADR-0022 supersede a ADR-0014 na cláusula "`--code-only` preferido"** (delta-025): a preferência normativa foi gravada a partir da doc upstream, antes de o modo ser exercido; a execução real mostrou que ele cega todo arquivo não-código. A escolha de modo passa a seguir o perfil do projeto-alvo. O resto da ADR-0014 — proibição de auto-install, pin datado, toggle no doc-profile, `tasks.md` dono do grafo — segue vigente.

## [1.5.0] - 2026-08-01

### Mudado

- **O `DEBT.md` vira um bloco por item, com referências navegáveis** (delta-024, MUDA R18/R51): a tabela de 11 colunas da delta-023 tinha linhas de até 1.549 caracteres e um campo `Título` que repetia o início da `Descrição` — ilegível na prática. Cada dívida passa a ser `### DT-NNN · natureza · estado` com título, descrição em prosa livre e campos (`Fila`, `Local`, `Gatilho`, `Origem`, `Ticket`/`Encerrado`), no mesmo padrão dos ADRs. Ticket, PR, issue, delta e artefato agora são **links relativos navegáveis** (`../../issues/N`, `specs/_archive/NNN-*/`), que resolvem no GitHub e sobrevivem a fork. O cabeçalho ganhou a legenda que faltava: uma tabela explicando os cinco estados e o que cada um exige, mais os três eixos da fila. Data e referência de encerramento saíram do rótulo de estado e viraram o campo `Encerrado`, deixando o estado escaneável. Registro ainda em tabela (incluindo o template distribuído pelo `projeto-init`) segue válido: o script avisa como converter em vez de rejeitar.
- **`stale` passa a medir decisão, não edição** (delta-024): como o `DT-NNN` vive só no cabeçalho do bloco, o relógio do aging reinicia quando o **estado** muda — reescrever a descrição não conta mais como "mexeu no item", o que é mais fiel ao que a marca cobra.

## [1.4.0] - 2026-08-01

### Adicionado

- **Dívida técnica com score determinístico e projeção para tickets** (delta-023, R1–R3 — [ADR-0020](docs/adrs/ADR-0020-modelo-de-divida-tecnica.md) e [ADR-0021](docs/adrs/ADR-0021-projecao-de-tickets.md)): o `DEBT.md` ganha `Título`, `Local`, `Fila` (`P·J·Pr`) e `Externo`, mais os estados `aceito`, `vigente` e `descartado`. O score `(juros × probabilidade) / principal` é calculado na leitura pelo novo `skills/handoff/scripts/debito.py` e **nunca gravado**; a probabilidade é conferida contra o churn real do git. O mesmo script exporta o JSON canônico e os dialetos de importação (bulk do Jira, linhas do GitHub) e compara o registro com o estado da ferramenta — **sem tocar a rede**: quem executa os comandos é a skill, no padrão do `projeto-infra`. Política de fila (override, trilha planejada, aging, aceitação) em `skills/handoff/references/debito.md`.
- **A ADR-0021 substitui a ADR-0007 na parte das Issues**, exatamente pela cláusula que a própria ADR-0007 havia escrito: com Issues e Jira entrando em uso, o espelho sancionado deixa de ser renúncia. O file-first permanece — ferramenta de ticket é projeção, a ida é mecânica e a volta só muda o arquivo com aprovação humana. A delta-017 (reservada) reusará este mecanismo no `tickets.md`.

## [1.3.0] - 2026-07-31

## [1.2.0] - 2026-07-31

### Adicionado

- **`status-pmo` ganha o nível épico/tarefa com dependências** (delta-022, R50–R52): novo gate `docs/epicos/<dir>.md` (um épico por etapa do cronograma, tarefas com dependência explícita derivadas dos RFs), página por épico (`etapa-<dir>-eN.html`: tarefas, depende-de/bloqueia, registros, chave do sistema externo) com a etapa do cronograma clicável, e grafo de dependências em SVG inline (camadas por profundidade, tokens CSS, nó clicável, ciclo degrada sem quebrar). Templates: `epicos-template.md` novo, `dados-schema.md` com `jira`/`epicos[]`, e os assets de marca passam a ter **tema claro como padrão** (escuro só pelo toggle). Lições da 1ª revisão do PO no caso de referência (repo imex, delta-003).

- **Skill `status-pmo` — site de status PMO montado sempre da mesma forma** (delta-021, [ADR-0019](docs/adrs/ADR-0019-status-pmo-site-de-status.md)): processo em 6 gates (cronograma canônico com D0/etapas/marcos → ata semanal → gerador stdlib no repo cliente → marca por tokens de CSS → publicação restrita → integração externa trocando só a coleta) + templates em `references/templates/` (`styles-tokens.css` com paleta placeholder, `theme.js`, templates de cronograma e ata, `dados-schema.md` como contrato do `dados.json`). Extração do caso validado no repo imex (deltas 002/003); renúncias registradas na ADR: SaaS/BI de status, gerador genérico no plugin e lib de gráfico (gantt é CSS grid puro).
- **Abertura à comunidade (DT-015): README em inglês, guia de contribuição e código de conduta** — `README.en.md` como espelho sancionado do `README.md` (tradução integral com nota de sincronia e seletor de idioma nos dois); `CONTRIBUTING.md` com o fluxo (fork → branch por escopo → Conventional Commits → PR com checks → squash), a regra do ciclo para mudanças em `skills/` e resumo em EN; `CODE_OF_CONDUCT.md` (Contributor Covenant 2.1, tradução oficial pt-BR). As skills permanecem em PT-BR por convenção registrada no CLAUDE.md.

## [1.1.0] - 2026-07-30

### Adicionado

- **`SECURITY.md` no padrão da comunidade** (pesquisa em claude-code, OpenSpec, Electron e Express): reporte privado via GitHub Security Advisories (nunca issue pública), SLA explícito (confirmação ≤ 3 dias úteis, correção ou decisão ≤ 30 dias), versões suportadas = última tag apenas (sem tabela fictícia de versões), e modelo de ameaça de ferramenta local com tabela escopo/fora de escopo — vulnerabilidade do Claude Code em si é redirecionada ao HackerOne da Anthropic. As práticas de desenvolvimento seguem referenciadas no CLAUDE.md (regra de ouro, sem duplicação).

### Mudado

- **Camada de apresentação troca Figma/FigJam por diagram-design + design-sync** (delta-020, MUDA R45/R46 — [ADR-0018](docs/adrs/ADR-0018-diagram-design-camada-apresentacao.md), supersede a ADR-0015): a decisão do usuário antecipou o gatilho do DT-014 (preço do `generate_diagram`) — o motor remoto beta sai e entra a skill `diagram-design` (diagramas editoriais HTML+SVG brandados, locais e versionáveis em `docs/apresentacao/`), com publicação opcional para stakeholders via `design-sync` (claude.ai/design, incremental e só por pedido). Invariantes mantidos: o `.mmd` segue a única fonte (unidirecional), o entregável congelado segue exclusivo do pipeline CLI, e a degradação graciosa cobre motor ausente. O acabamento agora entra no congelado por caminho reprodutível (`diagram-design:export` → PNG/SVG), eliminando o retoque manual da ADR-0015.
- **README reescrito como quickstart**, mais curto e em linguagem direta: 8 seções (o problema · instalação · comece um projeto · o ciclo · o dia a dia · as skills · as checagens · onde cada coisa mora) em vez do guia longo, com o jargão traduzido ("o que vale hoje" no lugar de "o que vige", "checagem automática" no lugar de "gate determinístico", "roda de novo sem estragar" no lugar de "idempotência defensiva"). As 9 skills viraram **uma tabela que linka para cada `SKILL.md`** — a explicação de cada skill continua com um dono só, o próprio `SKILL.md` (regra de ouro; padrão das Agent Skills), em vez de um `README.md` por skill que duplicaria o texto.
- **Diagramas Mermaid com tema claro**: `theme: base` + `classDef` numa paleta pastel de papel semântico (delta, verdade, gate, fase, fim), nós arredondados e borda escura. A `fontFamily` customizada foi deixada de fora de propósito — o `mmdc` calcula a largura do nó com a fonte disponível e cortava o texto ("ADICIONA R1, R" em vez de "R2"); com a fonte padrão do Mermaid os 6 diagramas renderizam íntegros.

### Removido

- **Seção de migração `sdd-iuri` → `deltaspec` do README** (introduzida pela delta-019/R47): a varredura dos consumidores fechou e o rename está concluído, então o README parte de `deltaspec` e ponto. O registro histórico do rename continua onde tem dono — [ADR-0016](docs/adrs/ADR-0016-rename-deltaspec.md), `specs/_archive/019-rename-deltaspec/` e a seção `[1.0.0]` abaixo.
- **Detalhamento no README que já tem dono em outro arquivo**: a tabela dos checks C1–C10 (dona: `spec-feature/SKILL.md`), a lista de CLIs de diagrama opcionais (dona: `doc-entregavel`) e a seção de convenções do repositório (dona: `CLAUDE.md`) saíram do README, que agora linka para elas. A versão exibida no topo, que apontava `v0.13.0`, passou a `v1.0.0`.

## [1.0.0] - 2026-07-28

### Adicionado

- **Guia de migração e guarda do registro histórico** (delta-019, R47): seção 2.1 do README com os passos exatos para quem vinha do `sdd-iuri`; `specs/_archive/`, ADRs `Accepted` e seções lançadas deste changelog preservam o nome de época — mesma guarda que a delta-010 aplicou no rename `STATE.md` → `HANDOFF.md` (DT-010).
- **ADR-0016**: decisão do nome com as renúncias registradas — `delta-spec` descartado pela colisão de nicho, camada de compatibilidade do `sdd-iuri.validator` descartada por não alcançar hooks já copiados.

### Mudado

- **BREAKING — o framework passa a se chamar `deltaspec`** (delta-019, R1–R5 + RNF1 — [ADR-0016](docs/adrs/ADR-0016-rename-deltaspec.md)): o nome pessoal saiu para abrir o projeto à comunidade. Instalação vira `/plugin marketplace add iuripereira/deltaspec` + `/plugin install deltaspec@deltaspec`, o namespace de invocação vira `deltaspec:` (todos os comandos `/sdd-iuri:*` deixam de existir — sem camada de compatibilidade) e a chave de config do hook pré-commit vira `deltaspec.validator`. `delta-spec` foi descartado por colidir com `codebycorey/delta-spec`, do mesmo nicho. Registro histórico preservado: `specs/_archive/`, ADRs `Accepted` e seções lançadas deste changelog mantêm o nome de época. Guia de migração na seção 2.1 do README.

  BREAKING CHANGE: o namespace de invocação das skills muda de `sdd-iuri:` para `deltaspec:`; consumidores precisam remover o marketplace antigo, reinstalar o plugin e atualizar os comandos citados no próprio `CLAUDE.md`.
- **README reescrito em chave didática**: nova estrutura em 8 seções (por que delta spec · instalação e configuração · como funciona · fluxo sugerido · skills uma a uma · gates · onde cada informação mora · convenções), com a analogia "delta spec = commit de requisito, TRUTH.md = working tree", 6 diagramas Mermaid (consolidação das deltas, estados, ciclo completo, orquestra×motores, greenfield, sessão), tabela dos checks C1–C10 e objetivo declarado de cada uma das 9 skills. Os limiares canônicos (particionamento do TRUTH, tamanho de PR) passaram a ser **referenciados** em vez de materializados — o `validate_integrity.py` acusou a duplicação (C2) e a correção mantém a regra de ouro. Diagramas em Mermaid por decisão da ADR-0015 (Figma é camada de apresentação a cliente, não fonte; FigJam não embeda em README).

## [0.13.0] - 2026-07-28

### Adicionado
- **Figma/FigJam como camada de apresentação a cliente** (delta-018, R1 — ADR-0015): categoria `apresentacao` no doc-profile; fluxo unidirecional Mermaid fonte → `generate_diagram` → retoque (o `.mmd` governa); tipo não suportado → render CLI + imagem no FigJam.
- **Figma MCP nos adapters** (delta-018, R2): linha de contrato com ponto sensível (beta → pago), seção com fallback (RNF2) e política sem pin ("n/a — serviço remoto", verificação datada); entregável congelado permanece exclusivo do pipeline CLI, documentado também na `doc-entregavel`.
- **Reserva explícita de número de delta** (delta-018, R3 — MUDA R5 no archive): o usuário pode reservar/saltar um número, com a reserva citada nos specs (caso real: 017 reservada para a Fase 4/Jira, preservando o gatilho da ADR-0012).
- **ADR-0015**: veredito híbrido com renúncias (Figma como fonte; round-trip) e limitações registradas (beta/preço → DT; export FigJam **não verificado**).

## [0.12.0] - 2026-07-28

### Adicionado

- **Arestas de bloqueio no tasks.md** (delta-016, R1): sintaxe `(dep: Tn[, Tm])` no template; unidades paralelizáveis derivadas do grafo; **C9** valida existência e aciclicidade. Sem `dep:` → cadeia linear implícita (retrocompatível).
- **C10 — convergência mínima no archive** (delta-016, R2): delta arquivada com task `- [ ]` remanescente → ALTO; auditoria semântica codebase×spec segue humana (ADR-0014).
- **Execução paralela por worktree** (delta-016, R3): unidades sem caminho entre si rodam em subagentes com worktree isolada (`superpowers:using-git-worktrees`); degradação sequencial topológica.
- **`references/harness.md`** (delta-016, R4): vocabulário canônico de harness — initializer, agente incremental, gate determinístico, degradação graciosa, human-in-the-loop, trilha de auditoria, unidade paralelizável.
- **Trilha de auditoria de aprovação** (delta-016, R5): toda aprovação humana registrada como linha citável no artefato da própria fase; sem audit.md separado (ADR-0014).
- **graphify como 4º motor externo opcional** (delta-016, R6): contrato nos adapters (instalação manual consciente, `--code-only`, tags → `confirmado`/`inferido`/`lacuna`), toggle `motores.graphify` no doc-profile, fallback grep/Explore.
- **ADR-0014**: renúncias das quatro decisões (audit.md, converge semântico, grafo de tarefas no graphify, auto-install).

### Mudado

- `check_cycle.py` passa a C1–C10 (MUDA R12 no archive) com fixtures novas no selftest; templates `tasks.md` com `dep:`; `cycle.md`/`adapters.md`/`SKILL.md`/README refletem grafo, worktrees, trilha e graphify; `tasks.md` de 6 deltas arquivadas receberam a higiene de checkbox exigida pelo C10 (trabalho já concluído nos merges).

## [0.11.0] - 2026-07-28

### Adicionado
- **Perfil de execução por delta** (delta-015, R1 — ADR-0013): `Perfil: completo|enxuto` no cabeçalho da spec, proposto pela IA e válido só com aprovação do usuário; enxuto = clarify sob demanda, test-plan dispensável, review com eixos fundidos. Sem o campo → completo (retrocompatível).
- **Prototipação opcional** (delta-015, R2): estágio CONDITIONAL proposto no specify; forma decidida pela categoria `prototipo` do `doc-profile.yaml`, default HTML estático em `docs/prototypes/NNN-nome/`.
- **Plano de testes como artefato** (delta-015, R3): `test-plan.md` derivado da spec + tasks (template novo), validado pelo **C8** do `check_cycle.py` — cobertura Rn/RNFn → caso, teste manual roteirizado conta.
- **Tipo `bugfix`** (delta-015, R4): template próprio (sintoma, reprodução, causa-raiz, teste de regressão obrigatório), pipeline curto, TRUTH consolidado só quando muda requisito; gate reconhece `Tipo: bugfix`.
- **ADR-0013**: renúncias das três decisões de desenho (composição do enxuto, forma do protótipo, pipeline do bugfix).

### Mudado
- `check_cycle.py` passa a C1–C8 (MUDA R12 no archive) com fixtures novas no selftest; R35 ganha exceção de fusão de eixos no perfil enxuto (MUDA R35 no archive); templates `delta-spec.md` com campo `Perfil`; `cycle.md`/`SKILL.md`/`adapters.md`/`analyze.md`/README refletem o pipeline novo.

## [0.10.0] - 2026-07-28

### Adicionado
- **ADR-0012** (delta-014): pin do `max@0.8.0` vira **fork deliberado**, com gatilho de migração na delta-017 — divergência e renúncias registradas na própria ADR.
- **Review em dois eixos paralelos** (delta-014): contrato em `adapters.md`, seção "Review em dois eixos"; fallback inline sequencial (RNF2).

### Mudado
- Política de dependência dos adapters com **verificação datada** por motor; `cycle.md` referencia os dois eixos no review; índice de ADRs atualizado (0009 Accepted, 0011 e 0012 incluídos — as duas primeiras eram defasagens de deltas anteriores).

## [0.9.0] - 2026-07-28

### Adicionado
- **Check de inventário de skills no CI** (delta-013): novo step do job `ci` compara cada diretório `skills/<nome>/` com as descrições dos dois manifestos (`plugin.json` e `marketplace.json`), case-insensitive, e falha nomeando a skill ausente e o manifesto omisso — mecaniza a classe de drift registrada nas Lições (7 vs 8 vs 9 skills).
- **Hook pré-commit versionado** (delta-013, quita DT-005): `.githooks/pre-commit` roda o `validate_integrity.py` quando o commit toca `.md`/`deps.toml`; template + oferta opt-in no bootstrap da `guarding-doc-integrity`. Mecanismo e ativação: README e SKILL.md da skill.

### Mudado
- Manifestos citam as **9 skills** (entram `descoberta` e `eu-tenho-tdah` onde faltavam); `eu-tenho-tdah` reconhecida como skill do plugin (R3 da delta-013, consolida no TRUTH no archive).
- **ADR-0009 promovida a Accepted** (evidência: piloto doc-profile+doc-entregavel nos 4 repos IMEX, 8 exports); `doc-entregavel` sai de experimental no README; a exceção de documentação cliente entra no RNF1 via MUDA no archive. Check mecânico do doc-profile permanece adiado (pendência roteada).
- Promessas do DT-005 alinhadas ao mecanismo real em `deps.toml`, `guarding-doc-integrity/SKILL.md`, `canonical-rules.md` e `README.md`.

## [0.8.0] - 2026-07-27

### Adicionado
- Skill **`descoberta`** (delta-012): fase **pré-specify** do ciclo — inventário de insumos brutos (transcrição/resumo de reunião, planilha legada, vídeo com frames via `ffmpeg`), mineração do processo as-is com **claims tagueados** `confirmado`/`inferido`/`lacuna` e fonte rastreável (modelo Reversa), dossiê em `docs/discovery/`, **população de `GLOSSARY.md`/`DATA_DICTIONARY.md`** por append/merge, divergências contra a baseline vigente (PRD/TRUTH) e pauta de validação em **Mob Elaboration** (AI-DLC: a IA propõe claim a claim, o stakeholder valida). Saída para `max:write-prd` com contrato de `[PRESUNÇÃO]` (claim não confirmado nunca vira requisito sem marca); fallback nativo quando o `max` falta. Renúncias (delegar ao write-prd, portar BMAD) registradas na [ADR-0011](docs/adrs/ADR-0011-descoberta-skill-propria.md). Adapters do `spec-feature` ganham a linha da pré-fase e o contrato descoberta/write-prd.

## [0.7.0] - 2026-07-26

### Adicionado
- `doc-entregavel`: **tipos de entregável jurídico-comercial** (delta-011). A skill passa a despachar por `tipo` — `prd-cliente` (fluxo vigente), `juridico-nda`, `juridico-contrato-ti` e `requisitos-cliente` — com as regras de **conteúdo** no novo `references/juridico.md` (fonte canônica; a SKILL.md aponta, não duplica): minuta obrigatória, formatação de mercado (a NBR 14724 é acadêmica e **não** se aplica a contrato), eficácia executiva (duas testemunhas com CPF, assinatura eletrônica, RTD), estrutura canônica do instrumento particular, cláusulas obrigatórias por tipo e checklist de eficácia. Tipos `juridico-*` não dependem do `doc-profile.yaml`; o export continua sendo o pipeline vigente.
- `doc-entregavel`: `requisitos-cliente` declara o recorte (requisitos **de projeto e/ou de produto/serviço**) com a seção de **Visão** correspondente, e traz **previsão de orçamento por fase** (com premissas da estimativa e faixa), **prazo total estimado** e **cronograma com marcos de pagamento** como seções obrigatórias — placeholder em destaque quando o valor não fechou, nunca omissão. Duas versões por regra de proteção de PI: A (proposta executiva, pré-NDA, sem arquitetura/modelagem/backlog) e B (especificação completa, pós-NDA), uma por arquivo.

### Corrigido
- `doc-entregavel` (auditoria da base jurídica, 2026-07-26): a premissa de que a jurisprudência exigiria assinatura **qualificada** (ICP-Brasil) para dispensar testemunhas estava **invertida**. O art. 784, §4º, do CPC (Lei 14.620/2023) admite qualquer modalidade de assinatura eletrônica, dispensando testemunhas quando a integridade é conferida por provedor de assinatura, e o STJ confirmou que a certificação ICP-Brasil não é obrigatória (REsp 2.205.708-PR, 4ª Turma, 04/11/2025, Informativo 871; REsp 2.150.278-PR, 3ª Turma, 24/09/2024; fundamento privado no art. 10, §2º, da MP 2.200-2/2001). A política conservadora foi mantida — bloco de duas testemunhas sempre + recomendação de provedor com trilha de auditoria — mas agora declarada como **redundância deliberada**, não como exigência legal. Corrigidas também a titularidade autoral de PJ (vem de cessão/obra sob encomenda, art. 49 da Lei 9.610/98 — o art. 11 *caput* é o autor pessoa física) e o alcance da Lei 14.063/2020 (rege interações com entes públicos, não a relação privada).
- `doc-entregavel`: lacunas de praxe no conteúdo dos tipos jurídicos — o NDA ganhou o fundamento de **segredo de negócio** (art. 195, XI e XII, da Lei 9.279/96), que alcança a ideia e a arquitetura onde o direito autoral não chega; o contrato de TI ganhou **reversibilidade/transição de saída** (anti lock-in), **SLA**, comunicação de **incidente** (art. 48 da LGPD), **licenças de terceiros/open source** e declaração de **uso de IA generativa** no desenvolvimento.
- `check_cycle.py`: **C4 lê o TRUTH particionado**. Com `specs/truth/<dominio>.md` (particionamento que o próprio C5 recomenda acima de 800 linhas), a verificação de "requisito ainda presente" lia só `specs/TRUTH.md` — o índice — e acusava **CRÍTICO falso de perda** para todo requisito que vivia numa partição. O diff já cobria `specs/truth`; só a leitura do estado resultante não. Selftest cobre o caso (falha sem o fix).
- `check_cycle.py`: **aceita a notação `RF-NN`/`RNF-NN`** além de `Rn`/`RNFn`, com numeração hierárquica opcional (`RF-01.1`). Projeto com corpus legado cita o ID de requisito em massa (o piloto IMEX tem 443 ocorrências em 70 arquivos, além das âncoras de um entregável contratual já assinado) — renomear tudo para `Rn` seria churn para chegar ao mesmo lugar, e o `tabela_cliente.py` do `doc-entregavel` **já exigia** `RF-NN`, deixando duas notações incompatíveis em dois scripts do mesmo plugin. Selftest cobre as duas notações em C1/C2 e C4.

## [0.6.0] - 2026-07-24

### Adicionado
- `doc-entregavel`: **Sumário automático no formato de contrato** (título pontilhado até o nº de página, subseções indentadas) em página própria após a capa, nos dois formatos. No pdf, os números de página vêm de **duas passadas de render** — a 1ª mede a página física de cada título (h1–h3, extensão `toc` do python-markdown) extraindo texto com pdftotext/pypdf em **busca reversa** (ignora as ocorrências dos títulos no próprio Sumário); sem extrator, sai sem números com aviso. No docx, campo `TOC` nativo com `updateFields` — o próprio Word gera pontilhado e paginação ao abrir. Selftest cobre campo no docx e nº de página no pdf.
- `doc-entregavel`: **corpo com linhas justificadas** por padrão nos dois formatos (títulos, tabelas e código permanecem à esquerda); pdf com hifenização pt-BR (`hyphens: auto` + `lang='pt-BR'`), docx justificando só parágrafos de corpo sem alinhamento explícito (capa e células de tabela intactas). Selftest cobre a justificação.
- `eu-tenho-tdah`: skill de estilo de escrita pessoal do Iuri (baseado em ayghri/i-have-adhd), fora do ciclo de delta specs — documentada no README.
- `handoff`: passo 5 — ao fechar a sessão, a skill imprime o **prompt de retomada** ("Leia o HANDOFF.md… Foco: <primeiro próximo passo>"), com variante para workspace multi-repo. O prompt referencia os registros, nunca os resume.

### Adicionado
- **Stack de diagramas completo com vínculo normativo categoria → ferramenta** (ADR-0009, ainda Proposed): tabela de categorias no ADR ganha Excalidraw (diagramas explicativos; alternativa a D2 na arquitetura visual moderna) e a regra "a ferramenta segue a categoria — não reaproveite diagrama de outra categoria" (modo de falha observado no piloto IMEX: tudo diagramado em Mermaid por inércia). `doc-profile.yaml` (template) ganha a ferramenta `excalidraw`, a categoria `explicativos` e passa a apontar `structurizr` como default de arquitetura; `cycle.md` e `doc-entregavel` repetem o vínculo no ponto de uso.
- **Regras de página no entregável** (achado da revisão IMEX): tabela inteira numa página quando couber e, transbordando, quebra sem cortar linha e com cabeçalho repetido (CSS `break-inside`/`thead` no pdf; `cantSplit`/`tblHeader` via python-docx no docx); diagrama/fluxograma pode preencher a própria página (`.fig-pagina`) e virar paisagem por diagrama (`.paisagem`, named page no chrome). `md_in_html` habilitado no caminho pdf para os wrappers.
- **Guia normativo de prosa** (`spec-feature/references/prosa.md`): uma regra por frase (EARS PT-BR), DEVE/NÃO DEVE/PODE (RFC 2119), regra combinatória vira tabela de decisão, fluxo > 3 passos vira diagrama + passos numerados, estrutura contexto → regra → exceções → auditoria, com antes/depois real (RBAC do travelplanner) e checklist pré-baseline. Referenciado no gate do `cycle.md` e no passo de montagem do `doc-entregavel`.
- `doc-entregavel`: comandos de render para `.dsl` (structurizr/structurizr → C4-PlantUML → plantuml, tudo docker) e `.excalidraw` (`excalidraw-brute-export-cli` headless via Playwright) — toolchain validada de ponta a ponta.

### Corrigido
- `tabela_cliente.py` localiza as seções de RF/RNF **pelo título** ("Requisitos Funcionais"/"Requisitos Não Funcionais"), não mais pelos números fixos `## 6./## 7./## 8.` — a renumeração dos PRDs IMEX (0→1, 20-07) moveu RF para §7 e RNF para §8 e o script quebrava no assert. Selftest cobre as duas numerações; SKILL.md e docstring atualizados.
- `tabela_cliente.py` (achados da rodada de export IMEX 20-07, reproduzidos nos 4 PRDs): a tabela gerada saía colada no heading seguinte ("## 7."/"## 8." viravam linha da tabela no python-markdown) e o conteúdo de nível superior após o último RNF (`---`, notas) era descartado — linha em branco garantida entre seções e cauda preservada; selftest cobre os dois casos.
- `.fig-pagina`: o `<p>` que o `md_in_html` embrulha na imagem quebrava a cadeia de `max-height` no print do Chrome (diagrama vazando por várias páginas ou página em branco) — o `<p>` agora vira flex 100% no CSS do exportador. SKILL.md documenta os demais modos de falha do export: SVG mermaid sem width/height absolutos, imagem dentro de div descartada pelo pandoc no docx (usar linha de imagem pura), DPI/pHYs do PNG no dimensionamento do pandoc e proporção extrema (> ~3:1) exigindo re-layout do fonte (`autolayout tb`).
- `doc-entregavel` ganha `scripts/tabela_cliente.py` (formato cliente, com `--selftest`): cenários DADO/QUANDO/ENTÃO dos §6 viram tabela por grupo de RF (Pré-condição · Ação · Resultado esperado) e os RNF do §7 viram tabela (Métrica · Verificação), com paridade garantida por assert e correção do achatamento de listas do caminho pdf (indentação 2→4). Validado na rodada IMEX de 2026-07-20 (4 PRDs, 173 cenários). SKILL.md instrui o passo e fixa a regra da capa: data da baseline, não do export.
- **Documentação visual como gate configurável** (ADR-0009, experimental — em validação no piloto imex-travelplanner): todo projeto com ciclo registra a decisão sobre documentação visual num `doc-profile.yaml` declarativo (para quem, o quê, com quê, quando, onde). O `projeto-init` gera o perfil default enxuto no scaffold (arquitetura + modelo de dados obrigatórios na spec; `docs/diagrams/`; `docs/entregaveis/` só com `publico.cliente: true`); na fase specify o agente gera **somente** o que o perfil declara obrigatório (`cycle.md`), perguntando antes de qualquer extra; ausência do arquivo = comportamento anterior + warning. Documentação cliente é isenta da economia de tokens (exceção ao RNF1 registrada na ADR; formalização como MUDA RNF1 pendente do piloto). Setup dos CLIs (mermaid obrigatório; dbml-renderer, plantuml, d2, structurizr opcionais) no README.
- Skill `sdd-iuri:doc-entregavel` (experimental): congela o entregável cliente — renderiza os diagramas do doc-profile, monta o documento com capa de assinatura parametrizada e exporta PDF/DOCX versionado em `docs/entregaveis/` via `exporta_entregavel.py` (generalização do pipeline dos PRDs/contratos IMEX: pypandoc + python-docx; markdown → HTML → chrome headless), com `--selftest`.
- `check_cycle.py` ganha o **C7**: mede as linhas adicionadas em `specs/NNN-nome/` contra o merge-base e reporta BAIXO (não bloqueia) quando passam do limiar de PR, mecanizando a régua manual do split condicional (R17/DT-003). Constante `PR_LIMITE` sancionada como espelho do `500` no `deps.toml`; selftest co-localizado com git real. `analyze.md`/`cycle.md`/`SKILL.md` atualizados. (delta-009)
- `deps.toml` passa a governar mais dois limiares antes duplicados sem sanção (DT-008): o do cabeçalho-resumo do `plan.md` (`15 linhas`, dono RNF1 do TRUTH.md; espelhos `resumo-plan.md` e `cycle.md`) e o de particionamento por domínios do TRUTH.md (`10 dom`, par do limiar de 800 linhas; espelhos `cycle.md` e `templates/TRUTH.md`) — o C1 do `validate_integrity.py` agora acusa drift entre eles.

### Adicionado
- `scripts/instala-motores.sh`: instala os três motores de terceiros em uma chamada só (substitui o pipeline `printf | xargs` do README); falha em um motor não interrompe os demais e o aviso sugere o `marketplace add` que pode faltar.

### Mudado
- **`STATE.md` renomeado para `HANDOFF.md`** em todo o framework (delta-010): o diário de bordo passa a ter o nome que diz o seu papel — o arquivo que a próxima sessão lê para retomar. Natureza intacta (janela rolante, digest que roteia, "união das verdades"). Template do `projeto-init`, `canonical-rules.md`, `detection.md`, `CLAUDE.md`, `deps.toml` (exclude), `README.md` e a skill `handoff` (prompt de retomada de uma linha) acompanham; `MUDA R19`/`MUDA R20` no `TRUTH.md`. Decisão e renúncias em [ADR-0010](docs/adrs/ADR-0010-handoff-renomeia-state.md). **BREAKING CHANGE:** projetos com `STATE.md` existente — a skill `handoff` migra em runtime (`git mv STATE.md HANDOFF.md` quando não há `HANDOFF.md`).
- README reescrito para leitura humana: estados da delta e ciclo em diagramas Mermaid (render nativo no GitHub, no lugar do bloco ASCII), seção "Como funciona" nova, instalação condensada em 3 comandos (motores de terceiros em lista estilo `requirements.txt` via `xargs -n1 claude plugin install`) e linha do `handoff` citando o prompt de retomada.
- delta-009 arquivada: `MUDA R12` (delta-006 → delta-009) consolidado no `TRUTH.md` — o gate mecânico agora cobre C1–C7 (o C7 mede o split de PR). DT-003 quitado. (#29)
- Espelhos do limiar de tamanho de PR enxugados de 4 para 1 (DT-002): `SKILL.md`, `detection.md` e `analyze.md` passam a citar "o limiar canônico" em vez de repetir o `500`, que fica materializado só no `CLAUDE.md` (regras canônicas do próprio repo). Sob o teto de 2–3 espelhos da guarding-doc-integrity.

### Corrigido
- `doc-entregavel`: a renderização do PNG mermaid passa a exigir a largura nativa do SVG (`--width` + `--scale 2`) — no viewport default (800px) do mmdc, diagrama largo saía de baixa resolução (achado do piloto ADR-0009 nos 4 repos IMEX); erro e correção registrados na tabela de erros comuns da skill.
- Formatação: quebra de linha manual removida da prosa em 27 arquivos `.md` (raiz, `docs/adrs/`,
  `skills/**`, `specs/TRUTH.md`) — parágrafos, itens de lista (inclusive aninhados), blockquotes
  e comentários HTML viram uma linha lógica só, sem cortar antes da largura real do leitor. Blocos
  de código, tabelas e frontmatter YAML preservados byte a byte; conteúdo de blocos ` ```markdown `
  (templates de módulo do `canonical-rules.md`, relatório do `analyze.md`) reflowado por dentro.
  `specs/_archive/` e as ADRs `Accepted` ficam de fora — histórico imutável. Verificado por
  comparação de tokens (zero palavra perdida/alterada) e idempotência (2ª passada é no-op).

## [0.5.1] - 2026-07-20

### Adicionado
- ADR-0008: skill handoff própria — renúncias a vendorizar/traduzir a skill externa e a delegar à `max:handoff` registradas em Nygard (a renúncia vivia só na spec arquivada da delta-008).
- `DEBT.md`: DT-008 (valores "≤15 linhas" e "~10 domínios" duplicados sem sanção no `deps.toml`) e lição do grep case-sensitive que deixou passar "Cinco skills" no manifesto do marketplace.

### Corrigido
- `.claude-plugin/marketplace.json`: descrição enumerava cinco skills sem a `handoff` — executor esquecido pela delta-008; agora sem numeral, com as seis. (achado ALTA da verificação final)
- Executores e resumos defasados alinhados ao TRUTH vigente: README enumera `DEBT` no scaffold do init (R18); docstring do `check_cycle.py` e SKILL da spec-feature citam os seis checks (C1–C6); comentário do `ci.yml` lista integridade documental e os dois contextos exigidos; template DEBT/regra canônica/CLAUDE.md materializam a data de quitação prometida pelo R18; DT-004/DT-005 corrigidos no `DEBT.md`; índice de ADRs com título íntegro da 0005, nota de sincronia do ADR-TEMPLATE e rodapé honesto sobre datas do backfill.

## [0.5.0] - 2026-07-20

### Adicionado
- Skill `sdd-iuri:handoff`: fecha a sessão nos registros com dono — atualiza o `STATE.md` (diário de bordo), roteia débito/pendência/lição novo para o `DEBT.md` (DT-NNN/Lições) e cita a delta em curso com fase e veredito do gate. Própria, inspirada na `handoff` de mattpocock/skills (MIT), reescrita para gravar no repo em vez de brief efêmero. (delta-008)

### Mudado
- A contagem de skills sai da redação viva (R15 do TRUTH.md, `CLAUDE.md`, `README.md`) — a próxima skill não exige rodada de MUDA por causa de um numeral; manifesto do plugin lista a sexta skill. (delta-008, #23)
- delta-008 arquivada: R20 (domínio "Handoff de sessão") + MUDA R15 consolidados no `TRUTH.md` com sufixo `(delta-008)`. (#24)

## [0.4.0] - 2026-07-20

### Adicionado
- `DEBT.md` na raiz — registro canônico de débito, pendências e lições com IDs `DT-NNN` (natureza, origem, data, gatilho de correção, status; item quitado muda de status, nunca some), com backfill DT-001..DT-007 e cinco lições datadas da varredura de registros. Renúncia a GitHub Issues como registro: ADR-0007. Template distribuído novo no `projeto-init` (`references/templates/DEBT.md`), com linha própria na matriz de scaffold. (delta-007)
- Backfill de ADRs: cinco decisões-com-renúncia que já vigiam ganham registro Nygard — ADR-0002 (tag git como fonte da versão), ADR-0003 (`--selftest` co-localizado), ADR-0004 (degradação graciosa por adapters), ADR-0005 (consolidação mecânica do archive) e ADR-0006 (perímetro dos gates determinísticos).
- Arquivo `LICENSE` (MIT) materializado — o `plugin.json` já declarava `"license": "MIT"` sem que o arquivo existisse.

### Corrigido
- `CLAUDE.md`: os 3 comandos de teste ganham o prefixo `skills/` (quebrados desde a reestruturação da delta-001) e o exemplo de caminho da seção Clean Code idem.
- `README.md`: a descrição do check `ci` passa a listar os 7 steps reais (faltavam portabilidade RNF5 e integridade documental); versões concretas dos motores de terceiros removidas — o dono é a tabela de política de versões do `adapters.md`.

### Mudado
- `STATE.md` deixa de acumular quatro naturezas e vira **diário de bordo** (Agora / Feito recentemente / Problemas atuais / Próximos passos imediatos, janela rolante): as-built vive no TRUTH/README, débito e lições no `DEBT.md`, decisões nos ADRs, histórico no CHANGELOG. Template do `projeto-init` e regra canônica (docs-sdd) acompanham. (delta-007)
- Pendência roteada no archive (R16) muda de destino: de "Decisões em aberto" do `STATE.md` para `DT-NNN` no `DEBT.md` — mensagem e fixture do C6 (`check_cycle.py`), regra 7 do `cycle.md` e comentário do template `delta-spec.md` atualizados juntos. (delta-007, #21)
- delta-007 arquivada: MUDA R16 + R18/R19 consolidados no `TRUTH.md` com sufixo `(delta-007)`. (#22)
- `CLAUDE.md` registra as convenções já praticadas e nunca escritas: escopo de commit da delta (`tipo(NNN-nome):`), tag cortada no merge que conclui a delta (o "pronto" inclui o archive) e merge por squash.

## [0.3.0] - 2026-07-19

### Adicionado
- `check_cycle.py` reconhece a notação `delta-NNN` além do símbolo legado `Δ` nos alvos de MUDA/REMOVE; o C4 passa a medir perda de requisito por presença de ID no `TRUTH.md` resultante, liberando a reescrita de sufixo em massa sem falso CRÍTICO. (delta-006)

### Mudado
- Notação viva das deltas passa de `ΔNNN` para `delta-NNN` (digitável) em templates, docs do framework, `CLAUDE.md`, `README.md`, `STATE.md` e nos sufixos do `TRUTH.md`. Histórico imutável (ADRs, `_archive/`, changelog lançado) preserva o `Δ`. (delta-006, #17)
- delta-006 arquivada: MUDA R6/R7/R12 consolidados no `TRUTH.md` com sufixo `(delta-006)`. (#18)

## [0.2.2] - 2026-07-19

### Corrigido
- `adapters.md` declara o fallback do review estágio 1 (conferência inline com aviso) — fecha o furo do RNF2 apontado pela revisão do backfill Δ000; redações de R13/RNF3 corrigidas na consolidação. (Δ005, #15)

### Mudado
- Δ005 arquivada: MUDA R13/RNF2/RNF3 consolidados no `TRUTH.md`. (#16)

## [0.2.1] - 2026-07-19

### Mudado
- Δ003 arquivada: R17 consolidado no `TRUTH.md`; pendência de mecanização do split roteada para o `STATE.md`. (#12)
- Δ004 arquivada: MUDA R13 consolidado no `TRUTH.md` (forma dos excludes do template). (#14)

### Corrigido
- `templates/deps.toml` da `guarding-doc-integrity`: excludes `**`-final (no-op em `pathlib` ≤ 3.12) trocados pela forma portável `**/*.md`, com comentário do porquê. (Δ004, #13)

## [0.2.0] - 2026-07-19

### Adicionado
- Split condicional do PR de delta (Δ003): no fim do analyze, o diff de `specs/NNN-nome/` é medido contra o limiar canônico de PR — acima dele, os artefatos são mergeados num PR próprio antes do implement; dentro dele, o fluxo de PR único segue inalterado (`cycle.md` + saída extra do gate em `analyze.md`). (#11)

## [0.1.0] - 2026-07-19

Primeiro release: cria o baseline SemVer do repositório. Tudo abaixo estava acumulado desde o início do projeto (PRs #1–#9).

### Adicionado
- `deps.toml` na raiz: os limiares espelhados do framework (particionamento do TRUTH.md e tamanho de PR) ganham dono e espelhos sancionados, com `validate_integrity.py` rodando contra o próprio repo no job `ci`. (#9)
- `check_cycle.py` C6: pendência aberta (`- [ ]` em "Dependências e riscos") de delta arquivada é acusada até ser roteada para o `STATE.md`; convenção no template `delta-spec.md`. (Δ002)
- Selftest do C4 com repositório git real (perda pós-commit e falso positivo de MUDA). (Δ002)
- Distribuição como plugin do Claude Code: `.claude-plugin/plugin.json` e skills em `skills/`, instalável por `/plugin marketplace add iuripereira/sdd-iuri` + `/plugin install sdd-iuri@sdd-iuri`. (#5)
- Step de CI que reprova caminho absoluto de máquina em `skills/` e `.github/` (RNF1 da Δ001). (#5)
- `spec-feature/scripts/check_cycle.py` — gate determinístico do ciclo: aceite verificável (C1), cobertura spec↔tasks (C2), estado × localização (C3), archive sem perda (C4) e limiar do TRUTH.md (C5). Sai 1 em ALTO/CRÍTICO. (#2)
- `guarding-doc-integrity` integrada ao framework como executora da regra de propagação, com `--selftest` no validador. (#3)
- Scaffold do próprio repositório via `projeto-init`: `CLAUDE.md`, `CHANGELOG.md`, `STATE.md`, `docs/adrs/`, `specs/TRUTH.md` com backfill do estado vigente (Δ000).
- Validação de TOML e execução dos `--selftest` dos gates no job `ci`.

### Mudado
- A saída do `check_cycle.py` declara-se parcial: checks 3 e 5 do analyze são humanos. (Δ002)
- Grep de portabilidade do CI cobre `$HOME/.claude/skills` e `/home/<user>/.claude/skills`. (Δ002)
- **BREAKING:** as cinco skills passam a ser invocadas sob o namespace `sdd-iuri:` (ex.: `/sdd-iuri:spec-feature`). Projetos que citem os nomes antigos precisam atualizar. (#5)
- Os scripts de gate resolvem o próprio caminho por `${CLAUDE_PLUGIN_ROOT}` em vez de `~/.claude/skills/...`. (#5)
- `.gitignore` deixa de ser allowlist: fora de `~/.claude/skills/` o repositório contém só o framework. (#5)
- `canonical-rules.md`: a regra de propagação passa a apontar para `deps.toml` + `guarding-doc-integrity`, no lugar do `scripts/check_docs.py` que nenhuma skill gerava. (#3)
- `templates/deps.toml`: o dono do exemplo passa de `PRD.md` (arquivo que o `projeto-init` nunca cria) para `specs/TRUTH.md`; `scan_globs` cobre o TRUTH consolidado mas não as deltas abertas. (#3)
- `analyze.md`, `cycle.md` e `spec-feature/SKILL.md` passam a invocar o gate mecânico antes da leitura de juízo. (#2)

### Segurança
- `.gitignore`: bloco de secrets anexado à allowlist. Sem ele, arquivos como `spec-feature/.env` seriam versionados — a allowlist re-inclui o diretório inteiro da skill.

### Corrigido
- `check_cycle.py` C4 compara o `TRUTH.md` contra o merge-base da branch com a main — fecha a janela cega pós-commit (gate LIBERADO com requisito perdido); fallback `HEAD` com aviso quando não há base. (Δ002)
- README: a instalação manual (`cp -r`) não copiava `guarding-doc-integrity`, deixando a skill inalcançável para quem seguisse a documentação. (#3)

<!--
No release: renomeie "[Não lançado]" para "## [X.Y.Z] - AAAA-MM-DD", abra uma nova seção "[Não lançado]" vazia acima, e crie a tag git vX.Y.Z. Bump derivado dos commits: fix→PATCH, feat→MINOR, !/BREAKING CHANGE→MAJOR (o maior vence). -->
