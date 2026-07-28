# Analyze — delta-015 · 2026-07-28
| # | Severidade | Onde | Inconsistência | Ação sugerida |
|---|---|---|---|---|
| 1 | BAIXO | specs/015-fluxo | 506 linhas adicionadas (limiar 500) — C7 | abrir primeiro o PR só dos artefatos — split condicional (cycle.md) |

Metade mecânica: `check_cycle.py` C1–C7, único achado acima. Metade humana (checks 3 e 5 do roteiro): resumo do plan cobre R1–R6 sem item fora da spec (README/doc-profile/CHANGELOG amparados por R5/R2/infra); blocos MUDA R12 e MUDA R35 repetem integralmente os cenários vigentes (conferido contra o TRUTH.md — nada se perde no archive); nenhuma violação de regra canônica — o split desta delta é a aplicação do limiar de PR, stdlib pura mantida no gate, tag segue fonte da versão.

Clarify (grill-me) encerrou com aggregate 0.06 (threshold 0.2): Goals 0.0 · Acceptance 0.1 · Boundaries 0.0 · Alternatives 0.1 (renúncias no ADR-0013) · Assumptions 0.1.

**Decisão sobre a ressalva:** split R17 aceito — artefatos seguem em PR próprio (`docs/015-fluxo`); implementação continua em `feat/015-fluxo`.

**Veredito:** LIBERADO COM RESSALVAS

## Review (2 eixos paralelos, R35) · 2026-07-28

Convergente (tratado): comentário do `delta-spec.md` com o literal da dispensa enganava o `campo()` — falso negativo do C8 reproduzido pelo eixo Spec (ALTO) e apontado como texto com 3 donos pelo eixo Qualidade. Fix: `cabecalho()` remove comentários HTML antes do parse (+ fixture de regressão) e o comentário do template virou referência de 1 linha ao cycle.md.

Eixo Spec: R1–R4/R6 ATENDIDOS, R5 PARCIAL→corrigido (acima); tratados também o flowchart do README sem `test-plan` (MÉDIO) e o placeholder de justificativa do Perfil (BAIXO). Eixo Qualidade (delete-list): tratados os runners duplicados do selftest (fundidos em `rodar()` com arquivos opcionais), o parse de `cobre:` duplicado entre C2/C8 (helper `cobre_alvos`) e a célula da tabela de perfil que reenunciava a regra do adapters. Recusados com justificativa: helper `secao()` (ganho marginal), cache do cabeçalho entre `checar()` e C8 (C8 continua chamável isolado) e o corte do campo `tipo:` do test-plan (a spec R3 o exige — spec é soberana).
