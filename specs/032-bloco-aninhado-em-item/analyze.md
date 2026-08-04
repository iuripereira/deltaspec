# Analyze — delta-032 · 2026-08-04
| # | Severidade | Onde | Inconsistência | Ação sugerida |
|---|---|---|---|---|
| 1 | BAIXO | test-plan.md | bugfix sem tasks — test-plan sob demanda (R39); o teste de regressão obrigatório cobre | nenhuma |

Metade mecânica: `check_cycle.py specs/032-bloco-aninhado-em-item` — C1–C12 sem ALTO/CRÍTICO (exit 0); `validate_integrity.py .` PASS.

Metade de juízo (checks 3 e 5 do roteiro):
- **Spec × plan:** o plan cobre exatamente a reprodução do spec; a 3ª causa (seam do `splitlines`) foi descoberta pelo passo fim a fim do próprio plan e incorporada à causa-raiz — não é scope creep, é a mesma correção no mesmo caminho.
- **Divergência com o TRUTH:** nenhuma — bugfix sem mudança de requisito (nenhum Rn descreve o `deepen_indents`); a seção Mudanças declara "nenhuma", e o archive move sem consolidar (R39).
- **Regras canônicas:** sem violação — stdlib apenas, PT-BR, causa corrigida em vez de contorno documentado (o contorno manual saiu da SKILL.md), função pura testável sem mock.

Teste de regressão (R4/delta-015, obrigatório): fixture no `--selftest` com os quatro casos — tabela colada no item, item seguinte colado na tabela, parágrafo aninhado, cerca intacta — vermelha antes do fix (`tabela colada sem linha em branco ou sem aprofundar`) e verde depois; quatro mutações (match só de bullets, sem abertura de bloco, sem fechamento de bloco, `splitlines` de volta) quebram o selftest. Fim a fim refeito **com a própria fixture do selftest** através do pipeline real: tabela dentro do `<li>` do RN-02, RN-03 vivo com o parágrafo dentro do item, cerca renderizada como código com a indentação byte a byte, heading do §6 intacto, nenhum hífen literal.

**Veredito:** LIBERADO

## Apêndice — review fundido (eixos Spec + Qualidade num único subagente)

O review **REPROVOU** a primeira versão, com razão: a correção da causa 2 era assimétrica — abria bloco antes da tabela e não fechava depois, então item `- RN-` colado após a tabela era **engolido como célula e sumia da lista**, exatamente a forma do PRD que originou o DT-009 (RNs 007/008 consecutivas); a fixture do selftest tinha a forma e nenhum assert olhava o render. Tratado: seam de fechamento no `deepen_indents` (linha em branco ao sair de tabela aninhada para linha não-vazia não-tabela), assert novo (`item seguinte colado na tabela seria engolido como célula`), mutação D cobrindo o fechamento, fim a fim refeito com a fixture real e este relatório corrigido — o achado BAIXO do review sobre a frase anterior do fim a fim ("conferido" numa forma mais benigna que a fixture) procede e está registrado. Ajuste opcional aplicado: o comentário do `split("\n")` agora atribui a cada parte o seu papel (split = `\n` final; seam do heading = `transform()`). Registrado sem ação: o idioma `.rstrip("\n") + "\n\n"` aparece 3× — helper só se crescer.

Review: convergentes tratados — 2026-08-04
