# ADR-0054: Registro de perguntas da descoberta — um arquivo por pergunta, índice gerado, dono na skill `descoberta`

- **Status:** Accepted (2026-11-03, delta-139)
- **Data:** 2026-11-03
- **Supersedes:** —
- **Superseded by:** —

## Context

A `descoberta` (delta-012) gerava `docs/discovery/questions.md` como um arquivo só: tabela `## Visão geral` (ID · Tema · Dono · Prioridade · Status) e, abaixo, um cabeçalho `### <código> · título — 🔴 Alta · ⬜ aberta` por pergunta, com o corpo em prosa. A `rodada-insumos` (delta-054) fechava pergunta "atualizando o status na visão geral e a nota datada no corpo" — dois lugares para o mesmo estado. Medido nos dois consumidores em 2026-11-03: no segundo, 8 das 26 perguntas têm um estado na tabela e outro no cabeçalho, e 7 perguntas nascidas em reunião (`NQ1`–`NQ7`, quatro delas 🔴 abertas) nunca entraram na tabela — que é a única parte que o relatório de gestão do portfólio lê. A trajetória de uma pergunta (contexto → avanços → resposta) se perdia no diff de um arquivo de 400 linhas, e o `git log` de uma pergunta não existia.

O primeiro consumidor resolveu isso em 2026-11-02 com um registro no molde do `debts/` ([ADR-0030](ADR-0030-registro-de-debitos-em-pasta-na-raiz.md), [ADR-0031](ADR-0031-debt-md-como-indice-gerado.md)): um arquivo `QUESTAO_QT-NNN-<topico>.md` por pergunta, frontmatter flat, índice gerado por um `questao.py` local (`novo`, `indice`, `migrar`), 110 perguntas migradas com datas, autor e release lidos do git. O script nasceu com o que era daquele projeto dentro dele: tabela de nomes de pessoas para identificar quem respondeu, regex de código que só aceitava `B4`/`T7`, texto do README. Uma cópia por consumidor é exatamente a classe de órfão que a `audit-workspace` acusa.

## Decision

1. **O plugin é o dono do registro de perguntas**, como já é de `debts/` e da memória: o script vive em `skills/descoberta/scripts/questao.py`, a gramática e o ritual em `skills/descoberta/references/questoes.md`, e as skills `descoberta`, `rodada-insumos`, `pedido-insumos` e `replan-doc` citam esse dono. Consumidor não tem cópia do script.
2. **Layout:** `docs/discovery/questions/QUESTAO_QT-NNN-<topico>.md`, um por pergunta, `QT-NNN` global ao repositório e nunca reusado; `docs/discovery/questions.md` é **projeção** regenerada por `questao.py indice`, nunca editada à mão. O código de época (`B4`, `GQ10`, `V-B1`) sobrevive em `codigo:` e na coluna Tema, porque PRD, débitos e e-mails o citam.
3. **Frontmatter flat parseado por regex stdlib**, não YAML — a mesma renúncia da ADR-0030 (`estado: no` viraria `False`; PyYAML segue opcional, [ADR-0023](ADR-0023-pyyaml-como-dependencia-admitida.md)). Chaves sempre escritas na ordem fixa; o `id` duplica o nome e o parser valida a igualdade.
4. **A tabela `## Visão geral` do índice é contrato externo** — cinco colunas e os glifos do arquivo legado — porque os relatórios de status do portfólio a leem de cada produto. Mudar as colunas é breaking change.
5. **Migração sem julgamento:** `migrar` lê do git a data de entrada, a transição para ✅ e a release; quando o cabeçalho diverge da tabela, **vale a tabela** (era o que o ritual atualizava e o relatório publicava) e o aviso nomeia a divergência; pergunta sem linha na tabela faz o comando recusar — completar a tabela é decisão humana. O autor da resposta sai do próprio rótulo (`**Resposta (DD/MM, Nome — …)**`), e nunca de uma tabela de nomes dentro do plugin: nome de terceiro não atravessa o allowlist de publicação ([ADR-0036](ADR-0036-publicacao-derivada-como-gate-de-confidencialidade.md)).

Renúncias:

- **Manter o monolítico e só corrigir o ritual** ("atualize os dois lugares") — a divergência medida é a prova de que disciplina não segura dois donos para o mesmo estado; e a trajetória por pergunta continuaria sem `git log` próprio.
- **Um script por consumidor** (copiar o `questao.py` para cada repo) — órfão por construção; a generalização que o plugin exige (código com hífen, autor pelo rótulo, texto neutro) é menor que manter N cópias.
- **`refs` genérico** (qualquer `XX-N`) para capturar IDs locais como `Q-N` ou `D14` — falso positivo em `PRO-9.3` e afins; o `refs` fica com os IDs que o framework governa, e o resto fica no corpo, pesquisável.
- **Preservar a `para` por inferência** (seção `##` ou prefixo do código) para pergunta sem linha na tabela — inventaria dono; o `migrar` recusa e o humano completa.

## Consequences

- Pergunta vira unidade endereçável: link estável, `git log -p` próprio, frontmatter legível por máquina. O "fecha pergunta" da `rodada-insumos` passa a ser uma edição de arquivo mais `indice`, não duas edições coordenadas.
- O primeiro consumidor fica com uma cópia local até a release que publica esta delta; trocá-la pelo script do plugin é DT lá, com o `audit-workspace` como testemunha.
- O índice pode ficar desatualizado sem que nada acuse (não há `indice --check` nem pré-commit nos consumidores) — pendência registrada na delta-139.
- Mais um script com `--selftest` no `ci` e nos READMEs, vigiado pelo `inventario_selftests.py`.
