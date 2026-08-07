# delta-017 — jira-tickets
Estado: proposta · Data: 2026-08-07 · Branch: feat/017-jira-tickets · Perfil: completo — contrato externo novo (dialeto acli/Jira) e reavaliação de pin de motor (ADR-0012) ({{aprovado: pendente}})
Clarify: {{pendente — entrevista do grill-with-docs a conduzir}}

> **Numeração (R5):** `017` é reserva explícita do usuário — número reservado desde o plano de upgrade de 2026-07-28 (Fase 4), consumido agora; as deltas 018–032 já existem arquivadas.

## Contexto (≤3 linhas)
Fase 4 do plano de upgrade (última fase aberta): tickets como projeção para gestão humana, reusando o mecanismo do R52 (delta-023). Destravada em 2026-08-07: o site `veredas.atlassian.net` tem 6 projetos IMEX reais + sandbox `SBX`, e a primeira execução real do dialeto (DT-021) confirmou o risco — `create-bulk` rejeita description com `\n`; o `create` unitário aceita. A ADR-0012 amarra a esta delta a reavaliação do fork do max (`to-tickets`/`wayfinder` ganham consumidor aqui).

## Mudanças
### R1 — ADICIONA: tickets.md é a projeção canônica das tasks da delta
- DADO uma delta com `tasks.md` QUANDO a projeção de tickets roda ENTÃO `specs/NNN-nome/tickets.md` nasce no repo como projeção mecânica (task → ticket, arestas `dep:` preservadas como bloqueio), sem acessar a rede — o repo permanece a fonte, o Jira é vitrine
- DADO o `tickets.md` gerado QUANDO a ida ao Jira roda ENTÃO a escada de automação é: acli (links + criação) → Rovo MCP `/v1/mcp` → REST → só arquivo, degradando com aviso de 1 linha (RNF2)

### R2 — MUDA R52: dialeto de importação corrigido pelos achados da primeira execução real
<!-- versão integral do R52 a consolidar; a forma do dialeto corrigido é decisão do clarify (candidatos do DT-021: .sh de `create` unitários preservando corpo multi-linha, ou bulk com description achatada) -->
- DADO o `DEBT.md` QUANDO `debito.py exportar` roda ENTÃO ele emite o JSON canônico e os dialetos de importação em arquivos, **sem acessar a rede** — quem executa os comandos é a skill, nunca o script; o dialeto que exige chave de projeto só é emitido quando ela é informada
- DADO o dialeto Jira emitido QUANDO ele é executado ENTÃO o corpo multi-linha dos itens chega íntegro ao ticket e a execução é não interativa (`--yes`) — achados da primeira execução real (DT-021, 2026-08-07): `create-bulk` rejeita `\n` na description; `create` unitário aceita
- DADO um item projetado QUANDO o ticket é criado ENTÃO ele carrega a etiqueta determinística com o `DT-NNN` e o título prefixado pelo ID, e a chave devolvida (`gh#NNN`, `PROJ-NNN`) é gravada na coluna `Externo` — é ela, e não o título, que garante idempotência
- DADO o estado coletado da ferramenta QUANDO `debito.py diff` roda ENTÃO ele emite a tabela *DEBT.md diz × ferramenta diz × impacto × ação proposta* (formato do R27), cobrindo item sem ticket, ticket fechado com item ativo e ticket sem item correspondente
- DADO uma divergência detectada QUANDO ela vira mudança no `DEBT.md` ENTÃO a alteração é **proposta e só aplicada após aprovação humana** — a ferramenta externa nunca sobrescreve o arquivo, que permanece a fonte da verdade
- DADO a ferramenta ausente, sem autenticação ou sem projeto configurado QUANDO a projeção é invocada ENTÃO o `DEBT.md` segue valendo sozinho, com no máximo 1 linha de aviso (RNF2)

### R3 — ADICIONA: volta Jira→repo dos tickets de delta é diff aprovado, nunca sync
- DADO o estado dos tickets no Jira QUANDO a volta roda ENTÃO ela emite diff (*tickets.md diz × Jira diz*) com ação proposta, e mudança no repo só se aplica após aprovação humana — mesmo contrato do R52 para o DEBT.md

## Fora de escopo
- Sync automático bidirecional (a volta é sempre diff + aprovação)
- Troca da fonte do `status-pmo` para Jira (delta futura; hoje lê os arquivos canônicos)
- Backfill/projeção dos projetos IMEX reais (TP, DASH, EST, NC, PMO, SUP) — validação usa o sandbox `SBX`

## Dependências e riscos
- `acli` v1.3.22 autenticado por máquina (auth é ato do usuário; fluxo `--web` não funciona sem TTY)
- Rovo MCP (`/v1/mcp`) sem autenticação no harness atual — degrau 2 da escada nasce não exercitado
- ADR-0012: decisão do pin do max (migrar para `to-tickets`/`grilling` upstream × manter fork 0.8.0) é saída obrigatória do clarify desta delta
- Achados completos da primeira execução real do dialeto: DT-021 no `DEBT.md`
