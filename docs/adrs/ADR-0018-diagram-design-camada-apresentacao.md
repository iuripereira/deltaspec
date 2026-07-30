# ADR-0018: diagram-design + design-sync como camada de apresentação — Mermaid permanece a fonte da verdade

- **Status:** Accepted (2026-07-30, delta-020)
- **Data:** 2026-07-30
- **Supersedes:** [ADR-0015](ADR-0015-figma-camada-apresentacao.md)
- **Superseded by:** —

## Context

A ADR-0015 adotou Figma/FigJam como camada de apresentação com gatilho de reavaliação no anúncio de preço do `generate_diagram` (DT-014). A decisão do usuário (2026-07-30) antecipou o gatilho: as limitações registradas na própria ADR-0015 já pesavam sem contrapartida — motor remoto beta com cobrança anunciada, ~6 tipos de `.mmd`, só FigJam, export não verificado, retoque manual não reprodutível — e a camada nunca chegou a ser materializada de fato num projeto real. O benchmark SDD de 2026-07-29 (origem dos DT-016–018) reforçou a preferência por motores locais e versionáveis.

Alternativas:

**1 — Manter Figma até o gatilho original (preço).** Preserva a ADR-0015, mas mantém o acabamento de stakeholder refém de um serviço beta com breaking anunciado e de retoque manual que nunca é reprodutível.

**2 — Só render CLI, sem camada de apresentação.** É a alternativa 2 já renunciada na ADR-0015: o gap de acabamento para cliente/gestão/stakeholder é real (validado nos projetos IMEX).

**3 — `diagram-design` + `design-sync`.** A skill `diagram-design` (cathrynlavery, MIT) gera diagramas editoriais **HTML+SVG autocontidos e brandados** localmente — 27 tipos, onboarding de identidade visual a partir do site do cliente, export PNG/SVG reprodutível via Playwright (`diagram-design:export`). A ferramenta `design-sync` publica os HTML num projeto claude.ai/design de forma incremental (list → plan → write), como canal opcional para stakeholders.

## Decision

Adotamos a **3** (decisão do usuário, 2026-07-30), mantendo os invariantes da camada: **unidirecional** (o `.mmd` em git é a única fonte; a materialização se refaz a partir dele; em divergência, o `.mmd` governa), **fora do caminho crítico** (o entregável congelado segue exclusivo do pipeline CLI) e **degradação graciosa** (motor ausente → render CLI + 1 linha de aviso). Prioridade de uso: documentação que vai a **cliente, gestão ou stakeholders**.

Renunciamos à 1 porque pagar o custo de um motor remoto beta para um acabamento que exige etapa manual não reprodutível é o pior dos dois mundos; à 2 porque o gap segue real e a camada agora custa ainda menos (tudo local, MIT). A renúncia ao round-trip da ADR-0015 permanece: edição na materialização (HTML ou claude.ai/design) nunca retorna ao git como fonte.

**Limitações registradas:** (a) `diagram-design` tem bus factor 1 e o contrato vem da doc upstream, **não testado em execução** — pin por commit/tag na primeira adoção real, mesmo padrão do graphify (delta-016); (b) `design-sync` exige login claude.ai com escopo de design — sessões headless ficam com a camada local (HTML em git), coberto pela degradação; (c) cliente que exigir especificamente Figma/FigJam fica sem caminho suportado — aceito: a exigência nunca ocorreu, e o congelado (que é o contrato) não depende da camada.

## Consequences

**Fica mais fácil:** a camada vira 100% local e versionável (HTML+SVG em git, regenerável), com custo zero de serviço; o acabamento entra no documento congelado por caminho **reprodutível** (`diagram-design:export` → PNG/SVG → pipeline CLI), eliminando o retoque manual da ADR-0015; a publicação para stakeholder fica no mesmo ecossistema Claude, sem MCP remoto pago.

**Fica mais difícil:** perde-se o canvas colaborativo do FigJam (stakeholder não edita/comenta na materialização — mitigado por a camada ser apresentação, nunca contrato); entra dependência de terceiro sem pin até a primeira adoção real; a qualidade "editorial" do diagram-design em diagramas técnicos densos só será conhecida na adoção — se decepcionar, o fallback render CLI continua a um aviso de distância.
