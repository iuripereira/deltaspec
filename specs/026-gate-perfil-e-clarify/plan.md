<!-- resumo deltaspec · ≤15 linhas · única parte do plano lida pelo analyze e pelo humano -->
**Objetivo:** Fechar DT-013 e DT-023 — o gate ganha o C11 (schema do `doc-profile.yaml`, núcleo exigido e cauda tolerada) e o C12 (trilha do clarify), e o contrato do clarify passa a declarar se houve canal humano. **Cobre:** R1, R2, RNF1 (da delta-026) **Decisões duráveis → ADRs:** ADR-0023 (PyYAML como dependência admitida, gravada no clarify) **Riscos assumidos:** o framework deixa de ser instalável por cópia pura — quem clonar precisa de `pip install pyyaml`, e a ressalva vive em 3 espelhos que precisam ficar em sincronia; o C11 valida o núcleo medido em 7 perfis reais, então perfil futuro com núcleo diferente exige nova delta.

**TDD:** obrigatório nas T1 e T2 (lógica pura, contrato fechado, fixtures baratas) — teste que falha antes, mínimo que passa depois. As T3–T5 são documentação/config, sem dispensa a justificar por não haver função a testar.

---

# Gate do doc-profile e canal humano no clarify — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dois checks novos no `check_cycle.py` com selftest co-localizado, o contrato do clarify exigindo trilha citável, e a exceção do PyYAML declarada nos três espelhos + CI.

**Architecture:** O `check_cycle.py` já tem o padrão: uma função `cNN_nome(...) -> None` que só **acrescenta tuplas** `(severidade, onde, inconsistência, ação)` na lista `v`, chamada por `checar()`. As funções são puras sobre texto lido pelo chamador — exceto as que precisam do filesystem (`c3`, `c4`, `c6`, `c10`), que recebem `root`. O C11 recebe `root` (lê `root/doc-profile.yaml`); o C12 recebe `spec_txt` já lido. Nenhum arquivo novo.

**Tech Stack:** Python 3.11+ · `yaml` (PyYAML — **primeira e única dependência externa**, ADR-0023) · `re`, `pathlib` · Markdown PT-BR.

## Global Constraints

- Identificadores e comentários dos scripts em **PT-BR** — padrão vigente em `check_cycle.py`; não misturar idiomas.
- **Zero valor mágico:** todo limiar e toda lista fechada vira constante nomeada no topo do módulo, junto de `REQ_ID`/`CABECALHO`.
- **Campo só vale na posição canônica** (lição de 2026-07-28 e 2026-08-01): usar `.match` com âncora de início de linha, nunca `search` solto. Toda sintaxe nova nasce com fixture de regressão "sintaxe mencionada em prosa/comentário".
- Nenhuma severidade do C11 ou do C12 é `CRÍTICO` — perímetro do ADR-0006: o gate reporta, o juízo decide.
- Commits: `feat(026-gate-perfil-e-clarify):`.

---

### Task 1: C11 — schema do `doc-profile.yaml`

**Files:**
- Modify: `skills/spec-feature/scripts/check_cycle.py` (constantes no topo · `c11_perfil()` antes de `checar()` · chamada em `checar()` · `selftest_c11()` · docstring do cabeçalho)

**Interfaces:**
- Consumes: nada (task livre).
- Produces: `c11_perfil(root: Path, v: list) -> None` e as constantes `NUCLEO_TOPO`, `NUCLEO_ARTEFATOS`, que a T2 não usa mas o selftest referencia.

- [ ] **Step 1: Escrever o selftest que falha**

Acrescentar em `selftest()`, no padrão das fixtures existentes (`tmp_path` com perfil escrito à mão):

```python
def selftest_c11() -> None:
    """C11: núcleo exigido, cauda tolerada, YAML inválido não estoura."""
    import tempfile, textwrap
    nucleo = textwrap.dedent("""\
        version: 1
        decisao: { data: "2026-08-02", justificativa: "" }
        publico: { interno: true, cliente: false }
        artefatos:
          arquitetura:  { obrigatorio: true }
          modelo-dados: { obrigatorio: false }
          fluxos:       { obrigatorio: false }
          casos-de-uso: { obrigatorio: false }
        """)
    casos = [
        (nucleo, [], "perfil de núcleo completo não acusa nada"),
        (nucleo + "  explicativos: { obrigatorio: false }\n", [], "cauda presente é aceita"),
        (nucleo.replace("version: 1\n", ""), ["ALTO"], "chave de núcleo ausente acusa ALTO"),
        (nucleo.replace("casos-de-uso: { obrigatorio: false }", ""), ["ALTO"], "categoria de núcleo ausente acusa ALTO"),
        (nucleo.replace("obrigatorio: true", "obrigatorio: false"), ["ALTO"], "nenhum obrigatório + justificativa vazia acusa ALTO"),
        (nucleo + "motores: { graphify: true, graphify_backend: '' }\n", ["ALTO"], "graphify ligado sem backend acusa ALTO"),
        ("version: 1\n  isto: : não é yaml\n", ["ALTO"], "YAML inválido acusa ALTO, sem exceção"),
    ]
    for texto, esperado, desc in casos:
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            (raiz / "doc-profile.yaml").write_text(texto, encoding="utf-8")
            v: list = []
            c11_perfil(raiz, v)
            sev = [s for s, *_ in v]
            assert [s for s in sev if s == "ALTO"] == [s for s in esperado if s == "ALTO"], f"{desc}: {v}"
            assert "CRÍTICO" not in sev, f"{desc}: C11 nunca é CRÍTICO"
    with tempfile.TemporaryDirectory() as d:  # ausência = BAIXO
        v = []
        c11_perfil(Path(d), v)
        assert v and v[0][0] == "BAIXO", v
    print("selftest C11: OK (núcleo exigido, cauda tolerada, YAML inválido tratado)")
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python3 skills/spec-feature/scripts/check_cycle.py --selftest`
Expected: `NameError: name 'c11_perfil' is not defined`

- [ ] **Step 3: Escrever o mínimo que passa**

Constantes junto das outras regex do topo:

```python
# C11 (delta-026): núcleo do doc-profile medido em 7 perfis reais (2026-08-02) — a cauda
# (explicativos, prototipo, apresentacao, ...) é opcional por desenho: categoria que uma
# delta acrescenta ao template nunca propaga retroativamente aos projetos existentes.
NUCLEO_TOPO = ("version", "decisao", "publico", "artefatos")
NUCLEO_ARTEFATOS = ("arquitetura", "modelo-dados", "fluxos", "casos-de-uso")
```

```python
def c11_perfil(root: Path, v: list) -> None:
    """Schema do doc-profile.yaml (DT-013, delta-026): exige o núcleo estável, tolera a
    cauda opcional. Nunca CRÍTICO — perfil malformado reporta, não bloqueia (ADR-0006)."""
    perfil = root / "doc-profile.yaml"
    if not perfil.is_file():
        v.append(("BAIXO", "doc-profile.yaml", "perfil ausente na raiz",
                  "criar do template do projeto-init para registrar a decisão de documentação (ADR-0009)"))
        return
    try:
        d = yaml.safe_load(perfil.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        v.append(("ALTO", "doc-profile.yaml", f"YAML inválido: {str(e).splitlines()[0]}", "corrigir a sintaxe do perfil"))
        return
    if not isinstance(d, dict):
        v.append(("ALTO", "doc-profile.yaml", "raiz do perfil não é um mapa", "usar o template do projeto-init"))
        return
    for chave in NUCLEO_TOPO:
        if chave not in d:
            v.append(("ALTO", "doc-profile.yaml", f"chave de núcleo ausente: {chave}", "copiar do template do projeto-init"))
    dec = d.get("decisao") or {}
    for sub in ("data", "justificativa"):
        if not isinstance(dec, dict) or sub not in dec:
            v.append(("ALTO", "doc-profile.yaml", f"decisao.{sub} ausente", "toda decisão de documentação é datada e justificada (ADR-0009)"))
    pub = d.get("publico") or {}
    for sub in ("interno", "cliente"):
        if not isinstance(pub, dict) or not isinstance(pub.get(sub), bool):
            v.append(("ALTO", "doc-profile.yaml", f"publico.{sub} ausente ou não booleano", "declarar true/false"))
    art = d.get("artefatos") or {}
    if not isinstance(art, dict):
        art = {}
    for cat in NUCLEO_ARTEFATOS:
        if cat not in art:
            v.append(("ALTO", "doc-profile.yaml", f"categoria de núcleo ausente: {cat}", "copiar do template — a cauda é opcional, o núcleo não"))
    obrigatorios = [k for k, s in art.items() if isinstance(s, dict) and s.get("obrigatorio")]
    just = (dec.get("justificativa") or "").strip() if isinstance(dec, dict) else ""
    if not obrigatorios and not just:
        v.append(("ALTO", "doc-profile.yaml", "nenhum artefato obrigatório e decisao.justificativa vazia",
                  "perfil sem obrigatório só é válido com justificativa preenchida (cycle.md)"))
    mot = d.get("motores") or {}
    if isinstance(mot, dict) and mot.get("graphify") and not (mot.get("graphify_backend") or "").strip():
        v.append(("ALTO", "doc-profile.yaml", "motores.graphify ligado sem motores.graphify_backend",
                  "declarar o backend ou pare e pergunte ao usuário (R44, ADR-0022)"))
```

Import no topo, junto dos demais: `import yaml`.

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `python3 skills/spec-feature/scripts/check_cycle.py --selftest`
Expected: `selftest C11: OK (núcleo exigido, cauda tolerada, YAML inválido tratado)`

- [ ] **Step 5: Ligar no `checar()` e atualizar a docstring do cabeçalho**

Em `checar()`, junto dos que recebem `root`: `c11_perfil(root, v)`. Na docstring do topo, acrescentar a linha `C11 doc-profile — núcleo ausente, YAML inválido, obrigatório sem justificativa (delta-026)`.

- [ ] **Step 6: Rodar contra os 7 perfis reais** (validação de campo, não teste)

Run: `for p in ~/code/*/doc-profile.yaml ~/code/imex/*/doc-profile.yaml; do echo "$p"; done`
Expected: o C11 acusa os desvios já medidos (justificativa vazia é aceita porque há obrigatório; `version: 2` passa — o check não fixa o valor) e **nenhum falso ALTO** em perfil íntegro.

- [ ] **Step 7: Commit**

```bash
git add skills/spec-feature/scripts/check_cycle.py
git commit -m "feat(026-gate-perfil-e-clarify): C11 valida o schema do doc-profile.yaml"
```

---

### Task 2 (dep: T1): C12 — trilha do clarify

**Files:**
- Modify: `skills/spec-feature/scripts/check_cycle.py` (regex `CLARIFY` no topo · `c12_clarify()` · chamada em `checar()` · `selftest_c12()` · docstring)

**Interfaces:**
- Consumes: o arquivo já editado pela T1 (mesmo arquivo → sequencial, não paralelizável).
- Produces: `c12_clarify(spec_txt: str, v: list) -> None`.

- [ ] **Step 1: Escrever o selftest que falha**

```python
def selftest_c12() -> None:
    """C12: trilha do clarify exigida no perfil completo, dispensada no enxuto,
    e imune a menção da sintaxe em prosa."""
    base = "# delta-999 — x\nEstado: proposta · Perfil: {perfil}\n{trilha}\n\n## Contexto\n"
    casos = [
        ("completo", "Clarify: entrevistado (2026-08-02) — 3 decisões do usuário", 0, "entrevistado passa"),
        ("completo", "Clarify: auto-avaliado (2026-08-02) — sem canal humano", 0, "auto-avaliado passa (declarado é o ponto)"),
        ("completo", "", 1, "perfil completo sem trilha acusa ALTO"),
        ("enxuto — aprovado", "", 0, "perfil enxuto dispensa (clarify sob demanda)"),
        ("completo", "o texto abaixo cita Clarify: entrevistado sem ser a âncora", 1,
         "sintaxe em prosa não conta — só vale no início da linha"),
    ]
    for perfil, trilha, esperado, desc in casos:
        v: list = []
        c12_clarify(base.format(perfil=perfil, trilha=trilha), v)
        assert len([s for s, *_ in v if s == "ALTO"]) == esperado, f"{desc}: {v}"
    print("selftest C12: OK (trilha exigida no completo, dispensada no enxuto, prosa não engana)")
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python3 skills/spec-feature/scripts/check_cycle.py --selftest`
Expected: `NameError: name 'c12_clarify' is not defined`

- [ ] **Step 3: Escrever o mínimo que passa**

```python
# C12 (delta-026): trilha do clarify. `match` com âncora de início de linha — a mesma
# sintaxe citada em prosa é texto, não campo (lições de 2026-07-28 e 2026-08-01).
CLARIFY = re.compile(r"^Clarify:\s*(entrevistado|auto-avaliado)\b", re.M)
```

```python
def c12_clarify(spec_txt: str, v: list) -> None:
    """Trilha do clarify (DT-023, delta-026): o perfil completo não fecha o clarify sem
    declarar se houve canal humano. Perfil enxuto dispensa — lá o clarify é sob demanda."""
    cab = cabecalho(spec_txt)
    perfil = (campo(cab, "Perfil") or "").lower()
    if perfil.startswith("enxuto"):
        return
    if not CLARIFY.search(spec_txt):
        v.append(("ALTO", "spec.md", "sem a trilha do clarify no cabeçalho",
                  "declarar 'Clarify: entrevistado (AAAA-MM-DD) — <N> decisões do usuário' "
                  "ou 'Clarify: auto-avaliado (AAAA-MM-DD) — sem canal humano' (R8)"))
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `python3 skills/spec-feature/scripts/check_cycle.py --selftest`
Expected: `selftest C12: OK (trilha exigida no completo, dispensada no enxuto, prosa não engana)`

- [ ] **Step 5: Ligar no `checar()`** — `c12_clarify(spec_txt, v)`, junto do C8 que também consome `spec_txt`. Docstring do topo ganha `C12 trilha do clarify — perfil completo sem canal humano declarado (delta-026)`.

- [ ] **Step 6: Rodar o gate na própria delta**

Run: `python3 skills/spec-feature/scripts/check_cycle.py specs/026-gate-perfil-e-clarify`
Expected: sem achado do C12 — a spec desta delta já carrega a linha.

- [ ] **Step 7: Commit**

```bash
git add skills/spec-feature/scripts/check_cycle.py
git commit -m "feat(026-gate-perfil-e-clarify): C12 exige a trilha do clarify no perfil completo"
```

---

### Task 3: Contrato do clarify na prosa normativa

**Files:**
- Modify: `skills/spec-feature/references/cycle.md` (linha do clarify na tabela de fases · tabela da trilha de auditoria)
- Modify: `skills/spec-feature/references/adapters.md` (verificação pós-fase da seção grill)
- Modify: `skills/spec-feature/references/templates/delta-spec.md` (linha `Clarify:` no cabeçalho)

**Interfaces:**
- Consumes: nada (task livre — arquivos distintos da T1/T2, paralelizável).
- Produces: a prosa que o C12 mecaniza; nenhuma outra task consome.

- [ ] **Step 1: `cycle.md`** — a coluna "Saída (critério de pronto)" da linha `clarify` ganha, ao final: `; trilha do clarify no cabeçalho declarando se houve canal humano (C12)`. A tabela "Trilha de auditoria de aprovação" ganha a linha:

```markdown
| Trilha do clarify (R8) | cabeçalho do `spec.md` | `Clarify: entrevistado (AAAA-MM-DD) — <N> decisões do usuário` · `Clarify: auto-avaliado (AAAA-MM-DD) — sem canal humano` |
```

- [ ] **Step 2: `adapters.md`**, seção grill-me/grill-with-docs — a verificação pós-fase passa a exigir a trilha e a registrar o viés:

```markdown
- **Verificação pós-fase:** ADRs novos conformes ao template **e** a trilha do clarify no
  cabeçalho do `spec.md` (C12) — `entrevistado` com o número de decisões do usuário, ou
  `auto-avaliado` quando não houve canal humano. Ambiguidade resolvida por exploração do
  repositório **não conta como resposta do usuário**; nesse caso o relatório sai marcado
  `auto-avaliado`. Quem redige a spec é quem pontua o relatório: na dúvida entre dois graus,
  escolha o mais ambíguo (regra do próprio `grill-me`).
```

- [ ] **Step 3: `templates/delta-spec.md`** — abaixo da linha de Estado:

```markdown
Clarify: {{entrevistado|auto-avaliado}} ({{AAAA-MM-DD}}) — {{<N> decisões do usuário | sem canal humano}}
<!-- trilha do clarify (R8): âncora canônica lida pelo C12; perfil enxuto dispensa -->
```

- [ ] **Step 4: Verificar**

Run: `python3 skills/guarding-doc-integrity/scripts/validate_integrity.py .`
Expected: `RESULTADO: PASS`

Run: `grep -c "auto-avaliado" skills/spec-feature/references/cycle.md skills/spec-feature/references/adapters.md skills/spec-feature/references/templates/delta-spec.md`
Expected: ≥ 1 em cada

- [ ] **Step 5: Commit**

```bash
git add skills/spec-feature/references/
git commit -m "docs(026-gate-perfil-e-clarify): contrato do clarify exige trilha de canal humano"
```

---

### Task 4: Exceção do PyYAML nos três espelhos e no CI

**Files:**
- Modify: `CLAUDE.md` (linha do princípio "Zero dependência supérflua")
- Modify: `README.md` · `README.en.md` (a frase "Sem dependência externa")
- Modify: `.github/workflows/ci.yml` (passo de instalação antes dos selftests)

**Interfaces:**
- Consumes: nada (task livre, paralelizável com T1–T3).
- Produces: nada que outra task consuma.

- [ ] **Step 1: `CLAUDE.md`** — a linha passa a:

```markdown
- **Zero dependência supérflua (YAGNI/DRY):** prefira stdlib e recursos nativos; não adicione framework/lib onde uma função resolve. Os gates usam stdlib (`re`, `pathlib`, `subprocess`, `tomllib`, `sys`) mais **uma única dependência externa admitida: `PyYAML`**, necessária para validar o `doc-profile.yaml` — a renúncia ao parser próprio está na [ADR-0023](docs/adrs/ADR-0023-pyyaml-como-dependencia-admitida.md). Dependência nova exige o mesmo grau de justificativa, nunca um aceno para essa ADR.
```

- [ ] **Step 2: `README.md`** — a frase de `:311` passa a:

```markdown
Tudo roda **na sua máquina** — na fase analyze, no arquivamento e no pré-commit ([ADR-0001](docs/adrs/ADR-0001-gates-rodam-local.md)). Uma única dependência externa: `pip install pyyaml`, para validar o `doc-profile.yaml` ([ADR-0023](docs/adrs/ADR-0023-pyyaml-como-dependencia-admitida.md)); o resto é biblioteca padrão do Python 3.11+.
```

- [ ] **Step 3: `README.en.md`** — a frase de `:312`, nos mesmos termos:

```markdown
Everything runs **on your machine** — at the analyze phase, at archive time and on pre-commit ([ADR-0001](docs/adrs/ADR-0001-gates-rodam-local.md)). A single external dependency: `pip install pyyaml`, to validate `doc-profile.yaml` ([ADR-0023](docs/adrs/ADR-0023-pyyaml-como-dependencia-admitida.md)); everything else is the Python 3.11+ standard library.
```

- [ ] **Step 4: `.github/workflows/ci.yml`** — antes do passo que roda os selftests:

```yaml
      - name: Instala a dependência dos gates (ADR-0023)
        run: python3 -m pip install --quiet pyyaml
```

- [ ] **Step 5: Verificar que nenhum espelho segue prometendo zero-dep**

Run: `grep -rn "só a biblioteca padrão\|just the Python 3.11+ standard library\|zero pacote externo" CLAUDE.md README.md README.en.md`
Expected: nenhuma linha

- [ ] **Step 6: Commit**

```bash
git add CLAUDE.md README.md README.en.md .github/workflows/ci.yml
git commit -m "docs(026-gate-perfil-e-clarify): declara PyYAML como dependência admitida"
```

---

### Task 5 (dep: T1, T2, T3, T4): CHANGELOG e HANDOFF

**Files:**
- Modify: `CHANGELOG.md` (`## [Não lançado]`) · `HANDOFF.md`

**Interfaces:**
- Consumes: T1–T4.

- [ ] **Step 1: `CHANGELOG.md`** sob `[Não lançado]`:

```markdown
### Adicionado
- **C11 e C12 no gate determinístico** (delta-026): o C11 valida o schema do `doc-profile.yaml` — núcleo exigido (`version`, `decisao`, `publico`, `artefatos` com as 4 categorias que existem em 7/7 dos perfis reais) e cauda tolerada, mais `motores.graphify` ligado sem backend. O C12 exige a trilha do clarify no perfil completo. Nenhum dos dois é CRÍTICO: reportam, não bloqueiam (ADR-0006). Fecha DT-013 e DT-023.

### Mudado
- **O clarify não fecha mais sem declarar se teve canal humano** (delta-026, MUDA R8): o `spec.md` passa a carregar `Clarify: entrevistado (data) — N decisões do usuário` ou `Clarify: auto-avaliado (data) — sem canal humano`. Ambiguidade resolvida por exploração do repositório não conta como resposta do usuário, e o contrato registra que quem redige a spec é quem pontua o relatório.
- **`PyYAML` passa a ser dependência externa admitida dos gates** (delta-026, [ADR-0023](docs/adrs/ADR-0023-pyyaml-como-dependencia-admitida.md)): a única. Renunciamos ao parser próprio porque o modo de falha dele é silencioso — um `LIBERADO` falso —, e à degradação graciosa porque ela é contrato para motor opcional, não para o gate. Os três espelhos da promessa e o CI foram atualizados.
```

- [ ] **Step 2: `HANDOFF.md`** — linha em "Feito recentemente" citando os dois DTs quitados e o achado da varredura (7 perfis, núcleo estável, cauda nunca propagada).

- [ ] **Step 3: Verificar**

Run: `python3 skills/spec-feature/scripts/check_cycle.py specs/026-gate-perfil-e-clarify`
Expected: sem CRÍTICO; C2 com todos os Rn cobertos

- [ ] **Step 4: Commit**

```bash
git add CHANGELOG.md HANDOFF.md
git commit -m "docs(026-gate-perfil-e-clarify): CHANGELOG e HANDOFF da delta-026"
```
