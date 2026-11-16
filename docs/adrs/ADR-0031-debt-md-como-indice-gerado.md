# ADR-0031: DEBT.md da raiz é índice gerado dos ativos — projeção, nunca fonte

- **Status:** Accepted (2026-08-11, delta-047)
- **Data:** 2026-08-11
- **Supersedes:** [ADR-0030](ADR-0030-registro-de-debitos-em-pasta-na-raiz.md) — **apenas na cláusula 4** ("ponteiro fino"): o `DEBT.md` deixa de ser ponteiro de 3 linhas e passa a carregar o índice gerado dos ativos. Tudo o mais da 0030 (pasta `debts/` dona, um arquivo por item, quitação por `git mv`, "nunca deletado") segue vigente.
- **Superseded by:** —

## Context

Horas depois da delta-043, o Iuri pediu utilidade real para o `DEBT.md` da raiz: um índice dos ativos agrupado por urgência (Críticos/Importantes/Médios/Não urgentes), em vez do ponteiro. A cláusula "Reabre quando" da ADR-0030 previu exatamente esta discussão — "aí a discussão é agrupamento/**índice gerado**" — e disparou por decisão de produto, não por volume.

A tensão é com a ADR-0020 ("score derivado e **nunca gravado**") e com a regra de ouro: um índice mantido à mão seria a mesma duplicação que a 0030 acabou de matar na tabela `## Arquivados`, e um índice com ordenação por score materializa valor derivado. O precedente que resolve já existe no repo: o `tickets.json` materializa o score desde a delta-023 sob a doutrina da ADR-0021 — **projeção não é fonte**; regenera-se do registro e, em divergência, o registro governa.

## Decision

1. **O `DEBT.md` da raiz é uma projeção gerada** por `debito.py indice`, com cabeçalho declarando "GERADO — não edite à mão". Editar o índice não muda item nenhum; a fonte segue sendo `debts/ativos/`.
2. **Agrupamento por valor gravado, zero limiar novo:** `Críticos` = override com prazo (impedimento) · `Importantes` = J9 · `Médios` = J3 · `Não urgentes` = J1 · `Sem triagem` = pontuável sem `fila` (caso dos consumidores recém-migrados) · `Guardas` ao fim. Trilha é marca na linha. Ordem interna = score decrescente **calculado na geração** — materializado como projeção, nunca como registro.
3. **`stale` fica fora do índice** — é marca temporal; num arquivo gerado ela apodreceria no dia seguinte. Vive só na saída viva do `fila`.
4. **Frescor por processo + aviso mecânico:** regenerar é passo do cadastro e da quitação (`debts/README.md`); `debito.py fila` compara o render atual com o arquivo (string, sem parsear o índice) e **avisa** quando divergem, sem mudar o exit — drift nunca é silencioso.
5. **`migrar` escreve o índice** no lugar do ponteiro — repo convertido já nasce com a visão.
6. **O C3 confere o índice de graça:** cada item é link relativo para o arquivo real, e o `DEBT.md` já está no escopo de links do `validate_integrity.py`.

## Alternativas recusadas

- **Índice mantido à mão** (o formato que o pedido esboçou): recusado — segunda fonte da verdade, dessincroniza a cada abertura/quitação; é a classe de duplicação que a ADR-0030 eliminou.
- **Bandas por faixa de score** (crítico = score ≥ N): recusado — exigiria limiares novos sem base empírica (DT-020); o eixo J já gravado dá as três bandas sem julgamento novo.
- **Regeneração no hook pre-commit:** recusado — o hook versionado hoje só valida; passar a escrever arquivo dentro dele muda o contrato por um ganho que o aviso do `fila` já entrega.
- **Timestamp e defasagem aceita** (regenera quem lembrar): recusado — sem cobrança mecânica, o índice viraria mentira educada em semanas.

## Consequences

- O `DEBT.md` ganha leitor de novo (visão de urgência no GitHub sem rodar script), ao custo de um passo de regeneração no processo — cobrado pelo aviso do `fila` quando esquecido.
- A ADR-0020 permanece intacta: o registro (`debts/ativos/`) continua sem score gravado; o que o índice materializa é projeção regenerável, mesma classe do `tickets.json`.
- Consumidores recém-migrados enxergam a própria pauta de triagem na seção `Sem triagem` — o índice vira o convite para triar.
- Reabre quando: o render precisar de julgamento que não esteja gravado nos eixos (aí a discussão é modelo, ADR-0020), ou o aviso de drift se provar insuficiente e a regeneração pedir mecanização (hook/CI — espírito do DT-031).
