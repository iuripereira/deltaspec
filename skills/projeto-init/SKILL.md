---
name: projeto-init
description: Use when initializing or standardizing a repository and a CLAUDE.md plus documentation scaffold is needed — CHANGELOG, debts, ADRs, specs, glossary. Triggers include "/deltaspec:projeto-init", "init personalizado", "gerar CLAUDE.md canônico", "scaffold de documentação", or setting up Keep a Changelog / SemVer / Conventional Commits / SDD conventions in a project.
---

# projeto-init

## Overview

Gera um `CLAUDE.md` sob medida + scaffold de documentação (SDD), **adaptado ao tipo de projeto**, usando o compilado de convenções do usuário. **Princípio central:** montar o output a partir das regras canônicas em `references/canonical-rules.md` — **não** do conhecimento genérico do modelo. Um agente sem este passo produz um CLAUDE.md plausível que perde as convenções distintivas do usuário (changelog em PT-BR, tag git = fonte da verdade, Git workflow completo, ADR imutável, segurança profunda). Reproduzir as regras canônicas é o objetivo, não improvisar.

## Processo

1. **Detectar** o tipo de projeto inspecionando a pasta alvo (`ls -a`, `cat package.json`, `find . -maxdepth 2 -type f`). Classifique com a tabela de `references/detection.md` (app-web · backend · site-estatico · workspace-dados · tooling). Na dúvida entre dois, **pergunte**. Extraia comandos reais (dev/build/lint/test) do `package.json`/Makefile para os placeholders.
2. **Confirmar** um plano curto com o usuário — tipo detectado, módulos que entram, arquivos a criar, e o toggle de co-autoria (`Co-Authored-By`, opcional). Um único gate; espere o "ok".
3. **Montar o `CLAUDE.md`**: leia `references/canonical-rules.md`, selecione os módulos que a matriz de `detection.md` marca para o tipo, na ordem do arquivo, preenchendo `{{placeholders}}`. Inclua sempre os módulos `header` + `core`. Copie o texto das regras canônicas; adapte só os exemplos ao stack. **Não substitua uma regra canônica por uma versão sua "equivalente".**
4. **Scaffold SDD** a partir de `references/templates/`, seguindo a matriz de arquivos por tipo. Preencha datas/nome do projeto; anexe `gitignore-secrets` ao `.gitignore` (append; inexistente → crie o arquivo com o snippet). Nos tipos com ciclo (coluna `ciclo` de detection.md), o scaffold de specs é `specs/` + `TRUTH.md` — **não** crie `docs/specs/` + SPEC-TEMPLATE nesses tipos. Nos tipos que a matriz marca, gere `doc-profile.yaml` (decisão de documentação visual — ADR-0009) do template com o default enxuto e pergunte se há entregável para cliente; crie `docs/diagrams/` quando o perfil declarar artefato obrigatório e `docs/entregaveis/` só se `publico.cliente: true`. Pergunte também o destino da dívida técnica (`motores.tickets`, delta-099): `none` (default — só o registro em `debts/`), `github-issues` ou `jira` (exige `motores.jira.projeto` — pergunte a chave); sem resposta, mantenha `none` do template.
5. **Oferecer o modelo de dados** (gate próprio, opcional): nos tipos com `DATA_DICTIONARY.md` na matriz, procure os sinais da tabela "Sinais de modelo de dados existente" de `detection.md`. Sinal encontrado → apresente-os e ofereça invocar a skill **modelo-dados** (produz `schema.dbml` + `docs/data-model.md` + ERD derivado e roda o gate), passando as fontes detectadas como insumo. Nenhum sinal → relate em 1 linha ("sem sinais de modelo de dados — o artefato nasce no ciclo, no gate do specify") e siga. Falha ou recusa **não trava o init** — reporte e siga; a skill é invocável avulsa depois.
6. **Oferecer o módulo infra** (gate próprio, opcional): apresente o perfil da coluna `infra` de detection.md e, se o usuário aceitar, invoque a skill **projeto-infra** com o tipo detectado. Falha de infra (sem rede, `gh` não autenticado) **não trava o init** — reporte e siga; a skill é invocável avulsa depois.
7. **Oferecer a trava de git** (gate próprio, opcional): procure os sinais — `git config core.hooksPath` ausente ou apontando para diretório inexistente, ou `.claude/settings.json` sem matcher que alcance `Bash`. Sinal encontrado → apresente-os e ofereça invocar a skill **git-guard** no modo `instalar` (hooks nativos, `.gitattributes`/CODEOWNERS, hook do harness — nunca sobrescreve o que existe). Nenhum sinal → relate em 1 linha ("trava de git já instalada") e siga. Recusa ou falha **não trava o init** — reporte e siga; a skill é invocável avulsa depois.
8. **Verificar os plugins do ciclo**: confira na lista de skills disponíveis `superpowers`, `ponytail`, `mattpocock-skills` (grilling — motor do clarify/spec-review) e `max` (write-prd — motor do PRD da descoberta). Ausente → reporte com o comando de instalação (`/plugin install superpowers@claude-plugins-official` · `/plugin install ponytail@ponytail` · `/plugin install mattpocock-skills@claude-plugins-official` · `/plugin install max@max4c-skills`) e o aviso de qual fase do ciclo degrada sem ele. **Nunca instale sem confirmação.**
9. **Verificar e reportar**: liste o que criou e o que pulou, com o porquê (ex.: "pulei a tríade de release: workspace de dados não versiona releases").

## Nunca sobrescrever

Arquivo já existe? **Não** clobber.
- `CLAUDE.md` existente → escreva `CLAUDE.generated.md` ao lado e mostre o diff; o usuário decide.
- Outros arquivos de scaffold → só crie os que faltam.
- `.gitignore` → **append** o trecho de secrets, nunca substitua.
- `doc-profile.yaml` existente → **relate, não escreva.** Compare as categorias de `artefatos` e a presença do bloco `motores` com os do template e diga em uma linha o que falta ("seu perfil não tem a categoria `prototipo`, nem a flag `apresentacao` nos artefatos, nem os blocos `apresentacao`/`motores`"). Perfil com `apresentacao` **dentro de `artefatos`** é do formato anterior à delta-042: continua válido e funcionando — relate a migração para a flag ([ADR-0029](../../docs/adrs/ADR-0029-apresentacao-como-modo-e-html-autocontido-canonico.md)) e pare aí. Só escreva com **aprovação explícita** do usuário, e mesmo então acrescente apenas chave ausente com o default do template — `decisao`, `publico` e qualquer `obrigatorio` já declarado são decisão registrada do projeto e **nunca** são tocados. Recusa não vira reescrita nem pergunta insistente: o relato é informativo e a 2ª execução continua não alterando arquivo versionado (RNF3). O perfil de um projeto está *atrás* do template por padrão — categoria que uma delta acrescenta não propaga retroativamente, e o C11 tolera a cauda ausente por desenho.

## Adaptação por tipo (resumo — detalhe em detection.md)

| Tipo | Pula | Ênfase |
|---|---|---|
| app-web | — | camadas, testes co-loc, a11y, i18n, segurança |
| backend | i18n-format(leve) | hexagonal, pytest, hardening de servidor |
| site-estatico | testing, architecture | design tokens, LGPD, tríade leve |
| workspace-dados | release-triad, testing, architecture | fontes vs derivados, PII, economia de tokens |
| tooling | i18n, architecture | registro/consistência, git workflow |

## Erros comuns

| Erro | Correto |
|---|---|
| Changelog em inglês (`[Unreleased]`, `Added`) | PT-BR: `[Não lançado]`, `Adicionado/Mudado/Corrigido/Removido/Obsoleto/Segurança` |
| SemVer sem citar a fonte da verdade | "A tag git `vX.Y.Z` é a fonte da verdade, não o `package.json`" |
| Omitir o módulo Git workflow | Sempre incluir (main protegida, 1 sessão=1 branch, PR acima do limiar=anti-padrão, higiene pós-merge) |
| Gerar a tríade de release num workspace de dados | Pular — não há build/release |
| Sobrescrever `CLAUDE.md` existente | Gerar `CLAUDE.generated.md` + diff |
| Improvisar regras genéricas | Copiar de `canonical-rules.md` |
| Criar `docs/specs/` em tipo com ciclo | `specs/` + `TRUTH.md` (o ciclo substitui o estático) |
| Instalar plugin ausente sem perguntar | Reportar comando de instalação e aguardar confirmação |
| Deixar o init travar porque a infra falhou | Infra é passo opcional com gate próprio; reporte e siga |
| Travar o init porque a modelo-dados falhou, ou invocá-la sem sinais | Gate próprio e opcional: sinal → oferecer; sem sinal → 1 linha e seguir |
| Instalar a trava de git sem oferecer, ou sobrescrever hook que o projeto já tinha | `git-guard instalar` é opt-in e nunca sobrescreve; sem sinal, 1 linha e seguir |

## Arquivos da skill

- `references/canonical-rules.md` — módulos montáveis do CLAUDE.md (as regras).
- `references/detection.md` — matriz tipo × módulos × arquivos de scaffold.
- `references/templates/` — CHANGELOG, changelog.d-README, HANDOFF (índice), debts-README, ADR-TEMPLATE, GLOSSARY, DATA_DICTIONARY, doc-profile.yaml, gitignore-secrets. (O template de handoff de sessão vive na skill `handoff`.)
