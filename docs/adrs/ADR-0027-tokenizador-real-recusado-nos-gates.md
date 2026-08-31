# ADR-0027: tokenizador real (tiktoken) recusado nos gates — a heurística stdlib mede melhor o que importa

- **Status:** Accepted (2026-08-09, delta-040)
- **Data:** 2026-08-09
- **Supersedes:** —
- **Superseded by:** —

## Context

O DT-035 pediu que o C5 do `check_cycle.py` medisse o `TRUTH.md` em tokens, não em linhas, e propôs a heurística `len(texto)//3` da stdlib. No clarify da delta-040 a pergunta natural apareceu: por que aproximar, se existe tokenizador de verdade? Revogar a [ADR-0023](ADR-0023-pyyaml-como-dependencia-admitida.md) e admitir o `tiktoken` como segunda dependência resolveria a calibração de uma vez.

A alternativa foi medida, não estimada. Instalação real do `tiktoken` 0.13.0 em ambiente limpo, em 2026-08-09, contra o `specs/TRUTH.md` deste repositório (67.445 caracteres, 339 linhas):

| Método | Tokens | Desvio vs. cl100k |
|---|---|---|
| `tiktoken` cl100k_base | 20.631 | — |
| `tiktoken` o200k_base | 18.398 | −11% |
| `len//3` (stdlib) | 22.481 | +9% |
| `len//2.5` (stdlib) | 26.978 | +31% |

Quatro fatos saíram da medição.

1. **A heurística stdlib já acerta dentro de 9%**, e erra para o lado de acusar cedo — que é o lado seguro para um gate cujo modo de falha é o context rot silencioso.
2. **Os dois encodings do próprio `tiktoken` divergem 11% entre si**, e nenhum deles é o tokenizador do Claude, que é quem de fato lê o `TRUTH.md`. A precisão oferecida é precisão do modelo errado; para um limiar cuja unidade é a dezena de milhar, 9% não muda decisão nenhuma.
3. **Não é uma dependência, são sete**: `tiktoken` arrasta `regex`, `requests`, `urllib3`, `certifi`, `idna` e `charset-normalizer` — 23 MB de `site-packages`. O RNF6 não diz "poucas dependências", diz **exatamente uma**, e o C1/C2 do `validate_integrity.py` verifica isso mecanicamente contra o `deps.toml`.
4. **O gate passaria a fazer I/O de rede.** Com o cache vazio, `get_encoding()` baixou os arquivos BPE de um blob remoto — 68 segundos no caso do `o200k_base`. O `check_cycle.py` roda em pré-commit e em máquina offline; um gate determinístico que depende de rede na primeira execução por máquina deixa de ser determinístico, e contradiz a [ADR-0001](ADR-0001-tudo-roda-na-sua-maquina.md).

A medição também corrigiu um erro de origem: o DT-035 registrava "~29k tokens" para o `TRUTH.md`, número que não reproduz por nenhum método medido aqui (+40% sobre o cl100k) e que quase induziu um divisor 31% mais conservador que o necessário.

## Decision

**Recusamos o tokenizador real nos gates. O C5 mede tokens por heurística stdlib, com divisor ancorado nesta medição e citado no código.** A ADR-0023 permanece vigente e intacta: `PyYAML` segue sendo a única dependência externa admitida.

Renunciamos ao `tiktoken` não por conservadorismo com dependências, mas porque **ele não entrega o que a proposta prometia**: a contagem exata seria de um tokenizador que não é o do consumidor real do arquivo, com dispersão entre encodings (11%) maior que o erro da heurística que ele substituiria (9%). Trocar sete pacotes, 23 MB e uma dependência de rede por uma precisão que é falsa na terceira casa é pagar caro por um número mais bonito, não por uma decisão melhor.

O corolário para o framework: **medir a alternativa é mais barato que argumentar sobre ela.** A instalação descartável que produziu a tabela acima levou minutos e inverteu a recomendação que estava na mesa — inclusive a do próprio agente, que havia recomendado `len//2.5` com base no número errado do DT-035.

## Consequences

**Fica mais fácil:** o `check_cycle.py` continua rodando com stdlib + PyYAML, offline, em pré-commit e em qualquer projeto consumidor sem passo de instalação novo; o RNF6 e os quatro espelhos da política de dependência ficam intocados; a delta-040 permanece pequena — muda um check, não a política de dependências do framework.

**Fica mais difícil:** o número do C5 é aproximado por design e será perguntado de novo por quem chegar depois — por isso o divisor carrega a proveniência da medição como comentário no código, e não um valor solto. Se o limiar de tokens vier a governar decisão de maior consequência que "particione o TRUTH", a aproximação volta à mesa.

**Reabre quando:** a stdlib do Python ganhar tokenizador; ou a Anthropic publicar um tokenizador local, offline e sem transitivos para o modelo que consome os artefatos — aí a precisão passaria a ser do consumidor certo e a conta muda; ou o limiar em tokens passar a governar decisão em que 10% de erro importe.
