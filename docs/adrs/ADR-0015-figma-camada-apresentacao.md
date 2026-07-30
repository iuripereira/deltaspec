# ADR-0015: Figma como camada de apresentação — Mermaid permanece a fonte da verdade

- **Status:** Accepted (2026-07-28, delta-018)
- **Data:** 2026-07-28
- **Supersedes:** — (complementa a ADR-0009, imutável — mesmo mecanismo da categoria `prototipo`, ADR-0013)
- **Superseded by:** [ADR-0018](ADR-0018-diagram-design-camada-apresentacao.md) (2026-07-30, delta-020)

## Context

A pesquisa do plano de upgrade (2026-07-28, 2 workflows com verificação adversarial) confrontou Figma e Mermaid para a documentação visual do framework. Resultados-chave: versionamento git e automação por agente são do Mermaid, por margem larga — o próprio caminho oficial do Figma prova (o `generate_diagram` do Figma MCP **só aceita Mermaid como input**, gera só em FigJam, ~6 tipos, sem ajuste fino); a qualidade visual para cliente é do Figma/FigJam, por margem menor que o senso comum (o claim "Mermaid perde por não ter ícones cloud" foi refutado — architecture-beta tem 200k+ ícones iconify); o C4 do Mermaid é experimental (confirmado). Três alternativas reais:

**1 — Figma como fonte principal.** Não se sustenta: quebra o versionamento git (regra de ouro do repo), a automação por agente e o pipeline headless do entregável congelado — e até o caminho oficial do Figma consome Mermaid como fonte.

**2 — Só Mermaid, sem camada Figma.** Mantém o status quo; renuncia ao acabamento de apresentação que stakeholder de contrato espera (validado nos projetos IMEX).

**3 — Híbrido unidirecional.** Mermaid em git como única fonte; Figma/FigJam como camada de **apresentação a cliente** (categoria `apresentacao` do doc-profile), materializada do `.mmd` via `generate_diagram` + retoque manual; entregável congelado segue no pipeline CLI; C4 segue no Structurizr (tabela da ADR-0009).

## Decision

Adotamos a **3**, com o fluxo deliberadamente unidirecional: o `.mmd` muda → re-materializa; edição feita no Figma **nunca retorna ao git como fonte** — em divergência, o `.mmd` governa. A categoria `apresentacao` entra no template do doc-profile como opcional (`obrigatorio: false`), e o Figma MCP entra nos adapters como motor opcional com fallback (ADR-0004): ausente/não autenticado → pipeline CLI com 1 linha de aviso.

Renunciamos à 1 pelos três vetos acima (git, automação, headless); à 2 porque a camada custa pouco (um toggle + um contrato) e cobre um gap real de apresentação. Renunciamos também ao round-trip Figma→git: sincronização bidirecional criaria segunda fonte da verdade — exatamente o que a regra de ouro proíbe.

**Limitações registradas:** (a) `generate_diagram` é beta e "will eventually be a usage-based paid feature" — fora do caminho crítico por design; pendência de reavaliação com gatilho no preço (DT roteado no archive da delta-018); (b) tipos de `.mmd` não suportados (~6 aceitos) → fallback render CLI + imagem colada no FigJam; (c) **não verificado** (fonte única, 2026-07-28): FigJam sem export SVG confiável — se o cliente exigir acabamento FigJam no documento congelado, o caminho é retoque/export manual; verificar na primeira materialização real.

## Consequences

**Fica mais fácil:** apresentação com acabamento para stakeholder sem abrir mão do git como fonte; o agente automatiza a materialização (Mermaid é o input que o MCP aceita); nada muda para projeto que não declara a categoria.

**Fica mais difícil:** um motor remoto a mais na tabela de adapters (verificação datada, R34) — e ele é beta com preço futuro; a materialização pode divergir do fonte até alguém re-materializar (mitigado pela regra "o `.mmd` governa"); o retoque manual não é reprodutível — aceito por ser camada de apresentação, nunca contrato.
