# Analyze — delta-028 · 2026-08-03

Metade mecânica: `check_cycle.py specs/028-propagacao-e-espelhos` → **LIBERADO**, C1–C12 sem nenhum achado.

**Verificações de juízo que passaram:**

- **Check 3 (spec × plan):** o resumo do plan cobre R1, R2 e RNF1 — os mesmos da spec. As três frentes do desenho mapeiam nos três requisitos, e a ordem obrigatória (TRUTH como espelho desde o início) sai do risco declarado, não de invenção do plano. Nenhum passo sem cenário que o sustente; nenhum cenário sem passo.
- **Check 4 (TRUTH.md) — conferido por comparação programática, não a olho:** `MUDA R12` traz **11 dos 12 cenários vigentes byte-idênticos**; o décimo-segundo é o do núcleo do C11, alterado de propósito (sai o `version`) — é o miolo do R1, não perda. Acrescenta 1 cenário novo (o campo sai do template). `MUDA R2` repete os **2 cenários vigentes byte-idênticos** e acrescenta 2. Zero perda silenciosa nos dois blocos.
- **Check 5 (regras canônicas):** a delta **aplica** duas regras canônicas em vez de contrariá-las — a regra de ouro (o `SECURITY.md` deixa de repetir o identificador e passa a apontar para o dono) e o teto de 2–3 espelhos da própria `guarding-doc-integrity`, que o arranjo atual estourava em silêncio. PT-BR em prosa e identificadores; o núcleo continua em constante nomeada (`NUCLEO_TOPO`), agora com um item a menos; CHANGELOG como task explícita (T4). Artefatos somam bem abaixo do limiar de PR — o C7 não disparou.
- **Perímetro do ADR-0006 respeitado:** a delta **afrouxa** um check (o C11 deixa de exigir uma chave) e move outra verificação para um mecanismo existente. Não mecaniza juízo novo, e o que ficou de fora está declarado — o check de padrão proibido, que permitiria fechar a metade negativa do RNF6, é delta própria.

**Decidido com o usuário, não inferido (clarify de 2026-08-03, 3 decisões):** matar o `version` em vez de fazê-lo significar algo; reduzir espelhos **antes** de mecanizar, em vez de criar check novo ou aceitar o `grep`; perfil `completo`. As três tinham alternativa defensável, e a medição foi apresentada antes de cada uma.

**Medição que sustenta o desenho (2026-08-03, 7 perfis reais de `~/code`):** `version` = 1 em seis e 2 em um — e o `2` é justamente o perfil **mais completo**, contra um template que declara `1` com as mesmas 7 categorias. O campo não rastreia schema nenhum. Categorias: 4·4·4·5·5·5·7; `motores` presente em 1 de 7. O `ADR-0023` aparece em 5 arquivos varridos pelo C2, o que faria owner + 4 espelhos sem a redução.

**Risco que o gate não mede:** o C2 passa a governar um **identificador de ADR**, não um valor de negócio como os demais `[[owner]]`. Se amanhã uma skill precisar citar a ADR-0023 legitimamente, o C2 vai acusar — e a resposta certa é entrar no manifesto como espelho, por decisão registrada, nunca ampliar o `exclude_globs` para calar. Fica dito aqui porque é onde a pressa erraria.

**Veredito:** LIBERADO
