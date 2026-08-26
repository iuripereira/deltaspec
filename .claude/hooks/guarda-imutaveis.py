#!/usr/bin/env python3
"""Hook PreToolUse (delta-061): escrita em histórico imutável pede confirmação.

Defesa em profundidade da regra "arquivado não é podado" (CLAUDE.md, Segurança):
Edit/Write em specs/_archive/ ou debts/_archive/ devolve decisão `ask` — a
escrita legítima (recálculo de link no archive, correção de C13) confirma e
segue; a acidental é pega antes de acontecer. Demais caminhos: silêncio, o
regime normal de permissão vale. Registrado em .claude/settings.json.
"""

import json
import sys

PASTAS_IMUTAVEIS = ("specs/_archive/", "debts/_archive/")


def decidir(file_path: str):
    """Decisão pura: caminho imutável → dict de `ask`; livre → None."""
    normalizado = file_path.replace("\\", "/")
    for pasta in PASTAS_IMUTAVEIS:
        if f"/{pasta}" in f"/{normalizado}":
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "ask",
                    "permissionDecisionReason": (
                        f"escrita em histórico imutável ({pasta}) — confirme se é "
                        "recálculo de link/correção legítima do archive"
                    ),
                }
            }
    return None


def selftest() -> int:
    assert decidir("specs/_archive/055-x/spec.md") is not None, "archive de spec deveria pedir ask"
    assert decidir("/repo/debts/_archive/DEBT_DT-001-x.md") is not None, "archive de débito deveria pedir ask"
    assert decidir("specs/061-least-privilege-skills/spec.md") is None, "delta aberta é caminho livre"
    assert decidir("") is None, "sem caminho, silêncio"
    veredito = decidir("specs/_archive/x.md")
    assert veredito["hookSpecificOutput"]["permissionDecision"] == "ask"
    print("guarda-imutaveis selftest: OK (5 casos)")
    return 0


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    try:
        entrada = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # input inesperado: silêncio, nunca bloqueia a sessão
    caminho = (entrada.get("tool_input") or {}).get("file_path", "")
    veredito = decidir(caminho)
    if veredito:
        print(json.dumps(veredito))
    return 0


if __name__ == "__main__":
    sys.exit(main())
