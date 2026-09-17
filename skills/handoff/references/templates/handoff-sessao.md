---
topico: {{tópico-kebab-case}}
data: {{AAAA-MM-DD}}
status: {{em curso|bloqueado|fechado}}
seq: {{N — 1 na primeira sessão do tópico, incrementa a cada continuação}}
veio_de: {{.claude/handoffs/HANDOFF_<tópico>_<data>.md da sessão anterior, ou vazio}}
delta: {{specs/NNN-nome/, ou vazio}}
resumo: {{uma frase, ≤180 caracteres — usada por handoff_indice.py para gerar "Sessões recentes" sem reabrir o arquivo}}
---

<!-- Nome do arquivo: .claude/handoffs/HANDOFF_<topico>_<AAAA>_<MM>_<DD>.md — <topico> em
     kebab-case curto, que desambigua sessões do mesmo dia (mesmo valor do campo `topico`
     acima). Foco em INTENÇÃO e PROGRESSO: nada do que a próxima sessão lê sozinha no
     código-fonte. Seção sem dado real sai — regra de ouro: referencie, não duplique.
     Gate mecânico: skills/handoff/scripts/check_handoff.py (valida os campos e os itens
     1/4/5/9/10 do checklist abaixo; os itens 2/3/6/7/8 são autorrevisão — SKILL.md passo 3.5). -->

**Branch/Commit:** `{{branch}}` @ `{{sha7, se aplicável}}` · **Delta:** `{{specs/NNN-nome/ fase <fase>, gate <veredito>, ou vazio}}`

## Objetivo

{{Uma frase. O que esta sessão foi fazer. Se não cabe em uma frase, a sessão fez duas
coisas — escreva dois handoffs.}}

## Herdado e entregue (interface)

- **Consumi:** {{o que o handoff anterior (veio_de) deixou pronto — arquivo, decisão, DT, PR}}
- **Entrego:** {{o que a próxima sessão pode assumir como verdade — assinatura, arquivo, gate ligado}}
- **Não entrego:** {{o que ficou pela metade e a próxima NÃO pode presumir}}

## Decisões congeladas e caminhos descartados

- **{{decisão}}** — porque {{razão medida, não opinião}}. Renúncia: {{o que foi rejeitado e
  por quê}}. Decisão com renúncia estrutural vai para `docs/adrs/`; aqui fica só o ponteiro.
- **Descartado: {{abordagem}}** — caiu em {{medição/teste/execução}}, não em leitura.
  Evidência: `{{comando}}` → `{{resultado}}`. Se a hipótese caiu por achismo, ela não caiu:
  ainda é caminho aberto.

## Estado do código

- **Mudou:** `{{caminho/arquivo.py:120-180}}` — {{o que mudou em intenção, não em diff}}
- **Verificado:** `{{comando exato}}` → `{{resultado}}`
- **NÃO verificado:** {{o que ficou sem teste, nomeado. Campo obrigatório — "nada ficou sem
  teste" é resposta válida e precisa estar escrita.}}
- **Git:** commitado? pushado? PR `#NNN` {{verde|vermelho|aberto}}? merge pendente de quem?

## Próximos passos imediatos

Ranqueados. Cada item cabe em **um turno** (não em uma delta) e traz comando literal.

1. *agora* — {{verbo no infinitivo + objeto específico}}
   - Onde: `{{caminho/arquivo.py:LINHA}}`
   - Comando: `{{comando literal, copiável}}`
   - Funciona quando: `{{saída esperada verificável}}`
2. *agora* — ...
3. *depois* — ...

## Pendências roteadas

- `DT-NNN` {{título}} — `debts/ativos/DEBT_DT-NNN-<topico>.md` (caminho relativo à raiz do repo)
- `L-NNN` {{regra}} — `debts/licoes/LICAO_L-NNN-<topico>.md`

## Avisos recebidos de outras sessões

<!-- Só existe se houve. Toda mensagem de outra sessão (cross-session messaging) que mudou
     o rumo vira linha aqui — mensagem não é registro; o registro é este arquivo. -->

- De `@{{sessão}}` em HH:MM — {{o que avisou}} → {{o que fiz com isso}}

## Prompt de retomada

```
Leia o HANDOFF.md deste repo e continue de onde paramos.
Foco: {{item 1 de "Próximos passos imediatos", literal}}.
```
