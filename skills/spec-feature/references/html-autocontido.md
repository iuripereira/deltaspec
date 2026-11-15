# HTML autocontido — regra canônica do framework

Este arquivo é o **dono único** dos invariantes de HTML gerado pelo deltaspec. Três consumidores o seguem: a **página de apresentação** do ciclo (materializada no archive quando um artefato do `doc-profile.yaml` marca `apresentacao: true`), a skill **`status-pmo`** e a skill **`doc-entregavel`**.

Quem cita esta regra **linka** para cá. Nenhuma `SKILL.md` reproduz o texto abaixo — valor concreto vive no arquivo dono, o resto referencia.

Decisão e renúncias: [ADR-0029](../../../docs/adrs/ADR-0029-apresentacao-como-modo-e-html-autocontido-canonico.md).

## Invariantes

1. A página **DEVE** ser um arquivo só. **NÃO DEVE** referenciar CDN, biblioteca, fonte remota nem folha de estilo externa, e **NÃO DEVE** fazer `fetch`, XHR ou WebSocket.
2. Diagrama **DEVE** ser SVG inline. **NÃO DEVE** ser `<img>` apontando para arquivo, porque a página deixa de ser autocontida no instante em que sai da pasta.
3. A página **DEVE** declarar os nove tokens da tabela abaixo em `:root`. **NÃO DEVE** inventar nome de token nem usar nome cromático.
4. Tema claro é o padrão. Tema escuro **PODE** existir por toggle explícito (`data-theme`); **NÃO DEVE** entrar por `prefers-color-scheme` — o destino é tela de reunião e papel.
5. A página **DEVE** ter `@media print` que imprima em A4 sem corte horizontal.
6. A página **DEVE** ter `lang`, exatamente um `<h1>`, hierarquia de headings sem salto de nível e `:focus-visible` visível.
7. Todo par tinta/fundo **DEVE** ter contraste ≥ 4.5:1 (WCAG AA).

## Vocabulário de tokens

Nove nomes, nenhum a mais. Os seis semânticos vêm do [styles-tokens.css](../../status-pmo/references/templates/styles-tokens.css), já provado em repo de cliente; os três de tipografia vêm do padrão editorial.

| Token | Papel | Origem |
|---|---|---|
| `--ink` | texto principal | semântico |
| `--paper` | fundo da página | semântico |
| `--card` | fundo de bloco destacado | semântico |
| `--muted` | texto secundário, legenda, metadado | semântico |
| `--line` | borda, régua, separador | semântico |
| `--acc` | acento — link, destaque, estado em curso | semântico |
| `--serif` | pilha serifada (título editorial) | tipografia |
| `--sans` | pilha sem serifa (corpo) | tipografia |
| `--mono` | pilha monoespaçada (código, ID, sobretítulo) | tipografia |

Nome semântico sobrevive à troca de marca; nome de cor não. `--acc` continua sendo o acento quando o cliente troca azul por terracota — `--clay` viraria mentira no mesmo dia.

Os valores concretos são do projeto, não desta regra: vêm de `apresentacao.paleta` no `doc-profile.yaml` (mapa inline token → cor) ou, ausente, da paleta default do exemplo.

## O esqueleto

Parta de [exemplo-apresentacao.html](exemplo-apresentacao.html) — página real e completa, com `<!-- TROQUE: ... -->` em cada ponto de substituição. Não há segundo template a manter em sincronia: o exemplo **é** o esqueleto.

## Os quatro blocos da página de apresentação

Só a página de apresentação do ciclo segue esta seção; `status-pmo` e `doc-entregavel` têm estrutura própria.

| Bloco | Conteúdo | Âncora |
|---|---|---|
| Contexto | o problema em prosa curta, colhido da seção Contexto da spec | `#contexto` |
| Uma seção por categoria marcada | o diagrama daquela categoria em SVG inline, com legenda | `#arquitetura`, `#fluxos`, ... |
| Decisões | os blocos `Rn` destilados e **reescritos** para quem não lê DADO/QUANDO/ENTÃO | `#decisoes` |
| Fonte | link para o `TRUTH.md` consolidado | — |

Fica de fora: `tasks.md`, `plan.md` e riscos internos. Quem lê é cliente, gestão ou stakeholder — não a próxima sessão de implementação.

A âncora é o que dispensa uma página por diagrama: mandar a arquitetura avulsa é mandar `NNN-nome.html#arquitetura`.

## Implementações e divergências

| Consumidor | Conforma | Divergência documentada |
|---|---|---|
| Página de apresentação (ciclo) | integral | — |
| [`status-pmo`](../../status-pmo/SKILL.md) | integral — o `styles-tokens.css` é a **implementação de referência** e segue dono do vocabulário de dashboard (gantt, farol, chips, `.pbar`), que é dele e não universal | saída **não versionada**, ao contrário da página de apresentação, que vive em git e é regenerável |
| [`doc-entregavel`](../../doc-entregavel/SKILL.md) | **parcial** | print-first: o CSS de [exporta_entregavel.py](../../doc-entregavel/scripts/exporta_entregavel.py) usa `@page`, unidades em `pt` e tipografia serifada fixa herdada dos contratos. Os invariantes 3, 4 e 6 são de tela e não se aplicam a um PDF/DOCX assinável. **Quando/como corrigir:** só se o congelado passar a ser lido em tela; hoje a divergência é deliberada, não descuido |

## Checklist antes de congelar

- [ ] Arquivo único; nenhuma requisição externa na aba Network do browser
- [ ] Diagramas em SVG inline, nenhum `<img>` para arquivo
- [ ] Só os nove tokens em `:root`, nenhum nome cromático
- [ ] Tema claro por padrão; escuro (se houver) só por toggle
- [ ] Impressão em A4 sem corte horizontal
- [ ] `lang` presente, exatamente um `<h1>`, headings sem salto
- [ ] Contraste ≥ 4.5:1 nos pares `--ink`/`--paper` e `--muted`/`--paper`
