# ADR-0014: Grafo de tasks no repo, auditoria distribuída nos artefatos e graphify como motor opcional

- **Status:** Accepted (2026-07-28, delta-016)
- **Data:** 2026-07-28
- **Supersedes:** —
- **Superseded by:** [ADR-0022](ADR-0022-backend-do-graphify-registrado-no-perfil.md) (2026-08-02, delta-025) — **apenas na cláusula "`--code-only` preferido"** da decisão 4-b: a primeira execução real mostrou que esse modo cega todo arquivo não-código, então a escolha de modo passa a ser informada pelo perfil do projeto-alvo, sem preferência normativa. O resto da decisão 4-b (instalação manual consciente, proibição do auto-install, pin com verificação datada, toggle no doc-profile) e as decisões 1-b, 2-c e 3-b seguem vigentes e continuam sendo referenciadas.

## Context

A Fase 3 do plano de upgrade (2026-07-28) traz o harness engineering para dentro do framework: o `tasks.md` ordenava por dependência mas não formalizava arestas de bloqueio (sem paralelização segura), as aprovações humanas do ciclo ficavam dispersas na conversa, e as fases que leem código não tinham camada de contexto fundamentada. AI-DLC (units of work paralelas, trilha `audit.md`), spec-kit (`/converge`) e graphify (grafo de codebase por AST, ~97k estrelas, 4 meses de vida, bus factor = 1) eram os padrões em jogo. Quatro decisões tiveram alternativas reais.

**1 — Trilha de auditoria.** Alternativas: (a) `audit.md` por delta (padrão AI-DLC — trilha centralizada, mas artefato a mais para manter e ler, contra o RNF1); (b) aprovações registradas como linhas citáveis no artefato da própria fase, no padrão `aprovado: AAAA-MM-DD` que o R36 já pratica.

**2 — Convergência no archive (`/converge`).** Alternativas: (a) auditoria semântica codebase×spec automatizada (promete gate que é só prompt — falso negativo confiante); (b) renúncia total (o review em dois eixos já confronta Rn×diff); (c) C10 mínimo mecanizável — delta arquivada com task `- [ ]` remanescente → ALTO — e a parte semântica permanece juízo humano do review.

**3 — Dono do grafo de execução.** Alternativas: (a) graphify modela também o grafo de tarefas (uma ferramenta só, mas acopla o ciclo a um motor externo de vida curta); (b) o `tasks.md` versionado continua dono das arestas (`dep: Tn`), com o C9 validando existência e aciclicidade.

**4 — Contrato do graphify.** Alternativas: (a) usar o `graphify install` oficial (conveniente, mas o instalador escreve hook `PreToolUse` e CLAUDE.md do projeto — interfere no harness do framework); (b) instalação manual consciente com pin datado (R34), preferência `--code-only` (determinístico, zero LLM) e toggle no `doc-profile.yaml`, com degradação graciosa quando ausente (ADR-0004).

## Decision

Decididas com o usuário em 2026-07-28 (clarify da delta-016): **1-b, 2-c, 3-b e 4-b.**

A trilha de auditoria vive nos artefatos que já existem — cada aprovação exigida pelo ciclo é uma linha citável no artefato da própria fase, e sobrevive no `_archive/`. Renunciamos ao `audit.md` porque centralizar custaria um artefato e tokens sem ganhar verificabilidade: a trilha distribuída é igualmente citável e o archive a preserva.

A convergência no archive entra só na parte mecanizável (C10); renunciamos à auditoria semântica automatizada pelo mesmo racional dos checks 3 e 5 do analyze — é juízo, não regex, e automatizá-la produziria falso negativo confiante.

O grafo de execução pertence ao `tasks.md` (arestas `dep:` explícitas, C9 valida, unidades paralelizáveis derivadas mecanicamente); o graphify entra como **4º motor externo opcional** para contexto de codebase (descoberta, specify/plan, review), nunca como dono de tarefa. Renunciamos ao auto-install: instalação manual consciente, pin com verificação datada, `--code-only` preferido, toggle no doc-profile — ausente, o fluxo atual (grep/Explore) segue com 1 linha de aviso. As tags `EXTRACTED`/`INFERRED`/`AMBIGUOUS` mapeiam em `confirmado`/`inferido`/`lacuna` (R25), mantendo o modelo de confiança único.

## Consequences

**Fica mais fácil:** implementação paralela segura (unidades sem caminho entre si → subagentes em worktrees isoladas, motor `superpowers:using-git-worktrees`); archive não fecha com trabalho declarado e não concluído (C10); auditoria de quem aprovou o quê sem artefato novo; projetos grandes/brownfield ganham insumo citável `arquivo:linha` nas fases que leem código.

**Fica mais difícil:** o `tasks.md` vira contrato lido por script (sintaxe `dep:` canônica — retrocompatível: arquivo sem `dep:` vale como cadeia linear); o adapter do graphify precisa de verificação datada como os demais (R34) e o risco de vida do projeto (bus factor = 1) fica permanente na tabela de pins; se o graphify morrer, nada do ciclo quebra, mas a linha do adapter vira ruído até ser removida.
