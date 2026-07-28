# delta-015 — fluxo
Estado: proposta · Data: 2026-07-28 · Branch: feat/015-fluxo

## Contexto (≤3 linhas)
Fase 2 do plano de upgrade: o ciclo cobre specify→archive, mas não tem prototipação, plano de testes nem liga/desliga de estágios — a economia de tokens hoje é só limite de linhas (RNF1). AI-DLC (workflow adaptativo), Kiro (spec `bugfix`) e BMAD (profundidade pela complexidade) validam o desenho.

## Mudanças

### R1 — ADICIONA: perfil de execução por delta (seleção adaptativa de estágios)
- DADO uma delta nova QUANDO o specify abre o `spec.md` ENTÃO a IA propõe no cabeçalho um perfil `completo|enxuto` com justificativa de 1 linha calibrada por escopo e risco, e o perfil só passa a valer após aprovação explícita do usuário, registrada no próprio cabeçalho
- DADO perfil `enxuto` aprovado QUANDO o ciclo roda ENTÃO os estágios marcados como condicionais para o perfil degradam/pulam conforme a tabela de estágios do `cycle.md` <!-- clarify: quais estágios exatamente -->
- DADO qualquer perfil QUANDO a delta chega ao gate ENTÃO o analyze roda mesmo assim (R11 — read-only e barato) e o archive continua parte do "pronto" (R7)

### R2 — ADICIONA: prototipação opcional (estágio CONDITIONAL pós-descoberta)
- DADO uma delta cujo escopo toca interface ou fluxo que o stakeholder precisa ver QUANDO o specify roda ENTÃO a IA propõe o estágio de prototipação com justificativa, e ele só executa com aprovação do usuário — nunca por iniciativa própria (mesma regra do gate visual, ADR-0009)
- DADO o estágio aprovado QUANDO o protótipo é produzido ENTÃO ele vive em local versionado do projeto e é referenciado pela delta <!-- clarify: forma e local -->
- DADO um projeto sem gatilho de prototipação QUANDO o ciclo roda ENTÃO o estágio se omite sem aviso além de 1 linha

### R3 — ADICIONA: plano de testes como artefato do ciclo
- DADO o `tasks.md` pronto QUANDO a fase tasks fecha ENTÃO existe `specs/NNN-nome/test-plan.md` derivado dos cenários DADO/QUANDO/ENTÃO da spec e das verificações das tasks — sem re-entrevistar nem inventar cenário novo
- DADO o plano de testes QUANDO o `check_cycle.py` roda ENTÃO um check novo (C8) valida a cobertura Rn/RNFn → caso de teste e acusa a lacuna <!-- clarify: severidade e direção da cobertura -->

### R4 — ADICIONA: `bugfix` como tipo de spec distinto
- DADO um pedido de correção de defeito QUANDO a delta abre ENTÃO ela pode nascer como tipo `bugfix` (template próprio: sintoma, reprodução DADO/QUANDO/ENTÃO, causa-raiz, teste de regressão) com pipeline reduzido <!-- clarify: quais fases e se consolida no TRUTH -->
- DADO um bugfix que altera requisito vigente QUANDO a delta consolida ENTÃO o bloco MUDA cita o alvo no TRUTH.md como qualquer delta (R6)

### R5 — MUDA R12 (delta-009): a metade mecânica do analyze ganha o C8 (plano de testes)
- DADO uma delta QUANDO `check_cycle.py` roda ENTÃO ele verifica aceite (C1), cobertura spec↔tasks (C2), estado × localização (C3), archive sem perda (C4), tamanho do TRUTH (C5), pendência roteada (C6), medição do split de PR (C7) e cobertura do plano de testes (C8), e sai 1 se houver ALTO ou CRÍTICO
- DADO um requisito removido do `TRUTH.md` resultante sem MUDA/REMOVE que o declare QUANDO o gate roda ENTÃO acusa CRÍTICO e o veredito é BLOQUEADO — comparando o `TRUTH.md` contra o merge-base da branch com a main (fallback `HEAD`, com aviso, quando não há base), para que consolidação já commitada não crie janela cega; sufixo reescrito cujo ID permanece no arquivo não é perda
- DADO uma delta cujo diff acumulado de `specs/NNN-nome/` contra o merge-base excede o limiar de PR da regra canônica QUANDO o C7 roda ENTÃO reporta BAIXO recomendando o split dos artefatos (regra em `cycle.md`), sem alterar o código de saída — a medição informa, o split é decisão do ciclo; sem git ou sem merge-base o C7 se omite, como o C4
- DADO a saída do script QUANDO impressa ENTÃO se declara parcial — nomeia os checks mecânicos cobertos e avisa que os checks 3 e 5 do `analyze.md` (scope creep, regra canônica) são humanos e não rodaram
- DADO um `TRUTH.md` com sufixos na notação legada `(ΔNNN)` ou na nova `(delta-NNN)` QUANDO o gate lê os alvos ENTÃO reconhece as duas formas, sem exigir migração dos projetos existentes

## Fora de escopo
- Arestas de bloqueio no `tasks.md` e execução paralela por worktree (Fase 3, delta-016)
- Graphify como motor (Fase 3) · integração Jira/tickets.md (Fase 4) · Figma/visual (Fase 5)
- Automatizar os checks de juízo (3 e 5 do analyze) — segue "por design, fora de escopo" no TRUTH

## Dependências e riscos
- Depende das Fases 0–1 concluídas (deltas 013–014, arquivadas) e do plano aprovado em 2026-07-28
- Risco: os 4 blocos + implementação devem exceder o limiar de PR — split R17 provável (artefatos primeiro, em PR próprio)
- Risco: chicken-egg — esta delta ainda roda no perfil vigente (completo); o perfil só vale para deltas abertas após o archive
