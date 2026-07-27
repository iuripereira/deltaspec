# delta-012 — descoberta
Estado: proposta · Data: 2026-07-27 · Branch: feat/012-descoberta

## Contexto (≤3 linhas)
O ciclo começa no specify com "pedido de feature" pronto; tudo que o produz (entrevista de negócio, processo legado as-is, ingestão de transcrição/planilha) está fora do framework, e GLOSSARY/DATA_DICTIONARY nascem vazios sem processo que os preencha. A skill `descoberta` cobre essa fase pré-specify, inspirada em AI-DLC (Mob Elaboration), BMAD (document-project) e Reversa (modelo de confiança).

## Mudanças

### R1 — ADICIONA: a skill `descoberta` cobre a fase pré-specify, produzindo dossiê a partir de insumos brutos
- DADO um projeto com insumos brutos de descoberta (transcrição/resumo de reunião, planilha, vídeo, docs legados) QUANDO `/sdd-iuri:descoberta` roda ENTÃO ela inventaria os insumos (o que existe, o que falta, pessoas-fonte, sistemas citados) e grava o dossiê em `docs/discovery/AAAA-MM-DD-<evento>.md` com o processo as-is, entidades, regras e dores minerados
- DADO um vídeo entre os insumos QUANDO `ffmpeg` está disponível ENTÃO frames amostrados (scene detection + intervalo fixo) dos trechos relevantes são fonte válida de mineração; `ffmpeg` ausente → o vídeo entra no inventário como lacuna, com aviso, sem quebrar a skill

### R2 — ADICIONA: todo claim do dossiê carrega nível de confiança e fonte rastreável
- DADO um claim extraído dos insumos QUANDO registrado no dossiê ENTÃO carrega uma tag `confirmado` (evidência direta), `inferido` (dedução/padrão) ou `lacuna` (requer validação humana) e a fonte rastreável (timestamp da transcrição, `arquivo:linha` ou frame); claim sem fonte não entra no dossiê

### R3 — ADICIONA: a descoberta popula GLOSSARY.md e DATA_DICTIONARY.md
- DADO termos de domínio e entidades minerados QUANDO o dossiê fecha ENTÃO `GLOSSARY.md` e `DATA_DICTIONARY.md` do projeto recebem as entradas novas com o nível de confiança, por append/merge — entrada existente nunca é sobrescrita sem divergência apontada

### R4 — ADICIONA: divergências contra a baseline vigente
- DADO um PRD ou TRUTH.md vigente no projeto QUANDO a mineração encontra contradição ou omissão ENTÃO gera `docs/discovery/divergencias-<baseline>.md` com tabela *baseline diz × descoberta revelou × impacto (IDs afetados) × ação proposta*
- DADO um projeto sem baseline QUANDO a skill roda ENTÃO a etapa de divergências se omite com aviso

### R5 — ADICIONA: pauta de validação em Mob Elaboration
- DADO o dossiê fechado QUANDO a skill encerra ENTÃO existem `docs/discovery/questions.md` (perguntas ranqueadas por dono/stakeholder) e um roteiro de sessão de validação em que a IA propõe o entendimento claim a claim e o stakeholder valida/corrige (Mob Elaboration; Domain Storytelling como técnica de condução)

### R6 — ADICIONA: presunção não vira requisito sem validação
- DADO claims `inferido` ou `lacuna` QUANDO o resultado da descoberta alimenta um PRD ou o specify ENTÃO eles entram marcados `[PRESUNÇÃO]`; somente claim `confirmado` ou validado em sessão entra sem marca

### R7 — ADICIONA: ponte da descoberta com o ciclo registrada nos adapters
- DADO o plugin `max` instalado QUANDO a descoberta encerra ENTÃO a skill oferece `max:write-prd` como motor do PRD rascunho, com o dossiê como contexto e o contrato de `[PRESUNÇÃO]` na invocação; `max` ausente → fallback nativo (PRD rascunho próprio) com o aviso de degradação
- DADO a tabela de contrato de `adapters.md` QUANDO a delta consolida ENTÃO existe a linha da fase `descoberta` (pré-specify) com skill esperada, ponto sensível e fallback

## Requisitos não funcionais
<!-- degradação já coberta por RNF2 vigente (delta-005): os fallbacks de ffmpeg e max:write-prd desta delta seguem aquela regra; nenhum RNF novo -->

## Fora de escopo
- Engenharia reversa automatizada de planilha (parser de fórmulas) — o protocolo é guiado/manual no roteiro de sessão.
- Transcrição de áudio/vídeo (assume transcrição já existente; gerá-la é pré-processamento do usuário).
- Tooling de Event Storming/diagramação obrigatória — diagrama segue o `doc-profile.yaml` do projeto-alvo.
- Persistir mídia bruta (vídeo/frames) no git do projeto-alvo — a skill instrui gitignore.

## Dependências e riscos
- Leitura visual de frames depende de harness multimodal; sem ela, frames viram lacuna no inventário.
- `max:write-prd` cobre entrevista com o dev, não com stakeholder externo — a sessão de validação (R5) continua sendo o mecanismo com terceiros.
- [ ] Primeira execução externa real da skill (projeto imex-estoque-inteligente) alimenta a evidência do DT-004 — registrar o resultado no DEBT.md após a rodada.
