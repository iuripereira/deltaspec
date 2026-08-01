# deltaspec — Fonte da verdade
<!-- consolidado a cada archive; histórico das deltas em specs/_archive/ -->
<!-- particionamento: >~800 linhas ou >~10 domínios → truth/<dominio>.md e este vira índice -->
<!-- delta-000 = backfill do estado pré-ciclo (PRs #1–#3), consolidado no projeto-init deste repo. Deltas reais começam em delta-001. -->

## Inicialização de projeto

- R1 (delta-001) — a skill `projeto-init` classifica o repositório e monta o `CLAUDE.md`.
  - DADO um repositório sem `CLAUDE.md` QUANDO a skill `projeto-init` roda ENTÃO o tipo é classificado pela tabela de `detection.md` e o `CLAUDE.md` contém os módulos que a matriz marca para o tipo, com o texto copiado de `canonical-rules.md`
- R2 (delta-000) — o init nunca sobrescreve arquivo existente.
  - DADO um `CLAUDE.md` já presente QUANDO o init roda ENTÃO ele grava `CLAUDE.generated.md` ao lado e mostra o diff, deixando a decisão de merge com o usuário
  - DADO um `.gitignore` já presente QUANDO o init roda ENTÃO o bloco de secrets é anexado (append), nunca substituído
- R3 (delta-000) — o scaffold criado varia por tipo.
  - DADO o tipo detectado QUANDO o scaffold roda ENTÃO só são criados os arquivos que a matriz de `detection.md` marca para aquele tipo, e só os que ainda não existem
  - DADO um tipo com ciclo QUANDO o scaffold roda ENTÃO cria `specs/` + `TRUTH.md`, e **não** `docs/specs/` + `SPEC-TEMPLATE.md`
- R18 (delta-023) — DEBT.md é o registro canônico de débito, pendências e lições, com IDs estáveis, priorização e ciclo de vida.
  - DADO um débito, pendência ou guarda novo QUANDO registrado ENTÃO entra no `DEBT.md` da raiz como linha `DT-NNN` (próximo número livre — numeração global, nunca reutilizada) com natureza, título curto, descrição, localização, origem, data de abertura, fila, gatilho de correção, status e chave externa
  - DADO um item quitado QUANDO a correção mergeia ENTÃO o status do item muda para quitado, com data — a linha nunca é apagada (a trajetória aberto→quitado é o registro da evolução)
  - DADO um tipo de projeto que recebe `docs/adrs/` na matriz de detection.md QUANDO o scaffold do projeto-init roda ENTÃO cria também `DEBT.md` a partir do template da skill, e só se não existir
  - DADO um item de natureza `débito` ou `pendência` QUANDO ele é registrado ENTÃO carrega `Título` (sintoma observável, não adjetivo), `Local` (link relativo a artefato real do repo) e `Fila` (`P{1|3|9}·J{1|3|9}·Pr{1|3|9}`, com sufixo opcional `trilha` ou `!<override>(AAAA-MM-DD)`); item de natureza `guarda` fica com `—` nos três, por não ter principal nem juros
  - DADO os estados do registro QUANDO um item muda de situação ENTÃO vale o conjunto `aberto` · `aceito (gatilho obrigatório)` · `vigente` (guarda permanente) · `descartado (AAAA-MM-DD, motivo)` · `quitado (AAAA-MM-DD, ref)`, e `stale` **nunca é escrito** — é derivado do git pelo script
  - DADO uma tabela no formato anterior à delta-023 (sem a coluna `Fila`) QUANDO o script a lê ENTÃO o registro segue válido e apenas a fila se omite, com aviso — retrocompatível, sem migração forçada
- R51 (delta-023) — a fila de dívida é determinística, calculada por script e nunca persistida.
  - DADO um `DEBT.md` no formato do R18 QUANDO `debito.py fila` roda ENTÃO ele imprime a fila ordenada por `override` primeiro, `trilha` em seguida e `score` decrescente no resto, com `score = (juros × probabilidade) / principal` calculado na leitura — o valor **não é gravado** em nenhum arquivo
  - DADO um item pontuável sem `Local`, com link de `Local` morto, sem `Título`, com `Fila` malformada, com `aceito` sem gatilho ou com estado encerrado sem data QUANDO o script roda ENTÃO ele reporta erro nomeando o `DT-NNN` e o campo, e sai com código ≠ 0
  - DADO o repositório com git QUANDO o script roda ENTÃO a probabilidade de incidência é derivada do churn do arquivo apontado em `Local` e a divergência contra o valor declarado é reportada — a derivação informa, o valor declarado decide; sem git, a conferência se omite com aviso
  - DADO um item com juros ≥ 3 cuja linha não muda há mais que o limiar de dias QUANDO o script roda ENTÃO ele é marcado `stale` na saída (data via `git log -G`, que reconhece edição de linha), forçando decisão entre agendar, aceitar ou descartar
  - DADO o parsing da tabela QUANDO o script lê uma linha ENTÃO cada campo é lido pela **posição da coluna**, nunca por busca de texto na linha — prosa que mencione a sintaxe não pode ser confundida com o campo
- R52 (delta-023) — ferramenta de ticket é projeção do registro, com ida mecânica e volta aprovada.
  - DADO o `DEBT.md` QUANDO `debito.py exportar` roda ENTÃO ele emite o JSON canônico e os dialetos de importação em arquivos, **sem acessar a rede** — quem executa os comandos é a skill, nunca o script; o dialeto que exige chave de projeto só é emitido quando ela é informada
  - DADO um item projetado QUANDO o ticket é criado ENTÃO ele carrega a etiqueta determinística com o `DT-NNN` e o título prefixado pelo ID, e a chave devolvida (`gh#NNN`, `PROJ-NNN`) é gravada na coluna `Externo` — é ela, e não o título, que garante idempotência
  - DADO o estado coletado da ferramenta QUANDO `debito.py diff` roda ENTÃO ele emite a tabela *DEBT.md diz × ferramenta diz × impacto × ação proposta* (formato do R27), cobrindo item sem ticket, ticket fechado com item ativo e ticket sem item correspondente
  - DADO uma divergência detectada QUANDO ela vira mudança no `DEBT.md` ENTÃO a alteração é **proposta e só aplicada após aprovação humana** — a ferramenta externa nunca sobrescreve o arquivo, que permanece a fonte da verdade
  - DADO a ferramenta ausente, sem autenticação ou sem projeto configurado QUANDO a projeção é invocada ENTÃO o `DEBT.md` segue valendo sozinho, com no máximo 1 linha de aviso (RNF2)
- R19 (delta-010) — HANDOFF.md é diário de bordo, não acumulador de estado.
  - DADO o template HANDOFF.md do projeto-init QUANDO o scaffold cria o arquivo ENTÃO o formato tem as seções "Agora", "Feito recentemente", "Problemas atuais" e "Próximos passos imediatos", com janela rolante declarada e a regra de merge "união das verdades" mantida
  - DADO conteúdo que tem dono próprio (as-built → TRUTH.md/README, débito/pendência/lição → DEBT.md, decisão com renúncia → ADR, histórico → CHANGELOG) QUANDO ele surgir no HANDOFF.md ENTÃO é movido para o dono no mesmo bloco de trabalho e o HANDOFF.md apenas referencia
  - DADO as referências ativas do framework (CLAUDE.md, canonical-rules.md, detection.md, deps.toml, README, template) QUANDO nomeiam o diário de bordo ENTÃO usam `HANDOFF.md`, não `STATE.md`, e não há dois donos de "onde paramos" — arquivos imutáveis (`specs/_archive/**`, ADRs Accepted, CHANGELOG lançado) preservam o nome histórico (guarda DT-010)

## Infraestrutura

- R4 (delta-001) — a skill `projeto-infra` configura a infraestrutura e é idempotente.
  - DADO um repositório já configurado QUANDO a skill `projeto-infra` roda de novo ENTÃO ela consulta o que existe, preenche só as lacunas e relata no-op no restante
  - DADO falha de infra (sem rede, `gh` não autenticado) QUANDO o init a invoca ENTÃO o init reporta e segue, sem travar

## Descoberta (pré-specify)

- R24 (delta-019) — a skill `descoberta` cobre a fase pré-specify, produzindo dossiê a partir de insumos brutos.
  - DADO um projeto com insumos brutos de descoberta (transcrição/resumo de reunião, planilha, vídeo, docs legados) QUANDO `/deltaspec:descoberta` roda ENTÃO ela inventaria os insumos (o que existe, o que falta, pessoas-fonte, sistemas citados) e grava o dossiê em `docs/discovery/AAAA-MM-DD-<evento>.md` com o processo as-is, entidades, regras e dores minerados
  - DADO um vídeo entre os insumos QUANDO `ffmpeg` está disponível ENTÃO frames amostrados (scene detection + intervalo fixo) dos trechos relevantes são fonte válida de mineração; `ffmpeg` ausente → o vídeo entra no inventário como lacuna, com aviso, sem quebrar a skill
- R25 (delta-012) — todo claim do dossiê carrega nível de confiança e fonte rastreável.
  - DADO um claim extraído dos insumos QUANDO registrado no dossiê ENTÃO carrega uma tag `confirmado` (evidência direta), `inferido` (dedução/padrão) ou `lacuna` (requer validação humana) e a fonte rastreável (timestamp da transcrição, `arquivo:linha` ou frame); claim sem fonte não entra no dossiê
- R26 (delta-012) — a descoberta popula GLOSSARY.md e DATA_DICTIONARY.md.
  - DADO termos de domínio e entidades minerados QUANDO o dossiê fecha ENTÃO `GLOSSARY.md` e `DATA_DICTIONARY.md` do projeto recebem as entradas novas com o nível de confiança, por append/merge — entrada existente nunca é sobrescrita sem divergência apontada
- R27 (delta-012) — divergências contra a baseline vigente.
  - DADO um PRD ou TRUTH.md vigente no projeto QUANDO a mineração encontra contradição ou omissão ENTÃO gera `docs/discovery/divergencias-<baseline>.md` com tabela *baseline diz × descoberta revelou × impacto (IDs afetados) × ação proposta*
  - DADO um projeto sem baseline QUANDO a skill roda ENTÃO a etapa de divergências se omite com aviso
- R28 (delta-012) — pauta de validação em Mob Elaboration.
  - DADO o dossiê fechado QUANDO a skill encerra ENTÃO existem `docs/discovery/questions.md` (perguntas ranqueadas por dono/stakeholder) e um roteiro de sessão de validação em que a IA propõe o entendimento claim a claim e o stakeholder valida/corrige (Mob Elaboration; Domain Storytelling como técnica de condução)
- R29 (delta-012) — presunção não vira requisito sem validação.
  - DADO claims `inferido` ou `lacuna` QUANDO o resultado da descoberta alimenta um PRD ou o specify ENTÃO eles entram marcados `[PRESUNÇÃO]`; somente claim `confirmado` ou validado em sessão entra sem marca
- R30 (delta-012) — ponte da descoberta com o ciclo registrada nos adapters.
  - DADO o plugin `max` instalado QUANDO a descoberta encerra ENTÃO a skill oferece `max:write-prd` como motor do PRD rascunho, com o dossiê como contexto e o contrato de `[PRESUNÇÃO]` na invocação; `max` ausente → fallback nativo (PRD rascunho próprio) com o aviso de degradação
  - DADO a tabela de contrato de `adapters.md` QUANDO a delta consolida ENTÃO existe a linha da fase `descoberta` (pré-specify) com skill esperada, ponto sensível e fallback

## Ciclo de features

- R5 (delta-018) — uma feature é uma delta spec, com numeração global ao repositório e reserva explícita admitida.
  - DADO um incremento novo QUANDO a skill `spec-feature` abre a delta ENTÃO cria `specs/NNN-nome/` com `NNN` = max(`specs/`, `specs/_archive/`) + 1 e a branch `tipo/NNN-nome`
  - DADO uma versão maior do projeto QUANDO uma delta nova é aberta ENTÃO a numeração continua do maior existente e nunca reinicia
  - DADO uma reserva de número declarada explicitamente pelo usuário QUANDO uma delta abre ENTÃO ela pode saltar o número reservado (ou consumi-lo, se for a delta reservada), mantendo a unicidade global — nenhum número é reutilizado, e tanto a delta que salta quanto a que consome citam a reserva de forma citável no spec (padrão R43)
- R6 (delta-006) — a delta declara só o que muda em relação ao TRUTH.md.
  - DADO o `TRUTH.md` vigente QUANDO a spec é redigida ENTÃO cada bloco é ADICIONA, MUDA ou REMOVE, e blocos MUDA/REMOVE citam o alvo vigente (ex.: "MUDA R2 (delta-001)")
  - DADO um requisito na delta QUANDO a spec é validada ENTÃO ele tem cenário DADO/QUANDO/ENTÃO verificável; qualidade sem limiar fechado vira pendência em riscos, não RNF
- R7 (delta-006) — a delta percorre os estados proposta → aplicada → arquivada, e o archive faz parte do "pronto".
  - DADO um PR mergeado QUANDO o archive roda ENTÃO o spec.md vira `Estado: arquivada`, o requisito é consolidado no `TRUTH.md` com sufixo `(delta-NNN)` e o diretório move para `specs/_archive/NNN-nome/`
  - DADO um bloco MUDA QUANDO o archive consolida ENTÃO o requisito vigente é substituído **integralmente** pelo bloco da delta — a consolidação é mecânica, não infere intenção
- R8 (delta-000) — as fases do pipeline são delegadas a motores de terceiros por contrato.
  - DADO a fase clarify/plan/implement/review QUANDO ela roda ENTÃO o motor é o declarado em `adapters.md`, invocado com o contrato de formato/destino e verificado após a fase
- R9 (delta-000) — plugin ausente degrada a fase, nunca quebra o ciclo.
  - DADO um plugin não instalado QUANDO a fase que depende dele roda ENTÃO o fallback documentado em `adapters.md` assume e o usuário recebe aviso explícito de qual fase degradou
- R10 (delta-001) — o ciclo aplicável varia por tipo.
  - DADO um projeto `site-estatico` QUANDO o ciclo roda ENTÃO é o reduzido (specify → plan → implement → review), com clarify e analyze sob demanda
  - DADO um projeto `workspace-dados` QUANDO a skill `spec-feature` é invocada ENTÃO ela recusa com explicação e aponta o scaffold estático do `projeto-init`
- R16 (delta-007) — pendência de risco sobrevive ao archive — roteada para o DEBT.md.
  - DADO uma delta com pendência aberta (item `- [ ]` em "Dependências e riscos") QUANDO o archive roda ENTÃO a pendência é registrada no `DEBT.md` como item `DT-NNN` de natureza pendência, com origem `delta-NNN`, e o item do spec vira `- [x]`, no mesmo commit da consolidação
  - DADO uma delta arquivada QUANDO o C6 roda ENTÃO acusa ALTO por delta com item `- [ ]` remanescente na seção "Dependências e riscos" do `spec.md`, reportando a contagem de itens
- R34 (delta-014) — política de pins com verificação datada e divergência upstream registrada.
  - DADO a tabela de política de dependência em `adapters.md` QUANDO a delta consolida ENTÃO cada motor declara versão testada, faixa aceita, data da última verificação e, quando houver, nota de divergência upstream com gatilho de reavaliação — para o max: fork deliberado da 0.8.0 (upstream removeu `write-prd` e fatorou `grilling`), gatilho na delta-017 (ADR-0012)
  - DADO o superpowers verificado em 2026-07-28 QUANDO a tabela é lida ENTÃO ela registra a última upstream verificada (6.2.0, dentro da faixa 6.x) sem alegar teste que não ocorreu (testada segue 6.1.1)
- R35 (delta-015) — review em dois eixos independentes, com fusão permitida no perfil enxuto.
  - DADO uma delta na fase review num harness com subagentes QUANDO o review roda ENTÃO os dois estágios executam como eixos independentes em subagentes paralelos — eixo Spec (conformidade: cada Rn/RNFn confrontado com o diff) e eixo Qualidade (ponytail-review/delete-list) — cada um cego ao contexto do outro, e os achados convergentes dos dois eixos são tratados antes do PR
  - DADO perfil `enxuto` aprovado (R36) QUANDO o review roda ENTÃO os dois eixos podem executar fundidos num único subagente, com os achados ainda classificados por eixo e a mesma regra de convergência
  - DADO um harness sem subagentes ou motor ausente QUANDO o review roda ENTÃO os estágios rodam inline em sequência com os fallbacks e avisos vigentes dos adapters (RNF2 preservado)
- R36 (delta-015) — perfil de execução por delta (seleção adaptativa de estágios).
  - DADO uma delta nova QUANDO o specify abre o `spec.md` ENTÃO a IA propõe no cabeçalho o campo `Perfil: completo|enxuto` com justificativa de 1 linha calibrada por escopo e risco, e o perfil só vale após aprovação explícita do usuário, registrada no próprio cabeçalho (`aprovado: AAAA-MM-DD`)
  - DADO perfil `enxuto` aprovado QUANDO o ciclo roda ENTÃO o clarify vira sob demanda (roda só se a spec tiver ambiguidade apontada), o `test-plan.md` é dispensável com justificativa de 1 linha no cabeçalho (`Test-plan: dispensado — <motivo>`) e o review executa os dois eixos fundidos num único subagente, com achados ainda classificados por eixo; plan, tasks, analyze e archive seguem integrais
  - DADO um `spec.md` sem o campo `Perfil` (deltas anteriores à delta-015) QUANDO o ciclo ou o gate roda ENTÃO vale `completo` — retrocompatível, sem migração
  - DADO o ciclo aplicável do tipo do projeto (R10) QUANDO o perfil é aplicado ENTÃO ele opera **dentro** do ciclo do tipo — perfil não reintroduz fase que o tipo já exclui
- R37 (delta-015) — prototipação opcional (estágio CONDITIONAL pós-descoberta).
  - DADO uma delta cujo escopo toca interface ou fluxo que o stakeholder precisa ver QUANDO o specify roda ENTÃO a IA propõe o estágio de prototipação com justificativa, e ele só executa com aprovação do usuário — nunca por iniciativa própria (mesma regra do gate visual, ADR-0009)
  - DADO o estágio aprovado QUANDO o protótipo é produzido ENTÃO a forma segue a categoria `prototipo` do `doc-profile.yaml` (dono da decisão); perfil ausente ou sem a categoria → default HTML estático navegável em `docs/prototypes/NNN-nome/`, versionado e referenciado na seção Contexto da delta
  - DADO uma delta sem gatilho de prototipação QUANDO o ciclo roda ENTÃO o estágio se omite com no máximo 1 linha de aviso
- R38 (delta-015) — plano de testes como artefato do ciclo.
  - DADO o `tasks.md` pronto QUANDO a fase tasks fecha ENTÃO existe `specs/NNN-nome/test-plan.md` (template da skill) derivado dos cenários DADO/QUANDO/ENTÃO da spec e das verificações das tasks — sem re-entrevistar nem inventar cenário novo
  - DADO um caso de teste QUANDO registrado no plano ENTÃO carrega o requisito coberto (`cobre: Rn|RNFn`), o tipo `auto|manual`, e o comando (auto) ou os passos roteirizados (manual) — teste manual roteirizado conta como cobertura
  - DADO perfil `enxuto` com dispensa justificada no cabeçalho QUANDO o ciclo roda ENTÃO o `test-plan.md` se omite e o C8 reporta BAIXO informativo em vez de ALTO
- R39 (delta-015) — `bugfix` como tipo de spec distinto.
  - DADO um pedido de correção de defeito QUANDO a delta abre ENTÃO ela pode nascer com `Tipo: bugfix` no cabeçalho e template próprio (sintoma, reprodução DADO/QUANDO/ENTÃO, causa-raiz, teste de regressão), mantendo a numeração NNN global
  - DADO uma delta `bugfix` QUANDO o ciclo roda ENTÃO o pipeline é specify → plan curto → implement (teste de regressão obrigatório) → review, com clarify, tasks e test-plan sob demanda e analyze mantido (read-only)
  - DADO uma delta `bugfix` sem mudança de requisito QUANDO o archive roda ENTÃO o diretório move para `_archive/` sem consolidar no TRUTH.md, e o gate não exige bloco Rn — a seção Mudanças declara "nenhuma (correção sem mudança de requisito)"
  - DADO um bugfix que altera requisito vigente QUANDO a delta consolida ENTÃO o bloco MUDA cita o alvo no TRUTH.md como qualquer delta (R6)
- R40 (delta-016) — arestas de bloqueio explícitas no tasks.md.
  - DADO a fase tasks QUANDO o `tasks.md` fecha ENTÃO toda dependência entre tasks está declarada na forma canônica `(dep: Tn[, Tm])` do template — task sem `dep:` é livre — e o conjunto forma um grafo dirigido acíclico
  - DADO o grafo QUANDO duas tasks não têm caminho entre si ENTÃO são paralelizáveis, e as unidades de execução paralela são deriváveis mecanicamente do grafo, sem anotação manual extra
  - DADO um `tasks.md` anterior à delta-016 (sem nenhum `dep:`) QUANDO o ciclo ou o gate o lê ENTÃO vale a ordem do arquivo como cadeia linear implícita — retrocompatível, sem migração
- R41 (delta-016) — execução paralela por worktree das unidades independentes.
  - DADO unidades paralelizáveis (R40) num harness com subagentes QUANDO o implement roda ENTÃO cada unidade pode executar num subagente com worktree isolada (motor: `superpowers:using-git-worktrees`, contrato em `adapters.md`), com convergência das worktrees antes do review
  - DADO um harness sem subagentes ou sem worktree QUANDO o implement roda ENTÃO a execução é sequencial na ordem topológica do grafo, com aviso de degradação (RNF2)
- R42 (delta-016) — vocabulário de harness canônico.
  - DADO os conceitos de harness que o framework pratica (initializer, agente incremental, gate determinístico, degradação graciosa, human-in-the-loop, trilha de auditoria, unidade paralelizável) QUANDO citados em skills e docs ENTÃO o termo e a definição vivem num reference canônico único da `spec-feature` e os demais arquivos referenciam sem duplicar (regra de ouro)
- R43 (delta-016) — trilha de auditoria de aprovação por fase.
  - DADO uma aprovação humana que o ciclo exige e ainda não tem registro mandatório (prototipação R37, ressalvas aceitas no analyze, aceite do review) QUANDO concedida ENTÃO fica registrada de forma citável no artefato da própria fase, seguindo o padrão de formato do R36 (`aprovado: AAAA-MM-DD`), sem arquivo de auditoria separado e sem inchar tokens — a aprovação de perfil continua regida pelo R36, dono vigente
  - DADO uma delta arquivada QUANDO auditada ENTÃO as aprovações são verificáveis nos artefatos em `_archive/` — a trilha sobrevive ao ciclo
- R44 (delta-016) — graphify como 4º motor externo opcional.
  - DADO um projeto-alvo com graphify instalado e habilitado no `doc-profile.yaml` QUANDO descoberta, specify/plan ou review rodam ENTÃO consultas `graphify query`/`path`/`explain` entram como insumo fundamentado com aresta citável `arquivo:linha`, e as tags `EXTRACTED`/`INFERRED`/`AMBIGUOUS` mapeiam no modelo `confirmado`/`inferido`/`lacuna` da descoberta (R25 — `AMBIGUOUS` → `lacuna`: requer validação humana)
  - DADO o contrato do adapter QUANDO a delta consolida ENTÃO a tabela de `adapters.md` tem a linha do graphify com instalação manual consciente (nunca deixar o `graphify install` escrever hook `PreToolUse`/CLAUDE.md — conflita com o harness), pin na política de versões com verificação datada (R34) e preferência pelo modo `--code-only` (determinístico, zero LLM)
  - DADO graphify presente e habilitado QUANDO o eixo Spec do review roda ENTÃO pode consultar o impacto do diff (`graphify query`) como insumo do confronto Rn×diff — mesmo contrato e mesma degradação dos demais cenários
  - DADO graphify ausente ou desabilitado QUANDO as fases rodam ENTÃO o fluxo atual (grep/Explore) segue com no máximo 1 linha de aviso — degradação graciosa (RNF2)
- R17 (delta-003) — o PR da delta faz split condicional pelo limiar canônico de PR.
  - DADO uma delta com analyze LIBERADO cujo diff acumulado de `specs/NNN-nome/` contra a main excede o limiar de PR da regra canônica QUANDO o ciclo segue para o implement ENTÃO os artefatos são mergeados antes, num PR próprio de documentação, e a implementação segue em PR separado
  - DADO uma delta cujos artefatos ficam dentro do limiar QUANDO o ciclo abre o PR ENTÃO um único PR carrega artefatos e implementação
  - DADO o texto do ciclo que descreve o split QUANDO cita o limiar ENTÃO referencia a regra canônica dona sem materializar o valor

## Gates determinísticos

- R11 (delta-000) — o gate analyze roda sempre no ciclo completo e é read-only.
  - DADO uma delta com spec, plan e tasks QUANDO o analyze roda ENTÃO grava `specs/NNN-nome/analyze.md` com veredito, **inclusive quando não há achados** — o relatório é o registro de que o gate rodou
  - DADO um achado CRÍTICO QUANDO o veredito é emitido ENTÃO é BLOQUEADO e o implement não começa até correção
- R12 (delta-016) — a metade mecânica do analyze é um script, não diligência.
  - DADO uma delta QUANDO `check_cycle.py` roda ENTÃO ele verifica aceite (C1), cobertura spec↔tasks (C2), estado × localização (C3), archive sem perda (C4), tamanho do TRUTH (C5), pendência roteada (C6), medição do split de PR (C7), cobertura do plano de testes (C8), validade do grafo de tasks (C9) e convergência mínima no archive (C10), e sai 1 se houver ALTO ou CRÍTICO
  - DADO um requisito removido do `TRUTH.md` resultante sem MUDA/REMOVE que o declare QUANDO o gate roda ENTÃO acusa CRÍTICO e o veredito é BLOQUEADO — comparando o `TRUTH.md` contra o merge-base da branch com a main (fallback `HEAD`, com aviso, quando não há base), para que consolidação já commitada não crie janela cega; sufixo reescrito cujo ID permanece no arquivo não é perda
  - DADO uma delta cujo diff acumulado de `specs/NNN-nome/` contra o merge-base excede o limiar de PR da regra canônica QUANDO o C7 roda ENTÃO reporta BAIXO recomendando o split dos artefatos (regra em `cycle.md`), sem alterar o código de saída — a medição informa, o split é decisão do ciclo; sem git ou sem merge-base o C7 se omite, como o C4
  - DADO um `test-plan.md` presente QUANDO o C8 roda ENTÃO acusa ALTO para Rn/RNFn da spec sem caso que o cubra e para caso citando requisito inexistente (espelho do C2); `test-plan.md` ausente sem dispensa declarada → ALTO; ausente com dispensa (R38) ou delta `bugfix` sem tasks → BAIXO informativo
  - DADO um `tasks.md` com `dep:` citando task inexistente ou formando ciclo QUANDO o C9 roda ENTÃO acusa ALTO (grafo inválido); nenhum `dep:` no arquivo → válido (cadeia linear implícita, R40)
  - DADO uma delta arquivada (`Estado: arquivada` em `_archive/`) com task `- [ ]` remanescente no `tasks.md` QUANDO o C10 roda ENTÃO acusa ALTO — o archive não fecha com trabalho declarado e não concluído; a auditoria semântica codebase×spec permanece juízo humano do review (renúncia por design, ADR-0014)
  - DADO a saída do script QUANDO impressa ENTÃO se declara parcial — nomeia os checks mecânicos cobertos e avisa que os checks 3 e 5 do `analyze.md` (scope creep, regra canônica) são humanos e não rodaram
  - DADO um `TRUTH.md` com sufixos na notação legada `(ΔNNN)` ou na nova `(delta-NNN)` QUANDO o gate lê os alvos ENTÃO reconhece as duas formas, sem exigir migração dos projetos existentes
- R32 (delta-013) — gate pré-commit real por hooks versionados.
  - DADO este repositório com `core.hooksPath` configurado para `.githooks/` QUANDO um commit toca arquivo `.md` ou o `deps.toml` ENTÃO o hook `pre-commit` roda `validate_integrity.py .` e bloqueia o commit quando o validador sai com código ≠ 0
  - DADO um projeto de usuário com `deps.toml` QUANDO a `guarding-doc-integrity` faz o bootstrap ENTÃO ela oferece a instalação do hook (template versionado + `git config core.hooksPath`), sem sobrescrever hook existente (RNF3) e sem quebrar quando o usuário recusa
  - DADO os cinco arquivos promissores do DT-005 (`deps.toml`, SKILL da `guarding-doc-integrity`, `canonical-rules.md`, `README.md`, TRUTH.md) QUANDO a delta consolida ENTÃO a promessa descrita bate com o mecanismo real (hook versionado opt-in + CI), sem prometer validação que não existe
- R13 (delta-005) — valor de negócio duplicado entre arquivos é governado por manifesto e validado por script.
  - DADO um repo com `deps.toml` QUANDO `validate_integrity.py` roda ENTÃO verifica espelhos em sincronia (C1), materialização fora dos sancionados (C2) e links relativos vivos (C3), saindo 1 em qualquer violação
  - DADO uma delta ainda aberta propondo valor novo QUANDO o validador roda ENTÃO ela não é acusada — as deltas abertas (`specs/NNN-*/`) ficam fora dos `scan_globs`; dentro de `specs/`, só o `TRUTH.md` consolidado (e `truth/`) entra na varredura
  - DADO o `templates/deps.toml` da skill QUANDO um `exclude_globs` mira conteúdo de diretório ENTÃO o glob termina em `**/*.md` (nunca em `**` solto), com comentário no template explicando o porquê — `pathlib` ≤ 3.12 casa só diretórios num `**` final e o exclude viraria no-op

## Revisão

- R14 (delta-001) — a revisão adversarial da spec é um toggle opcional, distinto do analyze.
  - DADO uma spec que toca segurança, dados persistentes, contrato externo ou dependência nova QUANDO a skill `spec-review` roda ENTÃO produz achados + edições propostas em blocos antes/depois, sem aplicar nenhuma sem aprovação do usuário

## Distribuição

- R15 (delta-019) — o framework é distribuído e instalado como plugin do Claude Code.
  - DADO um usuário sem o framework QUANDO ele roda `/plugin marketplace add iuripereira/deltaspec` seguido de `/plugin install deltaspec@deltaspec` ENTÃO as skills do plugin ficam disponíveis sob o namespace `deltaspec:`, sem cópia manual de arquivos e sem que o repositório precise viver dentro de `~/.claude/skills/`
  - DADO o repositório do framework QUANDO o Claude Code registra o marketplace ENTÃO encontra `.claude-plugin/marketplace.json` **e** `.claude-plugin/plugin.json` na raiz, com as skills em `skills/<nome>/SKILL.md`
- R31 (delta-013) — inventário de skills validado mecanicamente no CI.
  - DADO os manifestos `.claude-plugin/plugin.json` e `.claude-plugin/marketplace.json` QUANDO o job `ci` roda ENTÃO um step compara cada diretório `skills/<nome>/` com as descrições dos dois manifestos (case-insensitive, conforme lição de 2026-07-20) e falha nomeando a skill ausente e o manifesto omisso
  - DADO os dois manifestos citando as 10 skills atuais QUANDO o check roda ENTÃO passa sem achado
- R33 (delta-019) — perfil de escrita `eu-tenho-tdah` reconhecido como skill do plugin.
  - DADO o plugin instalado QUANDO as skills são listadas ENTÃO `eu-tenho-tdah` está disponível sob o namespace `deltaspec:` como perfil de escrita always-on, fora do ciclo de features, e o README e os manifestos a documentam como tal
- R47 (delta-019) — o rename preserva o registro histórico e publica caminho de migração.
  - DADO o rename `sdd-iuri` → `deltaspec` QUANDO ele é aplicado ENTÃO os registros imutáveis preservam o nome histórico — `specs/_archive/**`, ADRs já `Accepted` e seções lançadas do `CHANGELOG.md` não são reescritos (mesma guarda do DT-010, delta-010)
  - DADO um consumidor já instalado (plugin ou projeto bootstrapado) QUANDO ele abre o `README.md` ENTÃO encontra a seção de migração com os passos exatos: remover o marketplace antigo, adicionar `iuripereira/deltaspec`, instalar `deltaspec@deltaspec`, trocar os comandos `/sdd-iuri:*` do `CLAUDE.md` do projeto e reconfigurar `git config deltaspec.validator` quando o hook pré-commit estiver instalado
  - DADO o template `pre-commit` da `guarding-doc-integrity` QUANDO ele é instalado num projeto ENTÃO a chave de config lida é `deltaspec.validator`; hooks já copiados em projetos antigos seguem funcionando com a chave antiga até serem reinstalados (a cópia instalada não é tocada pelo rename)

## Handoff de sessão

- R20 (delta-019) — a skill handoff compacta a sessão nos registros com dono.
  - DADO uma sessão de trabalho neste repositório ou num projeto do framework QUANDO o usuário invoca `/deltaspec:handoff [foco da próxima sessão]` ENTÃO o `HANDOFF.md` (diário de bordo) é atualizado nas quatro seções — Agora, Feito recentemente, Problemas atuais, Próximos passos imediatos — com o foco informado refletido nos próximos passos
  - DADO o handoff fechado QUANDO ele imprime o prompt de retomada ENTÃO é uma linha única apontando o `HANDOFF.md` com o foco (variante multi-repo: os `HANDOFF.md` dos repos, âncora primeiro)
  - DADO um projeto com `STATE.md` legado e sem `HANDOFF.md` QUANDO o handoff roda ENTÃO ele renomeia `STATE.md` → `HANDOFF.md` (`git mv`) antes de escrever, sem deixar os dois arquivos coexistirem
  - DADO débito, pendência ou lição descoberto na sessão e ainda sem registro QUANDO o handoff roda ENTÃO ele entra no `DEBT.md` (linha `DT-NNN` ou seção Lições) antes de o diário ser fechado
  - DADO uma delta em curso em `specs/NNN-*/` QUANDO o handoff roda ENTÃO o diário cita a delta, a fase em que parou e o veredito do último gate
  - DADO conteúdo já registrado em spec/plan/ADR/DEBT/CHANGELOG/commit QUANDO o handoff escreve ENTÃO referencia por caminho/ID em vez de duplicar, e segredo/PII não entra no diário

## Entregáveis para cliente

- R21 (delta-011) — a `doc-entregavel` despacha por tipo de documento.
  - DADO um pedido de entregável QUANDO a skill roda ENTÃO ela identifica o `tipo` entre `prd-cliente` (fluxo vigente), `juridico-nda`, `juridico-contrato-ti` e `requisitos-cliente`, perguntando com opções fechadas apenas quando o pedido for ambíguo
  - DADO um `tipo` `juridico-*` ou `requisitos-cliente` QUANDO a skill monta o conteúdo ENTÃO as regras de conteúdo, estrutura e base legal vêm de `skills/doc-entregavel/references/juridico.md` e o export continua sendo o pipeline vigente da SKILL.md (render de diagramas, capa, Sumário, PDF/DOCX)
  - DADO a SKILL.md QUANDO ela cita uma regra jurídica ENTÃO referencia o reference sem reproduzir o texto da regra (fonte canônica única)
- R22 (delta-011) — documento jurídico sai como minuta, com eficácia executiva verificável.
  - DADO um documento de tipo `juridico-*` QUANDO ele é gerado ENTÃO o topo do arquivo traz a nota de minuta ("sujeita a revisão por advogado(a)", gerada por IA, não é aconselhamento jurídico) e o fecho traz bloco de assinaturas com as partes e duas testemunhas identificadas por nome e CPF
  - DADO uma base legal não listada no reference QUANDO o texto precisaria citá-la ENTÃO a skill grava `[VERIFICAR COM ADVOGADO]` no lugar, sem inventar dispositivo, número de lei ou julgado
  - DADO um documento `juridico-*` concluído QUANDO a skill encerra ENTÃO imprime o checklist de eficácia do reference (testemunhas, assinatura eletrônica com integridade conferida por provedor, rubrica, duas vias, revisão por advogado, registro em RTD no dia da assinatura quando optado)
  - DADO um pedido para "seguir ABNT" em instrumento contratual QUANDO a skill formata ENTÃO corrige a premissa (NBR 14724 é norma acadêmica) e aplica a convenção de mercado do reference
- R23 (delta-011) — `requisitos-cliente` cobre projeto e produto, em duas versões, com orçamento, prazo e cronograma.
  - DADO um pedido de `requisitos-cliente` QUANDO a skill monta o documento ENTÃO ele declara explicitamente o recorte coberto — requisitos de projeto e/ou de produto/serviço — e traz seção de Visão do produto e/ou Visão do projeto conforme o recorte declarado
  - DADO um documento `requisitos-cliente` QUANDO ele é gerado ENTÃO as seções de previsão de orçamento (por fase, com premissas da estimativa e faixa), prazo total estimado e cronograma (fases, marcos, dependências e marcos de pagamento vinculados) estão presentes e preenchidas ou marcadas com placeholder em destaque
  - DADO o estado da negociação QUANDO a skill escolhe a versão ENTÃO gera a Versão A (proposta executiva, pré-NDA: visão, problema, macro-funcionalidades, faixa de investimento e prazo macro, sem arquitetura detalhada, modelagem de dados ou backlog decomposto) ou a Versão B (especificação completa, pós-NDA assinado, com rodapé `CONFIDENCIAL` e nota de titularidade), nunca as duas no mesmo arquivo
  - DADO um documento `requisitos-cliente` QUANDO ele lista requisitos ENTÃO usa os IDs rastreáveis do framework (`OBJ-*`, `ESC-*`, `RF-*`, `RNF-*`, `RC-*`, `PRE-*`, `RSK-*`), compatíveis com o `tabela_cliente.py` da própria skill
- R45 (delta-020) — diagram-design como camada de apresentação a cliente, com Mermaid fonte.
  - DADO um projeto cujo `doc-profile.yaml` declara a categoria `apresentacao` QUANDO um diagrama Mermaid versionado precisa de acabamento para cliente, gestão ou stakeholder ENTÃO ele é materializado com a skill `diagram-design` (HTML+SVG autocontido, brandado) tendo o `.mmd` fonte como dono do conteúdo, saída em `docs/apresentacao/`, e o `.mmd` em git permanece a única fonte da verdade
  - DADO um diagrama já materializado QUANDO o `.mmd` fonte muda ENTÃO a materialização é refeita a partir do fonte; edição feita na materialização (HTML ou projeto claude.ai/design) nunca retorna ao git como fonte — em divergência, o `.mmd` governa
  - DADO identidade visual disponível (onboarding do diagram-design a partir do site do cliente/projeto, ou tokens declarados no doc-profile) QUANDO a materialização roda ENTÃO os tokens de marca são aplicados; identidade ausente → paleta default da skill, sem bloquear
  - DADO materializações prontas QUANDO o usuário pede publicação para stakeholders ENTÃO a ferramenta `design-sync` publica os HTML num projeto claude.ai/design (fluxo incremental list → plan → write, nunca replace integral) — publicação é opcional e por pedido explícito, nunca automática
  - DADO o template `doc-profile.yaml` QUANDO a delta consolida ENTÃO a categoria `apresentacao` aponta ferramenta `diagram-design` (+ `design-sync` como publicação opcional) no lugar de `figma-figjam`, mantendo `obrigatorio: false` por default
- R46 (delta-020) — entregável congelado fora da camada de apresentação, com contrato de motor e degradação graciosa.
  - DADO um entregável congelado (PDF/DOCX da `doc-entregavel`) QUANDO ele é gerado ENTÃO o pipeline CLI vigente (mmdc/dbml-renderer → export) permanece o caminho único — a camada de apresentação nunca entra no caminho crítico do documento assinável — e a SKILL.md da `doc-entregavel` documenta o papel da camada (apresentação, nunca no export)
  - DADO a tabela de contrato de `adapters.md` QUANDO a delta consolida ENTÃO a linha do Figma MCP é substituída pelas linhas do `diagram-design` (plugin de terceiro, local) e do `design-sync` (ferramenta do harness, serviço claude.ai), cada uma com ponto sensível a breaking e fallback declarado, e a política de versões tem as entradas com verificação datada (R34) — diagram-design sem pin até a primeira adoção real, mesmo padrão do graphify
  - DADO o plugin `diagram-design` ausente, ou o `design-sync` sem autorização claude.ai, ou a categoria `apresentacao` não declarada QUANDO o ciclo ou a doc-entregavel rodam ENTÃO o fluxo atual (render CLI do Mermaid) segue com no máximo 1 linha de aviso — degradação graciosa (RNF2)
  - DADO um cliente que exige o acabamento da camada dentro do documento congelado QUANDO o export é montado ENTÃO o caminho é exportar o HTML materializado para PNG/SVG (`diagram-design:export`, Playwright) e embutir a imagem no pipeline CLI — sem etapa manual não reprodutível

## Acompanhamento de status (PMO)

- R48 (delta-022) — a skill `status-pmo` conduz a montagem do site de status PMO.
  - DADO um repo do ciclo que precisa de acompanhamento de status QUANDO `/deltaspec:status-pmo` é invocada ENTÃO a SKILL.md conduz o processo em 7 gates (cronograma canônico → épicos e tarefas → ata semanal → gerador no repo cliente → marca por tokens → publicação restrita → integração externa via contrato de dados), com invariantes explícitos (fonte da verdade no repo, saída não versionada, só metadado de gestão, self-contained, coleta separada do render), **somente projetos com entrega rastreada** (repo de apoio fica fora) e tabela de erros comuns
- R50 (delta-022) — a skill cobre épicos, tarefas e dependências, com página por épico.
  - DADO a skill `status-pmo` QUANDO o processo é seguido ENTÃO existe o gate "Épicos e tarefas com dependências" (`docs/epicos/<dir>.md`: um épico por etapa do cronograma, mesma ordem e quantidade, com `**Dep:**` e tabela `| ID | Tarefa | Dep | Status |`), o gerador produz `etapa-<dir>-eN.html` por épico (tarefas, depende-de/bloqueia, registros, chave do sistema externo) com a etapa do cronograma clicável, e a seção "Diagramas de dependência" descreve o grafo em SVG inline (camadas por profundidade, tokens CSS, nó clicável, ciclo degrada sem quebrar)
  - DADO um projeto sem `docs/epicos/<dir>.md` QUANDO o site é gerado ENTÃO a seção mostra "em elaboração" e a geração completa
- R49 (delta-022) — os templates da status-pmo existem e são utilizáveis.
  - DADO o diretório `skills/status-pmo/references/templates/` QUANDO a skill é seguida ENTÃO existem: `styles-tokens.css` (design system com paleta placeholder e instrução de troca por marca), `theme.js` (toggle de tema persistido), `cronograma-template.md` (D0 + seções por projeto + `## Marcos` parseáveis), `ata-template.md` (5 seções fixas), `epicos-template.md` (épico = etapa, tarefas com dependência) e `dados-schema.md` (contrato do `dados.json`, incluindo `jira` e `epicos[]`, com regra de evolução aditiva); os assets de marca nascem com **tema claro por padrão** (sem `prefers-color-scheme`, escuro só por `data-theme`)

## Não funcionais

- RNF1 (delta-013) — economia de tokens é requisito, não consequência.
  - Métrica: `TRUTH.md` ≤ 800 linhas (acima disso, particiona); o analyze lê só o cabeçalho-resumo do plan (≤15 linhas), nunca o plano inteiro
  - Verificação: `check_cycle.py` C5; contrato de insumos em `analyze.md`
  - Exceção (ADR-0009): documentação **cliente** é entregável jurídico — completude e fidelidade dominam e a economia de tokens não se aplica; documentação **interna** segue o RNF integralmente
- RNF2 (delta-005) — o ciclo degrada com aviso em vez de abortar.
  - Métrica: toda fase com motor de terceiro tem fallback nativo declarado
  - Verificação: tabela de contrato em `adapters.md` — uma linha por fase, com o ponto sensível a breaking change **e uma seção de fallback correspondente para cada motor da linha**
- RNF3 (delta-019) — idempotência defensiva: nada é sobrescrito nem migrado sem pedido.
  - Métrica: 2ª execução de `/deltaspec:projeto-init` e `/deltaspec:projeto-infra` não altera nenhum arquivo versionado e relata o que pulou; artefato de comparação efêmero (`CLAUDE.generated.md` + diff, conforme R2) é permitido
  - Verificação: rodar duas vezes em repo já inicializado e conferir o relatório
- RNF4 (delta-002) — todo script de gate carrega o próprio teste, validado no CI.
  - Métrica: 100% dos scripts do framework expõem `--selftest` com fixtures; o C4 é coberto com repositório git real — caso positivo (perda acusada) e falso positivo (alvo declarado em MUDA não acusado)
  - Verificação: job `ci` executa `check_cycle.py --selftest` e `validate_integrity.py --selftest`
- RNF5 (delta-002) — portabilidade: nenhum artefato do framework depende de caminho de máquina.
  - Métrica: zero ocorrências de caminho de instalação legado em `skills/**` e `.github/**` — cobrindo as variantes `~/.claude/skills`, `$HOME/.claude/skills` e `/home/<user>/.claude/skills`; toda invocação de script do framework resolve por `${CLAUDE_PLUGIN_ROOT}`
  - Verificação: step no job `ci` rodando `! grep -rnE '(~|\$HOME|/home/[^/ ]+)/[.]claude/skills' skills/ .github/`

## Não implementado
<!-- visão conhecida que ainda não vige; não é delta e não tem número -->

- **CI dos gates dentro dos projetos do usuário.** Hoje os gates rodam local (analyze, archive, pré-commit); o porquê e as alternativas renunciadas estão em [ADR-0001](../docs/adrs/ADR-0001-gates-rodam-local.md).
- **Backfill assistido de TRUTH.md em brownfield.** Existe como tarefa sob demanda, não como fase.
- **Por design, fora de escopo:** os checks 3 e 5 do analyze (scope creep spec×plan, violação de regra canônica) e o mérito da spec no `/deltaspec:spec-review` continuam com o modelo — são juízo, não regex, e automatizá-los produziria falso negativo confiante.
