# Analyze — delta-033 · 2026-08-07
| # | Severidade | Onde | Inconsistência | Ação sugerida |
|---|---|---|---|---|

**Veredito:** LIBERADO

Registro do gate: metade mecânica (`check_cycle.py specs/033-parser-resiliente`) LIBERADO sem achados — C1 aceite, C2 cobertura (R1→T2/T4, R2→T1/T3; T5 mapeada), C8 test-plan (CT1–CT8, todo Rn com ≥1 caso), C9 grafo acíclico, C7 dentro do limiar.

Juízo (checks 3 e 5 do analyze.md):
- **Consistência spec × plan:** o resumo cobre R1/R2 e nada mais; sem scope creep — o módulo `itens.py` não é abstração especulativa, é o que o R2 exige literalmente (um parser, um dono).
- **Divergência com o TRUTH (check 4):** pega na escrita e corrigida antes deste registro — o primeiro rascunho do R1 dizia que `dep:` seria reconhecido "em qualquer linha do item", o que **contradiz o R40** (delta-016: a aresta só vale colada ao ID, para prosa não virar dependência). O cenário foi partido em dois: tolerância para os campos depois do travessão, âncora preservada para a aresta.
- **MUDA R12 íntegro:** os 8 cenários vigentes repetidos byte a byte + 2 novos — o archive substitui integralmente, cenário não repetido se perderia.
- **Regras canônicas:** PT-BR ✓ · zero dependência nova ✓ · âncora de início de linha reforçada (não afrouxada) ✓ · "não duplicar lógica" é o próprio objeto do R2 ✓ · template não muda de forma (fora de escopo declarado), então não há consumidor/fixture de template a sincronizar ✓.

Medições que fundamentam o desenho (varredura de 2026-08-07, antes de planejar):
- **92 headings `###` em 32 deltas arquivadas, 0 fora da forma canônica** — o detector do C1 nasce com falso positivo medido em zero, mesmo método que calibrou o C11 (delta-026).
- **40 `tasks.md`/`test-plan.md` arquivados: 0 item multi-linha e 0 conteúdo após a lista** — a tolerância não muda nenhum veredito existente, e o risco de sobre-captura é teórico (coberto pelo CT3 mesmo assim).
