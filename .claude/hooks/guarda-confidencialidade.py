#!/usr/bin/env python3
"""Gate de identificador de terceiro, nas duas pontas (delta-064).

Este repositório é **privado e é a fonte canônica**; o repositório público é
derivado dele por allowlist (`scripts/publica-dist.sh`, ADR-0036). A
documentação de processo cita casos concretos, e é natural que o nome do caso
escorregue junto com o fato técnico. O gate separa os dois: o fato entra, o
identificador não.

Dois modos, uma única regra de casamento (`achar_nomes`):

- **hook `PreToolUse`** (sem argumento, JSON no stdin) — primeira ponta, no
  momento da escrita. Sem a lista, avisa e libera: degradação graciosa (RNF2).
- **`--varre <dir>`** — segunda ponta, na publicação. Varre a árvore do
  snapshot e sai 1 se achar. Aqui a degradação **se inverte**: quem publica
  sem lista não tem gate, e sem gate não se publica — o chamador aborta.

O registro privado (`specs/`, `debts/`, handoffs) segue com nome real: o
escopo da regra é o allowlist de publicação, não todo arquivo versionado, e
é o que mantém o registro honesto (R7, delta-064).

**A lista de nomes vive FORA do git** (`.claude/nomes-confidenciais.txt`,
gitignored). Versioná-la anularia o propósito — a lista seria a exposição.

Escrita fora do diretório do projeto é ignorada: o alvo é o que pode ser
commitado.

**Bash também passa pelo gate** (DT-212): o hook lê `tool_input.command` e
barra (`deny`) o comando que **escreve** — redirecionamento, `tee`, `sed -i`,
`cp`/`mv` — num caminho do allowlist de publicação, com o mesmo casamento
(`achar_nomes`). O allowlist é lido do array `ALLOWLIST` de
`scripts/publica-dist.sh`, que é o dono; comando só de leitura não é barrado,
e destino indeterminável (`$VAR`, glob) vira `ask`. Limite honesto: comando
que monta o nome em runtime escapa; a defesa principal segue sendo o allowlist
mais a varredura `--varre`.
"""

import json
import os
import re
import shlex
import sys
import tempfile
from pathlib import Path

LISTA_PADRAO = ".claude/nomes-confidenciais.txt"


def carregar_nomes(texto: str) -> list[str]:
    """Parse puro da lista: uma entrada por linha, `#` comenta, vazias caem."""
    nomes = []
    for linha in texto.splitlines():
        entrada = linha.split("#", 1)[0].strip()
        if entrada:
            nomes.append(entrada)
    return nomes


def achar_nomes(conteudo: str, nomes: list[str]) -> list[str]:
    """Puro: nomes da lista presentes no conteúdo (case-insensitive, subpalavra).

    Subpalavra de propósito: a raiz curta do nome precisa casar os derivados
    (`<nome>-projeto`, `Suporte<Nome>`), que é como o identificador realmente
    aparece. O custo é falso positivo em palavra que contenha o nome; o remédio
    é a lista ser específica, não o casamento ser frouxo.
    """
    achados = []
    for nome in nomes:
        if re.search(re.escape(nome), conteudo, re.IGNORECASE):
            achados.append(nome)
    return achados


def varrer_arvore(raiz: Path, nomes: list[str]) -> list[tuple[str, str]]:
    """Puro sobre o disco: `(caminho relativo, nome)` para cada achado na árvore.

    Mesma regra de casamento do hook — `achar_nomes` é o dono. Arquivo que não
    decodifica como texto é pulado: o alvo é documentação e script, e binário
    ilegível não pode travar a publicação de tudo.
    """
    achados = []
    for arquivo in sorted(p for p in raiz.rglob("*") if p.is_file()):
        try:
            conteudo = arquivo.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        relativo = arquivo.relative_to(raiz).as_posix()
        achados.extend((relativo, nome) for nome in achar_nomes(conteudo, nomes))
    return achados


def dentro_do_projeto(caminho: str, raiz: str) -> bool:
    """Puro: o caminho cai sob a raiz do projeto?"""
    if not caminho or not raiz:
        return False
    try:
        Path(os.path.abspath(caminho)).relative_to(os.path.abspath(raiz))
        return True
    except ValueError:
        return False


def decidir(caminho: str, conteudo: str, nomes: list[str], raiz: str):
    """Decisão pura: nome confidencial em caminho do projeto → dict de `deny`."""
    if not nomes or not dentro_do_projeto(caminho, raiz):
        return None
    achados = achar_nomes(conteudo, nomes)
    if not achados:
        return None
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"nome confidencial na escrita ({', '.join(sorted(achados))}) — "
                "este caminho pode ser publicado. Use pseudônimo (`cliente-A`, "
                "`caso de referência`, `um repo consumidor`) e preserve só o "
                "fato técnico. Se a exposição for deliberada e autorizada, "
                f"retire o nome de {LISTA_PADRAO}."
            ),
        }
    }


ARQUIVO_ALLOWLIST = "scripts/publica-dist.sh"
SEPARADORES = {";", "&&", "||", "|", "&"}
REDIRECIONAMENTOS = {">", ">>", ">|"}
INDETERMINADO = re.compile(r"[$`*?\[{]")


def carregar_allowlist(texto: str) -> list[str]:
    """Parse puro do array `ALLOWLIST=( ... )` do `publica-dist.sh` (o dono)."""
    m = re.search(r"^ALLOWLIST=\((.*?)^\)", texto, re.MULTILINE | re.DOTALL)
    if not m:
        return []
    return [
        e
        for e in (l.split("#", 1)[0].strip() for l in m.group(1).splitlines())
        if e
    ]


def alvos_de_escrita(comando: str) -> tuple[list[str], bool]:
    """Puro: `(destinos de escrita, houve destino indeterminável)` do comando.

    Heurística: redirecionamento, `tee`, `sed -i`, `cp`/`mv`/`install`.
    Heredoc/printf/echo entram pelo `>` que os redireciona.
    """
    lexer = shlex.shlex(comando.replace("\n", " ; "), posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    try:
        tokens = list(lexer)
    except ValueError:
        return [], True  # aspas abertas etc.: não dá para saber
    segmentos, atual = [], []
    for t in tokens:
        if t in SEPARADORES:
            segmentos.append(atual)
            atual = []
        else:
            atual.append(t)
    segmentos.append(atual)

    alvos = []
    for seg in segmentos:
        redirecionados = [seg[i + 1] for i, t in enumerate(seg[:-1]) if t in REDIRECIONAMENTOS]
        alvos.extend(redirecionados)
        if not seg:
            continue
        cmd = os.path.basename(seg[0])
        # o alvo de um redirecionamento já entrou acima; tira-o dos argumentos
        args = [
            a for a in seg[1:]
            if not a.startswith("-") and a not in REDIRECIONAMENTOS and a not in redirecionados
        ]
        if cmd == "tee":
            alvos.extend(args)
        elif cmd == "sed" and any(a.startswith("-i") or a == "--in-place" for a in seg[1:]):
            alvos.extend(args)
        elif cmd in ("cp", "mv", "install") and args:
            alvos.append(args[-1])
    alvos = [a for a in alvos if not a.startswith("&")]  # `2>&1`
    return alvos, any(INDETERMINADO.search(a) for a in alvos)


def no_allowlist(caminho: str, allowlist: list[str], raiz: str) -> bool:
    """Puro: o caminho cai sob uma entrada do allowlist de publicação?"""
    completo = os.path.join(raiz, os.path.expanduser(caminho))
    if not dentro_do_projeto(completo, raiz):
        return False
    rel = os.path.relpath(os.path.abspath(completo), os.path.abspath(raiz))
    return any(rel == e or rel.startswith(e + "/") for e in allowlist)


def decidir_bash(comando: str, nomes: list[str], allowlist: list[str], raiz: str):
    """Decisão pura do Bash: escreve nome confidencial em caminho publicado → `deny`.

    Reusa `decidir` (e, por ela, `achar_nomes`). Só leitura passa; destino
    indeterminável com nome no comando pede `ask`.
    """
    if not comando or not nomes or not allowlist or not achar_nomes(comando, nomes):
        return None
    alvos, incerto = alvos_de_escrita(comando)
    for alvo in alvos:
        if no_allowlist(alvo, allowlist, raiz):
            return decidir(os.path.join(raiz, os.path.expanduser(alvo)), comando, nomes, raiz)
    if incerto:
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "ask",
                "permissionDecisionReason": (
                    "nome confidencial no comando e destino de escrita indeterminável — "
                    "confira que não grava em caminho publicado."
                ),
            }
        }
    return None


def selftest() -> int:
    nomes = carregar_nomes("# comentário\nAcme\n\n  Globex  # inline\n")
    assert nomes == ["Acme", "Globex"], nomes

    raiz = "/repo"
    assert decidir("/repo/CHANGELOG.md", "validado na Acme", nomes, raiz) is not None
    assert decidir("/repo/CHANGELOG.md", "validado no caso X", nomes, raiz) is None
    # subpalavra: repo derivado do nome precisa casar
    assert decidir("/repo/x.md", "acme-viagens", nomes, raiz) is not None
    # sufixo separado da raiz NÃO contém a raiz, logo não casa por subpalavra —
    # é assim que dois derivados atravessaram o gate até a delta-066. A correção
    # é de dado, não de código: o sufixo entra na lista como entrada própria.
    assert decidir("/repo/x.md", "viagens", nomes, raiz) is None
    nomes_com_sufixo = carregar_nomes("Acme\nviagens\n")
    assert decidir("/repo/x.md", "viagens", nomes_com_sufixo, raiz) is not None
    # case-insensitive
    assert decidir("/repo/x.md", "SuporteACME", nomes, raiz) is not None
    # fora do projeto: silêncio (scratchpad, rascunho local)
    assert decidir("/tmp/scratch/relatorio.md", "Acme", nomes, raiz) is None
    # lista ausente: degrada, nunca bloqueia
    assert decidir("/repo/CHANGELOG.md", "Acme", [], raiz) is None
    veredito = decidir("/repo/a.md", "Globex", nomes, raiz)
    assert veredito["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "Globex" in veredito["hookSpecificOutput"]["permissionDecisionReason"]

    assert achar_nomes("nada aqui", nomes) == []
    assert dentro_do_projeto("/repo/a.md", "/repo") is True
    assert dentro_do_projeto("/outro/a.md", "/repo") is False
    assert dentro_do_projeto("", "/repo") is False

    # --- modo varredura (delta-064): a árvore publicável passa pelo mesmo casamento ---
    with tempfile.TemporaryDirectory() as tmp:
        raiz_varre = Path(tmp)
        (raiz_varre / "sub").mkdir()
        (raiz_varre / "limpo.md").write_text("só fato técnico", encoding="utf-8")
        assert varrer_arvore(raiz_varre, nomes) == []

        (raiz_varre / "sub" / "sujo.md").write_text("validado na Acme", encoding="utf-8")
        achados = varrer_arvore(raiz_varre, nomes)
        assert achados == [("sub/sujo.md", "Acme")], achados

        # binário e ilegível não derrubam a varredura
        (raiz_varre / "bin.png").write_bytes(b"\x89PNG\x00\xff\xfeAcme")
        assert [c for c, _ in varrer_arvore(raiz_varre, nomes)] == ["sub/sujo.md"]

        # lista vazia não acha nada, mas quem decide publicar é o chamador
        assert varrer_arvore(raiz_varre, []) == []

    # --- Bash (DT-212) ---
    al = ["skills", "CHANGELOG.md", ".claude/hooks"]

    def bash(cmd):
        return decidir_bash(cmd, nomes, al, raiz)

    def nega(cmd):
        v = bash(cmd)
        return v is not None and v["hookSpecificOutput"]["permissionDecision"] == "deny"

    assert nega("echo 'validado na Acme' >> CHANGELOG.md")
    assert nega("cat > skills/x/SKILL.md <<'EOF'\nfeito na Acme\nEOF")
    assert nega("printf 'Acme' | tee -a /repo/CHANGELOG.md")
    assert nega("sed -i 's/caso/Acme/' skills/x/a.md")
    assert nega("cp rascunho-acme.md skills/x/a.md")
    assert nega("cd /repo && echo Globex > .claude/hooks/h.py")
    # só leitura: cita o nome e passa
    assert bash("grep -rn Acme skills/") is None
    assert bash("cat CHANGELOG.md | grep Acme") is None
    assert bash("git log --grep=Acme") is None
    assert bash("grep Acme skills/a.md 2>&1") is None
    # escrita fora do allowlist: nome real é permitido
    assert bash("echo Acme >> specs/001/spec.md") is None
    assert bash("cat > debts/ativos/x.md <<'EOF'\nAcme\nEOF") is None
    assert bash("echo Acme > /tmp/x.md") is None
    # sem nome, sem comando, sem lista, sem allowlist: libera
    assert bash("echo ok >> CHANGELOG.md") is None
    assert bash("") is None
    assert decidir_bash("echo Acme >> CHANGELOG.md", [], al, raiz) is None
    assert decidir_bash("echo Acme >> CHANGELOG.md", nomes, [], raiz) is None
    # destino indeterminável com nome: ask
    v = bash("echo Acme > $DESTINO")
    assert v["hookSpecificOutput"]["permissionDecision"] == "ask"
    assert carregar_allowlist("X=1\nALLOWLIST=(\n  skills\n  README.md # c\n)\nY=2\n") == ["skills", "README.md"]

    print("guarda-confidencialidade selftest: OK")
    return 0


def localizar_lista() -> Path:
    """I/O: a lista mora no repo (gitignored), nunca na árvore varrida."""
    raiz = os.environ.get("CLAUDE_PROJECT_DIR", "")
    return Path(raiz) / LISTA_PADRAO if raiz else Path(LISTA_PADRAO)


def varrer(destino: str) -> int:
    """I/O do modo publicação: 0 = árvore limpa, 1 = achado ou gate indisponível.

    Ao contrário do hook, lista ausente aqui **reprova**. Publicar é porta de
    mão única; sem gate, não se atravessa.
    """
    lista = localizar_lista()
    if not lista.is_file():
        print(
            f"guarda-confidencialidade: {LISTA_PADRAO} ausente — sem gate não se publica",
            file=sys.stderr,
        )
        return 1

    nomes = carregar_nomes(lista.read_text(encoding="utf-8"))
    if not nomes:
        print(f"guarda-confidencialidade: {LISTA_PADRAO} vazia — sem gate não se publica", file=sys.stderr)
        return 1

    achados = varrer_arvore(Path(destino), nomes)
    if not achados:
        print(f"guarda-confidencialidade: árvore limpa ({len(nomes)} termos conferidos)")
        return 0

    for caminho, nome in achados:
        print(f"guarda-confidencialidade: {caminho}: {nome}", file=sys.stderr)
    print(f"guarda-confidencialidade: {len(achados)} achado(s) — publicação abortada", file=sys.stderr)
    return 1


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    if "--varre" in sys.argv:
        return varrer(sys.argv[sys.argv.index("--varre") + 1])
    try:
        entrada = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # input inesperado: silêncio, nunca bloqueia a sessão

    raiz = os.environ.get("CLAUDE_PROJECT_DIR", "")
    lista = Path(raiz) / LISTA_PADRAO if raiz else Path(LISTA_PADRAO)
    if not lista.is_file():
        print(f"guarda-confidencialidade: {LISTA_PADRAO} ausente — gate inativo", file=sys.stderr)
        return 0

    nomes = carregar_nomes(lista.read_text(encoding="utf-8"))
    tool_input = entrada.get("tool_input") or {}
    if entrada.get("tool_name") == "Bash":
        arq = Path(raiz) / ARQUIVO_ALLOWLIST if raiz else Path(ARQUIVO_ALLOWLIST)
        if not arq.is_file():
            return 0  # sem o dono do allowlist: degrada em silêncio
        veredito = decidir_bash(
            tool_input.get("command") or "", nomes, carregar_allowlist(arq.read_text(encoding="utf-8")), raiz
        )
        if veredito:
            print(json.dumps(veredito))
        return 0
    caminho = tool_input.get("file_path", "")
    # Write manda `content`; Edit manda `new_string`.
    conteudo = f"{tool_input.get('content', '')}\n{tool_input.get('new_string', '')}"

    veredito = decidir(caminho, conteudo, nomes, raiz)
    if veredito:
        print(json.dumps(veredito))
    return 0


if __name__ == "__main__":
    sys.exit(main())
