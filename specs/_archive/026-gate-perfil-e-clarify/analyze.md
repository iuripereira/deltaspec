# Analyze — delta-026 · 2026-08-02

Metade mecânica: `check_cycle.py specs/026-gate-perfil-e-clarify` → **LIBERADO**, C1–C10 sem achados. A primeira rodada acusou **ALTO legítimo** (`bloco MUDA sem citar o alvo vigente`) e o achado era real: o R3 declarava `MUDA` de um "RNF do gate" que **não existe** no TRUTH — nenhum requisito é dono da política de dependência. Corrigido para `ADICIONA RNF1` com Métrica e Verificação próprias; o gate pegou erro de verdade antes do implement.

| # | Severidade | Onde | Inconsistência | Ação sugerida |
|---|---|---|---|---|
| 1 | BAIXO | spec.md RNF1 | A numeração local `RNF1` colide visualmente com o `RNF1` vigente no TRUTH (economia de tokens), embora a regra de archive mande atribuir o próximo livre — vai consolidar como `RNF6` | Aceito: é a regra vigente (o Rn local não migra). Quem ler a delta arquivada precisa lembrar disso — o mesmo já vale para todos os Rn locais |

**Verificações de juízo que passaram:**

- **Check 3 (spec × plan):** o resumo do plan cobre R1, R2 e RNF1 — os mesmos da spec. Nada no plano sem base: o C11 e o C12 saem dos cenários do R1; a prosa normativa da T3 sai do R2; os três espelhos e o step de CI da T4 saem da Métrica e da Verificação do RNF1. O plano não contradiz nenhum cenário de aceite; as severidades que ele codifica (BAIXO para perfil ausente, ALTO para núcleo ausente, nunca CRÍTICO) batem uma a uma com a spec.
- **Check 4 (TRUTH.md) — conferido por comparação programática, não a olho:** `MUDA R12` traz **7 dos 8 cenários vigentes byte-idênticos**; o oitavo (a enumeração dos checks) foi alterado de propósito, de C1–C10 para C1–C12 — é o miolo da delta, não perda. `MUDA R8` repete o único cenário vigente e acrescenta três. `ADICIONA RNF1` não duplica nem conflita: nenhum RNF vigente trata de política de dependência (RNF4 é selftest, RNF5 é portabilidade de caminho).
- **Check 5 (regras canônicas):** a delta **muda uma regra canônica de propósito** — o princípio de stdlib pura do `CLAUDE.md` —, o que é legítimo porque a renúncia está registrada em ADR própria (ADR-0023) e a mudança propaga para os três espelhos no mesmo change, sem deixar promessa órfã. Fora isso: PT-BR em identificadores e prosa; zero valor mágico (o núcleo do perfil vira `NUCLEO_TOPO`/`NUCLEO_ARTEFATOS`, não lista solta); nenhuma sobrescrita de arquivo; CHANGELOG como task explícita (T5); versão segue ancorada na tag. Artefatos somam 470 linhas contra a main — abaixo do limiar de PR, sem split (C7 não disparou), mas a **94% dele** (o número "85" desta linha era inventado; corrigido no review).
- **TDD (obrigatório aqui, tipo `tooling` com lógica pura):** T1 e T2 têm o ciclo completo — teste que falha por `NameError`, mínimo que passa, refactor implícito. As fixtures cobrem o caso feliz, cada modo de falha e, em ambas, a **regressão de sintaxe citada em prosa** que este repo já sofreu três vezes.
- **Perímetro do ADR-0006 respeitado:** nenhuma severidade nova é CRÍTICO, e o que ficou de fora está declarado — a qualidade da entrevista e a leitura do `<N>` de decisões são juízo, não regex.

**Risco que o gate não mede:** o C11 valida o núcleo medido em **7 perfis reais de 2026-08-02**. É amostra, não teorema — perfil futuro com núcleo legitimamente diferente vai acusar falso ALTO e exigir nova delta. O CT14 (rodar contra os 7) é o que segura isso no implement.

**Veredito:** LIBERADO

Ressalvas aceitas: 2026-08-02 — (1) artefatos em 503 linhas contra o limiar de 500: PR único, sem split, porque a branch já passou pelo review adversarial em dois eixos mais verificação independente, que é o que o limiar existe para garantir (decisão do usuário); (2) o C11 acusa BAIXO neste repo até o [DT-024](../../DEBT.md) ser resolvido.

## Apêndice — review em dois eixos (2026-08-02)

Review: convergentes tratados / recusas justificadas — 2026-08-02

Dois eixos independentes em subagentes paralelos (R35), cada um cego ao contexto do outro, com o viés do [DT-023](../../DEBT.md) como alvo declarado: quem escreveu o código, os testes que o julgam e a spec que ambos servem foi o mesmo agente. **Eixo Spec:** APROVADO COM AJUSTES (17 cenários conferidos — 12 cumpridos, 4 parciais, 1 contradito). **Eixo Qualidade:** APROVADO COM AJUSTES (delete-list de 6 itens, saldo −6 linhas; nenhuma gordura estrutural).

**O que o review pegou e o gate não alcança — as três afirmações que este analyze fazia sobre si mesmo e não sobreviveram à verificação independente:**

1. *"sem deixar promessa órfã"* — **falsa**. O `SECURITY.md` é um **quarto** espelho vivo da promessa de zero dependência, e usava a superfície de cadeia igual a zero como argumento de modelo de ameaça. A métrica do RNF1 dizia "três espelhos" e o grep do CI cobria três arquivos, então nada pegaria.
2. *"Artefatos somam 85 linhas"* — **falsa por 5,5×**. O real é 470 (limiar 500). O número não vinha de medição nenhuma.
3. *"as fixtures cobrem cada modo de falha"* — **falsa**. Teste de mutação: apagar a regra de `decisao.data/justificativa` ou a de `publico.*` booleano **não quebrava nenhum selftest**. É literalmente a lição de 2026-08-01 do `DEBT.md` reincidindo.

O que este analyze afirmou sobre os blocos MUDA, por outro lado, procede — o eixo Spec reconferiu por comparação programática independente: 7/8 cenários do R12 byte-idênticos (o oitavo é a enumeração dos checks, o miolo da delta), 1/1 do R8, zero perda silenciosa.

**Convergente (apontado pelos dois eixos — tratado antes do PR):** o C12 chamava `CLARIFY.search(spec_txt)`, varrendo o **documento inteiro**, com o cabeçalho já calculado e ignorado ao lado. Contradiz o cenário que a própria delta escreveu ("âncora canônica do cabeçalho, nunca busca de texto solto") e reintroduz a classe de bug que este repo já sofreu três vezes. Corrigido para `CLARIFY.search(cab)`, com fixture de regressão (trilha íntegra no corpo → ALTO).

**Aplicados:** trilha lida no cabeçalho + fixture · duas fixtures para as regras de `decisao` e `publico` que nenhum teste tocava · `version` declarado sem valor e `obrigatorio` como string deixam de passar · `SECURITY.md` atualizado, incluído no grep do RNF1 e na Métrica (quatro espelhos), com a ADR-0023 corrigida de "três lugares vivos" para quatro · `pip install pyyaml` movido para antes do `Validar YAML`, que já fazia `import yaml` e tornava o step decorativo onde estava · `ImportError` do PyYAML vira mensagem acionável em vez de traceback, e o comando entra na seção de instalação do README (a ADR pedia isso e não tinha sido feito) · `eh_bugfix()` extraído — o predicado estava em três cópias · `adapters.md` deixa de repetir a sintaxe da trilha, que tem dono no `cycle.md` · CT13 reescrito para o que foi de fato verificado, com o "job passa no PR" separado em CT15 aberto.

Depois das correções, 5 mutantes injetados nas regras novas foram todos pegos pelos selftests.

**Recusados, com motivo:**

- *Remover do CI o grep das frases literais de zero-dep* (delete-list 1): é exatamente a guarda de regressão da promessa — as frases não existem hoje **porque** esta delta as removeu. Custa 3 linhas; foi ampliada, não cortada.
- *Cortar a fixture de cauda "redundante"* (delete-list 2): custo zero e valor de documentação por categoria. O outro eixo achou fixture **faltando**, não sobrando.
- *Enxugar a prosa do PyYAML no CHANGELOG e no HANDOFF* (delete-list 3 e 4): os dois estão em `exclude_globs` do `deps.toml` por decisão registrada, justamente porque citam valores ao narrar. O dono canônico do argumento continua sendo a ADR-0023.
- *Trocar o grep do CI por entrada no `deps.toml`* (achado ALTO do eixo Qualidade): é o achado de maior valor estrutural — o repo tem mecanismo próprio de espelho e o RNF1 reimplementa à mão. Mas é troca de mecanismo com efeito no pré-commit, e o `TRUTH.md` ainda vai citar a ADR-0023 no archive (virando mais um espelho). Decidir no archive, não aqui.
- *`campo()` pega a primeira ocorrência no cabeçalho* (A8, BAIXO): resíduo pré-existente compartilhado por todos os checks; prosa dentro do cabeçalho mencionando `Perfil: enxuto` dispensaria o C12. Nenhum caso real, e consertar toca todos os checks — ressalva aceita, não DT.
- *Mover `PERFIL_NUCLEO` para junto do selftest* e *`import tempfile` no topo*: churn sem ganho; o segundo é convenção anterior a esta delta.

**Tamanho do PR:** o próprio apêndice empurrou os artefatos de 470 para 503 linhas e fez o C7 disparar — o review de uma delta engorda a delta. Decisão do usuário (2026-08-02): **PR único, sem split**, registrado na linha de ressalvas acima. O limiar existe para garantir revisibilidade, e esta branch teve dois eixos adversariais mais verificação independente.
