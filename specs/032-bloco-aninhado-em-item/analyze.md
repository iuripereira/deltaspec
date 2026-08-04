# Analyze — delta-032 · 2026-08-04
| # | Severidade | Onde | Inconsistência | Ação sugerida |
|---|---|---|---|---|
| 1 | BAIXO | test-plan.md | bugfix sem tasks — test-plan sob demanda (R39); o teste de regressão obrigatório cobre | nenhuma |

Metade mecânica: `check_cycle.py specs/032-bloco-aninhado-em-item` — C1–C12 sem ALTO/CRÍTICO (exit 0); `validate_integrity.py .` PASS.

Metade de juízo (checks 3 e 5 do roteiro):
- **Spec × plan:** o plan cobre exatamente a reprodução do spec; a 3ª causa (seam do `splitlines`) foi descoberta pelo passo fim a fim do próprio plan e incorporada à causa-raiz — não é scope creep, é a mesma correção no mesmo caminho.
- **Divergência com o TRUTH:** nenhuma — bugfix sem mudança de requisito (nenhum Rn descreve o `deepen_indents`); a seção Mudanças declara "nenhuma", e o archive move sem consolidar (R39).
- **Regras canônicas:** sem violação — stdlib apenas, PT-BR, causa corrigida em vez de contorno documentado (o contorno manual saiu da SKILL.md), função pura testável sem mock.

Teste de regressão (R4/delta-015, obrigatório): fixture no `--selftest` com os três casos — tabela colada, parágrafo aninhado, cerca intacta — vermelha antes do fix (`tabela colada sem linha em branco ou sem aprofundar`) e verde depois; três mutações (match só de bullets, sem linha em branco antes da tabela, `splitlines` de volta) quebram o selftest, a terceira via assert do `\n` final. Fim a fim conferido no HTML do pipeline real: tabela e parágrafo dentro do `<li>`, sem hífen literal, heading do §6 intacto.

**Veredito:** LIBERADO
