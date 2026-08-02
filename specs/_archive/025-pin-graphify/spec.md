# delta-025 — pin do graphify verificado por execução real
Estado: arquivada · Data: 2026-08-02 · Branch: feat/025-pin-graphify · Perfil: completo — o R44 é requisito citado por projeto-alvo e a delta mexe no schema do `doc-profile.yaml`; errar aqui propaga (aprovado: 2026-08-02)

## Contexto (≤3 linhas)
A primeira adoção real do graphify ocorreu em 2026-08-02 no `imex-travelplanner`: 235 documentos indexados, 1.053 nós, 2.752 arestas.
O contrato do R44 foi escrito a partir da doc upstream, sem execução — a política de pins ainda declara "não testada" e o adapter afirma preferência por `--code-only` sem dizer o que esse modo deixa de ver.
A execução confirmou o contrato de proveniência e expôs três lacunas que só o uso revela.

## Mudanças

### R1 — MUDA R44 (delta-016): graphify como 4º motor externo opcional, com pin verificado, escopo de modo e backend registrado
<!-- bloco único por decisão do clarify (2026-08-02): o contrato do motor é UM requisito; fragmentar em Rn novos multiplica artefato a gerenciar sem ganhar verificabilidade -->
- DADO um projeto-alvo com graphify instalado e habilitado no `doc-profile.yaml` QUANDO descoberta, specify/plan ou review rodam ENTÃO consultas `graphify query`/`path`/`explain` entram como insumo fundamentado com aresta citável `arquivo:linha`, e as tags `EXTRACTED`/`INFERRED`/`AMBIGUOUS` mapeiam no modelo `confirmado`/`inferido`/`lacuna` da descoberta (R25 — `AMBIGUOUS` → `lacuna`: requer validação humana)
- DADO o contrato do adapter QUANDO a delta consolida ENTÃO a tabela de `adapters.md` tem a linha do graphify com instalação manual consciente (nunca deixar `graphify install` — nem o alvo por plataforma `graphify claude install` — escrever hook `PreToolUse`/CLAUDE.md, o que conflita com o harness) e pin na política de versões com verificação datada (R34)
- DADO a escolha do modo de indexação QUANDO o adapter é lido ENTÃO ele declara o que `--code-only` entrega (AST local por tree-sitter, determinístico, zero LLM, nada sai da máquina) **e o que ele cega** (todo arquivo não-código — `.md`, PDF, DOCX, XLSX, imagem — é pulado, e a tag `AMBIGUOUS` nunca aparece), para que projeto-alvo cujo valor está na documentação não escolha o modo cego por default
- DADO que a indexação inclui arquivos não-código QUANDO o backend LLM é escolhido ENTÃO o adapter nomeia como primeira escolha os dois que não criam fronteira nova de confiança — `claude-cli` (CLI já autenticado, cobrado na assinatura, sem API key) e `ollama` (`localhost`, nada sai da máquina) — a escolha fica registrada em `motores.graphify_backend` do `doc-profile.yaml`, e campo vazio com indexação de docs pedida faz a IA **parar e perguntar**, nunca assumir default; em `--code-only` o campo é dispensável
- DADO um grafo que indexou documentação QUANDO uma aresta cita um arquivo de código ENTÃO a existência do arquivo é conferida antes de o claim entrar em artefato do ciclo; arquivo inexistente marca o claim como `inferido` (código planejado descrito em spec), nunca `confirmado`
- DADO graphify presente e habilitado QUANDO o eixo Spec do review roda ENTÃO pode consultar o impacto do diff (`graphify query`) como insumo do confronto Rn×diff — mesmo contrato e mesma degradação dos demais cenários
- DADO graphify ausente ou desabilitado QUANDO as fases rodam ENTÃO o fluxo atual (grep/Explore) segue com no máximo 1 linha de aviso — degradação graciosa (RNF2)

## Fora de escopo
- Tornar o graphify obrigatório ou habilitá-lo por default — segue opcional, `motores.graphify: false` no template (ADR-0014).
- Mecanizar a regra do arquivo inexistente num check do `check_cycle.py` (ADR-0022).
- Postura neutra sobre backends — "só documentar, sem eleger" (ADR-0022).
- Reavaliar o pin do `max` (gatilho próprio: delta-017, ADR-0012).

## Dependências e riscos
- Pin do graphify: **0.9.32**, verificado em 2026-08-02 por execução real no `imex-travelplanner` (release quase diária, bus factor = 1 — o risco de vida do projeto permanece na tabela).
- O `--code-only` desta execução rodou antes do modo completo; o incremental reaproveitou os 19 arquivos de código em cache, então o custo medido (2,7M tokens de entrada) é só dos 235 documentos.
- A estimativa prévia de tokens errou por 4,7× (576k projetados × 2,7M reais): o cap de 20k/arquivo não conta o system prompt repetido por chunk. Em backend pago isso muda a ordem de grandeza do custo.
- O campo `motores.graphify_backend` nasce só no template deste repo; a propagação ao CLAUDE.md distribuído segue a mesma dívida do DT-022.
