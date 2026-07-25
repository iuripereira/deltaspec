# Changelog

Todas as mudanças notáveis deste projeto são documentadas aqui.

O formato segue [Keep a Changelog 1.0.0](https://keepachangelog.com/pt-BR/1.0.0/) e o projeto adere ao [Versionamento Semântico 2.0.0](https://semver.org/lang/pt-BR/). A versão canônica vive nas tags git `vX.Y.Z`.

<!-- Este arquivo nasceu na aplicação do projeto-init ao próprio repo. Mudanças anteriores à sua criação vivem no histórico git; abaixo estão as notáveis ainda não lançadas. -->

## [Não lançado]

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
