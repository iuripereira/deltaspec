#!/usr/bin/env python3
"""Transforma um PRD (formato deltaspec) em markdown amigável ao cliente (ADR-0009).

O quê: nas seções "Requisitos Funcionais"/"Requisitos Não Funcionais" do padrão
deltaspec (localizadas pelo título, independentes da numeração), os cenários `- DADO ... QUANDO ... ENTÃO ...`
viram tabela por grupo de RF (Item · Pré-condição · Ação · Resultado esperado) e os
RNFs viram tabela (ID · Requisito · Métrica · Verificação); no restante do documento,
a indentação de bullets aninhados é dobrada (2→4), porque o caminho PDF do
`exporta_entregavel.py` usa python-markdown, que só aninha listas com 4 espaços —
com 2, a hierarquia achata e o cenário aparece como irmão do requisito.

Semântica da tabela: DADO = pré-condição (pré-requisito) · QUANDO = ação (gatilho) ·
ENTÃO = resultado esperado (saída verificável). Transformação de APRESENTAÇÃO apenas —
o `PRD.md` canônico permanece no formato deltaspec; rode sobre a cópia do entregável.

Paridade garantida por assert: nenhum cenário/RNF pode se perder na transformação.

Uso:  tabela_cliente.py <entrada.md> <saida.md>
      tabela_cliente.py --selftest
"""
import re
import sys


def esc(cell: str) -> str:
    return cell.replace("|", "\\|").strip()


def join_wrapped(lines):
    """Junta linhas de continuação (prosa quebrada) ao bullet anterior."""
    out = []
    for ln in lines:
        s = ln.strip()
        if not s:
            out.append(ln)
            continue
        starts_block = s.startswith(("- ", "* ", "#", ">", "|", "---"))
        prev_joinable = out and out[-1].strip().startswith(("- ", "* "))
        if starts_block or not prev_joinable:
            out.append(ln)
        else:
            out[-1] = out[-1].rstrip() + " " + s
    return out


def transform_rf(section: str):
    lines = join_wrapped(section.splitlines())
    out, rows, cur_req, n_scen = [], [], None, 0

    def flush():
        nonlocal rows
        if rows:
            out.extend(["",
                        "| Item | Pré-condição (DADO) | Ação (QUANDO) | Resultado esperado (ENTÃO) |",
                        "|---|---|---|---|", *rows, ""])
            rows = []

    for ln in lines:
        s = ln.strip()
        if s.startswith("### "):
            flush()
            out.append(ln)
            continue
        m = re.match(r"- \*\*(RF-[\d.]+)", s) if not ln.startswith(" ") else None
        if m:
            cur_req = m.group(1).rstrip(".")
            out.append(ln)
            continue
        if ln.startswith("  ") and s.startswith("- DADO "):
            body = s[2:]
            pre, sepq, rest = body.partition(" QUANDO ")
            acao, sepe, ent = rest.partition(" ENTÃO ")
            assert sepq and sepe, f"cenário sem QUANDO/ENTÃO: {s[:80]}"
            rows.append(f"| {esc(cur_req or '—')} | {esc(pre[len('DADO '):])} | {esc(acao)} | {esc(ent)} |")
            n_scen += 1
            continue
        if ln.startswith("  - "):  # nested não-cenário: aprofunda p/ 4 espaços
            out.append("    " + s)
            continue
        out.append(ln)
    flush()
    return "\n".join(out), n_scen


def transform_rnf(section: str):
    lines = join_wrapped(section.splitlines())
    intro, rows, tail, cur = [], [], [], None

    def push():
        if cur:
            rows.append(f"| {esc(cur['id'])} | **{esc(cur['title'])}.** {esc(cur['req'])} "
                        f"| {esc(cur['met'])} | {esc(cur['ver'])} |")

    for ln in lines:
        s = ln.strip()
        m = (re.match(r"- (~~)?\*\*(RNF-\d+)\s*—\s*(.+?)\.?\*\*(~~)?\s*(.*)", s)
             if not ln.startswith(" ") else None)
        if m:
            push()
            cur = {"id": m.group(2) + (" (removido)" if m.group(1) else ""),
                   "title": m.group(3), "req": m.group(5).replace("~~", ""),
                   "met": "—", "ver": "—"}
            continue
        if ln.startswith("  ") and s.startswith("- Métrica:") and cur:
            body = s[len("- Métrica:"):].strip()
            met, sep, ver = body.partition("· Verificação:")
            cur["met"] = met.strip(" ·")
            cur["ver"] = ver.strip() if sep else "—"
            continue
        if cur is None:
            intro.append(ln)
        elif not ln.startswith(" "):
            tail.append(ln)  # conteúdo de nível superior após os RNFs (---, notas) — preservar
    push()
    while tail and not tail[0].strip():
        tail.pop(0)
    out = intro + ["", "| ID | Requisito | Métrica | Verificação |", "|---|---|---|---|", *rows, ""] + tail
    return "\n".join(out), len(rows)


def deepen_indents(text: str) -> str:
    """Duplica a indentação de todo conteúdo aninhado (2→4, 4→8) — python-markdown só
    aninha com 4 — e abre linha em branco antes de tabela colada no item, sem a qual as
    linhas viram texto literal dentro do bullet mesmo com 4 espaços (DT-009, delta-032).
    Dentro de cerca (```) nada é tocado: indentação lá é literal."""
    out, cerca = [], False
    # split("\n"), não splitlines(): splitlines+join come o \n final — inclusive a linha em
    # branco que separa a última tabela da seção do heading seguinte (delta-032)
    for ln in text.split("\n"):
        if ln.lstrip().startswith("```"):
            cerca = not cerca
            out.append(ln)
            continue
        m = None if cerca else re.match(r"^( {2,})\S", ln)
        if m:
            if (ln.lstrip().startswith("|") and out and out[-1].strip()
                    and not out[-1].lstrip().startswith("|")):
                out.append("")
            ln = " " * (2 * len(m.group(1))) + ln.lstrip()
        out.append(ln)
    return "\n".join(out)


def split_sections(md: str):
    # localiza RF/RNF pelo TÍTULO, não pelo número — PRDs renumerados (0→1, 2026-07-20)
    # movem as seções (ex.: RF de §6 para §7) sem mudar os títulos
    h_rf = re.search(r"^## \d+\. Requisitos Funcionais.*$", md, re.M)
    h_rnf = re.search(r"^## \d+\. Requisitos Não Funcionais.*$", md, re.M)
    assert h_rf and h_rnf, "headings de RF/RNF não encontrados — o PRD segue o PRD.template.md?"
    h_next = re.search(r"^## \d+\. .*$", md[h_rnf.end():], re.M)
    assert h_next, "não há seção numerada após os RNF — o PRD segue o PRD.template.md?"
    fim_rnf = h_rnf.end() + h_next.start()
    return (md[: h_rf.start()], md[h_rf.start(): h_rnf.start()],
            md[h_rnf.start(): fim_rnf], md[fim_rnf:])


def transform(md: str):
    before, sec6, sec7, after = split_sections(md)
    n_src_scen = len(re.findall(r"^\s+- DADO ", sec6, re.M))
    n_src_rnf = len(re.findall(r"^- (?:~~)?\*\*RNF-\d+", sec7, re.M))
    t6, n_scen = transform_rf(sec6)
    t7, n_rnf = transform_rnf(sec7)
    assert n_scen == n_src_scen, f"cenários perdidos: fonte {n_src_scen}, tabela {n_scen}"
    assert n_rnf == n_src_rnf, f"RNFs perdidos: fonte {n_src_rnf}, tabela {n_rnf}"
    # linha em branco garantida entre cada seção e o heading seguinte — tabela colada em
    # "## 6."/"## 7."/"## 8." vira linha da tabela no python-markdown (achado da rodada
    # IMEX 20-07; o seam do before entrou na delta-032, quando o §5 passou a poder
    # terminar em tabela aninhada)
    t6, t7 = t6.rstrip("\n") + "\n\n", t7.rstrip("\n") + "\n\n"
    b = deepen_indents(before).rstrip("\n") + "\n\n"
    return b + t6 + t7 + deepen_indents(after), n_scen, n_rnf


SELFTEST_MD = """# PRD — Exemplo

## 5. Regras
- RN-01 — regra.
  - sub-bullet aninhado fora de RF/RNF
- RN-02 — regra com tabela de decisão colada no item:
  | Faixa | Ação |
  |---|---|
  | A | repor |
- RN-03 — regra com parágrafo aninhado:

  Detalhe da regra, aninhado no item.

```text
  linha indentada dentro de cerca — não tocar
```

## 6. Requisitos Funcionais (RF)

### RF-01 — Grupo um
- **RF-01.1** Enunciado do requisito.
  - DADO um estado com `pipe | dentro` QUANDO a ação ocorre
    ENTÃO o resultado esperado acontece
- **RF-01.2** Outro enunciado.
  - DADO outro estado QUANDO outra ação ENTÃO outro resultado

## 7. Requisitos Não Funcionais (RNF)

- **RNF-01 — Qualidade um.** Descrição.
  - Métrica: limiar X · Verificação: como medir
- ~~**RNF-02 — Removido.**~~ Obsoleto.

---

## 8. Seção seguinte
Texto.
"""


def selftest():
    result, n_scen, n_rnf = transform(SELFTEST_MD)
    assert n_scen == 2 and n_rnf == 2, f"contagem: {n_scen} cenários, {n_rnf} RNFs"
    assert "| RF-01.1 | um estado com `pipe \\| dentro` | a ação ocorre | o resultado esperado acontece |" in result
    assert "| RNF-01 | **Qualidade um.** Descrição. | limiar X | como medir |" in result
    assert "RNF-02 (removido)" in result
    assert "    - sub-bullet aninhado" in result, "indentação 2→4 fora de RF/RNF"
    # DT-009: bloco aninhado (tabela/parágrafo) também aprofunda, e tabela colada ganha bloco próprio
    assert "colada no item:\n\n    | Faixa | Ação |" in result, "tabela colada sem linha em branco ou sem aprofundar"
    assert "\n    |---|---|\n    | A | repor |" in result, "linhas da tabela aninhada não aprofundadas"
    assert "\n    Detalhe da regra, aninhado no item." in result, "parágrafo aninhado não aprofundado"
    assert "\n  linha indentada dentro de cerca — não tocar\n" in result, "conteúdo de cerca foi alterado"
    assert result.endswith("\n"), "o \\n final do arquivo foi comido (splitlines em vez de split)"
    assert "- DADO" not in result.split("## 7.")[0].split("## 6.")[1], "cenário sobrou como bullet"
    assert "\n\n## 6." in result and "\n\n## 7." in result and "\n\n## 8." in result, "heading colado na tabela (linha em branco ausente)"
    assert "\n---\n" in result.split("## 7.")[1].split("## 8.")[0], "conteúdo após o último RNF foi perdido"
    print("selftest: OK")


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--selftest":
        selftest()
        sys.exit(0)
    src, dst = sys.argv[1], sys.argv[2]
    result, n_scen, n_rnf = transform(open(src, encoding="utf-8").read())
    open(dst, "w", encoding="utf-8").write(result)
    print(f"{src}: {n_scen} cenários e {n_rnf} RNFs tabelados -> {dst}")
