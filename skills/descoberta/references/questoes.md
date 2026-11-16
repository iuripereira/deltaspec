# Registro de perguntas da descoberta — gramática e ritual

Dono da gramática do registro de perguntas aos stakeholders (ADR-0054 do plugin). O script é `scripts/questao.py` desta skill; a `rodada-insumos` e a `pedido-insumos` operam sobre o mesmo registro e apontam para cá.

## Layout

Uma pergunta = **um arquivo** `docs/discovery/questions/QUESTAO_QT-NNN-<topico>.md` (`QT-NNN` global ao repositório, nunca reusado; `<topico>` em kebab-case ASCII derivado do título). `docs/discovery/questions.md` é a **projeção** gerada por `questao.py indice .` — nunca editada à mão. Nenhuma pergunta é apagada: respondida muda de `estado`, e o `git log -p` do arquivo é a trajetória.

```markdown
---
id: QT-012
codigo: GQ1
estado: parcial
prioridade: alta
descricao: Critério escrito para dispensar uma OS
para: Qualidade
respondeu:
aberto: 2026-08-03
respondido:
release:
refs: RN-104, DT-036
---

# [QT-012] - Critério escrito para dispensar uma OS

**Contexto.** …

**Perguntas.** …

**Proposta de encaminhamento.** …

**Avanço (05/08, reunião — [dossiê](../2026-08-05-processo.md)).** …
```

Frontmatter flat, chaves ASCII, parser por regex (não YAML); **todas as chaves são sempre escritas**, vazias quando não se aplicam, na ordem acima.

| Chave | Valor |
|---|---|
| `id` | `QT-NNN`, igual ao do nome do arquivo (o nome é a fonte; o parser valida a igualdade) |
| `codigo` | código de época (`B4`, `GQ10`, `V-B1`…), citado em PRD, débitos e e-mails — nunca reusado; pergunta nova pode não ter |
| `estado` | `aberta` · `parcial` (parte já respondida) · `respondida` |
| `prioridade` | `alta` (trava definição de requisito) · `media` (refina o desenho) · `baixa` (não bloqueia) |
| `descricao` | título da pergunta, espelhado no H1 `# [QT-NNN] - descricao` (validado); sem `\|` |
| `para` | a quem foi dirigida, como está hoje (pessoa ou área; `A → B` quando mudou de mão) |
| `respondeu` | quem deu a resposta que fechou a pergunta; vazio enquanto não fecha |
| `aberto` | AAAA-MM-DD em que a pergunta entrou no registro |
| `respondido` | AAAA-MM-DD da resposta que fechou (data de negócio, não do commit) |
| `release` | tag `vX.Y.Z` que levou a resposta à `main`; `develop` quando integrada sem release; vazio na branch ou sem resposta |
| `refs` | `RF`/`RNF`/`RN`/`ADR`/`DT`/`delta` citados no título e no corpo — a relação com requisito e spec; o DT, quando há, descreve o que a resposta destrava. ID local do projeto (`Q-N`, `D14`) fica no corpo |

Links no corpo são relativos à pasta `questions/` (`../AAAA-MM-DD-dossie.md`, `../../../PRD.md`).

## Validações do `indice`

`questao.py indice .` relê todo o registro antes de escrever e sai 1 sem tocar o índice se algum item viola: `id` × nome do arquivo; obrigatórias `id, estado, prioridade, descricao, para, aberto`; `estado` e `prioridade` fora das listas; datas que não são AAAA-MM-DD; `respondida` sem `respondido`; H1 que não espelha `id` e `descricao`; `|` na `descricao`; `codigo` duplicado.

## Ritual

1. **Pergunta nova:** `python3 ${CLAUDE_PLUGIN_ROOT}/skills/descoberta/scripts/questao.py novo . --descricao "…" --para "<dono>" --prioridade alta|media|baixa [--codigo GQ14] [--refs "RF-110"]` — corpo com contexto e **proposta de encaminhamento** por `--corpo-arquivo` ou stdin. Nunca à mão: o ID sai do maior existente + 1.
2. **Resposta ou avanço:** edite o arquivo — nota datada com a fonte no corpo (`**Resposta (DD/MM, quem — [dossiê](../AAAA-MM-DD-x.md)).**`; `**Avanço (…)**` quando não fecha) e, no frontmatter, `estado`, mais `respondeu`/`respondido` ao fechar; `release` quando a resposta chegar à `main`.
3. **Sempre depois:** `python3 ${CLAUDE_PLUGIN_ROOT}/skills/descoberta/scripts/questao.py indice .` — valida e regenera o índice, no mesmo commit.

## Contrato do índice

A tabela `## Visão geral` do `questions.md` gerado tem **exatamente** `| ID | Tema | Dono | Prioridade | Status |` (Tema = `codigo · descricao`; glifos 🔴🟡🟢 e ✅🔶⬜): é lida pelos relatórios de status do portfólio de cada produto. Mudar colunas ou glifos é breaking change. As seções `## Pendentes` e `## Respondidas` (por prioridade, com link ao arquivo, dono ou autor, datas, refs e onde a resposta está integrada) são leitura humana.

## Migração do `questions.md` monolítico

`python3 ${CLAUDE_PLUGIN_ROOT}/skills/descoberta/scripts/questao.py migrar . [--dry-run]` converte o arquivo legado (`## Visão geral` + cabeçalhos `### <código> · título — 🔴 Alta · ⬜ aberta`) sem inventar julgamento:

- `QT-NNN` pela **ordem cronológica de entrada** no registro: primeiro commit do `git log -p` do arquivo que cita o código (desempate pela ordem no arquivo).
- `codigo` = código de época; `para` = coluna Dono da tabela; corpo verbatim com os links reescritos um nível acima (o item vive em `questions/`); tema da tabela diferente do título vira `**Pergunta:**` no corpo; sufixo do cabeçalho vira `**Estado:**`.
- `respondido`/`respondeu` do **último** rótulo `**Resposta|Decisão|Direção (…)**` do corpo — data em DD/MM[/AAAA] ou AAAA-MM-DD; autor = primeiro segmento após a data, aceito quando parece nome (palavras capitalizadas, partículas de/da/dos, iniciais, `PO`); decisão ou direção sem nada após a data = `PO`; segmento que não parece nome ("e-mail", "formulário") sai sem autor, com aviso. Fallback da data: o commit que marcou ✅ (no cabeçalho ou na linha da tabela; a transição conta quando nenhuma das duas já dizia ✅). `release` = tag mais antiga que contém esse commit; `develop` se só integrada; vazio fora.
- **Tabela vence cabeçalho:** estado ou prioridade divergentes entre a linha da Visão geral e o `###` ficam com o valor da tabela (era o que o ritual atualizava e o relatório publicava), com aviso nomeando a divergência.
- **Cabeçalho sem linha na tabela recusa** a migração nomeando os códigos: complete a tabela (dono, prioridade, estado) antes — é decisão humana. Linha na tabela sem cabeçalho não vira item e sai como aviso; célula sem glifo cai no valor do cabeçalho, também com aviso.
- `--dry-run` imprime a prévia (id, código, estado, datas, release, autor, título), os avisos (respondida sem data ou sem autor identificável) e os links sem alvo, sem escrever nada. Leia-o antes de migrar; o que ele acusa é dado a corrigir no arquivo legado ou, depois, no frontmatter (`respondeu:`), nunca no script.
- O cabeçalho e os preâmbulos de seção do arquivo antigo (revisões, notas de reunião, pedidos) ficam preservados em `docs/discovery/questions/README.md`, abaixo de um cabeçalho curto que aponta para esta gramática; o índice é regenerado no fim.

No consumidor, depois da migração: `docs/discovery/questions/**/*.md` entra no `exclude_globs` do `deps.toml` (valores citados são legítimos; links seguem no C3) e o `CLAUDE.md` descreve o registro ao lado do `DEBT.md`.
