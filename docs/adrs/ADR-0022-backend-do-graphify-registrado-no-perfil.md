# ADR-0022: Backend de indexação de docs do graphify é recomendado e registrado no doc-profile, não mecanizado no gate

- **Status:** Accepted (2026-08-02, delta-025)
- **Data:** 2026-08-02
- **Supersedes:** —
- **Superseded by:** —

## Context

A ADR-0014 contratou o graphify como 4º motor externo opcional a partir da doc upstream, sem execução: a política de pins registrava "não testada" e o contrato preferia `--code-only` ("determinístico, zero LLM") sem declarar o que esse modo deixa de ver.

A primeira adoção real, em 2026-08-02 no `imex-travelplanner` (graphify 0.9.32), produziu três fatos que o contrato escrito da doc não previa:

1. **`--code-only` cega a documentação.** A execução reportou `skipping 235 non-code file(s) (222 docs, 5 papers, 8 images)`. Num projeto-alvo com 5.235 linhas de código e 210 markdowns, o modo preferido pelo contrato indexava justamente a parte fria do repositório. A tag `AMBIGUOUS` — que o R44 mapeia em `lacuna` — **nunca aparece** nesse modo: só surgiu (13 arestas) quando os docs entraram.
2. **Indexar docs exige backend LLM**, e os nove disponíveis não são equivalentes em exposição. Dois não introduzem fronteira nova de confiança: `claude-cli` (roteia pelo CLI já autenticado, cobrado na assinatura, sem API key) e `ollama` (`localhost`, nada sai da máquina). Os demais mandam o corpus para um terceiro — no projeto-alvo em questão, `publico.cliente: true`, isso incluiria contrato, proposta comercial e relatório de custos.
3. **O grafo cita código que não existe.** Dos 27 arquivos de código referenciados, 16 são fantasmas (`apps/api/src/imex/core/policy.py`, ...): as specs descrevem implementação ainda não escrita, e o extrator criou o nó do alvo citado. Não é defeito do motor — é retrato fiel de um projeto documentado à frente do código.

Duas decisões tinham alternativa real.

**1 — Postura sobre backends.** (a) Só documentar que o modo docs exige LLM e listar os backends, sem eleger nenhum — neutro, não envelhece recomendando ferramenta que muda; (b) recomendar `claude-cli`/`ollama` como primeira escolha; (c) recomendar **e** exigir que a escolha fique registrada no `doc-profile.yaml` do projeto-alvo.

**2 — Regra do arquivo fantasma.** (a) Lição datada no `DEBT.md`, sem vincular projeto-alvo; (b) requisito no contrato do adapter, verificado na leitura; (c) requisito **mais** check no `check_cycle.py` validando existência dos arquivos citados.

## Decision

Decididas com o usuário em 2026-08-02 (clarify da delta-025): **1-c e 2-b.**

O adapter recomenda `claude-cli` e `ollama` antes de qualquer API paga, e o `doc-profile.yaml` ganha `motores.graphify_backend` — obrigatório quando a indexação inclui não-código, dispensável em `--code-only`. Campo vazio com indexação de docs pedida faz a IA **parar e perguntar**, nunca assumir default. Renunciamos à neutralidade (1-a) porque o silêncio do contrato é que produziu o risco: sem recomendação nomeada, o caminho de menor esforço é a primeira API key que estiver no ambiente, e o dado do cliente vaza por omissão. Renunciamos a (1-b) puro porque recomendação sem registro não sobrevive à troca de sessão — o próximo agente não sabe o que foi decidido.

A regra do arquivo fantasma entra como requisito de leitura do adapter: aresta que cita arquivo inexistente marca o claim como `inferido`, nunca `confirmado`. Renunciamos a mecanizá-la (2-c) porque o check acoplaria o gate determinístico a um artefato de motor externo **opcional** — o `check_cycle.py` passaria a depender da presença de `graphify-out/graph.json`, exatamente o acoplamento que a ADR-0014 recusou ao manter o `tasks.md` dono do grafo de execução. Renunciamos à lição solta (2-a) porque ela não vincula projeto-alvo nenhum.

## Consequences

**Fica mais fácil:** a escolha de modo passa a ser informada — quem lê o adapter sabe que `--code-only` é cego para docs antes de rodar, não depois; projeto com documentação sensível tem um caminho nomeado que não exporta nada; a decisão de backend sobrevive à sessão porque mora no perfil; claim sobre código planejado não entra em artefato como fato consumado.

**Fica mais difícil:** o `doc-profile.yaml` ganha um campo — todo projeto-alvo que ligar o graphify para docs precisa declará-lo, e o template distribuído tem que propagar (mesma dívida de propagação do DT-022); a recomendação de backend é datada por natureza e envelhece com o upstream, que tem release quase diária e bus factor = 1; a regra do fantasma depende de disciplina de leitura, sem gate que a cobre — se falhar em delta real, (2-c) volta à mesa por nova ADR.
