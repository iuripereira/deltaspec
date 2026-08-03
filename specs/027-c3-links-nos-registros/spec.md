# delta-027 — o C3 verifica link nos registros vivos
Estado: proposta · Data: 2026-08-02 · Branch: fix/027-c3-links-nos-registros · Perfil: enxuto — separa dois conjuntos numa função e trata um formato de link; diff previsto em dezenas de linhas, sem contrato novo (aprovado: 2026-08-02)

Clarify: entrevistado (2026-08-02) — 2 decisões do usuário
Test-plan: dispensado — perfil enxuto; um requisito com 8 cenários que mapeiam 1:1 nas fixtures do `--selftest`, e um test-plan aqui seria transcrição delas
<!-- trilha do clarify (R8): escopo do _archive e perfil da delta -->

## Contexto (≤3 linhas)
O `validate_integrity.py` calcula `scan = scan_globs - exclude_globs` **uma vez** e usa o mesmo conjunto no C2 e no C3, então `CHANGELOG.md`, `HANDOFF.md`, `DEBT.md` e as ADRs ficam sem verificação de link ([DT-027](../../DEBT.md)).
A exclusão foi escrita por um motivo do C2 — "onde citar valores é legítimo" —, que não diz nada sobre link quebrado; e é justamente onde mais se linka: o `DEBT.md` aponta delta, PR, issue e arquivo em quase todo item.
Custo já observado: o archive da delta-026 deixou três links quebrados e o `RESULTADO: PASS` saiu limpo; os três foram pegos à mão.

## Mudanças

### R1 — MUDA R13 (delta-005): o C2 e o C3 deixam de compartilhar o conjunto varrido
- DADO um repo com `deps.toml` QUANDO `validate_integrity.py` roda ENTÃO verifica espelhos em sincronia (C1), materialização fora dos sancionados (C2) e links relativos vivos (C3), saindo 1 em qualquer violação
- DADO uma delta ainda aberta propondo valor novo QUANDO o validador roda ENTÃO ela não é acusada — as deltas abertas (`specs/NNN-*/`) ficam fora dos `scan_globs`; dentro de `specs/`, só o `TRUTH.md` consolidado (e `truth/`) entra na varredura
- DADO o `templates/deps.toml` da skill QUANDO um `exclude_globs` mira conteúdo de diretório ENTÃO o glob termina em `**/*.md` (nunca em `**` solto), com comentário no template explicando o porquê — `pathlib` ≤ 3.12 casa só diretórios num `**` final e o exclude viraria no-op
- DADO um arquivo dispensado de citar valor pelo `exclude_globs` QUANDO o C3 roda ENTÃO ele **é varrido mesmo assim** — a dispensa é de materialização (C2), nunca de link vivo; os dois checks passam a ter conjuntos próprios
- DADO um registro imutável — `specs/_archive/**` e `docs/adrs/**` — QUANDO o C3 roda ENTÃO ele fica fora, por chave própria `exclude_links_globs` no `deps.toml`: são registro de época (R47) e apontar rot que a política proíbe corrigir seria ruído
- DADO um `deps.toml` sem a chave `exclude_links_globs` QUANDO o C3 roda ENTÃO vale o **default nomeado do script** — os dois globs de histórico imutável acima —, nunca lista vazia e nunca o `exclude_globs` do C2: vazia despejaria os achados do archive num projeto que nunca pediu (26 só neste repo), e herdar o do C2 manteria o ponto cego em todo projeto que não migrar o manifesto (DT-025)
- DADO um link no formato `../../issues/N`, `../../pull/N` ou `../../discussions/N` QUANDO o C3 o encontra ENTÃO ele o ignora como já ignora `http://` e `/` — é atalho relativo ao repositório do GitHub, não caminho de arquivo, e resolvê-lo como caminho acusaria 19 links vivos do `DEBT.md`
- DADO um link que apenas sobe dois níveis ou mais (`../../docs/...`, `../../../docs/...`) QUANDO o C3 o encontra ENTÃO ele **é verificado normalmente** — o corte casa a **forma** do atalho, nunca o prefixo `../../`; cortar por prefixo silenciava 10 links de `SKILL.md`/`references` para ADR neste repo, a classe que mais apodrece em rename

## Fora de escopo
- Corrigir os 26 links quebrados de `specs/_archive/**` — registro de época, decisão do usuário no clarify (2026-08-02). Se um dia virar escopo, é delta própria com o R47 na mesa.
- Verificar se o alvo de um link do GitHub (`../../issues/N`) existe de fato — exigiria rede, e o gate roda local por decisão registrada (ADR-0001).
- Validar âncora (`#secao`) dentro do arquivo alvo: o C3 já corta no `#` e ampliar isso é outra classe de check.

## Dependências e riscos
- Medição de 2026-08-02, com a mesma semântica do C3 (`path.parent / target`): registros vivos e ADRs com **zero** link quebrado — o check nasce verde e todo achado futuro é regressão real; `_archive/` com **26**, todos fora do escopo por decisão — o "13" que circulou no clarify era artefato de um script ad-hoc, não da semântica do C3; o número maior reforça a decisão, não a inverte.
- O `exclude_links_globs` é chave nova no `deps.toml` distribuído. O default nomeado existe para que a correção **propague sem pedir migração** — é a resposta desta delta ao problema que o DT-025 descreve, e não o resolve no geral: continua sem dono a propagação de schema para os manifestos já instalados.
- Projeto-alvo cujo histórico imutável não esteja em `_archive/`/`docs/adrs/` recebe achados na primeira execução. É o comportamento correto (são links quebrados de verdade), mas aparece como ruído para quem não esperava — a chave existe justamente para ele declarar o próprio recorte.
