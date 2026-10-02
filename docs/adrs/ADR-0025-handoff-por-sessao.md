# ADR-0025: Handoff por sessão — o diário de bordo vira índice fino + arquivos por sessão

- **Status:** Accepted
- **Data:** 2026-08-09
- **Supersedes:** — <!-- estende a ADR-0010, não a supersede: "um dono de onde paramos" continua valendo; muda onde vive o histórico de sessão -->
- **Superseded by:** —

## Context

A [ADR-0010](ADR-0010-handoff-renomeia-state.md) fixou o `HANDOFF.md` como ponto de entrada único da retomada, com janela rolante: entrada antiga sai, histórico permanente é CHANGELOG + git. Na prática deste repo a janela rolante falhou dos dois lados ao mesmo tempo: o arquivo cresceu até virar um bloco de prosa que a LLM navega mal (entradas de 5–10 linhas re-narrando o que CHANGELOG e PRs já contam), **e** a poda apagou contexto de sessão três vezes (2026-07-28, 08-03, 08-09) — o CHANGELOG guarda *o que* mudou, mas não a intenção, as decisões congeladas e os caminhos descartados de cada sessão, que é exatamente o que a próxima sessão precisa para não rediscutir.

O problema, portanto, não é o ponto de entrada único (esse acertou) — é que um arquivo só acumula duas responsabilidades: dizer **onde estamos agora** e guardar **como cada sessão chegou lá**.

## Decision

O diário de bordo passa a ter duas camadas com um dono cada:

- **`HANDOFF.md` (raiz)** — **índice fino**, teto de ~30 linhas: seção `Agora` (estado corrente em 2–4 linhas) + `Sessões recentes` (link e resumo de 1 linha por handoff). Continua o único dono do "onde paramos" e o único alvo do prompt de retomada ("Leia o HANDOFF.md…").
- **`.claude/handoffs/HANDOFF_<topico>_<AAAA>_<MM>_<DD>.md`** — um arquivo por sessão com progresso real, no template canônico de 5 seções (Objetivo · Contexto e decisões congeladas · Estado do código · Próximos passos · Skills recomendadas), focado em **intenção e progresso** — nunca no que se lê sozinho no código. Histórico endereçável: sai da lista do índice, mas o arquivo nunca é podado.

A pasta nasce com o primeiro handoff (sem scaffold próprio). Repos com `HANDOFF.md` cheio migram graciosamente na primeira rodada da skill nova, com data do git quando o header divergir.

Renúncias registradas:
- **Remover o `HANDOFF.md` da raiz** (só a pasta) — rejeitado: quebra os links vivos dos READMEs (C3), o prompt de retomada de uma linha e recria a ambiguidade de "qual arquivo ler primeiro" que a ADR-0010 matou.
- **Manter o arquivo único e só alargar a janela** — rejeitado: adia o problema de navegação sem resolver a perda; a poda continuaria apagando intenção.
- **Reescrever as sessões passadas no formato novo de 5 seções** — rejeitado (decisão do usuário, 2026-08-09): inventaria "objetivo" e "decisões" retroativos que ninguém declarou; a migração preserva o conteúdo original sob o cabeçalho novo.

A renúncia central da ADR-0010 — dois donos de "onde paramos" — **continua válida**: os arquivos por sessão são histórico datado (como `specs/_archive/`), não um segundo "agora".

## Consequences

Fica mais fácil: a retomada lê ~30 linhas e segue o link da sessão relevante; o contexto de sessão nunca mais é podado; buscar "quando decidimos X" vira abrir o arquivo daquela data em vez de arquear o git.

Fica mais difícil / custo aceito:
- **Um artefato a mais por sessão** — mitigado pela regra "só sessão com progresso real gera arquivo".
- **Cobertura de gates precisa acompanhar**: `.claude/handoffs/*.md` entra nos globs do `deps.toml` (C3 cobre links, C2 isenta valores) e o W7 do `audit-workspace` reconhece o diretório como diário — sem isso os links dos handoffs sairiam da validação em silêncio.
- Consumidores migram sob demanda (primeira rodada da skill); até lá os dois formatos coexistem **entre** repos, nunca dentro do mesmo repo.

Consolidada no TRUTH via MUDA R19, MUDA R20, MUDA R59 e o requisito novo do formato por sessão (delta-037).
