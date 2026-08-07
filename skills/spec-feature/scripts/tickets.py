#!/usr/bin/env python3
"""Projeção do tasks.md de uma delta para o Jira — tickets.md + ida via acli (R1, delta-017).

tickets.md nasce a partir do tasks.md (1 épico `[delta-NNN] nome` + 1 ticket por task,
arestas `dep:` viram links de bloqueio) quando o `doc-profile.yaml` declara
`motores.jira.projeto`; sem ele, a projeção se omite com 1 linha de aviso (RNF2) — o
tasks.md segue valendo sozinho. Este script **não acessa a rede**: só emite arquivos;
quem executa o `.sh` é a skill (mesmo contrato do R52/debito.py).

  gerar     lê tasks.md, escreve tickets.md (preserva Externo já gravado)
  exportar  emite o .sh de creates unitários (acli) + links de bloqueio; item com
            Externo preenchido no tickets.md é pulado — idempotência

Uso: tickets.py gerar DELTA_DIR
     tickets.py exportar DELTA_DIR [--saida DIR]
     tickets.py --selftest
Exit 0 = sem erro (inclui degradação RNF2) · 1 = tasks.md inválido · 2 = erro de uso.
"""
import argparse
import re
import sys
from pathlib import Path

try:
    import yaml  # única dependência externa admitida nos gates (ADR-0023)
except ModuleNotFoundError:
    sys.exit("ERRO: PyYAML ausente — rode 'pip install pyyaml' (ADR-0023)")

# Import do módulo comum de projeção — skill irmã do mesmo plugin. O layout
# skills/<nome>/scripts/ é estável tanto no repo quanto no cache do plugin instalado,
# por isso o caminho é relativo ao próprio arquivo, nunca absoluto de máquina.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "handoff" / "scripts"))
from projecao import emitir_sh_acli  # noqa: E402 — import após o path-fix acima, ordem exigida

TRACO = "—"
STATUS_ABERTO = "aberto"
STATUS_CONCLUIDO = "concluído"

# Âncora de início de linha (regra do R51 — nunca busca de texto). Formato do tasks.md
# gerado pelo template: "- [ ] T1 — ação · arquivos: X · cobre: Rn · verificação: cmd".
PADRAO_TASK = re.compile(
    r"^- \[([ x])\] (T\d+)(?: \(dep: ([^)]+)\))? — (.+?) · arquivos: .+? · cobre: .+? · verificação: .+$"
)
LINHA_EPICO = re.compile(r"^Épico: \[delta-(\d+)\] (.+?) · Externo: (.+)$", re.M)
LINHA_TICKET = re.compile(r"^- (T\d+) — .+? · status: .+? · deps: .+? · Externo: (.+)$", re.M)


def die(msg: str) -> None:
    print(f"ERRO: {msg}")
    sys.exit(2)


# ---------------------------------------------------------------- funções puras


def parse_tasks(texto: str) -> list:
    """Tasks do tasks.md por âncora — linha malformada nomeia o número e vira ValueError."""
    tarefas = []
    for n, linha_txt in enumerate(texto.splitlines(), 1):
        if not linha_txt.startswith("- ["):
            continue  # comentário/cabeçalho: não é linha de task
        m = PADRAO_TASK.match(linha_txt)
        if not m:
            raise ValueError(f"linha {n}: task malformada — {linha_txt!r}")
        feito, tid, deps, acao = m.groups()
        tarefas.append({
            "id": tid,
            "feito": feito == "x",
            "deps": [d.strip() for d in deps.split(",")] if deps else [],
            "acao": acao.strip(),
        })
    return tarefas


def ler_projeto_jira(root: Path) -> str | None:
    """`motores.jira.projeto` do doc-profile.yaml; ausente ou desligado → None (RNF2)."""
    perfil = root / "doc-profile.yaml"
    if not perfil.is_file():
        return None
    dados = yaml.safe_load(perfil.read_text(encoding="utf-8")) or {}
    jira = (dados.get("motores") or {}).get("jira")
    if not isinstance(jira, dict):
        return None
    projeto = jira.get("projeto")
    return projeto if projeto else None


def partir_delta(dirname: str) -> tuple:
    """NNN e nome a partir do diretório da delta: '017-jira-tickets' → ('017', 'jira-tickets')."""
    nnn, _, nome = dirname.partition("-")
    return nnn, nome


def parse_tickets_md(texto: str) -> dict:
    """Externo do épico e das filhas já gravados — é o que garante idempotência."""
    m = LINHA_EPICO.search(texto)
    epico_externo = None
    if m and m.group(3).strip() != TRACO:
        epico_externo = m.group(3).strip()
    itens_externo = {tid: ext.strip() for tid, ext in LINHA_TICKET.findall(texto)
                     if ext.strip() != TRACO}
    return {"epico": epico_externo, "itens": itens_externo}


def montar_tickets_md(dirname: str, projeto: str, nnn: str, nome: str, tarefas: list,
                       epico_externo: str | None = None, itens_externo: dict | None = None) -> str:
    """Markdown do tickets.md — parseável por `parse_tickets_md` (âncoras, não busca)."""
    itens_externo = itens_externo or {}
    linhas = [f"# Tickets — delta-{dirname} · projeto: {projeto}",
              f"Épico: [delta-{nnn}] {nome} · Externo: {epico_externo or TRACO}"]
    for t in tarefas:
        status = STATUS_CONCLUIDO if t["feito"] else STATUS_ABERTO
        deps = ", ".join(t["deps"]) if t["deps"] else TRACO
        externo = itens_externo.get(t["id"]) or TRACO
        linhas.append(f"- {t['id']} — {t['acao']} · status: {status} · deps: {deps} · Externo: {externo}")
    return "\n".join(linhas) + "\n"


def corpo_ticket_tarefa(t: dict, nnn: str, nome: str) -> str:
    """Markdown do corpo do ticket — a fonte é o tasks.md, o ticket é vitrine (ADR-0021)."""
    deps = ", ".join(t["deps"]) if t["deps"] else TRACO
    return (
        f"{t['acao']}\n\n"
        f"- **Delta:** delta-{nnn} ({nome})\n"
        f"- **Task:** {t['id']}\n"
        f"- **Depende de:** {deps}\n\n---\n"
        f"_Projeção de **{t['id']}** do `tasks.md`. A fonte da verdade é o arquivo versionado; "
        f"este ticket é espelho para gestão (ADR-0021)._"
    )


def montar_links_bloqueio(pendentes: list, externos: dict) -> list:
    """`acli jira workitem link --type Blocks` por aresta `dep:` entre as filhas pendentes.

    Extremo criado nesta rodada usa a variável capturada pelo `.sh` (`capturar_chaves=True`
    em `emitir_sh_acli`); extremo já exportado usa a chave literal gravada no tickets.md —
    chave do Jira é sempre `PROJ-NNN` (sem caractere que precise de shlex.quote). Dep sem
    chave conhecida (nem pendente nem exportada — não deveria ocorrer no fluxo normal, mas
    correção pós-review: falha visível, não silêncio) vira aviso de 1 linha no stderr do
    próprio `.sh`, e o link correspondente não é emitido.
    """
    ids_pendentes = {t["id"] for t in pendentes}
    linhas = []
    for t in pendentes:
        destino = f'"${t["id"]}_KEY"'
        for dep in t["deps"]:
            if dep in ids_pendentes:
                origem = f'"${dep}_KEY"'
            elif externos.get(dep):
                origem = f'"{externos[dep]}"'
            else:
                linhas.append(f'echo "aviso: {dep} sem chave conhecida — link {dep} -> {t["id"]} '
                              'não emitido" >&2')
                continue
            linhas.append(f"acli jira workitem link --source {origem} --target {destino} --type Blocks")
    return linhas


# ---------------------------------------------------------------- I/O


def _aviso_sem_jira(acao: str) -> None:
    print(f"motores.jira ausente ou sem projeto no doc-profile.yaml — {acao} (RNF2).")


def cmd_gerar(delta_dir: Path) -> int:
    root = delta_dir.resolve().parent.parent
    projeto = ler_projeto_jira(root)
    if not projeto:
        _aviso_sem_jira("tickets.md não gerado")
        return 0
    try:
        tarefas = parse_tasks((delta_dir / "tasks.md").read_text(encoding="utf-8"))
    except ValueError as e:
        print(f"ERRO: {e}")
        return 1
    nnn, nome = partir_delta(delta_dir.name)
    caminho = delta_dir / "tickets.md"
    epico_externo, itens_externo = None, {}
    if caminho.is_file():
        existentes = parse_tickets_md(caminho.read_text(encoding="utf-8"))
        epico_externo, itens_externo = existentes["epico"], existentes["itens"]
    texto = montar_tickets_md(delta_dir.name, projeto, nnn, nome, tarefas, epico_externo, itens_externo)
    caminho.write_text(texto, encoding="utf-8")
    print(f"tickets.md gerado em {caminho} · {len(tarefas)} task(s)")
    return 0


def cmd_exportar(delta_dir: Path, saida: Path) -> int:
    root = delta_dir.resolve().parent.parent
    projeto = ler_projeto_jira(root)
    if not projeto:
        _aviso_sem_jira("ida ao Jira não emitida")
        return 0
    try:
        tarefas = parse_tasks((delta_dir / "tasks.md").read_text(encoding="utf-8"))
    except ValueError as e:
        print(f"ERRO: {e}")
        return 1
    nnn, nome = partir_delta(delta_dir.name)
    caminho_tickets = delta_dir / "tickets.md"
    epico_externo, externos = None, {}
    if caminho_tickets.is_file():
        existentes = parse_tickets_md(caminho_tickets.read_text(encoding="utf-8"))
        epico_externo, externos = existentes["epico"], existentes["itens"]
    pendentes = [t for t in tarefas if t["id"] not in externos]
    itens = [{"id": t["id"], "title": f"{t['id']} — {t['acao']}",
              "body": corpo_ticket_tarefa(t, nnn, nome), "labels": [f"delta:{nnn}"]}
             for t in pendentes]
    saida.mkdir(parents=True, exist_ok=True)
    # Épico idempotente (R1: Externo é o que garante idempotência, épico incluso): já
    # tem chave gravada no tickets.md → reaproveita literal, nunca recria no Jira.
    if epico_externo:
        sh = emitir_sh_acli(itens, projeto, saida, epico_existente=epico_externo, capturar_chaves=True)
    else:
        sh = emitir_sh_acli(itens, projeto, saida, epico=f"[delta-{nnn}] {nome}", capturar_chaves=True)
    links = montar_links_bloqueio(pendentes, externos)
    if links:
        with sh.open("a", encoding="utf-8") as f:
            f.write("\n" + "\n".join(links) + "\n")
    print(f"{len(tarefas)} task(s) · {len(pendentes)} sem projeção · saída em {saida}")
    return 0


def main() -> None:
    if "--selftest" in sys.argv[1:]:
        selftest()
        return
    p = argparse.ArgumentParser(description="Projeção do tasks.md de uma delta para o Jira.")
    p.add_argument("comando", choices=("gerar", "exportar"))
    p.add_argument("delta_dir", help="specs/NNN-nome da delta")
    p.add_argument("--saida", help="diretório dos arquivos de exportação (exportar)")
    a = p.parse_args()
    delta_dir = Path(a.delta_dir).resolve()
    if not (delta_dir / "tasks.md").is_file():
        die(f"tasks.md não encontrado em {delta_dir}")
    if a.comando == "gerar":
        sys.exit(cmd_gerar(delta_dir))
    saida = Path(a.saida).resolve() if a.saida else delta_dir / "tickets-out"
    sys.exit(cmd_exportar(delta_dir, saida))


# ---------------------------------------------------------------- selftest


TASKS_FIXTURE = (
    "# Tasks — delta-999\n"
    "<!-- comentário que não é task -->\n"
    "- [ ] T1 — cria arquivo X · arquivos: a.py · cobre: R1 · verificação: pytest a\n"
    "- [x] T2 (dep: T1) — ajusta Y · arquivos: b.py · cobre: R2 · verificação: pytest b\n"
    "- [ ] T3 (dep: T1, T2) — documenta Z · arquivos: c.md · cobre: R1 · verificação: lint c\n"
)


def _montar_delta(tasks_texto=TASKS_FIXTURE, com_jira=True, projeto="SBX"):
    import tempfile
    root = Path(tempfile.mkdtemp())
    if com_jira:
        (root / "doc-profile.yaml").write_text(
            f"motores:\n  jira:\n    projeto: {projeto}\n", encoding="utf-8")
    else:
        (root / "doc-profile.yaml").write_text("motores:\n  jira: false\n", encoding="utf-8")
    delta_dir = root / "specs" / "999-fixture"
    delta_dir.mkdir(parents=True)
    (delta_dir / "tasks.md").write_text(tasks_texto, encoding="utf-8")
    return root, delta_dir


def selftest() -> None:
    import contextlib
    import io

    def quieto(fn, *args, **kwargs):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            r = fn(*args, **kwargs)
        return r, buf.getvalue()

    # parse_tasks: âncora, deps, feito — função pura, sem I/O
    tarefas = parse_tasks(TASKS_FIXTURE)
    assert [t["id"] for t in tarefas] == ["T1", "T2", "T3"], f"parser perdeu/reordenou task: {tarefas}"
    assert tarefas[0]["feito"] is False and tarefas[1]["feito"] is True, "flag 'feito' errada"
    assert tarefas[0]["deps"] == [] and tarefas[1]["deps"] == ["T1"] and tarefas[2]["deps"] == ["T1", "T2"]

    # linha malformada nomeia a linha e vira erro
    ruim = TASKS_FIXTURE + "- [ ] T4 sem separador certo\n"
    try:
        parse_tasks(ruim)
        assert False, "task malformada não foi rejeitada"
    except ValueError as e:
        assert "linha 6" in str(e), f"erro não nomeia a linha: {e}"

    # ler_projeto_jira: presente, desligado, ausente
    root, delta_dir = _montar_delta()
    assert ler_projeto_jira(root) == "SBX"
    root_off, delta_off = _montar_delta(com_jira=False)
    assert ler_projeto_jira(root_off) is None
    root_sem = _montar_delta()[0]
    (root_sem / "doc-profile.yaml").unlink()
    assert ler_projeto_jira(root_sem) is None

    # gerar: status e deps corretos no tickets.md
    codigo, _ = quieto(cmd_gerar, delta_dir)
    assert codigo == 0
    texto_tickets = (delta_dir / "tickets.md").read_text(encoding="utf-8")
    assert "Épico: [delta-999] fixture · Externo: —" in texto_tickets
    assert "- T1 — cria arquivo X · status: aberto · deps: — · Externo: —" in texto_tickets
    assert "- T2 — ajusta Y · status: concluído · deps: T1 · Externo: —" in texto_tickets
    assert "- T3 — documenta Z · status: aberto · deps: T1, T2 · Externo: —" in texto_tickets

    # gerar sem motores.jira: aviso de 1 linha, código 0 (RNF2) — tasks.md segue valendo sozinho
    codigo_off, saida_off = quieto(cmd_gerar, delta_off)
    assert codigo_off == 0 and not (delta_off / "tickets.md").exists()
    assert len(saida_off.strip().splitlines()) == 1, f"aviso não é 1 linha: {saida_off!r}"

    # exportar: T1 já tem Externo (pulado); T2/T3 pendentes; deps viram Blocks
    (delta_dir / "tickets.md").write_text(
        texto_tickets.replace(
            "- T1 — cria arquivo X · status: aberto · deps: — · Externo: —",
            "- T1 — cria arquivo X · status: aberto · deps: — · Externo: SBX-9"),
        encoding="utf-8")
    saida_dir = delta_dir / "out"
    codigo_exp, _ = quieto(cmd_exportar, delta_dir, saida_dir)
    assert codigo_exp == 0
    sh = (saida_dir / "tickets-acli.sh").read_text(encoding="utf-8")
    assert "T1_KEY" not in sh, "task já exportada (Externo preenchido) voltou ao .sh"
    assert sh.count("--type Task") == 2, "deveria criar só T2 e T3 (T1 já tem Externo)"
    assert "T2_KEY=$(acli jira workitem create" in sh and "T3_KEY=$(acli jira workitem create" in sh
    assert '--source "SBX-9" --target "$T2_KEY" --type Blocks' in sh, "dep já exportada devia virar chave literal"
    assert '--source "SBX-9" --target "$T3_KEY" --type Blocks' in sh, "T3 depende de T1 (já exportada)"
    assert '--source "$T2_KEY" --target "$T3_KEY" --type Blocks' in sh, "T3 depende de T2 (pendente nesta rodada)"
    assert "--label delta:999" in sh, "etiqueta delta:NNN ausente"
    assert "--type Epic --summary '[delta-999] fixture'" in sh, "épico não emitido com o summary certo"
    assert (saida_dir / "corpo-T2.md").read_text(encoding="utf-8") == corpo_ticket_tarefa(
        tarefas[1], "999", "fixture"), "corpo do ticket não bateu com o canônico"

    # épico com Externo preenchido: exportar reaproveita, não recria (correção pós-review —
    # R1 diz que Externo garante idempotência, e isso vale para o épico também)
    texto_com_epico = texto_tickets.replace(
        "Épico: [delta-999] fixture · Externo: —", "Épico: [delta-999] fixture · Externo: SBX-1"
    ).replace(
        "- T1 — cria arquivo X · status: aberto · deps: — · Externo: —",
        "- T1 — cria arquivo X · status: aberto · deps: — · Externo: SBX-9")
    (delta_dir / "tickets.md").write_text(texto_com_epico, encoding="utf-8")
    saida_dir2 = delta_dir / "out2"
    codigo_exp2, _ = quieto(cmd_exportar, delta_dir, saida_dir2)
    assert codigo_exp2 == 0
    sh2 = (saida_dir2 / "tickets-acli.sh").read_text(encoding="utf-8")
    assert "--type Epic" not in sh2, "épico com Externo preenchido não deveria ser recriado"
    assert "EPICO=SBX-1" in sh2, "épico existente deveria virar EPICO=<chave> literal"
    assert '--parent "$EPICO"' in sh2, "filhas seguem usando --parent mesmo com épico reaproveitado"

    # link sem chave conhecida em nenhum dos lados: aviso de 1 linha no stderr do .sh,
    # não silêncio (correção pós-review) — e o link correspondente não é emitido
    orfa = [{"id": "T9", "deps": ["T0"], "feito": False, "acao": "orfã"}]
    linhas_aviso = montar_links_bloqueio(orfa, {})
    assert any("aviso:" in l and ">&2" in l for l in linhas_aviso), "dep sem chave devia virar aviso, não silêncio"
    assert not any("workitem link" in l for l in linhas_aviso), "link não deveria ser emitido sem chave conhecida"

    # exportar sem motores.jira: mesma degradação de gerar (RNF2)
    saida_off2 = delta_off / "out"
    codigo_exp_off, saida_exp_off = quieto(cmd_exportar, delta_off, saida_off2)
    assert codigo_exp_off == 0 and not saida_off2.exists()
    assert len(saida_exp_off.strip().splitlines()) == 1

    print("selftest tickets: OK (parse âncora, deps/status, degradação RNF2, "
          "exportar idempotente inclusive épico, links Blocks, aviso de dep órfã)")


if __name__ == "__main__":
    main()
