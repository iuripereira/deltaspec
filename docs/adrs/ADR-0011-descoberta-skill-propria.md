# ADR-0011: A fase de descoberta é uma skill própria pré-specify, com modelo de confiança explícito

- **Status:** Accepted
- **Data:** 2026-07-27
- **Supersedes:** —
- **Superseded by:** —

## Context

O ciclo sdd-iuri começa no `specify`, cujo insumo é um "pedido de feature" já formulado (`cycle.md`). Tudo que produz esse pedido — entrevista de negócio com stakeholder externo, análise de processo legado as-is, ingestão de material fragmentado (transcrição de reunião, planilha, vídeo), mapeamento de domínio — estava fora do framework. Os recipientes `GLOSSARY.md` e `DATA_DICTIONARY.md` nascem vazios no `projeto-init` e nenhuma skill os preenche. O gap ficou concreto no projeto imex-estoque-inteligente: PRD contratualizado gerado por IA sem validação da stakeholder, contradito pelo kickoff.

A comunidade resolve isso de três formas: AI-DLC/AWS (fase Inception com ritual **Mob Elaboration**: IA propõe, humanos validam em sessão), BMAD (agente Analyst com workflow **document-project** para brownfield) e o framework Reversa (reverse documentation com **níveis de confiança** confirmado/inferido/lacuna).

## Decision

Criamos a skill **`descoberta`** como fase própria do framework, posicionada **antes do specify**: inventário de insumos → mineração com claim tagueado por confiança e fonte rastreável → dossiê em `docs/discovery/` + população de GLOSSARY/DATA_DICTIONARY → divergências contra baseline → pauta de Mob Elaboration → saída para `max:write-prd` (ou fallback nativo) com a regra dura de que claim não-confirmado entra como `[PRESUNÇÃO]`.

Renúncias registradas:
- **Delegar a descoberta ao `max:write-prd`** — rejeitado: ele cobre entrevista socrática com o *dev* e exploração de *código*; não cobre descoberta de negócio com stakeholder externo, processo legado nem ingestão de insumos brutos. Continua no ciclo, mas como motor do PRD *depois* do dossiê (mesmo padrão adapter das demais fases).
- **Portar BMAD (agente Analyst/document-project)** — rejeitado: dependência externa pesada e redundante; o sdd-iuri orquestra por skills enxutas com fallback (ADR-0004), não por simulação de time de agentes.
- **Descoberta como fase informal (sem skill)** — rejeitado: foi exatamente o que produziu PRD não validado tratado como baseline; sem o modelo de confiança mecanizado em template, inferência vira fato silenciosamente.

## Consequences

- O pipeline ganha uma pré-fase opcional: `descoberta → (write-prd) → specify → ...`; projetos com requisitos já claros continuam entrando direto no specify.
- GLOSSARY/DATA_DICTIONARY passam a ter processo de população com nível de confiança por entrada.
- O framework assume o vocabulário da comunidade (Mob Elaboration, as-is, claim) — documentado no SKILL.md para não virar jargão sem fonte.
- Custo aceito: a qualidade do dossiê depende de harness multimodal para frames de vídeo; sem ele, degrada para lacuna com aviso (coerente com RNF2).
