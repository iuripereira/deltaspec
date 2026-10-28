# Vista da fila de integração — gramática (delta-114)

## O que é
Vista **derivada** de git + GitHub, regenerada por `scripts/integracao.py`; nunca editada, nunca versionada (ADR-0043). Responde: o que está em voo, onde (worktree/sessão), há quanto tempo, com qual PR, em que ordem integrar, o que entrou na `main`.

## Unidade
Branch (local ou `origin/*`) com ≥1 commit novo sobre a base por `git cherry` **ou** checada em worktree. Nunca: `main`, `develop`, `HEAD`, `release-please--branches--*`. Base: `origin/develop` → `develop` → `origin/HEAD` → `main`.

## Fontes
| Coluna | Comando |
|---|---|
| Branch, Dias | `git for-each-ref --format='%(refname:short)\|%(committerdate:short)\|%(upstream:short)\|%(upstream:track)' refs/heads refs/remotes/origin` |
| Novos | `git cherry <base> <ref>` (linhas `+`) |
| Worktree, sujos | `git worktree list --porcelain`; `git -C <wt> status --porcelain` |
| PR, labels, pilha | `gh pr list -R <owner/repo> --state open --limit 100 --json number,headRefName,baseRefName,isDraft,createdAt,labels,url` |
| Sessões | **reservado** à delta-113 R2 (`guarda-sessao.py sessoes --json`, consumido por subprocess); até lá, sempre `?`/`null` |
| Plano | `git log --diff-filter=A --format= --name-only <base>..<ref> -- .claude/plans/` |
| Marco | `--cronograma`: tabela `## Marcos` (data `AAAA-MM-DD`, base `contrato`/`portfolio`) + `**Dir:**` na linha seguinte ao `## <Projeto>`; aviso em stderr quando nada casa (ver "Cronograma esperado") |
| Entrou / saiu / corrigido na release | `gh pr list --state merged --base <develop\|main\|release/X.Y.Z> --search "merged:>=<data>" --limit 100 --json number,headRefName,mergedAt,mergeCommit` — "entrou" e "saiu" olham os últimos `MERGEADAS_DIAS` (7) dias; "corrigido na release" usa a data do corte, o `merge-base` entre a base do repo e a `release/*` |
| Tags (bloco "saiu") | `git for-each-ref --format='%(objectname) %(refname:short)' refs/tags` — nomeia a tag do merge commit; sem tag correspondente, `null` |
| Stashes | `git stash list` |
| Frescor | `--fetch` (opt-in): `git fetch --prune origin` com timeout de 10 s por repo; falha vira `fetch falhou` no cabeçalho renderizado, nunca exit ≠ 0 |

Toda chamada de `gh pr list` usa `--limit 100`; um retorno com **exatamente 100** itens é tratado como truncado — aviso em stderr (`gh <args> retornou 100, pode truncar`), sem paginar: a lista segue sendo a fatia que o GitHub devolveu.

O bloco "corrigido na release" só existe quando o repo tem `release/*`; sem ela, a seção de mudanças recentes segue só com "entrou"/"saiu" — a vista lê o fluxo que o repo tem, nunca exige o que ele ainda não adotou.

## Estados (dono dos limiares)
Testados nesta ordem: `defasada` (> 7 dias sem commit, com ou sem PR) → `draft` → `em PR` → `parada` (> 2 dias, sem PR) → `ativa`. Os dois limiares vêm do agente `branch-killer` de um workspace consumidor (ATIVA_DIAS = 2, DEFASADA_DIAS = 7); o `deps.toml` espelha os valores no script.

## Ordem
Entre repos: marco futuro mais próximo (sem marco → fim; empate → nome). Dentro do repo: `release/*` sempre primeiro (spec R5) — enquanto uma release está aberta, o resto do repo fica represado esperando o próximo corte, e essa é a informação mais cara de descobrir tarde; a prioridade é do próprio item `release/*`, não da raiz da pilha em que ele esteja (uma branch empilhada sobre uma release não "sobe" com ela). Depois: membros de uma pilha logo após a raiz (profundidade crescente) → `fila:N` (menor primeiro, override) → PR mais antiga → tip mais antigo → nome. Pilha = `baseRefName` ≠ base do repo; ciclo em `baseRefName` para sem travar; base ausente vira raiz própria com `pilha_base` informativo.

## Cronograma esperado
Arquivo Markdown com seção `## Marcos` contendo tabela `| Marco | Data | Projeto | Base |` e, para cada projeto, um `## <Projeto>` seguido na linha seguinte de `**Dir:** <pasta>`. Linhas `D+n`, base `presumido` e datas passadas caem sem tratamento especial; projeto sem `**Dir:**` não recebe diretório.

O aviso em stderr distingue três causas, nunca uma mensagem genérica — colapsar as duas primeiras manda procurar no lugar errado, já que as colunas de `## Marcos` casam por posição:

- **(a)** a seção `## Marcos` está ausente, ou a primeira linha não vazia depois do heading não é o cabeçalho esperado (`| Marco | Data | Projeto | Base |`);
- **(b)** a tabela foi lida e nenhuma linha tem marco futuro com base `contrato`/`portfolio`;
- **(c)** um projeto tem marco casado, mas não tem `**Dir:**` na linha seguinte ao seu `## <Projeto>`.

**Limitação conhecida (DT-157):** a causa (a) dispara falso-positivo quando há prosa entre o heading `## Marcos` e a tabela — o critério lê a primeira linha não vazia, não a primeira linha com forma de cabeçalho de tabela. Os marcos em si saem certos (o casamento de `LINHA_MARCO` é por regex em qualquer linha, não por posição); só o aviso engana.

## Contrato `--json`
O objeto raiz traz `"contrato": 1` como **primeiro campo**. É o contrato de compatibilidade para quem consome a saída (ex.: `povoar-fila.py` do `_pmo`, fora desta delta): **remover um campo, ou mudar o tipo de um campo existente, incrementa o número; acrescentar campo novo não incrementa** — assim quem lê o número sabe quando parar de confiar na forma antiga, em vez de continuar parseando errado em silêncio.

```
{
  "contrato": 1,
  "gerado": "AAAA-MM-DDTHH:MM",
  "ativa_dias": 2,
  "defasada_dias": 7,
  "repos": [
    {
      "repo": str, "caminho": str, "base": str,
      "gh": bool, "fetch": bool | null,
      "marco": {"data": "AAAA-MM-DD", "nome": str} | null,
      "stashes": int,
      "checkouts": [{"caminho": str, "branch": str, "sujos": int, "flags": [str, ...], "sessoes": null}],
      "itens": [{
        "branch": str, "estado": str, "dias": int, "novos": int, "data": "AAAA-MM-DD",
        "worktree": str | null, "sessoes": null,
        "pr": {"numero": int, "base": str, "draft": bool, "criada": "AAAA-MM-DD", "labels": [str, ...], "url": str} | null,
        "fila": int | null, "plano": str | null, "upstream_gone": bool,
        "pilha_base": str | null, "ordem": int
      }],
      "mergeadas": [{"numero": int, "branch": str, "mergeada_em": "AAAA-MM-DD",
                     "bloco": "entrou" | "saiu" | "corrigido_na_release", "tag": str | null}]
    }
  ]
}
```

`sessoes` é sempre `null` nesta delta (reservado à 113 R2, mantido no contrato para o consumidor não precisar mudar depois). `fetch` é `null` sem `--fetch`, `false` quando o fetch daquele repo falhou ou estourou o tempo. `flags` de `checkouts` é subconjunto de `prunable`/`locked`/`detached`. `estado` é um dos cinco nomes da seção "Estados" acima.

## Degradação
Sem `gh` (ausente, sem rede, sem remoto GitHub, exit ≠ 0 ou JSON inválido — as cinco causas caem no mesmo caminho, sem distinção): `gh ?` no cabeçalho renderizado, PR `?` na tabela de texto (no `--json`, `pr` vira `null` e `mergeadas` fica vazio), razão registrada **uma vez** em stderr por repo, exit 0. Sessões: `?`/`null` (R3 adiado). Sem `--cronograma`: `sem marco`, ordem entre repos só por nome; com `--cronograma` e nada casável: aviso em stderr (ver "Cronograma esperado"), exit 0. `--fetch` que falha ou estoura 10 s: `fetch falhou` no cabeçalho renderizado, `fetch: false` no `--json`, refs locais. Idade é do **tip** (`committerdate`): rebase ou amend rejuvenesce a branch sem trabalho novo. Sem git: erro de uso (exit 2).
