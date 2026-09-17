#!/usr/bin/env python3
"""Painel de abertura de sessão de um projeto: o estado real de cada delta, derivado do git.

  sessao.py <projeto> [foco]      painel do projeto declarado em ~/.claude/sessoes/<projeto>.toml
  sessao.py <projeto> --semear    YAML da fila a partir das deltas ativas, no stdout
  sessao.py --selftest            valida os módulos puros da skill

O projeto é sempre explícito: sem ele a skill pergunta, nunca adivinha pelo diretório corrente.
Esquema e validação da config: `config.py`. Regras de estado, ordem, foco e bancada: `fila.py`.
Coleta: `evidencia.py`. Este arquivo é cola — orquestra e carimba, não decide.

O carimbo da última sessão e do foco é POR PROJETO, em $XDG_STATE_HOME/inicio-de-sessao/:
dois projetos têm ritmos diferentes, e um carimbo comum faria a abertura de um mentir sobre
a janela do outro.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import time
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

import config as cfgmod  # noqa: E402
import contexto as ctx  # noqa: E402
import nota as notamod  # noqa: E402
import evidencia as ev  # noqa: E402
import fila as nucleo  # noqa: E402

DIR_ESTADO = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state")) / "inicio-de-sessao"
# Registros de sessão do harness: mesma casa da config, nunca um caminho pessoal cravado.
DIR_SESSOES = Path(os.environ.get("CLAUDE_CONFIG_DIR") or (Path.home() / ".claude")) / "projects"


def carimbos(projeto):
    return DIR_ESTADO / f"ultima-sessao-{projeto}", DIR_ESTADO / f"foco-{projeto}"


def ler(caminho):
    return caminho.read_text(encoding="utf-8") if caminho.is_file() else ""


def pasta_da_delta(it, info):
    if it.get("spec"):
        return Path(str(it["spec"])).parent.name
    return next((n for n in info[it["repo"]]["ativas"] if n[:3] == it["nnn"]), "")


def painel(cfg, args):
    comeco = time.monotonic()
    # A auditoria de higiene é a parte mais cara: sobe agora e é colhida no fim, escondida
    # atrás do fetch e das chamadas de rede que viriam de qualquer jeito.
    varredura, erro_varredura = ev.higiene_em_curso(cfg["higiene"])
    carimbo_data, carimbo_foco = carimbos(cfg["nome"])
    foco, herdado, alerta_foco = nucleo.resolver_foco(args.foco, ler(carimbo_foco), cfg["repos"])

    bruta = ev.ler_fila(cfg)
    if bruta is None:
        # Estreia do projeto: semeia e PARA. Painel sem fila revisada não teria dependência
        # declarada, e um "pronto pra começar" que ignora trava é pior que nenhum painel.
        print(f"# `{cfg['nome']}` ainda não tem fila em {cfg['fila']['repo']}:{cfg['fila']['caminho']}.")
        print("# Abaixo, a semeadura a partir das deltas ativas de cada repositório. Revise o")
        print("# `depende_de` de cada item, salve no caminho acima e rode de novo — só então há painel.")
        semear(cfg, args)
        return 2

    itens, alertas = nucleo.validar(bruta, cfg["ordem"])
    alertas += [alerta_foco] if alerta_foco else []
    info, provas, evid, alertas_ev = ev.colher(cfg, itens, nucleo.ligado, nucleo.ligar_prs)
    alertas += alertas_ev

    linhas, presos, alertas_m = nucleo.montar(itens, provas, evid, cfg["ordem"])
    if presos:
        print(f"ERRO: ciclo em depende_de — fila não montada. Itens presos: {', '.join(presos)}")
        return 1
    alertas += alertas_m

    hoje = dt.date.today()
    desde = nucleo.ultima_sessao(ler(carimbo_data), hoje)
    por_id = {it["id"]: it for it in itens}
    lib, novos = {}, set()
    for l in linhas:
        if l["estado"] != nucleo.MERGED:
            continue
        i, prova = info[l["repo"]], por_id[l["id"]]["arquivo_prova"]
        lib[l["id"]] = ev.liberacao(i["raiz"], prova, ev.releases_de(i))
        if ev.entrou_desde(i, desde.isoformat(), prova):
            novos.add(l["id"])

    visivel = nucleo.filtrar_painel(linhas, lib, novos)
    ocultos_merged = {l["id"] for l in linhas if l["estado"] == nucleo.MERGED} - {l["id"] for l in visivel}
    bancada = []
    for sigla in cfg["ordem"]:
        i = info[sigla]
        entradas = ev.bancada_de(i["raiz"], i["base"], i["prs"])
        contagem, itens_b, sem_listar = nucleo.resumir_bancada(entradas, not foco or sigla in foco)
        bancada.append({"repo": sigla, "contagem": contagem, "itens": itens_b, "ocultos": sem_listar,
                        "worktrees": sum(e["wt"] for e in entradas),
                        "branches": sum(not e["wt"] for e in entradas)})

    debito = []
    for sigla in cfg["ordem"]:
        i = info[sigla]
        texto, erro = ev.fila_debito(i["raiz"])
        if erro:
            debito.append({"repo": sigla, "erro": erro})
            continue
        resumo = ctx.resumir_debito(
            ctx.parse_fila_debito(texto),
            cunhados=ctx.ids_de(ev.arquivos_desde(i, desde.isoformat(), "debts/ativos")),
            quitados=ctx.ids_de(ev.arquivos_desde(i, desde.isoformat(), "debts/_archive")))
        debito.append({"repo": sigla, **resumo})
    secao_debito = ctx.render_debito(debito) if any(d.get("total") or d.get("erro") for d in debito) else []

    handoffs = {s: ev.handoffs_desde(info[s], desde.isoformat()) for s in cfg["ordem"]}
    handoffs = {s: v for s, v in handoffs.items() if v}
    licoes = {s: n for s in cfg["ordem"] if (n := ev.licoes_alteradas(info[s], desde.isoformat()))}
    ledger = ctx.pendencias_desde(ev.linhas_do_ledger(cfg["ledger"]), desde) if cfg["ledger"] else []
    texto_higiene, erro_higiene = ev.colher_higiene(varredura)
    erro_higiene = erro_higiene or erro_varredura
    agora_higiene = ctx.parse_higiene(texto_higiene)
    cache = DIR_ESTADO / f"higiene-{cfg['nome']}.json"
    antes_higiene, estreia = {}, not cache.is_file()
    if not estreia:
        try:
            antes_higiene = json.loads(cache.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            antes_higiene, estreia = {}, True
    delta = {} if estreia else ctx.delta_higiene(antes_higiene, agora_higiene)
    retro = ctx.render_retrospectiva(handoffs, licoes, ledger, delta, erro_higiene,
                                     base_higiene=len(agora_higiene) if estreia and agora_higiene else 0)

    # tm_isdst é o estado de agora; time.daylight só diz que a zona define horário de verão,
    # e usá-lo daria o deslocamento de verão o ano inteiro em toda zona que o observa.
    fuso = -(time.altzone if time.localtime().tm_isdst > 0 else time.timezone) // 3600
    sessoes = ctx.contar_sessoes(ev.timestamps_de_sessao(DIR_SESSOES), desde, fuso)
    janela = (f"Janela: {desde.isoformat()} → {hoje.isoformat()}"
              + (f" · {sessoes} sessão(ões) iniciada(s)" if sessoes else ""))

    fila_prox = nucleo.proximos(linhas, foco)
    if foco and fila_prox and not any(l["repo"] in foco for l in fila_prox):
        alertas.append(f"foco {'/'.join(foco)} sem item pendente na fila — o Próximo vem de fora do foco")

    tarefa = ""
    if fila_prox:
        it = por_id[fila_prox[0]["id"]]
        pasta = pasta_da_delta(it, info)
        if pasta:
            tarefa = nucleo.proxima_tarefa(ev.texto_na_base(info[it["repo"]], f"specs/{pasta}/tasks.md"))

    logs = [(s, ev.log_desde(i, desde.isoformat())) for s, i in info.items()]
    nos, arestas = nucleo.grafo(itens, visivel, ocultos_merged)
    diagrama = nucleo.render_mermaid(nos, arestas)
    texto = nucleo.renderizar(cfg["titulo"], hoje, desde, logs, visivel, alertas, lib, diagrama,
                              fila_prox, tarefa, bancada, foco, herdado, secao_debito, retro, janela)
    prioridade = notamod.prioridade_de(por_id.get(fila_prox[0]["id"]) if fila_prox else {}, tarefa)
    if args.dry_run:
        anterior = notamod.ler_nota(notamod.nota_do_dia(cfg, hoje, cfg["nome"]))
        print(notamod.render_nota(hoje, cfg["nome"], texto,
                                  anotacoes=notamod.extrair_anotacoes(anterior),
                                  rastro=notamod.extrair_rastro(anterior),
                                  segundos=time.monotonic() - comeco))
        print(f"\n> ensaio: nada escrito. A nota iria para "
              f"{notamod.pasta_das_notas(cfg) / notamod.nome_da_nota(hoje, cfg['nome'], prioridade)}",
              file=sys.stderr)
    else:
        print(texto)
        print(f"\n*gerado em {time.monotonic() - comeco:.1f}s*")
        if args.gravar:
            # O diagrama externo só nasce quando o embutido deixa de caber numa tela.
            grande = nucleo.precisa_externo(len(nos), shutil.which("d2"))
            caminho, motivo = notamod.gravar_nota(cfg, hoje, cfg["nome"], prioridade, texto,
                                                  segundos=time.monotonic() - comeco,
                                                  dir_estado=DIR_ESTADO,
                                                  fonte_d2=nucleo.render_d2(nos, arestas) if grande else "")
            print(f"\n> nota: {caminho}" + (f"\n> {motivo}" if motivo else ""))
    # O ensaio não carimba: o carimbo define a janela da PRÓXIMA execução real, e um
    # ensaio que o move faz a retrospectiva seguinte nascer vazia, sem como recuperar.
    if not args.dry_run and not args.sem_carimbo:
        DIR_ESTADO.mkdir(parents=True, exist_ok=True)
        carimbo_data.write_text(hoje.isoformat() + "\n", encoding="utf-8")
        carimbo_foco.write_text(" ".join(foco) + "\n", encoding="utf-8")
        if agora_higiene or texto_higiene:
            cache.write_text(json.dumps(agora_higiene, ensure_ascii=False), encoding="utf-8")
    return 0


def semear(cfg, args):
    import yaml
    existentes = set()
    if args.so_novos:
        bruta = ev.ler_fila(cfg)
        existentes = {it["id"] for it in nucleo.validar(bruta or {}, cfg["ordem"])[0]}
    itens = []
    for sigla in cfg["ordem"]:
        raiz = cfg["repos"][sigla]
        ev.fetch(raiz)
        base = ev.base_de(raiz, cfg["bases"])
        ativas, _ = ev.deltas_de(raiz, base)
        specs = [(n, ev.git(raiz, "show", f"{base}:specs/{n}/spec.md").stdout or None) for n in ativas]
        itens += [it for it in nucleo.semear_itens(sigla, specs) if it["id"] not in existentes]
    print(f"# Semeado em {dt.date.today()} a partir das deltas ativas na base de cada repositório."
          " Preencha o depende_de de cada item antes de usar.")
    sys.stdout.write(yaml.safe_dump({"itens": itens}, allow_unicode=True, sort_keys=False))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("projeto", nargs="?", help="nome da config em ~/.claude/sessoes/<projeto>.toml")
    ap.add_argument("foco", nargs="?", help="para que lado olhar primeiro: sigla, nome da pasta ou "
                                            "texto livre; a palavra `sem` limpa. Omitido, herda o foco "
                                            "carimbado na última sessão deste projeto")
    ap.add_argument("--semear", action="store_true", help="YAML da fila a partir das deltas ativas")
    ap.add_argument("--so-novos", action="store_true", help="com --semear: só os itens fora da fila")
    ap.add_argument("--sem-carimbo", action="store_true", help="não grava a data nem o foco desta execução")
    ap.add_argument("--gravar", action="store_true",
                    help="grava a nota do dia no vault declarado na config")
    ap.add_argument("--vault", help="sobrescreve o vault da config (para experimentar sem tocar no seu)")
    ap.add_argument("--dry-run", action="store_true",
                    help="compõe a nota do dia e imprime na saída padrão, sem escrever nada")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        nucleo.selftest()
        cfgmod.selftest()
        ctx.selftest()
        notamod.selftest()
        return 0
    if not args.projeto:
        disponiveis = cfgmod.projetos()
        ap.error("diga qual projeto — este painel não adivinha pelo diretório corrente.\n"
                 + (f"disponíveis: {', '.join(disponiveis)}" if disponiveis
                    else f"nenhum configurado ainda; crie um .toml em {cfgmod.DIR_CONFIG}"))
    cfg = cfgmod.carregar(args.projeto)
    if args.vault:
        cfg["nota"] = {**cfg["nota"], "vault": Path(args.vault).expanduser()}
    return semear(cfg, args) if args.semear else painel(cfg, args)


if __name__ == "__main__":
    sys.exit(main())
