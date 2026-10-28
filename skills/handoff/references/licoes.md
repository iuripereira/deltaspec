# Registro de lições — gramática e índice (ADR-0042)

## Gramática do registro (layout `debts/licoes/`)

Cada lição é **um arquivo** `debts/licoes/LICAO_L-NNN-<topico>.md` (topico em kebab-case, sem data — a data vive no frontmatter). O frontmatter é flat, todas as nove chaves obrigatórias:

```markdown
---
id: L-001
data: {AAAA-MM-DD}
descricao: A regra que fica, em uma linha
familia: nome-curto-kebab
deteccao: gate
prevencao: disciplina
origem: delta-{NNN} · PR #{N}
gerou: —
reincide: —
---

# [L-001] - A regra que fica, em uma linha

## O que aconteceu
Sintoma, gatilho e custo medido, em prosa curta — números e datas do incidente entram aqui.

## Causa
- Um fator por linha. "Erro humano" não é causa: descreva a lacuna do sistema ou do
  processo ("o gate não existia", "o alerta não disparou").

## Desfecho
O que já foi feito, com link para delta/PR/DT.

## Prevenção
- gate: [check](caminho) — o que ele reprova
- disciplina: a regra, em uma frase

- **Origem:** {links}
- **Registro:** {commit/PR que gravou a lição, se conhecido}
```

**Por que cada campo existe:**

- **`descricao`** é a regra que fica — a primeira coisa que um agente lê ao varrer a pasta (é o mesmo motivo do teto de 100 caracteres do débito, R141: vira título do índice). Sintoma, não solução.
- **`familia`** agrupa reincidência (kebab-case livre, sem enum fechado — família nova nasce quando aparece; grafia divergente é pega no review, não vale o custo de um vocabulário fechado).
- **`deteccao`** (`gate|revisao|humano|sorte`) mede **como** o problema foi pego: `gate` (check automático acusou) · `revisao` (review ou releitura obrigatória antes de editar) · `humano` (alguém olhou o resultado e viu) · `sorte` (apareceu de raspão). É a métrica de quanto os gates do framework realmente pegam — insumo do DT-017.
- **`prevencao`** (`gate|debito|disciplina`) mede **o que** impede a reincidência: `gate` (há check que reprova) · `debito` (um `DT-NNN` cobre — cite-o em `gerou`) · `disciplina` (só regra escrita, sem gate). A lista de `prevencao: disciplina` é o backlog de mecanização visível — não folclore, um filtro no índice.
- **`gerou`** / **`reincide`** são arestas, não prosa: `gerou` lista os `DT-NNN` abertos por esta lição (obrigatório e não-vazio quando `prevencao: debito`); `reincide` lista as lições anteriores que este mesmo problema já tinha gerado — o índice deriva "reincidiu em" na lição antiga a partir disto — a lição antiga nunca é editada para recebê-lo.

## Quando nasce

A lição nasce **quando o desfecho já existe** — correção mergeada, configuração aplicada, ou um DT aberto para o que sobrou — no fechamento da sessão que o fechou, e chega à `main` pelo PR dessa sessão. `registro` é esse PR quando o número já é conhecido; senão, o campo fica ausente e o git responde (`git log -S`). A lição **não espera um PR**: medido em 2026-09-04, 30 dos 43 incidentes registrados no repositório não eram PR (tag cortada de main atrasada, config local do git, varredura de repos, colisão de sessão, premissa de plano, fixture cega) — só 13 nasceram de um PR mergeado errado, empilhado ou fechado.

## Causa: um fator por linha, nunca causa única

Separe **gatilho** (o que disparou) de **fatores contribuintes** (o que precisou estar presente) — a seção `## Causa` lista cada um em bullet próprio; se removê-lo evitaria o problema, ele entra. "Erro humano" nunca é o texto de um fator: é sempre sintoma de uma lacuna de sistema ou processo, e é essa lacuna que se escreve.

## Imutabilidade e reincidência

Uma lição gravada **nunca é editada** — é registro de época (mesma guarda do `debts/_archive/`; o hook `guarda-imutaveis.py` pede confirmação em `Edit`/`Write` sob `debts/licoes/`). Lição que se provou errada é corrigida por lição **nova** que a cita em `reincide:`, nunca apagada nem reescrita. O cadastro por `licao.py nova` (script, via Bash) não passa pelo hook — só a edição direta de um arquivo existente pede confirmação.

## Cadastro

Não escreva o arquivo à mão — `licao.py nova` calcula o `L-NNN` (numeração global, nunca reutilizada, união do disco com os refs remotos já buscados, sem rede), valida os dois enums, as arestas (`gerou` contra `debts/ativos/`+`debts/_archive/`, `reincide` contra `debts/licoes/`), a ordem das quatro seções e o teto da `descricao`, e relê o que escreveu — arquivo que não passa é apagado antes do comando devolver.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/handoff/scripts/licao.py nova . \
  --descricao "a regra que fica" --familia nome-kebab \
  --deteccao gate --prevencao disciplina --origem "delta-NNN · PR #N" \
  [--gerou DT-NNN[,DT-MMM]] [--reincide L-NNN[,L-MMM]] [--data AAAA-MM-DD] \
  [--registro "commit/PR"] --corpo-arquivo corpo.md
```

Corpo do arquivo passado por `--corpo-arquivo` (ou stdin) traz **só** as quatro seções (`## O que aconteceu` → `## Causa` → `## Desfecho` → `## Prevenção`), na ordem — o comando monta sozinho o frontmatter, o título H1 e os campos `Origem`/`Registro`, reescrevendo todo link do corpo e da origem para 2 níveis (mesma profundidade de `debts/ativos/`). Corpo acima de `LICAO_TETO_PALAVRAS` (constante nomeada em `scripts/licao.py`) **avisa, nunca recusa** — narrativa longa fica no handoff ou no PR, linkada em vez de duplicada.

## Índice (ADR-0042)

`debts/LICOES.md` é **projeção gerada**, nunca fonte:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/handoff/scripts/licao.py indice .              # regenera
python3 ${CLAUDE_PLUGIN_ROOT}/skills/handoff/scripts/licao.py indice . --verificar  # só compara; é o step do CI
```

Render determinístico (mesmas lições → mesmos bytes): contagens por `deteccao` e por `prevencao`, lições em ordem de data decrescente, e a seção **Famílias com reincidência** (famílias com duas ou mais lições). Lição ilegível estruturalmente é reportada e fica fora do índice — nunca some em silêncio. Eleger uma cópia como fonte é meia consolidação; a outra metade é o check que a vigia (lição de 2026-08-16) — por isso `--verificar` é step bloqueante do `ci`.

## O que não entra

- Narrativa completa do incidente (fica no handoff da sessão ou no PR, linkada em `Origem`/`Registro`).
- Cópia de conteúdo do commit/PR/DT (referência, não duplicação — regra de ouro).
- `estado` ou `dono`: a lição só existe quando a ação já tem destino — o estado vive no `DT-NNN` que ela gerou, o dono é o repositório.
- Enum fechado de `familia`, campos de timeline ou glossário — YAGNI até um caso provar necessidade.
