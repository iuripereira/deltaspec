# Analyze — delta-028 · 2026-08-03

Metade mecânica: `check_cycle.py specs/028-propagacao-e-espelhos` → **LIBERADO**, C1–C12 sem nenhum achado.

**Verificações de juízo que passaram:**

- **Check 3 (spec × plan):** o resumo do plan cobre R1, R2 e RNF1 — os mesmos da spec. As três frentes do desenho mapeiam nos três requisitos, e a ordem obrigatória (TRUTH como espelho desde o início) sai do risco declarado, não de invenção do plano. Nenhum passo sem cenário que o sustente; nenhum cenário sem passo.
- **Check 4 (TRUTH.md) — conferido por comparação programática, não a olho:** `MUDA R12` traz **11 dos 12 cenários vigentes byte-idênticos**; o décimo-segundo é o do núcleo do C11, alterado de propósito (sai o `version`) — é o miolo do R1, não perda. Acrescenta 1 cenário novo (o campo sai do template). `MUDA R2` repete os **2 cenários vigentes byte-idênticos** e acrescenta 2. **Retificado no review:** esta conferência cobriu **dois dos três** blocos MUDA e concluiu como se fossem todos — o `MUDA RNF6` nunca foi comparado, e era justamente o que perdia conteúdo. Depois da correção, os três bullets vigentes do RNF6 estão repetidos ou substituídos com o porquê declarado.
- **Check 5 (regras canônicas):** a delta **aplica** duas regras canônicas em vez de contrariá-las — a regra de ouro (o `SECURITY.md` deixa de repetir o identificador e passa a apontar para o dono) e o teto de 2–3 espelhos da própria `guarding-doc-integrity`, que o arranjo atual estourava em silêncio. PT-BR em prosa e identificadores; o núcleo continua em constante nomeada (`NUCLEO_TOPO`), agora com um item a menos; CHANGELOG como task explícita (T4). Artefatos somam bem abaixo do limiar de PR — o C7 não disparou.
- **Perímetro do ADR-0006 respeitado:** a delta **afrouxa** um check (o C11 deixa de exigir uma chave) e move outra verificação para um mecanismo existente. Não mecaniza juízo novo, e o que ficou de fora está declarado — o check de padrão proibido, que permitiria fechar a metade negativa do RNF6, é delta própria.

**Decidido com o usuário, não inferido (clarify de 2026-08-03, 3 decisões):** matar o `version` em vez de fazê-lo significar algo; reduzir espelhos **antes** de mecanizar, em vez de criar check novo ou aceitar o `grep`; perfil `completo`. As três tinham alternativa defensável, e a medição foi apresentada antes de cada uma.

**Medição que sustenta o desenho (2026-08-03, 7 perfis reais de `~/code`):** `version` = 1 em seis e 2 em um — e o `2` é justamente o perfil **mais completo**, contra um template que declara `1` com as mesmas 7 categorias. O campo não rastreia schema nenhum. Categorias: 4·4·4·5·5·5·7; `motores` presente em 1 de 7. O `ADR-0023` aparece em 5 arquivos varridos pelo C2, o que faria owner + 4 espelhos sem a redução.

**Risco que o gate não mede:** o C2 passa a governar um **identificador de ADR**, não um valor de negócio como os demais `[[owner]]`. Se amanhã uma skill precisar citar a ADR-0023 legitimamente, o C2 vai acusar — e a resposta certa é entrar no manifesto como espelho, por decisão registrada, nunca ampliar o `exclude_globs` para calar. Fica dito aqui porque é onde a pressa erraria.

**Veredito:** LIBERADO

## Apêndice — review em dois eixos (2026-08-03)

Review: convergentes tratados / recusas justificadas — 2026-08-03

Perfil `completo` → dois eixos independentes em subagentes paralelos (R35). **Eixo Spec: REPROVADO** (1 CRÍTICO, 1 ALTO). **Eixo Qualidade: APROVADO COM AJUSTES** (delete-list de 9 itens).

**O CRÍTICO — a delta criava o mecanismo de espelho e, no mesmo movimento, escrevia o texto que o esvaziava.** O bloco `RNF1` (a única parte que vai para o TRUTH na consolidação) não continha a string `ADR-0023`: falava em "a ADR que a admite" e "o padrão da ADR". Como o MUDA substitui o requisito **integralmente**, o archive removeria do `TRUTH.md` a única ocorrência do identificador — e o `deps.toml` acabara de declarar o TRUTH espelho desse padrão. Resultado simulado: `[C1] padrão ausente em specs/TRUTH.md`, `FAIL`, com o pré-commit bloqueando o próprio commit do archive. Corrigido, e a simulação do archive volta a dar `[C1] ... OK (dono + 3 espelho(s))`.

A ironia é exata e vale registrar: a delta-027 foi reprovada por reintroduzir a patologia que atacava; esta criava um espelho e o esvaziava no mesmo texto. Terceira vez seguida que o furo está **no ponto que a delta existe para reforçar** — é onde o autor menos olha, porque é onde ele tem mais certeza.

**O ALTO — perda silenciosa no MUDA RNF6.** Dois fatos normativos vigentes sumiam sem declaração: a mensagem acionável na ausência do PyYAML (+ o comando na seção de instalação do README) e a cláusula "instala antes do primeiro step que importa `yaml`". Os dois são comportamento **implementado**, e os dois nasceram como correção do review da delta-026 — seriam apagados do TRUTH pela delta seguinte. Repetidos no bloco.

**A auto-afirmação que caiu:** o Check 4 deste analyze dizia "conferido por comparação programática — zero perda silenciosa **nos dois blocos**". A delta tem **três**. O bloco não conferido era o único que perdia conteúdo. Quarta delta seguida em que o `analyze.md` afirma sobre si mesmo um escopo maior do que verificou.

**Também aplicado:** a renúncia ao check mecânico de "perfil atrás do template" — a alternativa que o próprio DT-025 nomeava — entrou em Fora de escopo com o motivo medido (6 dos 7 perfis reais acusariam na primeira execução, e a varredura de replicação mostrou que o consumidor já vai receber ruído demais); o risco do `[[owner]]` foi corrigido para o efeito real (o padrão casa o **nome do arquivo** da ADR, então proíbe *linkar* para ela, não só citá-la); o ponteiro torto do `SECURITY.md` (apontava para a seção Segurança, mas o dono da política é Clean Code); `harness.md` ainda dizia `C1–C10`, defasado desde a delta-026; e nove cortes do eixo Qualidade, entre eles um cabeçalho duplicado por copy-paste no `deps.toml`.

**Recusado:** cortar o CT10 do test-plan como subconjunto do CT9 (eixo Qualidade). Os dois **são** circulares — verificam prosa lendo a prosa —, e é isso que o eixo Spec registrou como A4. Apagar um deixaria o outro igualmente circular e a delta com menos rastro do problema; o conserto é o check mecânico, agora declarado em Fora de escopo com data de entrada.

**Honestidade de saldo (eixo Qualidade):** a troca do `grep` pelo manifesto **não reduz linhas** — saíram 3 de shell e entraram ~21 entre manifesto e comentário, ~10 depois dos cortes. O ganho é cobertura (pré-commit + C2 contra materialização), não economia. O plano dizia "o step do CI encolhe": o step encolheu, o repositório cresceu.
