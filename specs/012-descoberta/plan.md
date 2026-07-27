<!-- resumo sdd-iuri · ≤15 linhas · única parte do plano lida pelo analyze e pelo humano -->
**Objetivo:** criar a skill `descoberta` (fase pré-specify: insumos brutos → dossiê com confiança → pauta de validação) e cabeá-la no ciclo. **Cobre:** R1–R7 (da delta-012) **Decisões duráveis → ADRs:** ADR-0011 (skill própria pré-specify; renúncias: delegar ao write-prd, portar BMAD) **Riscos assumidos:** leitura de frames exige harness multimodal (degrada p/ lacuna); primeira execução externa real fica para o projeto imex-estoque-inteligente (evidência DT-004).

---

# Plano — delta-012 descoberta

## Passo 1 — SKILL.md da skill (R1, R2, R5, R6, R7 parcial)

Criar `skills/descoberta/SKILL.md` seguindo o padrão das skills existentes (Overview, processo em fases, erros comuns, arquivos da skill). Conteúdo:

- **Frontmatter** `name: descoberta` + `description` com gatilhos: "/sdd-iuri:descoberta", "processo de descoberta", "discovery", "minerar transcrição/reunião/kickoff", "documentar processo legado/as-is", "pré-specify sem PRD validado".
- **Fases (6):**
  1. *Inventário de insumos* — listar transcrições, resumos, vídeos, planilhas, docs, sistemas citados, pessoas-fonte; registrar o que falta. Vídeo: frames via `ffmpeg` (scene detection `select='gt(scene,0.3)'` + amostragem fixa nos trechos de tela compartilhada); `ffmpeg` ausente → vídeo vira lacuna com aviso.
  2. *Mineração* — processo as-is, entidades, regras, dores, KPIs ausentes; **todo claim com tag `confirmado`/`inferido`/`lacuna` + fonte (timestamp, arquivo:linha, frame)**; claim sem fonte não entra.
  3. *Dossiê* — `docs/discovery/AAAA-MM-DD-<evento>.md` (template) + popular `GLOSSARY.md`/`DATA_DICTIONARY.md` por append/merge com confiança; conflito com entrada existente → divergência apontada, nunca sobrescrita silenciosa.
  4. *Divergências* — se há PRD/TRUTH vigente: `docs/discovery/divergencias-<baseline>.md` (template); sem baseline → omite com aviso.
  5. *Pauta de Mob Elaboration* — `docs/discovery/questions.md` ranqueado por dono + roteiro de sessão (template): IA propõe claim a claim, stakeholder valida (Domain Storytelling na condução).
  6. *Saída* — oferecer `max:write-prd` com o dossiê como contexto e contrato `[PRESUNÇÃO]`; fallback nativo com aviso. Instruir gitignore para mídia bruta.
- **Erros comuns** (tabela): inferência sem tag vira fato · re-entrevistar em vez de propor p/ validação · dossiê sem fonte rastreável · minerar sem inventariar (perde lacunas) · commitar mídia bruta.

## Passo 2 — Templates (R2, R4, R5)

`skills/descoberta/references/templates/`:
- `dossie.md` — cabeçalho (evento, data, participantes, insumos), seções: Inventário de insumos · Processo as-is · Entidades e termos · Regras e dores · Claims (formato: `- [confirmado|inferido|lacuna] afirmação — fonte`).
- `divergencias.md` — tabela `| # | Baseline diz (ref) | Descoberta revelou (fonte) | Impacto (IDs) | Ação proposta |`.
- `pauta-validacao.md` — questions ranqueadas por dono + roteiro Mob Elaboration (abertura, validação claim a claim, walkthrough de artefato legado, fechamento com registro do que virou confirmado).

Mínimos (ponytail): cada template ≤40 linhas.

## Passo 3 — Cabear nos adapters (R7)

`skills/spec-feature/references/adapters.md`:
- Linha nova na tabela de contrato: fase `descoberta (pré-specify)` → skill `sdd-iuri:descoberta` (própria) + motor de PRD `max:write-prd` → ponto sensível: nome da skill max; formato do PRD.
- Seção curta `## descoberta / write-prd` com contrato de invocação (dossiê como contexto, `[PRESUNÇÃO]` obrigatória) e fallback (PRD rascunho nativo com aviso).
- `skills/spec-feature/SKILL.md`: 1 linha no Overview citando a pré-fase opcional (referencia, não duplica).

## Passo 4 — Distribuição e governança (cobre: infra)

- `README.md`: skill nova na lista (grep -i por contagem de skills — lição 2026-07-20).
- `.claude-plugin/marketplace.json`: idem.
- `CHANGELOG.md` `[Não lançado]` → Adicionado.
- `HANDOFF.md`: sessão registrada.

## Passo 5 — Gate, PR, archive, release

- `python3 scripts/check_cycle.py 012-descoberta` → analyze.md com veredito.
- PR (split condicional C7 se >limiar), merge, archive (consolida R no TRUTH.md, DT da pendência, `_archive/`), tag v0.8.0 via release-please ou manual conforme fluxo do repo.

## Verificação por passo

- P1–P2: arquivos existem; frontmatter válido (name+description); templates citados pelo SKILL.md existem.
- P3: `grep -n descoberta skills/spec-feature/references/adapters.md` mostra tabela + seção + fallback.
- P4: `grep -ic skill README.md .claude-plugin/marketplace.json` consistente com 9 skills.
- P5: check_cycle sem ALTO/CRÍTICO; C4 sem perda no TRUTH.
