#!/usr/bin/env bash
# Verificação do template pre-commit da git-guard, exercitando o hook de verdade num
# repositório temporário — bash não tem o --selftest dos gates em Python, e o hook só se
# prova instalado. Argumento opcional: raiz do plugin a testar (default: cwd).
#
#   caso 1  sem deps.toml na raiz: o bloco 1 se omite com aviso e o commit passa (DT-094)
#   caso 2  com deps.toml violado: o bloco 1 segue bloqueando
#
# O caso 2 é o que impede a regressão pela porta oposta — desligar o bloco em vez de
# guardar a pré-condição. Os dois juntos são o teste de regressão da delta-094.
set -euo pipefail
plugin=$(cd "${1:-.}" && pwd)
hook="$plugin/skills/git-guard/templates/githooks/pre-commit"
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT

monta() {  # $1 = nome do repo; cria repo com o hook instalado
  local r="$tmp/$1"; mkdir -p "$r/.githooks"
  git -C "$r" init -q 2>/dev/null || git init -q "$r"
  cp "$hook" "$r/.githooks/pre-commit"; chmod +x "$r/.githooks/pre-commit"
  git -C "$r" config core.hooksPath .githooks
  git -C "$r" config deltaspec.plugin-root "$plugin"
  git -C "$r" config user.email ct@exemplo.invalido
  git -C "$r" config user.name CT
  printf '# titulo\n' > "$r/README.md"
  git -C "$r" add README.md
}

# caso 1 — sem deps.toml: o bloco se omite e o commit passa
monta sem-manifesto
if ! git -C "$tmp/sem-manifesto" commit -q -m "docs: readme" 2>"$tmp/err1"; then
  echo "FALHA caso 1: commit bloqueado em repo sem deps.toml"; cat "$tmp/err1"; exit 1
fi
grep -q "sem deps.toml na raiz" "$tmp/err1" || { echo "FALHA caso 1: aviso de omissão ausente"; exit 1; }

# caso 2 — com deps.toml violado: o bloco segue bloqueando
monta com-manifesto
r="$tmp/com-manifesto"
printf 'scan_globs = ["*.md"]\n\n[[owner]]\nfile = "DONO.md"\nmirrors = []\n\n  [[owner.value]]\n  name = "limite"\n  pattern = %s\n' "'R\\\$ ?2\\.000'" > "$r/deps.toml"
printf '# dono\n\nO limite e R$ 2.000 por pedido.\n' > "$r/DONO.md"
printf '# titulo\n\nCopia nao sancionada do limite: R$ 2.000.\n' > "$r/README.md"
git -C "$r" add deps.toml DONO.md README.md
if git -C "$r" commit -q -m "docs: readme" 2>"$tmp/err2"; then
  echo "FALHA caso 2: commit passou com manifesto violado — o bloco 1 foi desligado"; exit 1
fi
grep -q "integridade documental FALHOU" "$tmp/err2" || { echo "FALHA caso 2: bloqueou por outro motivo"; cat "$tmp/err2"; exit 1; }

echo "CT-094: OK (2 casos)"
