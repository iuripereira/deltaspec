# Cronograma do portfólio — dono canônico

> Dono canônico do **cronograma**: D0, prazo contratual e etapas com status. As etapas são **espelho dos roadmaps dos PRDs** (duplicação documentada — mudou o roadmap, atualize aqui no mesmo change). O site de status (`status-pmo`) lê este arquivo; status `feita | em curso | prevista` é mantido à mão na revisão semanal.

**D0:** {{AAAA-MM-DD}} — {{âncora: início oficial; se mudar, ajustar somente aqui}}

## Marcos

| Marco | Data | Projeto | Entrega |
|---|---|---|---|
| D0 — início oficial | {{AAAA-MM-DD}} | todos | — |
| M1 — {{nome curto da entrega}} | {{AAAA-MM-DD}} | {{Nome do Projeto}} | {{o que o cliente recebe, numa frase}} |
| Entrega contratual | {{AAAA-MM-DD}} | {{Nome do Projeto}} | {{escopo contratado completo}} |
| Fim da estabilização | {{AAAA-MM-DD}} | {{Nome do Projeto}} | — |

> `Entrega` é opcional (tabela antiga, sem a coluna, segue válida — a página da entrega mostra "—"). Marco `M1`, `S2`… casa com a etapa de mesmo prefixo: entrega = etapa = épico.

## {{Nome do Projeto}}
**Dir:** {{diretorio-do-repo}} · **Prazo:** {{AAAA-MM-DD}} (D0 + {{N}}d — {{fonte do prazo}}) · **Fonte-repo:** {{repo/PRD.md:linha}} (§ Roadmap)

**Objetivos:**
- O1 — {{dor que o projeto resolve}} | Impacto: {{o que muda para a empresa}} | Evidência: {{como se sabe que foi atingido}}
- O2 — {{dor}} | Impacto: {{…}} | Evidência: {{…}}

<!-- de 1 a 4 objetivos (o self-check reprova mais de 4). `| Impacto:` e `| Evidência:` são opcionais:
     `- O1 — texto` segue válido (texto = dor; impacto e evidência = "—").
     Projeto operacional, regulatório ou de infraestrutura não inventa objetivo — troque a lista por:
     **Objetivos:** projeto operacional, sem objetivo de impacto
     O épico que atende declara `- Atende: O1` no arquivo de épicos. -->

| Etapa | Status |
|---|---|
| {{Etapa 1}} | em curso |
| {{Etapa 2}} | prevista |

### Riscos

| Risco | Nível | Prazo | Situação |
|---|---|---|---|
| {{o que pode dar errado e o efeito}} | {{Crítica · Alta · Média · Baixa}} | {{AAAA-MM-DD ou —}} | {{aberto · mitigado · materializado}} |

<!-- opcional; risco materializado vira impedimento. Nível e ordenação: onepage-layout.md § Criticidade. -->
