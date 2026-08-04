# delta-029 — o C3 para de acusar histórico imutável e sintaxe citada
Estado: arquivada · Data: 2026-08-03 · Branch: fix/029-c3-precisao · Perfil: completo — é o gate que destrava a replicação nos 11 consumidores, e um falso positivo aqui trava commit em repo alheio (aprovado: 2026-08-03)

Clarify: entrevistado (2026-08-03) — 3 decisões do usuário
<!-- trilha do clarify (R8): recorte por seção em vez de exclusão de arquivo, tratamento das 4 specs consumidoras e perfil da delta -->

## Contexto (≤3 linhas)
O C3 da delta-027 acusa **96 links mortos** no `imex-travelplanner` ([DT-028](../../DEBT.md)), e aquele repo tem hook `PreToolUse` em `git commit` que roda o validador pelo cache do plugin: no primeiro `/plugin update`, **todo commit lá para**.
Medição de 2026-08-03: **89 dos 96 estão em seções lançadas do `CHANGELOG.md`**, que o Keep a Changelog torna histórico imutável — a mesma classe de `_archive/` e ADRs que o `EXCLUDE_LINKS_PADRAO` já protege, e que ficou de fora por o recorte ser por arquivo.
Dos 7 restantes, **4 estão dentro de crases** num doc que documenta sintaxe de link; os 3 últimos são rot de verdade do repo consumidor, e o gate deve mesmo acusá-los.

## Mudanças

### R1 — MUDA R13 (delta-027): o C3 recorta por seção e ignora sintaxe citada
- DADO um repo com `deps.toml` QUANDO `validate_integrity.py` roda ENTÃO verifica espelhos em sincronia (C1), materialização fora dos sancionados (C2) e links relativos vivos (C3), saindo 1 em qualquer violação
- DADO uma delta ainda aberta propondo valor novo QUANDO o validador roda ENTÃO ela não é acusada — as deltas abertas (`specs/NNN-*/`) ficam fora dos `scan_globs`; dentro de `specs/`, só o `TRUTH.md` consolidado (e `truth/`) entra na varredura
- DADO o `templates/deps.toml` da skill QUANDO um `exclude_globs` mira conteúdo de diretório ENTÃO o glob termina em `**/*.md` (nunca em `**` solto), com comentário no template explicando o porquê — `pathlib` ≤ 3.12 casa só diretórios num `**` final e o exclude viraria no-op
- DADO um arquivo dispensado de citar valor pelo `exclude_globs` QUANDO o C3 roda ENTÃO ele **é varrido mesmo assim** — a dispensa é de materialização (C2), nunca de link vivo; os dois checks passam a ter conjuntos próprios
- DADO um registro imutável — `specs/_archive/**` e `docs/adrs/**` — QUANDO o C3 roda ENTÃO ele fica fora, por chave própria `exclude_links_globs` no `deps.toml`: são registro de época (R47) e apontar rot que a política proíbe corrigir seria ruído
- DADO um `deps.toml` sem a chave `exclude_links_globs` QUANDO o C3 roda ENTÃO vale o **default nomeado do script** — os dois globs de histórico imutável acima —, nunca lista vazia e nunca o `exclude_globs` do C2: vazia despejaria os achados do archive num projeto que nunca pediu (26 só neste repo), e herdar o do C2 manteria o ponto cego em todo projeto que não migrar o manifesto (DT-025)
- DADO um link no formato `../../issues/N`, `../../pull/N` ou `../../discussions/N` QUANDO o C3 o encontra ENTÃO ele o ignora como já ignora `http://` e `/` — é atalho relativo ao repositório do GitHub, não caminho de arquivo, e resolvê-lo como caminho acusaria 19 links vivos do `DEBT.md`
- DADO um link que apenas sobe dois níveis ou mais (`../../docs/...`, `../../../docs/...`) QUANDO o C3 o encontra ENTÃO ele **é verificado normalmente** — o corte casa a **forma** do atalho, nunca o prefixo `../../`; cortar por prefixo silenciava 10 links de `SKILL.md`/`references` para ADR neste repo, a classe que mais apodrece em rename
- DADO um arquivo com seção de versão lançada no padrão Keep a Changelog (`## [X.Y.Z]`) QUANDO o C3 o varre ENTÃO ele para na **primeira** dessas seções — release publicado é histórico imutável, a mesma razão que já mantém `_archive/` e ADRs fora; a seção `[Não lançado]`, que vem antes, continua verificada, e foi nela que estava o link quebrado real que motivou a delta-027
- DADO um link markdown dentro de crase simples (`` `[x](y.md)` ``) ou de bloco cercado por ``` QUANDO o C3 varre a linha ENTÃO ele o ignora — é sintaxe citada, não referência; sem isso, todo documento que **documenta** como escrever link é acusado por citá-lo, e a evidência é o `docs/CLAUDE.md` do `imex-travelplanner`, com 4 exemplos literais
- DADO o recorte por seção QUANDO ele decide se aplica ENTÃO olha o **conteúdo** do arquivo, não o nome — repo que chame o changelog de outro jeito recebe a mesma proteção, e arquivo sem seção lançada é varrido inteiro, como hoje

## Fora de escopo
- Corrigir os 3 links mortos que sobram no `imex-travelplanner` (`docs/implantacao/auditorias/`, `docs/reunioes/` no README) — são rot real daquele repo, e o gate acusá-los é o gate funcionando. Vira trabalho de lá, na preparação da replicação.
- Validar âncora (`#secao`) dentro do arquivo alvo, e link com espaço no alvo: o `MD_LINK` já declara essas duas limitações em comentário desde antes desta delta.
- Check de padrão proibido no `validate_integrity.py` (a metade negativa do RNF6, herdada da delta-028): continua fora, sem mudança.

## Dependências e riscos
- Medição de 2026-08-03 no `imex-travelplanner`, dentro do escopo real do C3 (`scan_globs` menos `exclude_links_globs`): **96 → 7 → 3**. O recorte por seção tira 89; o de crase tira 4; sobram 3 reais.
- **O recorte por conteúdo cega qualquer arquivo abaixo do primeiro `## [X.Y.Z]`,** inclusive se alguém puser conteúdo vivo lá por engano. É o mesmo tipo de cegueira que a delta-025 registrou para `--code-only` do graphify: aceita por ser o que a convenção do Keep a Changelog garante, e declarada aqui.
- **O recorte de crase e cerca cega referência de verdade, e isso tem vítima medida.** A premissa do cenário — "dentro de bloco cercado é sintaxe citada" — é **falsa** para docstring de Python e pseudocódigo que citam arquivo real. No `imex-travelplanner`, 240 links saíram da varredura e **3 deles são referências vivas que resolvem hoje**: `docs/specs/adapter-paytrack.md:61` (docstring dentro de ```` ```python ````), `docs/specs/scoring.md:130` (pseudocódigo) e `docs/CLAUDE.md:85` (crase de tabela). Elas passam a apodrecer em silêncio. Aceito porque a troca é 89 falsos positivos por 3 pontos cegos, mas é **troca, não ganho puro** — e o número que a delta mediu (96 → 3) conta o que parou de gritar, nunca o que parou de vigiar.
- Este repositório tem 3 meses de CHANGELOG e por isso não sentia o problema. A delta nasce de medição em repo alheio — a primeira vez que um consumidor **prova** um defeito do framework antes de o dono notar.
