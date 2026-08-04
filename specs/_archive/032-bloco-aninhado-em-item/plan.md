<!-- resumo deltaspec · ≤15 linhas · única parte do plano lida pelo analyze e pelo humano -->
**Objetivo:** bloco aninhado em item de lista (tabela, parágrafo) sobrevive ao caminho pdf — `deepen_indents` aprofunda todo conteúdo aninhado fora de cerca e abre linha em branco antes de tabela colada no item (quita o DT-009). **Cobre:** reprodução do spec (bugfix, sem Rn). **Decisões duráveis → ADRs:** nenhuma. **Riscos assumidos:** code block indentado sem cerca ganharia indentação visível — convenção do formato é cerca; declarado na spec.

## Desenho

`deepen_indents` ganha duas responsabilidades, na mesma passada e com estado de cerca:

1. **Aprofunda tudo que é aninhado:** o match muda de `^( {2,})- ` para `^( {2,})\S` — bullet, linha de tabela, parágrafo, citação. Dentro de cerca (```) nada é tocado.
2. **Abre bloco para tabela colada:** primeira linha de tabela aninhada (`|...`) cujo vizinho de cima não é vazio nem tabela recebe linha em branco antes — sem isso, mesmo com 4 espaços, o python-markdown a trata como continuação literal do item (reproduzido).

## Passos (TDD)

1. **Vermelho:** fixture no `SELFTEST_MD` — §5 com tabela colada num `- RN-`, parágrafo aninhado e cerca com linha interna indentada; asserts pela forma pós-fix (4 espaços, linha em branco antes da tabela, cerca intacta).
2. **Verde:** o `deepen_indents` novo.
3. **Regressão:** asserts existentes do selftest continuam verdes (sub-bullet 2→4, seções 6/7 intactas).
4. **Fim a fim:** o md da reprodução atravessa `transform()` + `markdown.markdown` e os três casos saem dentro do `<li>`.
5. SKILL.md: a linha do contorno manual em "Erros comuns" sai (o script passou a cobrir). CHANGELOG `[Não lançado]`, HANDOFF; quito do DT-009 no archive.

## Verificação

- `tabela_cliente.py --selftest` verde, com o vermelho registrado antes do fix.
- Mutação: reverter o match para `^( {2,})- ` e remover a inserção de linha em branco — cada uma quebra o selftest.
- `check_cycle.py specs/032-bloco-aninhado-em-item` sem ALTO/CRÍTICO; `validate_integrity.py .` PASS.
