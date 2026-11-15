# Perfis de exigência

> Nem todo repositório merece a mesma cobrança. Um rascunho sem remoto não pode ser cobrado por regra de servidor, e cobrá-lo mesmo assim produz relatório que ninguém lê. O perfil decide **o que é achado e o que é informação** — nunca o que é verificado: todos os checks rodam em todos os repositórios.
>
> Catálogo dos `Gn`: [anti-padroes.md](anti-padroes.md).

## Como o perfil é derivado

Dos sinais que já estão no repositório. Nenhum arquivo novo é exigido — dos repositórios medidos ao desenhar isto, a maioria não tinha workflow e a maioria não tinha tag, então exigir configuração prévia deixaria justamente os mais frágeis fora da auditoria.

Avaliado de cima para baixo; o primeiro que casa vence.

| Perfil | Sinal |
|---|---|
| `cliente` | `doc-profile.yaml` declara `publico.cliente: true` |
| `rigido` | tem tag **e** workflows **e** remoto — o repositório publica algo que alguém consome |
| `padrao` | tem remoto, sem release |
| `rascunho` | sem remoto, ou sob caminho de arquivo morto / quarentena |

**Override.** `doc-profile.yaml` com a chave `git.perfil` vence a detecção, e o relatório declara que veio de override — perfil silenciosamente diferente do detectado é pior que perfil errado.

```yaml
git:
  perfil: rigido   # rigido | cliente | padrao | rascunho
```

## O que cada perfil cobra

`cobra` = achado conta para o resultado · `info` = aparece no relatório sem derrubar nada.

| | G1 segredo | G2 gate local | G3 camada de agente | G4 main | G5 commit gigante | G6 mensagem | G7 arquivo grande | G8 atributos/donos | G9 branch integrada | G10 `.gitignore` sujo |
|---|---|---|---|---|---|---|---|---|---|---|
| `cliente` | cobra | cobra | cobra | cobra | cobra | cobra | cobra | cobra | cobra | cobra |
| `rigido` | cobra | cobra | cobra | cobra | cobra | cobra | cobra | cobra | cobra | cobra |
| `padrao` | cobra | cobra | cobra | info | cobra | cobra | cobra | cobra | cobra | cobra |
| `rascunho` | cobra | info | info | info | info | info | info | info | info | info |

Duas leituras que a tabela esconde:

- **G1 é cobrado em todos os perfis, sem exceção.** Segredo vazado não fica menos grave porque o repositório é rascunho — e o pior caso medido ao desenhar isto foi exatamente um rascunho: repositório sem `.gitignore`, sem remoto e sem nenhum commit, com um `.env` esperando o primeiro `git add -A`.
- **`rascunho` não é dispensa, é adiamento.** Tudo continua sendo medido e reportado; só não derruba o resultado. No dia em que ganhar um remoto, o perfil muda sozinho e a cobrança começa.

## `cliente`, além do `rigido`

Mesma cobrança, mais duas obrigações de manuseio do relatório:

- O relatório bruto **fica na sessão**. Não vira issue, não vira comentário de PR, não vai para ferramenta externa — é a doutrina do R64 da `audit-workspace`, aqui obrigatória em vez de recomendada.
- Achado de segredo é **escalado na hora**, não enfileirado como pendência. Em repositório de cliente a credencial provavelmente não é sua para rotacionar, e o custo do atraso é de outra pessoa.

## Piso de aderência a Conventional Commits (G6)

O piso varia por perfil e vive como **constante nomeada no `audit_workspace.py`**, junto do check que a consome. Este arquivo não reproduz os valores de propósito: um número em dois lugares é um número que vai divergir, e a regra de ouro do projeto manda referenciar em vez de duplicar.

O que este arquivo governa é a **ordem**, que é o que raramente muda: `cliente` ≥ `rigido` > `padrao` > `rascunho` (sem piso — G6 é informativo lá).

## Limites conhecidos

- A detecção lê o disco local. Um repositório com proteção de branch configurada no servidor mas sem workflow local aparece como `padrao`, não `rigido` — a skill não consulta a API do GitHub, por desenho (é a fronteira com a `projeto-infra`). O override existe para esse caso.
- "Tem tag" e "tem workflow" são proxies grosseiros de "isto é publicado". Erram para o lado seguro: erram cobrando de menos, nunca de mais.
