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

## Apêndice — review em dois eixos (2026-08-03)

Review: convergentes tratados / recusas justificadas — 2026-08-03

Perfil `completo` → dois eixos independentes em subagentes paralelos (R35). **Eixo Spec: APROVADO COM AJUSTES** (1 ALTO, 3 MÉDIO). **Eixo Qualidade: APROVADO COM AJUSTES** (delete-list de 6 itens, tudo medido por mutação).

**Sem CRÍTICO pela primeira vez em quatro deltas, e o eixo Spec disse por quê:** a patologia das anteriores — a delta furar exatamente no ponto que existe para reforçar — não se repetiu. O cenário vigente mais frágil (`TRUTH:176`, os 10 links de `SKILL.md`/`references` para ADR que a delta-027 quase silenciou) sobreviveu intacto: 10 antes, 10 depois.

**O ALTO — a medição contava o que parou de gritar, nunca o que parou de vigiar.** Os artefatos declaravam uma cegueira (o corte de seção) e omitiam a outra (crase e cerca), que é a que tem vítima real. No `imex-travelplanner`, **240 links saíram da varredura** e **3 são referências vivas que resolvem hoje**: docstring dentro de ```` ```python ````, pseudocódigo em bloco cercado e crase de tabela. A premissa do cenário — "dentro de cerca é sintaxe citada, não referência" — é **falsa** nesses arquivos. A troca continua valendo (89 falsos positivos por 3 pontos cegos), mas é troca, não ganho puro, e agora está escrita como tal na spec, no `SKILL.md` e no template do `deps.toml`.

**Duas fixtures que passavam por omissão, achadas por mutação:**

1. A do span de crase punha a crase e o link real em **linhas diferentes** — um `CODE_SPAN` guloso (`.*`) sobrevivia e engolia **27 links reais** só neste repo. Ao corrigir, descobri um segundo furo que nem o review tinha visto: com apenas **um** trecho em crase na linha, guloso e não-guloso casam igual e o mutante continua vivo. Só o link real **entre dois** trechos em crase mata. A fixture foi refeita assim e o mutante morre.
2. O número de linha do achado — a única parte acionável do relatório do C3 — não era preso por assert nenhum, e ele agora passa por uma função que **filtra** linhas, que é onde off-by-one se esconde. Dois mutantes (`start=0` e índice da lista filtrada) sobreviviam; um assert em `NOTAS.md:1 → de-verdade.md` mata os dois.

**Assert vácuo pré-existente, com agravante:** `assert "[C3]" in stdout` era sempre verdadeiro, porque a linha de resumo carrega o prefixo — e o mesmo valia para `"[C1]"`, que sai como `[C1] limite: OK` no caminho de sucesso. Só o `[C2]` assertava. O agravante é que **esta delta escreveu dois comentários avisando dessa exata armadilha** enquanto deixava a linha de pé, e o repo tem lição registrada sobre isso desde 2026-08-01. Corrigido para a forma da violação; um mutante em que o C1 nunca acusa passou a ser pego — antes sobrevivia.

**Cortes do eixo Qualidade aplicados:** a fixture "arquivo sem seção lançada" foi apagada — 6 mutantes morrem igual com e sem ela, e a `sujo`, vigente desde antes, já cobre o caminho (o CT3 passou a apontar para ela, em vez de declarar cobertura que não discriminava nada); e a terceira seção lançada da fixture do corte, que também não separava mutante nenhum.

**Recusado:** trocar `linhas_vivas` por gerador (−6 linhas). É churn numa função que já passa, e o próprio eixo classificou como opcional. Recusada também a alternativa `"".join(linha.split("`")[::2])` no lugar do `CODE_SPAN`: economiza uma constante e **engole link real quando a crase é ímpar** — entre duas opções do mesmo tamanho, fica a correta na borda.

**Dois números do `TRUTH.md` que o review achou irreprodutíveis e o MUDA reafirma byte a byte:** "26 achados do archive" (hoje 0 — o `_archive/` nem está nos `scan_globs` deste repo) e "19 links do `DEBT.md`" (hoje 22). São drift pré-existente das deltas 027/028, não desta; ficam como estão porque o bloco MUDA repete o vigente por regra, e vira DT se incomodar.
