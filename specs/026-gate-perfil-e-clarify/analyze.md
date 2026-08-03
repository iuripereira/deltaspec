# Analyze — delta-026 · 2026-08-02

Metade mecânica: `check_cycle.py specs/026-gate-perfil-e-clarify` → **LIBERADO**, C1–C10 sem achados. A primeira rodada acusou **ALTO legítimo** (`bloco MUDA sem citar o alvo vigente`) e o achado era real: o R3 declarava `MUDA` de um "RNF do gate" que **não existe** no TRUTH — nenhum requisito é dono da política de dependência. Corrigido para `ADICIONA RNF1` com Métrica e Verificação próprias; o gate pegou erro de verdade antes do implement.

| # | Severidade | Onde | Inconsistência | Ação sugerida |
|---|---|---|---|---|
| 1 | BAIXO | spec.md RNF1 | A numeração local `RNF1` colide visualmente com o `RNF1` vigente no TRUTH (economia de tokens), embora a regra de archive mande atribuir o próximo livre — vai consolidar como `RNF6` | Aceito: é a regra vigente (o Rn local não migra). Quem ler a delta arquivada precisa lembrar disso — o mesmo já vale para todos os Rn locais |

**Verificações de juízo que passaram:**

- **Check 3 (spec × plan):** o resumo do plan cobre R1, R2 e RNF1 — os mesmos da spec. Nada no plano sem base: o C11 e o C12 saem dos cenários do R1; a prosa normativa da T3 sai do R2; os três espelhos e o step de CI da T4 saem da Métrica e da Verificação do RNF1. O plano não contradiz nenhum cenário de aceite; as severidades que ele codifica (BAIXO para perfil ausente, ALTO para núcleo ausente, nunca CRÍTICO) batem uma a uma com a spec.
- **Check 4 (TRUTH.md) — conferido por comparação programática, não a olho:** `MUDA R12` traz **7 dos 8 cenários vigentes byte-idênticos**; o oitavo (a enumeração dos checks) foi alterado de propósito, de C1–C10 para C1–C12 — é o miolo da delta, não perda. `MUDA R8` repete o único cenário vigente e acrescenta três. `ADICIONA RNF1` não duplica nem conflita: nenhum RNF vigente trata de política de dependência (RNF4 é selftest, RNF5 é portabilidade de caminho).
- **Check 5 (regras canônicas):** a delta **muda uma regra canônica de propósito** — o princípio de stdlib pura do `CLAUDE.md` —, o que é legítimo porque a renúncia está registrada em ADR própria (ADR-0023) e a mudança propaga para os três espelhos no mesmo change, sem deixar promessa órfã. Fora isso: PT-BR em identificadores e prosa; zero valor mágico (o núcleo do perfil vira `NUCLEO_TOPO`/`NUCLEO_ARTEFATOS`, não lista solta); nenhuma sobrescrita de arquivo; CHANGELOG como task explícita (T5); versão segue ancorada na tag. Artefatos somam 85 linhas contra a main — bem abaixo do limiar de PR, sem split (C7 não disparou).
- **TDD (obrigatório aqui, tipo `tooling` com lógica pura):** T1 e T2 têm o ciclo completo — teste que falha por `NameError`, mínimo que passa, refactor implícito. As fixtures cobrem o caso feliz, cada modo de falha e, em ambas, a **regressão de sintaxe citada em prosa** que este repo já sofreu três vezes.
- **Perímetro do ADR-0006 respeitado:** nenhuma severidade nova é CRÍTICO, e o que ficou de fora está declarado — a qualidade da entrevista e a leitura do `<N>` de decisões são juízo, não regex.

**Risco que o gate não mede:** o C11 valida o núcleo medido em **7 perfis reais de 2026-08-02**. É amostra, não teorema — perfil futuro com núcleo legitimamente diferente vai acusar falso ALTO e exigir nova delta. O CT14 (rodar contra os 7) é o que segura isso no implement.

**Veredito:** LIBERADO
