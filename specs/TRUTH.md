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

## Handoff de sessão

- R20 (delta-010) — a skill handoff compacta a sessão nos registros com dono.
  - DADO uma sessão de trabalho neste repositório ou num projeto do framework QUANDO o usuário invoca `/sdd-iuri:handoff [foco da próxima sessão]` ENTÃO o `HANDOFF.md` (diário de bordo) é atualizado nas quatro seções — Agora, Feito recentemente, Problemas atuais, Próximos passos imediatos — com o foco informado refletido nos próximos passos
  - DADO o handoff fechado QUANDO ele imprime o prompt de retomada ENTÃO é uma linha única apontando o `HANDOFF.md` com o foco (variante multi-repo: os `HANDOFF.md` dos repos, âncora primeiro)
  - DADO um projeto com `STATE.md` legado e sem `HANDOFF.md` QUANDO o handoff roda ENTÃO ele renomeia `STATE.md` → `HANDOFF.md` (`git mv`) antes de escrever, sem deixar os dois arquivos coexistirem
  - DADO débito, pendência ou lição descoberto na sessão e ainda sem registro QUANDO o handoff roda ENTÃO ele entra no `DEBT.md` (linha `DT-NNN` ou seção Lições) antes de o diário ser fechado
  - DADO uma delta em curso em `specs/NNN-*/` QUANDO o handoff roda ENTÃO o diário cita a delta, a fase em que parou e o veredito do último gate
  - DADO conteúdo já registrado em spec/plan/ADR/DEBT/CHANGELOG/commit QUANDO o handoff escreve ENTÃO referencia por caminho/ID em vez de duplicar, e segredo/PII não entra no diário

## Não funcionais

- RNF1 (delta-000) — economia de tokens é requisito, não consequência.
  - Métrica: `TRUTH.md` ≤ 800 linhas (acima disso, particiona); o analyze lê só o cabeçalho-resumo do plan (≤15 linhas), nunca o plano inteiro
  - Verificação: `check_cycle.py` C5; contrato de insumos em `analyze.md`
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
