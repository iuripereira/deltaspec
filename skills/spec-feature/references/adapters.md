# Adapters — contratos de integração dos plugins

Princípio: acoplamento = (i) **contrato na invocação** (instrução de formato/destino passada à skill), (ii) **verificação pós-fase** do artefato produzido, (iii) **fallback com aviso** — o ciclo degrada, nunca quebra. Antes de cada fase, confira a skill esperada na lista de skills disponíveis; ausente ou renomeada → trate como não instalada (fallback) e reporte *"possível breaking change do plugin X — verificar changelog"*.

## Tabela de contrato (fase → skill esperada → ponto sensível)

| Fase | Skill esperada | Ponto sensível a breaking change |
|---|---|---|
| descoberta (pré-specify) | `deltaspec:descoberta` (própria) · `max:write-prd` (motor do PRD) | nome da skill max; formato/local do PRD gerado |
| clarify | `mattpocock-skills:grilling` · `mattpocock-skills:domain-modeling` (gatilho durável) | nomes das skills; `grilling` roda por rodadas, sem relatório quantificado (critério de saída: seção abaixo) |
| plan | `superpowers:writing-plans` | local default de planos (`docs/superpowers/plans/`) e a frase "User preferences for plan location override this default" |
| modelo de dados (specify/plan, categoria `modelo-dados` obrigatória no perfil) | `deltaspec:modelo-dados` (própria, delta-073) | nome fixo `docs/data-model.md`; subconjunto DBML do parser (`camadas.md` da skill) — `.dbml` fora dele cai em M1 |
| implement | `superpowers:executing-plans` · `superpowers:subagent-driven-development` · `superpowers:test-driven-development` · `superpowers:using-git-worktrees` | nomes das skills; obrigatoriedade de TDD |
| review | `superpowers:requesting-code-review` (eixo Spec) · `ponytail:ponytail-review` (eixo Qualidade) — paralelos | nomes; formato da delete-list |
| contexto de codebase (descoberta · specify/plan · review) — opcional | `graphify` (CLI/MCP externo, não é plugin Claude) | nomes dos comandos `query`/`path`/`explain`; formato das tags de confiança; instalador (escreve hook/CLAUDE.md — nunca usar) |
| apresentação a cliente/gestão/stakeholder (flag `apresentacao` no artefato) — **default nativo**, sem motor de terceiro | opcional: `diagram-design` (plugin de terceiro, local) · `design-sync` (ferramenta do harness + serviço claude.ai) | nomes/estrutura da skill diagram-design (27 tipos, HTML+SVG, `diagram-design:export` via Playwright); design-sync exige login claude.ai com escopo design e o fluxo list → plan → write |
| transversal | `ponytail:ponytail` (hook always-on) | nível default; `PONYTAIL_SUBAGENT_MATCHER` |

## descoberta / write-prd (pré-specify — delta-012)

- **Quando:** projeto sem PRD validado ou com insumos brutos de descoberta (transcrição, planilha legada, vídeo) — a `deltaspec:descoberta` roda antes do specify e produz o dossiê com claims tagueados (`confirmado`/`inferido`/`lacuna`).
- **Invocação (write-prd):** passe o dossiê como contexto com o contrato — *"claims `inferido`/`lacuna` entram no PRD marcados `[PRESUNÇÃO]`; só `confirmado`/validado entra sem marca"*. **Verificação pós-fase:** nenhum claim não-confirmado sem `[PRESUNÇÃO]` no PRD.
- **Fallback (max ausente):** PRD rascunho nativo com a mesma regra de marcação e o aviso *"saída degradada: max/write-prd não instalado"*. A skill `descoberta` em si é própria do framework — não degrada.

## grilling / domain-modeling (mattpocock-skills@claude-plugins-official — delta-039)

- **Invocação (clarify):** passe a delta spec rascunho como objeto da entrevista para `mattpocock-skills:grilling` (mecânica de rodadas: SKILL.md do motor). Gatilhos para juntar `mattpocock-skills:domain-modeling` (senão `grilling` puro): contrato externo · modelo de dados persistente · dependência nova · segurança. Reporte a escolha ao usuário.
- **Critério de saída (substituto do gate quantificado — R8/delta-039):** a fase encerra com **fronteira vazia** — nenhuma pergunta desbloqueada restante — e as decisões consolidadas na spec. Ponto sem resposta não fecha a fronteira: vira pendência declarada em "Dependências e riscos".
- **Contrato ADR (domain-modeling):** instrua na invocação — *"registre decisões como ADR usando o template `docs/adrs/ADR-TEMPLATE.md` deste projeto (PT-BR, imutável), na numeração existente"*. **Verificação pós-fase:** ADRs novos conformes ao template; não conformes → reformatar antes de prosseguir.
- **Canal humano (verificação pós-fase, delta-026):** além dos ADRs, a fase só fecha com a **trilha do clarify** no cabeçalho do `spec.md` (C12 — sintaxe na tabela de trilha de auditoria do `cycle.md`, dona do formato). Ambiguidade resolvida por exploração do repositório **não conta como resposta do usuário**: fatos resolvidos por subagente num repo com TRUTH e ADRs respondem quase tudo — o resultado é uma entrevista que nunca acontece. Nesse caso o relatório sai marcado `auto-avaliado`, em vez de passar como se tivesse havido conversa.
- **Viés de quem recomenda:** quem redige a spec é quem formula as perguntas **e a resposta recomendada de cada uma** — recomendação induz carimbo do usuário. Na dúvida entre dar um ponto por resolvido ou perguntá-lo, o ponto entra **aberto na rodada** (R8).
- **Consolidação:** passo nativo (cycle.md) — renúncia ao `to-spec` upstream registrada no ADR-0026 (o formato delta-spec é do framework; `to-spec` sintetiza sem entrevista e publica no tracker).
- **Fallback (mattpocock-skills ausente):** clarify próprio simplificado — cheque uma a uma as ambiguidades de **permissões, estados de erro, persistência, limites, concorrência** — com o aviso *"clarify degradado: mattpocock-skills/grilling não instalado"*.

## Superpowers

- **plan:** input = delta spec pós-clarify (**a spec do deltaspec é a fonte da verdade; o brainstorming/spec do Superpowers não é**). Local: a preferência no CLAUDE.md (módulo sdd-ciclo) redireciona para `specs/NNN-nome/plan.md`; reforce na invocação. Formato: o dele, **sem pós-processamento**. **Pós-fase:** (1) plano no local certo — se foi para `docs/superpowers/plans/`, mova; (2) prependa o cabeçalho de `templates/resumo-plan.md`.
- **implement:** TDD conforme a coluna `tdd` do tipo. `recomendado`/`off` → instrua na invocação a dispensa permitida, com justificativa registrada no plan.md por task dispensada. Unidades paralelizáveis (cycle.md, "Execução paralela por unidades") → um subagente com worktree por unidade (superpowers:using-git-worktrees); sem subagentes/worktree → sequencial topológico com aviso.
- **Fallback (superpowers ausente):** gere `plan.md` próprio (cabeçalho-resumo + plano detalhado com caminhos e verificação por passo) e rode o implement inline, com o aviso *"plan degradado: superpowers/writing-plans não instalado"*. O fallback **não substitui a fase tasks**: `tasks.md` continua sendo gerado dele (o analyze depende do tasks.md).
- **Fallback do review eixo Spec (superpowers ausente):** conduza a conferência inline — cada Rn/RNFn da spec confrontado com o diff da delta, com veredito por requisito — e registre o aviso *"review eixo Spec degradado: superpowers/requesting-code-review não instalado"*. O eixo Qualidade segue o fallback do ponytail abaixo.

## ponytail

- **Transversal:** hook always-on (nível `full` para todos os tipos — não suba para `ultra` por default; a11y/validação são inegociáveis). **Verificado na 4.8.4:** o hook `SubagentStart` injeta em **todos** os subagentes quando o modo está ativo — o `PONYTAIL_SUBAGENT_MATCHER` citado na análise original **não existe nesta versão**. Custo aceito (ruleset é inócuo em agentes read-only, só gasta tokens); não forkar por isso. Reavaliar a cada upgrade 4.x se o filtro por tipo de subagente apareceu.
- **Review eixo Qualidade:** rode `/ponytail-review`; a delete-list entra no relatório de qualidade antes do archive.
- **Fallback (ponytail ausente):** eixo Qualidade roda sem delete-list, com aviso; o NFR de economia segue coberto pelas regras canônicas do CLAUDE.md.

## Review em dois eixos (delta-014)

O review executa como **dois eixos independentes**, cada um cego ao contexto do outro (o achado de um não contamina a leitura do outro): **eixo Spec** (conformidade — motor `superpowers:requesting-code-review`, conteúdo na seção Superpowers acima) e **eixo Qualidade** (over-engineering — motor `ponytail:ponytail-review`, seção ponytail acima).

**Execução:** harness com subagentes → despache os dois eixos em **subagentes paralelos** (um por eixo, prompts independentes); harness sem subagentes ou motor ausente → inline, em sequência, com os fallbacks e avisos acima (RNF2). Perfil `enxuto` aprovado (R1, delta-015): os dois eixos podem rodar **fundidos num único subagente**, achados ainda classificados por eixo, mesma regra de convergência. Achado apontado pelos **dois** eixos é convergente — trate antes do PR, sempre. Os demais achados seguem a régua vigente (crítico bloqueia; o resto é decisão registrada).

## graphify (contexto de codebase — delta-016, opcional)

Camada de contexto para as fases que leem código em projeto-alvo grande/brownfield:
`descoberta`, `specify`/`plan` e o eixo Spec do `review` (impacto do diff da delta).
**Não** é motor de grafo de tarefas — o `tasks.md` continua dono das arestas (ADR-0014).

- **Habilitação dupla e manual:** binário instalado **e** `motores.graphify: true` no
  `doc-profile.yaml` do projeto-alvo. **Nunca rode `graphify install`** — nem o alvo
  por plataforma `graphify claude install`: os dois escrevem hook `PreToolUse` e seção
  no CLAUDE.md do projeto, interferindo no harness (renúncia:
  [ADR-0014](../../../docs/adrs/ADR-0014-harness-paralelismo-e-graphify.md)).
  Instalação manual consciente.
- **Modos — escolha informada, não default:** `--code-only` entrega AST local por
  tree-sitter (determinístico, zero LLM, nada sai da máquina) e **cega todo arquivo
  não-código** — `.md`, PDF, DOCX, XLSX e imagem são pulados, e a tag `AMBIGUOUS`
  nunca aparece. Projeto-alvo cujo valor está na documentação precisa do modo
  completo. (A preferência normativa por `--code-only` da ADR-0014 caiu aqui:
  [ADR-0022](../../../docs/adrs/ADR-0022-backend-do-graphify-registrado-no-perfil.md).)
- **Backend do modo docs (exige LLM):** prefira `claude-cli` ou `ollama` — nenhum dos
  dois cria fronteira nova de confiança
  ([ADR-0022](../../../docs/adrs/ADR-0022-backend-do-graphify-registrado-no-perfil.md)).
  API paga só como decisão consciente. A escolha é **registrada** em
  `motores.graphify_backend` do `doc-profile.yaml`; campo vazio com indexação de docs
  pedida → **pare e pergunte**, nunca assuma um default. Em `--code-only` o campo é
  dispensável.
- **Invocação:** `graphify query`/`path`/`explain` como insumo fundamentado — toda
  aresta citada entra com `arquivo:linha`. Tags de confiança mapeiam no modelo da
  descoberta (R25): `EXTRACTED` → `confirmado` · `INFERRED` → `inferido` ·
  `AMBIGUOUS` → `lacuna` (requer validação humana).
- **Verificação pós-fase:** claim vindo do graphify sem fonte `arquivo:linha` + tag
  mapeada não entra no artefato (mesma regra do R25).
- **Arquivo citado que não existe:** antes de o claim entrar em artefato do ciclo,
  confira a existência do arquivo — inexistente marca o claim como `inferido`
  (código planejado, descrito em spec e ainda não escrito), nunca `confirmado`.
- **Fallback (ausente ou desabilitado):** fluxo atual (grep/Explore) com no máximo
  1 linha de aviso — degradação graciosa (RNF2).

## Apresentação a cliente/gestão/stakeholder (modo — delta-042, ADR-0029)

Materializa o fonte versionado da categoria (`.mmd`, `.dsl`, `.dbml`) como página editorial **HTML+SVG autocontida**, no archive, quando um artefato do doc-profile marca `apresentacao: true`. **Unidirecional por design:** o fonte em git é a única fonte de conteúdo; edição na materialização (HTML ou projeto claude.ai/design) nunca retorna; em divergência, o fonte governa e re-materializa.

- **Motor default — nativo, sem plugin.** O agente escreve o HTML seguindo [html-autocontido.md](html-autocontido.md), partindo de [exemplo-apresentacao.html](exemplo-apresentacao.html). **Não há motor de terceiro no caminho padrão** — um acabamento que vai à alta gestão não deve depender por default de plugin com bus factor 1.
- **Motor opcional (geração):** `apresentacao.motor: diagram-design` no perfil → skill `diagram-design` com o conteúdo do fonte versionado; identidade visual via onboarding da skill (site do cliente/projeto) ou `apresentacao.paleta` — ausente, paleta default sem bloquear.
- **Invocação (publicação):** `design-sync` publica os HTML num projeto claude.ai/design, **incremental** (list → plan → write, nunca replace integral) e **só por pedido explícito do usuário** — nunca automática.
- **Fora do caminho crítico:** o entregável congelado (doc-entregavel) segue exclusivamente no pipeline CLI; acabamento da camada entra no congelado só pelo caminho reprodutível `diagram-design:export` (HTML → PNG/SVG via Playwright) com a imagem embutida no pipeline.
- **Fallback:** `motor: diagram-design` declarado e o plugin ausente → **cai para o motor nativo** com no máximo 1 linha de aviso (RNF2) — o nativo é o piso, não o render CLI. `design-sync` sem autorização claude.ai → a camada fica local (HTML em git), 1 linha de aviso. Nenhum artefato marcado → nada é gerado e **nada é avisado**.

## Política de dependência (versões)

| Plugin | Versão testada | Faixa aceita | Verificado em | Substituibilidade / divergência upstream |
|---|---|---|---|---|
| `max@max4c-skills` | 0.8.0 | **fork deliberado, escopo reduzido a `write-prd`** — pin na testada ([ADR-0012](../../../docs/adrs/ADR-0012-recontratacao-motores.md) · [ADR-0026](../../../docs/adrs/ADR-0026-recontratacao-hibrida-clarify-no-oficial.md)) | 2026-08-09 | Clarify recontratado no oficial pela delta-039; o max segue **somente** como motor do PRD entrevistado da descoberta (R30) — upstream sem equivalente (`to-spec` é síntese sem entrevista). **Gatilho:** o upstream ganhar motor de PRD entrevistado, ou breaking no 0.8.0 distribuído. Forkável: em último caso copiar a SKILL.md do write-prd para o diretório de skills pessoais e apontar este adapter |
| `mattpocock-skills@claude-plugins-official` | 1.2.3 | faixa 1.x | 2026-08-09 (instalação real; `grilling`/`domain-modeling` presentes na lista de skills) | Motor do clarify e do spec-review ([ADR-0026](../../../docs/adrs/ADR-0026-recontratacao-hibrida-clarify-no-oficial.md)). Ponto sensível: `grill-me`/`grill-with-docs` upstream viraram stubs de `grilling` — invocar sempre os nomes novos; `to-tickets` avaliado e não adotado (projeção Jira segue no `tickets.py`, ADR-0021). Forkável (MIT) |
| `superpowers@claude-plugins-official` | 6.1.1 | faixa 6.x | 2026-07-28 (upstream 6.2.0 de 2026-07-24 — dentro da faixa, não testada) | **não forkável** — dependência real; mitigação = fallbacks acima |
| `ponytail@ponytail` | 4.8.4 | faixa 4.x | 2026-07-28 | forkável (ruleset markdown + hook simples) |
| `graphify` (CLI externo, PyPI `graphifyy`) | 0.9.32 | pin na testada — release quase diária, bus factor = 1 | 2026-08-02 (execução real num repo consumidor: 235 docs, 1.053 nós; contrato de proveniência confirmado, `AMBIGUOUS` só aparece fora do `--code-only`) | opcional com degradação total: ausente, nada do ciclo quebra |
| `diagram-design` (plugin de terceiro) | — (não testada — contrato pela doc upstream) | pin por commit/tag na primeira adoção real (mesmo padrão do graphify) | 2026-08-10 (MIT, bus factor = 1) | opcional com degradação total e **fora do caminho default** desde a delta-042 ([ADR-0029](../../../docs/adrs/ADR-0029-apresentacao-como-modo-e-html-autocontido-canonico.md)): só entra quando o perfil declara `apresentacao.motor: diagram-design`; ausente, cai para o motor nativo. A exposição ao bus factor 1 caiu de "todo acabamento" para "quem optou explicitamente" |
| `design-sync` (ferramenta do harness + serviço claude.ai) | n/a — serviço remoto, sem versão pinável | acompanhar o fluxo list → plan → write na doc da ferramenta | 2026-07-30 (contrato pela doc da ferramenta) | opcional com degradação total: sem login/escopo design, a camada fica local (HTML versionado em git) |

Re-verificação: toda delta que tocar este arquivo atualiza a coluna "Verificado em" dos motores que conferir.

O `projeto-init` (passo de verificação de plugins) confere nomes e versões contra a tabela de contrato acima na inicialização de cada projeto.
