# Markdown: cifrão de moeda

- **Cifrão de moeda é a entidade `&#36;`, colada ao prefixo da moeda** (`R&#36; 100`, `US&#36; 5`, `R&#36;/mês`): o `$` cru vira fórmula no pandoc quando há outro no mesmo parágrafo, e o `\$` vaza a contrabarra no python-markdown. Sem o prefixo a entidade não protege — o GitHub a decodifica antes de procurar fórmula. Dentro de trecho ou bloco de código, o `$` fica como está. Substitui regra anterior que mande escapar o cifrão com `\$`.
