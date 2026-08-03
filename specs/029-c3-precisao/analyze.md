# Analyze — delta-029 · 2026-08-03

Metade mecânica: `check_cycle.py specs/029-c3-precisao` → **LIBERADO**, C1–C12 sem nenhum achado.

**Verificações de juízo que passaram:**

- **Check 3 (spec × plan):** o resumo do plan cobre R1 e só ele. Os dois recortes do desenho saem dos cenários 9 e 10; a decisão "conteúdo, não nome" sai do cenário 11. A separação I/O × lógica pura (`linhas_vivas` recebe e devolve texto) não está na spec porque é regra canônica do repo, não requisito da delta — e o plano a nomeia como tal.
- **Check 4 (TRUTH.md) — conferido por comparação programática, e desta vez sobre o bloco **único** desta delta:** `MUDA R13` traz os **8 cenários vigentes byte-idênticos** e acrescenta 3. Zero perda. *(A delta-028 falhou justamente aqui — declarou "os dois blocos" tendo três; esta tem um só, e ele foi comparado.)*
- **Check 5 (regras canônicas):** os dois recortes viram constantes nomeadas (`CORTE_LANCADO`, `CODE_SPAN`, `CERCA`), não regex solta no laço; função pura separada de I/O; PT-BR em prosa e identificadores; stdlib pura nesta skill; CHANGELOG como task explícita (T4). Artefatos bem abaixo do limiar de PR.
- **Perímetro do ADR-0006 respeitado:** a delta **restringe** o que um check acusa, com base em convenção pública (Keep a Changelog) e em sintaxe de markdown — não mecaniza juízo novo.

**Decidido com o usuário (clarify de 2026-08-03, 3 decisões):** recorte por seção em vez de excluir o arquivo inteiro (a alternativa "excluir `CHANGELOG.md` por default" perderia a seção `[Não lançado]`, que é onde estava o link real que motivou a delta-027); tratar as 4 specs consumidoras à mão em vez de dar corte por data ao C12; e o perfil `completo`.

**Medição que sustenta o desenho (2026-08-03, no `imex-travelplanner`, dentro do escopo real do C3):** 96 → 7 com o corte de seção → **3** com o de crase. Os 4 que só o segundo pega estão num doc que **documenta sintaxe de link**; os 3 finais são rot real do README de lá, e o gate deve acusá-los.

**Risco que o gate não mede:** o recorte por conteúdo cega tudo abaixo do primeiro `## [X.Y.Z]`. Se alguém puser conteúdo vivo lá por engano, o C3 não olha — é a mesma classe de cegueira que a delta-025 registrou para o `--code-only` do graphify, aceita porque é o que a convenção do Keep a Changelog garante.

**O que esta delta é, e vale registrar:** a primeira em que um **repositório consumidor provou um defeito do framework antes de o dono notar**. Este repo tem três meses de CHANGELOG e passava no próprio gate; o `imex-travelplanner` tem um ano e trava. A evidência auto-referencial que o DT-004 apontava por dois meses deixou de ser o único insumo.

**Veredito:** LIBERADO
