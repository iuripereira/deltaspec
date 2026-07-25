# HANDOFF.md — diário de bordo

> Andamento contínuo do trabalho: o que está em curso **agora**, o que acabou de ser feito, os problemas do momento e os próximos passos imediatos. Atualize com frequência dentro da própria sessão. **Janela rolante:** entrada antiga sai — histórico permanente é [CHANGELOG](CHANGELOG.md) + git; débito/pendência/lição é [DEBT.md](DEBT.md); decisão com renúncia é [docs/adrs/](docs/adrs/); o que vige é [specs/TRUTH.md](specs/TRUTH.md). Em conflito de merge, mantenha a **união das verdades** — nunca sobrescreva o progresso de outra sessão.

**Atualizado em:** 2026-07-21

## Agora
- Nada em curso — sessão IMEX de 20-07 (noite) fechada; próximo marco é a delta real no travelplanner.

## Feito recentemente
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
- Nenhum bloqueio. Débito durável: [DEBT.md](DEBT.md) (DT-001, DT-003..DT-007 abertos; DT-002/DT-008 quitados).

## Próximos passos imediatos
- Rodar `/plugin update sdd-iuri` no Claude Code local (cache anterior às deltas 007–008).
- Rodar uma delta real com o gate do specify no imex-travelplanner (fecha o piloto ADR-0009 e o gatilho do DT-004).
- Promover a ADR-0009 quando o piloto fechar: `Accepted` + MUDA RNF1 no TRUTH.md + avaliar check mecânico do doc-profile.
- Próxima delta livre: 010. Débito aberto: DT-001, DT-004, DT-005, DT-006 (guarda), DT-007, DT-009.
