# DEBT.md — registro de débito, pendências e lições

> Dono canônico de **débito técnico, pendências roteadas e guardas** deste repositório (decisão: [ADR-0007](docs/adrs/ADR-0007-registros-com-dono.md)). IDs `DT-NNN` são globais, estáveis e **nunca reutilizados**. Item quitado **muda de status, não some** — a trajetória aberto→quitado é o registro da evolução. Ticket em ferramenta externa é **projeção** deste arquivo, nunca a fonte ([ADR-0021](docs/adrs/ADR-0021-projecao-de-tickets.md)). Lições (post-mortems) não têm ação pendente e vivem na seção própria, datadas e com desfecho.

## Como ler este arquivo

Cada item é um bloco `### DT-NNN · natureza · estado`, com o título do sintoma em negrito, a descrição em prosa e os campos abaixo. Para ver o que fazer primeiro:

```bash
python3 skills/handoff/scripts/debito.py fila .
```

**As três naturezas.** `débito` é problema técnico a corrigir quando o gatilho disparar. `pendência` é trabalho ou decisão que sobrou de uma delta arquivada (R16). `guarda` é um aviso para **não** "consertar" histórico imutável — não é trabalho, é proteção.

**Os cinco estados** (o cabeçalho do bloco carrega um deles):

| Estado | O que significa | Exige |
|---|---|---|
| `aberto` | reconhecido, ainda não decidido nem pago | Fila, Local, Gatilho |
| `aceito` | dívida deliberada: você mediu e escolheu conviver com ela | **Gatilho** de reavaliação — sem ele, é esquecimento disfarçado |
| `vigente` | guarda permanente; nunca será "resolvida" | nada além da descrição |
| `descartado` | deixou de fazer sentido sem ter sido paga | campo **Encerrado** com data e motivo |
| `quitado` | resolvida de fato | campo **Encerrado** com data e a referência do que resolveu |

**`stale` não é um estado e nunca se escreve aqui.** É uma marca que o script calcula: item de juros altos cujo **cabeçalho** não muda há tempo demais. Editar a prosa não conta — só mudar o estado conta como decisão. Quando a marca aparece, ela cobra uma escolha: agendar, aceitar ou descartar.

**A fila** (`- **Fila:** P3·J9·Pr9`) tem três eixos, cada um em três degraus — 1 baixo, 3 médio, 9 alto:

- **P**rincipal — quanto custa pagar (menos de um dia · cerca de um ciclo · mais de um ciclo)
- **J**uros — o atrito **já observado** (incômodo · atrasa entregas · bloqueia entrega)
- **Pr**obabilidade — chance de a dívida incidir de novo (artefato frio · morno · tocado toda semana)

Deles sai o **score `(J × Pr) / P`**, que ordena a fila e **nunca é gravado** — quem grava cria uma segunda fonte da verdade ([ADR-0020](docs/adrs/ADR-0020-modelo-de-divida-tecnica.md)). Dois sufixos mudam a ordem: ` · trilha` tira o item da competição por score (dívida cara, paga em fatias) e ` · !security(prazo)` é impedimento, que fura a fila. Regra completa em [fila e projeção](skills/handoff/references/debito.md).

## Registro

### DT-001 · débito · aberto
**Parser do check_cycle acoplado ao formato dos templates**

Parser do `check_cycle.py` acoplado ao formato dos templates: blocos `### Rn — VERBO` no `spec.md` **e task em linha única** no `tasks.md` (task quebrada em linhas gera falso ALTO "task sem verificação") — falha ruidosa, não silenciosa

- **Fila:** `P3·J3·Pr9`
- **Local:** [check_cycle.py](skills/spec-feature/scripts/check_cycle.py)
- **Gatilho:** Template mudar de forma
- **Origem:** [PR #2](../../pull/2); sofrido na [delta-004](specs/_archive/004-exclude-portavel/) · aberto em 2026-07-18
- **Ticket:** [#88](../../issues/88)

### DT-002 · débito · quitado
Limiar de PR com 4 espelhos sancionados no `deps.toml`, acima do teto de 2–3 da própria skill — baseline consciente do estado atual

- **Gatilho:** Próxima delta que toque `canonical-rules.md`/`deps.toml` enxuga os espelhos
- **Origem:** [PR #9](../../pull/9) · aberto em 2026-07-19
- **Encerrado:** 2026-07-20, #27 — `SKILL.md`/`detection.md`/`analyze.md` passaram a citar "o limiar canônico"; só `CLAUDE.md` materializa o `500` (1 espelho)

### DT-003 · pendência · quitado
Mecanizar a medição do split condicional de PR: novo check no `check_cycle.py`, com selftest e MUDA no R12

- **Gatilho:** A régua manual falhar numa delta real
- **Origem:** [delta-003](specs/_archive/003-split-pr-delta/) · aberto em 2026-07-19
- **Encerrado:** 2026-07-20, #28 — C7 do `check_cycle.py` mede o diff dos artefatos vs merge-base e reporta BAIXO acima do limiar; `selftest_c7` com git real; MUDA R12 consolidado na delta-009

### DT-004 · débito · quitado
Evidência 100% auto-referencial: o framework nunca rodou em projeto que não seja ele mesmo. **Evidência parcial (2026-07-20):** doc-entregavel, handoff, registros (DEBT/STATE), ADR-0009 e o backfill brownfield rodaram nos 4 repos IMEX (dashboard-operacional, estoque-inteligente, nao-conformidade, travelplanner) — mas o ciclo de deltas com gate (`check_cycle.py`, TRUTH, archive) segue sem execução externa: os 4 TRUTH.md estão vazios, zero `specs/NNN-`; `deps.toml` só no travelplanner

- **Gatilho:** Delta real com gate arquivada e consolidada no TRUTH de um projeto externo (planejada: imex-travelplanner)
- **Origem:** desde o início do repo; registrado na varredura de 2026-07-19 · aberto em 2026-07-12
- **Encerrado:** 2026-07-31, `~/code/imex@8126614` — cumprido em **2026-07-24** pela delta-001 do repo **imex** (camada de gestão do portfólio, sem remote), não pelo travelplanner planejado: ciclo completo com gate (`analyze.md` com C1–C7 limpos e veredito LIBERADO — a 1ª rodada acusou ALTO legítimo no `cobre:` do T3 e foi corrigida antes do implement, o gate pegando erro real fora do próprio framework), archive em `specs/_archive/001-painel-portfolio/` e consolidação no `TRUTH.md` de lá (R1–R5 + RNF1–RNF2 com sufixo `(delta-001)`), release `v0.1.0`. Não foi evento único: em 2026-07-31 o mesmo repo tem a delta-002 `aplicada` e a delta-003 `proposta`, ambas com perfil `completo` aprovado. **Não quita** o DT-013 (o imex não tem `doc-profile.yaml` — gatilho próprio, sem alteração) nem o DT-017 (a rodada não teve tempo/tokens medidos)

### DT-005 · débito · quitado
Gate pré-commit prometido sem mecanismo: `deps.toml`, SKILL da `guarding-doc-integrity`, `canonical-rules.md`, `README.md` e o TRUTH.md ("Não implementado") prometem validação antes de todo commit `.md`, mas não há hook algum (`.git/hooks/` vazio) — a integridade depende da diligência de sessão que a própria skill declara insuficiente

- **Gatilho:** Decidir: hook real (husky/PreToolUse) ou reescrever a promessa para "gate de sessão + CI" em **todos** os promissores listados
- **Origem:** [PR #3](../../pull/3) (promessa); varredura 2026-07-19 (constatação) · aberto em 2026-07-18
- **Encerrado:** 2026-07-28, #53 — hook versionado `.githooks/pre-commit` (ativação `core.hooksPath` por clone) + `templates/pre-commit` na `guarding-doc-integrity` para projetos (validador via `git config sdd-iuri.validator`, opt-in no bootstrap); os 5 promissores reescritos para o mecanismo real; cobre também deleção de `.md` (achado da revisão)

### DT-006 · guarda · vigente
ADR-0001 cita caminho extinto (`~/.claude/skills/`) e delega ao STATE.md uma "limitação conhecida" que nunca existiu lá — ADR é imutável após Accepted; **não corrigir, não migrar**; o grep do RNF5 deliberadamente não varre `docs/`

- **Gatilho:** — (guarda permanente; cai se a ADR-0001 for superseded)
- **Origem:** [PR #6](../../pull/6) (achado 6); varredura 2026-07-19 · aberto em 2026-07-18

### DT-007 · débito · aberto
**Janela cega do C4 quando a consolidação vai direto para a main**

Janela cega residual do C4: consolidação commitada direto na `main` ou `origin/main` desatualizada escapam da comparação por merge-base

- **Fila:** `P3·J1·Pr9`
- **Local:** [check_cycle.py](skills/spec-feature/scripts/check_cycle.py)
- **Gatilho:** Reproduzir o furo numa delta real
- **Origem:** [delta-002](specs/_archive/002-gates/) · aberto em 2026-07-18
- **Ticket:** [#90](../../issues/90)

### DT-009 · débito · aberto
**Bloco aninhado em item de lista vira texto solto no PDF do cliente**

`tabela_cliente.py` não trata bloco aninhado em item de lista fora dos §6/§7 (tabela de decisão dentro de um `- RN-NNN` do §5 vira texto com hífen literal no pdf) — `deepen_indents` só aprofunda bullets; o contorno vive na montagem do entregável e no "Erros comuns" do SKILL.md (#34). **Pr revisto de 1 para 3 em 2026-08-02**: a dívida incide a cada export de PRD de cliente com bloco aninhado, e já mordeu uma vez — "artefato frio" era otimismo. A derivação por churn pede 9, e aí **divergimos**: 4 commits em 6 meses não é "tocado toda semana", é percentil de repo onde quase todo arquivo é frio

- **Fila:** `P1·J3·Pr3`
- **Local:** [tabela_cliente.py](skills/doc-entregavel/scripts/tabela_cliente.py)
- **Gatilho:** Próxima delta que toque a `doc-entregavel`: aprofundar blocos (tabela/parágrafo) dentro de item de lista no `deepen_indents`, com caso no selftest
- **Origem:** rodada de export IMEX 2026-07-20 (PRD estoque, RN-007/008) · aberto em 2026-07-20
- **Ticket:** [#91](../../issues/91)

### DT-008 · débito · quitado
Valores concretos duplicados sem sanção no `deps.toml`: "≤15 linhas" do cabeçalho-resumo do plan (TRUTH RNF1, `cycle.md`, `resumo-plan.md`) e "~10 domínios" do gatilho de particionamento (TRUTH, `cycle.md`, `templates/TRUTH.md`) — o C1 só governa 800 e 500; drift entre esses espelhos passa despercebido

- **Gatilho:** Próxima delta que toque `cycle.md`/templates sanciona os dois valores no `deps.toml` (junto do enxugue do DT-002)
- **Origem:** verificação final 2026-07-20 · aberto em 2026-07-20
- **Encerrado:** 2026-07-20, #27 — dois `[[owner]]` novos no `deps.toml` (`resumo-plan-limiar-linhas` pattern `15 linhas`, `truth-limiar-dominios` pattern `10 dom`); C1 os mantém em sincronia

### DT-011 · pendência · aberto
**Rodapé CONFIDENCIAL e marca d'água dependem de aplicação manual**

Rodapé `CONFIDENCIAL` e marca d'água em todas as páginas são instrução manual no `references/juridico.md` — o `exporta_entregavel.py` não tem flag para nenhum dos dois, então o entregável `juridico-nda`/`requisitos-cliente` depende de o operador aplicar à mão no DOCX/PDF. **Pr revisto de 1 para 3 em 2026-08-02**, acompanhando a derivação: incide em **todo** entregável jurídico, não eventualmente

- **Fila:** `P1·J3·Pr3`
- **Local:** [exporta_entregavel.py](skills/doc-entregavel/scripts/exporta_entregavel.py)
- **Gatilho:** Próxima delta que toque o `exporta_entregavel.py`: flags `--rodape` e `--marca-dagua`, com caso no selftest
- **Origem:** [delta-011](specs/_archive/011-doc-juridico/) · aberto em 2026-07-26
- **Ticket:** [#92](../../issues/92)

### DT-010 · guarda · vigente
Referências a `STATE.md` em `specs/_archive/**`, ADRs Accepted (0001/0007/0008) e entradas lançadas do CHANGELOG — o arquivo foi renomeado para `HANDOFF.md` (delta-010, ADR-0010), mas esses registros são imutáveis/histórico; **não corrigir, não migrar** (mesmo espírito da DT-006)

- **Gatilho:** — (guarda permanente; cai se esses registros deixarem de ser imutáveis)
- **Origem:** [delta-010](specs/_archive/010-handoff-renomeia-state/) · aberto em 2026-07-24

### DT-013 · pendência · quitado
**doc-profile.yaml não tem check mecânico de presença nem de schema**

Check mecânico do doc-profile (presença + schema do `doc-profile.yaml`) no `check_cycle.py` — adiado pelo perímetro do ADR-0006: mecanizar heurística antes do formato estabilizar produziria falso LIBERADO. A ADR-0009 foi promovida sem ele

- **Gatilho:** Formato do perfil estabilizado por uma delta real com o gate do specify num projeto externo (a mesma do gatilho do DT-004)
- **Origem:** [delta-013](specs/_archive/013-higiene/) · aberto em 2026-07-28
- **Ticket:** [#89](../../issues/89)
- **Encerrado:** 2026-08-02, [delta-026](specs/_archive/026-gate-perfil-e-clarify/)/[#105](../../pull/105) — o C11 exige o núcleo (`version`, `decisao`, `publico`, `artefatos` com as 4 categorias) e tolera a cauda, desenho que saiu de medir 7 perfis reais em vez de supor: o gatilho já tinha disparado havia semanas e ninguém tinha varrido (lição de 2026-08-02). Rodado contra os 7 perfis + o template: zero falso ALTO. O parser é PyYAML, dependência admitida por [ADR-0023](docs/adrs/ADR-0023-pyyaml-como-dependencia-admitida.md) — parser próprio foi recusado porque o modo de falha dele é o falso LIBERADO que manteve este débito aberto

### DT-014 · pendência · quitado
Reavaliar a camada de apresentação Figma (categoria `apresentacao`, ADR-0015) quando o preço do `generate_diagram` for anunciado — o motor é beta e "will eventually be a usage-based paid feature"; fora do caminho crítico por design, então a reavaliação é de custo/benefício, não de quebra. Na mesma revisão, verificar o claim não confirmado do export FigJam sem SVG (fonte única, 2026-07-28)

- **Gatilho:** Anúncio de preço do `generate_diagram` (ou primeira materialização real, o que vier antes)
- **Origem:** [delta-018](specs/_archive/018-visual/) · aberto em 2026-07-28
- **Encerrado:** 2026-07-30, delta-020/ADR-0018 — a decisão do usuário antecipou o gatilho: a camada Figma saiu (diagram-design + design-sync a substituem, MUDA R45/R46) e o claim do export FigJam morreu junto com o motor

### DT-012 · pendência · quitado
Primeira execução externa real da skill `descoberta` — rodada planejada no imex-estoque-inteligente (dossiê do kickoff de 2026-07-27) — deve ter o resultado registrado aqui, alimentando a evidência do DT-004 (skill validada fora do próprio repo)

- **Gatilho:** Registrar o desfecho da rodada (dossiê gerado, divergências, o que a skill não cobriu) quando ela ocorrer
- **Origem:** [delta-012](specs/_archive/012-descoberta/) · aberto em 2026-07-27
- **Encerrado:** 2026-07-27, imex-estoque-inteligente[#14](../../pull/14) — rodada completa no mesmo dia: dossiê do kickoff com claims tagueados (transcrição + 15 frames ffmpeg da planilha de 636 SKUs), GLOSSARY/DATA_DICTIONARY populados, 10 divergências vs PRD v1.5, pauta de Mob Elaboration e PRD v1.6 candidata com [PRESUNÇÃO]. Fricções: scene detection é inócua em tela compartilhada estática (amostragem fixa resolveu); nome de sistema citado em reunião veio errado ("SAP" era Sapiens/Senior) — a checagem web da fase 1 pegou. Alimenta a evidência do DT-004 (6ª skill validada externamente; o ciclo de deltas com gate segue sem execução externa)

### DT-015 · pendência · quitado
Abertura do framework à comunidade além do rename: documentação em EN (ou bilíngue — hoje tudo PT-BR, o que limita o alcance do plugin) e `CONTRIBUTING.md` + código de conduta. A ADR-0016 renomeou a identidade; falta o que torna o projeto de fato contribuível por terceiros

- **Gatilho:** Antes de divulgar o framework publicamente (post, submissão ao marketplace oficial de plugins ou primeiro contribuidor externo)
- **Origem:** [delta-019](specs/_archive/019-rename-deltaspec/) · aberto em 2026-07-28
- **Encerrado:** 2026-07-30, #79 — `README.en.md` (espelho sancionado com nota de sincronia), `CONTRIBUTING.md` (fluxo + regra do ciclo para `skills/` + resumo EN) e `CODE_OF_CONDUCT.md` (Contributor Covenant 2.1, tradução oficial pt-BR). Escopo: a interface pública ficou bilíngue; as skills seguem PT-BR por convenção do CLAUDE.md — traduzi-las seria delta própria

### DT-016 · pendência · aberto
**Código alterado fora de delta não tem detector de drift**

Detector de drift código×TRUTH (mudança fora de delta) — o mercado formalizou reconciliação como etapa do ciclo (`/opsx:sync` no OpenSpec, `/speckit.reconcile` no Spec Kit); o C4 só cobre perda no archive, código alterado sem delta não tem detector

- **Fila:** `P9·J3·Pr9 · trilha`
- **Local:** [check_cycle.py](skills/spec-feature/scripts/check_cycle.py)
- **Gatilho:** Primeira ocorrência real de código mudado sem delta, ou antes da divulgação pública (junto do DT-015)
- **Origem:** benchmark SDD 2026-07-29 · aberto em 2026-07-30
- **Ticket:** [#87](../../issues/87)

### DT-017 · pendência · aberto
**Ciclo sem benchmark próprio de tempo e tokens por delta**

Benchmark próprio (tempo/tokens por delta) num projeto externo — hoje a performance do framework é proxy do quadrante OpenSpec (12 min vs 90 min do Spec Kit vs 5,5 h do BMAD, Reenbit mai/2026); falta número medido do próprio ciclo. **Pr mantido em 1 contra a derivação (2026-08-02):** o churn aponta 9 porque o `cycle.md` é o arquivo mais tocado do repo (16 commits em 6 meses), mas a dívida não incide quando o `cycle.md` muda — incide quando alguém precisa de um número de performance, o que só acontece numa rodada externa medida. É o viés registrado do proxy em estado puro; o `Local` aponta o arquivo mais próximo porque esta dívida não mora em arquivo nenhum

- **Fila:** `P3·J1·Pr1`
- **Local:** [cycle.md](skills/spec-feature/references/cycle.md)
- **Gatilho:** Junto da delta externa do DT-004 (colher a medição na mesma rodada)
- **Origem:** benchmark SDD 2026-07-29 · aberto em 2026-07-30
- **Ticket:** [#94](../../issues/94)

### DT-018 · pendência · quitado
ADR decidindo a portabilidade multi-agente: suportar outros CLIs (mercado converge em 8–47 agentes por framework) ou registrar a renúncia deliberada ao Claude Code-only — hoje a exclusividade existe de fato mas não está decidida em registro citável

- **Gatilho:** Antes da divulgação pública (mesmo gatilho do DT-015)
- **Origem:** benchmark SDD 2026-07-29 · aberto em 2026-07-30
- **Encerrado:** 2026-07-30, ADR-0017 — decisão do usuário: Claude Code only por enquanto, renúncia registrada com gatilho de reavaliação (demanda externa concreta ou divulgação pública)

### DT-022 · pendência · aberto
**Modelo de dívida não propagado ao template distribuído**

O `DEBT.md` deste repo tem as colunas de fila e os estados novos, mas o template do `projeto-init` (e a `canonical-rules.md`, copiada para o CLAUDE.md de todo projeto) seguem no formato de 7 colunas — o script degrada com aviso em vez de rejeitar, então nada quebra, mas projeto novo nasce sem priorização

- **Fila:** `P3·J1·Pr3`
- **Local:** [templates/DEBT.md](skills/projeto-init/references/templates/DEBT.md)
- **Gatilho:** Depois do dogfood: quando a fila tiver guiado decisões reais neste repo, propagar template + regra canônica (a decisão de esperar está na spec da delta-023)
- **Origem:** [delta-023](specs/_archive/023-divida-tecnica-e-tickets/) · aberto em 2026-08-01
- **Ticket:** [#99](../../issues/99)

### DT-020 · débito · aberto
**Limiares da fila de dívida escolhidos sem dado empírico**

`STALE_DIAS`, `JANELA_CHURN` e os percentis de churn do `debito.py` são escolha de projeto, não calibração — a ADR-0020 admite isso em prosa e a primeira medição real já mostrou o viés do proxy (churn do arquivo ≠ incidência da dívida)

Duas evidências da **primeira revisão completa das marcas** (2026-08-02, 5 divergências olhadas uma a uma):

1. **O percentil mente em repo frio.** `PERCENTIL_QUENTE = 0.10` chamou de "tocado toda semana" um arquivo com **4 commits em 6 meses** (`tabela_cliente.py`, DT-009): num repositório onde quase todo arquivo é tocado uma vez, o top 10% relativo não significa quente em absoluto. Candidato: piso absoluto de commits antes de o percentil valer.
2. **Divergência justificada não silencia a marca.** Duas divergências foram examinadas e mantidas com motivo escrito (DT-017, DT-021), e a saída do script continua marcando as duas para sempre — "olhei e discordo" fica indistinguível de "ignorei". Uma marca que nunca se resolve deixa de ser cobrança e vira ruído, que é o oposto do desenho. Candidato: campo de divergência aceita com data, no padrão do `aceito` (que também exige gatilho de reavaliação)

- **Fila:** `P1·J1·Pr3`
- **Local:** [debito.py](skills/handoff/scripts/debito.py)
- **Gatilho:** Depois de a fila guiar decisões reais por um trimestre: comparar o que o score priorizou com o que de fato foi pago e recalibrar
- **Origem:** [delta-023](specs/_archive/023-divida-tecnica-e-tickets/) (review de qualidade) · aberto em 2026-08-01
- **Ticket:** [#95](../../issues/95)

### DT-021 · pendência · aberto
**Dialeto de importação do Jira nunca executado contra projeto real**

O `exportar --projeto` emite o lote do `acli jira workitem create-bulk`, mas nenhum projeto Jira existe para validá-lo — o formato veio da doc e do `--generate-json`, não de execução (a ADR-0021 registra a limitação). **Pr mantido em 1 contra a derivação (2026-08-02):** o churn do `debito.py` mede o desenvolvimento do script, não o uso do dialeto Jira — que nunca rodou uma vez e só roda quando existir projeto Jira (delta-017). Frio de verdade

- **Fila:** `P1·J1·Pr1`
- **Local:** [debito.py](skills/handoff/scripts/debito.py)
- **Gatilho:** Primeiro projeto Jira disponível — ou a delta-017, que reusa este mesmo mecanismo no `tickets.md`
- **Origem:** [delta-023](specs/_archive/023-divida-tecnica-e-tickets/) · aberto em 2026-08-01
- **Ticket:** [#96](../../issues/96)

### DT-019 · pendência · aberto
**diagram-design contratado como motor mas fora do caminho de instalação**

`diagram-design` contratado como motor opcional (delta-020/ADR-0018) mas fora do caminho de instalação: nem no `scripts/instala-motores.sh` (só superpowers/ponytail/max) nem na seção 2.2 do README — quem segue o quickstart nunca o instala. Decidir: incluir no instalador (é plugin comum, sem a renúncia de instalador do graphify/ADR-0014) ou documentar a instalação à parte (`/plugin marketplace add cathrynlavery/diagram-design` + `/plugin install diagram-design@diagram-design`). **Pr revisto de 1 para 3 em 2026-08-02**, acompanhando a derivação: incide em **toda** instalação nova que siga o quickstart, e falha em silêncio — o usuário não sabe que ficou sem o motor

- **Fila:** `P1·J1·Pr3`
- **Local:** [instala-motores.sh](scripts/instala-motores.sh)
- **Gatilho:** Primeira adoção real da camada `apresentacao` — a mesma que define o pin (R46)
- **Origem:** pergunta do Iuri em sessão, 2026-07-30 · aberto em 2026-07-30
- **Ticket:** [#93](../../issues/93)

### DT-023 · débito · quitado
**Clarify fecha sem canal humano — o grill se auto-responde e se auto-aprova**

O contrato do clarify é satisfazível sem uma única resposta do usuário: a verificação pós-fase dos adapters só confere formato de ADR e o critério de saída do `cycle.md` diz "ambiguidades resolvidas" sem distinguir *resolvida pelo usuário* de *resolvida por mim*. Somado à regra do próprio `grill-me` ("explore instead of asking" — no deltaspec o TRUTH/ADRs respondem quase tudo), ao auto-score de quem escreveu a spec e ao template do specify já cobrir as cinco dimensões, a entrevista degenera em relatório. Observado nas deltas 004, 005, 006 e 015 — agregados 0.05–0.10, sempre abaixo do limiar na primeira passada, portão nunca disparado; a [delta-004](specs/_archive/004-exclude-portavel/spec.md) admite em comentário "dúvidas resolvidas por exploração do código, sem entrevista". Correção candidata: clarify sem resposta humana registrada não fecha, e sem canal humano o relatório sai marcado `auto-avaliado`

- **Gatilho:** Próxima delta que tocar o contrato do clarify — ou a delta-017, que já reavalia o pin do max ([ADR-0012](docs/adrs/ADR-0012-recontratacao-motores.md)) e abre os mesmos arquivos
- **Origem:** pergunta do Iuri em sessão, 2026-08-02 · aberto em 2026-08-02
- **Encerrado:** 2026-08-02, [delta-026](specs/_archive/026-gate-perfil-e-clarify/)/[#105](../../pull/105) — o clarify passa a declarar `entrevistado`/`auto-avaliado` no cabeçalho, o C12 exige a trilha e o contrato registra que exploração do repositório não conta como resposta do usuário e que quem redige a spec é quem pontua o relatório. O próprio review da delta demonstrou o débito que ela fecha: dois eixos cegos derrubaram três afirmações que o `analyze.md` fazia sobre si mesmo — promessa órfã no `SECURITY.md`, contagem de linhas inventada e fixtures que não cobriam o que declaravam. **O que a delta não mecaniza** está na spec, seção Fora de escopo: qualidade da entrevista e leitura do `<N>` de decisões continuam juízo

### DT-024 · pendência · quitado
**O deltaspec não tem `doc-profile.yaml` e o próprio C11 acusa**

O C11, criado na delta-026, reporta BAIXO na primeira execução contra este repositório: `perfil ausente na raiz`. O framework exige dos projetos-alvo uma decisão registrada de documentação visual (ADR-0009) e não registrou a sua — os 7 projetos externos varridos em 2026-08-02 têm perfil, o dono da regra não. Não é falso positivo: é dogfood faltando. Decidir e declarar quais artefatos são obrigatórios aqui, com `decisao.justificativa` preenchida (o repo é ferramenta, então "nenhum obrigatório + justificativa" é resposta legítima)

- **Gatilho:** Já disparado — o C11 reporta em toda execução do gate; some quando o perfil existir
- **Origem:** [delta-026](specs/_archive/026-gate-perfil-e-clarify/) · aberto em 2026-08-02
- **Encerrado:** 2026-08-02, [#107](../../pull/107) — [`doc-profile.yaml`](doc-profile.yaml) na raiz com **nenhum artefato obrigatório e justificativa preenchida** (decisão do usuário): o repo é plugin de skills mais gates, sem UI, sem persistência e sem entregável de cliente, e os fluxos do ciclo vivem como Mermaid inline no README, que é o artefato de fato mantido. `graphify: false`. Com ele o gate deste repo passa a sair **LIBERADO** limpo

### DT-025 · pendência · aberto
**Nenhum dono para propagar mudança de schema aos `doc-profile.yaml` já existentes**

O C11 nasceu tolerando a cauda opcional exatamente porque categoria acrescentada ao template **nunca propaga retroativamente** — e a varredura de 2026-08-02 mostrou o efeito: dos 7 perfis reais, um declara `version: 2` sem migração documentada em lugar nenhum, e **nenhum** declara o `motores.graphify_backend` que a delta-025 criou. O template evolui, os perfis instalados não, e a `version` não é lida por ninguém. Decidir se `version` passa a significar algo (o C11 hoje não fixa valor) e quem propaga: passo idempotente no `projeto-init`, check que avisa quando o perfil está atrás do template, ou aceitar a divergência por escrito

- **Fila:** `P3·J3·Pr9`
- **Local:** [check_cycle.py](skills/spec-feature/scripts/check_cycle.py) (C11) · [projeto-init](skills/projeto-init/) (dono do template)
- **Gatilho:** Próxima categoria ou chave nova no `doc-profile.yaml` — ou a primeira vez que a divergência de `version` causar erro real
- **Origem:** [delta-026](specs/_archive/026-gate-perfil-e-clarify/) (pendência da seção Dependências e riscos) · aberto em 2026-08-02

### DT-026 · débito · aberto
**O RNF6 verifica espelho com `grep` no CI, ignorando o mecanismo de espelho do próprio repo**

A política de dependência (PyYAML nomeado com link para a ADR-0023 nos quatro espelhos) é verificada por um loop de `grep` no job `ci`. É exatamente o problema que o `deps.toml` + `validate_integrity.py` resolvem — o C1 é *"valor presente no arquivo dono e em cada espelho"* —, então o framework reimplementa à mão o que ele próprio oferece aos projetos-alvo. Trocar por um `[[owner]]` com `pattern = 'ADR-0023'` também leva a checagem para o pré-commit, e não só para o CI. Achado do eixo Qualidade do review da delta-026, adiado por ser troca de mecanismo depois da spec consolidada

- **Fila:** `P3·J1·Pr9`
- **Local:** [ci.yml](.github/workflows/ci.yml) (step do RNF1/RNF6) · [deps.toml](deps.toml)
- **Gatilho:** Já disparado — some quando a verificação migrar; a consolidação do RNF6 no `TRUTH.md` acrescentou um quinto espelho, que o grep atual não cobre
- **Origem:** [delta-026](specs/_archive/026-gate-perfil-e-clarify/) (review em dois eixos) · aberto em 2026-08-02

### DT-027 · débito · aberto
**O C3 herda a exclusão do C2 e deixa CHANGELOG, HANDOFF, DEBT e ADRs sem verificação de link**

O `validate_integrity.py` calcula `scan = scan_globs - exclude_globs` **uma vez** ([linhas 51-52](skills/guarding-doc-integrity/scripts/validate_integrity.py)) e usa o mesmo conjunto no C2 e no C3. O `exclude_globs` existe por um motivo que só vale para o C2 — o próprio `deps.toml` explica: "onde citar valores é legítimo: changelog, diário de bordo, registro de débito, ADRs e deltas arquivadas". Nada disso diz que **link quebrado** ali seja legítimo, e é justamente onde mais se linka: o `DEBT.md` aponta para delta, PR, issue e arquivo em quase todo item, e uma delta que arquiva move os caminhos debaixo dele. Custo observado: em 2026-08-02 o archive da delta-026 deixou dois links apontando para `specs/026-.../` já movido e o `RESULTADO: PASS` saiu limpo; um terceiro (ADR-0009 com nome de arquivo errado no CHANGELOG) também passou. Os três foram pegos à mão, que é exatamente o que o gate existe para não depender. Correção: separar os conjuntos — `exclude_globs` continua valendo para o C2, e o C3 varre tudo que o `scan_globs` casa. **Juros em 1, não 3:** os três links quebrados foram achados na mesma sessão e não atrasaram nada — é incômodo, não bloqueio, e J3 aqui seria o mesmo auto-score generoso que o DT-023 descreve (quem registra o débito é quem o pontua). **Pr em 9 contra a derivação, que pede 1:** o churn olha o `Local` (`validate_integrity.py`, arquivo frio), mas a dívida não incide quando o validador muda — incide quando um dos arquivos **excluídos** muda, e `DEBT.md`/`HANDOFF.md`/`CHANGELOG.md` mudam em toda sessão. Mesmo viés do DT-017, com o sinal trocado

- **Fila:** `P1·J1·Pr9`
- **Local:** [validate_integrity.py](skills/guarding-doc-integrity/scripts/validate_integrity.py) (`main`, montagem do `scan`) · [deps.toml](deps.toml)
- **Gatilho:** Já disparado — três links quebrados escaparam em 2026-08-02; incide em todo archive daqui em diante
- **Origem:** archive da [delta-026](specs/_archive/026-gate-perfil-e-clarify/) · aberto em 2026-08-02
- **Em curso:** corrigido na delta-027, quita no archive dela — o C2 e o C3 passaram a ter conjuntos próprios (`scan_valores` e `scan_links`), com chave `exclude_links_globs` no manifesto e default nomeado para propagar sem migração. Neste repo o C3 saltou de **105 para 171** links verificados (o "161" da primeira versão escondia 10 links que o corte por prefixo silenciava — pego no review). Dois achados que só a medição deu: o `DEBT.md` tem **19** links no atalho `../../issues/N` do GitHub, que viravam falso FAIL e passaram a ser ignorados como `http://` já era; e `specs/_archive/**` tem 26 links quebrados que ficaram **fora por decisão do usuário** — registro de época (R47), rot que a política proíbe corrigir

## Lições
<!-- post-mortems datados, com desfecho; sem ação pendente — ação pendente é DT -->

- **2026-08-02 — A lição de 2026-07-31 reincidiu em 5 semanas: o gatilho do DT-013 já tinha disparado e ninguém varreu.** O DT-013 dizia esperar "formato do perfil estabilizado por uma delta real com o gate do specify num projeto externo", e a leitura corrente era que isso não tinha acontecido — a mesma leitura de memória que a lição de 2026-07-31 já havia proibido. Uma varredura de filesystem de 30 segundos achou **7 `doc-profile.yaml`** em `~/code`, três deles em projeto com delta real; o gatilho estava satisfeito havia semanas. Pior: a varredura não só liberou o débito, ela **desenhou a solução** — medir os 7 perfis mostrou núcleo em 7/7 e cauda (`explicativos` 4/7, `prototipo`/`apresentacao` 1/7) nunca propagada, e é isso que o C11 exige e tolera, respectivamente. Sem a medição, o check teria exigido a cauda e produzido falso ALTO em 6 dos 7. **Desfecho:** a lição anterior tratava a varredura como *conferência* de um débito; ela é também **insumo de desenho**. Débito cujo gatilho fala de "projeto externo" se abre varrendo o filesystem primeiro — e o que a varredura mede entra no design, não só no veredito. Reincidência em 5 semanas sugere que a regra precisa de gatilho mecânico, não de memória: candidato a check que liste débitos cujo gatilho cita projeto externo e cobre a data da última varredura.

- **2026-08-01 — Texto que menciona a sintaxe enganou o parser três vezes na mesma sessão, duas delas dentro do próprio teste que existia para impedir isso.** A lição de 2026-07-28 já dizia a regra, e mesmo assim: (1) um `awk` de conferência leu a palavra "aberto" na prosa de um item quitado e o contou como ativo; (2) o selftest do `debito.py` procurou `gh issue create` por substring e achou primeiro a menção num comentário do roteiro gerado; (3) o assert "o módulo não acessa a rede" procurou `import urllib` no fonte e casou com a própria lista de proibidos. **Desfecho:** a regra vale para *qualquer* leitura, não só para os gates — verificação lê estrutura, nunca texto solto: coluna por índice (`parse_tabela`), comando por início de linha fora de comentário, import por `ast`. Sempre que um teste procurar um literal que ele mesmo contém, ele está errado.
- **2026-08-01 — O `-S` do git não detecta edição de linha, e o `stale` teria nascido cego.** O `dias_parado` usava `git log -S"DT-NNN"`, que só conta quando a string **passa a existir ou some**; editar a linha de um item já registrado não contava, então o relógio do aging nunca reiniciava. O furo só apareceu porque o review cobrou a fixture que o test-plan declarava e não existia (a que assere o `stale` sumindo depois de a linha mudar). **Desfecho:** `-G` no lugar de `-S`; e caso de teste marcado como concluído sem a fixture que ele descreve é dívida disfarçada de cobertura — o review de conformidade passou a conferir declaração × fixture.

- **2026-07-31 — O DT-004 ficou aberto por 7 dias depois de já estar satisfeito, e um quito afirmou o contrário no meio do caminho.** A delta-001 do `~/code/imex` fechou o gatilho em 2026-07-24 (gate + archive + TRUTH num projeto externo), mas o repo **não tem remote** — a mesma cegueira da lição de 2026-07-29 — e nunca entrou nas varreduras que avaliavam o débito. Pior: o quito do DT-012, escrito em 2026-07-27, afirmou que "o ciclo de deltas com gate segue sem execução externa", claim que já era falso havia 3 dias; a linha permanece como está, porque quito é registro de época (mesma guarda do DT-006/DT-010). **Desfecho:** débito cujo gatilho é *"aconteceu em algum projeto"* não se avalia de memória nem da lista de repos com PR — varre-se o filesystem antes de reafirmar que segue aberto. E afirmação de estado dentro de um quito ("segue sem X") é datada por natureza: vale até a próxima varredura, nunca como verdade corrente.
- **2026-07-29 — A análise de impacto do rename achou 1 consumidor; existiam 10, e o inventário errou duas vezes seguidas.** O primeiro levantamento usou `gh search code --owner iuripereira`, que **não indexa a maioria dos repositórios privados** — devolveu só o imex-travelplanner. A segunda tentativa (API de conteúdo do GitHub, arquivo por arquivo: `CLAUDE.md`, `doc-profile.yaml`, `deps.toml`, `specs/TRUTH.md`) chegou a 6, dois deles com acoplamento funcional, e **também estava incompleta**: perdeu repo de outra org (`imex-nao-conformidade` → remote `SuporteImex/nc`), repo **sem remote** (`~/code/imex`, `radar-financeiro`) e quem cita fora dos arquivos-marcador (`iuri.blog`, em `HANDOFF.md` e `.claude/`). Os 4 faltantes só apareceram numa varredura do **filesystem local**, e a conta de 6 sobreviveu tempo demais porque virou "a lista de PRs abertos" — quem não tinha PR sumia da vista. **Desfecho:** inventário de consumidores não sai de busca de código **nem** de API do GitHub; sai de `grep` sobre os diretórios de trabalho, que é o único lugar onde org, remote e nome de arquivo deixam de importar. E o grep que importa num rename não é o nome solto — é `marketplaces/`, `plugins/cache/` e `git config <nome>.`, onde a falha é **silenciosa** (aviso em stderr + `exit 0`, gate passando sem validar).
- **2026-07-28 — Texto que menciona a sintaxe engana parser posicional — duas ocorrências na mesma semana.** O C8 foi enganado por comentário de template citando `Test-plan:` (review da delta-015) e o C9 parseou `(dep: Tn)` citado na prosa da descrição de uma task, gerando falso ALTO no gate real da delta-016. **Desfecho:** regra de desenho para checks novos — campo/aresta só vale na posição canônica (âncora `match`, nunca busca solta na linha) e toda sintaxe nova nasce com fixture de regressão "sintaxe mencionada em prosa/comentário"; aplicada no C8 (`cabecalho()` remove comentários) e no C9 (`DEP.match` pós-ID).
- **2026-07-18 — A allowlist do `.gitignore` cobrou seu preço ao morrer.** Enquanto existiu, `git add -A` pulava em silêncio artefatos novos da raiz; na delta-001 ela engoliu o `.claude-plugin/plugin.json` — o commit "adiciona o manifesto" não continha o manifesto, e a verificação passou porque testava o disco, não o git. **Desfecho:** allowlist morta no #5; lição vigente: *verificação de "arquivo existe" consulta `git ls-files`, não o filesystem.*
- **2026-07-18 — Premissa de plataforma tratada como fato.** O plano da delta-001 assumiu comportamento do carregador de plugins sem validar em execução; dois bugs de plano derivaram disso. **Desfecho:** premissa de plataforma se valida com experimento antes de virar base de plano.
- **2026-07-19 — O plano esquece o CHANGELOG.** Três reincidências corrigidas pelo analyze (deltas 001, 004 e 005). **Desfecho:** o CHANGELOG é task explícita de toda delta; se reincidir, mecanizar (candidato a check do gate).
- **2026-07-19 — Renomear um termo citado em N requisitos custa N blocos MUDA completos.** Observado na delta-001 (5 blocos) e na delta-006. **Desfecho:** é o preço da consolidação mecânica ([ADR-0005](docs/adrs/ADR-0005-consolidacao-mecanica-archive.md)); o caso específico de sufixo foi mitigado na delta-006 (C4 mede perda por ID).
- **2026-07-19 — Revisão do backfill delta-000 concluída.** Contra as skills reais: 8 de 11 itens conferiam; os 3 achados foram tratados na delta-005. **Desfecho:** o C4 protege a integridade da consolidação, não a correção do conteúdo — revisão de conteúdo é evento, não gate.
- **2026-07-20 — O grep case-sensitive deixou passar "Cinco skills" no `marketplace.json`.** A verificação da delta-008 procurou "cinco skills" e o manifesto do marketplace (fora da lista de arquivos da task) dizia "Cinco" — o catálogo distribuiu contagem errada até a verificação final pegar. **Desfecho:** verificação de menção varre com `grep -i` e inclui `.claude-plugin/` quando o assunto é o plugin.
