# ADR-0017: portabilidade multi-agente — Claude Code only, por enquanto

- **Status:** Accepted (2026-07-30, decisão do usuário; quita o DT-018)
- **Data:** 2026-07-30
- **Supersedes:** —
- **Superseded by:** —

## Context

O benchmark do cenário SDD (2026-07-29, registrado no DEBT.md como origem dos DT-016–018) mostrou que todo framework relevante converge em portabilidade multi-agente: o Spec Kit gera templates para 30+ agentes, o OpenSpec para 47 ferramentas, o cc-sdd para 8. "Compatível com vários CLIs" virou feature de tabela nos comparativos — e proxy de não-lock-in.

O deltaspec, por outro lado, é **plugin do Claude Code** e depende de mecanismos do harness que não têm equivalente portável barato: skills com auto-invocação por description, `${CLAUDE_PLUGIN_ROOT}`, subagentes paralelos (review em dois eixos, R35), worktrees orquestradas (R41) e os motores de terceiros (superpowers, ponytail, max) que são, eles próprios, plugins do Claude Code. A parte agnóstica já é agnóstica por natureza: o formato delta + TRUTH.md é markdown puro e os gates (`check_cycle.py`, `validate_integrity.py`) são Python stdlib executável em qualquer lugar.

Alternativas:

**1 — Portar agora.** Gerar templates/comandos para outros CLIs (Cursor, Copilot, Gemini CLI…). Custo alto e permanente: cada mecanismo dependente do harness precisa de fallback por ferramenta, a matriz de teste explode, e hoje não existe nenhum usuário externo demandando — seria portabilidade especulativa (YAGNI).

**2 — Claude Code only, deliberado e registrado.** Aceitar o acoplamento como decisão de produto enquanto o framework não tem demanda externa; deixar o gatilho de reavaliação explícito.

**3 — Meio-termo: extrair um "core agnóstico".** Documentar formato + gates como camada portável e manter só a orquestração acoplada. É a fatia barata da 1 — mas sem consumidor externo é entrega sem demanda, e o formato já é legível sem documentação extra.

## Decision

Adotamos a **2**: o deltaspec é **Claude Code only, por enquanto** (decisão do usuário, 2026-07-30). A exclusividade deixa de ser fato acidental e passa a ser renúncia citável.

Renunciamos à 1 e à 3 pelo mesmo motivo: portabilidade sem demanda é custo especulativo — o valor do framework hoje está na orquestração profunda do harness (subagentes, worktrees, motores), exatamente a parte que não porta.

**Gatilho de reavaliação:** demanda externa concreta (primeiro pedido de suporte a outro CLI ou primeiro contribuidor interessado) ou a divulgação pública do framework — o mesmo gatilho do DT-015. Na reavaliação, a alternativa 3 (core agnóstico documentado) é o primeiro degrau natural antes da 1.

## Consequences

**Fica mais fácil:** o framework usa o harness sem culpa nem camada de abstração — subagentes, worktrees e skills continuam sendo mecanismo de primeira classe; zero matriz de compatibilidade para manter.

**Fica mais difícil:** adoção por quem não usa Claude Code fica bloqueada (e os comparativos de mercado leem isso como lock-in); se a reavaliação um dia mandar portar, o custo terá crescido junto com o acoplamento acumulado — mitigado pelo core (formato + gates) permanecer agnóstico por construção.
