# ADR-0020: dívida técnica com score determinístico, derivado e nunca gravado

- **Status:** Accepted (2026-08-01, delta-023)
- **Data:** 2026-08-01
- **Supersedes:** —
- **Superseded by:** —

## Context

O `DEBT.md` registra o **fato** de cada dívida (natureza, descrição, origem, data, gatilho, status) mas não registra **peso**: nada diz o que fazer primeiro quando dois gatilhos disparam no mesmo dia. Na prática a ordem saía da memória de quem estava lendo — e item caro nunca subia, porque "vou deixar para quando sobrar tempo" é uma decisão que se repete sozinha.

Além disso o arquivo não é validado por gate algum: o `deps.toml` o exclui da varredura e o C6 do `check_cycle.py` lê o `spec.md` arquivado, nunca o DEBT. Link morto, item sem localização e status inventado passavam despercebidos.

Alternativas consideradas:

1. **Manter a ordenação implícita pelo gatilho.** Custo zero, mas é justamente o estado que produziu itens abertos por semanas sem decisão — e o DT-004 provou que um item pode ficar aberto sete dias *depois de satisfeito* sem ninguém notar.
2. **Adotar o schema completo de Technical Debt Item** (14 campos obrigatórios: `layer`, `td_type`, `owner`, `origin_project`, atributo ISO 25010, causa/consequência/evidência estruturadas), em arquivo por item com front-matter YAML.
3. **Núcleo mínimo que paga, em colunas da tabela existente:** localização, os três eixos do score e estados de ciclo de vida — com o score derivado por script.

## Decision

Adotamos a **3**. A tabela do `DEBT.md` ganha `Título`, `Local`, `Fila` e `Externo`; o score é `(juros × probabilidade) / principal`, calculado por `skills/handoff/scripts/debito.py` na leitura e **nunca gravado**. A política de fila (override, trilha planejada, aging, aceitação) vive em `skills/handoff/references/debito.md`, e os limiares são constantes nomeadas no script.

Renunciamos à **2** em três frentes. **YAML está fora**: nenhum artefato do framework usa front-matter, nenhum script tem parser YAML, e adicionar PyYAML violaria a regra de zero dependência externa dos gates — a tabela markdown se parseia com `str.split` da stdlib. **Arquivo por item está fora**: a ADR-0007 promete `git log DEBT.md` e `grep -c` como forma de ler a trajetória da dívida, e ambos dependem de uma linha por item. **Sete campos ficaram de fora** (`layer`, `td_type`, `owner`, `origin_project`, ISO 25010, causa e consequência estruturadas): num registro de menos de uma dezena de itens pontuáveis com um único mantenedor, eles seriam formulário sem leitor — a causa e a consequência continuam em prosa nas colunas que já existem, e as etiquetas do ticket são derivadas de natureza e fila, sem campo novo.

Renunciamos à **1** porque a ordenação implícita já falhou de forma documentada.

Três proibições ficam registradas como parte da decisão: **não converter score em moeda** (falsa precisão que desloca a discussão para a planilha); **não priorizar por principal isolado** (barato e inofensivo continua sendo trabalho sem retorno); **não persistir o valor calculado** (seria uma segunda fonte da verdade, que é o que o `deps.toml` existe para impedir).

O script **não** entra como gate bloqueante nesta delta. Mecanizar um formato que ainda não estabilizou produziria falso "tudo certo" — é a mesma cautela que adiou o DT-013 e que a ADR-0006 fixou como perímetro.

## Consequences

**Fica mais fácil:** a fila tem ordem defensável e reprodutível, que não depende de quem está lendo; localização vira campo validado, então dívida sem endereço deixa de existir; a probabilidade é conferida contra o churn real do git em vez de ser chutada; `aceito` com gatilho separa dívida deliberada de dívida esquecida, e `stale` cobra decisão de quem adiou demais.

**Fica mais difícil:** cada item passa a exigir três julgamentos (principal, juros, probabilidade) na abertura, e julgamento ruim produz fila ruim com aparência de objetividade — mitigado pela derivação do churn, que desmente a probabilidade otimista; a tabela ficou mais larga; e os limiares (dias até `stale`, janela do churn, percentis) são hoje uma escolha de projeto sem dado empírico por trás, que só a operação vai calibrar.
