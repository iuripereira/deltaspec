---
name: replan-doc
description: Use when a plan already in execution — a dated file in .claude/plans/, a plan Claude saved outside the repo, a pasted prompt or loose notes, or a delta's plan.md/tasks.md — must be re-planned against what the repo learned after it: a rodada-insumos dossier, answered questions.md items, grilling output, handoffs, new or settled debts, lessons, delta specs, point corrections from the user. Triggers include "/deltaspec:replan-doc", "replanejar", "replanejamento", "o plano ficou velho", "atualizar o plano com o que mudou", "o que muda no plano depois disso". Not for writing a plan from scratch (superpowers:writing-plans), for reconciling a client input into the PRD (rodada-insumos) or for editing a delta's spec/plan/tasks (spec-feature).
---

# replan-doc

## Overview

Replaneja um plano **já em execução** contra o que o repo aprendeu depois dele. Entrada: o plano vigente e sua data (o **pivô**). Saída: um plano **novo, datado**, com tarefas checáveis; o anterior fica intacto, com um banner. Três regras sustentam tudo: a coleta é dirigida pelo **mapa de alvos** do template — os alvos são conhecidos, ninguém lê o repo para "ter contexto"; **fato sem fonte não entra** e `[x]` exige evidência no git; **decisão é do usuário** — congelada não reabre sem fato contrário, nova não nasce sem gate. Renúncias em [ADR-0044](../../docs/adrs/ADR-0044-replanejamento-como-documento-novo.md). Vocabulário: *replanejar* — "projeção" no deltaspec é repo → ticket.

Fronteiras: a `rodada-insumos` concilia insumo em PRD (aqui o PRD é só fonte); a `spec-feature` é dona de `specs/NNN-*/` — aqui, editar a delta vira **tarefa do replan**, que ela aplica na PR seguinte: o replan é a proposta com fonte, a delta é o resultado depois do gate; a `handoff` grava a sessão (é **fonte**, não saída, e é ela que aponta o `HANDOFF.md` para o plano novo); `superpowers:writing-plans` escreve do zero.

## Processo (6 fases)

1. **Ancorar.** Plano = argumento; senão o mais novo em `.claude/plans/` sem banner "Substituído"; ambíguo → **uma** pergunta (qual, desde quando). Plano fora do repo (`~/.claude/plans/`, prompt, anotações) → gravar antes em `<repo>/.claude/plans/AAAA-MM-DD-<topico>.md`; o caminho efêmero nunca é citado. **Pivô = data no nome do arquivo**; delta: o commit que criou a `spec.md` (`git log --diff-filter=A --format=%h -- specs/NNN-*/spec.md`). Ler o plano inteiro — numa delta, "plano" é `spec.md` + cabeçalho-resumo do `plan.md` + `tasks.md`; o corpo de código do `plan.md` não é plano. Anotar os IDs de tarefa e as decisões marcadas "não reabrir".
2. **Mapa de alvos.** `git log --since=<pivô> --name-only --pretty=format: | sort -u` (delta: `git log <commit da spec>..HEAD --name-only …`), **uma vez**. Cada caminho cai num de dois baldes: **fonte de fato** — casa com uma linha do inventário do template → abre; **evidência** — código, gerado, saída, teste → só caminho + PR/hash, para a fase 3. Arquivo citado pelo plano só entra se mudou desde o pivô. Fonte nomeada pelo usuário entra primeiro. "Abrir" tem profundidade: dossiê = seções de decisão, encaminhamento e débitos tocados; handoff = Entrego/Não entrego, decisões congeladas, próximos passos, pendências roteadas; o resto é contexto e fica fechado. Fora do git (reunião em MCP, e-mail, chat) **não é fato**: vira tarefa `rodada-insumos`. Código, dependências, configuração, branches e corpo de PR ficam fechados — o replan planeja, não audita.
3. **Fatos novos.** `F<n> — fato — fonte (arquivo:linha · #PR · DT-NNN · `git diff <pivô>..HEAD -- arquivo`) → efeito ∈ {muda, remove, adiciona, feito, bloqueia→Qn} → item do plano`. Só fato que muda algo ganha linha; sem fonte, não entra. **`[x]` só com evidência**: a `verificação:` da tarefa passa agora (rodar se < 1 min) **ou** commit/PR cita o ID ou toca os `arquivos:`. PR que cita o ID mas não fecha o aceite → `[x]` + nota do que faltou + tarefa nova para o resto. Handoff "feito" sem isso → `[ ]` + nota; handoff "não iniciado" com commit → `[ ]` + `evidência parcial: #PR` — git vence handoff nos dois sentidos. Fato que exige escolha (contradiz decisão congelada, fontes em conflito, tarefa nova sem dono ou fora do escopo aprovado) é `bloqueia→Qn` — **nunca uma decisão "N<n>" tomada pela skill**. **Nenhum fato novo → sem arquivo**: "plano segue válido (fontes checadas: …)" e parar.
4. **Gate de decisões** — só se existe algum `bloqueia`. Formato e motor da [rodada-insumos, fase 4](../rodada-insumos/SKILL.md) (❓Qn/➡️; `mattpocock-skills:grilling` ou condução nativa com aviso — [ADR-0004](../../docs/adrs/ADR-0004-degradacao-graciosa-adapters.md)). Congelada sem fato contrário = **herdada** por ID + link, não pergunta. Sem resposta — ou sem interlocutor, em sessão autônoma — o documento sai assim mesmo: toda escolha em "Pendentes" com ➡️, tarefa `bloqueada por Qn`. "Decida e aja" para esta skill significa recomendar e bloquear, nunca escolher.
5. **Escrever o replan** em `<repo>/.claude/plans/AAAA-MM-DD-<topico>.md` (data de hoje) pelo [template](references/templates/replan.md) — **sempre ali**, também quando o plano vigente é uma delta. IDs do plano anterior **nunca renumerados nem reagrupados** — manter as seções por fase do plano anterior não é reagrupar; mudar a série é. Nova continua a série inteira (`T3a`/`T0.1` somem do gate). Decisões e fatos medidos por **ID + link ao dono**, nunca copiados. Cada tarefa aberta: `arquivos:` + `verificação:` executável ou observável + `fonte:`, e cabe em um turno — senão vira delta (régua do passo 3.5 da [handoff](../handoff/SKILL.md)); a tarefa `rodada-insumos` é a exceção, é um ciclo com PR própria. Plano anterior em `.claude/plans/` recebe, após o H1, `> Substituído por [<novo>](<novo>) em AAAA-MM-DD` — e nada mais. Delta como plano vigente: cabeçalho `Replaneja: specs/NNN-nome` em vez de `Substitui:`, sem banner; nada em `specs/NNN-*/` é tocado; cada edição (task nova, `[x]`, `— deferido:`, pendência na spec) é uma tarefa do replan com `arquivos: specs/NNN-*/tasks.md` e `verificação: check_cycle.py specs/NNN-nome`.
6. **Fechamento.** `git worktree list` antes de ramificar (sessão concorrente pode ter a branch); branch `docs/replan-<topico>`, commit Conventional, PR aberto se `.claude/plans/` é versionado (`git check-ignore -q .claude/plans/x.md` silencioso — testar um caminho de arquivo, a pasta pode não existir; ignorado → arquivo local + aviso, sem branch). Só os gates que o repo já roda no commit; **gate que bloqueia vira tarefa ou `DT-NNN`, nunca `--no-verify`** — o replan espera no índice da branch, e o DT entra no mesmo commit quando o gate liberar; gate de ambiente (âncora de versão do framework) aceita o que a própria mensagem dele oferece, mas reancorar o repo é decisão do usuário → tarefa. **A skill para no PR.** Fim de sessão → `handoff`.

## Erros comuns

| Erro | Correto |
|---|---|
| Ler `src/`, `package.json`, `.env.example`, branches e corpo de PR "para ter contexto" | Abre só o balde *fonte de fato*; o resto é caminho + PR |
| Reescrever `tasks.md`/`spec.md` da delta ("é o dono canônico; lista paralela seria verdade concorrente") | O replan é proposta com fonte; aplicar na delta é tarefa dele, pela `spec-feature`, na PR seguinte |
| Salvar o replan dentro de `specs/NNN-*/` | Sempre `.claude/plans/AAAA-MM-DD-<topico>.md` |
| Reagrupar em A0–A4/B1–B9 ou criar `T3a` | IDs estáveis; nova continua a série |
| "N1: fechar a delta com 19 abas em vez de 51" — decisão de escopo tomada pela skill | `bloqueia→Qn` no gate; sem resposta, `bloqueada por Qn` |
| "Q3 não faz mais sentido, mudo" | Só no gate, com fato + fonte |
| Handoff diz "feito" → `[x]`; diz "não iniciado" → nem olha o git | Evidência = verificação passando ou commit/PR, nos dois sentidos |
| "Quinze aprendizados" em prosa, sem `arquivo:linha`/`#PR` | Tabela Fatos novos, uma fonte por linha |
| Tarefa "revisar o PRD" / "implementar a delta" | `arquivos:` + `verificação:` e cabe em um turno |
| Hook bloqueou → `git commit --no-verify` "consciente, só docs" | Gate bloqueado vira tarefa/DT; o commit espera |
| Bateria de gates e testes do repo inteiro durante o replan | Só a `verificação:` da tarefa em dúvida (< 1 min); o resto é da execução |
| Reunião no MCP / e-mail "disse X" → fato | Fora do git não é fato; tarefa `rodada-insumos` |
| Replan sem fato novo | "Plano segue válido (fontes checadas)" e parar |

## Arquivos da skill

- `references/templates/replan.md` — template do replan; o inventário pré-preenchido **é** o mapa de alvos.
