# delta-019 — rename-deltaspec
Estado: proposta · Data: 2026-07-28 · Branch: feat/019-rename-deltaspec · Perfil: enxuto — rename mecânico de identidade (manifestos, namespace, docs), sem lógica nova de gate; risco concentrado em consumidores instalados, endereçado por guia de migração (aprovado: 2026-07-28) · Test-plan: dispensado — a verificação é mecânica (selftests dos gates + grep de resíduo + reinstalação do plugin), declarada nas tasks
<!-- Numeração: 018 é a última arquivada; 017 segue reservada para a Fase 4 (Jira) e esta delta salta o número (R5 do TRUTH), sem consumi-lo. -->

## Contexto (≤3 linhas)
O framework abre à comunidade e `sdd-iuri` carrega o nome pessoal do autor, o que desincentiva adoção e contribuição de terceiros. O nome novo é `deltaspec` — `delta-spec` foi descartado por colidir com `codebycorey/delta-spec`, projeto do mesmo nicho no GitHub. Rename quebra o namespace de invocação: é breaking change e corta a v1.0.0.

## Mudanças

### R1 — MUDA R15 (delta-008): o framework é distribuído e instalado como plugin `deltaspec`
- DADO um usuário sem o framework QUANDO ele roda `/plugin marketplace add iuripereira/deltaspec` seguido de `/plugin install deltaspec@deltaspec` ENTÃO as skills do plugin ficam disponíveis sob o namespace `deltaspec:`, sem cópia manual de arquivos e sem que o repositório precise viver dentro de `~/.claude/skills/`
- DADO o repositório do framework QUANDO o Claude Code registra o marketplace ENTÃO encontra `.claude-plugin/marketplace.json` **e** `.claude-plugin/plugin.json` na raiz, com as skills em `skills/<nome>/SKILL.md`

### R2 — MUDA R20 (delta-010): a skill handoff compacta a sessão nos registros com dono
- DADO uma sessão de trabalho neste repositório ou num projeto do framework QUANDO o usuário invoca `/deltaspec:handoff [foco da próxima sessão]` ENTÃO o `HANDOFF.md` (diário de bordo) é atualizado nas quatro seções — Agora, Feito recentemente, Problemas atuais, Próximos passos imediatos — com o foco informado refletido nos próximos passos
- DADO o handoff fechado QUANDO ele imprime o prompt de retomada ENTÃO é uma linha única apontando o `HANDOFF.md` com o foco (variante multi-repo: os `HANDOFF.md` dos repos, âncora primeiro)
- DADO um projeto com `STATE.md` legado e sem `HANDOFF.md` QUANDO o handoff roda ENTÃO ele renomeia `STATE.md` → `HANDOFF.md` (`git mv`) antes de escrever, sem deixar os dois arquivos coexistirem
- DADO débito, pendência ou lição descoberto na sessão e ainda sem registro QUANDO o handoff roda ENTÃO ele entra no `DEBT.md` (linha `DT-NNN` ou seção Lições) antes de o diário ser fechado
- DADO uma delta em curso em `specs/NNN-*/` QUANDO o handoff roda ENTÃO o diário cita a delta, a fase em que parou e o veredito do último gate
- DADO conteúdo já registrado em spec/plan/ADR/DEBT/CHANGELOG/commit QUANDO o handoff escreve ENTÃO referencia por caminho/ID em vez de duplicar, e segredo/PII não entra no diário

### R3 — MUDA R24 (delta-012): a skill `descoberta` cobre a fase pré-specify
- DADO um projeto com insumos brutos de descoberta (transcrição/resumo de reunião, planilha, vídeo, docs legados) QUANDO `/deltaspec:descoberta` roda ENTÃO ela inventaria os insumos (o que existe, o que falta, pessoas-fonte, sistemas citados) e grava o dossiê em `docs/discovery/AAAA-MM-DD-<evento>.md` com o processo as-is, entidades, regras e dores minerados
- DADO um vídeo entre os insumos QUANDO `ffmpeg` está disponível ENTÃO frames amostrados (scene detection + intervalo fixo) dos trechos relevantes são fonte válida de mineração; `ffmpeg` ausente → o vídeo entra no inventário como lacuna, com aviso, sem quebrar a skill

### R4 — MUDA R33 (delta-013): perfil de escrita `eu-tenho-tdah` reconhecido como skill do plugin
- DADO o plugin instalado QUANDO as skills são listadas ENTÃO `eu-tenho-tdah` está disponível sob o namespace `deltaspec:` como perfil de escrita always-on, fora do ciclo de features, e o README e os manifestos a documentam como tal

### R5 — ADICIONA: o rename preserva o registro histórico e publica caminho de migração
- DADO o rename `sdd-iuri` → `deltaspec` QUANDO ele é aplicado ENTÃO os registros imutáveis preservam o nome histórico — `specs/_archive/**`, ADRs já `Accepted` e seções lançadas do `CHANGELOG.md` não são reescritos (mesma guarda do DT-010, delta-010)
- DADO um consumidor já instalado (plugin ou projeto bootstrapado) QUANDO ele abre o `README.md` ENTÃO encontra a seção de migração com os passos exatos: remover o marketplace antigo, adicionar `iuripereira/deltaspec`, instalar `deltaspec@deltaspec`, trocar os comandos `/sdd-iuri:*` do `CLAUDE.md` do projeto e reconfigurar `git config deltaspec.validator` quando o hook pré-commit estiver instalado
- DADO o template `pre-commit` da `guarding-doc-integrity` QUANDO ele é instalado num projeto ENTÃO a chave de config lida é `deltaspec.validator`; hooks já copiados em projetos antigos seguem funcionando com a chave antiga até serem reinstalados (a cópia instalada não é tocada pelo rename)

## Requisitos não funcionais

### RNF1 — MUDA RNF3 (delta-005): idempotência defensiva — nada é sobrescrito nem migrado sem pedido
- Métrica: 2ª execução de `/deltaspec:projeto-init` e `/deltaspec:projeto-infra` não altera nenhum arquivo versionado e relata o que pulou; artefato de comparação efêmero (`CLAUDE.generated.md` + diff, conforme R2) é permitido
- Verificação: rodar duas vezes em repo já inicializado e conferir o relatório

## Fora de escopo
- Reescrever `specs/_archive/`, CHANGELOG lançado e ADRs `Accepted` — histórico congelado (R5)
- Traduzir a documentação para EN e abrir CONTRIBUTING/código de conduta — abertura à comunidade é trabalho seguinte, roteado ao DEBT.md
- Criar organização GitHub própria — o user `deltaspec` já está ocupado por terceiro; o repo segue sob `iuripereira/`
- Migrar o `imex-travelplanner` — repo separado, PR próprio (mesma decisão desta sessão, fora desta delta)
- Renomear a pasta local de trabalho e caches de máquina — estado local, não versionado

## Dependências e riscos
- Depende do rename do repositório no GitHub (feito antes do conteúdo; o redirect do GitHub cobre remotes e URLs antigas durante a transição)
- Risco aceito: URLs `raw.githubusercontent.com` antigas dependem do redirect do GitHub — mitigado atualizando as URLs no README no mesmo change
- Risco aceito: quem tiver o plugin instalado perde os comandos `/sdd-iuri:*` até reinstalar — é o custo do breaking change, endereçado pelo guia de migração (R5) e pelo corte da v1.0.0
- [ ] Pendência: publicar a documentação em EN (ou bilíngue) e abrir CONTRIBUTING + código de conduta antes de divulgar o framework à comunidade
