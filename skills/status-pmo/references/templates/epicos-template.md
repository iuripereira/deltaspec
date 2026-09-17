# Épicos e tarefas — {{Nome do Projeto}}

> Dono canônico do detalhamento épico→tarefa na camada de gestão, derivado do PRD ({{repo/PRD.md}} § Roadmap + § RFs). **Épico = etapa do cronograma** (`docs/cronograma.md`, mesma ordem e mesma quantidade — o self-check do gerador falha se divergir; o **status do épico vive no cronograma**, não aqui). `Dep` = o que precisa concluir antes. O sistema externo (Jira {{CHAVE}}) assume estes registros quando o backlog for povoado; até lá os IDs locais `En-Tn` são estáveis e citáveis.

## E1 — {{Primeira etapa do cronograma}}
**Dep:** —

| ID | Tarefa | Dep | Status |
|---|---|---|---|
| E1-T1 | {{tarefa — cite o RF quando existir: "RF-01 — …"}} | — | prevista |
| E1-T2 | {{tarefa}} | E1-T1 | prevista |

## E2 — {{Segunda etapa do cronograma}}
**Dep:** E1

{{nota livre opcional — dependência externa, condicional, risco de calendário}}

| ID | Tarefa | Dep | Status |
|---|---|---|---|
| E2-T1 | {{tarefa}} | — | prevista |

<!-- Regras:
     · status da tarefa ∈ feita | em curso | prevista (mesmo vocabulário do cronograma);
     · dep de tarefa referencia ID do MESMO arquivo (o self-check acusa dep inexistente);
     · épicos que podem correr em paralelo declaram o mesmo `Dep:` — o diagrama os mostra
       na mesma coluna, sem inventar sequência que o PRD não define;
     · não invente data por tarefa: se o PRD não dá, o gantt fica no nível projeto. -->
