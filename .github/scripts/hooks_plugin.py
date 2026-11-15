#!/usr/bin/env python3
"""Gate do hooks/hooks.json do plugin (delta-134): o harness só carrega o arquivo com o wrapper
{"hooks": {...}}, e todo comando aponta o script por ${CLAUDE_PLUGIN_ROOT} — caminho de máquina ou
de projeto quebraria em todo consumidor. O `claude plugin validate .` não lê o hooks.json (medido
na 2.1.287: só o alvo .claude-plugin/plugin.json lê); este gate não depende da versão do CLI.

Uso:
  hooks_plugin.py [ROOT]     valida ROOT/hooks/hooks.json — sai 1 com achado, um por linha
  hooks_plugin.py --selftest
"""
import json
import re
import sys
import tempfile
from pathlib import Path

ARQUIVO = Path("hooks/hooks.json")
RAIZ_PLUGIN = "${CLAUDE_PLUGIN_ROOT}"
RE_SCRIPT = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([^\"'\s]+)")


def validar(texto: str, root: Path) -> list[str]:
    """Achados do hooks.json; [] quando válido. `root` resolve os scripts apontados."""
    try:
        dados = json.loads(texto)
    except ValueError as e:
        return [f"{ARQUIVO}: JSON inválido ({e})"]
    if not isinstance(dados, dict) or not isinstance(dados.get("hooks"), dict):
        return [f'{ARQUIVO}: sem o wrapper {{"hooks": {{...}}}} — o harness não carrega o arquivo']
    achados = []
    for evento, grupos in dados["hooks"].items():
        for grupo in grupos if isinstance(grupos, list) else [None]:
            ganchos = grupo.get("hooks") if isinstance(grupo, dict) else None
            if not isinstance(ganchos, list):
                achados.append(f"{ARQUIVO}: {evento} tem grupo sem lista 'hooks'")
                continue
            for g in ganchos:
                cmd = g.get("command", "") if isinstance(g, dict) else ""
                if RAIZ_PLUGIN not in cmd:
                    achados.append(f"{ARQUIVO}: {evento} tem comando sem {RAIZ_PLUGIN}: {cmd!r}")
                    continue
                achados += [f"{ARQUIVO}: {evento} aponta script inexistente {s}"
                            for s in RE_SCRIPT.findall(cmd) if not (root / s).is_file()]
    return achados


def checar(root: Path) -> int:
    caminho = root / ARQUIVO
    achados = validar(caminho.read_text(encoding="utf-8"), root) if caminho.is_file() else [f"{ARQUIVO}: ausente"]
    for a in achados:
        print(f"achado: {a}")
    if not achados:
        print(f"{ARQUIVO}: OK")
    return 1 if achados else 0


def selftest() -> int:
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "s").mkdir()
        (root / "s" / "a.py").write_text("", encoding="utf-8")
        cmd = 'python3 \\"${CLAUDE_PLUGIN_ROOT}/s/a.py\\" \\"$CLAUDE_PROJECT_DIR\\"'
        valido = '{"hooks": {"Stop": [{"hooks": [{"type": "command", "command": "%s"}]}]}}' % cmd
        assert validar(valido, root) == [], validar(valido, root)
        sem_wrapper = '{"Stop": [{"hooks": [{"type": "command", "command": "%s"}]}]}' % cmd
        assert "sem o wrapper" in validar(sem_wrapper, root)[0], "mapa de eventos solto não carrega"
        assert "JSON inválido" in validar("{", root)[0]
        projeto = valido.replace("${CLAUDE_PLUGIN_ROOT}", "$CLAUDE_PROJECT_DIR")
        assert "sem ${CLAUDE_PLUGIN_ROOT}" in validar(projeto, root)[0], "caminho de projeto quebra no consumidor"
        assert "inexistente s/b.py" in validar(valido.replace("a.py", "b.py"), root)[0]
        assert "sem lista 'hooks'" in validar('{"hooks": {"Stop": [{}]}}', root)[0]
        assert checar(root) == 1, "hooks.json ausente reprova"
    print("hooks_plugin selftest: OK (7 casos)")
    return 0


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    alvo = [a for a in sys.argv[1:] if not a.startswith("--")]
    return checar(Path(alvo[0] if alvo else ".").resolve())


if __name__ == "__main__":
    sys.exit(main())
