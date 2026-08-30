---
name: handoff
description: Use when ending or pausing a work session in a project that follows the deltaspec records — writes a per-session handoff to .claude/handoffs/HANDOFF_<topic>_<YYYY>_<MM>_<DD>.md (objective, frozen decisions, discarded paths, code state, immediate next steps) and updates the thin HANDOFF.md index, the debts/ registry (DT-NNN files/lições) and current delta status. Trigger BEFORE context is lost — end of session, before /clear or /compact, switching focus or branch, blocked awaiting a decision, or handing work to another agent/person. Triggers include "/deltaspec:handoff", "fechar a sessão", "handoff", "passar o bastão", "salvar o progresso", "vou limpar o contexto", "encerrar por hoje", optionally with the next session's focus as argument.
---

# handoff

## Overview

Fecha a sessão de trabalho **nos registros com dono** do repositório (R18/R19 do TRUTH.md do framework): a sessão vira um arquivo próprio em `.claude/handoffs/`, o índice `HANDOFF.md` aponta para ele, o que a sessão descobriu de durável vai para o registro `debts/` (arquivo DT-NNN / `LICOES.md`), e a delta em curso fica citada com fase e gate. O handoff é **persistente e versionado** — a próxima sessão (ou outra máquina, ou outro humano) lê o repo e continua; nada vive só na conversa. (ADR-0025; formato anterior de arquivo único: ADR-0010.)

> Inspirada na `handoff` de [mattpocock/skills](https://github.com/mattpocock/skills) (MIT); reescrita para gravar nos registros do deltaspec em vez de um brief efêmero em `/tmp`.

Argumento opcional: o **foco da próxima sessão** (`/deltaspec:handoff terminar a migração do gate`) — entra nos "Próximos passos imediatos" do handoff da sessão.

## Quando chamar, quando registrar

**Chame antes de o contexto se perder:** fim de sessão · antes de `/clear` ou `/compact` · troca de foco ou de branch · bloqueio aguardando decisão · passagem de bastão para outro agente/humano.

**Registre só sessão com progresso real** — decisão tomada, código alterado ou aprendizado durável. Pergunta pontual ou sessão só de leitura não gera arquivo; se descobriu algo durável, roteie para o `debts/` e pronto. O conteúdo é **intenção e progresso**, nunca o que a próxima sessão lê sozinha no código-fonte.

## Processo (na ordem — o índice fecha por último)

1. **Rotear os achados novos.** Débito, pendência ou guarda descoberto na sessão e ainda sem registro → `python3 ${CLAUDE_PLUGIN_ROOT}/skills/handoff/scripts/debito.py novo . --natureza <débito|pendência|guarda> --descricao "<sintoma>" --fila P·J·Pr --local "[artefato](caminho/da/raiz)" --gatilho "<quando reavaliar>" --origem "<delta/PR/sessão>"` (prosa do corpo por stdin ou `--corpo-arquivo`). O comando calcula o `DT-NNN`, escreve o arquivo e o relê antes de devolvê-lo: **campo que a natureza exige e não veio faz ele recusar**, e item inválido não fica no disco — nada de escrever frontmatter à mão. `guarda` não tem `fila`. Gramática completa em [references/debito.md](references/debito.md). **Item que muda para `quitado`/`descartado` arquiva no mesmo commit** (ADR-0030): frontmatter ganha o estado final e `encerrado: AAAA-MM-DD`, o corpo ganha a seção `#### Como foi quitado` (2–4 frases amigáveis — o que doía, o que foi feito, o que muda; técnico fica no commit/PR e no comentário do issue GitHub; fechamento no Jira em nível de negócio) e troca **Ticket** por **Encerrado**, e o arquivo move com `git mv` para `debts/_archive/DEBT_DT-NNN-<topico>_<AAAA>_<MM>_<DD>.md` (data do encerramento) — links **não mudam** (mesma profundidade); o arquivo arquivado **nunca é podado**. Post-mortem sem ação pendente → `debts/LICOES.md`, com data e desfecho. Depois de rotear ou quitar, **regenere o índice**: `python3 ${CLAUDE_PLUGIN_ROOT}/skills/handoff/scripts/debito.py indice .` (o `DEBT.md` é projeção — ADR-0031). Projeto sem `debts/` → crie do template da `projeto-init` (ou `debito.py migrar` num registro legado).
2. **Cobrar a fila de dívida (aging).** Rode `python3 ${CLAUDE_PLUGIN_ROOT}/skills/handoff/scripts/debito.py fila .`. Havendo ao menos um item marcado `stale` na saída, apresente ao usuário — por item — as três saídas doutrinárias ([references/debito.md](references/debito.md), seção C): **agendar** (abrir a delta pelo fluxo normal de `spec-feature`), **aceitar** (com gatilho, edição do item pelo fluxo já existente) ou **descartar** (com motivo, arquivamento no mesmo commit). Sem `stale` na saída, siga sem aviso — silêncio é o caminho feliz. Projeto sem `debts/` → passo se omite.
3. **Escrever o handoff da sessão** em `.claude/handoffs/HANDOFF_<topico>_<AAAA>_<MM>_<DD>.md` (crie a pasta se não existir), a partir do template `handoff-sessao.md` da `projeto-init` — cabeçalho (Data · Status · Branch/Commit) + as 5 seções; tópico em kebab-case curto que desambigua sessões do mesmo dia; seção sem dado real sai. Se houver delta em curso em `specs/NNN-*/`, cite número, fase em que parou e o veredito do último gate — em dúvida, rode `python3 ${CLAUDE_PLUGIN_ROOT}/skills/spec-feature/scripts/check_cycle.py specs/NNN-nome`.
4. **Atualizar o índice `HANDOFF.md`** (teto ~30 linhas): `Agora` com o estado corrente em 2–4 linhas, a sessão nova no topo de `Sessões recentes` (link + resumo de 1 linha, ~10 entradas — as antigas saem da lista, os arquivos ficam) e o campo "Atualizado em".
5. **Commitar junto do trabalho da sessão** quando houver mudança pendente (regra do CLAUDE.md: doc no mesmo change). Sessão só de leitura → commit próprio do diário é aceitável.
6. **Imprimir o prompt de retomada.** Encerre com o prompt que inicia a próxima sessão — uma linha, apontando o `HANDOFF.md` (o índice leva ao handoff mais recente):

   ```
   Leia o HANDOFF.md deste repo e continue de onde paramos.
   Foco: <primeiro item de "Próximos passos imediatos" do último handoff>.
   ```

   Workspace multi-repo → `Leia os HANDOFF.md dos repos (<repo âncora> primeiro) e continue. Foco: <próximo marco>.`

   O prompt referencia os registros, nunca os resume — o conteúdo vive no repo (regra de ouro).

## Migração de formato legado

- **`HANDOFF.md` cheio no formato anterior** (quatro seções com entradas datadas): crie `.claude/handoffs/`, mova cada entrada datada para um arquivo por sessão (cabeçalho novo + conteúdo original — não invente Objetivo/Decisões retroativos; quando o "Atualizado em" divergir do histórico, a data que vale é a do commit no git) e reduza o índice ao formato novo. Nunca deixe os dois formatos coexistirem no mesmo repo.
- **`STATE.md` legado sem `HANDOFF.md`**: `git mv STATE.md HANDOFF.md` antes de escrever (nunca deixe os dois coexistirem), e então aplique a migração acima.

## Fila de dívida e projeção para tickets (consulta avulsa, fora do fechamento de sessão)

A leitura da fila (`debito.py fila`) já roda no **passo 2** do fechamento — esta seção cobre a consulta avulsa (fora de um handoff) e a projeção para ticket, que seguem sob demanda. Regra completa em [references/debito.md](references/debito.md) — ida, volta, idempotência e degradação vivem lá; o script **não acessa a rede**, quem executa os comandos é você.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/handoff/scripts/debito.py exportar .   # JSON canônico + dialetos
python3 ${CLAUDE_PLUGIN_ROOT}/skills/handoff/scripts/debito.py diff . --externo estado.json
```

## Regras de conteúdo

- **Referencie, não duplique** (regra de ouro): o que já está em spec, plan, ADR, debts/, CHANGELOG ou commit entra por caminho/ID (`DT-003`, `specs/_archive/007-*/`, `#21`), nunca copiado.
- **Segredo/PII nunca entra no diário** — nem em nenhum registro versionado (seção Segurança do CLAUDE.md).

## Erros comuns

| Erro | Correto |
|---|---|
| Gravar o handoff fora do repo (/tmp, gist, memória da IA) | O handoff do deltaspec é o próprio repo: `.claude/handoffs/` + índice + `debts/`, versionados |
| Deixar débito descoberto só na conversa | Rotear para DT-NNN **antes** de fechar o diário (passo 1 vem primeiro) |
| Índice virar acumulador de histórico de novo | Teto ~30 linhas; o detalhe vive no arquivo da sessão (R19) |
| Narrar no handoff o que o código já mostra | Intenção, decisões e caminhos descartados — o resto a próxima sessão lê sozinha |
| Gravar sessão sem progresso real | Pergunta pontual não gera arquivo; durável vai direto ao `debts/` |
| Quitar um DT e deixar o arquivo em `ativos/` | Encerrou = arquivou: editar frontmatter + `git mv` → `debts/_archive/`, no mesmo commit (a fila avisa o candidato esquecido) |
| Duplicar conteúdo de spec/ADR/CHANGELOG no diário | Referência por caminho/ID |
| Esquecer a delta em curso | Passo 3 a cita quando existe `specs/NNN-*/` |
| Fechar sem dizer como retomar | Passo 6: imprimir o prompt de retomada preenchido com o foco real |
