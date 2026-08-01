<!-- resumo deltaspec · ≤15 linhas · única parte do plano lida pelo analyze e pelo humano -->
**Objetivo:** tornar o `DEBT.md` legível — bloco por item no lugar da tabela de 11 colunas — e transformar as referências (ticket, PR, delta, artefato) em links navegáveis. **Cobre:** R1, R2 (da delta-024) **Decisões duráveis → ADRs:** nenhuma — o formato do registro é escolha de apresentação, e as decisões de fundo (score derivado, projeção) continuam nas ADR-0020/0021 **Riscos assumidos:** o parser é reescrito e o selftest migra junto; links relativos dependem da convenção do GitHub para arquivo na raiz.

---

# Plano — delta-024

## Gramática do bloco

```markdown
### DT-001 · débito · aberto
**Título curto do sintoma**

Descrição em prosa, quantas linhas precisar.

- **Fila:** `P3·J3·Pr9`
- **Local:** [check_cycle.py](skills/spec-feature/scripts/check_cycle.py)
- **Gatilho:** template mudar de forma
- **Origem:** [PR #2](../../pull/2) · [delta-004](specs/_archive/004-notacao-delta/) · 2026-07-18
- **Ticket:** [#88](../../issues/88)
```

Item encerrado troca **Ticket** por **Encerrado:** `2026-07-20 · [#27](../../pull/27) — o que foi feito`.

## Ordem

1. **`debito.py`** — `parse_blocos()` no lugar de `parse_tabela()`: cabeçalho por regex ancorada (`^### (DT-\d+) · … · …$`), título pela primeira linha em negrito, campos por `^- \*\*Campo:\*\*` (âncora canônica, nunca busca solta). O resto do script (score, validação, churn, stale, exportar, diff) opera sobre o mesmo dicionário e **não muda**. Detecção de formato antigo: arquivo com `| DT-` e sem `### DT-` → aviso de conversão.
2. **Selftest migrado** — as fixtures viram blocos; a de regressão de prosa passa a ter a palavra "aberto" no meio da descrição de um item quitado.
3. **Script de conversão** (scratchpad, descartável): tabela → blocos para as 22 linhas, com os links montados a partir de `PR #N`, `#N`, `delta-NNN` e da chave `gh#N`.
4. **Legenda do cabeçalho** — um parágrafo por estado (incluindo `stale`, que é derivado e nunca escrito) e os três eixos da fila, sem repetir limiares.
5. **`references/debito.md`** e **`skills/handoff/SKILL.md`** — a gramática nova, sem duplicar a legenda.
6. **CHANGELOG** e **HANDOFF**.

## TDD

Obrigatório em T1 (parser novo, contrato fechado, já com selftest existente para migrar). Dispensado no resto: conversão de dados e texto normativo, verificados por gate e leitura.
