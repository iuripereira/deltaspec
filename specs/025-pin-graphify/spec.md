# delta-025 — pin do graphify verificado por execução real
Estado: proposta · Data: 2026-08-02 · Branch: feat/025-pin-graphify · Perfil: completo — o R44 é requisito citado por projeto-alvo e a delta mexe no schema do `doc-profile.yaml`; errar aqui propaga (aprovado: 2026-08-02)

## Contexto (≤3 linhas)
A primeira adoção real do graphify ocorreu em 2026-08-02 no `imex-travelplanner`: 235 documentos indexados, 1.053 nós, 2.752 arestas.
O contrato do R44 foi escrito a partir da doc upstream, sem execução — a política de pins ainda declara "não testada" e o adapter afirma preferência por `--code-only` sem dizer o que esse modo deixa de ver.
A execução confirmou o contrato de proveniência e expôs duas lacunas que só o uso revela.

## Mudanças

### R1 — MUDA R44 (delta-016): graphify como 4º motor externo opcional, com pin verificado e escopo do `--code-only` explícito
- DADO um projeto-alvo com graphify instalado e habilitado no `doc-profile.yaml` QUANDO descoberta, specify/plan ou review rodam ENTÃO consultas `graphify query`/`path`/`explain` entram como insumo fundamentado com aresta citável `arquivo:linha`, e as tags `EXTRACTED`/`INFERRED`/`AMBIGUOUS` mapeiam no modelo `confirmado`/`inferido`/`lacuna` da descoberta (R25 — `AMBIGUOUS` → `lacuna`: requer validação humana)
- DADO o contrato do adapter QUANDO a delta consolida ENTÃO a tabela de `adapters.md` tem a linha do graphify com instalação manual consciente (nunca deixar `graphify install` — nem o alvo `graphify claude install` — escrever hook `PreToolUse`/CLAUDE.md, o que conflita com o harness) e pin na política de versões com verificação datada (R34)
- DADO o modo `--code-only` QUANDO ele é escolhido ENTÃO o adapter declara o que ele entrega (AST local por tree-sitter, determinístico, zero LLM, nada sai da máquina) **e o que ele cega** (todo arquivo não-código — `.md`, PDF, DOCX, XLSX, imagem — é pulado, e a tag `AMBIGUOUS` nunca aparece), para que a escolha do modo seja informada pelo perfil do projeto-alvo
- DADO graphify presente e habilitado QUANDO o eixo Spec do review roda ENTÃO pode consultar o impacto do diff (`graphify query`) como insumo do confronto Rn×diff — mesmo contrato e mesma degradação dos demais cenários
- DADO graphify ausente ou desabilitado QUANDO as fases rodam ENTÃO o fluxo atual (grep/Explore) segue com no máximo 1 linha de aviso — degradação graciosa (RNF2)

### R2 — ADICIONA: indexação de documentação sem expor conteúdo a terceiro, com backend registrado
- DADO um projeto-alvo cujo valor está na documentação (não no código) QUANDO o adapter orienta a indexação de docs ENTÃO ele registra que esse modo **exige um backend LLM** e nomeia os dois que não introduzem fronteira nova de confiança — `claude-cli` (assinatura Claude Code já em uso, sem API key) e `ollama` (local, nada sai da máquina) — como primeira escolha, antes de qualquer backend de API paga
- DADO o `doc-profile.yaml` de um projeto-alvo QUANDO `motores.graphify: true` e a indexação inclui arquivos não-código ENTÃO o campo `motores.graphify_backend` declara o backend escolhido; campo vazio ou ausente com indexação de docs pedida → a IA **para e pergunta**, nunca assume um default
- DADO indexação restrita a `--code-only` QUANDO o perfil é lido ENTÃO `motores.graphify_backend` é dispensável — não há backend LLM em jogo
- DADO um projeto-alvo com `publico.cliente: true` QUANDO a indexação de docs é proposta ENTÃO a escolha do backend é decisão explícita do usuário registrada no perfil, nunca default da IA

### R3 — ADICIONA: aresta do grafo para arquivo inexistente não vira fato
- DADO um grafo que indexou documentação QUANDO uma aresta cita um arquivo de código ENTÃO a existência do arquivo é verificada antes de o claim entrar em artefato do ciclo; arquivo inexistente marca o claim como `inferido` (código planejado descrito em spec), nunca `confirmado`

## Fora de escopo
- Tornar o graphify obrigatório ou habilitá-lo por default — segue opcional, `motores.graphify: false` no template (ADR-0014).
- **Mecanizar o R3** num check do `check_cycle.py` — renúncia decidida no clarify: acoplaria o gate determinístico a artefato de motor externo opcional, o oposto do que a ADR-0014 fixou (registro: ADR-0022).
- **Postura neutra sobre backends** ("só documentar, sem eleger") — renunciada no clarify em favor de recomendar + registrar (ADR-0022).
- Reavaliar o pin do `max` (gatilho próprio: delta-017, ADR-0012).

## Dependências e riscos
- Pin do graphify: **0.9.32**, verificado em 2026-08-02 por execução real no `imex-travelplanner` (release quase diária, bus factor = 1 — o risco de vida do projeto permanece na tabela).
- O `--code-only` desta execução rodou antes do modo completo; o incremental reaproveitou os 19 arquivos de código em cache, então o custo medido (2,7M tokens de entrada) é só dos 235 documentos.
- A estimativa prévia de tokens errou por 4,7× (576k projetados × 2,7M reais): o cap de 20k/arquivo não conta o system prompt repetido por chunk. Em backend pago isso muda a ordem de grandeza do custo.
