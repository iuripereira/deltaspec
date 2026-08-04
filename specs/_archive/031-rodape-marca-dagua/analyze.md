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

## Apêndice — review fundido (perfil enxuto: eixos Spec + Qualidade num único subagente)

Achados tratados: **M1** a marca d'água no `juridico-nda` ampliava a regra sem respaldo do dono (`juridico.md` só a exigia na Versão B) — parado e perguntado, decisão do usuário (2026-08-04): **o NDA também leva marca**, regra ampliada no dono com o texto `CONFIDENCIAL` nomeado lá; o clarify da delta virou `entrevistado`; **M2** o CSS de confidencialidade entrava incondicionalmente, contrariando a verificação declarada da T2 — movido para `CSS_CONF` condicional: sem flag, o HTML volta a ser idêntico ao vigente; **B1** textos das flags agora escapados (`html.escape` no pdf, `saxutils.escape` no VML). Registrados sem ação: **B2** o assert da marca no pdf é `any()` e não "toda página" — a marca sai em toda página (raster conferido pelo revisor), mas na capa o extrator intercala os glifos rotacionados com o texto; fraqueza declarada na spec; **B3** vermelho e verde chegam no mesmo commit — o vermelho está registrado na mensagem, processo e não produto. Mutações reconferidas após o refactor: pdf sem injeção e docx sem VML seguem quebrando o selftest.

Sem achado: MUDA R21 íntegro byte a byte (conferência por script do revisor); retrocompatibilidade sem flags comprovada por diff do produto (texto extraído idêntico, mesmas páginas); VML canônico mantido inteiro — cortar `<v:handles>`/`<o:lock>` não paga o risco de mexer em artefato vendored do Word.

Review: convergentes tratados — 2026-08-04
