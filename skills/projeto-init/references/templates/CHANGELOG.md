# Changelog

Todas as mudanças notáveis deste projeto são documentadas aqui.

O formato segue [Keep a Changelog 1.0.0](https://keepachangelog.com/pt-BR/1.0.0/) e o projeto adere ao [Versionamento Semântico 2.0.0](https://semver.org/lang/pt-BR/). A versão canônica vive nas tags git `vX.Y.Z`.

Cada entrada é **uma linha** que diz o que mudou, com a referência do PR que conta a história:

```markdown
### Adicionado
- **BREAKING** `STATE.md` renomeado para `HANDOFF.md` (#44)
- Skills de efeito colateral viram manual-only (#227, #228)
```

## [Não lançado]

### Adicionado
### Mudado
### Corrigido
### Removido
### Obsoleto
### Segurança

<!--
No release: `/deltaspec:criar-release X.Y.Z` libera esta seção (renomeia "[Não lançado]" para "## [X.Y.Z] - AAAA-MM-DD", abre um "[Não lançado]" novo e escreve o link de comparação no rodapé), e `/deltaspec:release` cria a tag vX.Y.Z e a Release no merge — nunca à mão. Bump derivado dos commits: fix→PATCH, feat→MINOR, !/BREAKING CHANGE→MAJOR (o maior vence).

A narrativa (porquê, medição, renúncia, IDs de delta/débito/requisito) NÃO entra na entrada — ela vive no PR, na delta arquivada e na ADR. Formato validado por check_changelog.py; repositório sem remoto roda com --sem-pr e omite a referência. -->

<!-- Rodapé: um link de comparação por versão, o mais recente primeiro. Na primeira release, tire a linha abaixo do comentário com o seu repositório no lugar de USUARIO/REPO; daí em diante o `montar_changelog.py --liberar` a mantém.
[Não lançado]: https://github.com/USUARIO/REPO/compare/v0.1.0...HEAD -->
