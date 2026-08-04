# delta-032 — bloco aninhado em item de lista chega inteiro ao pdf
Estado: arquivada · Data: 2026-08-04 · Branch: fix/032-bloco-aninhado-em-item · Tipo: bugfix

## Sintoma (≤3 linhas)
Tabela de decisão dentro de um `- RN-NNN` do §5 vira **texto com hífen literal** no pdf do cliente ([DT-009](../../DEBT.md), rodada IMEX de 2026-07-20, PRD do estoque RN-007/008); parágrafo aninhado **escapa do item** e renderiza como irmão. O contorno é manual, no "Erros comuns" da SKILL.md — depende de o operador lembrar, em documento que vai para cliente.

## Reprodução
- DADO um PRD com tabela aninhada colada num item (`- **RN-007** ...:` seguido de `  | Faixa | ... |`) QUANDO `tabela_cliente.py` roda e o resultado passa pelo python-markdown do caminho pdf ENTÃO as linhas da tabela viram texto literal dentro do `<li>`, com pipes e hífens visíveis — esperado: tabela renderizada dentro do item
- DADO a mesma tabela precedida de linha em branco, indentada com 2 espaços QUANDO o pipeline roda ENTÃO a tabela renderiza **fora** do item, como irmã — esperado: dentro do item
- DADO um parágrafo aninhado no item (linha em branco + 2 espaços) QUANDO o pipeline roda ENTÃO o parágrafo escapa do item — esperado: dentro do item
- DADO um §5 que **termina** em tabela aninhada QUANDO as seções são concatenadas ENTÃO o heading `## 6.` vira linha da tabela — o `splitlines()`/`join` do `deepen_indents` comia a linha em branco final da seção (achado do fim a fim desta delta, mesma família do seam já documentado para t6/t7)
- DADO um item `- RN-` colado **logo após** a tabela aninhada QUANDO o pipeline roda ENTÃO o item seguinte é engolido como célula da tabela e some da lista — esperado: item preservado (achado do review desta delta; é a forma exata do PRD de origem, RNs 007/008 consecutivas)
- Reproduzido em 2026-08-04 com o pipeline real (`transform()` + `markdown.markdown` com as mesmas extensões do `exporta_entregavel.py`); com 4 espaços **e** linha em branco, os três casos renderizam dentro do `<li>`

## Causa-raiz
Três causas independentes no `deepen_indents` ([tabela_cliente.py:121](../../skills/doc-entregavel/scripts/tabela_cliente.py)): (1) o match só casa bullet (`^( {2,})- `) — qualquer outro bloco aninhado mantém os 2 espaços do formato deltaspec, e o python-markdown exige 4 para o conteúdo pertencer ao item; (2) tabela aninhada precisa de linha em branco **dos dois lados** — colada no texto do item vira continuação literal mesmo com 4 espaços, e sem a linha de baixo ela engole o item seguinte como célula; (3) o `splitlines()`/`join` come o `\n` final — inclusive a linha em branco que separa a última tabela da seção do heading seguinte, que o python-markdown então engole como linha da tabela.

## Teste de regressão
- `tabela_cliente.py --selftest`: fixture no §5 com (a) tabela colada num item, (b) item seguinte colado na tabela, (c) parágrafo aninhado com linha em branco e (d) bloco cercado com linha interna indentada. Falha antes do fix e passa depois; a linha dentro da cerca permanece byte a byte; quatro mutações (match só de bullets, sem abertura de bloco, sem fechamento de bloco, `splitlines` de volta) quebram o teste.

## Mudanças
- nenhuma (correção sem mudança de requisito)

## Dependências e riscos
- O aprofundamento passa a valer para **toda** linha indentada fora de cerca. Linha com 4+ espaços que fosse code block indentado (sem cerca) ganharia indentação visível — a convenção do formato é cerca (```), risco aceito e declarado aqui.
- Marcador de cerca não é aprofundado e o conteúdo cercado não é tocado — o `fenced_code` do python-markdown só reconhece cerca na coluna 0, e mexer em conteúdo literal seria corrupção.
