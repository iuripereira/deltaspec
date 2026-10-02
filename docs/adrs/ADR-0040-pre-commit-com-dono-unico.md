# ADR-0040: O `pre-commit` distribuído tem dono único — a `git-guard`

- **Status:** Accepted (2026-08-27, delta-090)
- **Data:** 2026-08-27
- **Supersedes:** —
- **Superseded by:** —

## Context

Até a delta-090 o framework distribuía um `pre-commit` pela `guarding-doc-integrity` (integridade documental, delta-013) e o repositório do próprio framework carregava uma cópia divergente em `.githooks/pre-commit`, com a duplicação declarada no `deps.toml` (delta-060). A `git-guard` (delta-076) nasceu prometendo a segunda metade — segredo no índice, arquivo grande, commit grande — e o catálogo dela fixa a regra que decide tudo: **hook local e CI têm de invocar o mesmo código**, senão o gate documentado diverge do gate executado.

Um repositório só tem um `pre-commit`. Três desenhos estavam na mesa quando a delta-090 abriu:

1. **A `git-guard` não toca o `pre-commit`** — só `commit-msg` e o hook do harness. O G1 ficaria sem trava local; só o CI o pegaria, depois do push.
2. **Dispatcher `pre-commit.d/`** — um `pre-commit` que executa o que cada skill instala na pasta. Flexível, e uma abstração para dois casos.
3. **Um template só, com dono único e blocos independentes** — a `git-guard` dona, a integridade documental como primeiro bloco, a doc-integrity apontando para ela.

Junto veio a pergunta do `pre-push`, listado no escopo original: ele não enxerga `--force` (só inferiria non-fast-forward comparando SHAs), e o G12 já fica coberto pelo hook do harness mais o ruleset do servidor.

## Decision

**O template `pre-commit` é da `git-guard`, e é o único.** Quatro blocos, cada um se omitindo com aviso quando o que ele precisa não está instalado — o hook nunca impede um commit por estar mal instalado. A `guarding-doc-integrity` deixa de ter template próprio e o passo de instalação dela aponta para `git-guard instalar`. No repositório do framework, `.githooks/` vira **symlink** para os templates: a duplicação deliberada da delta-060 deixa de existir, e o bloco do `deps.toml` que a vigiava sai com ela.

Renúncias, com o porquê:

- **Dispatcher `pre-commit.d/`** (decisão do Iuri, 2026-08-27): abstração para dois casos, com mais peças de instalação e um ponto a mais para o hook falhar em silêncio. Se um terceiro dono de bloco aparecer, esta ADR é o gatilho para reabrir.
- **`pre-push`** (decisão do Iuri, 2026-08-27): não vê a flag que importa, e a trava do G12 já existe em duas camadas. Menos um template, menos um caminho de instalação.
- **A `git-guard` fora do `pre-commit`**: deixaria o anti-padrão de dano máximo (G1) sem trava local, que é exatamente o que a delta-076 prometeu entregar.

Compatibilidade: instalação anterior, com `git config deltaspec.validator`, continua funcionando — o template aceita a chave como fallback do bloco de integridade. Migrar é reinstalar.

## Consequences

- **Fica mais fácil:** um só arquivo para instalar, um só dono para evoluir, e o repositório do framework roda exatamente o que distribui (symlink, não cópia).
- **Fica mais difícil:** a `guarding-doc-integrity` passou a depender da `git-guard` para o hook — uma skill que só cuida de docs instala um hook que também bloqueia segredo. É o preço de "um repositório só tem um `pre-commit`", e é declarado no passo 5 dela.
- **Trade-off aceito:** o bloco de integridade documental só bloqueia quando o commit toca `.md`/`deps.toml`; os blocos da `git-guard` rodam sempre. Um commit lento por causa do hook é sinal para fatiar, não para `--no-verify` — e o CI replica o bloco de segredo justamente porque `--no-verify` existe.
