#!/usr/bin/env bash
# Verificação do template pre-commit da git-guard, exercitando o hook de verdade num
# repositório temporário — bash não tem o --selftest dos gates em Python, e o hook só se
# prova instalado. Argumento opcional: raiz do plugin a testar (default: cwd).
#
#   caso 1  sem deps.toml na raiz: o bloco 1 se omite com aviso e o commit passa (DT-094)
#   caso 2  com deps.toml violado: o bloco 1 segue bloqueando
#   caso 3  doc-profile com âncora divergente do plugin: o bloco 5 bloqueia (delta-104)
#   caso 4  doc-profile sem a chave `ancora`: o bloco 5 se omite e o commit passa
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

# caso 3 — âncora divergente: o bloco 5 bloqueia. O plugin root do hook é o `$plugin`
# testado, cujo .claude-plugin/plugin.json é a versão real — a âncora fixada abaixo é
# propositalmente uma que nunca existirá, para não depender da versão do dia.
monta fora-da-ancora
r="$tmp/fora-da-ancora"
printf 'decisao: { data: "2026-01-01", justificativa: "ct" }\npublico: { interno: true, cliente: false }\nartefatos:\n  arquitetura: { obrigatorio: false }\ndeltaspec:\n  ancora: "v0.0.1"\n' > "$r/doc-profile.yaml"
git -C "$r" add doc-profile.yaml
if git -C "$r" commit -q -m "docs: readme" 2>"$tmp/err3"; then
  echo "FALHA caso 3: commit passou fora da âncora — o bloco 5 não morde"; exit 1
fi
grep -q "fora da âncora" "$tmp/err3" || { echo "FALHA caso 3: bloqueou por outro motivo"; cat "$tmp/err3"; exit 1; }

# caso 4 — sem a chave: o bloco 5 se omite (é o estado de todo projeto já inicializado)
monta sem-ancora
r="$tmp/sem-ancora"
printf 'decisao: { data: "2026-01-01", justificativa: "ct" }\npublico: { interno: true, cliente: false }\nartefatos:\n  arquitetura: { obrigatorio: false }\n' > "$r/doc-profile.yaml"
git -C "$r" add doc-profile.yaml
if ! git -C "$r" commit -q -m "docs: readme" 2>"$tmp/err4"; then
  echo "FALHA caso 4: commit bloqueado em repo sem âncora declarada"; cat "$tmp/err4"; exit 1
fi

echo "CT-094/104: OK (4 casos)"
