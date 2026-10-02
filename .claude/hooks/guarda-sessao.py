#!/usr/bin/env python3
"""Hooks de sessão (delta-083): escrita com outra sessão viva no mesmo checkout+branch
pede confirmação.

Faz cumprir o "1 sessão = 1 branch" que até aqui era só prosa. Cinco colisões até
2026-08-16 (uma com perda real de edições) estão na `debts/LICOES.md`, e em 2026-08-20
o checkout principal foi trocado de branch por baixo de outras sessões duas vezes numa
hora com quatro sessões vivas.

**`ask`, nunca `deny`** — decisão do Iuri registrada no DT-071: o custo de um falso
positivo travando a sessão é maior que o do aviso ignorável.

Três modos num script só:
  --registrar   SessionStart · grava o registro desta sessão
  --encerrar    SessionEnd   · apaga o registro desta sessão
  (sem flag)    PreToolUse   · decide sobre a escrita

Degradação graciosa em todos (RNF2): sem git, sem diretório gravável, JSON corrompido
ou input inesperado → exit 0 em silêncio. O hook nunca derruba a sessão.
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

# Registro mais velho que isto é resíduo de sessão que morreu sem SessionEnd, não
# sessão viva. Varrer o diretório a cada escrita para limpar custaria I/O em caminho
# quente; o TTL silencia o órfão sem esse custo.
SESSAO_TTL_HORAS = 12
FORMATO_HORA = "%Y-%m-%dT%H:%M:%S"


def dir_estado() -> Path:
    """Diretório do registro de sessões — variável do harness, com fallback próprio.

    O DT-071 desenhou sobre ${CLAUDE_PLUGIN_DATA}; medido na delta-083, ela **não
    existe** neste ambiente, e sem fallback o hook nasceria no-op. O fallback é de
    **usuário**, não de projeto, de propósito: a colisão que interessa cruza worktrees
    do mesmo repositório, e cada worktree tem um CLAUDE_PROJECT_DIR diferente.
    """
    base = os.environ.get("CLAUDE_PLUGIN_DATA")
    raiz = Path(base) if base else Path.home() / ".claude" / "deltaspec"
    return raiz / "sessoes"


def chave_do_checkout(checkout: str) -> str:
    """Nome de arquivo estável para um checkout — hash, não o caminho.

    O caminho tem barra e acento e vira nome ilegal; o hash é curto, estável e não
    escreve o layout de disco de ninguém dentro do diretório de estado.
    """
    return hashlib.sha1(checkout.encode("utf-8")).hexdigest()[:16]


def decidir(checkout: str, branch: str, agora: datetime, registros: list, id_atual: str):
    """Decisão pura: outra sessão viva no mesmo checkout+branch → dict de `ask`; senão None.

    Separada do I/O para o --selftest exercitá-la sem harness, sem git e sem relógio —
    é o que torna os seis casos testáveis.
    """
    for reg in registros:
        if reg.get("session_id") == id_atual:
            continue  # a própria sessão nunca se bloqueia
        if reg.get("checkout") != checkout or reg.get("branch") != branch:
            continue
        try:
            iniciado = datetime.strptime(reg.get("iniciado", ""), FORMATO_HORA)
        except (ValueError, TypeError):
            continue  # registro ilegível é ignorado, nunca vira bloqueio
        minutos = int((agora - iniciado).total_seconds() // 60)
        if minutos > SESSAO_TTL_HORAS * 60 or minutos < 0:
            continue  # resíduo de sessão morta sem SessionEnd
        idade = ("menos de 1 min" if minutos < 1
                 else f"{minutos} min" if minutos < 60
                 else f"{minutos // 60} h {minutos % 60} min")
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "ask",
                "permissionDecisionReason": (
                    f"outra sessão viva há {idade} no mesmo checkout e na branch "
                    f"'{branch}' — duas sessões no mesmo working tree já custaram edições "
                    f"(debts/LICOES.md). Isole com `claude --worktree`, ou confirme se "
                    f"você sabe que é seguro"
                ),
            }
        }
    return None


def git(*args):
    """stdout do git, ou None quando não há git/repositório — degrada como o C7."""
    try:
        r = subprocess.run(["git", *args], capture_output=True, text=True)
    except (FileNotFoundError, OSError):
        return None
    return r.stdout.strip() if r.returncode == 0 else None


def checkout_do_alvo(caminho: str):
    """(checkout, branch) do repositório que contém o **caminho-alvo da escrita**.

    Pelo alvo e nunca pelo cwd: guard por cwd bloquearia a escrita legítima de uma
    sessão que trabalha numa worktree diferente daquela em que foi aberta.
    """
    if not caminho:
        return None, None
    dono = Path(caminho).parent
    while not dono.exists() and dono != dono.parent:
        dono = dono.parent
    raiz = git("-C", str(dono), "rev-parse", "--show-toplevel")
    if not raiz:
        return None, None
    return raiz, git("-C", raiz, "rev-parse", "--abbrev-ref", "HEAD")


def le_registros(destino: Path) -> list:
    """Todos os registros vivos no diretório de estado; arquivo ilegível é pulado."""
    if not destino.is_dir():
        return []
    fora = []
    for arq in destino.glob("*.json"):
        try:
            fora.append(json.loads(arq.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, ValueError, OSError):
            continue
    return fora


def caminho_do_registro(destino: Path, checkout: str, id_sessao: str) -> Path:
    return destino / f"{chave_do_checkout(checkout)}-{id_sessao[:12]}.json"


def registrar(entrada: dict) -> int:
    id_sessao = entrada.get("session_id", "")
    raiz = git("rev-parse", "--show-toplevel")
    if not (id_sessao and raiz):
        return 0
    destino = dir_estado()
    try:
        destino.mkdir(parents=True, exist_ok=True)
        caminho_do_registro(destino, raiz, id_sessao).write_text(json.dumps({
            "session_id": id_sessao,
            "checkout": raiz,
            "branch": git("-C", raiz, "rev-parse", "--abbrev-ref", "HEAD") or "",
            "iniciado": datetime.now().strftime(FORMATO_HORA),
        }), encoding="utf-8")
    except OSError:
        return 0  # diretório não gravável: o hook se cala, a sessão segue
    return 0


def encerrar(entrada: dict) -> int:
    id_sessao = entrada.get("session_id", "")
    raiz = git("rev-parse", "--show-toplevel")
    if not (id_sessao and raiz):
        return 0
    try:
        caminho_do_registro(dir_estado(), raiz, id_sessao).unlink(missing_ok=True)
    except OSError:
        pass
    return 0


def avaliar(entrada: dict) -> int:
    checkout, branch = checkout_do_alvo((entrada.get("tool_input") or {}).get("file_path", ""))
    if not (checkout and branch):
        return 0
    veredito = decidir(checkout, branch, datetime.now(),
                       le_registros(dir_estado()), entrada.get("session_id", ""))
    if veredito:
        print(json.dumps(veredito))
    return 0


def selftest() -> int:
    agora = datetime(2026, 8, 24, 12, 0, 0)
    viva = [{"session_id": "outra", "branch": "feat/x", "checkout": "/repo",
             "iniciado": "2026-08-24T11:30:00"}]

    d = decidir("/repo", "feat/x", agora, viva, "minha")
    assert d and d["hookSpecificOutput"]["permissionDecision"] == "ask", d
    razao = d["hookSpecificOutput"]["permissionDecisionReason"]
    assert "30 min" in razao, f"idade do registro não foi reportada: {razao}"
    assert "worktree" in razao, f"a saída sugerida não foi oferecida: {razao}"
    # "há 0 min" lê mal na hora em que o aviso mais aparece: sessão aberta agora
    recem = [{**viva[0], "iniciado": "2026-08-24T12:00:00"}]
    razao_recem = decidir("/repo", "feat/x", agora, recem, "minha")["hookSpecificOutput"]["permissionDecisionReason"]
    assert "menos de 1 min" in razao_recem, razao_recem

    assert decidir("/repo", "feat/x", agora, viva, "outra") is None, "a própria sessão não se bloqueia"
    assert decidir("/repo", "feat/y", agora, viva, "minha") is None, "branch diferente é livre"
    assert decidir("/outro", "feat/x", agora, viva, "minha") is None, "checkout diferente é livre"
    assert decidir("/repo", "feat/x", agora, [], "minha") is None, "sem registro, silêncio"

    velha = [{**viva[0], "iniciado": "2026-08-20T11:30:00"}]
    assert decidir("/repo", "feat/x", agora, velha, "minha") is None, "registro além do TTL não avisa"
    ilegivel = [{**viva[0], "iniciado": "ontem de manhã"}]
    assert decidir("/repo", "feat/x", agora, ilegivel, "minha") is None, "registro ilegível não vira bloqueio"
    # relógio do sistema para trás entre duas sessões: idade negativa não é sessão viva
    futuro = [{**viva[0], "iniciado": "2026-08-24T13:00:00"}]
    assert decidir("/repo", "feat/x", agora, futuro, "minha") is None, "registro no futuro não avisa"

    # limite exato do TTL: 12 h ainda vale, 12 h e 1 min não
    no_limite = [{**viva[0], "iniciado": "2026-08-24T00:00:00"}]
    assert decidir("/repo", "feat/x", agora, no_limite, "minha") is not None, "12 h exatas ainda é sessão viva"
    passou = [{**viva[0], "iniciado": "2026-08-23T23:59:00"}]
    assert decidir("/repo", "feat/x", agora, passou, "minha") is None, "acima do TTL não avisa"

    assert avaliar({}) == 0, "input sem tool_input sai 0 em silêncio"
    assert avaliar({"tool_input": {"file_path": ""}}) == 0, "caminho vazio sai 0"
    assert chave_do_checkout("/a") != chave_do_checkout("/b"), "checkouts distintos, chaves distintas"
    assert chave_do_checkout("/a") == chave_do_checkout("/a"), "a chave é estável"

    # I/O real: registrar/encerrar/le_registros contra disco de verdade, num diretório
    # descartável — nunca o real, para não colidir com sessão viva de verdade.
    tmp = tempfile.mkdtemp()
    original = os.environ.get("CLAUDE_PLUGIN_DATA")
    try:
        os.environ["CLAUDE_PLUGIN_DATA"] = tmp
        entrada = {"session_id": "selftest-io"}
        assert registrar(entrada) == 0
        registros = le_registros(dir_estado())
        assert any(r.get("session_id") == "selftest-io" for r in registros), "registrar não gravou"

        (dir_estado() / "corrompido.json").write_text("{isto não é json", encoding="utf-8")
        registros = le_registros(dir_estado())
        assert any(r.get("session_id") == "selftest-io" for r in registros), \
            "JSON corrompido vizinho derrubou a leitura dos demais"

        assert encerrar(entrada) == 0
        registros = le_registros(dir_estado())
        assert not any(r.get("session_id") == "selftest-io" for r in registros), "encerrar não apagou"

        # diretório não gravável: a base aponta para dentro de um arquivo comum, então
        # mkdir(parents=True) estoura OSError — registrar/encerrar devem engolir e sair 0.
        arquivo_comum = Path(tmp) / "nao-e-diretorio"
        arquivo_comum.write_text("x", encoding="utf-8")
        os.environ["CLAUDE_PLUGIN_DATA"] = str(arquivo_comum / "sessoes")
        assert registrar(entrada) == 0, "diretório não gravável deveria degradar em silêncio"
    finally:
        if original is None:
            os.environ.pop("CLAUDE_PLUGIN_DATA", None)
        else:
            os.environ["CLAUDE_PLUGIN_DATA"] = original
        shutil.rmtree(tmp, ignore_errors=True)

    print("guarda-sessao selftest: OK (18 casos — ask, própria sessão, branch, checkout, "
          "TTL nos dois lados do limite, registro ilegível e futuro, degradação, I/O real de "
          "registrar/encerrar/leitura com JSON corrompido e diretório não gravável)")
    return 0


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    try:
        entrada = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError, OSError):
        return 0  # input inesperado: silêncio, nunca bloqueia a sessão
    if "--registrar" in sys.argv:
        return registrar(entrada)
    if "--encerrar" in sys.argv:
        return encerrar(entrada)
    return avaliar(entrada)


if __name__ == "__main__":
    sys.exit(main())
