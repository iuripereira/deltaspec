# delta-026 — gate do doc-profile e canal humano no clarify
Estado: proposta · Data: 2026-08-02 · Branch: feat/026-gate-perfil-e-clarify · Perfil: completo — mexe no gate determinístico (código novo + selftest), no contrato de uma fase e num princípio canônico do repo; errar propaga para todo projeto-alvo (aprovado: 2026-08-02)

Clarify: entrevistado (2026-08-02) — 3 decisões do usuário
<!-- trilha do clarify (R2 desta delta): âncora canônica no cabeçalho, lida pelo C12 -->

## Contexto (≤3 linhas)
Dois débitos vizinhos em `spec-feature`, ambos com gatilho disparado: **DT-013** (o `doc-profile.yaml` não tem check mecânico) e **DT-023** (o clarify fecha sem uma única resposta humana).
O gatilho do DT-013 exigia "formato estabilizado por delta real em projeto externo": a varredura de 2026-08-02 achou **7 perfis reais** — núcleo (`version`, `decisao`, `publico`, `artefatos` com 4 categorias) em 7/7, cauda opcional nunca propagada (`explicativos` 4/7, `prototipo`/`apresentacao` 1/7), `motores` em 1/7 e `decisao.justificativa` vazia em 6/7.
O DT-023 foi observado nas deltas 004/005/006/015; a delta-025 o contrariou à mão, sem regra que o sustente.

## Mudanças

### R1 — MUDA R12 (delta-016): a metade mecânica do analyze é um script, agora com o perfil e a trilha do clarify
- DADO uma delta QUANDO `check_cycle.py` roda ENTÃO ele verifica aceite (C1), cobertura spec↔tasks (C2), estado × localização (C3), archive sem perda (C4), tamanho do TRUTH (C5), pendência roteada (C6), medição do split de PR (C7), cobertura do plano de testes (C8), validade do grafo de tasks (C9), convergência mínima no archive (C10), schema do `doc-profile.yaml` (C11) e trilha do clarify (C12), e sai 1 se houver ALTO ou CRÍTICO
- DADO um requisito removido do `TRUTH.md` resultante sem MUDA/REMOVE que o declare QUANDO o gate roda ENTÃO acusa CRÍTICO e o veredito é BLOQUEADO — comparando o `TRUTH.md` contra o merge-base da branch com a main (fallback `HEAD`, com aviso, quando não há base), para que consolidação já commitada não crie janela cega; sufixo reescrito cujo ID permanece no arquivo não é perda
- DADO uma delta cujo diff acumulado de `specs/NNN-nome/` contra o merge-base excede o limiar de PR da regra canônica QUANDO o C7 roda ENTÃO reporta BAIXO recomendando o split dos artefatos (regra em `cycle.md`), sem alterar o código de saída — a medição informa, o split é decisão do ciclo; sem git ou sem merge-base o C7 se omite, como o C4
- DADO um `test-plan.md` presente QUANDO o C8 roda ENTÃO acusa ALTO para Rn/RNFn da spec sem caso que o cubra e para caso citando requisito inexistente (espelho do C2); `test-plan.md` ausente sem dispensa declarada → ALTO; ausente com dispensa (R38) ou delta `bugfix` sem tasks → BAIXO informativo
- DADO um `tasks.md` com `dep:` citando task inexistente ou formando ciclo QUANDO o C9 roda ENTÃO acusa ALTO (grafo inválido); nenhum `dep:` no arquivo → válido (cadeia linear implícita, R40)
- DADO uma delta arquivada (`Estado: arquivada` em `_archive/`) com task `- [ ]` remanescente no `tasks.md` QUANDO o C10 roda ENTÃO acusa ALTO — o archive não fecha com trabalho declarado e não concluído; a auditoria semântica codebase×spec permanece juízo humano do review (renúncia por design, ADR-0014)
- DADO um projeto cujo tipo tem ciclo QUANDO o C11 roda ENTÃO reporta BAIXO se o `doc-profile.yaml` estiver ausente na raiz — mesma severidade do warning que o specify já emite, sem quebrar projeto anterior à ADR-0009
- DADO um `doc-profile.yaml` presente QUANDO o C11 o valida ENTÃO exige o **núcleo estável** — `version`; `decisao.data` e `decisao.justificativa` como chaves; `publico.interno` e `publico.cliente` booleanos; `artefatos` com `arquitetura`, `modelo-dados`, `fluxos` e `casos-de-uso` — e acusa ALTO nomeando a chave ausente; categoria fora do núcleo é opcional (ausência não é erro, categoria desconhecida no máximo BAIXO), porque a cauda do template nunca propaga retroativamente
- DADO um perfil sem nenhum artefato `obrigatorio: true` e com `decisao.justificativa` vazia, ou com `motores.graphify: true` e `motores.graphify_backend` vazio/ausente, ou que não seja YAML válido QUANDO o C11 roda ENTÃO acusa ALTO citando a causa — e nenhuma severidade do C11 é CRÍTICO: perfil malformado reporta, não bloqueia o implement (perímetro do ADR-0006)
- DADO uma delta cujo perfil manda o clarify rodar QUANDO o C12 roda ENTÃO acusa ALTO se o `spec.md` não tiver a linha de trilha do clarify na âncora canônica do cabeçalho; a linha é lida por âncora de início de linha, nunca por busca de texto solto, e o C12 se omite quando o perfil dispensa o clarify
- DADO a saída do script QUANDO impressa ENTÃO se declara parcial — nomeia os checks mecânicos cobertos e avisa que os checks 3 e 5 do `analyze.md` (scope creep, regra canônica) são humanos e não rodaram
- DADO um `TRUTH.md` com sufixos na notação legada `(ΔNNN)` ou na nova `(delta-NNN)` QUANDO o gate lê os alvos ENTÃO reconhece as duas formas, sem exigir migração dos projetos existentes

### R2 — MUDA R8 (delta-000): fases delegadas por contrato, e o clarify declara se teve canal humano
- DADO a fase clarify/plan/implement/review QUANDO ela roda ENTÃO o motor é o declarado em `adapters.md`, invocado com o contrato de formato/destino e verificado após a fase
- DADO uma delta cujo perfil manda o clarify rodar QUANDO a fase encerra ENTÃO o `spec.md` carrega a linha citável `Clarify: entrevistado (AAAA-MM-DD) — <N> decisões do usuário` ou `Clarify: auto-avaliado (AAAA-MM-DD) — sem canal humano`, e a fase não fecha sem ela — a verificação pós-fase de `adapters.md` passa a exigir a linha além da conformidade de ADR
- DADO um clarify sem nenhuma resposta do usuário — harness sem canal humano, ou ambiguidades todas resolvidas por exploração do repositório — QUANDO o relatório de ambiguidade é gravado ENTÃO ele sai marcado `auto-avaliado`, tornando visível o que hoje passa silencioso, e o critério de saída do `cycle.md` distingue ambiguidade resolvida **pelo usuário** de resolvida **pelo agente**
- DADO que o agente que redige a spec é o mesmo que pontua o relatório QUANDO o contrato do clarify é lido ENTÃO ele registra esse viés e manda escolher o grau mais ambíguo em caso de dúvida — regra que o `grill-me` já enuncia e que o contrato do deltaspec não repetia

### R3 — MUDA RNF do gate: os scripts passam a admitir uma dependência externa declarada
- DADO os gates do framework QUANDO eles importam bibliotecas ENTÃO `PyYAML` é dependência externa **declarada e admitida** — única exceção ao princípio de stdlib pura, necessária porque o C11 lê YAML e um parser próprio seria código a manter com falso negativo silencioso
- DADO os três espelhos vivos da promessa de zero dependência (`CLAUDE.md`, `README.md`, `README.en.md`) QUANDO a delta consolida ENTÃO os três declaram a exceção nos mesmos termos, e nenhum segue prometendo "só a biblioteca padrão"
- DADO o job `ci` QUANDO ele roda os selftests ENTÃO instala a dependência explicitamente, sem depender do que o runner traz pré-instalado

## Fora de escopo
- Mecanizar a **qualidade** da entrevista (número de perguntas, profundidade) — juízo, perímetro do ADR-0006. O C12 verifica presença de âncora, não mérito.
- Ler o número `<N>` de decisões da linha do clarify para reprovar `entrevistado` com zero — parsing semântico de texto, a classe de erro que já gerou três falsos positivos neste repo.
- Propagar o schema aos 7 perfis dos projetos-alvo — trabalho de cada repo; o C11 tolera a cauda ausente por desenho.

## Dependências e riscos
- Evidência do gatilho do DT-013 (varredura local, 2026-08-02): 7 perfis em `~/code`, 3 deles em projeto com delta real.
- A dependência dura de PyYAML é decisão do usuário no clarify (2026-08-02) e exige ADR própria, por renunciar a um princípio canônico vigente.
- [ ] Um dos 7 perfis declara `version: 2` sem migração documentada, e nenhum declara o `motores.graphify_backend` criado pela delta-025 — sem dono de propagação; roteia como DT no archive se não for resolvido aqui.
