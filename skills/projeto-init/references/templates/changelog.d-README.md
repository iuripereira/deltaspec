# changelog.d — entradas de CHANGELOG por PR

Cada PR que muda algo **notável para quem consome o projeto** deixa aqui um arquivo:

    changelog.d/<slug>.<categoria>.md

`<categoria>` é uma de `adicionado · mudado · corrigido · removido · obsoleto · seguranca` (ASCII, sem acento no nome do arquivo). O conteúdo é **uma linha**: o bullet, sem o `- ` inicial, com no máximo 200 caracteres, terminando na referência da PR.

    changelog.d/regras-nativas.adicionado.md
    → Regras do Documento v3 nativas no jira-config.json (#186)

Por que arquivo em vez de editar o `CHANGELOG.md`: duas PRs vivas editando a mesma seção conflitam a cada merge; dois arquivos com nomes diferentes, nunca.

A narrativa — porquê, medição, renúncia, IDs de delta e débito — **não vem para cá**. O dono dela é a PR, a delta arquivada e a ADR (ADR-0035).

## Comandos

Trocando `<deltaspec>` pela raiz do plugin (`git config deltaspec.plugin-root`):

```bash
# depois de abrir a PR, carimba o número nos fragmentos que ainda não têm
python3 <deltaspec>/skills/spec-feature/scripts/montar_changelog.py --preencher-pr 186

# gate: valida forma sem escrever nada
python3 <deltaspec>/skills/spec-feature/scripts/montar_changelog.py --verificar

# no release: monta o [Não lançado] e apaga os fragmentos
python3 <deltaspec>/skills/spec-feature/scripts/montar_changelog.py
```

Mudança sem efeito observável para quem consome o projeto **não vira entrada** — o tipo do commit não decide isso, quem escreve a PR decide.
