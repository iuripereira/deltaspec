# Ciclo deltaspec — máquina de estados e fases

## Estados da delta (vivem no cabeçalho do `spec.md`)

```
proposta ──(analyze LIBERADO + implement + review + merge)──▶ aplicada ──(consolidação)──▶ arquivada
```

- **proposta** — de specify até o fim do review. Vive em `specs/NNN-nome/`.
- **aplicada** — código mergeado; falta consolidar. Estado transitório: não pare aqui.
- **arquivada** — consolidada no `TRUTH.md` e movida para `specs/_archive/NNN-nome/`.

## Fases — critérios de entrada/saída

| Fase | Entrada | Saída (critério de pronto) | Motor |
|---|---|---|---|
| specify | pedido de feature; `TRUTH.md` lido | `specs/NNN-nome/spec.md` rascunho no template; branch `tipo/NNN-nome` criada | nativo |
| clarify | spec rascunho | ambiguidades resolvidas — distinguindo o que o **usuário** respondeu do que o **agente** resolveu sozinho; fronteira do motor esgotada (critério de saída: adapters.md); spec consolidada: todo Rn com DADO/QUANDO/ENTÃO; RNFs aplicáveis (desempenho, segurança, acessibilidade, ...) elicitados com métrica; ADRs gravados se domain-modeling; **trilha do clarify no cabeçalho** declarando se houve canal humano (C12) | mattpocock-skills:grilling / + domain-modeling |
| plan | spec consolidada | `plan.md` em `specs/NNN-nome/` com o cabeçalho-resumo (≤15 linhas) prependido | superpowers:writing-plans |
| tasks | plan.md | `tasks.md`: cada task com arquivos, `cobre:` e verificação, ordenada por dependência, com arestas `(dep: Tn)` explícitas quando há bloqueio (C9 valida) | nativo (template) |
| test-plan | tasks.md pronto | `test-plan.md` derivado dos cenários da spec e das verificações das tasks (template; C8 valida; dispensável no perfil enxuto — tabela abaixo) | nativo (template) |
| analyze | spec + plan + tasks | `analyze.md` com veredito LIBERADO (ou ressalvas aceitas pelo usuário) | nativo (analyze.md) |
| implement | analyze liberado | todas as tasks concluídas com as verificações rodadas; TDD conforme coluna `tdd` do tipo; unidades paralelizáveis podem rodar em worktrees (seção abaixo) | superpowers:executing-plans ou subagent-driven-development |
| review | implementação completa | eixo Spec ok; eixo Qualidade ok com delete-list tratada; convergentes tratados (contrato: adapters.md, "Review em dois eixos"; perfil enxuto: eixos fundidos — tabela abaixo) | superpowers + ponytail:ponytail-review |
| archive | PR mergeado | Estado: arquivada; TRUTH.md consolidado; diretório em `_archive/` | nativo (regras abaixo) |

Fim de cada fase = **commit dos artefatos na branch da delta** (regra canônica: fim de etapa = commit). Não acumule o ciclo inteiro num commit só.

## Gate de documentação visual (doc-profile — ADR-0009)

Na fase **specify**, leia o `doc-profile.yaml` da raiz do projeto — a decisão registrada sobre documentação visual.

- **Presente** → gere/atualize **somente** os artefatos com `obrigatorio: true` e `fase: spec`, com a ferramenta e a pasta de saída declaradas, até o fim do **plan** (antes do analyze). Qualquer diagrama fora do perfil exige **pergunta explícita ao usuário antes** — nunca gere por iniciativa própria.
- **Ausente** → siga como hoje (sem gate) e emita o warning: "projeto sem `doc-profile.yaml` — considere criar (template no projeto-init) para registrar a decisão de documentação visual (ADR-0009)". Nenhum projeto existente quebra.
- **Perfil sem artefato obrigatório** → válido se `decisao.justificativa` estiver preenchida; vazia, aponte a pendência ao usuário.
- **`publico.cliente: true`** → no `momento` declarado em `entregaveis` (`entrega-prd` | `fechamento-fase`), invoque a skill **`doc-entregavel`** para exportar o PDF/DOCX congelado em `docs/entregaveis/`.

Documentação **cliente** é isenta da economia de tokens (exceção registrada na ADR-0009); a **interna** segue o RNF1 — Mermaid inline enxuto, mantido junto do código a cada mudança relevante.

**A ferramenta segue a categoria do diagrama** (tabela normativa no ADR-0009): fluxo/sequência/ERD rápido → Mermaid; modelo de dados canônico → DBML; arquitetura de alto nível/C4 → Structurizr DSL; UML/casos de uso → PlantUML; explicativos → Excalidraw. Não reaproveite diagrama pronto de outra categoria.

**Categoria `modelo-dados` obrigatória** → o motor é a skill [`modelo-dados`](../../modelo-dados/SKILL.md) (delta-073): além do `.dbml`, materializa `docs/data-model.md` (camada conceitual + ERD **derivado**) até o fim do plan; no analyze, o `check_data_model.py check` roda ao lado do `check_cycle.py` (comando e omissão: [analyze.md](analyze.md)). Regra das camadas e donos: `camadas.md` da skill ([ADR-0038](../../../docs/adrs/ADR-0038-modelo-de-dados-em-tres-camadas-com-dono-unico.md)).

**Apresentação NÃO é categoria** — é a flag `apresentacao: true` no artefato ([ADR-0029](../../../docs/adrs/ADR-0029-apresentacao-como-modo-e-html-autocontido-canonico.md)). Acabamento é eixo perpendicular à categoria: marcar a arquitetura não troca o Structurizr por outra coisa, só declara que ela também sai com acabamento editorial. A materialização acontece no **archive** (regras abaixo), não no specify.

**Prosa de regras e processos** (spec, PRD, entregável): siga [references/prosa.md](prosa.md) — uma regra por frase, DEVE/NÃO DEVE/PODE, regra combinatória vira tabela de decisão, fluxo > 3 passos vira diagrama + passos numerados. O checklist do guia roda antes de congelar qualquer baseline.

## Projeção Jira (doc-profile — `motores.jira`, delta-017)

Ao fim da fase **tasks**, leia `motores: jira: {projeto: CHAVE}` no `doc-profile.yaml` (mesmo padrão do graphify — decisão registrada por projeto). **Presente** → rode `python3 ${CLAUDE_PLUGIN_ROOT}/skills/spec-feature/scripts/tickets.py gerar specs/NNN-nome` (nasce `tickets.md`: 1 épico + 1 ticket por task, arestas `dep:` como links de bloqueio) e `python3 ${CLAUDE_PLUGIN_ROOT}/skills/spec-feature/scripts/tickets.py exportar specs/NNN-nome --saida DIR` (`.sh` de creates unitários, dialeto em [debito.md](../../handoff/references/debito.md)). **A skill executa o `.sh`** — o script nunca acessa a rede — e grava as chaves devolvidas na coluna `Externo` do `tickets.md`: é ela, e não o título, que garante idempotência. **Ausente** → a projeção se omite com no máximo 1 linha de aviso (RNF2); o `tasks.md` segue valendo sozinho.

**Escada de automação da ida (cenário 3 do R1):** `acli` disponível e autenticado → a skill roda o `.sh` emitido. Sem ele → tenta o Rovo MCP (`/v1/mcp`) se o conector estiver autenticado no harness. Sem os dois → REST da Atlassian se houver credencial. Sem nenhum → os arquivos emitidos (`tickets.md` + `.sh` + corpos) ficam como entregável, e a skill avisa em 1 linha qual degrau faltou (RNF2) — a degradação nunca é silenciosa. Degraus 2 e 3 nascem não exercitados (risco registrado na spec, delta-017).

**Volta:** `python3 ${CLAUDE_PLUGIN_ROOT}/skills/spec-feature/scripts/tickets.py diff specs/NNN-nome --externo jira.json`, com `jira.json` colhido por `acli jira workitem search --jql "project=CHAVE AND labels=delta:NNN" --json`. Emite a tabela *tickets.md diz × Jira diz × impacto × ação proposta* (formato do R27) — sempre **proposta + aprovação humana**, nunca escrita automática. Detalhe de flags e subcomandos: `--help` do script.

## PR da delta — split condicional (delta-003)

O limiar de tamanho de PR (dono: regra canônica do git-workflow, no projeto-init) vale para o PR da delta — **e os artefatos do ciclo contam**. O **C7** do `check_cycle.py` mede isso no analyze e reporta BAIXO quando os artefatos passam do limiar (sem git ou sem merge-base o C7 se omite; nesse caso meça à mão):

```bash
git diff origin/main --shortstat -- specs/NNN-nome/
```

- **Linhas adicionadas acima do limiar** → split: os artefatos são mergeados primeiro num PR próprio (branch `docs/NNN-nome`, commit `docs(NNN-nome): artefatos da delta-NNN`); a implementação segue depois em `tipo/NNN-nome`, com PR separado.
- **Dentro do limiar** → um único PR carrega artefatos + implementação (fluxo vigente).

Implementação que sozinha excede o limiar já tem regra própria: fim de etapa = commit + PR — não acumule etapas. O valor do limiar não é repetido aqui de propósito (fonte canônica única); em repo com `deps.toml`, o C2 do `validate_integrity.py` acusa a materialização.

Ciclo reduzido (site-estatico): specify → plan → implement → review. clarify/analyze entram sob demanda (spec ambígua ou toque em regra canônica).

## Triagem do clarify (escolha do motor — reporte ao usuário)

Gatilhos, seleção do motor (`grilling` puro × `grilling` + `domain-modeling`) e fallback: seção grilling/domain-modeling de `adapters.md`. Reporte a escolha ao usuário.

## Perfil de execução da delta (R1, delta-015 — ADR-0013)

No specify, a IA propõe `Perfil: completo|enxuto` no cabeçalho com justificativa de 1 linha (escopo/risco); **só vale com aprovação explícita do usuário** registrada no cabeçalho (`aprovado: AAAA-MM-DD`). Sem o campo → `completo` (retrocompatível, sem migração). O perfil opera **dentro** do ciclo do tipo (R10) — não reintroduz fase que o tipo exclui.

| Estágio | completo | enxuto |
|---|---|---|
| clarify | roda | sob demanda (só com ambiguidade apontada) |
| test-plan | obrigatório (C8: ALTO se ausente) | dispensável — `Test-plan: dispensado — <motivo>` no cabeçalho (C8: BAIXO) |
| review | dois eixos em subagentes paralelos (R35) | eixos fundidos num único subagente (regra: adapters.md, "Review em dois eixos") |
| plan · tasks · analyze · archive | integrais | integrais |

## Execução paralela por unidades (delta-016)

O grafo do `tasks.md` (arestas `(dep: Tn[, Tm])`; task sem `dep:` é livre) define as
unidades de execução: **duas tasks sem caminho entre si são paralelizáveis**. No
implement, harness com subagentes → cada unidade pode rodar num subagente com
worktree isolada (motor `superpowers:using-git-worktrees`, contrato em adapters.md),
com convergência (merge das worktrees) antes do review. Harness sem subagentes ou
sem worktree → execução sequencial na ordem topológica, com aviso de degradação
(RNF2). O C9 valida o grafo — dep existente e aciclicidade; arquivo sem nenhum
`dep:` vale como cadeia linear implícita pela ordem (retrocompatível).

## Trilha de auditoria de aprovação (delta-016)

Toda aprovação humana que o ciclo exige fica registrada como linha citável no
artefato da própria fase — sem arquivo de auditoria separado (renúncia ao audit.md
do AI-DLC: ADR-0014). A trilha sobrevive ao archive junto com os artefatos.

| Aprovação | Artefato (dono) | Sintaxe |
|---|---|---|
| Perfil da delta (R36) | cabeçalho do `spec.md` | `Perfil: <perfil> — <justificativa> (aprovado: AAAA-MM-DD)` |
| Trilha do clarify (R8) | cabeçalho do `spec.md` | `Clarify: entrevistado (AAAA-MM-DD) — <N> decisões do usuário` · `Clarify: auto-avaliado (AAAA-MM-DD) — sem canal humano` |
| Prototipação (R37) | seção Contexto do `spec.md` | `Protótipo (aprovado: AAAA-MM-DD) — <caminho>` |
| Ressalvas do analyze | `analyze.md`, linha após o veredito | `Ressalvas aceitas: AAAA-MM-DD — <resumo>` |
| Achados do review | `analyze.md`, apêndice do review | `Review: convergentes tratados / recusas justificadas — AAAA-MM-DD` |

## Prototipação opcional (R2, delta-015 — estágio CONDITIONAL)

Delta cujo escopo toca interface ou fluxo que o stakeholder precisa ver → no specify a IA **propõe** o estágio com justificativa; executa só com aprovação do usuário (mesma regra do gate visual, ADR-0009). Forma: categoria `prototipo` do `doc-profile.yaml` (dono da decisão); perfil ausente ou sem a categoria → default HTML estático navegável em `docs/prototypes/NNN-nome/`, versionado e referenciado no Contexto da delta. Sem gatilho → o estágio se omite com no máximo 1 linha.

## Delta bugfix (R4, delta-015)

`Tipo: bugfix` no cabeçalho, template `templates/bugfix-spec.md` (sintoma, reprodução DADO/QUANDO/ENTÃO, causa-raiz, teste de regressão obrigatório), numeração NNN global. Pipeline: specify → plan curto → implement → review; clarify, tasks e test-plan sob demanda; analyze roda (read-only). Archive: sem mudança de requisito → move para `_archive/` sem consolidar no TRUTH.md; com bloco MUDA → consolidação normal (R6).

## Consolidação entrevista → delta spec (passo nativo, ex-to-spec)

Ao fim do clarify, sintetize **da conversa já feita** — NUNCA re-entreviste:
1. Cada decisão da entrevista vira um Rn novo ou ajusta um existente, sempre com DADO/QUANDO/ENTÃO verificável.
2. Qualidade discutida (desempenho, segurança, acessibilidade, capacidade, ...) vira RNFn com Métrica e Verificação. Qualidade sem limiar fechado na entrevista **não vira RNF** — vai para "Dependências e riscos" como pendência ("rápido" não é requisito; "p95 < 300ms" é).
3. Renúncias explícitas vão para "Fora de escopo".
4. Pendências sem resposta vão para "Dependências e riscos" — não invente resposta.
5. Decisão durável discutida sem ADR gravado? Registre o ADR agora (template do projeto, `docs/adrs/`), antes do plan.

## Regras de archive (consolidação no TRUTH.md)

O `TRUTH.md` vive em **`specs/TRUTH.md`**. Blocos MUDA/REMOVE da delta devem **citar o alvo vigente** nele (ex.: "MUDA R2 (delta-001)"). `specs/TRUTH.md` inexistente (primeiro archive) → crie de `templates/TRUTH.md` antes de consolidar.

1. **ADICIONA** → o requisito entra no domínio correspondente como **heading `### Rn (delta-NNN) — título`** seguido dos cenários DADO/QUANDO/ENTÃO em bullets — um cenário por bullet, efeitos atômicos do mesmo commit como sub-bullets de 1 linha (formato ADR-0034; a âncora `Rn (delta-NNN)` fica na linha do heading, que é o que o C4 lê). No TRUTH particionado, o destino é a partição `truth/<dominio>.md` do domínio — domínio novo sem partição óbvia → pergunte ao usuário o destino. Recebe o **próximo número R livre do TRUTH** — a numeração é global e nunca reutiliza número (nem de requisito removido); o Rn local da delta não migra. TRUTH legado em bullets (`- Rn (delta-NNN) — ...`) continua válido — nenhum gate exige migração; consolide no formato do arquivo em que está.
2. **MUDA** → substitui **integralmente** o requisito vigente (texto + cenários) pelo bloco da delta; o sufixo passa a `(delta-NNN)` da delta nova. Por isso o bloco MUDA deve conter a versão completa do requisito — cenário vigente que continua valendo é **repetido na delta**; o archive consolida mecanicamente, não infere intenção.
3. **REMOVE** → apaga a entrada do TRUTH.md.
4. **Blocos RNFn** seguem as regras 1–3 igualmente, consolidando na seção **Não funcionais** do TRUTH.md (Métrica e Verificação incluídas), com numeração RNF própria — também global e nunca reutilizada.
5. Atualize `Estado: arquivada` no spec.md e mova `specs/NNN-nome/` → `specs/_archive/NNN-nome/` (com plan.md, tasks.md, analyze.md juntos — o histórico completo vive no archive). **No mesmo passo, recalcule os links relativos dos artefatos a partir do destino novo** — o move soma um nível de profundidade (`](../../` → `](../../../` no caso comum), mas link que aponta para dentro de `specs/` tem outra conta, então recalcule em vez de somar às cegas. Atalho do GitHub (`(../)+issues|pull|discussions/N`) fica fora: não é caminho de arquivo. O **C13** do `check_cycle.py` acusa o que sobrar — a regra 6 já manda rodá-lo aqui, então não há passo novo a lembrar.
6. **Verificação obrigatória (diff):** todo Rn/RNFn ADICIONA/MUDA da delta presente no TRUTH.md consolidado; todo REMOVE ausente; nenhum requisito de outras deltas alterado. Perda de requisito no archive é o pior bug do ciclo — por isso é mecânica, não conferida a olho: rode `scripts/check_cycle.py <delta>` **depois de consolidar** (antes ou depois de commitar — o C4 compara o TRUTH.md contra o merge-base da branch com a main, sem janela cega pós-commit) e ele acusa CRÍTICO em requisito removido que a delta não declara como alvo de MUDA/REMOVE. A comparação contra o que o bloco MUDA **declara** (cenário que a delta prometeu e a consolidação não entregou) só roda com a delta em `Estado: arquivada`: antes disso, `para` é sempre o número antigo e toda delta que **cresce** um requisito sairia ALTO sem ter nada a corrigir — foi o que aconteceu nas deltas 086 e 087 (delta-088).
7. **Pendência roteada:** item `- [ ]` em "Dependências e riscos" do spec arquivado é pendência aberta — registre-a com **`debito.py novo`** (`--natureza pendência --origem delta-NNN`), que calcula o `DT-NNN` e escreve `debts/ativos/DEBT_DT-NNN-<topico>.md` já validado, e marque `- [x]`, no mesmo commit da consolidação. Projeto sem `debts/` cria a pasta a partir do template da projeto-init nesse momento (registro legado converte com `debito.py migrar`). O C6 do `check_cycle.py` acusa ALTO para `- [ ]` remanescente.
8. **Entrada no CHANGELOG:** escreva em `## [Não lançado]` a linha da delta, na categoria correspondente — **uma frase com a referência do PR** (formato e limite: regra canônica do módulo release-triad; gate: `scripts/check_changelog.py`). A narrativa fica no PR, na delta que acabou de arquivar e na ADR; a entrada só referencia. Como a narrativa é do PR, ela tem de descrever a branch inteira: antes do merge, releia título e descrição contra os commits que entraram depois da abertura — com mais de um commit, o squash leva o **título do PR** para a base (regra canônica do módulo git-workflow). É aqui que a entrada é escrita porque é aqui que o "pronto" fecha e a tag corta — antes da delta-062 esse passo não existia escrito em lugar nenhum e dependia de disciplina, com três reincidências registradas na `debts/LICOES.md`.

Particionamento do TRUTH.md: acima de ~800 linhas, ~40.000 tokens aproximados ou ~12 domínios claros → dividir em `truth/<dominio>.md` e o TRUTH.md vira **índice enxuto** — propósito, tabela domínio → link da partição → contagem de requisitos, sem lista de IDs (sem gerador ela vira índice mentiroso — ADR-0034; a âncora do heading e o grep respondem "onde está R42"). Cada partição abre com `# <Domínio> — verdade vigente`, o comentário de partição e `> Propósito:`; projeto novo nasce **monolítico** no formato do template e particiona só quando o C5 acusar. Particionado, o C5 mede cada partição isoladamente — o custo que importa é o da maior, não a soma.

### Página de apresentação (delta-042, ADR-0029)

Roda no archive, **junto da consolidação** e antes do move para `_archive/` — o conteúdo já estabilizou, que é o motivo de não rodar no specify.

Leia o `doc-profile.yaml`. Ao menos um artefato com `apresentacao: true` → gere `<apresentacao.saida>/NNN-nome.html` seguindo [html-autocontido.md](html-autocontido.md), partindo de [exemplo-apresentacao.html](exemplo-apresentacao.html), com uma seção ancorada por categoria marcada. Bloco `apresentacao` ausente → defaults `motor: html-editorial`, `saida: docs/apresentacao/`, paleta default.

| Situação | O que fazer |
|---|---|
| Nenhum artefato marcado | Nada é gerado e **nada é avisado** — a ausência de marcação é decisão registrada, não esquecimento |
| `prototipo` marcado | Recuse a marcação com a razão — protótipo já é HTML interativo ([ADR-0013](../../../docs/adrs/ADR-0013-selecao-adaptativa-e-bugfix.md)) — e apenas **linke** o protótipo na página |

Escolha do motor e o que fazer quando ele falta: [adapters.md](adapters.md), seção apresentação — ela é dona do contrato e do fallback, aqui não se repete.

Unidirecional: o fonte versionado da categoria (`.mmd`, `.dsl`, `.dbml`) é o dono do conteúdo; a página se refaz a partir dele e, em divergência, o fonte governa. Edição feita na página nunca retorna ao git como fonte.

## Economia de tokens (NFR de primeira classe)

Artefatos **duráveis** (spec.md, TRUTH.md) são enxutos — limites nos templates. O `plan.md` é artefato **efêmero de execução**: verboso por design (executável por subagente sem contexto), arquivado junto com a delta e fora do caminho depois. Não pós-processe o plan para "enxugar" — só o cabeçalho-resumo importa para humanos e para o analyze.
