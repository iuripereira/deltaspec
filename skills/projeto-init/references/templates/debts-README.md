# debts/ — registro de débito técnico, pendências e guardas

> Dono canônico do registro de dívida deste repositório (modelo do deltaspec, ADR-0030/0031/0042 do framework). **Um arquivo por item**: ativos em `ativos/`, encerrados em `_archive/` (a pasta nasce no primeiro arquivamento), post-mortems em `licoes/` (nasce na primeira lição). Ticket em ferramenta externa (GitHub/Jira) é **projeção** deste registro, nunca a fonte — e o `DEBT.md`/`LICOES.md` da raiz são **índices gerados** (`debito.py indice .` / `licao.py indice .`), nunca editados à mão.

## Como ler

Para ver o que fazer primeiro:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/handoff/scripts/debito.py fila .
```

**As três naturezas.** `débito` é problema técnico a corrigir quando o gatilho disparar. `pendência` é trabalho ou decisão que sobrou de uma delta arquivada. `guarda` é um aviso para **não** "consertar" histórico imutável — não é trabalho, é proteção.

**Os cinco estados** (chave `estado:` do frontmatter):

| Estado | O que significa | Exige |
|---|---|---|
| `aberto` | reconhecido, ainda não decidido nem pago | `fila`, Local, Gatilho |
| `aceito` | dívida deliberada: você mediu e escolheu conviver com ela | **Gatilho** de reavaliação |
| `vigente` | guarda permanente; nunca será "resolvida" | nada além da descrição |
| `descartado` | deixou de fazer sentido sem ter sido paga | **Encerrado** com data e motivo + move para `_archive/` |
| `quitado` | resolvida de fato | **Encerrado** com data e referência + move para `_archive/` |

**`stale` não é um estado e nunca se escreve aqui.** É marca que o script deriva do git: item de juros altos cujo frontmatter (`natureza:`/`estado:`) não muda há tempo demais. Editar prosa não conta — só mudar o estado conta como decisão.

## Formato do arquivo

Ativo = `ativos/DEBT_DT-NNN-<topico>.md` (topico em kebab-case, **sem data** — as datas vivem no frontmatter):

```markdown
---
id: DT-NNN
natureza: débito | pendência | guarda
estado: aberto | aceito | vigente
fila: P3·J1·Pr9          ← só os eixos; guarda NÃO tem fila; score nunca é gravado
descricao: Uma linha com o sintoma observável
aberto: AAAA-MM-DD
---

# [DT-NNN] - Uma linha com o sintoma observável

Prosa livre. Seções opcionais (`#### Impacto`, `#### Solução proposta`,
`#### Critérios de conclusão`) são prosa — o parser as ignora.

- **Local:** [artefato](../../caminho/real)
- **Gatilho:** quando reavaliar/corrigir
- **Origem:** {{PR/delta/decisão}}
- **Ticket:** {{link, quando projetado}}
```

- O `id:` duplica o do nome **de propósito** e o script valida a igualdade (o nome é a fonte).
- A primeira linha do corpo é o **título humano** `# [DT-NNN] - <descricao>` — espelho do frontmatter, validado pelo script.
- Chaves do frontmatter em ASCII sem acento (`descricao`, nunca `descrição`).
- `- **Fila:**` no corpo é erro: a fila vive só no frontmatter (fonte única).
- Links são relativos ao arquivo (2 níveis): repo = `../../x`; atalho GitHub = `../../../../issues/N`. Como `ativos/` e `_archive/` têm a mesma profundidade, **quitar nunca reescreve link**.

## Cadastro

Não escreva o arquivo à mão: `debito.py novo` calcula o `DT-NNN` (numeração global, IDs **nunca reutilizados**, contando `ativos/`, `_archive/` e as branches remotas já buscadas), escreve o formato e relê o arquivo antes de devolvê-lo — campo que a natureza exige e não veio faz o comando recusar nomeando o campo, e item que não passa não fica no disco. Nunca invente valor: sem a triagem dos eixos, a fila sai com erro cobrando.

## A fila (3 eixos → score derivado)

`fila: P{1|3|9}·J{1|3|9}·Pr{1|3|9}` — cada eixo em três degraus (1 baixo, 3 médio, 9 alto):

- **P**rincipal — quanto custa pagar (menos de um dia · cerca de um ciclo · mais de um ciclo)
- **J**uros — o atrito **já observado** (incômodo · atrasa entregas · bloqueia entrega)
- **Pr**obabilidade — chance de a dívida incidir de novo (artefato frio · morno · tocado toda semana)

Deles sai o **score `(J × Pr) / P`**, que ordena a fila e **nunca é gravado** (ADR-0020 do framework). Sufixos: ` · trilha` tira o item da competição por score; ` · !<caso>(prazo)` é impedimento e fura a fila. Regra completa (override, trilha, aging, aceitação, projeção): `references/debito.md` da skill handoff do deltaspec.

## Quitação e descarte (mesmo commit)

**Quitação/descarte = `debito.py quitar`, não edição à mão.** A única edição manual é gravar `estado: quitado`/`descartado` no frontmatter:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/handoff/scripts/debito.py quitar . DT-NNN \
  --como "2-4 frases: o que doía, o que foi feito, o que muda" [--ticket-ref "delta-NNN · #PR"]
```

Ele injeta `encerrado: AAAA-MM-DD`, escreve `#### Como foi quitado` (linguagem amigável — detalhe técnico fica no commit/PR e no comentário do issue), troca `- **Ticket:**` por `- **Encerrado:**` e move com `git mv` para `_archive/`. Regenere o índice: `python3 ${CLAUDE_PLUGIN_ROOT}/skills/handoff/scripts/debito.py indice .` (o `fila` avisa se esquecer).

O item **muda de lugar, nunca some**: o arquivo arquivado não é podado. Ticket aberto do item? Feche citando a quitação — no GitHub o comentário pode ser técnico; **no Jira, em nível de negócio** (resultado e impacto, sem jargão).

## Lições

Post-mortem sem ação pendente é uma lição — `licoes/LICAO_L-NNN-<topico>.md`, uma por arquivo, **imutável** depois do commit: frontmatter (`id`, `data`, `descricao`, `familia`, `deteccao: gate | revisao | humano | sorte`, `prevencao: gate | debito | disciplina`, `origem`, `gerou`, `reincide`) e corpo em quatro seções fixas — `## O que aconteceu` → `## Causa` (um fator por linha; "erro humano" não é causa) → `## Desfecho` → `## Prevenção`. Valores de `deteccao`: `gate|revisao|humano|sorte`; de `prevencao`: `gate|debito|disciplina` — legenda de cada um em `references/licoes.md` da skill handoff. Cadastro só por comando:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/handoff/scripts/licao.py nova . \
  --descricao "a regra que fica" --familia nome-kebab --deteccao gate --prevencao disciplina \
  --origem "delta-NNN · PR #N" [--gerou DT-NNN] [--reincide L-NNN] --corpo-arquivo corpo.md
```

Reincidência é lição **nova** que cita a antiga em `reincide:` — a antiga nunca é editada. `LICOES.md` é índice gerado: `python3 ${CLAUDE_PLUGIN_ROOT}/skills/handoff/scripts/licao.py indice .`. Gramática completa: `references/licoes.md` da skill handoff do deltaspec.

## Avisos de operação

- Registro legado (`DEBT.md` com blocos ou tabela)? `debito.py migrar .` converte — fila/datas ausentes viram relatório de triagem, nunca valor inventado.
- Prosa que **inicie linha** com `estado:` ou `natureza:` no corpo reinicia o relógio do `stale` daquele arquivo (falso reset conservador). Cite essas chaves no meio da frase ou com crase.
