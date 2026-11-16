#!/usr/bin/env python3
"""Config por projeto do painel de abertura de sessão: forma validada, caminhos resolvidos.

O projeto é declarado fora do plugin, em `~/.claude/sessoes/<projeto>.toml` — é lá que vivem
os nomes reais de repositório e de cliente, que não podem entrar num diretório publicado.
Um `config.toml` opcional na mesma pasta carrega o que vale para todos (o vault das notas,
tipicamente); o arquivo do projeto sobrescreve campo a campo.

REGRAS — este texto é o dono do esquema; a SKILL.md e o plan.md da delta apontam para cá
e não o repetem.

Esquema:
  titulo              nome do projeto no cabeçalho do painel (default: o nome do arquivo)
  workspace           raiz onde moram os repositórios
  bases               refs candidatas a base, na ordem (default: origin/develop, origin/main)
  [repos]             SIGLA = pasta — relativa ao workspace, ou absoluta/com `~`
  [fila].repo         sigla do repositório dono do arquivo de fila
  [fila].caminho      caminho do arquivo dentro desse repositório, lido da base dele
  [fila].ordem        siglas na ordem de desempate (default: a ordem de [repos])
  [nota].vault        raiz do vault onde a nota do dia é gravada
  [nota].pasta        subpasta dentro do vault (default: 40-periodico/sessoes)
  [ledger]            seção opcional; ausente = nenhuma leitura de pendências fora de projeto
  [ledger].caminho          arquivo append-only de pendências, fora de qualquer repositório
  [higiene]           seção inteira opcional; ausente = nenhuma varredura de higiene
  [higiene].raiz            raiz da varredura
  [higiene].profundidade    níveis a descer (default: 2)
  [higiene].excluir         nomes de pasta a pular (default: nenhum)

Config inválida não produz painel: os erros saem TODOS de uma vez, cada um nomeando o campo,
e o código de saída é 2. Painel parcial mentiria — é o mesmo princípio do fetch que falha.
Sigla fora de `^[A-Z]{2,5}$` é recusada porque ela é prefixo do id do item (`SIGLA/NNN`) e
vira nome de subgrafo no diagrama. Pasta sem `.git` é recusada porque o motor roda `git -C`
ali: é fronteira de confiança, não conveniência.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - depende da versão do interpretador
    print("este painel exige Python 3.11 ou mais novo (o tomllib entrou na 3.11); "
          f"o interpretador em uso é {sys.version.split()[0]}", file=sys.stderr)
    raise SystemExit(2)

# A casa é a do Claude Code, não a do XDG: usar `XDG_CONFIG_HOME` jogaria a pasta
# para dentro dele em toda máquina que o define, e a doc promete outro lugar.
DIR_CONFIG = Path(os.environ.get("CLAUDE_CONFIG_DIR") or (Path.home() / ".claude")) / "sessoes"
GLOBAL = "config"  # nome reservado: é o arquivo do que vale para todos, não um projeto
BASES_PADRAO = ("origin/develop", "origin/main")
PASTA_NOTA_PADRAO = "40-periodico/sessoes"
PROFUNDIDADE_PADRAO = 2
RE_SIGLA = re.compile(r"^[A-Z]{2,5}$")
CHAVES = ("titulo", "workspace", "bases", "repos", "fila", "nota", "ledger", "higiene")


# ---------- funções puras ----------

def mesclar(comum, projeto):
    """Campo do projeto vence o comum; tabela é mesclada chave a chave, não substituída."""
    saida = dict(comum or {})
    for chave, valor in (projeto or {}).items():
        if isinstance(valor, dict) and isinstance(saida.get(chave), dict):
            saida[chave] = {**saida[chave], **valor}
        else:
            saida[chave] = valor
    return saida


def resolver(base, caminho):
    """Caminho absoluto ou com `~` fica como está; o resto pende do `base`."""
    p = Path(str(caminho)).expanduser()
    return p if p.is_absolute() else Path(base) / p


def validar_config(dados, nome="projeto"):
    """(cfg, erros). Acumula TODOS os erros de forma; nada de disco é checado aqui."""
    dados = dados if isinstance(dados, dict) else {}
    erros = [f"chave desconhecida `{k}` — as aceitas são {', '.join(CHAVES)}"
             for k in dados if k not in CHAVES]

    workspace = str(dados.get("workspace") or "").strip()
    if not workspace:
        erros.append("falta `workspace`: a raiz onde moram os repositórios do projeto")
    raiz = Path(workspace).expanduser() if workspace else Path()

    repos, brutos = {}, dados.get("repos") if isinstance(dados.get("repos"), dict) else {}
    if not brutos:
        erros.append("`[repos]` vazio ou ausente: declare ao menos um `SIGLA = \"pasta\"`")
    for sigla, pasta in brutos.items():
        if not RE_SIGLA.match(str(sigla)):
            erros.append(f"sigla `{sigla}` fora do formato de 2 a 5 letras maiúsculas "
                         "— ela é o prefixo do id do item e vira nome de subgrafo no diagrama")
        elif not str(pasta or "").strip():
            erros.append(f"repo `{sigla}` sem pasta")
        else:
            repos[str(sigla)] = resolver(raiz, pasta)

    fila = dados.get("fila") if isinstance(dados.get("fila"), dict) else {}
    fila_repo, fila_caminho = str(fila.get("repo") or "").strip(), str(fila.get("caminho") or "").strip()
    if not fila_repo:
        erros.append("falta `[fila].repo`: a sigla do repositório dono do arquivo de fila")
    elif fila_repo not in repos:
        erros.append(f"`[fila].repo` = `{fila_repo}`, que não está em `[repos]`")
    if not fila_caminho:
        erros.append("falta `[fila].caminho`: o arquivo de fila dentro desse repositório")

    ordem = [str(s) for s in fila.get("ordem") or list(repos)]
    erros += [f"`[fila].ordem` cita `{s}`, que não está em `[repos]`" for s in ordem if s not in repos]

    nota = dados.get("nota") if isinstance(dados.get("nota"), dict) else {}
    vault = str(nota.get("vault") or "").strip()
    if not vault:
        erros.append("falta `[nota].vault`: a raiz do vault onde a nota do dia é gravada")

    ledger = None
    if "ledger" in dados:
        l = dados.get("ledger") if isinstance(dados.get("ledger"), dict) else {}
        lcaminho = str(l.get("caminho") or "").strip()
        if not lcaminho:
            erros.append("`[ledger]` declarada sem `caminho` — remova a seção ou nomeie o arquivo")
        else:
            ledger = Path(lcaminho).expanduser()

    higiene = None
    if "higiene" in dados:
        h = dados.get("higiene") if isinstance(dados.get("higiene"), dict) else {}
        hraiz = str(h.get("raiz") or "").strip()
        if not hraiz:
            erros.append("`[higiene]` declarada sem `raiz` — remova a seção ou nomeie a raiz da varredura")
        else:
            prof = h.get("profundidade", PROFUNDIDADE_PADRAO)
            if isinstance(prof, bool) or not isinstance(prof, int) or prof < 1:
                erros.append(f"`[higiene].profundidade` = {prof!r}: esperado inteiro maior que zero")
                prof = PROFUNDIDADE_PADRAO
            higiene = {"raiz": Path(hraiz).expanduser(), "profundidade": prof,
                       "excluir": [str(x) for x in h.get("excluir") or []]}

    cfg = {
        "nome": nome,
        "titulo": str(dados.get("titulo") or nome),
        "workspace": raiz,
        "bases": tuple(str(b) for b in dados.get("bases") or BASES_PADRAO),
        "repos": repos,
        "ordem": [s for s in ordem if s in repos],
        "fila": {"repo": fila_repo, "caminho": fila_caminho},
        "nota": {"vault": Path(vault).expanduser() if vault else None,
                 "pasta": str(nota.get("pasta") or PASTA_NOTA_PADRAO)},
        "ledger": ledger,
        "higiene": higiene,
    }
    return cfg, erros


# ---------- I/O ----------

def erros_de_disco(cfg):
    """Repositório declarado que não existe ou não é git — fronteira de confiança do `git -C`."""
    erros = []
    for sigla, pasta in cfg["repos"].items():
        if not pasta.is_dir():
            erros.append(f"repo `{sigla}`: pasta inexistente — {pasta}")
        elif not (pasta / ".git").exists():
            erros.append(f"repo `{sigla}`: {pasta} não é um repositório git")
    return erros


def ler_toml(caminho):
    """(dados, erro). Arquivo ilegível ou malformado é mensagem, nunca rastro de pilha (RNF3)."""
    try:
        with caminho.open("rb") as f:
            return tomllib.load(f), ""
    except tomllib.TOMLDecodeError as e:
        return {}, f"{caminho.name}: TOML malformado — {e}"
    except OSError as e:
        return {}, f"{caminho.name}: não deu para ler — {e.strerror}"


def projetos(raiz=DIR_CONFIG):
    return sorted(p.stem for p in raiz.glob("*.toml") if p.stem != GLOBAL) if raiz.is_dir() else []


def recusar(mensagem):
    """Toda recusa de config sai com 2 e mensagem no stderr — nunca 1, nunca rastro de pilha."""
    print(mensagem, file=sys.stderr)
    raise SystemExit(2)


def carregar(nome, raiz=DIR_CONFIG):
    """Config do projeto, já mesclada com a comum e validada. Recusa sai 2 com todos os erros."""
    arquivo = raiz / f"{nome}.toml"
    if not arquivo.is_file():
        disponiveis = projetos(raiz)
        recusar(f"projeto `{nome}` não tem config em {raiz}.\n"
                + (f"disponíveis: {', '.join(disponiveis)}" if disponiveis
                   else f"nenhum projeto configurado ainda — crie {arquivo}"))
    comum = raiz / f"{GLOBAL}.toml"
    dados_comuns, erro_comum = ler_toml(comum) if comum.is_file() else ({}, "")
    dados_projeto, erro_projeto = ler_toml(arquivo)
    leitura = [e for e in (erro_comum, erro_projeto) if e]
    if leitura:
        recusar("config ilegível — sem painel:\n" + "\n".join(f"  - {e}" for e in leitura))
    cfg, erros = validar_config(mesclar(dados_comuns, dados_projeto), nome)
    erros += erros_de_disco(cfg) if not erros else []
    if erros:
        recusar(f"config inválida em {arquivo} — sem painel:\n"
                + "\n".join(f"  - {e}" for e in erros))
    return cfg


# ---------- selftest ----------

def selftest():
    # Fixtures com caminho neutro: o gate de portabilidade (RNF5) proíbe caminho de home
    # em artefato publicado, e o selftest é publicado junto com o resto da skill.
    base = {"workspace": "/w", "repos": {"APP": "aplicacao", "GEST": "_gestao"},
            "fila": {"repo": "GEST", "caminho": "planejamento/fila.yml", "ordem": ["APP", "GEST"]},
            "nota": {"vault": "/v"}}

    cfg, erros = validar_config(base, "projeto-x")
    assert erros == [], erros
    assert cfg["titulo"] == "projeto-x" and cfg["ordem"] == ["APP", "GEST"]
    assert cfg["bases"] == ("origin/develop", "origin/main")  # default
    assert cfg["nota"]["pasta"] == "40-periodico/sessoes" and cfg["higiene"] is None
    assert cfg["ledger"] is None  # seção ausente desliga a leitura de pendências
    assert cfg["repos"]["APP"] == Path("/w/aplicacao")  # relativa pende do workspace
    assert cfg["fila"] == {"repo": "GEST", "caminho": "planejamento/fila.yml"}

    # caminho absoluto escapa do workspace; `~` expande para a home
    cfg, _ = validar_config({**base, "repos": {"APP": "aplicacao", "DOT": "/opt/ferramenta"}})
    assert cfg["repos"]["DOT"] == Path("/opt/ferramenta")
    assert resolver("/base", "~") == Path.home()

    # ordem ausente cai na ordem de [repos]
    b2 = {**base, "fila": {"repo": "GEST", "caminho": "f.yml"}}
    assert validar_config(b2)[0]["ordem"] == ["APP", "GEST"]

    # obrigatórios: todos os erros de uma vez, nunca o primeiro
    _, e = validar_config({"repos": {}})
    assert len(e) >= 4 and any("workspace" in m for m in e) and any("[repos]" in m for m in e)
    assert any("[fila].repo" in m for m in e) and any("[nota].vault" in m for m in e)

    # sigla: formato e coerência com [repos]
    _, e = validar_config({**base, "repos": {"app": "x", "MUITOLONGA": "y"}})
    assert sum("fora do formato" in m for m in e) == 2
    assert any("`app`" in m for m in e)
    _, e = validar_config({**base, "fila": {"repo": "ZZ", "caminho": "f.yml"}})
    assert any("`ZZ`" in m and "[repos]" in m for m in e)
    _, e = validar_config({**base, "fila": {"repo": "GEST", "caminho": "f.yml", "ordem": ["APP", "ZZ"]}})
    assert any("ordem" in m and "ZZ" in m for m in e)

    # typo em TOML é silencioso demais: chave desconhecida nomeia as aceitas
    _, e = validar_config({**base, "vaut": "/v"})
    assert any("`vaut`" in m and "workspace" in m for m in e)

    # higiene: seção ausente desliga; presente sem raiz é erro; defaults preenchidos
    cfg, e = validar_config({**base, "higiene": {"raiz": "/w", "excluir": ["forks"]}})
    assert e == [] and cfg["higiene"]["profundidade"] == 2 and cfg["higiene"]["excluir"] == ["forks"]
    _, e = validar_config({**base, "higiene": {"profundidade": 3}})
    assert any("higiene" in m and "raiz" in m for m in e)
    # ledger: mesmo desenho — ausente desliga, presente sem caminho é erro
    cfg, e = validar_config({**base, "ledger": {"caminho": "/v/pendencias.md"}})
    assert e == [] and cfg["ledger"] == Path("/v/pendencias.md")
    _, e = validar_config({**base, "ledger": {}})
    assert any("ledger" in m and "caminho" in m for m in e)
    # profundidade não numérica é erro acumulado, não exceção: validar_config é pura e sempre devolve
    for ruim in ("dois", [2], 0, True):
        cfg, e = validar_config({**base, "higiene": {"raiz": "/w", "profundidade": ruim}})
        assert any("profundidade" in m for m in e), ruim
        assert cfg["higiene"]["profundidade"] == 2  # cai no default para o resto seguir validando

    # mescla: o projeto vence, e tabela se funde chave a chave em vez de substituir
    comum = {"nota": {"vault": "/v", "pasta": "40-periodico/sessoes"}}
    assert mesclar(comum, {"workspace": "/w"})["nota"]["vault"] == "/v"
    fundido = mesclar(comum, {"nota": {"pasta": "outra"}})["nota"]
    assert fundido == {"vault": "/v", "pasta": "outra"}
    assert mesclar({}, {}) == {} and mesclar(None, {"a": 1}) == {"a": 1}

    # resolver
    assert resolver("/base", "sub") == Path("/base/sub") and resolver("/base", "/abs") == Path("/abs")

    # TOML malformado ou ilegível vira mensagem, nunca rastro de pilha (RNF3)
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        bom = Path(tmp) / "bom.toml"
        bom.write_text('titulo = "x"\n', encoding="utf-8")
        assert ler_toml(bom) == ({"titulo": "x"}, "")
        ruim = Path(tmp) / "ruim.toml"
        ruim.write_text("titulo = [sem fechar\n", encoding="utf-8")
        dados, erro = ler_toml(ruim)
        assert dados == {} and "malformado" in erro and "ruim.toml" in erro
        dados, erro = ler_toml(Path(tmp) / "inexistente.toml")
        assert dados == {} and "não deu para ler" in erro

    print("selftest ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true", help="valida as funções puras deste módulo")
    ap.add_argument("--mostrar", metavar="PROJETO", help="carrega e imprime a config resolvida")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return 0
    if args.mostrar:
        cfg = carregar(args.mostrar)
        for chave, valor in cfg.items():
            print(f"{chave}: {valor}")
        return 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
