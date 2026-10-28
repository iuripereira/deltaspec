# Replan — {{topico}}
Data: {{AAAA-MM-DD}} · {{Substitui: plano anterior (caminho) · ou, para delta: Replaneja: specs/NNN-nome}} · Pivô: {{data do plano anterior · commit da spec}} · Objetivo: {{1 linha}}

## Inventário de fontes
<!-- linhas fixas = mapa de alvos; preencha só "Encontrado". Abre apenas o que está aqui; evidência é caminho + PR/hash -->
| Fonte | Filtro | Encontrado |
|---|---|---|
| Fontes nomeadas pelo usuário | — | {{lista · —}} |
| Arquivos que o plano cita | mudaram desde o pivô (`git log --since`) | {{lista · nada novo}} |
| `docs/discovery/*.md` (dossiês, divergências, grilling) | data no nome ≥ pivô | {{…}} |
| `docs/discovery/questions.md` | blocos `> Revisão de DD/MM` ≥ pivô | {{IDs tocados}} |
| `.claude/handoffs/` | data no nome ≥ pivô | {{arquivos}} |
| `debts/ativos` · `debts/_archive` | criados após o pivô (`git log --diff-filter=A <pivô>..HEAD -- debts/`) | {{DT-NNN}} |
| Lições (`debts/licoes/` ou `debts/LICOES.md`) | novas desde o pivô | {{L-NNN · —}} |
| `specs/` (novas, arquivadas, TRUTH) | mudaram desde o pivô | {{…}} |
| PRD — histórico de revisões | linhas ≥ pivô | {{versão}} |
| Evidência (código, gerado, saída, teste) | resto do `git log` | {{n arquivos · #PRs}} |

## Fatos novos
<!-- só o que muda algo; fato sem fonte não entra; escolha aberta = bloqueia→Qn, nunca decisão da skill -->
| # | Fato | Fonte | Efeito | Item |
|---|---|---|---|---|
| F1 | {{afirmação}} | {{arquivo:linha · #PR · DT-NNN}} | {{muda · remove · adiciona · feito · bloqueia→Qn}} | {{T<N> · D<N> · Q<N>}} |

## Decisões
- Herdadas: {{Q1..Qn}} — [{{plano anterior}}]({{caminho}}#{{âncora}}) (não reabrir)
- Novas (gate {{data}}): **Q{{n}}** — {{1 linha}} — fonte: F{{n}} {{· "nenhuma" quando o gate não abriu}}
- Pendentes: **Q{{n}}** — {{pergunta}} · ➡️ {{recomendação}} · bloqueia: T{{n}}

## Tarefas
<!-- IDs do plano anterior, nunca renumerados; nova = série continuada. Uma linha por tarefa; cabe em um turno ou vira delta -->
- [x] {{T<N>}} — {{ação}} · evidência: {{#PR · hash · comando OK}}
- [ ] {{T<N>}} (dep: {{T<M>}}) — {{ação}} · arquivos: {{caminhos}} · verificação: {{comando ou observável}} · fonte: {{F<n> · herdada}}
- [ ] {{T<N>}} — {{ação}} · arquivos: {{…}} · verificação: {{…}} · bloqueada por: Q{{n}}
- ~~{{T<N>}}~~ — removida: {{motivo}} (F{{n}})

## Auditoria
<!-- comandos que provam o plano inteiro; herde do anterior o que ainda vale; nunca inventar -->
1. `{{comando}}` → {{resultado esperado}}

Próximo passo: {{T<N>}} — {{como + comando}}
