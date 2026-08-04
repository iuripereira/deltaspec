# Prosa de regras, processos e decisões — guia normativo

Vale para PRD, spec, ADR e entregável cliente. Fundamentos: EARS (Easy Approach to
Requirements Syntax), tabelas de decisão (DMN), RFC 2119 e guias de technical writing
(Google Tech Writing One): **uma ideia por frase, prosa rasa, estrutura visível**.

## Os 6 mandamentos

1. **Uma regra = uma frase** (15–20 palavras). Frase com dois "e", "exceto", "desde que"
   aninhados → quebrar em duas regras ou virar tabela.
2. **Prosa não aninha.** Condição dentro de condição dentro de exceção é sinal de que o
   formato está errado — o conteúdo pede tabela de decisão, lista ou diagrama, não parágrafo.
3. **Palavras normativas fixas:** DEVE / NÃO DEVE / PODE (equivalente PT-BR do RFC 2119).
   "É o caminho padrão", "obrigatoriamente", "apenas se" espalhados pelo texto viram
   ambiguidade jurídica no entregável.
4. **Regra combinatória vira tabela de decisão.** A partir de ~3 condições ou de qualquer
   produto cartesiano (papéis × permissões, canal × falha, provedor × domínio), a prosa é
   substituída — não complementada — por uma tabela: uma linha por combinação, colunas
   Condição(ões) · Resultado · Justificativa/Ref. O que não está na tabela é proibido por
   default, e a tabela diz isso na legenda.
5. **Processo/fluxo vira diagrama + passos numerados.** Sequência com mais de 3 passos ou
   qualquer bifurcação: diagrama da categoria certa (fluxo → Mermaid; conceito/explicativo →
   Excalidraw, ADR-0009) + lista numerada onde cada passo é uma frase. A prosa fica para o
   *porquê*, nunca para o *como* passo-a-passo.
6. **Estrutura padrão de uma seção de regra:** contexto (1–2 frases de prosa) → regra
   (EARS/tabela) → exceções (explícitas, mesmo formato da regra) → auditoria/verificação
   (como se observa o cumprimento). Nunca misturar as quatro coisas num parágrafo só.
7. **Número medido entra datado.** Contagem, medição ou estado observado citado como
   evidência carrega a data (ou a delta) da medição — "19 links (medição de 2026-08-02)"
   é verdade para sempre; "19 links" apodrece em silêncio. Valor normativo (limiar, teto,
   versão pinada) não é medição e segue sem data. Norma do ciclo: R6 do TRUTH (delta-030).

## Padrões EARS (para a frase da regra)

| Padrão | Molde (PT-BR) | Exemplo |
|---|---|---|
| Ubíquo | O \<sistema\> DEVE \<resposta\> | O backend DEVE registrar toda mudança de role em `audit_log` |
| Dirigido por evento | QUANDO \<gatilho\>, o \<sistema\> DEVE \<resposta\> | QUANDO a trip é persistida, o motor DEVE criar uma linha em `notifications` por canal habilitado |
| Estado | ENQUANTO \<estado\>, o \<sistema\> DEVE \<resposta\> | ENQUANTO o provedor estiver indisponível, o worker DEVE reter a entrega na fila |
| Comportamento indesejado | SE \<condição indesejada\>, o \<sistema\> DEVE \<resposta\> | SE o e-mail não for corporativo, o SSO DEVE rejeitar com 403 |
| Opcional | ONDE \<feature presente\>, o \<sistema\> DEVE \<resposta\> | ONDE WhatsApp estiver habilitado, o worker DEVE usar o template aprovado |

## Antes → depois (o anti-padrão real que motivou este guia)

**Antes (aninhado, ambíguo):**

> Autorização: RBAC (planner, manager, technician (fora do MVP — ver tabela abaixo), admin,
> root). O campo users.roles é um array — modelo suporta múltiplas roles por usuário, com
> restrições abaixo. Acumulação de roles — invariante: apenas usuários gestores podem
> acumular role. A única combinação permitida é [manager, admin]. Demais combinações
> (ex.: [planner, manager], …) são proibidas pelo backend (validação no payload…).

**Depois (contexto + tabela + exceção + auditoria):**

> O modelo autoriza por RBAC; `users.roles` é um array, mas acumulação é exceção, não regra.
>
> | Combinação | Permitida? | Justificativa |
> |---|---|---|
> | 1 role qualquer | Sim | caso comum |
> | `[manager, admin]` | Sim | gestor que também administra a configuração |
> | qualquer outra | **Não** | separação de funções (operacionais não acumulam); `root` é exclusivo por desenho |
>
> O backend DEVE rejeitar no payload de criação/edição qualquer combinação fora desta tabela.
> Toda mudança em `users.roles` DEVE gerar entrada em `audit_log` com before/after.

## Checklist de revisão (antes de congelar baseline)

- [ ] Nenhum parágrafo com regra combinatória em prosa (procure "exceto", "apenas se", "a única combinação")
- [ ] Nenhum parêntese dentro de parêntese; nenhuma frase > ~20 palavras com 2+ condições
- [ ] DEVE/NÃO DEVE/PODE usados de forma consistente; sinônimos soltos eliminados
- [ ] Todo fluxo > 3 passos tem diagrama da categoria certa (ADR-0009) e passos numerados
- [ ] Toda regra tem sua verificação/auditoria declarada ao lado, não em outra seção
- [ ] Nenhum número medido sem a data (ou a delta) da medição — ilustração datada (mandamento 7)
