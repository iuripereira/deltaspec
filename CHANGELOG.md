# Changelog

Todas as mudanças notáveis deste projeto são documentadas aqui.

O formato segue [Keep a Changelog 1.0.0](https://keepachangelog.com/pt-BR/1.0.0/) e o projeto adere ao [Versionamento Semântico 2.0.0](https://semver.org/lang/pt-BR/). A versão canônica vive nas tags git `vX.Y.Z`.

Cada entrada é **uma linha** que diz o que mudou, com a referência do PR que conta a história ([ADR-0035](docs/adrs/ADR-0035-changelog-lancado-e-projecao-reescrevivel.md)).

<!-- Este arquivo nasceu na aplicação do projeto-init ao próprio repo. Mudanças anteriores à sua criação vivem no histórico git; abaixo estão as notáveis ainda não lançadas.
     A reescrita das versões antigas na forma de uma linha terminou nos PRs #233/#234/#235 (delta-062): o arquivo inteiro segue o formato. -->

## [Não lançado]

## [1.44.1] - 2026-08-24

### Corrigido

- Rodapé do CHANGELOG apontava um repositório de commits órfãos, onde `compare/` é 404; o C5 novo confere a correspondência heading ↔ rodapé (#320)

## [1.44.0] - 2026-08-24

### Corrigido

- C3 (`guarding-doc-integrity`) confundia link válido que escapa da raiz do repo com link morto em worktree aninhado — agora resolve pela raiz do repo principal (delta-085) (#315)

## [1.43.0] - 2026-08-24

### Adicionado

- Hook `guarda-sessao.py`: sessão concorrente no mesmo checkout e branch recebe `ask` antes da escrita, registrado nos três eventos do `.claude/settings.json` e no selftest do CI (#305)
- projeto-init detecta sinais de modelo de dados existente e oferece invocar a modelo-dados no init; fontes existentes alimentam a proposta de contrato (#307)

### Corrigido

- `.markdownlint.json` com `MD024.siblings_only` impede que o auto-fix do IDE renomeie headings duplicados válidos do CHANGELOG (ex.: `### Corrigido` → `### Corrigido — 0.4.0`) (#311)
- O workflow de Conventional Commits ignora commits vazios e segue cobrando o padrão nos commits que mudam arquivos (#311)

## [1.42.0] - 2026-08-24

### Adicionado

- O C4 mede cenário perdido dentro de bloco `MUDA`, nas duas pontas: contra o merge-base e contra o que a delta declara (#302)
- Check `C14`: delta aberta sob `plugins/marketplaces/` é ALTO, e clone raso vira BAIXO informativo explicando o silêncio do C4 e do C7 (#302)
- `--proximo-numero` soma os `NNN` de branches do `origin`, por `ls-remote` com fallback nos refs de rastreio já em disco (#302)

### Corrigido

- Seis ativos com `fila` fora da escala ou Gatilho invisível ao parser derrubavam a fila inteira de dívida — a priorização voltou a sair (#299)

## [1.41.0] - 2026-08-23

### Adicionado

- O gate de versão do `ci` consulta o repositório derivado e avisa quando ele fica atrás da tag corrente (#295)

### Corrigido

- Satélites do registro de débitos apontavam o `DEBT.md`, que é índice gerado, e a regra canônica não dizia que o cadastro é por comando (#294)

### Segurança

- O bypass do ruleset da `main` derivada saiu do papel Admin e passou a uma deploy key dedicada, exigida pelo publicador (#293)

## [1.40.0] - 2026-08-23

### Adicionado

- `debito.py novo` cadastra `DT-NNN` já validado, com o ID calculado sobre disco e refs remotos (#288)

## [1.39.0] - 2026-08-23

### Mudado

- Skill `eu-tenho-tdah` deixa de nomear o autor, declara os dois eixos e o README ganha seção própria do registro de débitos (#286)

## [1.38.0] - 2026-08-23

### Adicionado

- `DATA_DICTIONARY.md` refeito como camada semântica por campo (8 dimensões) e `check_data_model.py` com M4–M6 — cobertura `.dbml` ↔ dicionário, células decorativas e anti-tautologia (#275)
- Skill `modelo-dados`: modos `auditar` (grilling das lacunas do dicionário) e `padronizar` (cross-repo, 1 PR por repo com confirmação) (#276)

### Mudado

- Skill `eu-tenho-tdah`: a rota de captura dispara pela ausência de registro `debts/`/`DEBT.md`, não pela ausência de repo, e destino em repo git fecha com commit sem push (#285)

## [1.37.0] - 2026-08-22

### Adicionado

- Skill `git-guard`: catálogo canônico de anti-padrões de git, perfil de exigência por repositório e checks G1–G7 no `audit_workspace.py` (#280)

### Corrigido

- `core.hooksPath` deste checkout apontava para a estrutura de pastas anterior: o gate pré-commit não rodava, sem erro nem aviso (#278)

## [1.36.0] - 2026-08-22

### Adicionado

- Skill `pedido-insumos`: gera um e-mail de cobrança por dono, a partir dos registros de discovery do projeto (#277)

## [1.35.0] - 2026-08-20

### Adicionado

- Modelo de dados em três camadas: skill `modelo-dados`, `docs/data-model.md` com ERD derivado do `.dbml` e gate `check_data_model.py` (M1–M3) (#272, #273)

### Corrigido

- Delta-072: `audit-workspace` (W10) não confunde mais o repo-fonte de um plugin com cópia órfã ao comparar contra o próprio cache instalado (#270)

## [1.34.0] - 2026-08-20

### Mudado

- Delta-067 arquivada: R95 e o RNF5 alargado consolidados no TRUTH; as mudanças de comportamento já haviam saído na v1.33.0 (#244, #267)

## [1.33.4] - 2026-08-17

### Mudado

- Skill `eu-tenho-tdah` mais enxuta no caminho sempre carregado: description sem proveniência, proibições deduplicadas no leading word "registro, não convite" e rota fora-de-repo em `references/` (#261)

## [1.33.3] - 2026-08-17

### Segurança

- Estreia pública destravada: integridade do snapshot passa a abortar a publicação, doc sem link para a camada privada, instalação por clone e SECURITY.md melhor-esforço (#258)

## [1.33.2] - 2026-08-16

### Segurança

- Nome de branch deixa de ser interpolado dentro de `run:` no workflow de commits, e um gate novo reprova a classe em toda a árvore versionada (#256)

## [1.33.1] - 2026-08-16

### Corrigido

- Publicador não pode mais apagar a própria fonte: remote público sem default, snapshot vindo da tag, commit órfão de verdade e CI do derivado verde (#246)

## [1.33.0] - 2026-08-16

### Adicionado

- Skill `gerar-diagrama`: a categoria do diagrama decide a ferramenta, e o fonte `.excalidraw` nasce de gerador stdlib, sem dependência npm (#248)

### Mudado

- Pendência fora de repo passa a ter destino gravável — ledger local por padrão e inbox do vault sob pedido, no lugar da rota órfã `gtd-captura` (#244)
- O gate de portabilidade reprova caminho de máquina nas três árvores publicadas e admite caminho da home só sob `.claude/` (#244)

### Corrigido

- Publicar exige o repositório de destino declarado e recusa alvo igual à origem; o snapshot vem da tag e o commit é órfão de verdade (#246)

### Segurança

- Todo workflow declara `permissions: contents: read`, e dois identificadores de terceiro que sobreviviam pelo sufixo saíram do que é publicado (#246)

## [1.32.0] - 2026-08-15

### Adicionado

- `scripts/publica-dist.sh` deriva o repositório público de um allowlist, com um commit órfão por release (#241)
- Modo `--varre` do `guarda-confidencialidade.py`: a árvore publicável é conferida e a publicação aborta em qualquer achado (#241)

### Mudado

- O escopo da regra de identificador de terceiro passa a ser o allowlist de publicação, não todo artefato versionado (#241)
- O rodapé de comparação do CHANGELOG é truncado no snapshot público, onde os links não teriam histórico a apontar (#241)
- Identificador de terceiro sai dos 8 ADRs e do CHANGELOG que são publicados, com cada fato técnico preservado (#242)

## [1.31.0] - 2026-08-14

### Adicionado

- Hook `guarda-confidencialidade.py`: identificador de terceiro na escrita recebe `deny`, com a lista fora do git (#237)

### Mudado

- As skills passam a citar os casos de referência por pseudônimo, mantendo o fato técnico e omitindo o identificador (#237)

### Corrigido

- O entregável passa a sair em A4 nas duas saídas: o pdf fixava Letter no CSS e o docx herdava o default do Word (#238)
- Tabela de conteúdo do docx sai com borda de 0,5pt e largura da página, espelhando o pdf; bloco de assinaturas fica de fora (#238)

## [1.30.0] - 2026-08-14

### Adicionado

- Gate `check_changelog.py`: categoria PT-BR, tamanho do bullet, referência de PR e ordenação das seções (#231)

### Mudado

- A entrada do CHANGELOG passa a ser uma linha terminada na referência do PR, que é onde a história fica (#231)
- Escrever a entrada do CHANGELOG vira passo explícito das regras de archive do ciclo (#231)

## [1.29.0] - 2026-08-13

### Adicionado

- Skills de efeito colateral externo viram manual-only e a escrita em `_archive/` pede confirmação por hook PreToolUse (#227)

## [1.28.0] - 2026-08-13

### Adicionado

- Duplicações deliberadas saem do comentário e entram no `deps.toml` como `[[owner]]`; o RNF5 do CI passa a varrer `docs/` (#225)

## [1.27.0] - 2026-08-13

### Adicionado

- CI cobre 100% dos selftests e valida o schema do plugin pelo validador oficial — 804 linhas que nunca rodavam (#223)

## [1.26.3] - 2026-08-13

### Corrigido

- `CLAUDE.md` alinhado ao TRUTH particionado e às convenções invisíveis; a lista de selftests deixa de ser duplicada em parte (#222)

## [1.26.2] - 2026-08-13

### Corrigido

- `plugin.json.version` deixa de ser registro por disciplina e vira espelho vigiado da tag git, com gate próprio no CI (#219)

## [1.26.1] - 2026-08-13

### Corrigido

- `--proximo-numero` contava citação de delta de outro repo como delta local; menção solta agora respeita a contiguidade (#215)

## [1.26.0] - 2026-08-13

### Adicionado

- TRUTH legível: requisito vira heading, cenário vira bullet atômico e a verdade se parte em `specs/truth/<dominio>.md` (#207, #208)

### Mudado

- Template do TRUTH e regras de archive no formato novo; TRUTH legado em bullets continua válido, sem migração exigida (#212)

## [1.25.1] - 2026-08-13

### Corrigido

- "Próximo número livre" da delta deixa de ser fórmula de cabeça e vira `check_cycle.py --proximo-numero` (#201)

## [1.25.0] - 2026-08-12

### Adicionado

- Skill `rodada-insumos`: concilia cada insumo novo do cliente nos registros vivos, com gate de decisões em toda rodada (#202)

## [1.24.1] - 2026-08-12

### Corrigido

- O C4 não enxergava requisito com anotação de proveniência: dava CRÍTICO falso e deixava o já anotado fora da cobertura (#198)

## [1.24.0] - 2026-08-11

### Adicionado

- C13 no `check_cycle.py`: links relativos vivos em toda delta arquivada, reusando a resolução do C3 (#194)

### Mudado

- Regra 5 do archive: os links relativos são recalculados a partir do destino no mesmo passo do move (#194)

### Corrigido

- Faxina retroativa de 32 links mortos em 17 deltas arquivadas, sem nenhum órfão — todo alvo original existe (#194)

## [1.23.1] - 2026-08-11

### Corrigido

- `debito.py migrar`: célula com link markdown levava o link cru para a `descricao` e o título, nascendo morto (#193)

## [1.23.0] - 2026-08-11

### Adicionado

- Skill `ticket-to-jira`: contrato de projeção repo → Jira, com subset do ADF, templates por tipo e idempotência estrutural (#170)

## [1.22.0] - 2026-08-11

### Adicionado

- O DT encerrado ganha a seção `#### Como foi quitado`, em duas a quatro frases sem jargão de implementação (#191)

## [1.21.0] - 2026-08-11

### Adicionado

- Título humano `# [DT-NNN] - <descricao>` nos arquivos de débito, validado contra o frontmatter pelo `debito.py` (#188)
- `check_cycle.py` ganha o C13, importando `scan_links_c3()` em vez de reimplementar a resolução de link (#194)

### Corrigido

- Archive não quebra mais links relativos em silêncio: a regra 5 manda recalcular a profundidade no mesmo passo do move (#194)

## [1.20.0] - 2026-08-11

### Adicionado

- `debito.py indice`: regenera o `DEBT.md` da raiz como índice gerado dos ativos, por urgência — projeção, nunca fonte (#184)

### Mudado

- `debito.py fila` avisa quando o índice diverge do render atual, sem mudar o exit (#184)
- `debito.py migrar` escreve o índice gerado no lugar do ponteiro fino (#184)
- Regenerar o índice vira passo do cadastro e da quitação nos docs de processo (#184)

## [1.19.2] - 2026-08-11

### Corrigido

- `debito.py migrar`: o ponteiro do `DEBT.md` linkava arquivos inexistentes e o repo migrado nascia com link morto (#182)

## [1.19.1] - 2026-08-11

### Corrigido

- `debito.py migrar`: pipe escapado quebrava o alinhamento das colunas e linha de aridade divergente era adivinhada (#181)

## [1.19.0] - 2026-08-11

### Adicionado

- `debts/` na raiz como dono canônico do registro de dívida: um arquivo por item ativo, com frontmatter (#177)
- Subcomando `debito.py migrar`: converte registro legado sem inventar julgamento — fila ausente vira relatório de triagem (#176)
- Template `debts-README.md` no `projeto-init`: projeto novo nasce com `debts/` no lugar do `DEBT.md` de tabela (#179)

### Mudado

- `debito.py` em dual-mode: `debts/ativos/` tem precedência e o `DEBT.md` de blocos segue lido com aviso de deprecação (#176)
- Quitação vira editar e mover no mesmo commit; ativo e arquivado têm a mesma profundidade, então links não se reescrevem (#177)
- `DEBT.md` da raiz vira ponteiro fino e nunca é deletado, por causa dos links históricos (#177)
- C6 do `check_cycle.py` roteia pendência de archive para arquivo novo em `debts/ativos/`; satélites acompanham (#178)
- ADR-0030 supersede a ADR-0028 e derruba as renúncias a arquivo-por-item da ADR-0020; o modelo de fila segue intacto (#175)

### Corrigido

- Reescrita de link com texto igual ao alvo trocava o texto e matava o destino — corrigida por span do grupo (#176)
- `references/debito.md` citava uma constante inexistente e documentava `git log -S` onde o código usa `-G` (#176)

## [1.18.0] - 2026-08-10

### Mudado

- Apresentação deixa de ser categoria de diagrama e vira modo por artefato, materializado no archive como HTML autocontido (#168)
- O C5 mede o custo de contexto do TRUTH em três sinais — linhas, tokens aproximados e domínios —, todos BAIXO (#157)

### Adicionado

- ADR-0027: tokenizador real medido e recusado nos gates; a medição corrigiu o número registrado no DT-035 (#167)
- Regra canônica de HTML autocontido com dono único, que as três skills emissoras passam a linkar em vez de reproduzir (#168)
- DT-038 e DT-039 registram as duas renúncias da delta-042, cada uma com gatilho escrito (#167)

## [1.17.0] - 2026-08-10

### Adicionado

- Débito encerrado arquiva em arquivo próprio no mesmo commit da quitação, com linha-índice no `DEBT.md` (#159)

### Mudado

- `DEBT.md` vira registro em duas camadas; a migração retroativa de 24 quitados cortou o arquivo de 409 para ~230 linhas (#160)
- O skip de atalhos GitHub do C3 passa a casar a forma em qualquer profundidade — 22 falsos link-morto na migração (#159)

## [1.16.0] - 2026-08-09

### Mudado

- Clarify recontratado no plugin oficial: entram `grilling` e `domain-modeling`, e o fork do `max` reduz ao escopo `write-prd` (#154)

## [1.15.1] - 2026-08-09

### Mudado

- A fronteira entre `audit-workspace` e `guarding-doc-integrity` vira doutrina explícita nas duas SKILL.md (#151)

### Corrigido

- A SKILL.md da `audit-workspace` dizia que o W1 chama `--links-only` por subprocess; o código faz import direto (#151)

## [1.15.0] - 2026-08-09

### Mudado

- Handoff por sessão: o diário vira índice fino de ~30 linhas mais um arquivo por sessão, que nunca é podado (#148)

## [1.14.0] - 2026-08-09

### Adicionado

- Skill `audit-workspace`: auditoria de consistência entre repos de um workspace multi-repo, com modo repo/workspace detectado sozinho (#144)

## [1.13.0] - 2026-08-07

### Adicionado

- `debito.py exportar` lê o destino do ticket em `motores.jira.projeto` do `doc-profile.yaml`, em vez de exigir a flag (#140)

### Corrigido

- Ticket projetado no Jira saía com Markdown cru: novo `md_para_adf.py` converte o corpo, validado contra um Jira real (#139)

## [1.12.0] - 2026-08-07

### Adicionado

- `itens.py` vira dono canônico do formato de item do ciclo, antes espalhado em quatro regex de dois scripts (#137)

### Corrigido

- Parser do `check_cycle.py` tolera item multi-linha e acusa heading órfão em vez de perder o requisito em silêncio (#137)

## [1.11.0] - 2026-08-07

### Adicionado

- `tickets.md` por delta como projeção canônica das tasks para o Jira, com as arestas `dep:` viradas em links de bloqueio (#135)

### Corrigido

- `diagram-design` entra no `instala-motores.sh` e no README — estava contratado desde a delta-020 e fora do quickstart (#133)
- Dialeto Jira do `debito.py` vira `.sh` de creates unitários: o `create-bulk` rejeita `\n` na `description` (#135)
- Sintaxe do link de bloqueio corrigida contra o `acli` real — o subcomando é `link create`, com `--out`/`--in` (#135)

### Mudado

- Release passa a exigir revisão do processo e dos READMEs; a primeira aplicação achou quatro defasagens (#127)
- Pin do `max@max4c-skills` re-verificado e mantido como fork deliberado — ADR-0024 (#135)

## [1.10.1] - 2026-08-04

### Corrigido

- Bloco aninhado em item de lista chega inteiro ao pdf do cliente: o `deepen_indents` tinha três furos independentes (#123)

## [1.10.0] - 2026-08-04

### Adicionado

- `--rodape` e `--marca-dagua` no `exporta_entregavel.py`: a marca do confidencial sai do export, nos dois formatos (#121)

## [1.9.0] - 2026-08-04

### Mudado

- Número medido em cenário do TRUTH passa a entrar datado, para não apodrecer em silêncio a cada MUDA (#119)

## [1.8.1] - 2026-08-03

### Corrigido

- O C3 acusava histórico imutável e sintaxe citada; num repo consumidor os links mortos caíram de 96 para 3 (#113)

## [1.8.0] - 2026-08-03

### Mudado

- O campo `version` sai do `doc-profile.yaml` — nenhum consumidor o lia e ele já nascera incoerente (#111)
- A política de dependência passa a ser verificada pelo `deps.toml` do próprio framework, e não por `grep` no CI (#111)

## [1.7.1] - 2026-08-03

### Corrigido

- O C3 deixava `CHANGELOG.md`, `HANDOFF.md`, `DEBT.md` e as ADRs sem verificação de link; saltou de 105 para 171 links (#109)

### Adicionado

- `doc-profile.yaml` na raiz deste repositório — o framework exigia dos projetos a decisão que não tinha registrado (#107)

## [1.7.0] - 2026-08-02

### Adicionado

- C11 e C12 no gate: schema do `doc-profile.yaml` com cauda tolerada, e trilha do clarify exigida no perfil completo (#105)

### Mudado

- O clarify não fecha mais sem declarar se teve canal humano — exploração do repo não conta como resposta do usuário (#105)
- `PyYAML` vira a única dependência externa admitida dos gates, com o parser próprio recusado por falhar em silêncio (#105)

## [1.6.0] - 2026-08-02

### Adicionado

- Campo `motores.graphify_backend` no template do `doc-profile.yaml`: vazio com indexação pedida faz a IA parar e perguntar (#103)

### Mudado

- Contrato do graphify ganha pin verificado por execução real, e o adapter passa a declarar o que cada modo cega (#103)
- A ADR-0022 supersede a ADR-0014 na cláusula "`--code-only` preferido": o modo cega todo arquivo não-código (#103)

## [1.5.0] - 2026-08-01

### Mudado

- O `DEBT.md` vira um bloco por item com referências navegáveis; a tabela de 11 colunas chegava a 1.549 caracteres por linha (#101)
- `stale` passa a medir decisão, não edição: o relógio do aging reinicia quando o estado muda (#101)

## [1.4.0] - 2026-08-01

### Adicionado

- Dívida técnica com score determinístico calculado na leitura e nunca gravado, mais projeção para Jira e GitHub (#97)
- A ADR-0021 substitui a ADR-0007 na parte das Issues, pela cláusula que a própria ADR-0007 havia escrito (#97)

## [1.3.0] - 2026-07-31

## [1.2.0] - 2026-07-31

### Adicionado

- `status-pmo` ganha o nível épico/tarefa com dependências, página por épico e grafo em SVG inline (#83)
- Skill `status-pmo`: site de status PMO em seis gates, com templates e paleta por tokens de CSS (#81)
- Abertura à comunidade: `README.en.md` como espelho sancionado, `CONTRIBUTING.md` e código de conduta (#79)

## [1.1.0] - 2026-07-30

### Adicionado

- `SECURITY.md` no padrão da comunidade: reporte privado por advisory, SLA explícito e modelo de ameaça de ferramenta local (#76)

### Mudado

- Camada de apresentação troca Figma/FigJam por `diagram-design` + `design-sync`, com o `.mmd` seguindo como fonte única (#77)
- README reescrito como quickstart, em oito seções e sem jargão; as skills viram tabela que linka cada `SKILL.md` (#71)
- Diagramas Mermaid ganham tema claro; a `fontFamily` customizada ficou de fora porque o `mmdc` cortava o texto do nó (#71)

### Removido

- Seção de migração `sdd-iuri` → `deltaspec` do README: a varredura dos consumidores fechou e o rename está concluído (#71)
- Detalhamento do README que já tem dono em outro arquivo — tabela dos checks, CLIs de diagrama e convenções (#71)

## [1.0.0] - 2026-07-28

### Adicionado

- Guia de migração no README e guarda do registro histórico: `_archive/`, ADRs e changelog lançado preservam o nome de época (#67)
- ADR-0016 registra a escolha do nome, com `delta-spec` descartado por colisão de nicho e a camada de compatibilidade recusada (#67)

### Mudado

- **BREAKING** o framework passa a se chamar `deltaspec`: namespace, instalação e chave do hook mudam, sem camada de compatibilidade (#67)
- README reescrito em chave didática, com a analogia "delta spec = commit de requisito" e seis diagramas Mermaid (#66)

## [0.13.0] - 2026-07-28

### Adicionado

- Figma/FigJam como camada de apresentação a cliente, em fluxo unidirecional a partir do `.mmd`, que governa (#63)
- Figma MCP nos adapters, com o ponto sensível beta→pago declarado e o entregável congelado fora do caminho (#63)
- Reserva explícita de número de delta: o usuário pode saltar um número, com a reserva citada no spec (#63)
- ADR-0015: veredito híbrido com as renúncias e as limitações registradas, incluindo o export FigJam não verificado (#63)

## [0.12.0] - 2026-07-28

### Adicionado

- Arestas de bloqueio `(dep: Tn)` no `tasks.md`, com o C9 validando existência e aciclicidade (#61)
- C10 — convergência mínima no archive: delta arquivada com task `- [ ]` remanescente vira ALTO (#61)
- Execução paralela por worktree: unidades sem caminho entre si rodam em subagentes isolados (#61)
- `references/harness.md`: vocabulário canônico de harness, dono único que os demais docs linkam (#61)
- Trilha de auditoria de aprovação como linha citável no artefato da própria fase, sem `audit.md` separado (#61)
- graphify como quarto motor externo opcional, com instalação manual consciente e fallback grep/Explore (#61)
- ADR-0014: renúncias das quatro decisões — audit.md, converge semântico, grafo no graphify e auto-install (#61)

### Mudado

- `check_cycle.py` passa a C1–C10; templates, `cycle.md`, `adapters.md` e READMEs refletem grafo, worktrees e graphify (#61)

## [0.11.0] - 2026-07-28

### Adicionado

- Perfil de execução por delta (`completo|enxuto`), proposto pela IA e válido só com aprovação do usuário (#58)
- Prototipação opcional como estágio CONDITIONAL, com a forma decidida pela categoria `prototipo` do perfil (#58)
- Plano de testes como artefato `test-plan.md`, validado pelo C8 — teste manual roteirizado conta como cobertura (#58)
- Tipo `bugfix` com template próprio e pipeline curto; o TRUTH só consolida quando o bugfix muda requisito (#58)
- ADR-0013: renúncias das três decisões de desenho — composição do enxuto, forma do protótipo e pipeline do bugfix (#58)

### Mudado

- `check_cycle.py` passa a C1–C8; o R35 ganha exceção de fusão de eixos no perfil enxuto (#58)

## [0.10.0] - 2026-07-28

### Adicionado

- ADR-0012: o pin do `max@0.8.0` vira fork deliberado, com gatilho de migração marcado na delta-017 (#55)
- Review em dois eixos paralelos, com fallback inline sequencial quando o motor falta (#55)

### Mudado

- Política de dependência dos adapters ganha verificação datada por motor, e o índice de ADRs é atualizado (#55)

## [0.9.0] - 2026-07-28

### Adicionado

- Step de CI que compara cada `skills/<nome>/` com as descrições dos dois manifestos e falha nomeando a skill ausente (#53)
- Hook pré-commit versionado em `.githooks/`, com oferta opt-in no bootstrap da `guarding-doc-integrity` (#53)

### Mudado

- Manifestos passam a citar as nove skills; `eu-tenho-tdah` reconhecida como skill do plugin (#53)
- ADR-0009 promovida a Accepted e `doc-entregavel` sai de experimental no README (#53)
- Promessas do DT-005 alinhadas ao mecanismo real em `deps.toml`, SKILL.md, regra canônica e README (#53)

## [0.8.0] - 2026-07-27

### Adicionado

- Skill `descoberta`: fase pré-specify do ciclo — mineração de insumo bruto em dossiê as-is com claims tagueados e rastreáveis (#50)

## [0.7.0] - 2026-07-26

### Adicionado

- `doc-entregavel` despacha por tipo e ganha os jurídico-comerciais: `juridico-nda`, `juridico-contrato-ti` e `requisitos-cliente` (#48)
- `requisitos-cliente` exige orçamento por fase, prazo e cronograma, em duas versões por regra de proteção de PI (#48)

### Corrigido

- Base jurídica da assinatura eletrônica estava invertida: o CPC admite qualquer modalidade e o STJ dispensa ICP-Brasil (#48)
- Lacunas de praxe nos tipos jurídicos: segredo de negócio no NDA; reversibilidade, SLA, incidente e uso de IA no contrato de TI (#48)
- `check_cycle.py`: o C4 lia só o índice e acusava CRÍTICO falso de perda em TRUTH particionado (#47)
- `check_cycle.py` aceita a notação `RF-NN`/`RNF-NN` além de `Rn`, com numeração hierárquica opcional (#47)

## [0.6.0] - 2026-07-24

### Adicionado

- Sumário automático no formato de contrato, com número de página obtido em duas passadas de render (#43)
- Corpo justificado nos dois formatos de export, com hifenização pt-BR no pdf (#43)
- Skill `eu-tenho-tdah`: perfil de escrita pessoal do Iuri, fora do ciclo de delta specs (#42)
- `handoff` imprime o prompt de retomada ao fechar a sessão (#36)
- Stack de diagramas com vínculo normativo categoria → ferramenta, incluindo Excalidraw e Structurizr (#33)
- Regras de página no entregável: tabela sem corte com cabeçalho repetido, diagrama em página própria e em paisagem (#33)
- Guia normativo de prosa em `references/prosa.md`: uma regra por frase, DEVE/NÃO DEVE/PODE, tabela de decisão (#33)
- Comandos de render para `.dsl` (structurizr) e `.excalidraw`, com toolchain validada de ponta a ponta (#33)
- Documentação visual vira gate configurável pelo `doc-profile.yaml` — ADR-0009 (#30)
- Skill `doc-entregavel`: congela o entregável cliente e exporta PDF/DOCX versionado com capa de assinatura (#30)
- `tabela_cliente.py`: cenários DADO/QUANDO/ENTÃO viram tabela no formato cliente, com `--selftest` (#32)
- `check_cycle.py` ganha o C7, que mede o split de PR contra o limiar canônico (#28)
- `deps.toml` passa a governar dois limiares antes duplicados sem sanção (#27)
- `scripts/instala-motores.sh`: instala os três motores de terceiros numa chamada só (#40)

### Mudado

- **BREAKING** `STATE.md` renomeado para `HANDOFF.md` em todo o framework; a skill `handoff` migra em runtime (#44, #45)
- README reescrito para leitura humana: estados e ciclo em Mermaid, instalação em três comandos (#38)
- delta-009 arquivada: MUDA R12 consolidado no `TRUTH.md` e DT-003 quitado (#29)
- Espelhos do limiar de tamanho de PR enxugados de quatro para um (#27)

### Corrigido

- `tabela_cliente.py` localiza as seções de RF/RNF pelo título, não pelos números fixos de seção (#39)
- `tabela_cliente.py`: a tabela saía colada no heading seguinte e a cauda após o último RNF era descartada (#32)
- `.fig-pagina`: o `<p>` do `md_in_html` quebrava a cadeia de `max-height` no print do Chrome (#34)
- Render do PNG mermaid passa a exigir a largura nativa do SVG — no viewport default o diagrama largo saía borrado (#31)
- Quebra de linha manual removida da prosa em 27 arquivos `.md`, com histórico imutável de fora (#26)

## [0.5.1] - 2026-07-20

### Adicionado

- ADR-0008: skill `handoff` própria, com as renúncias a vendorizar e a delegar registradas em Nygard (#25)
- `DEBT.md` ganha o DT-008 e a lição do grep case-sensitive que deixou passar "Cinco skills" no manifesto (#25)

### Corrigido

- `marketplace.json` enumerava cinco skills sem a `handoff` — executor esquecido pela delta-008 (#25)
- Executores e resumos defasados alinhados ao TRUTH vigente: README, docstring do gate, `ci.yml` e templates (#25)

## [0.5.0] - 2026-07-20

### Adicionado

- Skill `sdd-iuri:handoff`: fecha a sessão nos registros com dono, roteando débito e lição para o `DEBT.md` (#23)

### Mudado

- A contagem de skills sai da redação viva — skill nova não exige mais rodada de MUDA por causa de um numeral (#23)
- delta-008 arquivada: R20 e MUDA R15 consolidados no `TRUTH.md` (#24)

## [0.4.0] - 2026-07-20

### Adicionado

- `DEBT.md` na raiz: registro canônico de débito, pendências e lições com IDs `DT-NNN`, e backfill DT-001..DT-007 (#21)
- Backfill de cinco ADRs — decisões-com-renúncia que já vigiam ganham registro Nygard (#20)
- Arquivo `LICENSE` (MIT), que o `plugin.json` já declarava sem que existisse (#19)

### Mudado

- `STATE.md` deixa de acumular quatro naturezas e vira diário de bordo em janela rolante (#21)
- Pendência roteada no archive muda de destino: de "Decisões em aberto" do `STATE.md` para `DT-NNN` no `DEBT.md` (#21)
- delta-007 arquivada: MUDA R16 e R18/R19 consolidados no `TRUTH.md` (#22)
- `CLAUDE.md` registra convenções já praticadas e nunca escritas: escopo de commit, corte da tag e merge por squash (#19)

### Corrigido

- Os três comandos de teste do `CLAUDE.md` ganham o prefixo `skills/`, quebrados desde a delta-001 (#19)
- `README.md` passa a listar os sete steps reais do check `ci` (#19)

## [0.3.0] - 2026-07-19

### Adicionado

- `check_cycle.py` reconhece a notação `delta-NNN` além do símbolo legado `Δ` nos alvos de MUDA/REMOVE (#17)

### Mudado

- Notação viva das deltas passa de `ΔNNN` para `delta-NNN`; o histórico imutável preserva o `Δ` (#17)
- delta-006 arquivada: MUDA R6/R7/R12 consolidados no `TRUTH.md` (#18)

## [0.2.2] - 2026-07-19

### Corrigido

- `adapters.md` declara o fallback do review estágio 1, fechando o furo do RNF2 apontado pela revisão do backfill (#15)

### Mudado

- Δ005 arquivada: MUDA R13/RNF2/RNF3 consolidados no `TRUTH.md` (#16)

## [0.2.1] - 2026-07-19

### Mudado

- Δ003 arquivada: R17 consolidado no `TRUTH.md` (#12)
- Δ004 arquivada: MUDA R13 consolidado no `TRUTH.md` (#14)

### Corrigido

- `templates/deps.toml`: excludes `**`-final, no-op em `pathlib` ≤ 3.12, trocados pela forma portável `**/*.md` (#13)

## [0.2.0] - 2026-07-19

### Adicionado

- Split condicional do PR de delta: artefatos acima do limiar canônico mergeiam num PR próprio antes do implement (#11)

## [0.1.0] - 2026-07-19

Primeiro release: cria o baseline SemVer do repositório. Tudo abaixo estava acumulado desde o início do projeto (PRs #1–#9).

### Adicionado

- `deps.toml` na raiz: os limiares espelhados do framework ganham dono e o validador roda contra o próprio repo no `ci` (#9)
- `check_cycle.py` ganha o C6: pendência aberta em delta arquivada é acusada até ser roteada (#7)
- Selftest do C4 com repositório git real, cobrindo perda pós-commit e falso positivo de MUDA (#7)
- Distribuição como plugin do Claude Code, instalável por `/plugin marketplace add iuripereira/sdd-iuri` (#5)
- Step de CI que reprova caminho absoluto de máquina em `skills/` e `.github/` (#5)
- `check_cycle.py` — gate determinístico do ciclo, com os checks C1 a C5 e saída 1 em ALTO/CRÍTICO (#2)
- `guarding-doc-integrity` integrada ao framework como executora da regra de propagação (#3)
- Scaffold do próprio repositório via `projeto-init`, com `TRUTH.md` em backfill do estado vigente (#4)
- Validação de TOML e execução dos `--selftest` dos gates no job `ci` (#4)

### Mudado

- **BREAKING** as cinco skills passam a ser invocadas sob o namespace `sdd-iuri:` (#5)
- A saída do `check_cycle.py` declara-se parcial: os checks 3 e 5 do analyze continuam humanos (#7)
- Grep de portabilidade do CI cobre `$HOME/.claude/skills` e `/home/<user>/.claude/skills` (#7)
- Os scripts de gate resolvem o próprio caminho por `${CLAUDE_PLUGIN_ROOT}` (#5)
- `.gitignore` deixa de ser allowlist: fora de `~/.claude/skills/` o repositório contém só o framework (#5)
- `canonical-rules.md`: a regra de propagação aponta `deps.toml` + `guarding-doc-integrity` (#3)
- `templates/deps.toml`: o dono do exemplo passa de `PRD.md`, que o `projeto-init` nunca cria, para `specs/TRUTH.md` (#3)
- `analyze.md`, `cycle.md` e `spec-feature/SKILL.md` invocam o gate mecânico antes da leitura de juízo (#2)

### Segurança

- `.gitignore` ganha bloco de secrets: sem ele, a allowlist re-incluía o diretório da skill e versionaria `.env` (#4)

### Corrigido

- `check_cycle.py`: o C4 compara contra o merge-base da branch com a main, fechando a janela cega pós-commit (#7)
- README: a instalação manual por `cp -r` não copiava `guarding-doc-integrity`, deixando a skill inalcançável (#3)

<!--
No release: renomeie "[Não lançado]" para "## [X.Y.Z] - AAAA-MM-DD", abra uma nova seção "[Não lançado]" vazia acima, e crie a tag git vX.Y.Z. Bump derivado dos commits: fix→PATCH, feat→MINOR, !/BREAKING CHANGE→MAJOR (o maior vence). -->

