# delta-017 — jira-tickets
Estado: arquivada · Data: 2026-08-07 · Branch: feat/017-jira-tickets · Perfil: completo — contrato externo novo (dialeto acli/Jira) e reavaliação de pin de motor (ADR-0012) (aprovado: 2026-08-07)
Clarify: entrevistado (2026-08-07) — 7 decisões do usuário

> **Numeração (R5):** `017` é reserva explícita do usuário — número reservado desde o plano de upgrade de 2026-07-28 (Fase 4), consumido agora; as deltas 018–032 já existem arquivadas.

## Contexto (≤3 linhas)
Fase 4 do plano de upgrade (última fase aberta): tasks de delta projetadas para o Jira como vitrine de gestão, reusando o mecanismo de projeção do R52 (delta-023). Destravada em 2026-08-07: site `veredas.atlassian.net` com 6 projetos IMEX reais + sandbox `SBX`, e a primeira execução real do dialeto (DT-021) confirmou o risco — `create-bulk` rejeita description com `\n`; o `create` unitário aceita. A reavaliação do pin do max (gatilho da ADR-0012) foi cumprida no clarify: fork mantido ([ADR-0024](../../docs/adrs/ADR-0024-pin-do-max-reavaliado-fork-mantido.md)).

## Mudanças
### R1 — ADICIONA: tickets.md é a projeção canônica das tasks da delta
- DADO um projeto cujo `doc-profile.yaml` declara `motores: jira` com a chave do projeto (mesmo padrão do graphify: decisão registrada por projeto) QUANDO a fase tasks conclui ENTÃO `specs/NNN-nome/tickets.md` nasce no repo como projeção mecânica do `tasks.md` — 1 épico `[delta-NNN] nome` + 1 ticket por task, arestas `dep:` preservadas como links de bloqueio — **sem acessar a rede** (quem executa os comandos é a skill, nunca o script)
- DADO um projeto sem `motores: jira` no doc-profile QUANDO o ciclo roda ENTÃO a projeção se omite com no máximo 1 linha de aviso (RNF2) — o `tasks.md` segue valendo sozinho
- DADO o `tickets.md` gerado QUANDO a ida ao Jira roda ENTÃO a escada de automação é acli → Rovo MCP `/v1/mcp` → REST → só arquivo, degradando com aviso de 1 linha (RNF2)
- DADO um ticket criado QUANDO a chave devolvida chega (`PROJ-NNN`) ENTÃO ela é gravada no `tickets.md` — é ela, e não o título, que garante idempotência (mesma regra do R52)

### R2 — MUDA R52 (delta-023): dialeto de importação corrigido pelos achados da primeira execução real
- DADO o `DEBT.md` QUANDO `debito.py exportar` roda ENTÃO ele emite o JSON canônico e os dialetos de importação em arquivos, **sem acessar a rede** — quem executa os comandos é a skill, nunca o script; o dialeto que exige chave de projeto só é emitido quando ela é informada
- DADO o dialeto Jira emitido QUANDO ele é gerado ENTÃO é um `.sh` de `acli jira workitem create` **unitários** (padrão do `tickets-gh.sh`), preservando o corpo multi-linha dos itens — decisão da primeira execução real (DT-021, 2026-08-07: `create-bulk` rejeita `\n` na description; o lote bulk deixa de ser emitido) — e execução não interativa
- DADO um item projetado QUANDO o ticket é criado ENTÃO ele carrega a etiqueta determinística com o `DT-NNN` e o título prefixado pelo ID, e a chave devolvida (`gh#NNN`, `PROJ-NNN`) é gravada na coluna `Externo` — é ela, e não o título, que garante idempotência
- DADO o estado coletado da ferramenta QUANDO `debito.py diff` roda ENTÃO ele emite a tabela *DEBT.md diz × ferramenta diz × impacto × ação proposta* (formato do R27), cobrindo item sem ticket, ticket fechado com item ativo e ticket sem item correspondente
- DADO uma divergência detectada QUANDO ela vira mudança no `DEBT.md` ENTÃO a alteração é **proposta e só aplicada após aprovação humana** — a ferramenta externa nunca sobrescreve o arquivo, que permanece a fonte da verdade
- DADO a ferramenta ausente, sem autenticação ou sem projeto configurado QUANDO a projeção é invocada ENTÃO o `DEBT.md` segue valendo sozinho, com no máximo 1 linha de aviso (RNF2)

### R3 — ADICIONA: volta Jira→repo dos tickets de delta é diff aprovado, nunca sync
- DADO o estado dos tickets no Jira QUANDO a volta roda ENTÃO ela emite a tabela *tickets.md diz × Jira diz × impacto × ação proposta* (formato do R27) cobrindo **status e existência**: issue fechada com task aberta, task concluída com issue aberta, issue órfã/faltante, épico aberto com delta arquivada — assignee, comentários e descrição ficam fora (gestão edita no Jira sem gerar divergência)
- DADO uma divergência detectada QUANDO ela vira mudança no repo ENTÃO a alteração é **proposta e só aplicada após aprovação humana** — mesmo contrato do R52

## Fora de escopo
- Sync automático bidirecional (a volta é sempre diff + aprovação)
- Migração do pin do max para o upstream — reavaliada e renunciada nesta delta (ADR-0024)
- Troca da fonte do `status-pmo` para Jira (delta futura; hoje lê os arquivos canônicos)
- Backfill/projeção dos projetos IMEX reais (TP, DASH, EST, NC, PMO, SUP) — validação usa o sandbox `SBX`
- Espelho completo na volta (descrição/assignee/comentários)

## Dependências e riscos
- Dono do código (decisão do clarify): `tickets.py` novo em `skills/spec-feature/scripts/`; a emissão de dialeto sai do `debito.py` para módulo comum do plugin, importado pelos dois consumidores (não duplicar lógica)
- `acli` v1.3.22 autenticado por máquina (auth é ato do usuário; fluxo `--web` não funciona sem TTY)
- Rovo MCP (`/v1/mcp`) sem autenticação no harness atual — degrau 2 da escada nasce não exercitado (degradação coberta pelo R1)
- Achados completos da primeira execução real do dialeto: DT-021 no `DEBT.md`
- Mecânica do épico/parent no acli (flag `--parent`, ordem épico→filhas com captura da chave) — verificar no implement contra o `SBX`
