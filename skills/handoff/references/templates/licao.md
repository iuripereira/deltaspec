<!-- Template canônico da lição (ADR-0042). Placeholders {{...}} — não preencha à
     mão: o comando escreve. Gramática completa, com o porquê de cada campo,
     em ../licoes.md; este arquivo só existe para dar ao agente um exemplo real
     preenchido, que ensina o formato melhor do que a descrição do formato. -->

## Arquivo-modelo

```markdown
---
id: {{L-NNN}}
data: {{AAAA-MM-DD}}
descricao: {{a regra que fica, uma linha}}
familia: {{nome-curto-kebab}}
deteccao: {{gate|revisao|humano|sorte}}
prevencao: {{gate|debito|disciplina}}
origem: {{delta-NNN · PR #N · sessão}}
gerou: {{DT-NNN[, DT-MMM] ou —}}
reincide: {{L-NNN[, L-MMM] ou —}}
---

# [{{L-NNN}}] - {{a regra que fica, uma linha}}

## O que aconteceu
{{sintoma, gatilho e custo medido}}

## Causa
- {{um fator por linha — lacuna do sistema ou do processo, nunca "erro humano"}}

## Desfecho
{{o que já foi feito, com link para delta/PR/DT}}

## Prevenção
- {{gate|debito|disciplina}}: {{o check, o DT-NNN, ou a regra}}

- **Origem:** {{links}}
- **Registro:** {{commit/PR, se conhecido}}
```

## Exemplo preenchido

<example>

```markdown
---
id: L-043
data: 2026-08-30
descricao: Toda escrita seguida de git mv termina em git add explícito do destino
familia: indice-git-vs-disco
deteccao: revisao
prevencao: gate
origem: delta-097 · PR #363 · DT-130
gerou: —
reincide: L-001
---

# [L-043] - Toda escrita seguida de git mv termina em git add explícito do destino

## O que aconteceu
`debito.py quitar` reescrevia o frontmatter, chamava `git mv` e devolvia o caminho
novo. O `git mv` stagiou o blob antigo do índice (`estado: aberto`), não o que
acabou de ser escrito no disco. O commit que quitava o DT-130 gravou em
`_archive/` um item que a `main` ainda via como aberto. Custo: 1 item; nenhum gate
acusou — apareceu só ao revisar o DT já mergeado com `git show`.

## Causa
- `git mv` sobre um arquivo com modificação não-adicionada stagia a rename com o
  blob do índice, não com o disco — não é "mover e adicionar".
- O `--selftest` comparava o disco com o esperado, nunca `git show :<caminho>`.
- `git status` mostra `R` (renomeado) sem dizer qual conteúdo; CI e validador leem
  o disco, não o índice.

## Desfecho
delta-100 (`fix`, #394): `git add` do destino logo após o `git mv`, mais a
regressão que faltava, confrontando o blob staged contra o disco. A varredura
confirmou dano de um único item, corrigido no mesmo PR.

## Prevenção
- gate: [regressão do `--selftest` de `debito.py quitar`](../../scripts/debito.py) —
  reprova sempre que o índice divergir do disco no destino do `git mv`

- **Origem:** [delta-097](../../specs/_archive/097-lote-de-debitos-independentes/) · [PR #363](../../../../pull/363)
- **Registro:** [PR #395](../../../../pull/395)
```

</example>

<rationale>
`descricao` é a regra ("toda escrita seguida de git mv..."), não o sintoma ("o
DT-130 nasceu aberto no archive") — é o que generaliza para o próximo comando
que combine escrita + `git mv`, e é o que um agente lê ao varrer a pasta.
`Causa` lista o mecanismo do git e a lacuna do teste, nunca "esqueceram de
commitar" — a pergunta certa é o que no *sistema* permitiu o erro, não quem
errou. `Prevenção` aponta o gate real (a regressão do selftest) com link, não
uma promessa de disciplina — porque já existe um teste que reprova a
reincidência, `prevencao: gate` é o valor honesto, e `disciplina` seria
subdeclarar o que já está mecanizado.
</rationale>
