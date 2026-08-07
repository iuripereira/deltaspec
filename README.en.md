<!-- Espelho sancionado do README.md (DT-015): tradução integral — mudou lá, sincronize aqui no mesmo change. -->
# deltaspec

**Spec-Driven Development via delta specs**, for [Claude Code](https://claude.com/claude-code).

**[Leia em português](README.md)** · Project language is PT-BR — this English README and the summary in [CONTRIBUTING.md](CONTRIBUTING.md) are the sanctioned exceptions.

Instead of maintaining a giant requirements document that ages badly, each feature writes **only what changes**. A single file — `specs/TRUTH.md` — holds what is true today.

> **It's git, applied to requirements.** Each feature is a spec *commit* (ADICIONA / MUDA / REMOVE — adds / changes / removes). `TRUTH.md` is the *working tree*: the current state, with every commit already applied. Old specs go to `specs/_archive/` — they are history, not truth.

[Current version: tags](https://github.com/iuripereira/deltaspec/tags) · 10 skills · MIT License

---

## Table of contents

1. [The problem](#1-the-problem)
2. [Installation](#2-installation)
3. [Start a project](#3-start-a-project)
4. [The lifecycle of a feature](#4-the-lifecycle-of-a-feature)
5. [Day to day](#5-day-to-day)
6. [The skills](#6-the-skills)
7. [The automated checks](#7-the-automated-checks)
8. [Where everything lives](#8-where-everything-lives)

---

## 1. The problem

You write a 40-page PRD, ship 3 features — and the PRD is already lying. Nobody rewrites the whole document on every change, so it becomes fiction.

deltaspec's way out: **the big document is never written by hand.** It is assembled from the deltas.

```mermaid
%%{init: {'theme':'base','themeVariables':{'lineColor':'#5b6472','primaryTextColor':'#1f2937','primaryBorderColor':'#2b2b2b','edgeLabelBackground':'#ffffff'}}}%%
flowchart LR
    d1("delta-001<br>ADDS R1, R2") --> T
    d2("delta-002<br>CHANGES R2<br>ADDS R3") --> T
    d3("delta-003<br>REMOVES R1") --> T
    T("specs/TRUTH.md<br><b>what is true today</b>")
    T --> arq("specs/_archive/<br>delta history")

    classDef delta fill:#cfe9f3,stroke:#2b2b2b,stroke-width:1.5px,color:#1f2937
    classDef verdade fill:#f9c3d4,stroke:#2b2b2b,stroke-width:1.5px,color:#1f2937
    classDef hist fill:#f4eccd,stroke:#2b2b2b,stroke-width:1.5px,color:#1f2937
    class d1,d2,d3 delta
    class T verdade
    class arq hist
```

What this gives you:

| You get | How |
|---|---|
| A spec that doesn't lie | `TRUTH.md` only changes at archive time, and only with what the delta declared |
| Cheap context for the AI | The AI reads `TRUTH.md` — short by rule ([RNF1](specs/TRUTH.md)) — instead of a whole PRD |
| Traceability | Every requirement has a fixed ID (`R7`, `RNF2`) and shows which delta it came from: `R7 (delta-006)` |
| Requirements can't vanish by accident | A script compares `TRUTH.md` before and after: if something disappeared without a declared `REMOVE`, the PR is blocked |

---

## 2. Installation

### 2.1 The plugin — 2 commands inside Claude Code

```
/plugin marketplace add iuripereira/deltaspec
/plugin install deltaspec@deltaspec
```

Done: the 10 skills show up under the `deltaspec:` prefix. To update later, `/plugin update deltaspec@deltaspec` — without the marketplace's `@deltaspec`, the plugin is not found.

### 2.2 The engines — 1 command in the terminal

deltaspec **coordinates**; third-party plugins **do** the heavy lifting of each phase. One command installs them all:

```bash
curl -fsSL https://raw.githubusercontent.com/iuripereira/deltaspec/main/scripts/instala-motores.sh | bash
```

(With the repository cloned, call [scripts/instala-motores.sh](scripts/instala-motores.sh) directly.)

### 2.3 The gates — 1 dependency

```bash
pip install pyyaml
```

The framework's single external dependency, used to validate `doc-profile.yaml` ([ADR-0023](docs/adrs/ADR-0023-pyyaml-como-dependencia-admitida.md)). Without it the gates stop with a message asking for this command; everything else is the Python 3.11+ standard library.

```mermaid
%%{init: {'theme':'base','themeVariables':{'lineColor':'#5b6472','primaryTextColor':'#1f2937','primaryBorderColor':'#2b2b2b','edgeLabelBackground':'#ffffff'}}}%%
flowchart LR
    c("deltaspec<br><b>coordinates</b><br>cycle · contracts · checks")
    sp("superpowers<br>plan · implement · review")
    po("ponytail<br>keeps code lean")
    mx("max<br>interviews the spec")
    dd("diagram-design<br>presentation layer")
    gf("graphify<br><i>optional</i>")
    fb("plugin missing?<br>the phase runs in simple mode<br>+ a degradation warning")

    c --> sp
    c --> po
    c --> mx
    c --> dd
    c --> gf
    sp -.-> fb
    fb -.-> c

    classDef core fill:#f9c3d4,stroke:#2b2b2b,stroke-width:1.5px,color:#1f2937
    classDef motor fill:#cfeadd,stroke:#2b2b2b,stroke-width:1.5px,color:#1f2937
    classDef aviso fill:#f4eccd,stroke:#2b2b2b,stroke-width:1.5px,color:#1f2937
    class c core
    class sp,po,mx,dd,gf motor
    class fb aviso
```

Each one covers a front: [`superpowers`](https://github.com/anthropics/claude-plugins) runs plan, implement and review; `ponytail` holds back over-engineering; `max` interviews the spec (`grill-me`) and writes the discovery PRD (`write-prd`); [`diagram-design`](https://github.com/cathrynlavery/diagram-design) materializes the presentation layer for client/management docs ([ADR-0018](docs/adrs/ADR-0018-diagram-design-camada-apresentacao.md)); `graphify`, optional, provides a code graph as a citable source (`file:line`).

> **Golden rule:** a missing plugin **never breaks the cycle**. The phase falls back to the simple path described in [`adapters.md`](skills/spec-feature/references/adapters.md) and you get a warning telling you which phase lost power.

### 2.4 Mermaid — the only required CLI

```bash
npm install -g @mermaid-js/mermaid-cli
```

Other renderers (DBML, PlantUML, D2, Structurizr) and the PDF/DOCX exporter only come in if the project's `doc-profile.yaml` asks for them — the [`doc-entregavel`](skills/doc-entregavel/SKILL.md) skill lists the commands at the right time.

---

## 3. Start a project

```mermaid
%%{init: {'theme':'base','themeVariables':{'lineColor':'#5b6472','primaryTextColor':'#1f2937','primaryBorderColor':'#2b2b2b','edgeLabelBackground':'#ffffff'}}}%%
flowchart LR
    a("1<br>projeto-init") --> b("2<br>gh repo create<br>+ projeto-infra")
    b --> c("3<br>spec-feature<br><b>delta-001</b>")
    c --> d("4<br>spec-feature<br>on every increment")
    d --> d

    classDef passo fill:#cfe9f3,stroke:#2b2b2b,stroke-width:1.5px,color:#1f2937
    classDef primeira fill:#cfeadd,stroke:#2b2b2b,stroke-width:1.5px,color:#1f2937
    class a,b,d passo
    class c primeira
```

**1. Prepare the folder.**

```
/deltaspec:projeto-init
```

It figures out the project type, writes the `CLAUDE.md` from the canonical rules, creates the base files and checks that the engines are installed. **It never overwrites anything:** if a `CLAUDE.md` already exists, you get a `CLAUDE.generated.md` next to it, with the diff, and you decide what to merge.

**2. Protect the repository** (after creating the remote on GitHub):

```
/deltaspec:projeto-infra
```

Branch protection, CI, Conventional Commits check, release-please, assisted review. Running it again breaks nothing — the second run just reports what was already there.

Also enable the pre-commit gate, once per clone:

```bash
git config core.hooksPath .githooks
```

**3. Write the first feature.**

```
/deltaspec:spec-feature
```

**delta-001 is always the walking skeleton**: the smallest slice that works end to end. Never "the whole system" — the big vision becomes the "Não implementado" (not implemented) section of `TRUTH.md`.

**4. Repeat on every increment.** `TRUTH.md` grows on its own, one archive at a time.

> **Existing project?** Nothing is overwritten or migrated without you asking. Missing files are created, `.gitignore` only receives new lines, `TRUTH.md` is born empty and grows with the **new** deltas, and numbering continues from the highest number already used.

---

## 4. The lifecycle of a feature

One feature = one `specs/NNN-nome/` folder with `spec.md`, `plan.md` and `tasks.md`. It goes through three states:

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

- **proposta** (proposed) — the spec exists, the code doesn't.
- **aplicada** (applied) — the code exists, but the requirement hasn't reached `TRUTH.md` yet.
- **arquivada** (archived) — the folder moves to `specs/_archive/NNN-nome/` **and** `TRUTH.md` is updated.

> **Archiving is part of "done".** A feature without its archive is an unfinished feature. The version tag is cut on the merge that closes the delta.

The `NNN` number **never resets**: it is cited in ADRs, commits and in `TRUTH.md` itself.

### The phases

```mermaid
%%{init: {'theme':'base','themeVariables':{'lineColor':'#5b6472','primaryTextColor':'#1f2937','primaryBorderColor':'#2b2b2b','edgeLabelBackground':'#ffffff'}}}%%
flowchart TD
    desc("descoberta<br><i>optional, before everything</i>") -.-> spec
    spec("specify<br>opens the delta") --> cla("clarify<br>the interview that pokes holes")
    cla --> plan("plan<br>how to build")
    plan --> tk("tasks<br>order and parallelism")
    tk --> tp("test-plan<br>one case per requirement")
    tp --> an{"analyze"}
    an -->|blocked| spec
    an -->|cleared| imp("implement<br>TDD + ponytail")
    imp --> rev("review<br>spec × quality")
    rev --> arc("archive<br>updates TRUTH.md")
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

| Phase | The question it answers | What comes out |
|---|---|---|
| **descoberta** (discovery) | "What exists today, really?" | dossier of the current process, with a confidence level on every claim |
| **specify** | "What changes in what is already true?" | `spec.md` with ADICIONA/MUDA/REMOVE blocks |
| **clarify** | "Where is this spec fragile?" | spec revised after the interview |
| **plan** | "How do we build it?" | `plan.md` |
| **tasks** | "In what order? What can run in parallel?" | `tasks.md` with `(dep: T1, T2)` dependencies — and, when `doc-profile.yaml` enables `motores.jira`, the `tickets.md` projected to Jira (epic + tickets + blocking links) |
| **test-plan** | "How do I prove each requirement works?" | `test-plan.md` with `cobre: Rn` (covers) |
| **analyze** | "Do the documents agree with each other?" | `analyze.md` with a LIBERADO (cleared) or BLOQUEADO (blocked) verdict |
| **implement** | — | code + tests |
| **review** | "Does the code do what the spec promised? Any fat left?" | findings from both axes |
| **archive** | "What becomes true?" | updated `TRUTH.md` + delta moved |

### Not every feature needs the full cycle

At specify time the AI **suggests** a profile, with a one-line justification. It **only takes effect if you approve it**, and the approval is recorded in the spec header.

| Stage | `completo` (full) | `enxuto` (lean) |
|---|---|---|
| clarify | always | only if ambiguity shows up |
| test-plan | required | waivable, with a written reason |
| review | two axes in parallel | both axes together, in one pass |
| plan · tasks · analyze · archive | in full | in full |

Bug fixes have their own path (`Tipo: bugfix`): a template with symptom, reproduction, root cause and regression test, and a short pipeline — specify → plan → implement → review. If the bug doesn't change a requirement, it archives **without** touching `TRUTH.md`.

---

## 5. Day to day

```mermaid
%%{init: {'theme':'base','themeVariables':{'lineColor':'#5b6472','primaryTextColor':'#1f2937','primaryBorderColor':'#2b2b2b','edgeLabelBackground':'#ffffff'}}}%%
flowchart LR
    s1("open:<br>read HANDOFF.md") --> s2("spec-feature<br>opens or resumes the delta")
    s2 --> s3{"risky<br>delta?"}
    s3 -->|yes| s4("spec-review")
    s3 -->|no| s5
    s4 --> s5("implement → review<br>→ archive → PR")
    s5 --> s6("close:<br>handoff")

    classDef borda fill:#cfe9f3,stroke:#2b2b2b,stroke-width:1.5px,color:#1f2937
    classDef meio fill:#ffffff,stroke:#2b2b2b,stroke-width:1.5px,color:#1f2937
    classDef porta fill:#f0b040,stroke:#2b2b2b,stroke-width:1.5px,color:#1f2937
    class s1,s6 borda
    class s2,s4,s5 meio
    class s3 porta
```

Two hygiene rules hold up the rest:

- **1 session = 1 branch = 1 scope.** Work from another topic showed up? It becomes another branch — or a `DT-NNN` line in `DEBT.md`.
- **Close with `/deltaspec:handoff`.** What you learned goes into the project files, not into the conversation's memory.

---

## 6. The skills

Eight cycle commands, in the order you meet them. Click a name to read the skill's details.

| Skill | What it's for | When to use it |
|---|---|---|
| [`projeto-init`](skills/projeto-init/SKILL.md) | Turns any folder into a project that follows the conventions: `CLAUDE.md`, base files, `specs/` | Once per repository |
| [`projeto-infra`](skills/projeto-infra/SKILL.md) | Protects `main` and gets PRs to green checks | After creating the repo on GitHub. Needs authenticated `gh` |
| [`descoberta`](skills/descoberta/SKILL.md) | Turns raw material (meetings, spreadsheets, a process in someone's head) into a dossier where every claim states its source and confidence level | No validated PRD, or raw material to digest |
| [`spec-feature`](skills/spec-feature/SKILL.md) | Drives an increment from specify to PR, skipping nothing. The command you use the most | On every feature |
| [`spec-review`](skills/spec-review/SKILL.md) | Tries to poke holes in the spec **before** it becomes code: fragile assumptions, unhandled errors, external contracts | Optional; recommended when the spec touches security, persistent data or a new dependency |
| [`guarding-doc-integrity`](skills/guarding-doc-integrity/SKILL.md) | Keeps a value repeated across 5 files from drifting apart: one topic has one owner file, the rest link to it | A value changed in a repository with canonical documents |
| [`handoff`](skills/handoff/SKILL.md) | Closes the session into the right files: `HANDOFF.md`, `DEBT.md` and the state of the current delta | At the end of the day |
| [`doc-entregavel`](skills/doc-entregavel/SKILL.md) | Freezes a signable PDF/DOCX for the client, with a signature cover page and rendered diagrams | Projects with `publico.cliente: true` |
| [`status-pmo`](skills/status-pmo/SKILL.md) | Builds the PMO status site (dashboard with %/phase/traffic light, gantt with milestones, per-project one-page) the same way every time | Portfolio/project reporting status to management |

The tenth is not a command: [`eu-tenho-tdah`](skills/eu-tenho-tdah/SKILL.md) is Iuri's writing profile (based on [ayghri/i-have-adhd](https://github.com/ayghri/i-have-adhd)), always on — action before context, ranked lists, tangents become saved pending items.

**spec-review or analyze?** analyze checks whether the documents **agree with each other** (mechanical). spec-review debates the **merit** of the spec.

---

## 7. The automated checks

The idea: **integrity can't depend on whoever is tired.** A human forgets, an optimistic AI does too. The script doesn't.

Everything runs **on your machine** — at the analyze phase, at archive time and on pre-commit ([ADR-0001](docs/adrs/ADR-0001-gates-rodam-local.md)). A single external dependency: `pip install pyyaml`, to validate `doc-profile.yaml` ([ADR-0023](docs/adrs/ADR-0023-pyyaml-como-dependencia-admitida.md)); everything else is the Python 3.11+ standard library.

```bash
# the delta's cycle: acceptance, coverage, state, lossless archiving,
# TRUTH size, task dependencies (checks C1–C12)
python3 skills/spec-feature/scripts/check_cycle.py specs/NNN-nome

# mirrored values across documents and relative links
python3 skills/guarding-doc-integrity/scripts/validate_integrity.py .
```

A HIGH or CRITICAL finding fails the command — and implement doesn't start. The most important check is **lossless archiving**: a requirement that vanished from `TRUTH.md` without a declared `REMOVE` is CRITICAL.

`check_cycle.py` **tells you it is partial**: it names the checks it ran and reminds you that "scope creep" and "canonical rule violated" remain human judgment. Automating those would produce a confident false "all clear" — the full list is in the [skill](skills/spec-feature/SKILL.md).

Every script carries its own test:

```bash
python3 skills/spec-feature/scripts/check_cycle.py --selftest
python3 skills/guarding-doc-integrity/scripts/validate_integrity.py --selftest
```

---

## 8. Where everything lives

The non-negotiable principle: **every piece of information has one owner.** Reference, don't copy.

| File | Owner of | Rule |
|---|---|---|
| [`specs/TRUTH.md`](specs/TRUTH.md) | what is **true** today | Only changes at archive time |
| `specs/_archive/` | delta history | Never touched |
| [`CHANGELOG.md`](CHANGELOG.md) | permanent history | Keep a Changelog, in PT-BR |
| [`HANDOFF.md`](HANDOFF.md) | the **now** | Rolling window: old entries leave |
| [`DEBT.md`](DEBT.md) | debt, pending items and lessons | Stable `DT-NNN` IDs; resolved items **change status, never disappear** |
| [`docs/adrs/`](docs/adrs/) | decisions and what was discarded | Immutable after `Accepted`; changed your mind? new ADR |
| [`CLAUDE.md`](CLAUDE.md) | the repository's conventions | The AI reads it every session |
| `deps.toml` | owner → authorized copies map | Validated by script |

In practice: **debt doesn't become a HANDOFF comment, and decisions don't become a paragraph in the spec.**

---

## Learn more

- [`CONTRIBUTING.md`](CONTRIBUTING.md) — how to contribute (with an English summary).
- [`CLAUDE.md`](CLAUDE.md) — this repository's conventions (release, git, clean code, tests, security) — in PT-BR.
- [`docs/adrs/`](docs/adrs/) — why each decision was made, and what was discarded along the way.
- [`skills/spec-feature/references/cycle.md`](skills/spec-feature/references/cycle.md) — the cycle in detail: each phase's input and output.
- [`CHANGELOG.md`](CHANGELOG.md) — what changed in each version.

> **The framework is applied to itself.** Every change under `skills/` goes through its own cycle — including when the change is in what the cycle says about itself.
