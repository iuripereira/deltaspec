<!-- resumo deltaspec · ≤15 linhas · única parte do plano lida pelo analyze e pelo humano -->
**Objetivo:** número medido citado em cenário do TRUTH deixa de apodrecer — passa a entrar como ilustração datada, e os 5 já defasados ou em risco (4 no R13, 1 no R31) ganham data. **Cobre:** R1, R2, R3 (da delta-030). **Decisões duráveis → ADRs:** nenhuma — a renúncia ao check que recalcula está registrada na spec (Fora de escopo) com gatilho de reabertura; não é decisão de arquitetura. **Riscos assumidos:** a regra vive de disciplina de escrita — a rede é o review de spec/archive, mesmo perímetro dos checks humanos do analyze (ADR-0006).

## Desenho

A norma entra como 3º cenário do R6 (MUDA), que é o requisito dono de "como se escreve uma delta". O guia do redator (`prosa.md`) ganha o espelho instrucional: mandamento 7 e uma linha no checklist de congelamento — apontando o R6 como dono, sem reproduzir a justificativa (regra de ouro).

Os números existentes são tratados nos próprios blocos MUDA da spec (R13: "26", "19", "10", "4"; R31: "10 skills"), consolidados mecanicamente no archive — não há edição direta do TRUTH fora da consolidação.

**TDD: não se aplica** — delta sem código (justificativa de dispensa registrada aqui, conforme CLAUDE.md). Verificação pelos gates e pelo diff do archive.

## Passos

1. `prosa.md`: mandamento 7 ("número medido entra datado") + item no checklist de revisão.
2. Registros: CHANGELOG `[Não lançado]` (Mudado), HANDOFF, progresso do DT-029 no DEBT.md (quita no archive, precedente das deltas 026–029).
3. Gate: `check_cycle.py specs/030-numero-datado` + `validate_integrity.py .`.
4. No archive: consolidar MUDA R6/R13/R31 e conferir os 5 números datados no diff do TRUTH.

## Verificação

- `check_cycle.py specs/030-numero-datado` sem ALTO/CRÍTICO; `validate_integrity.py .` PASS.
- Pós-archive: os 3 requisitos no TRUTH com sufixo `(delta-030)`; grep de conferência no TRUTH — toda ocorrência dos 5 números acompanhada de `medição de AAAA-MM-DD`; C4 sem perda.
