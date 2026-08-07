<!-- resumo deltaspec · ≤15 linhas · única parte do plano lida pelo analyze e pelo humano -->
**Objetivo:** projetar tasks de delta para o Jira (épico + filhas + links de bloqueio) e corrigir o dialeto do DEBT.md com os achados do DT-021. **Cobre:** R1, R2 (MUDA R52), R3 (da delta-017) **Decisões duráveis → ADRs:** ADR-0024 (pin do max mantido — gravado no clarify) **Riscos assumidos:** módulo comum importado entre skills do mesmo plugin (caminho relativo estável no cache); degrau Rovo MCP da escada nasce não exercitado (sem auth no harness); validação real limitada ao sandbox SBX.

---

# delta-017 — Plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `tickets.md` por delta como projeção canônica das tasks (épico por delta, filhas com links de bloqueio) com ida mecânica ao Jira via `.sh` de `acli` unitários, volta como diff aprovado, e o dialeto do `debito.py` corrigido (bulk quebrado sai, unitário entra).

**Architecture:** a emissão de dialeto (corpo, etiquetas, `.sh` de creates unitários) sai do `debito.py` para o módulo comum `projecao.py` (skills/handoff/scripts/), importado pelos dois consumidores. `tickets.py` novo (skills/spec-feature/scripts/) parseia o `tasks.md` por âncoras de início de linha (regra do R51), gera `tickets.md` + `.sh`, e faz o diff da volta contra o JSON do `acli search`. Scripts nunca acessam a rede — quem executa os `.sh` é a skill (R52).

**Tech Stack:** Python 3.11+ stdlib (re, pathlib, json, subprocess p/ git) + PyYAML só para ler `doc-profile.yaml` (ADR-0023). CLI externo: `acli` v1.3.22 (executado pela skill, nunca pelo script).

## Global Constraints

- Identificadores, comentários e mensagens em **PT-BR** (padrão dos scripts vigentes).
- **Zero dependência nova**: stdlib + PyYAML (ADR-0023); dependência nova exigiria ADR própria.
- **Sem rede nos scripts** (R52): scripts emitem arquivos; a skill executa comandos.
- **Zero valor mágico**: limiar/constante nomeada no topo do script.
- Funções puras separadas de I/O; cada script com `--selftest` co-localizado (fixtures inline).
- Parsing por **âncoras de início de linha**, nunca busca de texto (regra do R51).
- Referências de caminho entre skills via layout do plugin (`skills/<nome>/scripts/`), nunca caminho absoluto de máquina (o job `ci` reprova).
- Ao mudar template (`references/templates/`), atualizar consumidores **e** fixtures juntos.

---

### Task 1: módulo comum `projecao.py` (emissão de dialetos)

**Files:**
- Create: `skills/handoff/scripts/projecao.py`
- Test: selftest embutido (`python3 skills/handoff/scripts/projecao.py --selftest`)

**Interfaces:**
- Consumes: nada (folha).
- Produces (usado por T2 e T3):
  - `corpo_ticket(item: dict, entrada: dict) -> str` e `etiquetas(item: dict, entrada: dict) -> list[str]` — **movidos** do `debito.py` (linhas 250–279) sem mudança de assinatura.
  - `emitir_sh_acli(itens: list[dict], projeto: str, saida: Path, epico: str | None = None) -> Path` — itens `{"id","title","body","labels"}`; escreve `corpo-<id>.md` por item + `tickets-acli.sh` com `acli jira workitem create --project <projeto> --type Task --summary ... --label a,b --description-file <corpo> --json`; com `epico`, o `.sh` cria o épico primeiro (`--type Epic --json`), captura a chave com `python3 -c` sobre o stdout JSON e usa `--parent "$EPICO"` nas filhas. Retorna o caminho do `.sh`.
  - Constante `TIPO_ITEM = "Task"` e `TIPO_EPICO = "Epic"` (zero valor mágico).

- [ ] **Step 1: escrever o selftest que falha** — casos: (a) 2 itens sem épico → `.sh` com 2 creates unitários, corpos em arquivos, sem `create-bulk` na saída; (b) com épico → primeiro create é `--type Epic`, filhas com `--parent`; (c) corpo multi-linha com lista/`---` chega **byte-idêntico** ao `corpo-<id>.md`; (d) `shlex.quote` em summary com aspas.

```python
def selftest():
    with tempfile.TemporaryDirectory() as td:
        saida = Path(td)
        itens = [
            {"id": "DT-001", "title": 'a "b"', "body": "l1\n\n- item\n\n---\nfim", "labels": ["dt:DT-001"]},
            {"id": "DT-002", "title": "c", "body": "curto", "labels": ["x", "y"]},
        ]
        sh = emitir_sh_acli(itens, "SBX", saida)
        texto = sh.read_text(encoding="utf-8")
        assert "create-bulk" not in texto, "bulk quebrado não pode voltar (DT-021)"
        assert texto.count("acli jira workitem create ") == 2
        assert (saida / "corpo-DT-001.md").read_text(encoding="utf-8") == itens[0]["body"]
        assert "--label dt:DT-001" in texto and "--label x,y" in texto
        sh2 = emitir_sh_acli(itens, "SBX", saida, epico="[delta-017] jira-tickets")
        t2 = sh2.read_text(encoding="utf-8")
        assert t2.index("--type Epic") < t2.index("--type Task")
        assert '--parent "$EPICO"' in t2
    print("selftest projecao: OK")
```

- [ ] **Step 2: rodar e ver falhar** — `python3 skills/handoff/scripts/projecao.py --selftest` → NameError.
- [ ] **Step 3: implementar** — mover `corpo_ticket`/`etiquetas` do `debito.py` (cópia literal; o T2 remove de lá) e escrever `emitir_sh_acli`:

```python
def emitir_sh_acli(itens, projeto, saida, epico=None):
    """Emite .sh de creates unitários — decisão da delta-017 (DT-021: bulk rejeita \n)."""
    linhas = ["#!/usr/bin/env bash",
              "# Emitido por projecao.py — revise antes de executar (R52: quem executa é a skill).",
              "set -euo pipefail", ""]
    if epico:
        linhas += [f"EPICO=$(acli jira workitem create --project {shlex.quote(projeto)} "
                   f"--type {TIPO_EPICO} --summary {shlex.quote(epico)} --json "
                   "| python3 -c 'import json,sys; print(json.load(sys.stdin)[\"key\"])')",
                   'echo "épico criado: $EPICO"', ""]
    for i in itens:
        corpo = saida / f"corpo-{i['id']}.md"
        corpo.write_text(i["body"], encoding="utf-8")
        rotulos = f" --label {shlex.quote(','.join(i['labels']))}" if i["labels"] else ""
        pai = ' --parent "$EPICO"' if epico else ""
        linhas.append(f"acli jira workitem create --project {shlex.quote(projeto)} "
                      f"--type {TIPO_ITEM} --summary {shlex.quote(i['title'])}{rotulos}"
                      f"{pai} --description-file {shlex.quote(str(corpo))} --json")
    destino = saida / "tickets-acli.sh"
    destino.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return destino
```

- [ ] **Step 4: selftest verde** — `python3 skills/handoff/scripts/projecao.py --selftest`.
- [ ] **Step 5: commit** — `feat(017-jira-tickets): módulo comum projecao.py emite dialeto acli unitário`.

### Task 2: `debito.py` passa ao dialeto unitário (MUDA R52)

**Files:**
- Modify: `skills/handoff/scripts/debito.py` (funções `corpo_ticket`/`etiquetas` removidas → import de `projecao`; bloco do `tickets-acli.json` em `exportar()` [linhas ~329-337] substituído por chamada a `emitir_sh_acli`; docstring/uso atualizados)
- Test: `python3 skills/handoff/scripts/debito.py --selftest`

**Interfaces:**
- Consumes: `projecao.corpo_ticket`, `projecao.etiquetas`, `projecao.emitir_sh_acli` (import por caminho do próprio diretório — mesmo `scripts/`).
- Produces: `exportar --projeto CHAVE` agora emite `tickets-acli.sh` + `corpo-DT-NNN.md` (DEBT.md não usa épico: `epico=None`); **`tickets-acli.json` deixa de existir**.

- [ ] **Step 1: ajustar o selftest primeiro** — onde ele espera `tickets-acli.json`, passar a exigir `tickets-acli.sh` sem `create-bulk` e com corpo íntegro; rodar → FAIL.
- [ ] **Step 2: implementar** — `from projecao import corpo_ticket, etiquetas, emitir_sh_acli` (mesmo diretório); em `exportar()`, `if projeto: emitir_sh_acli([...], projeto, saida)` montando itens de `dados["items"]` com `not i["externo"]`.
- [ ] **Step 3: selftest verde** + `python3 skills/handoff/scripts/debito.py exportar . --saida /tmp/x --projeto SBX` gera `.sh` são.
- [ ] **Step 4: commit** — `feat(017-jira-tickets): debito.py emite .sh unitário e aposenta o bulk (MUDA R52)`.

### Task 3: `tickets.py` — geração do tickets.md e da ida (R1)

**Files:**
- Create: `skills/spec-feature/scripts/tickets.py`
- Test: selftest embutido (`--selftest`, fixtures inline com tasks.md sintético)

**Interfaces:**
- Consumes: `projecao.emitir_sh_acli` via `sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "handoff" / "scripts"))` — layout `skills/<nome>/scripts/` é estável no repo e no cache do plugin; comentário no código explica a dependência.
- Produces:
  - `parse_tasks(texto: str) -> list[dict]` — âncora `^- \[([ x])\] (T\d+)(?: \(dep: ([^)]+)\))? — (.+?) · arquivos: .+? · cobre: .+? · verificação: .+$` → `{"id","feito","deps","acao"}`; linha T malformada → erro nomeando a linha (código ≠ 0).
  - `ler_projeto_jira(root: Path) -> str | None` — lê `doc-profile.yaml` → `motores.jira.projeto`; ausente/desligado → `None`.
  - Subcomandos: `gerar <delta-dir>` (escreve `tickets.md`), `exportar <delta-dir> --saida DIR` (chama `emitir_sh_acli` com `epico="[delta-NNN] nome"`; tickets com `Externo` preenchido são pulados — idempotência), `diff <delta-dir> --externo jira.json` (T4).
  - Formato do `tickets.md` gerado (parseável por âncoras; `Externo` gravado pela skill após executar o `.sh`):

```markdown
# Tickets — delta-017-jira-tickets · projeto: SBX
Épico: [delta-017] jira-tickets · Externo: —
- T1 — <ação> · status: aberto · deps: — · Externo: —
- T2 — <ação> · status: aberto · deps: T1 · Externo: —
```

- [ ] **Step 1: selftest que falha** — casos: tasks.md com 3 tasks (1 com dep, 1 feita) → tickets.md com status certo e deps preservadas; doc-profile sem `jira` → `gerar` sai com aviso de 1 linha e código 0 (RNF2); linha T malformada → erro nomeando a linha; `exportar` com um `Externo: SBX-9` preenchido → esse ticket não aparece no `.sh`; deps viram bloco de `acli jira workitem link` no `.sh` (tipo `Blocks`).
- [ ] **Step 2: rodar e ver falhar.**
- [ ] **Step 3: implementar** — funções puras (`parse_tasks`, `montar_tickets_md`) separadas do I/O (`cmd_gerar`, `cmd_exportar`); links de bloqueio: após os creates, `acli jira workitem link --source <filho-dep> --target <filho> --type Blocks` usando as chaves capturadas em variáveis do `.sh` (`T1_KEY=$(... --json | python3 -c ...)`).
- [ ] **Step 4: selftest verde.**
- [ ] **Step 5: commit** — `feat(017-jira-tickets): tickets.py gera tickets.md e a ida acli (R1)`.

### Task 4: volta como diff aprovado (R3)

**Files:**
- Modify: `skills/spec-feature/scripts/tickets.py` (subcomando `diff`)
- Test: selftest (fixtures de JSON do `acli search`)

**Interfaces:**
- Consumes: `parse_tickets_md(texto) -> list[dict]` (interno, mesma âncora do formato acima); JSON de `acli jira workitem search --jql "project=CHAVE AND labels=delta:NNN" --json` colhido pela skill e passado por arquivo.
- Produces: tabela markdown *tickets.md diz × Jira diz × impacto × ação proposta* (formato do R27) cobrindo: issue fechada com task aberta; task concluída (`- [x]` no tasks.md ⇒ `status: concluído`) com issue aberta; issue órfã (label da delta sem linha correspondente); ticket sem issue (Externo vazio ou chave inexistente); épico aberto com delta arquivada. **Nunca escreve** no repo — só propõe (aprovação humana aplica).

- [ ] **Step 1: selftest que falha** — um caso por linha da cobertura acima, com JSON mínimo inline.
- [ ] **Step 2–4: implementar (pura: `comparar(tickets, externos) -> list[dict]`; I/O só imprime), selftest verde, commit** — `feat(017-jira-tickets): volta Jira→repo como diff aprovado (R3)`.

### Task 5: C11 valida `motores.jira` + template do doc-profile

**Files:**
- Modify: `skills/spec-feature/scripts/check_cycle.py` (bloco C11, ~linha 400: `jira` ligado sem `projeto` → ALTO, espelhando o caso do graphify_backend) e selftest do C11 (3 casos novos: `jira: {projeto: SBX}` → 0 achados; `jira: {}`/`jira: true` → 1 ALTO; sem `jira` → 0)
- Modify: `skills/projeto-init/references/templates/doc-profile.yaml` (chave `jira` comentada na seção `motores`, com 1 linha de explicação)
- Test: `python3 skills/spec-feature/scripts/check_cycle.py --selftest`

**Interfaces:** consome/produz nada de outras tasks (paralelizável).

- [ ] **Step 1: casos novos no selftest do C11 → FAIL. Step 2: implementar. Step 3: verde. Step 4: commit** — `feat(017-jira-tickets): C11 valida motores.jira; template do doc-profile ganha a chave`.

### Task 6: documentação no mesmo change

**Files:**
- Modify: `skills/spec-feature/references/cycle.md` (fase tasks ganha o passo condicional de projeção: doc-profile com `motores.jira` → `tickets.py gerar/exportar`; a skill executa o `.sh` e grava `Externo`)
- Modify: `skills/spec-feature/references/adapters.md` (tabela de política: re-verificação do max datada 2026-08-07, nota da ADR-0024, gatilho novo)
- Modify: `skills/handoff/references/debito.md` (dialeto: `.sh` unitário, bulk aposentado, motivo DT-021)
- Modify: `CHANGELOG.md` (`[Não lançado]`: Adicionado — tickets.md/projeção Jira; Corrigido — dialeto; Mudado — política do max)
- Test: `python3 skills/guarding-doc-integrity/scripts/validate_integrity.py .` (links) — roda no pre-commit.

- [ ] **Step 1: editar os 4 + conferir se algum doc cita `tickets-acli.json` (grep) e corrigir. Step 2: commit** — `docs(017-jira-tickets): ciclo, adapters (ADR-0024 datado), debito.md e CHANGELOG`.

### Task 7 (dep: T2, T3, T4): validação real contra o SBX — fecha o DT-021

**Files:**
- Modify: `DEBT.md` (DT-021 → quitado, com evidência)
- Test: execução real no sandbox (a skill executa; os scripts só emitiram)

- [ ] **Step 1:** `python3 skills/handoff/scripts/debito.py exportar <fixture DT-021> --saida X --projeto SBX` + executar o `.sh` → corpo multi-linha íntegro no ticket (conferir com `acli jira workitem view <chave> --json`).
- [ ] **Step 2:** fixture de delta (tasks.md de 3 tasks) → `tickets.py gerar` + `exportar` + executar → épico + 3 filhas + link de bloqueio visíveis no SBX; `search --jql` + `tickets.py diff` → tabela sã (1 divergência forjada fechando uma issue à mão).
- [ ] **Step 3:** DT-021 → `quitado` no DEBT.md (Encerrado: data + evidência SBX + ref do PR); `python3 skills/handoff/scripts/debito.py fila .` PASS.
- [ ] **Step 4: commit** — `feat(017-jira-tickets): validação real no SBX — DT-021 quitado`.

---

## Self-review (executado na escrita)

1. **Cobertura:** R1→T3+T5+T6/T7; R2→T1+T2+T7; R3→T4+T7. Sem lacuna.
2. **Placeholders:** nenhum TBD; código central presente (emissão, âncoras, selftests).
3. **Consistência de tipos:** `emitir_sh_acli(itens, projeto, saida, epico=None)` idêntica em T1/T2/T3; formato do tickets.md idêntico em T3/T4.
