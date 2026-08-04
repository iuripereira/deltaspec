# Analyze — delta-031 · 2026-08-04
| # | Severidade | Onde | Inconsistência | Ação sugerida |
|---|---|---|---|---|
| 1 | BAIXO | test-plan.md | dispensado no cabeçalho (perfil enxuto aprovado 2026-08-04) — C8 reporta informativo, conforme R38 | nenhuma |

Metade mecânica: `check_cycle.py specs/031-rodape-marca-dagua` — C1–C12 sem ALTO/CRÍTICO; `validate_integrity.py .` PASS (161 links). O veredito impresso ("LIBERADO COM RESSALVAS") decorre só do achado #1, informativo com a dispensa aprovada (R38).

Metade de juízo (checks 3 e 5 do roteiro):
- **Spec × plan:** o resumo cobre R1 e nada além; o desenho (fixed no pdf, VML no docx) executa o cenário sem ampliá-lo; a paginação `X/Y`, tentação natural de scope creep aqui, está explicitamente em Fora de escopo.
- **Divergência com o TRUTH:** o MUDA R21 repete os 3 cenários vigentes byte a byte e acrescenta 2 (flags e retrocompatibilidade); nenhum outro requisito tocado — R22/R23/R46 continuam donos do que já dizem.
- **Regras canônicas:** sem dependência nova (python-docx, pypandoc e Chrome já são o pipeline — RNF6 intacto); PT-BR; valores de apresentação (opacidade, corpo da fonte) vivem no bloco CSS/VML do próprio script, como os demais estilos do exportador — não são limiar de negócio.

**Veredito:** LIBERADO
