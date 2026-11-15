#!/usr/bin/env python3
"""Hook Stop da memória de projeto (delta-137, DT-208): cobra o fato antes de a sessão parar.

Bloqueia a parada **uma vez por sessão** (marcador por session_id) quando o repo tem .claude/memory/, houve commit ou edição desde
o início da sessão e nenhum fato de .claude/memory/ (inbox incluso) foi criado ou alterado.
Com `stop_hook_active`, sem memória, sem registro de início ou com entrada ilegível, sai 0 em
silêncio (RNF2). "Desde o início" = o `iniciado` que o guarda-sessao.py grava no SessionStart,
ou, onde ele não existe, o que o próprio `--registrar` grava no SessionStart do plugin (delta-134).

Uso:
  parada.py [ROOT]              lê o JSON do hook Stop no stdin
  parada.py --registrar [ROOT]  lê o JSON do hook SessionStart no stdin e grava o início da sessão
  parada.py --selftest
"""
import io
import json
import os
import re
import sys
import tempfile
from contextlib import redirect_stdout
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from memoria import DIR_MEMORIA, INDICE, _git, _repo_tmp  # noqa: E402

FORMATO_HORA = "%Y-%m-%dT%H:%M:%S"   # o mesmo de guarda-sessao.py, que grava o `iniciado` lido aqui
PROJECOES = ("HANDOFF.md", f"{DIR_MEMORIA.as_posix()}/{INDICE}")   # regeneradas: não são trabalho nem fato
SEM_ASPAS = ("-c", "core.quotePath=false")
# Subpasta do registro gravado pelo --registrar: fora do glob("*.json") do guarda-sessao.py, que lê
# todo registro a cada escrita (caminho quente) e não precisa ver estes, sem checkout nem branch.
DIR_REGISTRO_PLUGIN = "memoria"
MOTIVO_PARADA = (
    "Houve commit ou edição nesta sessão e nenhum fato de .claude/memory/ foi gravado. Antes de parar, "
    "grave ou atualize com Write o fato .claude/memory/agora-<frente>.md da frente trabalhada (estado e "
    "próximo passo; preferência do usuário vai para .claude/memory/inbox/) e rode `memoria.py indice .`. "
    "Se nada durável nasceu, diga isso em uma linha e pare de novo — este aviso aparece uma vez por sessão.")


def dir_sessoes() -> Path:
    """Espelho de `dir_estado()` em .claude/hooks/guarda-sessao.py — manter em sincronia: o plugin
    não importa hook de repo, e o registro lido aqui é o que aquele hook grava."""
    base = os.environ.get("CLAUDE_PLUGIN_DATA")
    return (Path(base) if base else Path.home() / ".claude" / "deltaspec") / "sessoes"


def _seguro(session_id: str) -> str:
    """session_id como nome de arquivo: fora de [A-Za-z0-9_-] vira `_` (sem separador, sem traversal)."""
    return re.sub(r"[^A-Za-z0-9_-]", "_", session_id)


def inicio_da_sessao(session_id: str, pasta: Path) -> datetime | None:
    """`iniciado` do registro do guarda-sessao.py (pasta/*.json) ou do --registrar
    (pasta/memoria/<session_id>.json); sem registro, None."""
    if not session_id or not pasta.is_dir():
        return None
    for arq in [*pasta.glob("*.json"), pasta / DIR_REGISTRO_PLUGIN / f"{_seguro(session_id)}.json"]:
        try:
            reg = json.loads(arq.read_text(encoding="utf-8"))
            if reg.get("session_id") == session_id:
                return datetime.strptime(reg["iniciado"], FORMATO_HORA)
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            continue  # registro ilegível é pulado, como no guarda-sessao
    return None


def mudados_desde(root: Path, inicio: datetime) -> set[str]:
    """Caminhos (relativos à raiz do repo) tocados desde `inicio`: arquivos dos commits com data
    >= inicio, mais os do working tree com mtime >= inicio. Apagado (sem mtime) conta como tocado.
    `core.quotePath=false` mantém nome acentuado legível (sem aspas e octal), para o stat e o prefixo casarem."""
    caminhos = {l for l in _git(root, *SEM_ASPAS, "log", f"--since={inicio.strftime(FORMATO_HORA)}",
                                "--format=", "--name-only").splitlines() if l}
    for linha in _git(root, *SEM_ASPAS, "status", "--porcelain", "-uall", "--no-renames").splitlines():
        rel = linha[3:]
        try:
            tocado = datetime.fromtimestamp((root / rel).stat().st_mtime) >= inicio
        except OSError:
            tocado = True
        if tocado:
            caminhos.add(rel)
    return caminhos


def decidir_parada(mudados: set[str]) -> str | None:
    """Pura: trabalho fora da memória sem nenhum fato tocado (inbox conta) → motivo do bloqueio."""
    prefixo = f"{DIR_MEMORIA.as_posix()}/"
    relevantes = mudados - set(PROJECOES)
    trabalho = any(not p.startswith(prefixo) for p in relevantes)
    fato = any(p.startswith(prefixo) for p in relevantes)
    return MOTIVO_PARADA if trabalho and not fato else None


def cmd_parar(root: Path, texto: str) -> int:
    """Hook Stop. Bloqueia uma vez por sessão (marcador); com stop_hook_active, sem memória, sem registro de início ou
    com entrada ilegível, sai 0 em silêncio (RNF2)."""
    try:
        entrada = json.loads(texto)
    except ValueError:
        return 0
    if not isinstance(entrada, dict) or entrada.get("stop_hook_active") or not (root / DIR_MEMORIA).is_dir():
        return 0
    sid = str(entrada.get("session_id") or "")
    pasta = dir_sessoes()
    marca = pasta / f"parada-{_seguro(sid)}.marca"
    inicio = inicio_da_sessao(sid, pasta)
    if inicio is None or marca.exists():
        return 0
    try:
        motivo = decidir_parada(mudados_desde(root, inicio))
    except OSError:
        return 0  # git ausente ou subprocess falhou: degrada em silêncio (RNF2)
    if motivo:
        print(json.dumps({"decision": "block", "reason": motivo}))
        try:
            # ponytail: um marcador por sessão, nunca limpo (arquivos pequenos acumulam); upgrade:
            # apagar no `guarda-sessao --encerrar`.
            marca.touch()
        except OSError:
            pass  # sem marcador cobra de novo na próxima parada: erra para o lado seguro
    return 0


def cmd_registrar(root: Path, texto: str) -> int:
    """SessionStart do plugin (delta-134): grava o início da sessão onde o guarda-sessao.py não roda.
    Sem .claude/memory/, sem session_id, com registro já existente ou com qualquer falha, não grava
    nada e sai 0 em silêncio (RNF2). Registro existente nunca é reescrito."""
    try:
        entrada = json.loads(texto)
    except ValueError:
        return 0
    if not isinstance(entrada, dict) or not (root / DIR_MEMORIA).is_dir():
        return 0
    sid, pasta = str(entrada.get("session_id") or ""), dir_sessoes()
    if not sid or inicio_da_sessao(sid, pasta) is not None:
        return 0
    try:
        # ponytail: um arquivo por sessão, nunca limpo (sem SessionEnd no plugin); upgrade: hook SessionEnd.
        (pasta / DIR_REGISTRO_PLUGIN).mkdir(parents=True, exist_ok=True)
        (pasta / DIR_REGISTRO_PLUGIN / f"{_seguro(sid)}.json").write_text(json.dumps(
            {"session_id": sid, "iniciado": datetime.now().strftime(FORMATO_HORA)}), encoding="utf-8")
    except OSError:
        pass  # diretório não gravável: o Stop não cobra nesta sessão, erra para o lado de liberar
    return 0


def selftest_decidir_parada() -> None:
    assert decidir_parada({"a.py"}) == MOTIVO_PARADA, "trabalho sem fato bloqueia"
    assert decidir_parada({"a.py", ".claude/memory/agora-x.md"}) is None, "fato tocado libera"
    assert decidir_parada({"a.py", ".claude/memory/inbox/pref.md"}) is None, "fato no inbox conta"
    assert decidir_parada({"a.py", ".claude/memory/MEMORY.md"}) == MOTIVO_PARADA, "índice não é fato"
    assert decidir_parada({"HANDOFF.md", ".claude/memory/MEMORY.md"}) is None, "só projeção não é trabalho"
    assert decidir_parada({".claude/memory/agora-x.md"}) is None and decidir_parada(set()) is None
    print("selftest_decidir_parada: OK")


def selftest_inicio_da_sessao() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        pasta = Path(tmp)
        (pasta / "corrompido.json").write_text("{não é json", encoding="utf-8")
        (pasta / "outra.json").write_text(json.dumps({"session_id": "s2", "iniciado": "ontem"}), encoding="utf-8")
        (pasta / "minha.json").write_text(json.dumps({"session_id": "s1", "iniciado": "2026-10-24T09:30:00"}), encoding="utf-8")
        assert inicio_da_sessao("s1", pasta) == datetime(2026, 10, 24, 9, 30), "acha pelo session_id"
        assert inicio_da_sessao("s2", pasta) is None, "iniciado ilegível: None"
        assert inicio_da_sessao("s3", pasta) is None and inicio_da_sessao("", pasta) is None
        assert inicio_da_sessao("s1", pasta / "nao-existe") is None
    print("selftest_inicio_da_sessao: OK")


def selftest_mudados_desde() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = _repo_tmp(tmp, ("feat: base",))
        antes, depois = datetime.now() - timedelta(minutes=5), datetime.now() + timedelta(minutes=5)
        assert "a.txt" in mudados_desde(root, antes), "commit depois do início conta"
        velho = (datetime.now() - timedelta(hours=1)).timestamp()
        (root / "velho.txt").write_text("x", encoding="utf-8")
        os.utime(root / "velho.txt", (velho, velho))
        (root / "novo.txt").write_text("x", encoding="utf-8")
        (root / "a.txt").unlink()
        mudados = mudados_desde(root, datetime.now() - timedelta(minutes=5))
        assert "novo.txt" in mudados and "a.txt" in mudados, mudados
        assert "velho.txt" not in mudados, "edição anterior ao início não conta"
        (root / "decisões.md").write_text("x", encoding="utf-8")
        os.utime(root / "decisões.md", (velho, velho))
        assert "decisões.md" not in mudados_desde(root, antes), "nome acentuado velho não conta (quotePath)"
        (root / "decisões.md").unlink()
        assert mudados_desde(root, depois) == {"a.txt"}, "só o apagado, sem mtime, conta depois do início"
    print("selftest_mudados_desde: OK")


def selftest_cmd_parar() -> None:
    with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as dados:
        root = _repo_tmp(tmp, ("feat: base",))
        original = os.environ.get("CLAUDE_PLUGIN_DATA")
        os.environ["CLAUDE_PLUGIN_DATA"] = dados
        try:
            (Path(dados) / "sessoes").mkdir()
            inicio = (datetime.now() - timedelta(minutes=5)).strftime(FORMATO_HORA)
            (Path(dados) / "sessoes" / "r.json").write_text(
                json.dumps({"session_id": "s1", "iniciado": inicio}), encoding="utf-8")
            entrada = json.dumps({"session_id": "s1", "stop_hook_active": False})

            def rodar(texto: str) -> str:
                saida = io.StringIO()
                with redirect_stdout(saida):
                    assert cmd_parar(root, texto) == 0
                return saida.getvalue()

            assert rodar(entrada) == "", "sem .claude/memory/: silêncio"
            fato = root / DIR_MEMORIA / "agora-x.md"
            fato.parent.mkdir(parents=True)
            fato.write_text("---\nname: agora-x\ndescription: x\nmetadata:\n  type: project\n---\n", encoding="utf-8")
            velho = (datetime.now() - timedelta(hours=1)).timestamp()
            os.utime(fato, (velho, velho))
            assert json.loads(rodar(entrada)) == {"decision": "block", "reason": MOTIVO_PARADA}
            assert rodar(json.dumps({"session_id": "s1", "stop_hook_active": True})) == "", "2ª tentativa para"
            assert rodar("{não é json") == "" and rodar("[]") == "", "entrada ilegível: silêncio"
            assert rodar(json.dumps({"session_id": "sem-registro"})) == "", "sem registro de início: silêncio"
            assert rodar(entrada) == "", "marcador gravado: 2ª parada da sessão, mesmo com stop_hook_active=false"
            for m in (Path(dados) / "sessoes").glob("parada-*.marca"):
                m.unlink()
            os.utime(fato, None)
            assert rodar(entrada) == "", "fato tocado na sessão libera"
            (root / DIR_MEMORIA / "agora-revisão.md").write_text("x", encoding="utf-8")
            (root / "decisões.md").write_text("x", encoding="utf-8")
            os.utime(root / "decisões.md", (velho, velho))
            os.utime(fato, (velho, velho))
            assert rodar(entrada) == "", "fato acentuado tocado conta; arquivo acentuado velho não é trabalho"
        finally:
            if original is None:
                os.environ.pop("CLAUDE_PLUGIN_DATA", None)
            else:
                os.environ["CLAUDE_PLUGIN_DATA"] = original
    print("selftest_cmd_parar: OK")


def selftest_cmd_registrar() -> None:
    with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as dados:
        root, pasta = Path(tmp), Path(dados) / "sessoes"
        original = os.environ.get("CLAUDE_PLUGIN_DATA")
        os.environ["CLAUDE_PLUGIN_DATA"] = dados
        try:
            entrada = json.dumps({"session_id": "s1", "hook_event_name": "SessionStart", "source": "startup"})
            assert cmd_registrar(root, entrada) == 0 and not pasta.exists(), "sem .claude/memory/: nada gravado"
            (root / DIR_MEMORIA).mkdir(parents=True)
            for ruim in ("{não é json", "[]", json.dumps({"session_id": ""}), json.dumps({})):
                assert cmd_registrar(root, ruim) == 0 and not pasta.exists(), ruim
            assert cmd_registrar(root, entrada) == 0
            reg = json.loads((pasta / DIR_REGISTRO_PLUGIN / "s1.json").read_text(encoding="utf-8"))
            assert set(reg) == {"session_id", "iniciado"}, "sem checkout/branch: o guarda-sessao ignora o registro"
            assert inicio_da_sessao("s1", pasta) == datetime.strptime(reg["iniciado"], FORMATO_HORA)
            (pasta / DIR_REGISTRO_PLUGIN / "s1.json").write_text(
                json.dumps({"session_id": "s1", "iniciado": "2026-10-24T09:30:00"}), encoding="utf-8")
            assert cmd_registrar(root, entrada) == 0
            assert inicio_da_sessao("s1", pasta) == datetime(2026, 10, 24, 9, 30), "registro existente não é reescrito"
            (pasta / "guarda.json").write_text(json.dumps(
                {"session_id": "s2", "checkout": "/r", "branch": "b", "iniciado": "2026-10-24T08:00:00"}), encoding="utf-8")
            assert cmd_registrar(root, json.dumps({"session_id": "s2"})) == 0
            assert not (pasta / DIR_REGISTRO_PLUGIN / "s2.json").exists(), "registro do guarda-sessao basta"
            assert cmd_registrar(root, json.dumps({"session_id": "../fora"})) == 0
            assert (pasta / DIR_REGISTRO_PLUGIN / "___fora.json").exists() and not (pasta / "fora.json").exists()
            arquivo_comum = Path(dados) / "nao-e-diretorio"
            arquivo_comum.write_text("x", encoding="utf-8")
            os.environ["CLAUDE_PLUGIN_DATA"] = str(arquivo_comum)
            assert cmd_registrar(root, json.dumps({"session_id": "s3"})) == 0, "não gravável: silêncio"
        finally:
            if original is None:
                os.environ.pop("CLAUDE_PLUGIN_DATA", None)
            else:
                os.environ["CLAUDE_PLUGIN_DATA"] = original
    print("selftest_cmd_registrar: OK")


def selftest_parar_com_registro_do_plugin() -> None:
    with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as dados:
        root = _repo_tmp(tmp, ("feat: base",))
        original = os.environ.get("CLAUDE_PLUGIN_DATA")
        os.environ["CLAUDE_PLUGIN_DATA"] = dados
        try:
            (root / DIR_MEMORIA).mkdir(parents=True)
            assert cmd_registrar(root, json.dumps({"session_id": "s9"})) == 0
            (root / "novo.txt").write_text("x", encoding="utf-8")
            saida = io.StringIO()
            with redirect_stdout(saida):
                assert cmd_parar(root, json.dumps({"session_id": "s9", "stop_hook_active": False})) == 0
            assert json.loads(saida.getvalue())["decision"] == "block", "o Stop mede a partir do registro do plugin"
        finally:
            if original is None:
                os.environ.pop("CLAUDE_PLUGIN_DATA", None)
            else:
                os.environ["CLAUDE_PLUGIN_DATA"] = original
    print("selftest_parar_com_registro_do_plugin: OK")


def selftest() -> None:
    selftest_decidir_parada()
    selftest_inicio_da_sessao()
    selftest_mudados_desde()
    selftest_cmd_parar()
    selftest_cmd_registrar()
    selftest_parar_com_registro_do_plugin()
    print("selftest: OK (decisão, início, mudados, hook, registro)")


def _ler_stdin() -> str:
    try:
        return sys.stdin.read()
    except (OSError, UnicodeDecodeError):
        return ""  # erro de leitura vira entrada ilegível: cmd_parar sai 0 (RNF2)


def main() -> None:
    if "--selftest" in sys.argv:
        selftest()
        return
    alvo = [a for a in sys.argv[1:] if not a.startswith("--")]
    comando = cmd_registrar if "--registrar" in sys.argv else cmd_parar
    sys.exit(comando(Path(alvo[0] if alvo else ".").resolve(), _ler_stdin()))


if __name__ == "__main__":
    main()
