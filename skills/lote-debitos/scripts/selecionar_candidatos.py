#!/usr/bin/env python3
"""Seleção determinística de candidatos ao lote paralelo de débitos independentes (R2).

Fatia mecânica da skill `lote-debitos`: reaproveita o parser e a fila de
`debito.py` (não os reimplementa — mesmo item, mesma leitura), e aplica só a
exclusão que R2 exige antes do dispatch de subagente:

  - fora de `aberto`/`aceito`/`vigente` (já quitado/descartado — nada a fazer)
  - marcado `trilha` na fila — tem mecanismo próprio (debito.md, seção B),
    nunca entra sozinho; segue elegível se citado explicitamente por `--ids`

Filtro de workspace (ex.: uma chave própria de um cliente no frontmatter) fica a cargo de quem chama
a skill (R2, "Fora de escopo") — este script não conhece essa convenção.

Uso: selecionar_candidatos.py [ROOT] [--ids DT-001,DT-002,...]
     selecionar_candidatos.py --selftest
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "handoff" / "scripts"))
from debito import ESTADOS_ATIVOS, parse_ativos, parse_fila  # noqa: E402 — após o path-fix


def candidatos(root: Path, ids_explicitos: list | None = None) -> tuple[list, list]:
    """(selecionados, avisos) — item elegível por padrão: ativo e não-trilha.

    `ids_explicitos` restringe ao subconjunto pedido e libera itens `trilha`
    (pedido nomeado é decisão de quem chama, não seleção automática) — mas
    nunca libera item fora de `aberto`/`aceito`/`vigente`.
    """
    itens, erros = parse_ativos(root)
    avisos = [f"ignorado (malformado): {e}" for e in erros]
    por_id = {item["id"]: item for item in itens}

    if ids_explicitos:
        selecionados = []
        for ident in ids_explicitos:
            item = por_id.get(ident)
            if item is None:
                avisos.append(f"{ident}: não encontrado em debts/ativos/")
            elif item["status"] not in ESTADOS_ATIVOS:
                avisos.append(f"{ident}: estado '{item['status']}' não é ativo — fora do lote")
            else:
                selecionados.append(item)
        return selecionados, avisos

    selecionados = []
    for item in itens:
        if item["status"] not in ESTADOS_ATIVOS:
            continue
        _, _, _, trilha, _ = parse_fila(item.get("fila", "")) or (0, 0, 0, False, None)
        if trilha:
            avisos.append(f"{item['id']}: marcado trilha — não entra sozinho no lote")
            continue
        selecionados.append(item)
    return selecionados, avisos


CONCORRENCIA_DEFAULT = 3  # RNF2: teto conservador — I/O de N worktrees em máquina fraca


def levas(itens: list, n: int = CONCORRENCIA_DEFAULT) -> list:
    """Fatia `itens` em lotes de até `n` — RNF2: no máximo N worktrees simultâneas.

    Pura e determinística: quem dispara a próxima leva é a skill, só depois que
    a leva corrente terminar (nunca dispara a leva N+1 antes da N liberar).
    """
    if n < 1:
        raise ValueError("concorrência precisa ser >= 1")
    return [itens[i:i + n] for i in range(0, len(itens), n)]


def main() -> None:
    if "--selftest" in sys.argv[1:]:
        selftest()
        return
    args = [a for a in sys.argv[1:] if not a.startswith(("--ids", "--concorrencia"))]
    ids_arg = next((a for a in sys.argv[1:] if a.startswith("--ids")), None)
    ids_explicitos = ids_arg.split("=", 1)[1].split(",") if ids_arg and "=" in ids_arg else None
    conc_arg = next((a for a in sys.argv[1:] if a.startswith("--concorrencia")), None)
    n = int(conc_arg.split("=", 1)[1]) if conc_arg and "=" in conc_arg else CONCORRENCIA_DEFAULT
    root = Path(args[0]).resolve() if args else Path(".").resolve()
    sel, avisos = candidatos(root, ids_explicitos)
    for a in avisos:
        print(f"[aviso] {a}", file=sys.stderr)
    for i, leva in enumerate(levas(sel, n), 1):
        print(f"-- leva {i} ({len(leva)}/{n}) --")
        for item in leva:
            print(f"{item['id']}\t{item['título']}")
    print(f"{len(sel)} candidato(s) em {len(levas(sel, n))} leva(s) de até {n}", file=sys.stderr)


def selftest() -> None:
    import tempfile

    def repo(itens):
        d = Path(tempfile.mkdtemp())
        pasta = d / "debts/ativos"
        pasta.mkdir(parents=True)
        for ident, status, fila, titulo in itens:
            (pasta / f"DEBT_{ident}-caso.md").write_text(
                f"---\nid: {ident}\nnatureza: débito\nestado: {status}\nfila: {fila}\n"
                f"descricao: {titulo}\naberto: 2026-01-01\n---\n\n"
                f"# [{ident}] - {titulo}\n\nProsa.\n\n"
                f"- **Local:** [x](x.py)\n- **Gatilho:** sempre\n- **Origem:** manual\n",
                encoding="utf-8")
        return d

    # seleção padrão: ativo e não-trilha entram; quitado e trilha ficam de fora
    r = repo([
        ("DT-001", "aberto", "P3·J9·Pr9", "Candidato normal"),
        ("DT-002", "vigente", "P1·J3·Pr9 · trilha", "Trilha planejada"),
        ("DT-003", "quitado", "P3·J9·Pr9", "Já resolvido"),
        ("DT-004", "aceito", "P1·J1·Pr1", "Aceito, ativo"),
    ])
    sel, avisos = candidatos(r)
    ids = {i["id"] for i in sel}
    assert ids == {"DT-001", "DT-004"}, f"seleção padrão errada: {ids}"
    assert any("DT-002" in a and "trilha" in a for a in avisos), f"trilha sem aviso: {avisos}"

    # --ids explícito libera trilha, mas nunca item não-ativo
    sel2, avisos2 = candidatos(r, ids_explicitos=["DT-002", "DT-003", "DT-999"])
    ids2 = {i["id"] for i in sel2}
    assert ids2 == {"DT-002"}, f"--ids devia liberar trilha e recusar quitado/inexistente: {ids2}"
    assert any("DT-003" in a for a in avisos2) and any("DT-999" in a for a in avisos2), \
        f"avisos de --ids incompletos: {avisos2}"

    # levas: N por vez, resto na última, N inválido recusa
    assert levas([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]], "levas não fatiou certo"
    assert levas([], 3) == [], "lista vazia devia dar zero levas"
    assert levas([1], 3) == [[1]], "1 item cabe numa leva só, sem leva vazia sobrando"
    try:
        levas([1], 0)
        raise AssertionError("concorrência 0 devia recusar")
    except ValueError:
        pass

    print("selftest selecionar_candidatos: OK (padrão exclui trilha/inativo, --ids libera trilha "
          "mas não estado final, levas por concorrência)")


if __name__ == "__main__":
    main()
