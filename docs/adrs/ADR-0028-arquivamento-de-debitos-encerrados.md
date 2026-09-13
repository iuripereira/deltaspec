# ADR-0028: débitos encerrados arquivam em `.claude/debts/`; o DEBT.md fica com os ativos e um índice

- **Status:** Accepted (2026-08-10, delta-041)
- **Data:** 2026-08-10
- **Supersedes:** [ADR-0020](ADR-0020-modelo-de-divida-tecnica.md) — **apenas na renúncia a "arquivo por item"**: ela cai para itens em estado final (`quitado`/`descartado`). O modelo de fila (score derivado e nunca gravado, três eixos, `stale` calculado) segue vigente e continua sendo referenciado por aquela ADR.
- **Superseded by:** [ADR-0030](ADR-0030-registro-de-debitos-em-pasta-na-raiz.md) (2026-08-11, delta-043) — integralmente: o registro vira a pasta `debts/` na raiz (split total, um arquivo por item, ativos inclusive); `.claude/debts/` migra para `debts/_archive/` e a tabela `## Arquivados` deixa de existir. A renúncia ao "split total" abaixo caiu por decisão de produto.

## Context

O `DEBT.md` chegou a 408 linhas / ~66 KB (~22k tokens) e **57% das linhas pertencem a itens `quitado`** (24 encerrados vs 13 ativos). O arquivo está no caminho quente de toda sessão: a `eu-tenho-tdah` manda lê-lo inteiro antes de qualquer append, o `deltaspec:handoff` o atualiza em todo fechamento, e o custo de contexto cresce a cada quitação — o mesmo padrão que a delta-037/ADR-0025 diagnosticou no `HANDOFF.md` (um arquivo só acumulando "o que está vivo" e "como cada coisa terminou") e que a delta-040 está medindo no `TRUTH.md`.

A [ADR-0020](ADR-0020-modelo-de-divida-tecnica.md) havia renunciado a arquivo por item: *"a ADR-0007 promete `git log DEBT.md` e `grep -c` como forma de ler a trajetória da dívida, e ambos dependem de uma linha por item"*. A renúncia foi escrita quando o registro tinha uma fração do tamanho atual e protegia a leitura da trajetória — hoje o custo de carregar 24 desfechos completos supera o benefício de tê-los todos no mesmo arquivo.

## Decision

**Duas camadas, um dono por estado de vida** (decisões do usuário na entrevista da delta-041):

1. **Ativos (`aberto`/`aceito`/`vigente`) continuam blocos no `DEBT.md`** — gramática, fila, `stale` e parser do `debito.py` intactos.
2. **Item que muda para `quitado`/`descartado` arquiva no mesmo commit:** o bloco inteiro move para `.claude/debts/DEBT_DT-NNN-<topico>_<AAAA>_<MM>_<DD>.md` (data do encerramento, padrão de nome espelhando os handoffs) e o `DEBT.md` ganha uma linha na seção nova `## Arquivados` (`| [DT-NNN](caminho) | descrição breve | natureza | estado |`).
3. **"Quitado nunca some" (ADR-0007) é reinterpretado, não revogado:** visibilidade pela linha da tabela, história pelo arquivo — que **nunca é podado** (mesma cláusula dos handoffs de sessão).
4. **Numeração e projeção enxergam as duas camadas:** o próximo `DT-NNN` livre considera também os nomes em `.claude/debts/`, e o `debito.py diff` trata ID arquivado como estado final (o `DT-NNN` no nome do arquivo existe para isso — nenhum parser novo).
5. **Escopo: só este repositório.** O template do `projeto-init` e a `canonical-rules.md` não mudam; a propagação continua sob o DT-022, com o gatilho ampliado.

## Alternativas recusadas

- **Split total** (DEBT.md vira só tabela; todo DT, ativo ou não, em arquivo próprio): exigiria reescrever `carregar`/`montar_fila`/`dias_parado` do `debito.py` para varrer diretório, quebrando o contrato do R51 por um ganho marginal — os ativos são a parte útil do contexto.
- **Archive único** (`.claude/debts/ARCHIVE.md` com todos os encerrados): menor diff, mas recria o crescimento sem teto num arquivo só e não dá o índice navegável por item.
- **Remover o `DEBT.md` da raiz:** mesma razão da ADR-0025 — quebraria links vivos, o destino de pendências das skills e recriaria a ambiguidade "qual arquivo ler".

## Consequences

- `DEBT.md` cai de 408 para ~200 linhas; sessões pagam só pelos itens que ainda pedem decisão.
- `git log DEBT.md` deixa de contar o pós-vida dos encerrados — a trajetória de um item arquivado passa a ser: história no `DEBT.md` até o encerramento, desfecho completo no arquivo de `.claude/debts/`. A tendência abertos×quitados sai da tabela + `ls .claude/debts/`, não mais de `grep -c`.
- `.claude/debts/*.md` entra em `scan_globs` e `exclude_globs` do `deps.toml` (C3 vigia links, C2 isenta valores — regra do R61). Os atalhos `../../issues/N` reescritos para `../../../../` **não** são conferidos pelo C3 (R57 os ignora); a conferência é humana, no review da migração.
- Reabre quando: o volume de **ativos** tornar o próprio índice pesado (aí a discussão vira particionamento, no espírito do DT-036), ou a leitura da trajetória por arquivo se provar pior que a promessa original da ADR-0007.
