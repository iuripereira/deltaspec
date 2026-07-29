---
name: descoberta
description: Use when a project needs discovery BEFORE any spec exists — mining raw inputs (meeting transcript/summary, video, legacy spreadsheet, scattered docs) into an as-is dossier with explicit confidence levels, populated glossary/data dictionary, divergences against an existing baseline and a stakeholder validation agenda. Triggers include "/deltaspec:descoberta", "processo de descoberta", "discovery", "minerar transcrição", "reunião de kickoff", "documentar processo legado", "as-is", "levantar requisitos com stakeholder", or entering the deltaspec cycle without a validated PRD.
---

# descoberta

## Overview

Fase **pré-specify** do ciclo deltaspec: transforma insumos brutos de descoberta em um **dossiê as-is com incerteza explícita**, pronto para virar PRD (via `max:write-prd`) ou alimentar o `specify`. Fundamentos: **AI-DLC/AWS** (Inception + ritual *Mob Elaboration*: a IA propõe, o stakeholder valida em sessão), **BMAD** (*document-project*: documentar o existente antes do PRD) e **Reversa** (claims com nível de confiança). Registro da decisão e renúncias: [ADR-0011](../../docs/adrs/ADR-0011-descoberta-skill-propria.md).

Regra de ouro da fase: **inferência nunca vira fato**. Todo claim carrega confiança e fonte; o que não foi confirmado sai como `[PRESUNÇÃO]`.

Pipeline com a pré-fase (opcional — requisitos já claros entram direto no specify):
```
descoberta → (write-prd) → specify → clarify → plan → ...
```

## Processo (6 fases)

1. **Inventário de insumos.** Liste o que existe — transcrições, resumos, vídeos, planilhas, docs legados, sistemas citados (nome real + fabricante, confirmado na web quando possível), pessoas-fonte — e o que **falta** (planilha não compartilhada, acesso a base, dono ausente). Vídeo: extraia frames com `ffmpeg` (scene detection, ex.: `select='gt(scene,0.3)'`, + amostragem fixa ~1 frame/10s nos trechos de tela compartilhada) para leitura visual; `ffmpeg` indisponível ou harness sem visão → o vídeo entra como **lacuna**, com aviso, e a skill segue.
2. **Mineração.** Extraia dos insumos: processo as-is (fluxo ponta a ponta), entidades de domínio, regras de negócio, dores, indicadores ausentes. **Todo claim recebe tag e fonte**: `confirmado` (evidência direta — citação da transcrição, célula/fórmula, frame), `inferido` (dedução de padrão) ou `lacuna` (só validação humana responde). Claim sem fonte rastreável (timestamp, `arquivo:linha`, frame) **não entra**.
3. **Dossiê + glossário.** Grave `docs/discovery/AAAA-MM-DD-<evento>.md` a partir de [templates/dossie.md](references/templates/dossie.md). Em seguida **popule `GLOSSARY.md` e `DATA_DICTIONARY.md`** do projeto com termos/entidades minerados, cada entrada com o nível de confiança — por **append/merge**: entrada existente nunca é sobrescrita; conflito com o que já está lá vira divergência apontada (fase 4).
4. **Divergências contra a baseline.** Se o projeto tem PRD ou `specs/TRUTH.md` vigente, gere `docs/discovery/divergencias-<baseline>.md` de [templates/divergencias.md](references/templates/divergencias.md): *baseline diz (ref) × descoberta revelou (fonte) × impacto (RN/RF/R afetados) × ação proposta*. Sem baseline → omita a etapa com aviso.
5. **Pauta de Mob Elaboration.** Gere `docs/discovery/questions.md` (perguntas ranqueadas por dono/stakeholder) e o roteiro de sessão de [templates/pauta-validacao.md](references/templates/pauta-validacao.md): a IA apresenta o entendimento **claim a claim** e o stakeholder valida/corrige (condução por Domain Storytelling: "quem faz o quê, com o quê, por quê"). Não entreviste do zero o que o insumo já responde — proponha, não pergunte.
6. **Saída.** Com o plugin `max` instalado, ofereça `max:write-prd` com o dossiê como contexto e o contrato: *"claims `inferido`/`lacuna` entram no PRD marcados `[PRESUNÇÃO]`; só `confirmado`/validado entra sem marca"*. `max` ausente → PRD rascunho nativo (mesma regra) com o aviso *"saída degradada: max/write-prd não instalado"*. Instrua o `.gitignore` do projeto para a mídia bruta (vídeo/frames **não** entram no git).

Fim de fase relevante = commit (regra canônica). A sessão de validação executada atualiza o dossiê: claim validado muda para `confirmado` com fonte "sessão AAAA-MM-DD".

Projeto com graphify habilitado (doc-profile `motores.graphify: true`): as consultas ao grafo de codebase entram como insumo da mineração com fonte `arquivo:linha` e tag mapeada no modelo de confiança — contrato, avisos de instalação e fallback na seção graphify de `spec-feature/references/adapters.md`. Ausente → mineração atual, com 1 linha de aviso.

## Erros comuns

| Erro | Correto |
|---|---|
| Inferência registrada sem tag, lida depois como fato | Todo claim com `confirmado`/`inferido`/`lacuna` + fonte; sem fonte, não entra |
| Re-entrevistar o stakeholder do zero | Mob Elaboration: propor o entendimento claim a claim para validação |
| Minerar direto sem inventariar | O inventário registra o que **falta** — lacunas somem sem ele |
| Sobrescrever entrada existente do GLOSSARY/DATA_DICTIONARY | Append/merge; conflito vira divergência apontada |
| Commitar vídeo/frames no repo | Mídia bruta fica fora do git (gitignore); o dossiê referencia |
| Descoberta virando PRD sem marcas | `[PRESUNÇÃO]` em tudo que não é `confirmado`/validado |
| Tratar planilha legada como doc | Planilha é legacy code: fórmulas + entrevista com quem a constrói |

## Arquivos da skill

- `references/templates/dossie.md` — estrutura do dossiê (inventário, as-is, entidades, claims).
- `references/templates/divergencias.md` — tabela de divergências contra a baseline.
- `references/templates/pauta-validacao.md` — questions por dono + roteiro da sessão de validação.
