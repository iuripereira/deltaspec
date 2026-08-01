# ADR-0007: Registros com dono — DEBT.md file-first; Issues não são registro

- **Status:** Accepted
- **Data:** 2026-07-19
- **Supersedes:** —
- **Superseded by:** [ADR-0021](ADR-0021-projecao-de-tickets.md) (2026-08-01, delta-023) — **apenas na parte das Issues**: a alternativa 3 (espelho sancionado) foi adotada quando a cláusula "Reabre quando" abaixo disparou. O `DEBT.md` file-first, os IDs `DT-NNN` e a regra "quitado muda de status, nunca some" seguem vigentes e continuam sendo referenciados por esta ADR.

## Context

A varredura de registros do repo (2026-07-19, histórico #1–#18 + deltas 001–006) mostrou o
STATE.md acumulando quatro naturezas — inventário as-built, backlog decisório, débito+pegadinhas+
lições e uma tabela de histórico duplicando o CHANGELOG — sem IDs, sem datas, sem status. Efeito:
a evolução do framework (débito aberto vs. quitado) ficou invisível, e cada leitura exigia
adivinhar o que era acionável, o que era lição e o que era limite por design.

O repo já tinha três camadas com dono (CHANGELOG para o que mudou, `specs/TRUTH.md` para o que
vige, ADRs para tradeoffs); faltava a quarta: **onde vive o débito**. Candidatos:

1. **GitHub Issues** (habilitadas, zeradas): workflow pronto, trend aberto/fechado de graça.
2. **`DEBT.md` versionado** na raiz, com IDs `DT-NNN` — mesma família dos `Rn`/`ADR-NNNN`.
3. **Ambos**, Issues espelhando o arquivo (ou vice-versa).

## Decision

Adotamos a alternativa 2: **`DEBT.md` na raiz é o dono canônico de débito, pendências e guardas**,
uma linha `DT-NNN` por item (natureza, origem, data, gatilho de correção, status), mais a seção
"Lições" para post-mortems datados. Item quitado **muda de status, nunca some** — a trajetória
aberto→quitado é o que torna a evolução visível. O STATE.md vira **diário de bordo** (andamento
contínuo, janela rolante) e para de acumular papéis.

Renunciamos às Issues como registro (1) por quatro razões: **atomicidade** — R16 e o CLAUDE.md
exigem registro *no mesmo commit* da mudança, e issue não entra em commit; **offline/file-first**
— os gates (`check_cycle.py` C6) leem arquivos, não a API; **numeração** — Issues compartilham o
contador com PRs (o "DT-5" nasceria como #23), quebrando IDs estáveis e citáveis; **regra de
ouro** — a coexistência sincronizada (3) criaria um espelho permanente a manter, exatamente a
duplicação que o `deps.toml` existe para conter. Issue *pode* referenciar um DT para discussão —
referência, nunca fonte.

## Consequences

**Fica mais fácil:** débito nasce e morre no mesmo diff da mudança que o cria/quita; o gate C6
roteia pendência de delta arquivada para um destino versionado; `git log DEBT.md` conta a história
do débito; a tendência (abertos vs. quitados) é visível num `grep -c`.

**Fica mais difícil:** sem notificação/assignee/labels das Issues; discussão longa sobre um DT não
tem lugar nativo (abre-se uma issue referenciando o DT, que continua sendo a fonte); o arquivo
exige a disciplina de status que a ferramenta não força.

**Reabre quando:** o projeto ganhar colaboradores que trabalhem primariamente pela interface do
GitHub — aí Issues-como-espelho-sancionado (3) entra na mesa via `deps.toml`, e esta ADR é
substituída — não editada.
