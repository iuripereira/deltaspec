# deltaspec

**Spec-Driven Development por delta specs**, para o [Claude Code](https://claude.com/claude-code).

**[Read in English](README.en.md)**

Em vez de manter um documento de requisitos gigante que envelhece mal, cada feature escreve **só o que muda**. Um único arquivo — o `specs/TRUTH.md` — guarda o que vale hoje.

> **É o git, aplicado a requisitos.** Cada feature é um *commit* de spec (ADICIONA / MUDA / REMOVE). O `TRUTH.md` é o *working tree*: o estado atual, com todos os commits já aplicados. As specs antigas vão para `specs/_archive/` — elas são histórico, não verdade.

[Versão corrente: tags](https://github.com/iuripereira/deltaspec/tags) · 10 skills · Licença MIT

---

## Índice

1. [O problema](#1-o-problema)
2. [Instalação](#2-instalação)
3. [Comece um projeto](#3-comece-um-projeto)
4. [O ciclo de uma feature](#4-o-ciclo-de-uma-feature)
5. [O dia a dia](#5-o-dia-a-dia)
6. [As skills](#6-as-skills)
7. [As checagens automáticas](#7-as-checagens-automáticas)
8. [Onde cada coisa mora](#8-onde-cada-coisa-mora)

---

## 1. O problema

Você escreve um PRD de 40 páginas, implementa 3 features — e o PRD já mente. Ninguém reescreve o documento inteiro a cada mudança, então ele vira ficção.

A saída do deltaspec: **o documento grande nunca é escrito à mão.** Ele é montado a partir das deltas.

```mermaid
%%{init: {'theme':'base','themeVariables':{'lineColor':'#5b6472','primaryTextColor':'#1f2937','primaryBorderColor':'#2b2b2b','edgeLabelBackground':'#ffffff'}}}%%
flowchart LR
    d1("delta-001<br>ADICIONA R1, R2") --> T
    d2("delta-002<br>MUDA R2<br>ADICIONA R3") --> T
    d3("delta-003<br>REMOVE R1") --> T
    T("specs/TRUTH.md<br><b>o que vale hoje</b>")
    T --> arq("specs/_archive/<br>histórico das deltas")

    classDef delta fill:#cfe9f3,stroke:#2b2b2b,stroke-width:1.5px,color:#1f2937
    classDef verdade fill:#f9c3d4,stroke:#2b2b2b,stroke-width:1.5px,color:#1f2937
    classDef hist fill:#f4eccd,stroke:#2b2b2b,stroke-width:1.5px,color:#1f2937
    class d1,d2,d3 delta
    class T verdade
    class arq hist
```

O que isso te dá:

| Você ganha | Como |
|---|---|
| Spec que não mente | O `TRUTH.md` só muda no arquivamento, e só com o que a delta declarou |
| Contexto barato para a IA | A IA lê o `TRUTH.md` — curto por regra ([RNF1](specs/TRUTH.md)) — em vez de um PRD inteiro |
| Rastreabilidade | Todo requisito tem ID fixo (`R7`, `RNF2`) e mostra de qual delta veio: `R7 (delta-006)` |
| Requisito não some sem querer | Um script compara o `TRUTH.md` antes e depois: sumiu sem `REMOVE` declarado, o PR trava |

---

## 2. Instalação

### 2.1 O plugin — 2 comandos dentro do Claude Code

```
/plugin marketplace add iuripereira/deltaspec
/plugin install deltaspec@deltaspec
```

Pronto: as 10 skills aparecem com o prefixo `deltaspec:`. Para atualizar depois, `/plugin update deltaspec@deltaspec` — sem o `@deltaspec` do marketplace, o plugin não é encontrado.

### 2.2 Os motores — 1 comando no terminal

O deltaspec **coordena**; plugins de terceiros **fazem** o trabalho pesado de cada fase. Um comando instala todos:

```bash
curl -fsSL https://raw.githubusercontent.com/iuripereira/deltaspec/main/scripts/instala-motores.sh | bash
```

(Com o repositório clonado, chame [scripts/instala-motores.sh](scripts/instala-motores.sh) direto.)

### 2.3 Os gates — 1 dependência

```bash
pip install pyyaml
```

Única dependência externa do framework, para validar o `doc-profile.yaml` ([ADR-0023](docs/adrs/ADR-0023-pyyaml-como-dependencia-admitida.md)). Sem ela os gates param com a mensagem pedindo este comando; o resto é biblioteca padrão do Python 3.11+.

```mermaid
%%{init: {'theme':'base','themeVariables':{'lineColor':'#5b6472','primaryTextColor':'#1f2937','primaryBorderColor':'#2b2b2b','edgeLabelBackground':'#ffffff'}}}%%
flowchart LR
    c("deltaspec<br><b>coordena</b><br>ciclo · contratos · checagens")
    sp("superpowers<br>plan · implement · review")
    po("ponytail<br>evita código demais")
    mx("max<br>entrevista a spec")
    gf("graphify<br><i>opcional</i>")
    fb("plugin faltando?<br>a fase roda no modo simples<br>+ aviso de que degradou")

    c --> sp
    c --> po
    c --> mx
    c --> gf
    sp -.-> fb
    fb -.-> c

    classDef core fill:#f9c3d4,stroke:#2b2b2b,stroke-width:1.5px,color:#1f2937
    classDef motor fill:#cfeadd,stroke:#2b2b2b,stroke-width:1.5px,color:#1f2937
    classDef aviso fill:#f4eccd,stroke:#2b2b2b,stroke-width:1.5px,color:#1f2937
    class c core
    class sp,po,mx,gf motor
    class fb aviso
```

Cada um cobre uma frente: [`superpowers`](https://github.com/anthropics/claude-plugins) executa plan, implement e review; `ponytail` segura o excesso de engenharia; `max` entrevista a spec (`grill-me`) e escreve o PRD da descoberta (`write-prd`); o `graphify`, opcional, dá um grafo do código como fonte citável (`arquivo:linha`).

> **Regra de ouro:** plugin faltando **nunca quebra o ciclo**. A fase cai no caminho simples descrito em [`adapters.md`](skills/spec-feature/references/adapters.md) e você recebe um aviso dizendo qual fase perdeu potência.

### 2.4 Mermaid — o único CLI obrigatório

```bash
npm install -g @mermaid-js/mermaid-cli
```

Outros renderizadores (DBML, PlantUML, D2, Structurizr) e o exportador de PDF/DOCX só entram se o `doc-profile.yaml` do projeto pedir — a skill [`doc-entregavel`](skills/doc-entregavel/SKILL.md) lista os comandos na hora certa.

---

## 3. Comece um projeto

```mermaid
%%{init: {'theme':'base','themeVariables':{'lineColor':'#5b6472','primaryTextColor':'#1f2937','primaryBorderColor':'#2b2b2b','edgeLabelBackground':'#ffffff'}}}%%
flowchart LR
    a("1<br>projeto-init") --> b("2<br>gh repo create<br>+ projeto-infra")
    b --> c("3<br>spec-feature<br><b>delta-001</b>")
    c --> d("4<br>spec-feature<br>a cada incremento")
    d --> d

    classDef passo fill:#cfe9f3,stroke:#2b2b2b,stroke-width:1.5px,color:#1f2937
    classDef primeira fill:#cfeadd,stroke:#2b2b2b,stroke-width:1.5px,color:#1f2937
    class a,b,d passo
    class c primeira
```

**1. Prepare a pasta.**

```
/deltaspec:projeto-init
```

Ele descobre o tipo do projeto, escreve o `CLAUDE.md` a partir das regras canônicas, cria os arquivos-base e confere se os motores estão instalados. **Não sobrescreve nada:** se já existe um `CLAUDE.md`, você recebe um `CLAUDE.generated.md` ao lado, com o diff, e decide o que juntar.

**2. Proteja o repositório** (depois de criar o remote no GitHub):

```
/deltaspec:projeto-infra
```

Branch protection, CI, checagem de Conventional Commits, release-please, review assistido. Rodar de novo não estraga nada — a segunda vez só relata o que já estava lá.

Ative também o gate pré-commit, uma vez por clone:

```bash
git config core.hooksPath .githooks
```

**3. Escreva a primeira feature.**

```
/deltaspec:spec-feature
```

A **delta-001 é sempre o walking skeleton**: a menor fatia que funciona de ponta a ponta. Nunca "o sistema inteiro" — a visão grande vira a seção "Não implementado" do `TRUTH.md`.

**4. Repita a cada incremento.** O `TRUTH.md` cresce sozinho, um arquivamento por vez.

> **Projeto que já existe?** Nada é sobrescrito nem migrado sem você pedir. Os arquivos que faltam são criados, o `.gitignore` só recebe linhas novas, o `TRUTH.md` nasce vazio e cresce com as **novas** deltas, e a numeração continua do maior número já usado.

---

## 4. O ciclo de uma feature

Uma feature = uma pasta `specs/NNN-nome/` com `spec.md`, `plan.md` e `tasks.md`. Ela passa por três estados:

```mermaid
%%{init: {'theme':'base','themeVariables':{'lineColor':'#5b6472','primaryTextColor':'#1f2937','primaryBorderColor':'#2b2b2b','edgeLabelBackground':'#ffffff'}}}%%
stateDiagram-v2
    direction LR
    [*] --> proposta : specify
    proposta --> aplicada : implement
    aplicada --> arquivada : archive
    arquivada --> [*]

    classDef prop fill:#cfe9f3,stroke:#2b2b2b,stroke-width:1.5px,color:#1f2937
    classDef apl fill:#f4eccd,stroke:#2b2b2b,stroke-width:1.5px,color:#1f2937
    classDef arq fill:#cfeadd,stroke:#2b2b2b,stroke-width:1.5px,color:#1f2937
    class proposta prop
    class aplicada apl
    class arquivada arq
```

- **proposta** — a spec existe, o código não.
- **aplicada** — o código existe, mas o requisito ainda não entrou no `TRUTH.md`.
- **arquivada** — a pasta vai para `specs/_archive/NNN-nome/` **e** o `TRUTH.md` é atualizado.

> **Arquivar faz parte do "pronto".** Feature sem arquivamento é feature não terminada. A tag de versão sai no merge que fecha a delta.

O número `NNN` **nunca reinicia**: ele é citado em ADRs, commits e no próprio `TRUTH.md`.

### As fases

```mermaid
%%{init: {'theme':'base','themeVariables':{'lineColor':'#5b6472','primaryTextColor':'#1f2937','primaryBorderColor':'#2b2b2b','edgeLabelBackground':'#ffffff'}}}%%
flowchart TD
    desc("descoberta<br><i>opcional, antes de tudo</i>") -.-> spec
    spec("specify<br>abre a delta") --> cla("clarify<br>entrevista que fura a spec")
    cla --> plan("plan<br>como construir")
    plan --> tk("tasks<br>ordem e paralelismo")
    tk --> tp("test-plan<br>um caso por requisito")
    tp --> an{"analyze"}
    an -->|travado| spec
    an -->|liberado| imp("implement<br>TDD + ponytail")
    imp --> rev("review<br>spec × qualidade")
    rev --> arc("archive<br>atualiza o TRUTH.md")
    arc --> pr("PR + tag")

    classDef inicio fill:#cfe9f3,stroke:#2b2b2b,stroke-width:1.5px,color:#1f2937
    classDef fase fill:#ffffff,stroke:#2b2b2b,stroke-width:1.5px,color:#1f2937
    classDef porta fill:#f0b040,stroke:#2b2b2b,stroke-width:1.5px,color:#1f2937
    classDef fim fill:#cfeadd,stroke:#2b2b2b,stroke-width:1.5px,color:#1f2937
    class desc,spec inicio
    class cla,plan,tk,tp,imp,rev fase
    class an porta
    class arc,pr fim
```

| Fase | A pergunta que ela responde | O que sai |
|---|---|---|
| **descoberta** | "O que existe hoje, de verdade?" | dossiê do processo atual, com o nível de certeza de cada afirmação |
| **specify** | "O que muda no que já vale?" | `spec.md` com blocos ADICIONA/MUDA/REMOVE |
| **clarify** | "Onde essa spec é frágil?" | spec revisada depois da entrevista |
| **plan** | "Como construir?" | `plan.md` |
| **tasks** | "Em que ordem? O que dá para fazer em paralelo?" | `tasks.md` com dependências `(dep: T1, T2)` |
| **test-plan** | "Como eu provo que cada requisito funciona?" | `test-plan.md` com `cobre: Rn` |
| **analyze** | "Os documentos combinam entre si?" | `analyze.md` com veredito LIBERADO ou BLOQUEADO |
| **implement** | — | código + testes |
| **review** | "O código faz o que a spec prometeu? Sobrou gordura?" | achados dos dois eixos |
| **archive** | "O que passa a valer?" | `TRUTH.md` atualizado + delta movida |

### Nem toda feature precisa do ciclo inteiro

No specify a IA **sugere** um perfil, com uma linha de justificativa. Ele **só vale se você aprovar**, e a aprovação fica registrada no cabeçalho da spec.

| Etapa | `completo` | `enxuto` |
|---|---|---|
| clarify | sempre | só se aparecer ambiguidade |
| test-plan | obrigatório | dispensável, com motivo escrito |
| review | dois eixos em paralelo | os dois eixos juntos, numa passada |
| plan · tasks · analyze · archive | inteiros | inteiros |

Correção de bug tem caminho próprio (`Tipo: bugfix`): template com sintoma, reprodução, causa-raiz e teste de regressão, e um pipeline curto — specify → plan → implement → review. Se o bug não muda requisito, arquiva **sem** mexer no `TRUTH.md`.

---

## 5. O dia a dia

```mermaid
%%{init: {'theme':'base','themeVariables':{'lineColor':'#5b6472','primaryTextColor':'#1f2937','primaryBorderColor':'#2b2b2b','edgeLabelBackground':'#ffffff'}}}%%
flowchart LR
    s1("abrir:<br>ler o HANDOFF.md") --> s2("spec-feature<br>abre ou retoma a delta")
    s2 --> s3{"delta<br>arriscada?"}
    s3 -->|sim| s4("spec-review")
    s3 -->|não| s5
    s4 --> s5("implement → review<br>→ archive → PR")
    s5 --> s6("fechar:<br>handoff")

    classDef borda fill:#cfe9f3,stroke:#2b2b2b,stroke-width:1.5px,color:#1f2937
    classDef meio fill:#ffffff,stroke:#2b2b2b,stroke-width:1.5px,color:#1f2937
    classDef porta fill:#f0b040,stroke:#2b2b2b,stroke-width:1.5px,color:#1f2937
    class s1,s6 borda
    class s2,s4,s5 meio
    class s3 porta
```

Duas regras de higiene sustentam o resto:

- **1 sessão = 1 branch = 1 escopo.** Apareceu trabalho de outro assunto? Vira outra branch — ou uma linha `DT-NNN` no `DEBT.md`.
- **Feche com `/deltaspec:handoff`.** O que você descobriu vai para os arquivos do projeto, não para a memória da conversa.

---

## 6. As skills

Oito comandos do ciclo, na ordem em que você os encontra. Clique no nome para ler o detalhe da skill.

| Skill | Para que serve | Quando usar |
|---|---|---|
| [`projeto-init`](skills/projeto-init/SKILL.md) | Transforma uma pasta qualquer num projeto que segue as convenções: `CLAUDE.md`, arquivos-base, `specs/` | Uma vez por repositório |
| [`projeto-infra`](skills/projeto-infra/SKILL.md) | Deixa a `main` protegida e o PR com checks verdes | Depois de criar o repo no GitHub. Precisa do `gh` autenticado |
| [`descoberta`](skills/descoberta/SKILL.md) | Vira material bruto (reunião, planilha, processo na cabeça de alguém) em dossiê onde toda afirmação diz sua fonte e seu nível de certeza | Não existe PRD validado, ou há material bruto para digerir |
| [`spec-feature`](skills/spec-feature/SKILL.md) | Conduz um incremento do specify ao PR, sem pular etapa. É o comando que você mais usa | A cada feature |
| [`spec-review`](skills/spec-review/SKILL.md) | Tenta furar a spec **antes** de virar código: premissas frágeis, erro não previsto, contrato externo | Opcional; recomendado quando a spec toca segurança, dados persistentes ou dependência nova |
| [`guarding-doc-integrity`](skills/guarding-doc-integrity/SKILL.md) | Impede que um valor repetido em 5 arquivos fique desencontrado: um assunto tem um arquivo dono, o resto linka | Um valor mudou num repositório com documentos canônicos |
| [`handoff`](skills/handoff/SKILL.md) | Fecha a sessão nos arquivos certos: `HANDOFF.md`, `DEBT.md` e o estado da delta em curso | Ao encerrar o dia |
| [`doc-entregavel`](skills/doc-entregavel/SKILL.md) | Congela um PDF/DOCX assinável para o cliente, com capa de assinatura e diagramas renderizados | Projeto com `publico.cliente: true` |
| [`status-pmo`](skills/status-pmo/SKILL.md) | Monta o site de status PMO (dashboard %/fase/farol, gantt com marcos, one-page por projeto) sempre da mesma forma | Portfólio/projeto que reporta status à gestão |

A décima não é comando: [`eu-tenho-tdah`](skills/eu-tenho-tdah/SKILL.md) é o perfil de escrita do Iuri (baseado em [ayghri/i-have-adhd](https://github.com/ayghri/i-have-adhd)), ligado o tempo todo — ação antes de contexto, listas ranqueadas, tangente vira pendência salva.

**spec-review ou analyze?** O analyze confere se os documentos **combinam entre si** (mecânico). O spec-review discute o **mérito** da spec.

---

## 7. As checagens automáticas

A ideia: **integridade não pode depender de quem está cansado.** Um humano esquece, uma IA otimista também. O script não.

Tudo roda **na sua máquina** — na fase analyze, no arquivamento e no pré-commit ([ADR-0001](docs/adrs/ADR-0001-gates-rodam-local.md)). Uma única dependência externa: `pip install pyyaml`, para validar o `doc-profile.yaml` ([ADR-0023](docs/adrs/ADR-0023-pyyaml-como-dependencia-admitida.md)); o resto é biblioteca padrão do Python 3.11+.

```bash
# o ciclo da delta: aceite, cobertura, estado, arquivamento sem perda,
# tamanho do TRUTH, dependências das tasks (checagens C1–C12)
python3 skills/spec-feature/scripts/check_cycle.py specs/NNN-nome

# os valores espelhados entre documentos e os links relativos
python3 skills/guarding-doc-integrity/scripts/validate_integrity.py .
```

Achado ALTO ou CRÍTICO derruba o comando — e o implement não começa. A checagem mais importante é o **arquivamento sem perda**: requisito que sumiu do `TRUTH.md` sem um `REMOVE` declarado é CRÍTICO.

O `check_cycle.py` **avisa que é parcial**: ele diz quais checagens fez e lembra que "fugiu do escopo" e "violou regra canônica" continuam sendo julgamento humano. Automatizar isso daria falso "tudo certo" — a lista completa está na [skill](skills/spec-feature/SKILL.md).

Cada script carrega o próprio teste:

```bash
python3 skills/spec-feature/scripts/check_cycle.py --selftest
python3 skills/guarding-doc-integrity/scripts/validate_integrity.py --selftest
```

---

## 8. Onde cada coisa mora

O princípio que não se negocia: **cada informação tem um dono.** Referencie, não copie.

| Arquivo | Dono de | Regra |
|---|---|---|
| [`specs/TRUTH.md`](specs/TRUTH.md) | o que **vale** hoje | Só muda no arquivamento |
| `specs/_archive/` | histórico das deltas | Não se mexe |
| [`CHANGELOG.md`](CHANGELOG.md) | histórico permanente | Keep a Changelog, em PT-BR |
| [`HANDOFF.md`](HANDOFF.md) | o **agora** | Janela rolante: entrada velha sai |
| [`DEBT.md`](DEBT.md) | débito, pendência e lição | `DT-NNN` fixo; item resolvido **muda de status, nunca some** |
| [`docs/adrs/`](docs/adrs/) | decisões e o que foi descartado | Imutável depois de `Accepted`; mudou? nova ADR |
| [`CLAUDE.md`](CLAUDE.md) | as convenções do repositório | A IA lê a cada sessão |
| `deps.toml` | mapa dono → cópias autorizadas | Validado por script |

Na prática: **débito não vira comentário no HANDOFF, e decisão não vira parágrafo na spec.**

---

## Para saber mais

- [`CLAUDE.md`](CLAUDE.md) — as convenções deste repositório (release, git, clean code, testes, segurança).
- [`docs/adrs/`](docs/adrs/) — por que cada decisão foi tomada, e o que foi descartado no caminho.
- [`skills/spec-feature/references/cycle.md`](skills/spec-feature/references/cycle.md) — o ciclo em detalhe: entrada e saída de cada fase.
- [`CHANGELOG.md`](CHANGELOG.md) — o que mudou em cada versão.

> **O framework é aplicado a si mesmo.** Toda mudança em `skills/` passa pelo próprio ciclo — inclusive quando a mudança é no que o ciclo diz sobre si mesmo.
