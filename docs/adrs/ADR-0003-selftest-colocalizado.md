# ADR-0003: Verificação co-localizada — todo gate carrega o próprio `--selftest`

- **Status:** Accepted
- **Data:** 2026-07-18
- **Supersedes:** —
- **Superseded by:** —

## Context

> Registrada retroativamente em 2026-07-19, no backfill de ADRs da varredura de registros.
> A decisão vige desde o PR #2 e foi formalizada como RNF4 na delta-002.

O framework ganhou gates determinísticos em Python (`check_cycle.py` no PR #2, depois
`validate_integrity.py`). São scripts de ~250–300 linhas, stdlib pura, distribuídos **dentro das
skills** (`skills/<nome>/scripts/`). Um gate sem teste apodrece calado: um refactor que quebre um
check silenciosamente transforma o gate em teatro.

Alternativas consideradas:

1. **Diretório `tests/` + framework de teste** (pytest): estrutura convencional, cobertura fina.
2. **Sem testes automatizados**, confiando na validação de convenções do CI.
3. **`--selftest` embutido em cada script**, com fixtures inline, executado pelo job `ci`.

## Decision

Adotamos a alternativa 3: **cada script de gate carrega o próprio `--selftest` com fixtures**, e o
CI deste repositório executa todos (RNF4: 100% dos scripts expõem `--selftest`; o C4 é coberto com
repositório git real).

Renunciamos ao diretório de testes (1) porque ele traria a primeira dependência externa do
framework (pytest) e uma estrutura paralela para exatamente dois arquivos — infraestrutura
desproporcional, e o script deixaria de ser autocontido: a skill é copiada/instalada como unidade,
e o teste que mora fora dela se perde na distribuição. Renunciamos ao "sem testes" (2) porque gate
é código de segurança do ciclo: é a última coisa que pode quebrar calada.

## Consequences

**Fica mais fácil:** o script é autocontido e portável com a skill (teste viaja junto); rodar a
verificação é um comando sem setup (`python3 <script> --selftest`); zero dependência nova — os
gates seguem só com `re`, `pathlib`, `subprocess`, `tomllib`.

**Fica mais difícil:** fixtures inline engordam o arquivo do script; não há parametrização,
cobertura por linha nem relatório de falha rico. Para dois scripts, o custo é aceito.

**Reabre quando:** os scripts de gate se multiplicarem além do punhado, ou as fixtures passarem a
dominar o arquivo (sinal: mais linhas de fixture que de lógica). Aí um diretório de testes com
framework vira a candidata natural, e esta ADR é substituída — não editada.
