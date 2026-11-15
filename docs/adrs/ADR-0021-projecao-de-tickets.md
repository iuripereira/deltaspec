# ADR-0021: ferramenta de ticket é projeção do arquivo — ida mecânica, volta aprovada

- **Status:** Accepted (2026-08-01, delta-023)
- **Data:** 2026-08-01
- **Supersedes:** [ADR-0007](ADR-0007-registros-com-dono.md) (na parte das Issues; o file-first permanece)
- **Superseded by:** —

## Context

A ADR-0007 renunciou às Issues como registro e listou três alternativas, entre elas a **3 — "Ambos, Issues espelhando o arquivo"**, rejeitada porque "criaria um espelho permanente a manter". Ela também escreveu a própria condição de retorno: *"Reabre quando: o projeto ganhar colaboradores que trabalhem primariamente pela interface do GitHub — aí Issues-como-espelho-sancionado (3) entra na mesa, e esta ADR é substituída — não editada."*

Em 2026-08-01 o usuário confirmou que **GitHub Issues e Jira serão usados de fato** na gestão. A condição disparou.

O desenho não é inédito no framework: a delta-017 (reservada, Fase 4) já registrou o mesmo princípio para `tickets.md` — arquivo canônico no repo, Jira como projeção, ida mecânica pela escada de motores e volta sempre com diff e avaliação. O `status-pmo` (ADR-0019) já pratica a mesma separação: *"repo é a fonte da verdade; sistema externo é enriquecimento — a sincronização troca a coleta, nunca o render"*.

Alternativas consideradas:

1. **Manter a renúncia da ADR-0007.** Quem acompanha pela ferramenta não enxerga a dívida; o registro fica invisível para gestão.
2. **Mover o registro para a ferramenta** (Issues/Jira como fonte). Quebraria a atomicidade que a ADR-0007 defendeu — dívida nasce e morre no mesmo diff da mudança — e os IDs `DT-NNN` estáveis, que Issues não conseguem oferecer por compartilharem contador com PRs.
3. **Espelho sancionado unidirecional:** arquivo canônico, ferramenta como projeção, com chave externa persistida no arquivo e volta condicionada a aprovação humana.

## Decision

Adotamos a **3**, e esta ADR **substitui a ADR-0007 na parte das Issues** — o restante dela (o `DEBT.md` file-first, os `DT-NNN` estáveis, quitado que muda de status e nunca some) permanece integralmente válido e continua sendo a referência desses pontos.

O contrato tem quatro invariantes:

**O arquivo é a fonte.** Em divergência, o `DEBT.md` governa. Nenhuma etapa automática escreve nele a partir da ferramenta.

**A ida é mecânica, mas o framework não fala com a rede.** `debito.py exportar` emite o JSON canônico e os dialetos (bulk do Jira, linhas de criação do GitHub); quem executa é a skill, com os comandos à vista do usuário — o mesmo padrão do `projeto-infra`, que é roteiro em markdown sem script instalável. Isso mantém autenticação, limite de taxa e efeito colateral fora do código do framework.

**A volta é sempre avaliada.** O estado coletado da ferramenta entra em `debito.py diff`, que emite a tabela *DEBT.md diz × ferramenta diz × impacto × ação proposta* — a mesma forma do relatório de divergências da `descoberta` (R27). A IA propõe, o humano aprova, e só então o arquivo muda. **Nunca overwrite cego.**

**A idempotência é por chave, não por título.** A chave devolvida pela ferramenta é gravada na coluna `Externo`, e a etiqueta `dt:DT-NNN` marca o ticket. Buscar por título dependeria do índice de busca da ferramenta, que tem atraso de propagação e produz duplicata — falha documentada em projetos que sincronizam markdown com Issues.

Renunciamos à **1** porque a invisibilidade era o problema; à **2** pelas duas razões que a ADR-0007 já havia fixado e que continuam de pé (atomicidade e IDs estáveis).

Esta delta valida o caminho **GitHub** de ponta a ponta; o dialeto do Jira é emitido e verificado por formato, sem execução, por não haver projeto nem credencial. A delta-017 reusará este mesmo mecanismo para o `tickets.md` em vez de construir um segundo.

## Consequences

**Fica mais fácil:** quem acompanha pela ferramenta enxerga a dívida sem que o registro saia do git; a projeção é reprodutível e idempotente; o mecanismo nasce compartilhado com a Fase 4, evitando dois exportadores; e o framework continua funcionando inteiro sem rede, autenticação ou serviço externo.

**Fica mais difícil:** existe agora um espelho a manter — exatamente o custo que a ADR-0007 quis evitar, aceito conscientemente em troca da visibilidade, e mitigado por o `diff` transformar a divergência em achado explícito em vez de deixá-la silenciosa; a coluna `Externo` precisa ser preenchida a cada projeção, sob pena de duplicar ticket; e os *issue fields* do GitHub (score numérico, data) só valem em repositório de organização — em repositório pessoal os valores são descartados em silêncio, então o score viaja no corpo e em etiqueta de faixa.
