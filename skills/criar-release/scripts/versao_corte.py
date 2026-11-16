#!/usr/bin/env python3
"""Pré-voo da versão no corte de release (delta-117).

A versão é o único item que o humano decide em `/deltaspec:criar-release X.Y.Z`;
este gate confere que a decisão cabe na tríade de release (CLAUDE.md):

  - a pedida é SemVer 2.0.0 estrito (sem zero à esquerda) e maior que a última
    tag `vX.Y.Z` do repo;
  - a pedida é o SUCESSOR IMEDIATO da última tag no nível do bump — patch
    X.Y.(Z+1), minor X.(Y+1).0, major (X+1).0.0; pular número ou deixar de
    zerar os componentes inferiores reprova (SemVer §7/§8);
  - o bump pedido paga o que os commits desde a última tag exigem —
    `!` ou rodapé `BREAKING CHANGE:` = MAJOR, `feat` = MINOR, o resto = PATCH;
    em `0.y.z` o BREAKING vale MINOR (SemVer 2.0.0 §4: sem promessa de
    estabilidade antes da 1.0.0); bump maior que o exigido passa (decisão do
    humano, não do gate);
  - `--hotfix`: a pedida tem de ser exatamente o sucessor de PATCH, e os commits
    do conserto não podem exigir mais que PATCH;
  - repo sem tag nenhuma aceita qualquer SemVer (caso real: consumidor com
    zero tags cortando a primeira release) — menos no `--hotfix`, que pressupõe
    uma release anterior.

Tags: só `vX.Y.Z` estrito conta como última. Tag de pré-release (`v1.0.0-rc.1`)
não conta; tag que parece versão fora do formato (`1.5.0`, `v2.0`, `v1.02.0`) é
ignorada COM aviso — senão o repo passaria calado por "primeira release". Nome
que não parece versão (`nightly`) é ignorado em silêncio.

Início da conta: a última tag. Primeiro corte depois da adoção do fluxo, com
histórico `develop→main` por squash: a tag está num commit de pai único e chegou
à develop por back-merge, então `tag..develop` ainda lista os commits que o
squash já lançou (os da develop nunca viram ancestrais da tag). Nesse caso a
conta começa no back-merge que trouxe a tag — o merge commit da
primeira-paternidade da base cujo segundo pai contém a tag e o primeiro não — e
a saída diz isso. Tag em merge commit (o fluxo vigente) conta desde a tag: ali o
que entrou na develop entre o corte e o sync ainda não foi lançado. `--desde REF`
força o início. A saída sempre diz quantos commits entraram na conta.
Limite conhecido: se a última tag do fluxo antigo foi um hotfix por squash
direto na main, o back-merge não marca o que a develop já tinha lançado — a
conta sai curta; o aviso nomeia o início, e `--desde` corrige.

Uso: versao_corte.py X.Y.Z [--base REF] [--raiz DIR] [--desde REF] [--hotfix]
     (defaults: --base HEAD, --raiz .)
     versao_corte.py --selftest
Exit 0 = ok · 1 = reprova (versão ≤ última tag, não é o sucessor imediato,
bump abaixo do exigido — a mensagem cita o subject que o exige —, hotfix fora de
PATCH) · 2 = uso inválido (versão fora do SemVer, argumento ausente ou
desconhecido, ref inexistente).

Só os subjects e rodapés dos commits entram na conta; merge commits ficam de
fora (`--no-merges`). Commit fora do padrão Conventional Commits conta como
PATCH — quem reprova a forma é o job `commits`, não este gate.
"""
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

# espelho — dono canonical-rules.md (deps.toml commit-tipos)
TIPOS_COMMIT = ("feat", "fix", "docs", "refactor", "chore", "ci", "test", "style", "perf", "build", "revert")

NIVEIS = ("patch", "minor", "major")  # ordem crescente; o índice é o peso
_NUMERO = r"(0|[1-9]\d*)"  # SemVer §2: inteiro não negativo, sem zero à esquerda
RE_SEMVER = re.compile(rf"^{_NUMERO}\.{_NUMERO}\.{_NUMERO}$")
RE_TAG = re.compile(rf"^v{_NUMERO}\.{_NUMERO}\.{_NUMERO}$")
RE_TAG_PRE_RELEASE = re.compile(rf"^v{_NUMERO}\.{_NUMERO}\.{_NUMERO}-[0-9A-Za-z.-]+$")
RE_PARECE_VERSAO = re.compile(r"^v?\d")  # tag que tenta ser versão e não casa RE_TAG → aviso
RE_SUBJECT = re.compile(r"^(?P<tipo>" + "|".join(TIPOS_COMMIT) + r")(\([^)]*\))?(?P<bang>!)?:")
RE_RODAPE_BREAKING = re.compile(r"^BREAKING[ -]CHANGE:", re.M)
SEPARADOR_MENSAGENS = "\x00"  # NUL: o git escreve com %x00, já que argv não carrega o byte
TAMANHO_SHA_CURTO = 7


# ── puras ────────────────────────────────────────────────────────────────────

def parse_versao(texto: str):
    """'1.57.0' → (1, 57, 0); qualquer outra forma (inclusive zero à esquerda) → None."""
    m = RE_SEMVER.match(texto.strip())
    return tuple(int(g) for g in m.groups()) if m else None


def eh_semver(texto: str) -> bool:
    return parse_versao(texto) is not None


def classificar_tags(nomes):
    """(maior 'vX.Y.Z' por ordem numérica ou '', avisos). Pré-release não conta
    como última; nome que parece versão fora do formato é ignorado com aviso."""
    versoes, avisos = [], []
    for nome in (n.strip() for n in nomes):
        m = RE_TAG.match(nome)
        if m:
            versoes.append(tuple(int(g) for g in m.groups()))
        elif RE_TAG_PRE_RELEASE.match(nome):
            avisos.append(f"tag de pré-release {nome} não conta como última")
        elif RE_PARECE_VERSAO.match(nome):
            avisos.append(f"tag {nome} fora do formato vX.Y.Z — ignorada")
    maior = "v{}.{}.{}".format(*max(versoes)) if versoes else ""
    return maior, avisos


def nivel_do_commit(mensagem: str) -> str:
    """Nível que UMA mensagem de commit (subject + corpo) exige."""
    subject = mensagem.strip().splitlines()[0] if mensagem.strip() else ""
    m = RE_SUBJECT.match(subject)
    if (m and m.group("bang")) or RE_RODAPE_BREAKING.search(mensagem):
        return "major"
    if m and m.group("tipo") == "feat":
        return "minor"
    return "patch"


def bump_exigido(mensagens, ultima: str = ""):
    """(nível, subject responsável) do maior bump que a lista de mensagens exige.
    Em 0.y.z o MAJOR rebaixa para MINOR. Lista vazia → ('patch', '')."""
    exigido, culpado = "patch", ""
    for mensagem in mensagens:
        nivel = nivel_do_commit(mensagem)
        if NIVEIS.index(nivel) > NIVEIS.index(exigido):
            exigido, culpado = nivel, mensagem.strip().splitlines()[0]
    versao_ultima = parse_versao(ultima.lstrip("v")) if ultima else None
    if exigido == "major" and versao_ultima and versao_ultima[0] == 0:
        exigido = "minor"
    return exigido, culpado


def sucessores(ultima: tuple) -> dict:
    """Sucessor imediato por nível (SemVer §6-§8: sobe um, zera os inferiores)."""
    x, y, z = ultima
    return {"patch": (x, y, z + 1), "minor": (x, y + 1, 0), "major": (x + 1, 0, 0)}


def _rotulo(versao: tuple) -> str:
    return ".".join(str(p) for p in versao)


def validar(pedida: str, ultima: str, exigido: str, hotfix: bool = False):
    """Veredito puro (ok, motivo). `ultima` é 'vX.Y.Z' ou '' (sem tag)."""
    v_pedida = parse_versao(pedida)
    if v_pedida is None:
        return False, f"versão pedida não é SemVer: {pedida!r}"
    if not ultima:
        if hotfix:
            return False, f"{pedida}: hotfix pressupõe uma release anterior (tag vX.Y.Z), e o repo não tem — corte uma release normal"
        return True, f"{pedida}: sem tag anterior — primeira release, qualquer SemVer serve"
    v_ultima = parse_versao(ultima.lstrip("v"))
    if v_pedida <= v_ultima:
        return False, f"{pedida} não é maior que a última tag {ultima}"
    por_nivel = sucessores(v_ultima)
    pedido = next((n for n, v in por_nivel.items() if v == v_pedida), None)
    if pedido is None:
        validos = ", ".join(f"{_rotulo(v)} ({n})" for n, v in por_nivel.items())
        return False, f"{pedida} não é sucessor imediato de {ultima} — os válidos são {validos}"
    if hotfix and pedido != "patch":
        return False, f"hotfix é PATCH: sobre {ultima} a versão é {_rotulo(por_nivel['patch'])}, não {pedida}"
    if NIVEIS.index(pedido) < NIVEIS.index(exigido):
        return False, f"{pedida} é bump {pedido} sobre {ultima}, mas os commits exigem {exigido}"
    return True, f"{pedida} sobre {ultima}: bump {pedido} paga o {exigido} exigido"


# ── I/O ──────────────────────────────────────────────────────────────────────

def _git(raiz: Path, *args) -> str:
    return subprocess.run(["git", "-C", str(raiz), *args], capture_output=True, text=True, check=True).stdout


def tags_do_repo(raiz: Path):
    return _git(raiz, "tag", "--list").split()


def eh_ancestral(raiz: Path, a: str, b: str) -> bool:
    """`git merge-base --is-ancestor`: 0 = sim, 1 = não, outro = erro (ref inexistente)."""
    r = subprocess.run(["git", "-C", str(raiz), "merge-base", "--is-ancestor", a, b], capture_output=True, text=True)
    if r.returncode not in (0, 1):
        raise subprocess.CalledProcessError(r.returncode, r.args, r.stdout, r.stderr)
    return r.returncode == 0


def tag_em_merge_commit(raiz: Path, tag: str) -> bool:
    """A tag está num merge commit (fluxo vigente: release/hotfix entram por merge)?"""
    return len(_git(raiz, "rev-list", "--parents", "-n", "1", tag).split()) > 2


def back_merge_da_tag(raiz: Path, tag: str, base: str):
    """SHA do merge commit que trouxe a tag para a base: na primeira-paternidade de
    `base`, o segundo pai contém a tag e o primeiro não. Na primeira-paternidade só
    um merge satisfaz isso (depois dele a tag está em todo primeiro pai); None se a
    tag já estava na própria primeira-paternidade (perfil sem develop, hotfix)."""
    # ponytail: dois `merge-base` por merge da base desde a tag; o back-merge fica
    # entre os primeiros do --reverse — só base sem nenhum paga a varredura inteira.
    for linha in _git(raiz, "rev-list", "--first-parent", "--merges", "--parents", "--reverse",
                      f"{tag}..{base}").splitlines():
        partes = linha.split()
        if len(partes) >= 3 and eh_ancestral(raiz, tag, partes[2]) and not eh_ancestral(raiz, tag, partes[1]):
            return partes[0]
    return None


def inicio_da_contagem(raiz: Path, ultima: str, base: str, desde: str):
    """(início da conta, aviso ou ''). Início '' = todo o histórico até a base."""
    if desde:
        return desde, f"início forçado por --desde {desde}"
    if not ultima:
        return "", ""
    if not eh_ancestral(raiz, ultima, base):
        return ultima, (f"a última tag {ultima} não é ancestral de {base} — a conta pega {ultima}..{base} "
                        f"inteiro; se o bump exigido vier inflado, force o início com --desde REF")
    if tag_em_merge_commit(raiz, ultima):
        return ultima, ""
    back_merge = back_merge_da_tag(raiz, ultima, base)
    if not back_merge:
        return ultima, ""  # tag na primeira-paternidade da base (perfil sem develop, hotfix)
    subject = _git(raiz, "log", "-1", "--format=%s", back_merge).strip()
    return back_merge, (f"a última tag {ultima} está num commit de pai único (squash) que chegou a {base} por "
                        f"back-merge — primeiro corte depois da adoção; a conta começa no back-merge "
                        f"{back_merge[:TAMANHO_SHA_CURTO]} {subject!r} (--desde REF força outro início)")


def mensagens_desde(raiz: Path, inicio: str, base: str):
    """Mensagens completas (subject + corpo) dos commits não-merge em inicio..base;
    sem início, todo o histórico até base."""
    intervalo = f"{inicio}..{base}" if inicio else base
    saida = _git(raiz, "log", "--no-merges", "--format=%B%x00", intervalo)
    return [m.strip() for m in saida.split(SEPARADOR_MENSAGENS) if m.strip()]


# ── selftest ─────────────────────────────────────────────────────────────────

def _selftest_puro() -> int:
    casos = 0

    def caso(condicao, mensagem):
        nonlocal casos
        assert condicao, mensagem
        casos += 1

    caso(eh_semver("1.57.0") and eh_semver("0.0.0"), "SemVer estrito aceita 0")
    caso(not eh_semver("v1.57.0") and not eh_semver("1.57"), "sem 'v', três componentes")
    caso(not eh_semver("1.03.0") and not eh_semver("01.0.0"), "zero à esquerda não é SemVer (§2)")

    caso(classificar_tags(["v1.9.0", "v1.10.1", "v1.10.0", "release-3", "nightly"]) == ("v1.10.1", []),
         "ordem numérica, não alfabética; nome que não parece versão some calado")
    maior, avisos = classificar_tags(["v1.2.3", "v1.3.0-rc.1", "1.5.0", "v2.0", "v1.02.0"])
    caso(maior == "v1.2.3", "pré-release e fora do formato não contam como última")
    caso(len(avisos) == 4 and "pré-release" in avisos[0] and all("fora do formato" in a for a in avisos[1:]),
         "cada tag ignorada gera aviso")
    caso(classificar_tags(["banana"]) == ("", []), "sem tag v* não há maior")

    caso(bump_exigido(["feat(x): nova coisa", "fix(y): conserto"], "v1.2.3") == ("minor", "feat(x): nova coisa"), "feat → minor")
    caso(bump_exigido(["fix(y): conserto", "docs: texto"], "v1.2.3") == ("patch", ""), "fix → patch")
    caso(bump_exigido(["feat(x)!: quebra"], "v1.2.3")[0] == "major", "'!' antes de ':' → major")
    caso(bump_exigido(["feat!: sem escopo"], "v1.2.3")[0] == "major", "'!' sem escopo → major")
    caso(bump_exigido(["refactor(x): muda\n\nBREAKING CHANGE: api"], "v1.2.3")[0] == "major", "rodapé BREAKING CHANGE → major")
    caso(bump_exigido(["refactor(x): muda\n\nBREAKING-CHANGE: api"], "v1.2.3")[0] == "major", "rodapé BREAKING-CHANGE → major")
    caso(bump_exigido(["feat(x)!: quebra"], "v0.21.1") == ("minor", "feat(x)!: quebra"), "0.y.z: BREAKING vale minor")
    caso(bump_exigido([], "v1.2.3") == ("patch", ""), "sem commit → patch")
    caso(bump_exigido(["texto solto sem tipo"], "v1.2.3")[0] == "patch", "fora do padrão conta como patch")

    ok, motivo = validar("1.2.3", "v1.2.3", "patch")
    caso(not ok and "não é maior" in motivo, "pedida igual à última reprova")
    ok, _ = validar("1.2.2", "v1.2.3", "patch")
    caso(not ok, "pedida menor que a última reprova")
    ok, motivo = validar("1.2.4", "v1.2.3", "minor")
    caso(not ok and "exigem minor" in motivo, "patch pedido com minor exigido reprova")
    ok, _ = validar("1.3.0", "v1.2.3", "minor")
    caso(ok, "bump igual ao exigido passa")
    ok, _ = validar("2.0.0", "v1.2.3", "patch")
    caso(ok, "bump maior que o exigido passa")
    ok, _ = validar("0.22.0", "v0.21.1", "minor")
    caso(ok, "0.y.z: BREAKING pago com minor")
    for errada in ("1.3.7", "2.1.0", "1.4.0", "1.2.5", "3.0.0"):
        ok, motivo = validar(errada, "v1.2.3", "patch")
        caso(not ok and "sucessor imediato" in motivo and "1.2.4 (patch)" in motivo, f"{errada} não é sucessor imediato")
    ok, motivo = validar("0.1.0", "", "major")
    caso(ok and "primeira release" in motivo, "sem tag aceita qualquer SemVer")
    ok, _ = validar("1.2", "v1.2.3", "patch")
    caso(not ok, "pedida fora do SemVer reprova")

    ok, _ = validar("1.2.4", "v1.2.3", "patch", hotfix=True)
    caso(ok, "hotfix com o sucessor de patch passa")
    for errada in ("1.3.0", "2.0.0"):
        ok, motivo = validar(errada, "v1.2.3", "patch", hotfix=True)
        caso(not ok and "hotfix é PATCH" in motivo and "1.2.4" in motivo, f"hotfix {errada} reprova")
    ok, motivo = validar("1.2.4", "v1.2.3", "minor", hotfix=True)
    caso(not ok and "exigem minor" in motivo, "hotfix com feat no conserto reprova")
    ok, motivo = validar("0.1.0", "", "patch", hotfix=True)
    caso(not ok and "release anterior" in motivo, "hotfix sem tag reprova")
    return casos


def _selftest_git() -> int:
    """Repos git temporários (sem rede) exercitando o I/O e a CLI: --no-merges,
    corpo multilinha pelo %x00, exit 0/1/2, --hotfix, back-merge da adoção,
    --desde e tags fora do formato."""
    casos = 0
    env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
           "GIT_AUTHOR_NAME": "selftest", "GIT_AUTHOR_EMAIL": "selftest@sdd",
           "GIT_COMMITTER_NAME": "selftest", "GIT_COMMITTER_EMAIL": "selftest@sdd"}

    def caso(condicao, mensagem):
        nonlocal casos
        assert condicao, mensagem
        casos += 1

    with tempfile.TemporaryDirectory() as d:
        def git(raiz, *args):
            return subprocess.run(["git", "-C", str(raiz), *args], check=True, capture_output=True,
                                  text=True, env=env).stdout.strip()

        def commit(raiz, mensagem):
            git(raiz, "commit", "-q", "--allow-empty", "-m", mensagem)

        def cli(raiz, *args):
            r = subprocess.run([sys.executable, __file__, "--raiz", str(raiz), *args],
                               capture_output=True, text=True, env=env)
            return r.returncode, r.stdout + r.stderr

        # 1) tag + merge --no-ff com feat dentro + commit de corpo multilinha
        a = Path(d) / "a"
        git(d, "init", "-q", "-b", "main", str(a))
        commit(a, "chore: início")
        git(a, "tag", "v1.0.0")
        commit(a, "fix: a\n\ncorpo de\nvárias linhas")
        git(a, "switch", "-q", "-c", "feature")
        commit(a, "feat: f")
        git(a, "switch", "-q", "main")
        git(a, "merge", "-q", "--no-ff", "feature", "-m", "Merge branch 'feature'")
        mensagens = mensagens_desde(a, "v1.0.0", "HEAD")
        caso(len(mensagens) == 2 and not any(m.startswith("Merge") for m in mensagens), "--no-merges tira o merge commit")
        caso("corpo de\nvárias linhas" in "".join(mensagens), "corpo multilinha sobrevive ao separador NUL")
        rc, saida = cli(a, "1.1.0")
        caso(rc == 0 and "2 commit(s) na conta" in saida, f"feat pago com minor → 0 ({rc}: {saida})")
        rc, saida = cli(a, "1.0.1")
        caso(rc == 1 and "exigem minor" in saida and "'feat: f'" in saida, f"patch com feat → 1 citando o subject ({rc})")
        rc, _ = cli(a, "1.0.0")
        caso(rc == 1, "versão igual à última tag → 1 (D2)")
        rc, saida = cli(a, "1.1.1")
        caso(rc == 1 and "sucessor imediato" in saida, "não sucessor → 1")
        rc, _ = cli(a, "1.01.0")
        caso(rc == 2, "zero à esquerda → 2 (uso inválido)")
        rc, _ = cli(a, "1.1.0", "--base", "nao-existe")
        caso(rc == 2, "--base inexistente → 2")
        rc, _ = cli(a, "1.1.0", "--desde", "nao-existe")
        caso(rc == 2, "--desde inexistente → 2")
        rc, saida = cli(a, "1.1.0", "--base")
        caso(rc == 2 and "exige um valor" in saida, "flag sem valor → 2")
        rc, saida = cli(a, "1.0.1", "--hotfix")
        caso(rc == 1 and "exigem minor" in saida, "hotfix com feat no intervalo → 1")
        rc, saida = cli(a, "1.0.1", "--hotfix", "--base", "v1.0.0")
        caso(rc == 0 and "0 commit(s)" in saida, "hotfix recém-cortado da tag (intervalo vazio) → 0")
        rc, saida = cli(a, "1.1.0", "--hotfix", "--base", "v1.0.0")
        caso(rc == 1 and "hotfix é PATCH" in saida, "hotfix minor → 1")
        commit(a, "refactor: x\n\nBREAKING-CHANGE: api")
        rc, saida = cli(a, "1.1.0")
        caso(rc == 1 and "exigem major" in saida, "rodapé BREAKING-CHANGE no corpo → major")

        # 2) adoção: develop com BREAKING, squash na main + tag, back-merge, fix novo
        b = Path(d) / "b"
        git(d, "init", "-q", "-b", "main", str(b))
        commit(b, "chore: início")
        git(b, "switch", "-q", "-c", "develop")
        commit(b, "feat(x)!: api nova (#1)")
        commit(b, "fix: coisa (#2)")
        git(b, "switch", "-q", "main")
        commit(b, "chore(release): 1.0.0 (#3)")  # o squash: commit novo, sem ancestralidade
        git(b, "tag", "v1.0.0")
        git(b, "switch", "-q", "develop")
        git(b, "merge", "-q", "--no-ff", "main", "-m", "Merge branch 'main' into develop")
        commit(b, "fix: correção nova (#4)")
        rc, saida = cli(b, "1.0.1", "--base", "develop")
        caso(rc == 0 and "back-merge" in saida and "1 commit(s) na conta" in saida,
             f"primeiro corte pós-adoção conta desde o back-merge (D4) → 0 ({rc}: {saida})")
        git(b, "switch", "-q", "main")
        commit(b, "docs: direto na main (#5)")
        git(b, "switch", "-q", "develop")
        git(b, "merge", "-q", "--no-ff", "main", "-m", "Merge branch 'main' into develop")
        rc, saida = cli(b, "1.0.1", "--base", "develop")
        caso(rc == 0 and "2 commit(s) na conta" in saida,
             f"back-merge posterior não encurta a conta: vale o que trouxe a tag ({rc}: {saida})")
        primeiro = git(b, "rev-list", "--max-parents=0", "develop")
        rc, saida = cli(b, "1.0.1", "--base", "develop", "--desde", primeiro)
        caso(rc == 1 and "exigem major" in saida and "--desde" in saida, "--desde força o início")

        # 3) fluxo vigente: tag no merge commit da release; feat entra na develop
        #    depois do corte e antes do sync — ainda não lançado, tem de contar
        e = Path(d) / "e"
        git(d, "init", "-q", "-b", "main", str(e))
        commit(e, "chore: início")
        git(e, "switch", "-q", "-c", "develop")
        commit(e, "fix: a (#1)")
        git(e, "switch", "-q", "-c", "release/1.0.1")
        git(e, "switch", "-q", "develop")
        commit(e, "feat: b depois do corte (#2)")
        git(e, "switch", "-q", "main")
        git(e, "merge", "-q", "--no-ff", "release/1.0.1", "-m", "Merge pull request #3 from release/1.0.1")
        git(e, "tag", "v1.0.1")
        git(e, "switch", "-q", "develop")
        git(e, "merge", "-q", "--no-ff", "main", "-m", "Merge branch 'main' into develop")
        commit(e, "fix: c (#4)")
        rc, saida = cli(e, "1.0.2", "--base", "develop")
        caso(rc == 1 and "exigem minor" in saida and "back-merge" not in saida,
             f"tag em merge commit conta desde a tag, com o feat pós-corte ({rc}: {saida})")
        rc, saida = cli(e, "1.1.0", "--base", "develop")
        caso(rc == 0 and "2 commit(s) na conta" in saida, f"minor paga o feat pós-corte ({rc}: {saida})")

        # 4) tags fora do formato: ignoradas com aviso, e o repo segue sem última
        c = Path(d) / "c"
        git(d, "init", "-q", "-b", "main", str(c))
        commit(c, "chore: início")
        git(c, "tag", "1.5.0")
        git(c, "tag", "v2.0.0-rc.1")
        rc, saida = cli(c, "0.0.1")
        caso(rc == 0 and "1.5.0 fora do formato" in saida and "pré-release v2.0.0-rc.1" in saida,
             f"tag sem 'v' e pré-release avisam ({rc}: {saida})")
    return casos


def selftest() -> int:
    total = _selftest_puro() + _selftest_git()
    print(f"versao_corte selftest: OK ({total} casos)")
    return 0


# ── CLI ──────────────────────────────────────────────────────────────────────

COM_VALOR = ("--base", "--raiz", "--desde")
SEM_VALOR = ("--hotfix",)


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        return selftest()
    if not args or "--help" in args or "-h" in args:
        print(__doc__.strip())
        return 0 if args else 2
    opcoes = {"--base": "HEAD", "--raiz": ".", "--desde": ""}
    hotfix = False
    posicionais = []
    i = 0
    while i < len(args):
        if args[i] in COM_VALOR:
            if i + 1 >= len(args):
                print(f"erro de uso: {args[i]} exige um valor.", file=sys.stderr)
                return 2
            opcoes[args[i]] = args[i + 1]
            i += 2
        elif args[i] in SEM_VALOR:
            hotfix = True
            i += 1
        elif args[i].startswith("-"):
            print(f"erro de uso: argumento desconhecido {args[i]!r} — veja --help.", file=sys.stderr)
            return 2
        else:
            posicionais.append(args[i])
            i += 1
    if len(posicionais) != 1 or not eh_semver(posicionais[0]):
        print("erro de uso: informe UMA versão X.Y.Z (SemVer, sem 'v' e sem zero à esquerda).", file=sys.stderr)
        return 2
    pedida, base, raiz, desde = posicionais[0], opcoes["--base"], Path(opcoes["--raiz"]), opcoes["--desde"]

    try:
        ultima, avisos_tags = classificar_tags(tags_do_repo(raiz))
        inicio, aviso_inicio = inicio_da_contagem(raiz, ultima, base, desde)
        mensagens = mensagens_desde(raiz, inicio, base)
    except (subprocess.CalledProcessError, OSError) as e:
        erro = (getattr(e, "stderr", "") or str(e)).strip() or str(e)
        print(f"erro de uso: git falhou em {raiz} ({base}): {erro.splitlines()[0]}", file=sys.stderr)
        return 2

    for aviso in avisos_tags + ([aviso_inicio] if aviso_inicio else []):
        print(f"versao_corte: aviso — {aviso}")
    intervalo = f"{inicio}..{base}" if inicio else base
    print(f"versao_corte: {len(mensagens)} commit(s) na conta ({intervalo}, sem merges)")
    exigido, culpado = bump_exigido(mensagens, ultima)
    ok, motivo = validar(pedida, ultima, exigido, hotfix)
    print(f"versao_corte: {motivo}")
    if not ok and culpado:
        print(f"versao_corte: o bump {exigido} vem de: {culpado!r}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
