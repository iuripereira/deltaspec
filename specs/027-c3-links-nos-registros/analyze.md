# Analyze — delta-027 · 2026-08-02

Metade mecânica: `check_cycle.py specs/027-c3-links-nos-registros` → **LIBERADO COM RESSALVAS**, único achado o BAIXO do test-plan dispensado, que é a forma sancionada do perfil enxuto (R38).

| # | Severidade | Onde | Inconsistência | Ação sugerida |
|---|---|---|---|---|
| 1 | BAIXO | test-plan.md | dispensado no cabeçalho | Aceito: perfil enxuto aprovado pelo usuário em 2026-08-02; os 8 cenários do R1 mapeiam 1:1 nas fixtures do `--selftest` |

**Verificações de juízo que passaram:**

- **Check 3 (spec × plan):** o resumo do plan cobre R1 e só ele. Cada passo do plano sai de um cenário: os dois conjuntos e o default nomeado saem dos cenários 4–6, o corte do `../../` sai do cenário 7, a propagação ao template sai da consequência de a chave ser nova. Nada no plano sem base na spec, e nenhum cenário sem passo que o realize.
- **Check 4 (TRUTH.md) — conferido por comparação programática:** `MUDA R13` traz os **3 cenários vigentes byte-idênticos** e acrescenta 4. Zero perda; nenhum cenário vigente reescrito.
- **Check 5 (regras canônicas):** PT-BR em prosa e identificadores; o default do C3 vira constante nomeada (`EXCLUDE_LINKS_PADRAO`), não lista solta no meio da função; stdlib pura nesta skill (o PyYAML da ADR-0023 é do `check_cycle`, não deste script); nenhuma duplicação — a exclusão do C2 continua com um dono só e a do C3 ganha o seu, que é justamente o ponto. CHANGELOG é task explícita (T4). **Retificado no review:** a afirmação original "nenhuma duplicação" era falsa — a lista do default nascera em três donos (script, `deps.toml` deste repo, template); a cópia do `deps.toml` saiu e o repo passou a exercitar o caminho de chave ausente.

**Escopo decidido com o usuário, não inferido (clarify de 2026-08-02, 2 decisões):** `specs/_archive/**` fica fora do C3 e o perfil é enxuto. A primeira decisão evita 26 achados em registro que a política (R47, e a guarda DT-006) proíbe corrigir; ela é do usuário porque tem contrapartida real — link de archive apodrece e ninguém saberá.

**Risco que o gate não mede:** a chave `exclude_links_globs` propaga por **default nomeado**, não por migração de manifesto. Projeto-alvo cujo histórico imutável não more em `_archive/`/`docs/adrs/` recebe achados na primeira execução — são links quebrados de verdade, mas chegam sem aviso. É a mesma classe do DT-025, que segue aberto; esta delta escolhe o default menos ruidoso, não resolve a propagação.

**Medição que sustenta o desenho (2026-08-02, mesma semântica do C3 — `path.parent / target`):** registros vivos e ADRs com **zero** link quebrado, então o check nasce verde e todo achado futuro é regressão real; `specs/_archive/**` com **26**, todos fora de escopo por decisão (o "13" apresentado no clarify era erro de medição do meu script ad-hoc — o review pegou); `DEBT.md` com **19** links no atalho `../../` do GitHub, que sem o corte do cenário 7 virariam 19 falsos FAIL na primeira execução.

**Veredito:** LIBERADO

## Apêndice — review (2026-08-02)

Review: convergentes tratados / recusas justificadas — 2026-08-02

Perfil enxuto → os dois eixos fundidos num único subagente (R35), achados classificados por eixo. **Veredito: APROVADO COM AJUSTES**, com 1 ajuste bloqueante.

**O bloqueante, convergente entre os eixos — a delta reintroduziu, com o sinal trocado, a patologia que ela existe para matar.** O corte do atalho do GitHub foi escrito como prefixo (`target.startswith("../../")`) em vez da forma. Consequência medida: **10 links reais deixaram de ser verificados** — `SKILL.md` e `references/` apontando para ADR, exatamente a classe que apodrece em rename — e um link `../../` genuinamente quebrado passou de `FAIL` na `main` para `PASS` nesta branch. Corrigido para casar a forma (`../../(issues|pull|discussions)/`), com fixture de regressão que mata o mutante `ATALHO_GITHUB = ".."`. O C3 subiu de 161 para **171** links, e a renomeação simulada de uma ADR volta a acusar.

**As três auto-afirmações deste analyze que não sobreviveram à conferência independente** — a mesma série do DT-023, agora na terceira delta seguida:

1. *"13 links quebrados em `_archive/`"* — o número não reproduzia sob nenhuma leitura; era artefato de um script ad-hoc meu, não da semântica do C3. O real, sob o check entregue, é **26**. Foi apresentado ao usuário como evidência de uma decisão do clarify — a decisão não muda, mas a evidência estava errada.
2. *"nenhuma duplicação"* — falsa: a lista do default tinha três donos.
3. *"105 → 161 links"* — número verdadeiro apresentado como ganho puro, escondendo as 10 perdas do achado acima. Agregado que esconde regressão é exatamente o oposto de débito honesto.

**Também aplicado:** assert vácuo no selftest (`"[C3]" in stdout` é sempre verdadeiro, porque a linha de resumo carrega o prefixo — virou `"[C3] link morto"`); cenários do R1 recontados de 6 para 8, com o cenário novo do "sobe dois níveis não é atalho"; prescrição desatualizada no corpo do DT-027; três blocos de comentário que repetiam a mesma prosa em quatro arquivos.

**Recusado:** cortar a chave `exclude_links_globs` do `templates/deps.toml` — é o material que o projeto-alvo lê, e o comentário lá é o dono do porquê; quem saiu foi a cópia no `deps.toml` deste repo.

**Ressalva aceita:** o `exclude_links_globs` herda a armadilha do `pathlib` (glob terminando em `**` solto vira no-op) e o comentário da chave nova não a repete — o do `exclude_globs`, logo acima, já avisa. Os valores entregues terminam em `**/*.md`, então não há bug vivo.
