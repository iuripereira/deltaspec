# delta-015 — fluxo
Estado: arquivada · Data: 2026-07-28 · Branch: feat/015-fluxo

## Contexto (≤3 linhas)
Fase 2 do plano de upgrade: o ciclo cobre specify→archive, mas não tem prototipação, plano de testes nem liga/desliga de estágios — a economia de tokens hoje é só limite de linhas (RNF1). AI-DLC (workflow adaptativo), Kiro (spec `bugfix`) e BMAD (profundidade pela complexidade) validam o desenho; renúncias em [ADR-0013](../../docs/adrs/ADR-0013-selecao-adaptativa-e-bugfix.md).

## Mudanças

### R1 — ADICIONA: perfil de execução por delta (seleção adaptativa de estágios)
- DADO uma delta nova QUANDO o specify abre o `spec.md` ENTÃO a IA propõe no cabeçalho o campo `Perfil: completo|enxuto` com justificativa de 1 linha calibrada por escopo e risco, e o perfil só vale após aprovação explícita do usuário, registrada no próprio cabeçalho (`aprovado: AAAA-MM-DD`)
- DADO perfil `enxuto` aprovado QUANDO o ciclo roda ENTÃO o clarify vira sob demanda (roda só se a spec tiver ambiguidade apontada), o `test-plan.md` é dispensável com justificativa de 1 linha no cabeçalho (`Test-plan: dispensado — <motivo>`) e o review executa os dois eixos fundidos num único subagente, com achados ainda classificados por eixo; plan, tasks, analyze e archive seguem integrais
- DADO um `spec.md` sem o campo `Perfil` (deltas anteriores a esta) QUANDO o ciclo ou o gate roda ENTÃO vale `completo` — retrocompatível, sem migração
- DADO o ciclo aplicável do tipo do projeto (R10) QUANDO o perfil é aplicado ENTÃO ele opera **dentro** do ciclo do tipo — perfil não reintroduz fase que o tipo já exclui

### R2 — ADICIONA: prototipação opcional (estágio CONDITIONAL pós-descoberta)
- DADO uma delta cujo escopo toca interface ou fluxo que o stakeholder precisa ver QUANDO o specify roda ENTÃO a IA propõe o estágio de prototipação com justificativa, e ele só executa com aprovação do usuário — nunca por iniciativa própria (mesma regra do gate visual, ADR-0009)
- DADO o estágio aprovado QUANDO o protótipo é produzido ENTÃO a forma segue a categoria `prototipo` do `doc-profile.yaml` (dono da decisão); perfil ausente ou sem a categoria → default HTML estático navegável em `docs/prototypes/NNN-nome/`, versionado e referenciado na seção Contexto da delta
- DADO uma delta sem gatilho de prototipação QUANDO o ciclo roda ENTÃO o estágio se omite com no máximo 1 linha de aviso

### R3 — ADICIONA: plano de testes como artefato do ciclo
- DADO o `tasks.md` pronto QUANDO a fase tasks fecha ENTÃO existe `specs/NNN-nome/test-plan.md` (template da skill) derivado dos cenários DADO/QUANDO/ENTÃO da spec e das verificações das tasks — sem re-entrevistar nem inventar cenário novo
- DADO um caso de teste QUANDO registrado no plano ENTÃO carrega o requisito coberto (`cobre: Rn|RNFn`), o tipo `auto|manual`, e o comando (auto) ou os passos roteirizados (manual) — teste manual roteirizado conta como cobertura
- DADO perfil `enxuto` com dispensa justificada no cabeçalho QUANDO o ciclo roda ENTÃO o `test-plan.md` se omite e o C8 reporta BAIXO informativo em vez de ALTO

### R4 — ADICIONA: `bugfix` como tipo de spec distinto
- DADO um pedido de correção de defeito QUANDO a delta abre ENTÃO ela pode nascer com `Tipo: bugfix` no cabeçalho e template próprio (sintoma, reprodução DADO/QUANDO/ENTÃO, causa-raiz, teste de regressão), mantendo a numeração NNN global
- DADO uma delta `bugfix` QUANDO o ciclo roda ENTÃO o pipeline é specify → plan curto → implement (teste de regressão obrigatório) → review, com clarify, tasks e test-plan sob demanda e analyze mantido (read-only)
- DADO uma delta `bugfix` sem mudança de requisito QUANDO o archive roda ENTÃO o diretório move para `_archive/` sem consolidar no TRUTH.md, e o gate não exige bloco Rn — a seção Mudanças declara "nenhuma (correção sem mudança de requisito)"
- DADO um bugfix que altera requisito vigente QUANDO a delta consolida ENTÃO o bloco MUDA cita o alvo no TRUTH.md como qualquer delta (R6)

### R5 — MUDA R12 (delta-009): a metade mecânica do analyze ganha o C8 (plano de testes)
- DADO uma delta QUANDO `check_cycle.py` roda ENTÃO ele verifica aceite (C1), cobertura spec↔tasks (C2), estado × localização (C3), archive sem perda (C4), tamanho do TRUTH (C5), pendência roteada (C6), medição do split de PR (C7) e cobertura do plano de testes (C8), e sai 1 se houver ALTO ou CRÍTICO
- DADO um requisito removido do `TRUTH.md` resultante sem MUDA/REMOVE que o declare QUANDO o gate roda ENTÃO acusa CRÍTICO e o veredito é BLOQUEADO — comparando o `TRUTH.md` contra o merge-base da branch com a main (fallback `HEAD`, com aviso, quando não há base), para que consolidação já commitada não crie janela cega; sufixo reescrito cujo ID permanece no arquivo não é perda
- DADO uma delta cujo diff acumulado de `specs/NNN-nome/` contra o merge-base excede o limiar de PR da regra canônica QUANDO o C7 roda ENTÃO reporta BAIXO recomendando o split dos artefatos (regra em `cycle.md`), sem alterar o código de saída — a medição informa, o split é decisão do ciclo; sem git ou sem merge-base o C7 se omite, como o C4
- DADO um `test-plan.md` presente QUANDO o C8 roda ENTÃO acusa ALTO para Rn/RNFn da spec sem caso que o cubra e para caso citando requisito inexistente (espelho do C2); `test-plan.md` ausente sem dispensa declarada → ALTO; ausente com dispensa (R3) ou delta `bugfix` sem tasks → BAIXO informativo
- DADO a saída do script QUANDO impressa ENTÃO se declara parcial — nomeia os checks mecânicos cobertos e avisa que os checks 3 e 5 do `analyze.md` (scope creep, regra canônica) são humanos e não rodaram
- DADO um `TRUTH.md` com sufixos na notação legada `(ΔNNN)` ou na nova `(delta-NNN)` QUANDO o gate lê os alvos ENTÃO reconhece as duas formas, sem exigir migração dos projetos existentes

### R6 — MUDA R35 (delta-014): review em dois eixos, com fusão permitida no perfil enxuto
- DADO uma delta na fase review num harness com subagentes QUANDO o review roda ENTÃO os dois estágios executam como eixos independentes em subagentes paralelos — eixo Spec (conformidade: cada Rn/RNFn confrontado com o diff) e eixo Qualidade (ponytail-review/delete-list) — cada um cego ao contexto do outro, e os achados convergentes dos dois eixos são tratados antes do PR
- DADO perfil `enxuto` aprovado (R1) QUANDO o review roda ENTÃO os dois eixos podem executar fundidos num único subagente, com os achados ainda classificados por eixo e a mesma regra de convergência
- DADO um harness sem subagentes ou motor ausente QUANDO o review roda ENTÃO os estágios rodam inline em sequência com os fallbacks e avisos vigentes dos adapters (RNF2 preservado)

## Fora de escopo
- Arestas de bloqueio no `tasks.md` e execução paralela por worktree (Fase 3, delta-016)
- Graphify como motor (Fase 3) · integração Jira/tickets.md (Fase 4) · Figma/visual (Fase 5)
- Automatizar os checks de juízo (3 e 5 do analyze) — segue "por design, fora de escopo" no TRUTH
- Novo check mecânico para aprovação do perfil (juízo do analyze humano cobre; YAGNI)

## Dependências e riscos
- Depende das Fases 0–1 concluídas (deltas 013–014, arquivadas) e do plano aprovado em 2026-07-28
- Risco: os 6 blocos + implementação excedem o limiar de PR — split R17 provável (artefatos primeiro, em PR próprio)
- Risco: chicken-egg — esta delta roda no perfil vigente (completo); perfil/test-plan valem para deltas abertas após o archive
