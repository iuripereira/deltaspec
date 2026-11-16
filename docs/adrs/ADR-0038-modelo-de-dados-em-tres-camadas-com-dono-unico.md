# ADR-0038: Modelo de dados em três camadas com dono único, ERD derivado do contrato e gate que nasce ALTO

- **Status:** Accepted (2026-08-20, delta-073)
- **Data:** 2026-08-20
- **Supersedes:** —
- **Superseded by:** —

## Context

O deltaspec não tinha artefato de modelo de dados. A categoria `modelo-dados` do `doc-profile.yaml` ([ADR-0009](ADR-0009-documentacao-visual-gate-configuravel.md)) produzia apenas um `schema.dbml` solto: sem camada conceitual que dissesse o que cada entidade **é** e por que se relaciona, sem gate que verificasse coerência, e com um `DATA_DICTIONARY.md` de 13 linhas que nenhuma skill consumia — sem definição de negócio, domínio de valores, steward, sensibilidade nem origem, documentação decorativa (lacuna já registrada na [ADR-0011](ADR-0011-deps-toml-metadados-de-validacao.md)).

O benchmark feito em 2026-08-20 sobre seis frameworks SDD da comunidade (GitHub Spec Kit, OpenSpec, Kiro, cc-sdd, AWS AI-DLC e BMAD v6 — fontes primárias, registradas no prompt de planejamento da delta) mostrou que **nenhum valida dados deterministicamente**: o Spec Kit nomeia um `data-model.md` e só confere `is_file()`; o OpenSpec tem gate forte e é cego a dados; Kiro e cc-sdd embutem o modelo no design doc sem formato exigido; o AI-DLC tem a melhor semântica, mas em prosa e com gate humano; o BMAD tem lint determinístico do spine e nada sobre dados. A vaga de diferencial é real.

Duas forças em tensão. A **regra de ouro do repositório** (cada informação tem um dono canônico) empurra contra o artefato único que "contém tudo": estrutura, significado e contrato são informações de naturezas diferentes, escritas por pessoas diferentes, em momentos diferentes. Já a **economia de tokens** (RNF1) empurra contra multiplicar arquivos e contra gate que exija cerimônia em projeto que não persiste dados.

## Decision

**O modelo de dados tem três camadas, e cada camada tem exatamente um arquivo dono.** O `docs/diagrams/schema.dbml` é dono do contrato executável (camada 3 — já canônico pela ADR-0009). O `docs/data-model.md` é dono da camada conceitual (camada 1: propósito na linguagem ubíqua, agregado, relações com o porquê, invariantes) e carrega um ERD Mermaid **derivado** do `.dbml`. O `DATA_DICTIONARY.md` é dono da semântica por campo (camada 2: definição de negócio, domínio de valores, steward, sensibilidade, origem, qualidade — um ISO/IEC 11179-lite). O `data-model.md` cobre as três camadas por composição e link, não por conter. A distinção que separa as camadas 1 e 2: o modelo responde "como as coisas se relacionam"; o dicionário responde "o que exatamente é este campo, quem é dono, o que é valor válido, de onde veio".

**O ERD é derivado, nunca editado, e o gate o confere byte a byte.** A informação flui numa direção só — `.dbml → erDiagram` — respeitando a unidirecionalidade já decidida para a camada de apresentação ([ADR-0029](ADR-0029-apresentacao-como-modo-e-html-autocontido-canonico.md)): o fonte versionado governa. O gerador é determinístico (mesma entrada, mesmos bytes), o que torna o check de drift uma comparação de strings em vez de um juízo. Significado, invariante e renúncia não são deriváveis do contrato e por isso nascem na camada 1 — não há mão dupla.

**Os checks de dados nascem com severidade máxima ALTO, nunca CRÍTICO, e a promoção exige ADR nova.** ALTO já bloqueia o PR (exit 1); a diferença é de **discurso**: CRÍTICO é reservado no framework para perda de requisito e violação de regra canônica, achados que não admitem ressalva. Um gate que nasce sem uso real em projeto consumidor não ganhou esse direito. Gatilho de promoção: cerca de cinco deltas de uso real em projetos consumidores sem falso positivo acusado — medido nos handoffs e nos débitos, não estimado.

**A camada 2 reusa o vocabulário de confiança do framework** (`confirmado`/`inferido`/`lacuna`, da skill `descoberta`) em vez de importar a taxonomia do 11179 — o vocabulário já existe, já é compreendido e já é produzido pela mineração de insumos.

**O gate é script próprio da skill (`check_data_model.py`), não um check novo do `check_cycle.py`.** É verificação de artefato vivo do projeto, não por delta; não toca `PERFIL_NUCLEO` nem as fixtures do C11; segue o padrão de selftest co-localizado de `audit_workspace.py` e `gera_excalidraw.py`. A delta-074 estende o mesmo script com os checks da camada 2.

Renunciamos, com o porquê:

- **Registro ISO/IEC 11179 completo** (conceito de dado, elemento, domínio de valores, esquema de classificação, administração de registro): a carga de metadados supera em ordem de grandeza o que um projeto do ciclo sustenta; ficam as dimensões que têm consumidor real (definição, domínio, steward, sensibilidade, origem, qualidade).
- **ISO/IEC 21838 (ontologia de topo)**: resolve interoperabilidade entre ontologias, problema que nenhum projeto consumidor tem.
- **dbt semantic layer / MetricFlow**: acoplaria o framework a uma stack de dados específica; a camada semântica daqui é texto em Markdown, lido por gente e por gate.
- **JSON Schema como fonte da camada 3**: o DBML já é a ferramenta decidida pela ADR-0009 e é mais legível para modelar; JSON Schema/DDL ficam como **export derivado** futuro — e a validação real exigiria a lib `jsonschema`, dependência nova que pede ADR própria sob a régua da [ADR-0023](ADR-0023-pyyaml-como-dependencia-admitida.md).
- **Detecção de breaking change de esquema** (campo removido, tipo estreitado, `not null` adicionado entre duas versões do `.dbml`): diferencial real e ausente em todos os frameworks comparados, mas é um segundo produto; vira débito roteado no archive da delta-073, com contrato já esboçado (stdlib, saída JSON com exit 0, política no chamador).
- **Modelo embutido no design doc à la Kiro/cc-sdd**: um arquivo que mistura arquitetura, modelo e decisões tem três donos num lugar só — exatamente o que a regra de ouro proíbe. A separação por dono venceu.

## Consequences

Fica mais fácil: drift entre diagrama e contrato deixa de existir como classe de bug — o ERD é regenerado, e o gate acusa quando alguém o editou à mão. Órfão entre o conceitual e o contrato (entidade descrita sem tabela, tabela sem descrição) vira achado mecânico em vez de descoberta em revisão. A camada 2 ganha um lugar e um gate próprios na delta-074 sem reabrir esta decisão.

Fica mais difícil: são três arquivos para manter onde antes havia um `.dbml` opcional. A mitigação é o perfil — o gate só exige `data-model.md` quando `modelo-dados` é obrigatório no `doc-profile.yaml`, e se omite com uma linha no resto (RNF2). O parser DBML é um subconjunto por regex (`Table`, colunas, `pk`, `ref:`/`Ref:`); `.dbml` real fora dele cai em M1 como falso positivo, e ampliar o subconjunto é PATCH sem ADR.

Trade-off aceito: o heading da entidade no `data-model.md` usa o nome físico da `Table`, não o nome de negócio — é o que torna o M2 um set-diff honesto. O nome de negócio vive na frase de propósito, e um alias explícito é extensão possível quando a delta-074 trouxer o nome canônico por campo.

<!--
Imutável após "Accepted". Mudou a decisão? Crie uma NOVA ADR com "Supersedes ADR-0038" e marque esta como "Superseded by ADR-YYYY". Nunca reescreva uma ADR aceita. Atualize o índice docs/adrs/README.md no mesmo PR. -->
