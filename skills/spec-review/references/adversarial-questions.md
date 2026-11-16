# Perguntas adversariais canônicas (fallback do spec-review)

Use quando `mattpocock-skills:grilling` não estiver instalado. Uma pergunta por vez, com resposta recomendada quando houver base na spec/código — explore o repositório antes de perguntar o redundante. Registre cada resposta; ao final, converta os achados em edições propostas (antes/depois).

1. Qual é a forma mais barata de esta feature falhar em produção que a spec não cobre?
2. Que entrada inválida, estado de erro ou timeout não tem cenário DADO/QUANDO/ENTÃO?
3. Se um requisito tivesse que ser cortado hoje, qual seria — e por que ele está na spec?
4. Que dependência externa a spec assume estável, e o que acontece quando ela muda ou cai?
5. Onde a spec assume comportamento do usuário que ninguém validou?
6. Que dado persistente esta mudança cria ou migra, e qual é o caminho de volta (rollback)?
7. Quem mais consome os contratos/artefatos tocados, e o que quebra neles?
8. Qual requisito duplica ou contradiz o TRUTH.md ou uma regra canônica do CLAUDE.md?
9. O que no plano é mais complexo do que o requisito exige (over-engineering a cortar)?
10. Que decisão ficou como "depois a gente vê" e bloqueia implementação ou vira ADR agora?
11. Que qualidade (desempenho, segurança, acessibilidade, capacidade) a spec assume de graça — e cadê o RNFn com métrica e verificação que a sustenta?
