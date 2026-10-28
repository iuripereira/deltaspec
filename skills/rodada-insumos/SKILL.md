---
name: rodada-insumos
description: Use when a NEW client input arrives in a project that already has deltaspec discovery records (docs/discovery/, questions.md, PRD-proposta) — a recorded meeting, a Teams/e-mail message, a spreadsheet, form answers — and it must be reconciled into the living records and requirements. Runs the full cycle inventory → mining (via descoberta) → reconciliation → decision gate with the user → PRD version bump with frozen deliverable → open PR + digest. Triggers include "/deltaspec:rodada-insumos", "rodada de insumos", "chegou insumo novo", "conciliar esse insumo", "novas respostas do cliente", "minerar essa reunião e atualizar o PRD", "o cliente mandou/registrou/respondeu".
---

# rodada-insumos

## Overview

Regime **recorrente pós-PRD-proposta** do ciclo: cada insumo novo do cliente (reunião, mensagem, planilha, respostas de formulário) atravessa o mesmo pipeline — minerar, conciliar com os registros vivos, confirmar decisões com o usuário, atualizar requisitos e parar num PR aberto. A `descoberta` abre o projeto; esta skill o **mantém sincronizado** com o cliente, com a mesma régua de confiança e os mesmos registros. Composição, não duplicação: a mineração delega às fases 1–3 da [descoberta](../descoberta/SKILL.md); o fechamento segue a [handoff](../handoff/SKILL.md). Registro da decisão e renúncias: [ADR-0033](../../docs/adrs/ADR-0033-rodada-insumos-skill-propria.md).

Regras de ouro herdadas e mecanizadas aqui: **inferência nunca vira fato** (todo claim com confiança + fonte); **propor, não re-entrevistar** (pergunta nova sempre carrega proposta de encaminhamento); **baseline muda por divergência registrada e gate humano, nunca por edição silenciosa**.

## Processo (7 fases)

1. **Inventário.** O que chegou desde a última rodada (= data do dossiê mais recente em `docs/discovery/`). As fontes são do projeto — declaradas num command wrapper do workspace ou perguntadas **uma** vez (ex.: pasta de mídia bruta fora do git, MCP de reuniões, export de formulário, e-mail). Snapshot de fonte dinâmica = arquivo **novo** datado (`respostas-<fonte>-AAAA-MM-DD.json`), comparado com o anterior — só o novo entra na rodada. **Nada novo em nenhuma fonte → digest "rodada vazia (fontes checadas: …)" e parar** — sem dossiê vazio.
2. **Mineração.** Delegar às fases 1–3 da `descoberta`: dossiê datado `docs/discovery/AAAA-MM-DD-<evento>.md` ([template](../descoberta/references/templates/dossie.md)), claim com `confirmado`/`inferido`/`lacuna` + fonte rastreável (`arquivo:linha`, timestamp, id de resposta, frame), GLOSSARY/DATA_DICTIONARY por append/merge (dicionário no formato de 6 colunas por campo — camadas.md da skill `modelo-dados`; confiança como prefixo da Definição). Dossiê do dia já existe → append, nunca sobrescrever. Insumo que chegou **atrasado** (datado antes de eventos já minerados) → "nota de sequência" no dossiê tratando duplicidade com o que outras vias já capturaram, em vez de reabrir questão fechada.
3. **Conciliação (4 trilhos).** Para cada achado do dossiê, um destino — nunca deixar achado sem trilho:
   - **Fecha pergunta** → registro vivo de questões (`questions.md`): status na visão geral + nota datada com fonte no corpo. Pergunta nunca some — a trajetória é o registro.
   - **Conflita com ou amplia a baseline vigente** → linha em `docs/discovery/divergencias-<baseline>.md` ([template](../descoberta/references/templates/divergencias.md)): *baseline diz (ref) × descoberta revelou (fonte) × impacto (IDs) × ação proposta*.
   - **Informação nova sem pergunta** → pergunta nova com ID estável (nunca reusar) **e proposta de encaminhamento** — a skill propõe, o stakeholder corrige; pergunta em branco é re-entrevista.
   - **Artefato recebido** → inventário do dossiê + baixa no checklist de insumos pendentes do projeto.
   Retrato histórico (pedido formal, snapshot de pauta) ganha **nota datada** apontando o registro vivo, nunca reescrita.
4. **Gate de decisões (toda rodada).** Antes de tocar PRD/escopo: apresentar as decisões da rodada como perguntas numeradas com recomendação (formato `❓ Qn — título: corpo` / `➡️ recomendação`), uma rodada por conjunto de decisões independentes, e **aguardar as respostas do usuário**. Com o plugin `mattpocock-skills` instalado, conduza pela skill `grilling`; ausente → condução nativa no mesmo formato, com o aviso *"saída degradada: mattpocock-skills/grilling não instalado"*. **Sem resposta = sem edição de PRD** — os achados ficam no dossiê/divergências aguardando.
5. **Atualização do produto** — só o que o gate confirmou:
   - `[PRESUNÇÃO]` fechada vira *"confirmada em AAAA-MM-DD (fonte)"*; requisito ampliado ganha **subitem novo** (RF-NNN.M), nunca reescrita silenciosa; decisão fechada é riscada da tabela de diferidas com data e fonte.
   - **Bump de versão do PRD-proposta** (vX.Y+1) com linha no histórico de revisões — é ela que alimenta o "o que mudou" dos entregáveis.
   - **Entregável congelado da versão nova = arquivo novo** com a versão no nome ([doc-entregavel](../doc-entregavel/SKILL.md)); baseline anterior intacta; ponteiros de publicação (mapas `PUBLICADAS` e afins) atualizados no mesmo change.
   - **Nunca promover PRD-proposta a baseline contratual** — decisão do humano, por escrito.
6. **Fechamento.** CHANGELOG `[Não lançado]`; branch própria da rodada (`docs/rodada-insumos-<evento>`); commit Conventional; **PR aberto — a skill para aqui** (merge = humano). Lição recorrente/estrutural → `DT-NNN` no registro de débitos do projeto. Fim de sessão → `handoff`.
7. **Digest final** (única saída longa da rodada, [template](references/digest.md)): fontes · dossiês · perguntas fechadas/novas com IDs e fonte · divergências · presunções confirmadas · versão nova do PRD · PR aberto (link) · **passos pós-merge que ficam com o humano**, listados explicitamente (publicação de site/report, tag, promoção de baseline).

## Erros comuns

| Erro | Correto |
|---|---|
| Sobrescrever dossiê, snapshot ou registro de questões | Append/merge; snapshot novo datado; item respondido muda de status, nunca some |
| Resposta registrada "só no e-mail"/chat | Toda resposta retorna ao registro vivo com autor, data e fonte |
| Claim `inferido` lido depois como fato | Tag de confiança + fonte rastreável obrigatórias; sem fonte, não entra |
| Reusar ou apagar ID de pergunta/requisito | ID novo, estável; histórico fica — outros documentos apontam para ele |
| Editar PRD/escopo antes do gate de decisões | Gate primeiro, em toda rodada; sem resposta do usuário, sem edição |
| Sobrescrever entregável de baseline anterior | Arquivo novo com a versão no nome; o antigo é histórico (possivelmente assinado) |
| Mergear PR, publicar site ou promover baseline por conta própria | A skill para no PR aberto; o resto é do humano, listado no digest |
| Pergunta nova em branco ("o que é X?") | Sempre com proposta de encaminhamento — propor, não re-entrevistar |
| Rodada sem insumo virando dossiê vazio | Digest "rodada vazia" com fontes checadas e parar |
| Insumo atrasado reabrindo questão já fechada por outra via | Nota de sequência no dossiê apontando a duplicidade |
| Ampliar requisito reescrevendo o texto original | Subitem novo (RF-NNN.M) + linha no histórico de revisões |

## Arquivos da skill

- `references/digest.md` — template do digest final da rodada.
- Dossiê e divergências reusam os templates da `descoberta` (`../descoberta/references/templates/`), citados nas fases 2–3.
