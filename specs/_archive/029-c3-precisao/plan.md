<!-- resumo deltaspec · ≤15 linhas · única parte do plano lida pelo analyze e pelo humano -->
**Objetivo:** tirar do C3 as duas classes de falso positivo que travam commit em repo consumidor — seção lançada de changelog e sintaxe de link citada — sem perder a cobertura que a delta-027 ganhou. **Cobre:** R1 (da delta-029) **Decisões duráveis → ADRs:** nenhuma — os dois recortes executam a razão que o `EXCLUDE_LINKS_PADRAO` já declara (histórico imutável fora do C3), agora no nível certo de granularidade. **Riscos assumidos:** o recorte por conteúdo cega tudo abaixo do primeiro `## [X.Y.Z]`, mesmo se houver conteúdo vivo lá por engano.

## Desenho

Uma função nova, pura, entre a leitura do arquivo e o laço de links:

```python
CORTE_LANCADO = re.compile(r"^## \[\d+\.\d+\.\d+\]")   # Keep a Changelog: daqui pra baixo é imutável
CODE_SPAN = re.compile(r"`[^`]*`")                      # sintaxe citada, não referência
CERCA = re.compile(r"^\s*```")

def linhas_vivas(texto: str):
    """(nº, linha) das linhas em que um link é referência de verdade (delta-029)."""
```

O laço do C3 passa a iterar `linhas_vivas(texto)` em vez de `texto.splitlines()`. Nada mais muda: `scan_links`, `exclude_links_globs` e o corte do atalho do GitHub ficam como estão.

Separação I/O × lógica pura (regra canônica): `linhas_vivas` recebe e devolve texto, sem tocar disco — testável direto, sem subprocess.

## Passos (TDD)

1. **Vermelho.** Fixture no `selftest`: arquivo com `## [Não lançado]` contendo link morto **e** `## [1.0.0]` contendo outro → o assert exige exatamente **1** `[C3] link morto` (o da seção viva).
2. **Verde.** `CORTE_LANCADO` + `linhas_vivas` cortando na primeira seção lançada.
3. **Vermelho.** Fixture: link morto dentro de crase e dentro de bloco cercado → assert exige `PASS`; o mesmo link fora da crase, na linha seguinte, exige `FAIL`. As duas metades no mesmo caso, senão o teste passa por omissão.
4. **Verde.** `CODE_SPAN` removido da linha antes do `findall`; estado de bloco cercado alternando em `CERCA`.
5. **Regressão da delta-027:** as fixtures existentes continuam verdes — em especial a do atalho do GitHub e a do histórico imutável.
6. **Registrar:** DT-028 (progresso; quita no archive), CHANGELOG, HANDOFF.

## Verificação

- `validate_integrity.py --selftest` verde, cada fixture nova falhando antes do passo que a resolve.
- Mutação: remover o corte de seção, remover o de crase, e trocar `^## \[\d+\.\d+\.\d+\]` por `^## \[` (que engoliria `[Não lançado]`) — os três têm de quebrar o selftest.
- **Medição de aceite, no repo que originou o débito:** `validate_integrity.py ~/code/imex/imex-travelplanner` sai de 96 para **3** links mortos, e os 3 são os rot reais do README de lá.
- `validate_integrity.py .` neste repo continua `PASS`.
