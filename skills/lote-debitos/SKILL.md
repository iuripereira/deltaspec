---
name: lote-debitos
description: Use when several small, independent DT-NNN debt items in debts/ativos/ are ready to fix in one pass instead of one at a time — the skill selects candidates, dispatches one subagent per DT in its own git worktree, runs each repo's own local gate, and calls `debito.py quitar` per item, always stopping before any git push or PR creation for explicit human approval. Triggers include "/deltaspec:lote-debitos", "corrigir vários débitos de uma vez", "lote de débitos", "resolver os DTs pequenos em paralelo". Not for a single debt (use the manual ritual or `debito.py quitar` directly), a `trilha`-marked debt (that has its own graph mechanism), or debts requiring a shared branch/merge (each DT here keeps its own branch/PR, by design).
---

# Lote de débitos independentes

## Visão geral

Fechar um `DT-NNN` de cada vez é seguro, mas não escala quando a fila tem dezenas de itens pequenos e sem relação entre si — é exatamente o caso comum da fila de dívida (a maioria dos itens é `P1·J1·Pr3` ou similar, sem dependência declarada). Esta skill mecaniza o **lote**: seleciona candidatos, isola cada um numa worktree própria, dispara um subagente por DT e para antes de qualquer ação de rede.

Cada `DT-NNN` já é um registro plano — sem campo de dependência na gramática (`debts/README.md`). O caso de débito **grande**, que precisa ser fatiado em tarefas com aresta de bloqueio, já tem mecanismo próprio: a **trilha planejada** (`skills/handoff/references/debito.md`, seção B — vira uma delta com `tasks.md` e `(dep: Tn)`, o que o framework já usa para `specs/NNN-*/`). Esta skill não duplica isso — item marcado `trilha` nunca entra no lote sozinho.

## Fronteira com `debito.py quitar`

`debito.py quitar` (`skills/handoff/scripts/debito.py`) é o subcomando que fecha **um** item — pré-condição de estado final já decidido, injeta `#### Como foi quitado`, `git mv` para `_archive/`. Esta skill não reimplementa esse ritual: cada subagente do lote chama `debito.py quitar` no fim do próprio DT, exatamente como faria uma sessão manual.

## Fronteira com o orquestrador de `delta-NNN` (ADR-0014)

Caso irmão, não o mesmo. O orquestrador de `delta-NNN` (roadmap: `orquestrador-implement-paralelo`) faz **convergência** — várias tasks de uma mesma delta, numa mesma branch, mergeadas de volta em ordem topológica. Aqui não há convergência nenhuma: cada `DT-NNN` já é seu próprio escopo, sua própria branch, seu próprio PR — o fim de cada subagente é um commit numa worktree isolada, ponto final.

## Passo 1 — Selecionar candidatos

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/lote-debitos/scripts/selecionar_candidatos.py <root>
# ou, para um subconjunto explícito (libera item `trilha`, nunca item já quitado/descartado):
python3 ${CLAUDE_PLUGIN_ROOT}/skills/lote-debitos/scripts/selecionar_candidatos.py <root> --ids=DT-001,DT-002
```

O script reaproveita o parser de `debito.py` (não reimplementa fila nem score) e exclui, por padrão:

- item fora de `aberto`/`aceito`/`vigente` — já quitado/descartado, nada a fazer;
- item marcado `trilha` na fila — mecanismo próprio, nunca entra sozinho.

**Filtro de workspace fica de fora de propósito.** Convenção específica de um cliente (uma chave própria no frontmatter, por exemplo) não é regra do framework — quem consome a skill filtra a lista antes de passar `--ids`, sem hardcode de convenção alheia aqui.

## Passo 2 — Confirmar com o humano antes de disparar

Apresente a lista de candidatos (IDs + título) e a concorrência que vai usar (passo 3) **antes** de abrir a primeira worktree. Lote é trabalho em paralelo sobre vários arquivos do registro — a mesma cautela de "parar e perguntar em ambiguidade" do framework vale aqui para a lista, não só para cada correção.

## Passo 3 — Levas por concorrência (RNF2)

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/lote-debitos/scripts/selecionar_candidatos.py <root> --concorrencia=3
```

Teto default **3** worktrees simultâneas (`CONCORRENCIA_DEFAULT`, constante nomeada no script) — concorrência maior satura I/O local em máquina fraca. A leva N+1 só começa depois que **todos** os subagentes da leva N terminaram (sucesso ou pendência) — nunca dispara acima do teto.

## Passo 4 — Um subagente por DT, cada um em worktree isolada

Para cada `DT-NNN` da leva corrente, use `superpowers:using-git-worktrees` para isolar o trabalho e dispare um subagente com este roteiro fechado:

1. Ler **só** o arquivo `debts/ativos/DEBT_DT-NNN-*.md` daquele DT — nada além dele, para não vazar contexto de outro item na mesma leva.
2. Corrigir a causa descrita no débito, no repositório-alvo daquela worktree.
3. Rodar o gate local do repositório-alvo (`check_cycle.py`/`validate_integrity.py` neste repo; o equivalente declarado no repo-alvo em outro caso — a skill não assume qual é, cada repositório é dono do próprio gate).
4. Editar o frontmatter do próprio DT para `estado: quitado` ou `estado: descartado` (decisão do subagente, é a única edição manual que sobra) e chamar:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/skills/handoff/scripts/debito.py quitar <root> DT-NNN --como "..." [--ticket-ref "..."]
   ```
5. Commitar (`git add` **nomeado**, nunca `-A`) na branch da worktree.
6. **Parar.** Nenhum `git push`, nenhuma criação de PR — RNF1 é absoluto, sem exceção por DT "trivial".

Se o subagente não conseguir corrigir a causa com segurança (ambiguidade real, teste que não fecha, gate que não passa), ele **não força** a quitação — deixa o DT como estava e registra a pendência para o relatório final (passo 5), nunca inventa uma correção capenga só para fechar o item.

**RNF1 é contrato de instrução, não portão de código.** O gate mecânico (impedir programaticamente que um subagente chame `git push`) exigiria falar com a API do GitHub ou interceptar o `Bash` — fora do escopo desta skill (mesma classe de "sem trava local" que o catálogo do `git-guard` já registra para regra de conteúdo de PR, R135). A garantia real é dupla: a instrução acima, mais o hook de agente `guarda-git.py` deste repositório, que já pede confirmação (`ask`) antes de qualquer `git push` — RNF1 nunca depende de um único mecanismo. Verificação: roteiro manual no `test-plan.md` desta delta, no precedente do CT3–CT6 da delta-083 (DT-086) — orquestração de agente real não é algo que um `pytest` observe de verdade.

## Passo 5 — Relatório de execução (R3)

Quando a última leva termina (todo subagente terminou ou parou), produza uma tabela — uma linha por DT processado:

| DT | Arquivo(s) tocado(s) | Gate local | Branch | Pendência |
|---|---|---|---|---|
| DT-089 | `skills/handoff/references/debito.md` | pass | `fix/dt-089-...` | — |
| DT-118 | — | — | — | ambiguidade real: RNF2 citado em 15 lugares, nenhum aponta a mesma regra — decisão de qual é a certa não é do subagente |

"Pendência" fica `—` quando o DT fechou; senão, a frase curta de por que não fechou (o subagente **não inventa** correção para preencher a célula). Nenhuma linha desta tabela implica push ou PR — isso continua sendo decisão sua, PR a PR, fora desta skill.

## Erros comuns

| Erro | Correto |
|---|---|
| Rodar o lote sem confirmar a lista com o humano primeiro | Passo 2 é obrigatório — a lista é decisão, não só a correção |
| Deixar um DT `trilha` entrar via seleção automática | `trilha` só entra por `--ids` explícito (decisão nomeada), nunca pela seleção default |
| Um subagente forçar `git push` "porque o DT era trivial" | RNF1 não tem exceção — pare e reporte pendente de aprovação |
| Um subagente ver dois DTs da mesma leva para resolver ambiguidade | Cada subagente lê só o próprio arquivo — vazamento de contexto entre DTs da mesma leva não é isolamento de verdade |
| Aumentar a concorrência para "ir mais rápido" numa máquina compartilhada | RNF2 é teto de I/O, não de paciência — suba com `--concorrencia` só quando souber que a máquina aguenta |
