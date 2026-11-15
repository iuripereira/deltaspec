# ADR-0033: A conciliação de insumo novo é uma skill própria do ciclo, não um comando de workspace

- **Status:** Accepted
- **Data:** 2026-08-12
- **Supersedes:** —
- **Superseded by:** —

## Context

Depois que a `descoberta` (ADR-0011) produz o dossiê inicial e o PRD-proposta existe, o projeto entra num regime recorrente: cada insumo novo do cliente (reunião gravada, mensagem de Teams, planilha, respostas de formulário) precisa ser minerado, conciliado com os registros vivos (`questions.md`, divergências, GLOSSARY/DATA_DICTIONARY), transformado em atualização de requisitos e propagado aos entregáveis. No portfólio do caso de referência esse ciclo rodou **cinco vezes** entre 27/07 e 12/08/2026, sempre por prompt digitado a cada sessão — e a quinta rodada (registro Teams da gestora, 12/08) consolidou duas peças que nenhum registro do framework cobria: um **gate de decisões com o usuário antes de tocar o PRD** e a mecânica de **bump de versão com entregável congelado por versão** (baseline anterior intacta).

Existia uma automação parcial: o comando `/pmo-insumos`, no diretório de comandos de um workspace de portfólio — pasta **fora de git** (pendência registrada no handoff do `_pmo` de 12/08), com fontes e guardas específicas daquele portfólio misturadas ao processo genérico, e sem o gate de decisões nem a mecânica de versão/entregável.

## Decision

Criamos a skill **`rodada-insumos`** no plugin (delta-054), generalizando o ciclo: inventário → mineração (compondo a `descoberta`, nunca duplicando) → conciliação em 4 trilhos → gate de decisões (perguntas numeradas com recomendação; `grilling` do `mattpocock-skills` quando instalado, condução nativa com aviso quando não) → atualização do produto com bump de versão e entregável congelado por versão → fechamento com **PR aberto** (merge, promoção de baseline e publicação ficam com o humano) → digest único. O comando `/pmo-insumos` daquele workspace vira **wrapper fino**: aponta a skill e declara só o que é específico do projeto (fontes de insumo, guardas de publicação/Jira/D1, scripts pós-merge).

Renúncias registradas:

- **Manter o processo como comando de workspace** — rejeitado: fora de git (sem versionamento, sem CI, sem changelog), invisível a outros projetos do ciclo, e o processo genérico ficava acoplado às fontes daquele workspace. Reincidiria o padrão que a ADR-0011 corrigiu para a descoberta inicial.
- **Ampliar a skill `descoberta` com as fases da rodada** — rejeitado: a descoberta é a fase *pré-specify* de mineração pontual; a rodada é o regime *recorrente pós-PRD-proposta*, com gate de decisões, versão e git flow que não pertencem à mineração. Fundir os dois tornaria a descoberta obrigatoriamente interativa e inflaria seu SKILL.md — composição preserva as duas coesas.
- **Automatizar sem gate humano (rodada 100% autônoma)** — rejeitado pelo usuário na decisão de escopo (2026-08-12): edição de PRD sem confirmação repete o erro-fundador daquele projeto (PRD gerado por IA sem validação, contradito no kickoff). O gate roda em **toda** rodada e a autonomia para no PR aberto.

## Consequences

- O ciclo ganha um regime recorrente nomeado: `descoberta` abre o projeto; `rodada-insumos` o mantém sincronizado com o cliente a cada insumo — mesma régua de confiança, mesmos registros.
- O gate de decisões torna explícito o ponto onde a inferência da IA vira requisito só com aval humano — a regra "inferência nunca vira fato" ganha um mecanismo de processo, não só de marcação.
- Projetos fora daquele portfólio usam a skill sem herdar fontes/guardas alheias; especificidades vivem no wrapper de cada workspace.
- Custo aceito: rodada sem canal humano para no gate por design — sessões headless não completam o ciclo (coerente com a renúncia à autonomia total).
