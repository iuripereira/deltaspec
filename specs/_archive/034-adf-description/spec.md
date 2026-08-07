# delta-034 — adf-description
Estado: arquivada · Data: 2026-08-07 · Branch: fix/034-adf-description · Tipo: bugfix

## Sintoma (≤3 linhas)
Ticket projetado no Jira exibe a marcação literal — `**Delta:**`, crases, `---`, `_itálico_` — em vez de texto formatado. Visível em qualquer item criado pelo `tickets-acli.sh`, desde a delta-017 (2026-08-07), que trocou o `create-bulk` pelo create unitário. Reportado pelo Iuri a partir do SBX-14.

## Reprodução
- DADO um `DEBT.md` com um item aberto e sem `Ticket:` QUANDO `debito.py exportar . --saida X --projeto SBX` e o `tickets-acli.sh` resultante são executados ENTÃO a `description` da issue criada é um parágrafo único de texto puro com os asteriscos, crases e hífens visíveis — esperado: negrito, código, lista e regra horizontal renderizados.
- DADO um corpo com `` `x` `` de cerca dupla QUANDO ele é convertido ENTÃO os pares de crase desalinham e o restante da linha perde a formatação **sem erro** — esperado: a cerca de N crases casa com N crases.

## Causa-raiz
`emitir_sh_acli` escrevia o corpo Markdown em `corpo-<id>.md` e o passava a `--description-file` (`projecao.py:105-111`, antes desta delta). O `acli jira workitem create` aceita **texto puro ou ADF**, nunca Markdown — a marcação nunca foi interpretada por ninguém no caminho. A delta-017 validou que o corpo chegava **íntegro** (byte a byte), o que é verdade e insuficiente: íntegro como texto, não como formatação.

## Teste de regressão
- `skills/handoff/scripts/md_para_adf.py --selftest` — subset inteiro, aninhamento de marcas, exclusividade da `code`, cerca de N crases, ausência de text node vazio.
- `skills/handoff/scripts/projecao.py` (caso c2) — falha se o `.md` voltar a ir para o `--description-file` ou se a estrutura do corpo se perder na conversão.
- Execução real: SBX-24, criado pelo `tickets-acli.sh` gerado do caminho completo (`debito.py exportar`), com zero marcação crua fora de nós `code`.

## Mudanças
- nenhuma (correção sem mudança de requisito) — R52 continua descrevendo a projeção; o que muda é o formato do arquivo que o comando consome.

## Dependências e riscos
- O conversor cobre **só** o subset que `corpo_ticket()` emite (parágrafo, lista `- `, negrito, código, `---`, itálico, link). Sintaxe fora disso — tabela, título, citação, lista numerada — sai como texto do parágrafo, sem erro. É deliberado: o corpo é gerado por função nossa, não escrito à mão.
- Dois achados só apareceram na execução real contra o Jira, nenhum no selftest sintético: a mark `code` é **exclusiva** no ADF (combinada com `em`/`strong` o Jira recusa o documento inteiro, não o trecho), e a cerca dupla desalinhava em silêncio. Mantida a lição da delta-017: dialeto de ferramenta externa não se dá por validado sem execução real.
