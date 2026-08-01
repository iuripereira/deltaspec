# delta-023 — dívida técnica com score e projeção para tickets
Estado: proposta · Data: 2026-08-01 · Branch: feat/023-divida-tecnica-e-tickets · Perfil: completo — script novo com lógica determinística, mudança de contrato normativo (MUDA R18) e integração externa inédita (aprovado: 2026-08-01)
<!-- Numeração: 022 é a última arquivada; 017 segue reservada para a Fase 4 (Jira/tickets.md) e esta delta salta o número sem consumi-lo (R5). Esta delta constrói o mecanismo de projeção que a delta-017 reusará no tickets.md. -->
<!-- Clarify: conduzido em plan mode (2026-08-01) por 8 perguntas fechadas — alcance, arquitetura, campos, estados, escopo vs delta-017, profundidade da ida, volta e ferramenta a validar. Decisões no plano aprovado; não re-entrevistar (cycle.md). -->

## Contexto (≤3 linhas)
O `DEBT.md` tem 19 itens sem priorização mecânica e sem validação nenhuma — o `deps.toml` o exclui da varredura e nenhum gate o lê. O usuário confirmou que GitHub Issues e Jira **serão usados**, o que aciona a cláusula de reabertura escrita na própria ADR-0007 e converge com o desenho da delta-017 reservada (arquivo canônico, ferramenta como projeção).

## Mudanças
<!-- só o que muda; um bloco por requisito; ADICIONA/MUDA/REMOVE em relação ao TRUTH.md -->

### R1 — MUDA R18 (delta-007): DEBT.md registra priorização e ciclo de vida, além do fato
- DADO um débito, pendência ou guarda novo QUANDO registrado ENTÃO entra no `DEBT.md` da raiz como linha `DT-NNN` (próximo número livre — numeração global, nunca reutilizada) com natureza, título curto, descrição, localização, origem, data de abertura, fila, gatilho de correção, status e chave externa
- DADO um item quitado QUANDO a correção mergeia ENTÃO o status do item muda para quitado, com data — a linha nunca é apagada (a trajetória aberto→quitado é o registro da evolução)
- DADO um tipo de projeto que recebe `docs/adrs/` na matriz de detection.md QUANDO o scaffold do projeto-init roda ENTÃO cria também `DEBT.md` a partir do template da skill, e só se não existir
- DADO um item de natureza `débito` ou `pendência` QUANDO ele é registrado ENTÃO carrega `Título` (sintoma observável, não adjetivo), `Local` (link relativo a artefato real do repo) e `Fila` (`P{1|3|9}·J{1|3|9}·Pr{1|3|9}`, com sufixo opcional `trilha` ou `!<override>(AAAA-MM-DD)`); item de natureza `guarda` fica com `—` nos três, por não ter principal nem juros
- DADO os estados do registro QUANDO um item muda de situação ENTÃO vale o conjunto `aberto` · `aceito (gatilho obrigatório)` · `vigente` (guarda permanente) · `descartado (AAAA-MM-DD, motivo)` · `quitado (AAAA-MM-DD, ref)`, e `stale` **nunca é escrito** — é derivado pelo script a partir do git

### R2 — ADICIONA: fila de dívida determinística, calculada por script e nunca persistida
- DADO um `DEBT.md` no formato do R1 QUANDO `debito.py fila` roda ENTÃO ele imprime a fila ordenada por `override` primeiro, `trilha` em seguida e `score` decrescente no resto, com `score = (juros × probabilidade) / principal` calculado na leitura — o valor **não é gravado** em nenhum arquivo
- DADO um item pontuável sem `Local`, com link de `Local` morto, sem `Título` ou com `Fila` malformada QUANDO o script roda ENTÃO ele reporta erro nomeando o `DT-NNN` e o campo, e sai com código ≠ 0
- DADO o repositório com git QUANDO o script roda ENTÃO a probabilidade de incidência de cada item é derivada do churn do arquivo apontado em `Local` (percentil sobre `git log --since=<janela> --name-only`) e a divergência contra o valor declarado é reportada; sem git, a derivação se omite com aviso e o valor declarado vale
- DADO um item com juros ≥ 3 cuja linha não muda há mais que o limiar de dias QUANDO o script roda ENTÃO ele é marcado `stale` na saída — a data vem de `git log -1 -S"DT-NNN" -- DEBT.md`, e a marca força decisão explícita entre agendar, aceitar ou descartar
- DADO o parsing da tabela QUANDO o script lê uma linha ENTÃO cada campo é lido pela **posição da coluna**, nunca por busca de texto na linha inteira — prosa que mencione a sintaxe (ex.: a palavra "aberto" dentro de uma célula de status) não pode ser confundida com o campo (lição de 2026-07-28)

### R3 — ADICIONA: ferramenta de ticket é projeção do arquivo, com ida mecânica e volta aprovada
- DADO o `DEBT.md` QUANDO `debito.py exportar` roda ENTÃO ele emite o JSON canônico dos itens e os dialetos de importação (bulk do Jira e linhas de criação do GitHub) em arquivos, **sem acessar a rede** — quem executa os comandos é a skill, nunca o script (mesmo padrão do `projeto-infra`)
- DADO um item projetado QUANDO o ticket é criado ENTÃO ele carrega a etiqueta determinística com o `DT-NNN` e o título prefixado pelo ID, e a chave devolvida pela ferramenta (`gh#NNN`, `PROJ-NNN`) é gravada na coluna `Externo` da linha correspondente — é essa chave, e não o título, que garante idempotência na próxima execução
- DADO o estado coletado da ferramenta externa QUANDO `debito.py diff` roda ENTÃO ele emite a tabela *DEBT.md diz × ferramenta diz × impacto × ação proposta* (formato de divergências do R27), cobrindo item sem ticket, ticket fechado com item ainda aberto e ticket sem item correspondente
- DADO uma divergência detectada QUANDO ela vira mudança no `DEBT.md` ENTÃO a alteração é **proposta ao usuário e só aplicada após aprovação** — a ferramenta externa nunca sobrescreve o arquivo, que permanece a fonte da verdade
- DADO a ferramenta externa ausente, sem autenticação ou sem projeto configurado QUANDO a projeção é invocada ENTÃO o `DEBT.md` segue valendo sozinho, com no máximo 1 linha de aviso — degradação graciosa (RNF2)

## Fora de escopo
- `tickets.md` das deltas e a skill `spec-tickets` — Fase 4, **delta-017 reservada**, que reusará o mecanismo desta delta.
- Propagação ao template distribuído (`projeto-init`), à `canonical-rules.md` e ao README — só depois do dogfood neste repo.
- Check bloqueante no `check_cycle.py`: mecanizar antes do formato estabilizar produziria falso LIBERADO (mesma cautela do DT-013, ADR-0006).
- Execução real no Jira (sem projeto nem credencial) — o dialeto é emitido e verificado por formato, não por criação.
- Reclassificar a coluna `Natureza` (mistura tipo, origem e função) — exigiria MUDA R16; vira débito registrado.
- Coletor automático de dívida (SonarQube, CodeScene) e conversão de score em moeda.

## Dependências e riscos
- `gh` autenticado é pré-requisito da validação de ponta a ponta; `acli` e um projeto Jira não existem hoje, e o caminho Jira fica emitido-e-não-executado até existirem.
- Os *Issue Fields* do GitHub (score numérico, data) só valem em repositório de organização — `iuripereira/deltaspec` é pessoal, então esses valores seriam **descartados em silêncio**; score e data vão no corpo do ticket e em etiqueta de faixa.
- O repositório é público e os tickets criados também serão; o conteúdo já está publicado hoje no `DEBT.md`, mas o corpo gerado é conferido antes da criação.
- A ADR-0021 supersede a ADR-0007 — a ADR antiga permanece imutável, marcada `Superseded by`, e a citação em `CLAUDE.md` passa a apontar a nova.
- O conjunto de artefatos + implementação passa do limiar canônico de PR: split obrigatório (R17), artefatos primeiro.
- [ ] Propagar o modelo ao template distribuído do `projeto-init` depois do dogfood — vira `DT-NNN` no archive.
