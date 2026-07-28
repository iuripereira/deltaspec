# Test plan — delta-015
<!-- derivado dos cenários DADO/QUANDO/ENTÃO da spec e das verificações do tasks.md (R3) -->
- [ ] CT1 — spec sem campo Perfil vale completo (retrocompat): test-plan ausente acusa ALTO · cobre: R1 · tipo: auto · verificação: fixture C8 "ausente" no `check_cycle.py --selftest`
- [ ] CT2 — dispensa declarada no perfil enxuto rebaixa o C8 a BAIXO · cobre: R1, R3 · tipo: auto · verificação: fixture C8 "dispensa" no `check_cycle.py --selftest`
- [ ] CT3 — proposta de prototipação só executa com aprovação do usuário e a forma segue o doc-profile · cobre: R2 · tipo: manual · verificação: 1) abrir delta com escopo de UI num repo de teste; 2) conferir que a IA propõe (não executa) o estágio; 3) aprovar e conferir saída em docs/prototypes/NNN-nome/ (ou categoria do doc-profile)
- [ ] CT4 — requisito sem caso e caso com referência morta acusam ALTO; caso incompleto acusa MÉDIO · cobre: R3, R5 · tipo: auto · verificação: fixtures C8 "órfão", "referência morta" e "caso incompleto" no `check_cycle.py --selftest`
- [ ] CT5 — bugfix sem bloco Rn passa; sem Reprodução ou teste de regressão acusa ALTO · cobre: R4 · tipo: auto · verificação: fixtures bugfix no `check_cycle.py --selftest`
- [ ] CT6 — review fundido no perfil enxuto mantém achados classificados por eixo e regra de convergência · cobre: R6 · tipo: manual · verificação: 1) rodar review de delta enxuta aprovada; 2) conferir relatório único com achados rotulados eixo Spec/eixo Qualidade; 3) conferir convergentes tratados antes do PR
