#!/usr/bin/env bash
# Deriva o repositório público a partir deste, que é a fonte canônica (ADR-0036).
#
# O dado de cliente não é removido do público: ele mora em caminhos que nunca
# são copiados. Por isso o ALLOWLIST é a defesa principal — ela não depende de
# a lista de nomes estar completa — e o gate de confidencialidade é a segunda,
# que aborta a publicação se um nome escapou para dentro do payload.
#
# O snapshot vem da TAG, nunca do disco: worktree suja, arquivo não commitado e
# commit posterior à tag não têm como entrar (delta-066).
#
# Uso:
#   export DELTASPEC_REMOTE_PUBLICO=git@github.com:<dono>/<repo-publico>.git
#   scripts/publica-dist.sh --dry-run vX.Y.Z   # ensaia: imprime árvore e veredito
#   scripts/publica-dist.sh vX.Y.Z             # publica: commit órfão, tag, Release
set -euo pipefail

# Único lugar a editar quando o payload mudar. Tudo o que não está aqui fica no
# privado — `specs/`, `debts/`, `DEBT.md`, `HANDOFF.md` e o resto de `.claude/`
# inclusive. `CLAUDE.md` e `.claude/hooks/` entram porque o `ci.yml` publicado os
# invoca: sem eles o repositório derivado nasce com o CI vermelho, e o grep da
# política de dependência sai 2 imprimindo "OK" sem ter checado nada (delta-066).
ALLOWLIST=(
  skills
  .claude-plugin
  .claude/hooks
  .github/workflows
  .github/scripts
  scripts
  docs/adrs
  CLAUDE.md
  doc-profile.yaml
  README.md
  README.en.md
  CHANGELOG.md
  LICENSE
  SECURITY.md
  CONTRIBUTING.md
  CODE_OF_CONDUCT.md
  .gitignore
)

GATE=".claude/hooks/guarda-confidencialidade.py"
INTEGRIDADE="skills/guarding-doc-integrity/scripts/validate_integrity.py"

RAIZ="$(git rev-parse --show-toplevel)"
cd "${RAIZ}"

# host/dono/repo — comparável entre as formas ssh e https da mesma URL.
normaliza_remote() {
  sed -E 's#^[a-z+]+://##; s#^[^@/]+@##; s#:#/#; s#/+$##; s#\.git$##' <<<"$1" | tr 'A-Z' 'a-z'
}

# Sem default: o slug do público e o do privado coincidem, então um alvo errado
# fica invisível no --dry-run — ele imprime o nome e o nome parece certo. A
# publicação apaga o conteúdo do alvo, e o alvo errado é a fonte (delta-066).
REMOTE_PUBLICO="${DELTASPEC_REMOTE_PUBLICO:-}"
if [[ -z "${REMOTE_PUBLICO}" ]]; then
  echo "exporte DELTASPEC_REMOTE_PUBLICO com a URL do repositório público" >&2
  echo "  não há default: publicar no alvo errado apaga o repositório canônico" >&2
  exit 2
fi

origem="$(git remote get-url origin 2>/dev/null || true)"
if [[ -n "${origem}" ]] && [[ "$(normaliza_remote "${REMOTE_PUBLICO}")" == "$(normaliza_remote "${origem}")" ]]; then
  echo "alvo idêntico ao remote 'origin' (${origem})" >&2
  echo "  este é o repositório canônico; o derivado é outro" >&2
  exit 2
fi

# O push abaixo é force sobre a default branch do derivado, que o ruleset
# `sdd-protect-main` protege — e commit órfão não tem PR possível (ADR-0036).
# Quem atravessa é a **deploy key dedicada** registrada lá, único ator de bypass
# do ruleset desde o DT-067: o bypass amplo do papel Admin saiu. Publicar com a
# credencial pessoal, ou trocar a chave sem registrar a nova como deploy key com
# escrita, faz o GitHub recusar o push citando as regras que estaria pulando.
CHAVE_PUBLICACAO="${DELTASPEC_SSH_KEY_PUBLICA:-${HOME}/.ssh/deltaspec-publica}"
if [[ ! -f "${CHAVE_PUBLICACAO}" ]]; then
  echo "chave de publicação ausente: ${CHAVE_PUBLICACAO}" >&2
  echo "  gere o par e registre a pública como deploy key com escrita no derivado:" >&2
  echo "    ssh-keygen -t ed25519 -N '' -f ${CHAVE_PUBLICACAO}" >&2
  echo "    gh api repos/<dono>/<repo-derivado>/keys -f title=publica-dist -f key=@${CHAVE_PUBLICACAO}.pub -F read_only=false" >&2
  echo "  ou aponte DELTASPEC_SSH_KEY_PUBLICA para a chave já registrada" >&2
  exit 2
fi
if [[ ! "${REMOTE_PUBLICO}" =~ ^(git@|ssh://) ]]; then
  echo "DELTASPEC_REMOTE_PUBLICO precisa ser URL ssh (${REMOTE_PUBLICO})" >&2
  echo "  deploy key não autentica em https, e é ela que tem o bypass" >&2
  exit 2
fi
export GIT_SSH_COMMAND="ssh -i ${CHAVE_PUBLICACAO} -o IdentitiesOnly=yes"

ensaio=0
versao=""
for arg in "$@"; do
  case "${arg}" in
    --dry-run) ensaio=1 ;;
    v*) versao="${arg}" ;;
    *) echo "argumento desconhecido: ${arg}" >&2; exit 2 ;;
  esac
done

if [[ -z "${versao}" ]]; then
  echo "uso: $0 [--dry-run] vX.Y.Z" >&2
  exit 2
fi

if ! git rev-parse -q --verify "refs/tags/${versao}" >/dev/null; then
  echo "tag ${versao} não existe neste repositório" >&2
  echo "  o snapshot vem da tag, não do disco — corte a tag antes de publicar" >&2
  exit 2
fi

destino="$(mktemp -d)"
espelho="$(mktemp -d)"
trap 'rm -rf "${destino}" "${espelho}"' EXIT

# `git archive` reprova pathspec ausente na tag: filtra antes e diz o que ficou
# de fora, em vez de morrer no meio da montagem.
presentes=()
for caminho in "${ALLOWLIST[@]}"; do
  if [[ -n "$(git ls-tree -r --name-only "${versao}" -- "${caminho}")" ]]; then
    presentes+=("${caminho}")
  else
    echo "aviso: '${caminho}' do allowlist não existe em ${versao} — fora do snapshot" >&2
  fi
done
git archive --format=tar "${versao}" -- "${presentes[@]}" | tar -x -C "${destino}"

# O rodapé de comparação pertence ao repositório que tem o histórico (R80). No
# público esses links apontariam para commits que nunca existiram lá.
changelog="${destino}/CHANGELOG.md"
if [[ -f "${changelog}" ]]; then
  # Âncora em qualquer definição de link, não só nas numeradas: a primeira linha
  # do rodapé é `[Não lançado]`, e `^\[[0-9]` a deixava passar para o público.
  primeiro_link="$(grep -n '^\[[^]]*\]:' "${changelog}" | head -1 | cut -d: -f1 || true)"
  if [[ -n "${primeiro_link}" ]]; then
    head -n "$((primeiro_link - 1))" "${changelog}" > "${changelog}.tmp"
    mv "${changelog}.tmp" "${changelog}"
  fi
fi

echo "==> árvore do snapshot de ${versao} (${destino})"
(cd "${destino}" && find . -type f | sed 's|^\./||' | sort)
echo "==> $(cd "${destino}" && find . -type f | wc -l) arquivos"

echo "==> gate de confidencialidade"
CLAUDE_PROJECT_DIR="${RAIZ}" python3 "${GATE}" --varre "${destino}"

# O snapshot é o que estranhos vão ler e o CI deles vai rodar. Sem `deps.toml`
# no payload a conferência é a de links (C3, R60) — e **bloqueia**: link morto
# no snapshot aborta a publicação (R1, delta-070). A justificativa do modo
# relatório era o próprio DT-058; quitado, o escape morre.
echo "==> integridade documental do snapshot (bloqueante)"
python3 "${RAIZ}/${INTEGRIDADE}" --links-only "${destino}"

if ((ensaio)); then
  echo "==> ensaio: nada enviado. Publicaria ${versao} em ${REMOTE_PUBLICO}"
  exit 0
fi

# Commit órfão de verdade: repositório novo em diretório vazio, nunca `clone`.
# O `clone || init` anterior produzia commit filho do histórico existente — a
# garantia do R86 valia por acidente, só enquanto o alvo estivesse vazio.
git init --quiet -b main "${espelho}"
cd "${espelho}"
git remote add origin "${REMOTE_PUBLICO}"
cp -r "${destino}/." .
git add -A
git commit --quiet -m "release: ${versao}"
git tag -a "${versao}" -m "${versao}"

# Órfão não compartilha ancestral com o que estiver publicado: o push é
# substituição declarada, não merge que o git recusaria.
git push --quiet --force origin HEAD:main
git push --quiet --force origin "${versao}"

# `gh --repo` quer [HOST/]DONO/REPO — a URL ssh do remote não serve.
repo_gh="$(normaliza_remote "${REMOTE_PUBLICO}" | sed -E 's#^[^/]+/##')"
notas="$(awk "/^## \[${versao#v}\]/{f=1;next} /^## \[/{f=0} f" "${RAIZ}/CHANGELOG.md")"
gh release create "${versao}" --repo "${repo_gh}" --title "${versao}" --notes "${notas:-${versao}}"

echo "==> publicado: ${versao}"
