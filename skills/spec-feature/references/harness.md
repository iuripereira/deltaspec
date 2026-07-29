# Harness — vocabulário canônico do framework

<!-- Dono único dos termos de harness engineering que o deltaspec pratica (delta-016).
     Skills e docs citam o termo e linkam este arquivo; não redefinem (regra de ouro). -->

O deltaspec é um **harness**: a estrutura determinística — skills, gates, registros
com dono — que envolve o agente e torna o trabalho verificável, auditável e
retomável entre sessões. Termos canônicos:

- **Initializer** — skill que prepara o ambiente antes do trabalho incremental
  (`projeto-init`, `projeto-infra`); padrão initializer + agentes incrementais (Anthropic).
- **Agente incremental** — sessão que executa exatamente uma delta (1 feature =
  1 delta spec); deltas pequenas são o ponto crítico validado do padrão.
- **Gate determinístico** — verificação mecânica versionada no repo com selftest
  (`check_cycle.py` C1–C10, `validate_integrity.py`), distinta de gate por prompt:
  o que é juízo permanece humano (ADR-0006, ADR-0014).
- **Degradação graciosa** — motor externo ausente → fallback com aviso, nunca
  quebra (ADR-0004; RNF2; contratos em adapters.md).
- **Human-in-the-loop** — a IA propõe, o humano aprova; toda aprovação exigida pelo
  ciclo tem registro citável (trilha de auditoria, cycle.md).
- **Trilha de auditoria** — o conjunto das aprovações registradas nos artefatos das
  próprias fases (regras e sintaxes: cycle.md, "Trilha de auditoria de aprovação"; ADR-0014).
- **Unidade paralelizável** — subconjunto de tasks sem caminho entre si no grafo do
  `tasks.md`; pode executar em subagente com worktree isolada (cycle.md,
  "Execução paralela por unidades").
