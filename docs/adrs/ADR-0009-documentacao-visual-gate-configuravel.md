# ADR-0009: Documentação visual como gate configurável — a decisão é obrigatória, os diagramas não

- **Status:** Accepted (2026-07-28, delta-013) <!-- promovida com a evidência do piloto doc-profile+doc-entregavel nos 4 repos IMEX (8 exports, 2026-07-20); o check mecânico do doc-profile permanece adiado — pendência roteada na delta-013; a delta externa com gate do specify segue como gatilho do DT-004 -->
- **Data:** 2026-07-20
- **Supersedes:** —
- **Superseded by:** —

## Context

A documentação visual (arquitetura, modelo de dados, fluxos, casos de uso) ficava fora do ciclo: cada projeto decidia ad hoc se e quando diagramar, e o resultado era inconsistência — projetos com entregável contratual (PRD/contrato assinado pelo cliente, como nos projetos IMEX) precisam de diagramas congelados em PDF/DOCX, enquanto projetos internos precisam no máximo de Mermaid inline vivo junto do código. Duas forças em tensão:

- **RNF1 (economia de tokens)** empurra contra gerar diagramas por default — artefato não pedido é custo puro.
- **Entregável cliente** empurra a favor de completude e fidelidade visual — um PRD assinável sem o diagrama de arquitetura ou o modelo de dados é entregável incompleto, e o custo de errar aqui é jurídico/comercial, não técnico.

Há ainda a distinção de natureza: documentação **interna** é viva (mantida a cada mudança relevante, renderiza nativa no GitHub/Obsidian); documentação **cliente** é congelada (exportada em momento definido, versionada, re-assinada a cada baseline — padrão já praticado nos contratos IMEX, cláusula 1.3.1).

Alternativas consideradas:

1. **Tudo obrigatório:** todo projeto gera arquitetura + modelo de dados + fluxos + casos de uso na spec. Viola o RNF1 no caso comum (projeto interno sem necessidade) e trata igual o que é desigual.
2. **Tudo opcional (status quo):** nada muda; diagramas surgem quando alguém lembra. O furo não é a falta de diagrama — é a falta de *decisão registrada*: ninguém sabe se o projeto não tem diagramas por escolha ou por esquecimento.
3. **Gate configurável:** o que é obrigatório é a **decisão consciente**, registrada num perfil declarativo por projeto (`doc-profile.yaml`); os diagramas são consequência do perfil, nunca improvisados.

## Decision

Adotamos a alternativa 3: **todo projeto com ciclo toma uma decisão registrada sobre documentação visual; a implementação é o `doc-profile.yaml`.** O perfil responde PARA QUEM (interno e/ou cliente), O QUÊ (arquitetura, modelo de dados, fluxos, casos de uso), COM QUÊ, QUANDO E ONDE (ferramenta, fase, pasta de saída). O `projeto-init` gera o perfil default no scaffold; na fase de spec o agente lê o perfil e gera **somente** o que está declarado como obrigatório, perguntando antes de gerar qualquer coisa fora dele. Projeto sem diagramas é perfil válido — com justificativa registrada. Ausência do arquivo = comportamento anterior, com warning sugerindo criar o perfil (compatibilidade: nenhum projeto existente quebra).

Stack padrão diagram-as-code (CLIs via bash), **uma ferramenta por categoria**:

| Categoria | Ferramenta | Observação |
|---|---|---|
| Fluxogramas / sequência / ERD rápido | **Mermaid** (`.mmd`) | renderiza nativo no GitHub/Obsidian, custo baixo de tokens — default |
| Modelo de dados canônico | **DBML** (`schema.dbml` → dbml-renderer) | default |
| Arquitetura de alto nível / C4 formal | **Structurizr DSL** (`.dsl`) | opcional por projeto |
| Arquitetura visual moderna | **D2** (`.d2`) ou **Excalidraw** (`.excalidraw`) | opcional por projeto |
| UML formal e casos de uso | **PlantUML** (`.puml`) | opcional por projeto |
| Diagramas explicativos (regras, conceitos) | **Excalidraw** (`.excalidraw`) | opcional por projeto |

**A ferramenta segue a categoria — vínculo normativo:** um diagrama pertence a uma categoria e usa a ferramenta dela. **Não reaproveite um diagrama existente de outra categoria/ferramenta** só porque já está pronto: arquitetura C4 desenhada em Mermaid, por exemplo, é migrada para Structurizr DSL quando a categoria dela é arquitetura formal. O reuso cross-categoria foi o modo de falha observado no piloto (todos os conceitos diagramados na mesma ferramenta por inércia).

**Exceção ao RNF1, registrada aqui:** documentação **cliente** é entregável jurídico — completude e fidelidade dominam, economia de tokens **não se aplica** (a renderização é via CLI; o custo de tokens é marginal). Documentação **interna** segue o RNF1 integralmente: defaults enxutos (arquitetura + modelo de dados na spec; fluxos e casos de uso sob demanda), Mermaid inline, nada fora do perfil. A formalização como MUDA RNF1 no TRUTH.md entra na consolidação da delta que validar o piloto.

Para o entregável congelado nasce a skill **`doc-entregavel`**: renderiza os diagramas do perfil (mmdc/dbml-renderer → SVG/PNG), monta o documento final com capa de assinatura parametrizada e exporta PDF/DOCX em `docs/entregaveis/` — generalização do pipeline já validado nos 4 PRDs + 4 contratos IMEX (pypandoc + python-docx para DOCX; markdown → HTML+CSS → chrome headless para PDF). Nova baseline = novo arquivo versionado = nova assinatura; entregável nunca é sobrescrito.

Renunciamos a (1) porque obrigatoriedade uniforme gera diagrama-cerimônia que ninguém mantém — o oposto de documentação viva. Renunciamos a (2) porque a ausência de decisão é indistinguível de esquecimento, e o custo de descobrir tarde (na entrega ao cliente) é o mais alto. Renunciamos também a um check mecânico no `check_cycle.py` por ora: validar presença/schema do YAML é mecanizável, mas o perímetro (ADR-0006) manda mecanizar depois que o formato estabilizar no piloto — heurística antes disso produziria falso LIBERADO.

## Consequences

**Fica mais fácil:** a decisão sobre documentação visual tem dono e data; o agente tem instrução determinística (ler o perfil, gerar só o declarado); o entregável cliente sai por pipeline reprodutível em vez de exportação manual; projetos internos continuam enxutos por default.

**Fica mais difícil:** mais um arquivo no scaffold (`doc-profile.yaml`) e mais uma skill para manter; o perfil pode divergir da prática (declarar obrigatório e não manter) — o gate cobre a geração na spec, não a manutenção contínua; a stack de CLIs opcionais (plantuml/java, d2, structurizr/docker) adiciona dependências de host para quem optar por elas.

**Promoção (2026-07-28, delta-013):** o piloto doc-profile+doc-entregavel fechou nos 4 repos IMEX (8 exports em 2 rodadas, 2026-07-20) e a exceção do RNF1 consolidou via MUDA no TRUTH.md; a `doc-entregavel` saiu de experimental no README. O check mecânico do doc-profile (presença + schema) permanece adiado pelo perímetro do ADR-0006 — pendência roteada na delta-013. A delta externa com gate do specify (travelplanner) não condicionava esta promoção e segue como gatilho do DT-004.
