# HANDOFF.md — diário de bordo

> Andamento contínuo do trabalho: o que está em curso **agora**, o que acabou de ser feito, os problemas do momento e os próximos passos imediatos. Atualize com frequência dentro da própria sessão. **Janela rolante:** entrada antiga sai — histórico permanente é [CHANGELOG](CHANGELOG.md) + git; débito/pendência/lição é [DEBT.md](DEBT.md); decisão com renúncia é [docs/adrs/](docs/adrs/); o que vige é [specs/TRUTH.md](specs/TRUTH.md). Em conflito de merge, mantenha a **união das verdades** — nunca sobrescreva o progresso de outra sessão.

**Atualizado em:** 2026-07-28

## Agora

- **delta-016 (harness) implementada** na `feat/016-harness` — Tasks 1–7 completas, review por task limpo. Próxima: review em 2 eixos paralelos (R35) → PR da implementação → archive (consolida R40–R44, MUDA R12 no TRUTH, tag v0.12.0).
- Plugin local atualizado: revisão `d6b9814` (v0.11.0) ativa no `installed_plugins.json`.

## Feito recentemente
- 2026-07-28 — **delta-015 (fluxo) arquivada** (#57 artefatos + #58 implementação + PR de archive): R36–R39 no TRUTH (perfil `completo|enxuto`, prototipação CONDITIONAL, `test-plan.md`, tipo `bugfix`), MUDA R12 (C8 no gate) e MUDA R35 (fusão de eixos no enxuto), ADR-0013, `v0.11.0`.
- 2026-07-28 — **delta-015 (fluxo) ciclo completo até o review**: perfil `completo|enxuto` (ADR-0013), prototipação CONDITIONAL (categoria `prototipo` no doc-profile), `test-plan.md` + C8 no gate (TDD), tipo `bugfix` reconhecido pelo gate, MUDA R12/R35. Clarify via grill-me (aggregate 0.06, 4 decisões do usuário); split R17 executado (PR #57 só de artefatos). O review em 2 eixos paralelos (dogfood do R35) pegou **falso negativo real do C8** (comentário de template enganava o `campo()`) — corrigido com TDD + 2 refactors da delete-list; recusas justificadas no analyze.md.
- 2026-07-28 — **delta-014 (motores) implementada e arquivada** (#55 + PR de archive): Fase 1 do upgrade — pin do max mantido como **fork deliberado** (ADR-0012, decisão do usuário; gatilho de migração na delta-017), política de pins com verificação datada, **review em dois eixos paralelos** formalizado em adapters/cycle, R34–R35 no TRUTH, `v0.10.0`. O review da própria delta (dogfooding) pegou o índice de ADRs 3× defasado (0009/0011/0012) — quitado.
- 2026-07-28 — **delta-013 (higiene) implementada e arquivada** (#53 + PR de archive): Fase 0 do plano de upgrade — manifestos com as 9 skills + check de inventário no CI, hook pré-commit versionado (DT-005 quitado; cobre deleção de `.md`), ADR-0009 `Accepted` com MUDA RNF1 (exceção de doc cliente), R31–R33 no TRUTH, DT-013 roteado (check do doc-profile), `v0.9.0`. Review em 2 eixos com subagentes paralelos (padrão que a Fase 1 formaliza nos adapters).
- 2026-07-28 — **Plano de reavaliação/upgrade do framework aprovado**: pesquisa verificada (AI-DLC, Pocock atual, superpowers 6.2, harness Anthropic, Jira acli/Rovo MCP, Figma vs Mermaid, graphify) + 6 fases (deltas 013–018). Decisões-chave: tickets.md canônico no repo com Jira como projeção; Mermaid fonte + Figma apresentação; graphify como 4º motor opcional.
- 2026-07-27 — **delta-012 implementada e arquivada** (#50 + PR de archive): skill `descoberta` (fase pré-specify — insumos brutos → dossiê com claims `confirmado`/`inferido`/`lacuna`, GLOSSARY/DATA_DICTIONARY, divergências, pauta de Mob Elaboration), R24–R30 no TRUTH.md, ADR-0011, adapters com contrato descoberta/write-prd, `v0.8.0`. Motivada pelo gap real do imex-estoque-inteligente (PRD contratualizado sem validação da stakeholder, contradito pelo kickoff). Pendência DT-012 (execução externa) roteada.
- 2026-07-26 — **delta-011 arquivada** (#49): R21–R23 consolidados no TRUTH.md, pendência do rodapé `CONFIDENCIAL`/marca d'água roteada para DT-011, `v0.7.0`.
- 2026-07-26 — **delta-011 implementada** (#48): auditoria do prompt jurídico solto (não versionado) e integração como `doc-entregavel/references/juridico.md`, com dispatch por tipo na SKILL.md. Achado principal: a premissa sobre assinatura eletrônica estava invertida — o STJ (REsp 2.205.708-PR, Info 871, 04/11/2025) dispensa testemunhas com qualquer modalidade cuja integridade seja conferida por provedor, sem exigir ICP-Brasil; a política conservadora ficou, agora como redundância declarada. `requisitos-cliente` passou a exigir Visão (produto e/ou projeto), orçamento por fase, prazo e cronograma com marcos de pagamento. Detalhes no CHANGELOG (`[Não lançado]`).
- 2026-07-21 — Skill `eu-tenho-tdah` (perfil de escrita pessoal do Iuri) adicionada, fora do ciclo de delta specs; README documenta como skill always-on.
- 2026-07-21 — Balanço da rodada IMEX no DT-004: evidência parcial anotada (5 skills validadas nos 4 repos; ciclo de deltas com gate ainda sem execução externa) e gatilho precisado — quita com a delta real arquivada no travelplanner. Segue aberto.
- 2026-07-20 (noite) — **Stack visual normativo + regras de página + guia de prosa** (#33) e erro comum de tabela aninhada (#34), da revisão pré-assinatura IMEX: ADR-0009 ganhou a tabela categoria→ferramenta (com Excalidraw) e o vínculo "a ferramenta segue a categoria"; `exporta_entregavel.py` com regras de página (break-inside, `.fig-pagina`/`.paisagem`, cantSplit/tblHeader); `spec-feature/references/prosa.md` (EARS PT-BR, tabelas de decisão, checklist pré-baseline); fixes do export validados nos 4 PRDs IMEX (8 exports, 2 rodadas). Toolchain `.dsl` (docker structurizr→C4-PlantUML) e `.excalidraw` (Playwright) validada. Novo DT-009.
- 2026-07-20 — Piloto ADR-0009 (doc-profile + doc-entregavel, #30) executado nos 4 repos IMEX: `doc-profile.yaml` com `publico.cliente: true` nos 4; no travelplanner os `.mmd` nasceram como espelhos extraídos do portal; entregáveis PDF+DOCX reproduziram capa/tipografia dos de imex-contratos e superaram (referências não embutiam diagrama). Achado: PNG mermaid no viewport default (800px) sai de baixa resolução em diagrama largo → `--width` na largura nativa do SVG, incorporado à skill.
- 2026-07-20 — delta-009 implementada (#28) e arquivada: **C7** no `check_cycle.py` mede o split
  de PR (BAIXO acima do limiar); MUDA R12 consolidado no TRUTH.md (delta-009); DT-003 quitado.
- 2026-07-20 — DT-002/DT-008 quitados no #27 (mergeado): espelhos do limiar de PR de 4→1
  (`SKILL/detection/analyze.md` citam "o limiar canônico"; `500` só no `CLAUDE.md`); `deps.toml`
  governa `15 linhas` e `10 dom`. Chore, sem tag/bump.
- 2026-07-20 — Formatação: quebra de linha manual removida da prosa em 27 `.md` (style, sem
  delta — mudança mecânica, zero conteúdo/requisito alterado, não cabe no template de spec).
- 2026-07-20 — Fechamento da reorganização de registros (#25): marketplace.json, README,
  docstrings, DEBT.md e ADR-0008 alinhados ao TRUTH vigente; `v0.5.1`.
- 2026-07-20 — delta-008 arquivada (#24): R20 + MUDA R15 no TRUTH.md, `v0.5.0`; ruleset passou a exigir também o check `commits`; description/topics do repo atualizados no GitHub.
- 2026-07-20 — delta-008 implementada (#23): skill `sdd-iuri:handoff`.
- 2026-07-20 — delta-007 implementada (#21) e arquivada (#22): DEBT.md (DT-NNN), STATE diário de bordo, C6 → DT-NNN, ADR-0007, `v0.4.0`.
- 2026-07-19 — Higiene de registros (#19), backfill de ADRs 0002..0006 (#20), varredura completa (110 agentes) e plano aprovado.

## Problemas atuais
- Nenhum bloqueio. Débito durável: [DEBT.md](DEBT.md) (DT-001, DT-004..DT-007, DT-009..DT-011 abertos; DT-002/DT-003/DT-008 quitados).

## Próximos passos imediatos
- Fase 3 do plano de upgrade (delta-016): vocabulário de harness, arestas de bloqueio no tasks.md (grafo → execução paralela por worktree), trilha de auditoria de aprovação, avaliar check tipo `/converge`; graphify como 4º motor opcional (adapter ADR-0004, instalação manual consciente).
- Rodar uma delta real com o gate do specify no imex-travelplanner (gatilho do DT-004 e do DT-013) — agora com perfil e test-plan disponíveis.
- Rodar `/plugin update sdd-iuri` no Claude Code local (cache anterior às deltas 013–015).
- Próxima delta livre: 016. Débito aberto: DT-001, DT-004, DT-006 (guarda), DT-007, DT-009, DT-010 (guarda), DT-011, DT-013.
