<!-- resumo deltaspec · ≤15 linhas · única parte do plano lida pelo analyze e pelo humano -->
**Objetivo:** trocar o motor da camada de apresentação (Figma/FigJam → diagram-design + design-sync), mantendo Mermaid fonte e o entregável no pipeline CLI. **Cobre:** R1, R2 (da delta-020) **Decisões duráveis → ADRs:** ADR-0018 (supersede ADR-0015) **Riscos assumidos:** diagram-design sem pin nem teste de execução até a primeira adoção real (padrão graphify); design-sync indisponível em sessão sem login claude.ai — ambos cobertos pela degradação graciosa (RNF2).

---

# Plano — delta-020

Toda a mudança é texto de contrato (ADR, adapters, templates, SKILL) — sem código de gate, sem script novo. O TRUTH.md e o DEBT.md só mudam no archive (R7).

1. **ADR-0018** (`docs/adrs/ADR-0018-diagram-design-camada-apresentacao.md`): contexto (DT-014 antecipado por decisão do usuário; benchmark 2026-07-29), alternativas (manter Figma até o anúncio de preço · só render CLI · diagram-design + design-sync), decisão pela 3ª com renúncias, limitações registradas (bus factor 1, contrato não testado). Marcar ADR-0015 `Superseded by: ADR-0018` (única edição sancionada em ADR Accepted) e atualizar o índice `docs/adrs/README.md` (linha 0018 + status da 0015).
2. **`skills/spec-feature/references/adapters.md`**: linha da tabela de contrato (`apresentação a cliente` → diagram-design + design-sync, pontos sensíveis: 27 tipos/HTML+SVG/Playwright p/ export; login claude.ai/escopo design), seção do motor reescrita (invocação: conteúdo do `.mmd` como fonte; saída `docs/apresentacao/`; publicação via design-sync incremental por pedido; fallback render CLI + 1 aviso), política de versões (sai linha Figma MCP; entram diagram-design — sem pin até adoção real — e design-sync — n/a, ferramenta do harness; verificado em 2026-07-30).
3. **`skills/projeto-init/references/templates/doc-profile.yaml`**: comentários da categoria `apresentacao` (ferramenta `diagram-design` + `design-sync` opcional, ADR-0018).
4. **`skills/doc-entregavel/SKILL.md`**: bloco "Figma/FigJam (ADR-0015)" vira o papel da nova camada (ADR-0018) + caminho reprodutível de embutir no congelado (`diagram-design:export` → PNG/SVG → pipeline CLI).
5. **`skills/spec-feature/references/cycle.md`**: tabela ferramenta-por-categoria — "apresentação a cliente → diagram-design materializado do Mermaid fonte (ADR-0018, unidirecional)".
6. **`CHANGELOG.md`** (`[Não lançado]` → Mudado): a troca do motor, citando delta-020/ADR-0018.
7. **Verificação transversal:** `grep -ri "figma" skills/` → zero ocorrência viva (imutáveis fora: `_archive/`, ADRs Accepted, CHANGELOG lançado); gates `check_cycle.py specs/020-*` e `validate_integrity.py .` verdes.
8. **Archive (pós-merge):** consolidar MUDA R45/R46 no TRUTH.md com sufixo `(delta-020)`, `Estado: arquivada`, mover para `_archive/`, quitar DT-014 no DEBT.md, PR de archive e tag `v1.1.0` (feat → MINOR).

**TDD:** dispensado em todas as tasks — não há lógica executável nova; a verificação é gate + grep (tipo `tooling`, dispensa registrada aqui por task, conforme SKILL).
