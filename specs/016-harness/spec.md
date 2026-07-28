# delta-016 — harness
Estado: proposta · Data: 2026-07-28 · Branch: feat/016-harness · Perfil: completo — mexe no contrato do ciclo (template de tasks, gate, adapters) e adota motor novo; risco estrutural (aprovado: 2026-07-28)

## Contexto (≤3 linhas)
Fase 3 do plano de upgrade: o `tasks.md` ordena por dependência mas não formaliza arestas de bloqueio nem paralelização; os conceitos de harness que o framework pratica não têm vocabulário canônico; aprovações humanas por fase ficam dispersas na conversa; e as fases que leem código não têm camada de contexto fundamentada. AI-DLC (units of work paralelas, trilha de auditoria), Anthropic (harness engineering) e graphify validam o desenho.

## Mudanças

### R1 — ADICIONA: arestas de bloqueio explícitas no tasks.md
- DADO a fase tasks QUANDO o `tasks.md` fecha ENTÃO toda dependência entre tasks está declarada na forma canônica `(dep: Tn[, Tm])` do template — task sem `dep:` é livre — e o conjunto forma um grafo dirigido acíclico
- DADO o grafo QUANDO duas tasks não têm caminho entre si ENTÃO são paralelizáveis, e as unidades de execução paralela são deriváveis mecanicamente do grafo, sem anotação manual extra
- DADO um `tasks.md` anterior a esta delta (sem nenhum `dep:`) QUANDO o ciclo ou o gate o lê ENTÃO vale a ordem do arquivo como cadeia linear implícita — retrocompatível, sem migração

### R2 — MUDA R12 (delta-015): a metade mecânica do analyze ganha C9 (grafo de tasks) e C10 (convergência mínima no archive)
- DADO uma delta QUANDO `check_cycle.py` roda ENTÃO ele verifica aceite (C1), cobertura spec↔tasks (C2), estado × localização (C3), archive sem perda (C4), tamanho do TRUTH (C5), pendência roteada (C6), medição do split de PR (C7), cobertura do plano de testes (C8), validade do grafo de tasks (C9) e convergência mínima no archive (C10), e sai 1 se houver ALTO ou CRÍTICO
- DADO um requisito removido do `TRUTH.md` resultante sem MUDA/REMOVE que o declare QUANDO o gate roda ENTÃO acusa CRÍTICO e o veredito é BLOQUEADO — comparando o `TRUTH.md` contra o merge-base da branch com a main (fallback `HEAD`, com aviso, quando não há base), para que consolidação já commitada não crie janela cega; sufixo reescrito cujo ID permanece no arquivo não é perda
- DADO uma delta cujo diff acumulado de `specs/NNN-nome/` contra o merge-base excede o limiar de PR da regra canônica QUANDO o C7 roda ENTÃO reporta BAIXO recomendando o split dos artefatos (regra em `cycle.md`), sem alterar o código de saída — a medição informa, o split é decisão do ciclo; sem git ou sem merge-base o C7 se omite, como o C4
- DADO um `test-plan.md` presente QUANDO o C8 roda ENTÃO acusa ALTO para Rn/RNFn da spec sem caso que o cubra e para caso citando requisito inexistente (espelho do C2); `test-plan.md` ausente sem dispensa declarada → ALTO; ausente com dispensa (R38) ou delta `bugfix` sem tasks → BAIXO informativo
- DADO um `tasks.md` com `dep:` citando task inexistente ou formando ciclo QUANDO o C9 roda ENTÃO acusa ALTO (grafo inválido); nenhum `dep:` no arquivo → válido (cadeia linear implícita, R1)
- DADO uma delta arquivada (`Estado: arquivada` em `_archive/`) com task `- [ ]` remanescente no `tasks.md` QUANDO o C10 roda ENTÃO acusa ALTO — o archive não fecha com trabalho declarado e não concluído; a auditoria semântica codebase×spec permanece juízo humano do review (renúncia por design, ADR-0014)
- DADO a saída do script QUANDO impressa ENTÃO se declara parcial — nomeia os checks mecânicos cobertos e avisa que os checks 3 e 5 do `analyze.md` (scope creep, regra canônica) são humanos e não rodaram
- DADO um `TRUTH.md` com sufixos na notação legada `(ΔNNN)` ou na nova `(delta-NNN)` QUANDO o gate lê os alvos ENTÃO reconhece as duas formas, sem exigir migração dos projetos existentes

### R3 — ADICIONA: execução paralela por worktree das unidades independentes
- DADO unidades paralelizáveis (R1) num harness com subagentes QUANDO o implement roda ENTÃO cada unidade pode executar num subagente com worktree isolada (motor: `superpowers:using-git-worktrees`, contrato em `adapters.md`), com convergência das worktrees antes do review
- DADO um harness sem subagentes ou sem worktree QUANDO o implement roda ENTÃO a execução é sequencial na ordem topológica do grafo, com aviso de degradação (RNF2)

### R4 — ADICIONA: vocabulário de harness canônico
- DADO os conceitos de harness que o framework pratica (initializer, agente incremental, gate determinístico, degradação graciosa, human-in-the-loop, trilha de auditoria, unidade paralelizável) QUANDO citados em skills e docs ENTÃO o termo e a definição vivem num reference canônico único da `spec-feature` e os demais arquivos referenciam sem duplicar (regra de ouro)

### R5 — ADICIONA: trilha de auditoria de aprovação por fase
- DADO uma aprovação humana que o ciclo exige e ainda não tem registro mandatório (prototipação R37, ressalvas aceitas no analyze, aceite do review) QUANDO concedida ENTÃO fica registrada de forma citável no artefato da própria fase, seguindo o padrão de formato do R36 (`aprovado: AAAA-MM-DD`), sem arquivo de auditoria separado e sem inchar tokens — a aprovação de perfil continua regida pelo R36, dono vigente
- DADO uma delta arquivada QUANDO auditada ENTÃO as aprovações são verificáveis nos artefatos em `_archive/` — a trilha sobrevive ao ciclo

### R6 — ADICIONA: graphify como 4º motor externo opcional
- DADO um projeto-alvo com graphify instalado e habilitado no `doc-profile.yaml` QUANDO descoberta, specify/plan ou review rodam ENTÃO consultas `graphify query`/`path`/`explain` entram como insumo fundamentado com aresta citável `arquivo:linha`, e as tags `EXTRACTED`/`INFERRED`/`AMBIGUOUS` mapeiam no modelo `confirmado`/`inferido`/`lacuna` da descoberta (R25 — `AMBIGUOUS` → `lacuna`: requer validação humana)
- DADO o contrato do adapter QUANDO a delta consolida ENTÃO a tabela de `adapters.md` tem a linha do graphify com instalação manual consciente (nunca deixar o `graphify install` escrever hook `PreToolUse`/CLAUDE.md — conflita com o harness), pin na política de versões com verificação datada (R34) e preferência pelo modo `--code-only` (determinístico, zero LLM)
- DADO graphify presente e habilitado QUANDO o eixo Spec do review roda ENTÃO pode consultar o impacto do diff (`graphify query`) como insumo do confronto Rn×diff — mesmo contrato e mesma degradação dos demais cenários
- DADO graphify ausente ou desabilitado QUANDO as fases rodam ENTÃO o fluxo atual (grep/Explore) segue com no máximo 1 linha de aviso — degradação graciosa (RNF2)

## Fora de escopo
- Grafo de tarefas no graphify — o `tasks.md` continua dono das arestas de bloqueio; visualização/export Mermaid do grafo
- Jira/tickets.md (Fase 4, delta-017) · Figma/documentação visual (Fase 5, delta-018)
- Automatizar juízo humano do analyze (checks 3 e 5) — segue "por design, fora de escopo" no TRUTH
- Convergência semântica automatizada no archive (auditar codebase contra spec/plan além do C10 mínimo) e `audit.md` separado por delta (padrão AI-DLC) — renúncias registradas na ADR-0014

## Dependências e riscos
- Depende das Fases 0–2 arquivadas (deltas 013–015) e do plano de upgrade aprovado em 2026-07-28
- Risco: graphify tem ~4 meses de vida e bus factor = 1 — mitigado por ser motor opcional com degradação, pin e `--code-only` (tabela de riscos do plano)
- [x] Fechado no clarify (2026-07-28): trilha de auditoria nas linhas dos artefatos da própria fase (R5); C10 mínimo mecanizável adotado (R2) com renúncia da parte semântica; impacto de PR do graphify como cenário simples do R6 — renúncias na ADR-0014
- Risco: 6 blocos + implementação excedem o limiar de PR — split R17 provável (artefatos primeiro, PR próprio)
