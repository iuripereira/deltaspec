# ADR-0006: Perímetro dos gates determinísticos — o papel, não o implement/review

- **Status:** Accepted
- **Data:** 2026-07-18
- **Supersedes:** —
- **Superseded by:** —

## Context

> Registrada retroativamente em 2026-07-19, no backfill de ADRs da varredura de registros.
> A decisão vige desde o PR #2 ("fora de escopo") e foi refinada na delta-002 ("determinismo
> sobre riqueza"); o recorte humano dos checks 3 e 5 está no `specs/TRUTH.md` ("Não implementado").

"Gates determinísticos" é a marca do framework — mas determinismo não é gratuito: cada check
mecânico só cobre o que regex e diff alcançam. Três fronteiras precisavam de decisão explícita:

- **Fases:** o dano real acontece no `implement` e no `review` — e são as fases sem gate.
- **Checks do analyze:** scope creep spec×plan (check 3) e violação de regra canônica (check 5)
  exigem juízo, não pattern matching.
- **C6 (pendência roteada):** verificar que a pendência saiu da delta arquivada é mecânico;
  verificar que ela **chegou** ao destino exigiria matching de texto contra outro arquivo — frágil
  a qualquer renomeação ou reescrita.

Alternativas consideradas:

1. **Gate mecânico também no implement/review** (ex.: heurísticas de cobertura, lint semântico).
2. **Automatizar os checks 3 e 5** com heurísticas de similaridade.
3. **C6 com matching de texto** no arquivo de destino da pendência.
4. **Perímetro restrito ao papel:** gates cobrem spec/plan/tasks/archive; o resto fica declarado
   como humano.

## Decision

Adotamos a alternativa 4: **o determinismo cobre o perímetro mais barato de errar — o papel.**
Spec, plan, tasks e archive têm gate (`check_cycle.py` C1–C6); `implement` e `review` ficam com o
modelo, a disciplina delegada (TDD do superpowers, ponytail) e o review humano. Os checks 3 e 5 do
analyze permanecem humanos, e a saída do script **declara-se parcial** nomeando o que não rodou. O
C6 acusa a pendência na origem (spec arquivado) e não valida o destino — determinismo sobre
riqueza.

Renunciamos a automatizar juízo (1, 2) porque heurística vestida de gate produz **falso negativo
confiante**: um "LIBERADO" mecânico em cima de análise que exige entendimento vale menos que um
"não rodei" honesto. Renunciamos ao matching de texto (3) porque acopla o gate à redação de outro
arquivo — qualquer reescrita legítima viraria falha espúria.

## Consequences

**Fica mais fácil:** nenhum gate finge cobertura que não tem; os checks são estáveis (não quebram
com reescrita de prosa); a saída parcial explícita diz ao usuário exatamente o que ainda é
diligência dele.

**Fica mais difícil:** a fase de maior dano não tem rede mecânica — um implement ruim passa se o
review humano falhar. É limite reconhecido do desenho, não débito a corrigir: está registrado no
`TRUTH.md` ("Não implementado", por design) e o esforço de determinismo cobriu onde errar é barato
de detectar.

**Reabre quando:** surgir um check de implement que seja genuinamente mecânico (ex.: task declarada
sem diff correspondente), ou o C6 ganhar um destino com formato estável o bastante para verificação
por ID em vez de texto. Extensão entra por delta com MUDA no R12 — nunca rebaixando o padrão de
"mecânico de verdade".
