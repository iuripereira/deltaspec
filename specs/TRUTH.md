# sdd-iuri — Fonte da verdade
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
- R18 (delta-007) — DEBT.md é o registro canônico de débito, pendências e lições, com IDs estáveis.
  - DADO um débito, pendência ou guarda novo QUANDO registrado ENTÃO entra no `DEBT.md` da raiz como linha `DT-NNN` (próximo número livre — numeração global, nunca reutilizada) com natureza, descrição, origem, data de abertura, gatilho de correção e status
  - DADO um item quitado QUANDO a correção mergeia ENTÃO o status do item muda para quitado, com data — a linha nunca é apagada (a trajetória aberto→quitado é o registro da evolução)
  - DADO um tipo de projeto que recebe `docs/adrs/` na matriz de detection.md QUANDO o scaffold do projeto-init roda ENTÃO cria também `DEBT.md` a partir do template da skill, e só se não existir
- R19 (delta-010) — HANDOFF.md é diário de bordo, não acumulador de estado.
  - DADO o template HANDOFF.md do projeto-init QUANDO o scaffold cria o arquivo ENTÃO o formato tem as seções "Agora", "Feito recentemente", "Problemas atuais" e "Próximos passos imediatos", com janela rolante declarada e a regra de merge "união das verdades" mantida
  - DADO conteúdo que tem dono próprio (as-built → TRUTH.md/README, débito/pendência/lição → DEBT.md, decisão com renúncia → ADR, histórico → CHANGELOG) QUANDO ele surgir no HANDOFF.md ENTÃO é movido para o dono no mesmo bloco de trabalho e o HANDOFF.md apenas referencia
  - DADO as referências ativas do framework (CLAUDE.md, canonical-rules.md, detection.md, deps.toml, README, template) QUANDO nomeiam o diário de bordo ENTÃO usam `HANDOFF.md`, não `STATE.md`, e não há dois donos de "onde paramos" — arquivos imutáveis (`specs/_archive/**`, ADRs Accepted, CHANGELOG lançado) preservam o nome histórico (guarda DT-010)

## Infraestrutura

- R4 (delta-001) — a skill `projeto-infra` configura a infraestrutura e é idempotente.
  - DADO um repositório já configurado QUANDO a skill `projeto-infra` roda de novo ENTÃO ela consulta o que existe, preenche só as lacunas e relata no-op no restante
  - DADO falha de infra (sem rede, `gh` não autenticado) QUANDO o init a invoca ENTÃO o init reporta e segue, sem travar

## Descoberta (pré-specify)

- R24 (delta-012) — a skill `descoberta` cobre a fase pré-specify, produzindo dossiê a partir de insumos brutos.
  - DADO um projeto com insumos brutos de descoberta (transcrição/resumo de reunião, planilha, vídeo, docs legados) QUANDO `/sdd-iuri:descoberta` roda ENTÃO ela inventaria os insumos (o que existe, o que falta, pessoas-fonte, sistemas citados) e grava o dossiê em `docs/discovery/AAAA-MM-DD-<evento>.md` com o processo as-is, entidades, regras e dores minerados
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

- R5 (delta-001) — uma feature é uma delta spec, com numeração global ao repositório.
  - DADO um incremento novo QUANDO a skill `spec-feature` abre a delta ENTÃO cria `specs/NNN-nome/` com `NNN` = max(`specs/`, `specs/_archive/`) + 1 e a branch `tipo/NNN-nome`
  - DADO uma versão maior do projeto QUANDO uma delta nova é aberta ENTÃO a numeração continua do maior existente e nunca reinicia
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
- R35 (delta-014) — review em dois eixos independentes, paralelos quando houver subagentes.
  - DADO uma delta na fase review num harness com subagentes QUANDO o review roda ENTÃO os dois estágios executam como eixos independentes em subagentes paralelos — eixo Spec (conformidade: cada Rn/RNFn confrontado com o diff) e eixo Qualidade (ponytail-review/delete-list) — cada um cego ao contexto do outro, e os achados convergentes dos dois eixos são tratados antes do PR
  - DADO um harness sem subagentes ou motor ausente QUANDO o review roda ENTÃO os estágios rodam inline em sequência com os fallbacks e avisos vigentes dos adapters (RNF2 preservado)
- R17 (delta-003) — o PR da delta faz split condicional pelo limiar canônico de PR.
  - DADO uma delta com analyze LIBERADO cujo diff acumulado de `specs/NNN-nome/` contra a main excede o limiar de PR da regra canônica QUANDO o ciclo segue para o implement ENTÃO os artefatos são mergeados antes, num PR próprio de documentação, e a implementação segue em PR separado
  - DADO uma delta cujos artefatos ficam dentro do limiar QUANDO o ciclo abre o PR ENTÃO um único PR carrega artefatos e implementação
  - DADO o texto do ciclo que descreve o split QUANDO cita o limiar ENTÃO referencia a regra canônica dona sem materializar o valor

## Gates determinísticos

- R11 (delta-000) — o gate analyze roda sempre no ciclo completo e é read-only.
  - DADO uma delta com spec, plan e tasks QUANDO o analyze roda ENTÃO grava `specs/NNN-nome/analyze.md` com veredito, **inclusive quando não há achados** — o relatório é o registro de que o gate rodou
  - DADO um achado CRÍTICO QUANDO o veredito é emitido ENTÃO é BLOQUEADO e o implement não começa até correção
- R12 (delta-009) — a metade mecânica do analyze é um script, não diligência.
  - DADO uma delta QUANDO `check_cycle.py` roda ENTÃO ele verifica aceite (C1), cobertura spec↔tasks (C2), estado × localização (C3), archive sem perda (C4), tamanho do TRUTH (C5), pendência roteada (C6) e medição do split de PR (C7), e sai 1 se houver ALTO ou CRÍTICO
  - DADO um requisito removido do `TRUTH.md` resultante sem MUDA/REMOVE que o declare QUANDO o gate roda ENTÃO acusa CRÍTICO e o veredito é BLOQUEADO — comparando o `TRUTH.md` contra o merge-base da branch com a main (fallback `HEAD`, com aviso, quando não há base), para que consolidação já commitada não crie janela cega; sufixo reescrito cujo ID permanece no arquivo não é perda
  - DADO uma delta cujo diff acumulado de `specs/NNN-nome/` contra o merge-base excede o limiar de PR da regra canônica QUANDO o C7 roda ENTÃO reporta BAIXO recomendando o split dos artefatos (regra em `cycle.md`), sem alterar o código de saída — a medição informa, o split é decisão do ciclo; sem git ou sem merge-base o C7 se omite, como o C4
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

- R15 (delta-008) — o framework é distribuído e instalado como plugin do Claude Code.
  - DADO um usuário sem o framework QUANDO ele roda `/plugin marketplace add iuripereira/sdd-iuri` seguido de `/plugin install sdd-iuri@sdd-iuri` ENTÃO as skills do plugin ficam disponíveis sob o namespace `sdd-iuri:`, sem cópia manual de arquivos e sem que o repositório precise viver dentro de `~/.claude/skills/`
  - DADO o repositório do framework QUANDO o Claude Code registra o marketplace ENTÃO encontra `.claude-plugin/marketplace.json` **e** `.claude-plugin/plugin.json` na raiz, com as skills em `skills/<nome>/SKILL.md`
- R31 (delta-013) — inventário de skills validado mecanicamente no CI.
  - DADO os manifestos `.claude-plugin/plugin.json` e `.claude-plugin/marketplace.json` QUANDO o job `ci` roda ENTÃO um step compara cada diretório `skills/<nome>/` com as descrições dos dois manifestos (case-insensitive, conforme lição de 2026-07-20) e falha nomeando a skill ausente e o manifesto omisso
  - DADO os dois manifestos citando as 9 skills atuais QUANDO o check roda ENTÃO passa sem achado
- R33 (delta-013) — perfil de escrita `eu-tenho-tdah` reconhecido como skill do plugin.
  - DADO o plugin instalado QUANDO as skills são listadas ENTÃO `eu-tenho-tdah` está disponível sob o namespace `sdd-iuri:` como perfil de escrita always-on, fora do ciclo de features, e o README e os manifestos a documentam como tal

## Handoff de sessão

- R20 (delta-010) — a skill handoff compacta a sessão nos registros com dono.
  - DADO uma sessão de trabalho neste repositório ou num projeto do framework QUANDO o usuário invoca `/sdd-iuri:handoff [foco da próxima sessão]` ENTÃO o `HANDOFF.md` (diário de bordo) é atualizado nas quatro seções — Agora, Feito recentemente, Problemas atuais, Próximos passos imediatos — com o foco informado refletido nos próximos passos
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

## Não funcionais

- RNF1 (delta-013) — economia de tokens é requisito, não consequência.
  - Métrica: `TRUTH.md` ≤ 800 linhas (acima disso, particiona); o analyze lê só o cabeçalho-resumo do plan (≤15 linhas), nunca o plano inteiro
  - Verificação: `check_cycle.py` C5; contrato de insumos em `analyze.md`
  - Exceção (ADR-0009): documentação **cliente** é entregável jurídico — completude e fidelidade dominam e a economia de tokens não se aplica; documentação **interna** segue o RNF integralmente
- RNF2 (delta-005) — o ciclo degrada com aviso em vez de abortar.
  - Métrica: toda fase com motor de terceiro tem fallback nativo declarado
  - Verificação: tabela de contrato em `adapters.md` — uma linha por fase, com o ponto sensível a breaking change **e uma seção de fallback correspondente para cada motor da linha**
- RNF3 (delta-005) — idempotência defensiva: nada é sobrescrito nem migrado sem pedido.
  - Métrica: 2ª execução de `/sdd-iuri:projeto-init` e `/sdd-iuri:projeto-infra` não altera nenhum arquivo versionado e relata o que pulou; artefato de comparação efêmero (`CLAUDE.generated.md` + diff, conforme R2) é permitido
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
- **Por design, fora de escopo:** os checks 3 e 5 do analyze (scope creep spec×plan, violação de regra canônica) e o mérito da spec no `/sdd-iuri:spec-review` continuam com o modelo — são juízo, não regex, e automatizá-los produziria falso negativo confiante.
