# delta-033 — parser-resiliente
Estado: proposta · Data: 2026-08-07 · Branch: fix/033-parser-resiliente · Perfil: completo — o gate é o coração do framework e a mudança toca o parser que 3 scripts consomem (aprovado: 2026-08-07)
Clarify: entrevistado (2026-08-07) — 2 decisões do usuário

## Contexto (≤3 linhas)
O parser do `check_cycle.py` está acoplado à forma exata dos templates ([DT-001](../../DEBT.md), topo da fila desde 2026-07-18). A reprodução de 2026-08-07 mediu **dois** modos de falha, não um: task quebrada em duas linhas produz **3 achados falsos** (2 ALTO + 1 MÉDIO, exit 1), e requisito com cabeçalho fora da forma exata **desaparece do gate inteiro em silêncio**, com veredito LIBERADO — este segundo não estava no registro do DT-001, que o descrevia como "falha ruidosa, não silenciosa".

## Mudanças
### R1 — MUDA R12 (delta-028): a metade mecânica do analyze é um script, e o núcleo que ele exige não inclui campo que ninguém lê.
<!-- versão integral do R12 vigente + 2 cenários novos (multi-linha e bloco órfão); os demais são repetidos byte a byte porque o archive substitui integralmente -->
- DADO uma delta QUANDO `check_cycle.py` roda ENTÃO ele verifica aceite (C1), cobertura spec↔tasks (C2), estado × localização (C3), archive sem perda (C4), tamanho do TRUTH (C5), pendência roteada (C6), medição do split de PR (C7), cobertura do plano de testes (C8), validade do grafo de tasks (C9), convergência mínima no archive (C10), schema do `doc-profile.yaml` (C11) e trilha do clarify (C12), e sai 1 se houver ALTO ou CRÍTICO
- DADO um item de `tasks.md` ou de `test-plan.md` cujo texto continua em linhas seguintes QUANDO o gate o lê ENTÃO os campos (`arquivos:`, `cobre:`, `verificação:`, `dep:`, `tipo:`) são reconhecidos em qualquer das linhas do item, que termina no próximo item ou no fim da seção — quebra de linha é apresentação, não conteúdo, e nunca produz achado falso
- DADO um heading `###` na seção de mudanças do `spec.md` que não casa a forma canônica `### Rn|RNFn — ADICIONA|MUDA|REMOVE` QUANDO o C1 roda ENTÃO acusa **ALTO** nomeando a linha e o texto do heading — requisito que o parser não enxerga nunca sai LIBERADO em silêncio (reprodução de 2026-08-07: `### R2 — Adiciona:` em minúscula passava sem nenhum check de cenário)
- DADO um requisito removido do `TRUTH.md` resultante sem MUDA/REMOVE que o declare QUANDO o gate roda ENTÃO acusa CRÍTICO e o veredito é BLOQUEADO — comparando o `TRUTH.md` contra o merge-base da branch com a main (fallback `HEAD`, com aviso, quando não há base), para que consolidação já commitada não crie janela cega; sufixo reescrito cujo ID permanece no arquivo não é perda
- DADO uma delta cujo diff acumulado de `specs/NNN-nome/` contra o merge-base excede o limiar de PR da regra canônica QUANDO o C7 roda ENTÃO reporta BAIXO recomendando o split dos artefatos (regra em `cycle.md`), sem alterar o código de saída — a medição informa, o split é decisão do ciclo; sem git ou sem merge-base o C7 se omite, como o C4
- DADO um `test-plan.md` presente QUANDO o C8 roda ENTÃO acusa ALTO para Rn/RNFn da spec sem caso que o cubra e para caso citando requisito inexistente (espelho do C2); `test-plan.md` ausente sem dispensa declarada → ALTO; ausente com dispensa (R38) ou delta `bugfix` sem tasks → BAIXO informativo
- DADO um `tasks.md` com `dep:` citando task inexistente ou formando ciclo QUANDO o C9 roda ENTÃO acusa ALTO (grafo inválido); nenhum `dep:` no arquivo → válido (cadeia linear implícita, R40)
- DADO uma delta arquivada (`Estado: arquivada` em `_archive/`) com task `- [ ]` remanescente no `tasks.md` QUANDO o C10 roda ENTÃO acusa ALTO — o archive não fecha com trabalho declarado e não concluído; a auditoria semântica codebase×spec permanece juízo humano do review (renúncia por design, ADR-0014)
- DADO um projeto cujo tipo tem ciclo QUANDO o C11 roda ENTÃO reporta BAIXO se o `doc-profile.yaml` estiver ausente na raiz — mesma severidade do warning que o specify já emite, sem quebrar projeto anterior à ADR-0009

### R2 — ADICIONA: o formato de item do ciclo tem um parser só, com dono canônico
- DADO os scripts do framework que leem item de `tasks.md`/`test-plan.md` (`check_cycle.py` nos C2/C8/C9/C10 e `tickets.py` na projeção) QUANDO qualquer um deles parseia um item ENTÃO todos passam pela **mesma função** do módulo dono, e nenhum script reimplementa a regex da linha — regra de ouro do repositório, medida no review por ausência de padrão duplicado
- DADO um `tasks.md` com item multi-linha QUANDO a projeção de tickets (R53) roda ENTÃO ela enxerga os mesmos campos que o gate enxerga, incluindo `dep:` na continuação — dois parsers divergentes projetariam bloqueio faltando no Jira em silêncio

## Fora de escopo
- Mudar a **forma** dos templates (`references/templates/`): a linha única segue sendo o que o template gera; a delta muda o que o parser **tolera**, não o que ele produz
- Tolerar heading fora da forma canônica: o `### Rn — VERBO` continua obrigatório — a delta faz o desvio virar achado, não faz o parser adivinhar
- Migração de delta arquivada: `specs/_archive/**` é imutável e não é reescrito

## Dependências e riscos
- O parser tolerante remove a garantia implícita "1 task = 1 linha" que o `tickets.py` (delta-017) e os C9/C10 assumem — por isso o R2 unifica; se a unificação for adiada, a divergência vira defeito silencioso na projeção Jira
- Risco de sobre-captura: a continuação precisa parar no próximo item **e** no fim da seção (heading `##`), senão prosa depois da lista entra na última task e cria falso `verificação:` — caso de teste obrigatório
- Reprodução e medição dos dois modos de falha: registradas no DT-001 no mesmo change (o texto vigente do débito subestima o problema)
