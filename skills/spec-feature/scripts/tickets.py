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
  diff      compara o tickets.md com o estado coletado do Jira (`acli jira workitem
            search --jql "project=CHAVE AND labels=delta:NNN" --json`, colhido pela
            skill e passado por arquivo) — só propõe, nunca escreve (R3)

Uso: tickets.py gerar DELTA_DIR
     tickets.py exportar DELTA_DIR [--saida DIR]
     tickets.py diff DELTA_DIR --externo ESTADO.json
     tickets.py --selftest
Exit 0 = sem erro (inclui degradação RNF2) · 1 = tasks.md inválido ou diff achou
divergência · 2 = erro de uso.
"""
import argparse
import json
import re
import sys
from pathlib import Path

from itens import itens, ITEM  # dono do formato de item (delta-033) — mesmo parser do check_cycle.py (C9)

try:
    import yaml  # única dependência externa admitida nos gates (ADR-0023)
except ModuleNotFoundError:
    sys.exit("ERRO: PyYAML ausente — rode 'pip install pyyaml' (ADR-0023)")

# Import do módulo comum de projeção — skill irmã do mesmo plugin. O layout
# skills/<nome>/scripts/ é estável tanto no repo quanto no cache do plugin instalado,
# por isso o caminho é relativo ao próprio arquivo, nunca absoluto de máquina.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "handoff" / "scripts"))
from projecao import emitir_sh_acli, nome_var  # noqa: E402 — import após o path-fix acima, ordem exigida

TRACO = "—"
STATUS_ABERTO = "aberto"
STATUS_CONCLUIDO = "concluído"

# Item ('- [ ] T1 ...', checkbox/id/continuação) vem de itens.py — dono único do formato
# (R2, delta-033). Daqui pra frente são duas checagens, não uma:
# 1) PADRAO_CABECA valida a CABEÇA de forma ancorada sobre item["resto"] (o que vem
#    logo após o ID, só a primeira linha) — "(dep: Tn)" opcional seguido de " — ".
#    Ancorada de propósito: sem isso, "T1 lixo aqui — ação..." (lixo antes do "—") ou
#    "T1 sem formato" com os campos jogados numa continuação passavam batido, porque o
#    PADRAO_CORPO_TASK abaixo é `search`, não `match` (achado do review pós-Task 3). O
#    grupo capturado é a própria aresta `dep:` — nunca lida de item["texto"] (texto
#    acumulado), onde "(dep: Tn)" citado na prosa de uma continuação não pode virar
#    aresta (mesma regra do C9/R40 em check_cycle.py).
# 2) PADRAO_CORPO_TASK busca os campos ("ação · arquivos: X · cobre: Rn · verificação:
#    cmd") de forma tolerante sobre item["texto"] — é aqui que mora a tolerância a
#    task quebrada em duas linhas.
PADRAO_CABECA = re.compile(r"^(?:\(dep:\s*([^)]*)\))?\s*— ")
PADRAO_CORPO_TASK = re.compile(r"— (.+?) · arquivos: .+? · cobre: .+? · verificação: .+$")
LINHA_EPICO = re.compile(r"^Épico: \[delta-(\d+)\] (.+?) · Externo: (.+)$", re.M)
# LINHA_TICKET casa (tid, externo) — consumidor: parse_tickets_md (idempotência de
# gerar/exportar). LINHA_TICKET_DIFF casa (tid, status, externo) — consumidor:
# parse_tickets_diff (o `diff`, R3, também compara o status contra o Jira). Duplicação
# deliberada em vez de mudar o grupo do LINHA_TICKET e quebrar quem já desempacota
# (tid, externo) — regra de ouro do CLAUDE.md: **mudou o formato da linha do ticket em
# um dos dois regexes (campos, ordem, separador `·`), mude no outro também.**
LINHA_TICKET = re.compile(r"^- (T\d+) — .+? · status: .+? · deps: .+? · Externo: (.+)$", re.M)
LINHA_TICKET_DIFF = re.compile(r"^- (T\d+) — .+? · status: (.+?) · deps: .+? · Externo: (.+)$", re.M)
ESTADO_ARQUIVADA = re.compile(r"^Estado:\s*arquivada", re.M)

# Categoria "fechado" por nome de status do Jira — vocabulário fechado, mas
# extensível: workflow customizado do projeto pode acrescentar nomes aqui.
CONCLUIDOS = {"Done", "Concluído", "Concluída"}


def die(msg: str) -> None:
    print(f"ERRO: {msg}")
    sys.exit(2)


# ---------------------------------------------------------------- funções puras


LINHA_CHECKBOX = re.compile(r"^\s*-\s*\[[ xX]\]")


def parse_tasks(texto: str) -> list:
    """Tasks do tasks.md via itens.py (R2) — cabeça ancorada + campos tolerantes a
    multi-linha; item malformado em qualquer uma das duas nomeia a linha e vira ValueError.

    Checagem extra antes de chamar itens.py: itens() filtra por prefixo ("T"), então uma
    linha `- [ ] ...` sem ID Tn/CTn nunca vira item — sumiria da projeção em silêncio (sozinha)
    ou seria absorvida como continuação da task anterior. Rejeita as duas pela mesma âncora
    (ITEM, de itens.py) antes que isso aconteça.
    """
    for n, linha in enumerate(texto.splitlines(), 1):
        if LINHA_CHECKBOX.match(linha) and not ITEM.match(linha):
            raise ValueError(f"linha {n}: task malformada — {linha!r}")
    tarefas = []
    for item in itens(texto, "T"):
        cabeca = PADRAO_CABECA.match(item["resto"])
        corpo = PADRAO_CORPO_TASK.search(item["texto"])
        if not cabeca or not corpo:
            raise ValueError(f"linha {item['linha']}: task malformada — {item['texto']!r}")
        dep_str = cabeca.group(1)
        tarefas.append({
            "id": item["id"],
            "feito": item["feito"],
            "deps": [d.strip() for d in dep_str.split(",")] if dep_str else [],
            "acao": corpo.group(1).strip(),
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


def parse_tickets_diff(texto: str) -> tuple:
    """Épico e tickets com status+Externo — o que o `diff` precisa comparar contra o Jira."""
    m = LINHA_EPICO.search(texto)
    epico = {"externo": m.group(3).strip() if m and m.group(3).strip() != TRACO else None}
    tickets = [
        {"id": tid, "status": status.strip(), "externo": ext.strip() if ext.strip() != TRACO else None}
        for tid, status, ext in LINHA_TICKET_DIFF.findall(texto)
    ]
    return epico, tickets


def fechado(status_jira: str) -> bool:
    """Categoria 'fechado' por nome de status — ver CONCLUIDOS (extensível por projeto)."""
    return status_jira in CONCLUIDOS


def delta_arquivada(delta_dir: Path) -> bool:
    """Arquivada quando o diretório está sob specs/_archive/ ou o spec.md declara Estado: arquivada."""
    if "_archive" in delta_dir.parts:
        return True
    spec = delta_dir / "spec.md"
    return spec.is_file() and bool(ESTADO_ARQUIVADA.search(spec.read_text(encoding="utf-8")))


def comparar(epico: dict, tickets: list, externos: dict, arquivada: bool) -> list:
    """Diff tickets.md × Jira — função pura, sem I/O (R3).

    epico: {"externo": chave|None}. tickets: [{"id", "status", "externo"}, ...] — status é
    "aberto"/"concluído" (STATUS_ABERTO/STATUS_CONCLUIDO). externos: {chave: nome do status
    no Jira}, já normalizado. arquivada: delta_dir arquivada (ver `delta_arquivada`).

    Cobertura: issue fechada com task aberta; task concluída com issue aberta; issue
    órfã (chave no Jira sem linha correspondente); ticket sem issue (Externo vazio ou
    chave ausente do JSON); épico aberto com delta arquivada. Só reporta — a atualização
    do tickets.md/tasks.md é proposta e aplicada por quem revisa (R3).
    """
    linhas = []
    chaves_conhecidas = {t["externo"] for t in tickets if t["externo"]}
    if epico["externo"]:
        chaves_conhecidas.add(epico["externo"])

    for t in tickets:
        if not t["externo"]:
            linhas.append({
                "tickets_diz": f"{t['id']} — sem Externo",
                "jira_diz": TRACO,
                "impacto": "ticket sem issue correspondente no Jira",
                "acao": "exportar com `tickets.py exportar` para abrir a issue",
            })
            continue
        status_jira = externos.get(t["externo"])
        if status_jira is None:
            linhas.append({
                "tickets_diz": f"{t['id']} — Externo: {t['externo']}",
                "jira_diz": f"{t['externo']} não encontrada na busca",
                "impacto": "ticket sem issue correspondente no Jira",
                "acao": "confirmar a chave ou limpar o Externo no tickets.md",
            })
        elif t["status"] == STATUS_CONCLUIDO and not fechado(status_jira):
            linhas.append({
                "tickets_diz": f"{t['id']} — status: concluído",
                "jira_diz": f"{t['externo']} — {status_jira}",
                "impacto": "repo marca pronto, issue segue aberta no Jira",
                "acao": "fechar a issue no Jira ou revisar o status no tasks.md",
            })
        elif t["status"] == STATUS_ABERTO and fechado(status_jira):
            linhas.append({
                "tickets_diz": f"{t['id']} — status: aberto",
                "jira_diz": f"{t['externo']} — {status_jira}",
                "impacto": "issue fechada no Jira, repo ainda marca aberto",
                "acao": "concluir a task no tasks.md ou reabrir a issue",
            })

    for chave, status_jira in sorted(externos.items()):
        if chave not in chaves_conhecidas:
            linhas.append({
                "tickets_diz": f"nenhuma linha — {chave}",
                "jira_diz": f"{chave} — {status_jira}",
                "impacto": "issue com a label da delta sem correspondência no tickets.md",
                "acao": "adicionar o Externo na task correta ou remover a label da delta",
            })

    if arquivada and epico["externo"]:
        status_epico = externos.get(epico["externo"])
        if status_epico is not None and not fechado(status_epico):
            linhas.append({
                "tickets_diz": "épico — delta arquivada",
                "jira_diz": f"{epico['externo']} — {status_epico}",
                "impacto": "delta encerrada com o épico ainda aberto no Jira",
                "acao": "fechar o épico no Jira",
            })
    return linhas


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
    """`acli jira workitem link create --type Blocks` por aresta `dep:` entre as filhas pendentes.

    Extremo criado nesta rodada usa a variável capturada pelo `.sh` (`capturar_chaves=True`
    em `emitir_sh_acli`); extremo já exportado usa a chave literal gravada no tickets.md —
    chave do Jira é sempre `PROJ-NNN` (sem caractere que precise de shlex.quote). Dep sem
    chave conhecida (nem pendente nem exportada — não deveria ocorrer no fluxo normal, mas
    correção pós-review: falha visível, não silêncio) vira aviso de 1 linha no stderr do
    próprio `.sh`, e o link correspondente não é emitido.

    Sintaxe real do acli (achado da validação real, delta-017/T7 — o plano previa
    `link --source/--target`, que não existe): subcomando `link create`, flags `--out`
    (quem bloqueia) / `--in` (quem é bloqueado) e `--yes` para não interromper a
    execução não interativa do `.sh` — confirmado contra o `SBX` (`--out X --in Y
    --type Blocks` grava `X Blocks Y`, i.e. X bloqueia Y).
    """
    ids_pendentes = {t["id"] for t in pendentes}
    linhas = []
    for t in pendentes:
        destino = f'"${nome_var(t["id"])}_KEY"'
        for dep in t["deps"]:
            if dep in ids_pendentes:
                origem = f'"${nome_var(dep)}_KEY"'
            elif externos.get(dep):
                origem = f'"{externos[dep]}"'
            else:
                linhas.append(f'echo "aviso: {dep} sem chave conhecida — link {dep} -> {t["id"]} '
                              'não emitido" >&2')
                continue
            linhas.append(f"acli jira workitem link create --out {origem} --in {destino} "
                          "--type Blocks --yes")
    return linhas


# ---------------------------------------------------------------- I/O


def _aviso_sem_jira(acao: str) -> None:
    print(f"motores.jira ausente ou sem projeto no doc-profile.yaml — {acao} (RNF2).")


class _SemProjeto(Exception):
    """Sinaliza degradação RNF2 (motores.jira ausente/desligado) — o chamador decide o aviso."""


def _carregar_contexto(delta_dir: Path) -> tuple:
    """Contexto comum a `gerar`/`exportar`: projeto, tarefas, NNN/nome da delta e o que já
    foi exportado (épico e filhas), lido do `tickets.md` quando ele existe.

    Levanta `_SemProjeto` na degradação RNF2 e `ValueError` (de `parse_tasks`) quando o
    `tasks.md` tem linha malformada — cada subcomando decide o próprio código de saída.
    """
    root = delta_dir.resolve().parent.parent
    projeto = ler_projeto_jira(root)
    if not projeto:
        raise _SemProjeto
    tarefas = parse_tasks((delta_dir / "tasks.md").read_text(encoding="utf-8"))
    nnn, nome = partir_delta(delta_dir.name)
    caminho = delta_dir / "tickets.md"
    epico_externo, itens_externo = None, {}
    if caminho.is_file():
        existentes = parse_tickets_md(caminho.read_text(encoding="utf-8"))
        epico_externo, itens_externo = existentes["epico"], existentes["itens"]
    return projeto, tarefas, nnn, nome, epico_externo, itens_externo


def cmd_gerar(delta_dir: Path) -> int:
    try:
        projeto, tarefas, nnn, nome, epico_externo, itens_externo = _carregar_contexto(delta_dir)
    except _SemProjeto:
        _aviso_sem_jira("tickets.md não gerado")
        return 0
    except ValueError as e:
        print(f"ERRO: {e}")
        return 1
    caminho = delta_dir / "tickets.md"
    texto = montar_tickets_md(delta_dir.name, projeto, nnn, nome, tarefas, epico_externo, itens_externo)
    caminho.write_text(texto, encoding="utf-8")
    print(f"tickets.md gerado em {caminho} · {len(tarefas)} task(s)")
    return 0


def cmd_exportar(delta_dir: Path, saida: Path) -> int:
    try:
        projeto, tarefas, nnn, nome, epico_externo, externos = _carregar_contexto(delta_dir)
    except _SemProjeto:
        _aviso_sem_jira("ida ao Jira não emitida")
        return 0
    except ValueError as e:
        print(f"ERRO: {e}")
        return 1
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
        # etiqueta delta:NNN no épico (achado da validação real, T7): sem ela o JQL de
        # diff (labels=delta:NNN) nunca devolve o épico — R3 não alcança o caso "épico
        # aberto com delta arquivada" fora do selftest sintético.
        sh = emitir_sh_acli(itens, projeto, saida, epico=f"[delta-{nnn}] {nome}",
                            epico_labels=[f"delta:{nnn}"], capturar_chaves=True)
    links = montar_links_bloqueio(pendentes, externos)
    if links:
        with sh.open("a", encoding="utf-8") as f:
            f.write("\n" + "\n".join(links) + "\n")
    print(f"{len(tarefas)} task(s) · {len(pendentes)} sem projeção · saída em {saida}")
    return 0


def _normalizar_externos(dados) -> dict:
    """chave -> nome do status, do JSON bruto de `acli jira workitem search --json`.

    Aceita a lista direta ou o envelope `{"issues": [...]}` (dialetos observados do
    acli). Item sem `key` ou sem `fields.status.name` é ignorado — dado incompleto
    não deveria derrubar o diff inteiro.
    """
    itens = dados.get("issues", dados) if isinstance(dados, dict) else dados
    externos = {}
    for item in itens or []:
        chave = item.get("key")
        status = ((item.get("fields") or {}).get("status") or {}).get("name")
        if chave and status:
            externos[chave] = status
    return externos


def cmd_diff(delta_dir: Path, externo: Path) -> int:
    caminho = delta_dir / "tickets.md"
    if not caminho.is_file():
        die(f"tickets.md não encontrado em {delta_dir} — rode 'gerar' primeiro")
    epico, tickets = parse_tickets_diff(caminho.read_text(encoding="utf-8"))
    try:  # fronteira de confiança: o arquivo vem de fora, colhido à mão pela skill
        dados = json.loads(externo.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as erro:
        die(f"não consegui ler {externo}: {erro}")
    linhas = comparar(epico, tickets, _normalizar_externos(dados), delta_arquivada(delta_dir))
    print(f"# Divergências tickets.md × Jira · {len(linhas)} achado(s)\n")
    if not linhas:
        print("Nenhuma divergência: tickets.md e Jira estão em sincronia.")
        return 0
    print("| tickets.md diz | Jira diz | impacto | ação proposta |")
    print("|---|---|---|---|")
    for l in linhas:
        print(f"| {l['tickets_diz']} | {l['jira_diz']} | {l['impacto']} | {l['acao']} |")
    print("\n> Proposta, não aplicação: aprovação humana decide o que muda no "
          "tickets.md/tasks.md (R3).")
    return 1


def main() -> None:
    if "--selftest" in sys.argv[1:]:
        selftest()
        return
    p = argparse.ArgumentParser(description="Projeção do tasks.md de uma delta para o Jira.")
    p.add_argument("comando", choices=("gerar", "exportar", "diff"))
    p.add_argument("delta_dir", help="specs/NNN-nome da delta")
    p.add_argument("--saida", help="diretório dos arquivos de exportação (exportar)")
    p.add_argument("--externo", help="JSON de `acli jira workitem search --json` (diff)")
    a = p.parse_args()
    delta_dir = Path(a.delta_dir).resolve()
    if not (delta_dir / "tasks.md").is_file():
        die(f"tasks.md não encontrado em {delta_dir}")
    if a.comando == "gerar":
        sys.exit(cmd_gerar(delta_dir))
    if a.comando == "diff":
        if not a.externo:
            die("diff exige --externo ESTADO.json (saída de `acli jira workitem search --json`)")
        sys.exit(cmd_diff(delta_dir, Path(a.externo).resolve()))
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

    # checkbox sem ID nenhum (nem Tn nem CTn) não pode sumir em silêncio — itens() filtra
    # por prefixo, então sem esta checagem a linha nunca vira item (achado do review)
    sem_id = "- [ ] ação sem ID\n"
    try:
        parse_tasks(sem_id)
        assert False, "checkbox sem ID devia ser rejeitado"
    except ValueError as e:
        assert "linha 1" in str(e), f"erro não nomeia a linha: {e}"

    # checkbox sem ID logo após uma task válida não pode ser absorvido como continuação
    valida_e_sem_id = (
        "- [ ] T1 — ação · arquivos: a.py · cobre: R1 · verificação: x\n"
        "- [ ] sem id\n"
    )
    try:
        parse_tasks(valida_e_sem_id)
        assert False, "checkbox sem ID após task válida devia ser rejeitado, não absorvido"
    except ValueError as e:
        assert "linha 2" in str(e), f"erro não nomeia a linha: {e}"

    # task multi-linha: (dep: T1) colada ao ID na primeira linha, 'verificação:' na
    # continuação — parse_tasks usa itens.py (R2), tickets.md tem que trazer os dois
    tasks_multi = (
        "- [ ] T1 — cria arquivo X · arquivos: a.py · cobre: R1 · verificação: pytest a\n"
        "- [x] T2 (dep: T1) — ajusta Y · arquivos: b.py\n"
        "      · cobre: R2 · verificação: pytest b\n"
    )
    tarefas_multi = parse_tasks(tasks_multi)
    assert tarefas_multi[1]["deps"] == ["T1"], f"dep na primeira linha não capturada: {tarefas_multi}"
    assert tarefas_multi[1]["acao"] == "ajusta Y", f"ação da task quebrada em duas linhas: {tarefas_multi}"
    texto_multi = montar_tickets_md("999-fixture", "SBX", "999", "fixture", tarefas_multi)
    assert "- T2 — ajusta Y · status: concluído · deps: T1 · Externo: —" in texto_multi, \
        f"tickets.md não trouxe dep+ação da task multi-linha: {texto_multi}"

    # cabeça malformada não pode passar batido só porque os campos aparecem em algum
    # ponto do texto acumulado (regressão pega no review pós-Task 3: search() sem
    # âncora na cabeça aceitava lixo antes do '—' e primeira linha fora de forma)
    cabeca_com_lixo = "- [ ] T1 lixo aqui — ação · arquivos: a.py · cobre: R1 · verificação: x\n"
    try:
        parse_tasks(cabeca_com_lixo)
        assert False, "lixo antes do '—' na cabeça devia ser rejeitado"
    except ValueError as e:
        assert "linha 1" in str(e), f"erro não nomeia a linha: {e}"

    primeira_linha_sem_forma = (
        "- [ ] T1 blah blah sem formato\n"
        "      — ação real · arquivos: a.py · cobre: R1 · verificação: x\n"
    )
    try:
        parse_tasks(primeira_linha_sem_forma)
        assert False, "primeira linha fora de forma não pode ser salva pela continuação"
    except ValueError as e:
        assert "linha 1" in str(e), f"erro não nomeia a linha: {e}"

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
    assert 'link create --out "SBX-9" --in "$T2_KEY" --type Blocks --yes' in sh, \
        "dep já exportada devia virar chave literal"
    assert 'link create --out "SBX-9" --in "$T3_KEY" --type Blocks --yes' in sh, \
        "T3 depende de T1 (já exportada)"
    assert 'link create --out "$T2_KEY" --in "$T3_KEY" --type Blocks --yes' in sh, \
        "T3 depende de T2 (pendente nesta rodada)"
    assert "--label delta:999" in sh, "etiqueta delta:NNN ausente"
    assert "--type Epic --summary '[delta-999] fixture' --label delta:999" in sh, \
        "épico não emitido com o summary e a etiqueta delta:NNN certos (achado T7: sem ela o JQL do diff não o acha)"
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

    # comparar (R3): pura, um caso por linha de cobertura
    def tk(id_, status, ext):
        return {"id": id_, "status": status, "externo": ext}

    epico_ok = {"externo": "SBX-1"}

    # issue fechada no Jira, task ainda aberta no tickets.md
    d = comparar(epico_ok, [tk("T1", STATUS_ABERTO, "SBX-10")],
                 {"SBX-1": "Done", "SBX-10": "Done"}, False)
    assert any("T1" in l["tickets_diz"] and "SBX-10" in l["jira_diz"] for l in d), \
        f"issue fechada com task aberta não acusada: {d}"

    # task concluída no tickets.md, issue ainda aberta no Jira
    d = comparar(epico_ok, [tk("T2", STATUS_CONCLUIDO, "SBX-11")],
                 {"SBX-1": "Done", "SBX-11": "In Progress"}, False)
    assert any("T2" in l["tickets_diz"] and "SBX-11" in l["jira_diz"] for l in d), \
        f"task concluída com issue aberta não acusada: {d}"

    # issue órfã: chave com a label da delta no Jira sem linha correspondente
    d = comparar(epico_ok, [tk("T1", STATUS_ABERTO, None)], {"SBX-1": "Done", "SBX-77": "To Do"}, False)
    assert any("SBX-77" in l["tickets_diz"] and "SBX-77" in l["jira_diz"] for l in d), \
        f"issue órfã não acusada: {d}"

    # ticket sem issue — Externo vazio
    d = comparar(epico_ok, [tk("T3", STATUS_ABERTO, None)], {"SBX-1": "Done"}, False)
    assert any("T3" in l["tickets_diz"] and "sem Externo" in l["tickets_diz"] for l in d), \
        f"Externo vazio não acusado: {d}"

    # ticket sem issue — chave gravada no tickets.md mas ausente do JSON
    d = comparar(epico_ok, [tk("T4", STATUS_ABERTO, "SBX-99")], {"SBX-1": "Done"}, False)
    assert any("T4" in l["tickets_diz"] and "não encontrada" in l["jira_diz"] for l in d), \
        f"chave ausente do JSON não acusada: {d}"

    # épico aberto com delta arquivada — e o caso limpo (não arquivada) não diverge
    d = comparar(epico_ok, [], {"SBX-1": "In Progress"}, True)
    assert any("arquivada" in l["tickets_diz"] and "SBX-1" in l["jira_diz"] for l in d), \
        f"épico aberto com delta arquivada não acusado: {d}"
    assert comparar(epico_ok, [], {"SBX-1": "In Progress"}, False) == [], \
        "épico aberto sem delta arquivada não deveria divergir"

    # tudo sincronizado → zero divergência
    limpo = comparar(epico_ok, [tk("T1", STATUS_CONCLUIDO, "SBX-10")],
                      {"SBX-1": "Done", "SBX-10": "Done"}, True)
    assert limpo == [], f"registro sincronizado não deveria divergir: {limpo}"

    # delta_arquivada: caminho sob specs/_archive/, spec.md com Estado: arquivada, nenhum dos dois
    root_a, delta_a = _montar_delta()
    assert delta_arquivada(delta_a) is False, "delta comum acusada como arquivada"
    arq_dir = root_a / "specs" / "_archive" / "999-fixture"
    arq_dir.mkdir(parents=True)
    assert delta_arquivada(arq_dir) is True, "specs/_archive/ não reconhecido como arquivada"
    (delta_a / "spec.md").write_text("Título\nEstado: arquivada · Data: 2026-01-01\n", encoding="utf-8")
    assert delta_arquivada(delta_a) is True, "spec.md com 'Estado: arquivada' não reconhecido"

    # cmd_diff (I/O): parse real do tickets.md, envelope {"issues": [...]}, tabela impressa,
    # nunca escreve no repo — só imprime
    root_d, delta_d = _montar_delta()
    (delta_d / "tickets.md").write_text(
        "# Tickets — delta-999 · projeto: SBX\n"
        "Épico: [delta-999] fixture · Externo: SBX-1\n"
        "- T1 — cria arquivo X · status: aberto · deps: — · Externo: SBX-10\n"
        "- T2 — ajusta Y · status: concluído · deps: T1 · Externo: SBX-11\n"
        "- T3 — documenta Z · status: aberto · deps: T1, T2 · Externo: —\n",
        encoding="utf-8")
    jira_json = delta_d / "jira.json"
    jira_json.write_text(json.dumps({"issues": [
        {"key": "SBX-1", "fields": {"status": {"name": "In Progress"}}},
        {"key": "SBX-10", "fields": {"status": {"name": "Done"}}},
        {"key": "SBX-11", "fields": {"status": {"name": "In Progress"}}},
        {"key": "SBX-20", "fields": {"status": {"name": "To Do"}}},
    ]}), encoding="utf-8")
    antes = (delta_d / "tickets.md").read_text(encoding="utf-8")
    codigo_diff, saida_diff = quieto(cmd_diff, delta_d, jira_json)
    assert codigo_diff == 1, "diff não sinalizou divergência achada"
    assert "| tickets.md diz | Jira diz | impacto | ação proposta |" in saida_diff
    for esperado in ("T1", "T2", "SBX-20"):
        assert esperado in saida_diff, f"diff não cobriu {esperado}: {saida_diff}"
    assert (delta_d / "tickets.md").read_text(encoding="utf-8") == antes, "diff alterou o tickets.md"

    # lista direta (sem envelope 'issues') também é aceita; sincronizado → limpo, código 0
    (delta_d / "tickets.md").write_text(
        "# Tickets — delta-999 · projeto: SBX\n"
        "Épico: [delta-999] fixture · Externo: SBX-1\n"
        "- T1 — cria arquivo X · status: concluído · deps: — · Externo: SBX-10\n"
        "- T2 — ajusta Y · status: concluído · deps: T1 · Externo: SBX-11\n",
        encoding="utf-8")
    jira_lista = delta_d / "jira_lista.json"
    jira_lista.write_text(json.dumps([
        {"key": "SBX-1", "fields": {"status": {"name": "Done"}}},
        {"key": "SBX-10", "fields": {"status": {"name": "Done"}}},
        {"key": "SBX-11", "fields": {"status": {"name": "Done"}}},
    ]), encoding="utf-8")
    codigo_limpo, saida_limpo = quieto(cmd_diff, delta_d, jira_lista)
    assert codigo_limpo == 0 and "Nenhuma divergência" in saida_limpo, f"diff limpo não sincronizou: {saida_limpo}"

    # JSON ilegível: erro de uso (exit 2), como o resto do script
    try:
        quieto(cmd_diff, delta_d, root_d / "nao-existe.json")
        assert False, "JSON ausente deveria abortar com erro de uso"
    except SystemExit as e:
        assert e.code == 2, f"JSON ausente devia sair com código 2: {e.code}"

    print("selftest tickets: OK (parse âncora, deps/status, degradação RNF2, "
          "exportar idempotente inclusive épico, links Blocks, aviso de dep órfã, "
          "diff Jira→repo cobrindo as 5 divergências do R3)")


if __name__ == "__main__":
    main()
