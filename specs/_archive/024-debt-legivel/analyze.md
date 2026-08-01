# Analyze — delta-024 · 2026-08-01
| # | Severidade | Onde | Inconsistência | Ação sugerida |
|---|---|---|---|---|

Checks mecânicos C1–C10: limpos, sem achado.

**Check 3 (spec × plan).** O resumo do plan cobre R1 e R2; nada no plano fora da spec. A ausência de ADR é declarada e correta: o formato do registro é apresentação, e as decisões de fundo (score derivado, projeção) continuam nas ADR-0020/0021, que não mudam.

**Check 4 (divergência com o TRUTH, juízo).** Os blocos MUDA repetem os cenários vigentes de R18 e R51 que continuam válidos (numeração global, quitado que não some, score derivado e nunca gravado, parsing por âncora, ordem da fila) e substituem apenas os que descreviam a tabela. Nada de válido se perde na substituição integral do archive.

**Check 5 (regras canônicas).** CHANGELOG como task explícita (T7); nenhuma sobrescrita; PT-BR; stdlib pura; conversão feita por script descartável no scratchpad, não à mão. Diff dentro do limiar de PR.

## Achados da execução (registrados aqui porque mudaram o desenho)

1. **O `stale` mudou de semântica — para melhor.** Com o ID vivendo só no cabeçalho do bloco, `git log -G "DT-NNN"` passa a casar exatamente mudanças de estado e natureza. Editar a prosa não reinicia mais o relógio, o que é mais fiel ao que a marca quer dizer: *houve decisão?*. O selftest cobre os dois lados (prosa não zera; mudança de estado zera).
2. **Conversor produzia link aninhado e link semanticamente errado.** `PR #2` virava `[PR [#2](…)](…)` porque duas substituições em sequência casavam o mesmo número, e `delta-001` do repo **imex**, citado na quitação do DT-004, virava link para a delta-001 *deste* repositório. Corrigido: uma passada só de substituição, e link de delta apenas no campo `Origem`, onde a referência é local por construção.
3. **Crase quebrava a fila.** A conversão escreveu `` `P3·J3·Pr9` `` e o `parse_fila` recusou. O parser passou a tolerar a crase — formatar bonito não pode invalidar o registro.

**Veredito:** LIBERADO
