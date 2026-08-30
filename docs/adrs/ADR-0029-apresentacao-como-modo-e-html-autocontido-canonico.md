# ADR-0029: Apresentação é modo por categoria, com motor nativo — e o HTML autocontido ganha dono único

- **Status:** Accepted (2026-08-10, delta-042)
- **Data:** 2026-08-10
- **Supersedes:** [ADR-0018](ADR-0018-diagram-design-camada-apresentacao.md)
- **Superseded by:** —

## Context

A ADR-0018 contratou `diagram-design` + `design-sync` como camada de apresentação e a materializou no `doc-profile.yaml` como a **categoria** `apresentacao` — um sétimo tipo de diagrama, irmão de `arquitetura`, `modelo-dados`, `fluxos`, `casos-de-uso`, `explicativos` e `prototipo`. O uso real expôs dois furos.

**1 — a categoria não expressa o pedido.** O que um projeto precisa dizer é "quero *a arquitetura* com acabamento para a alta gestão". A modelagem por categoria só permite dizer "quero um diagrama da categoria apresentação", que é outra coisa: obriga a escolher entre a ferramenta correta da categoria (o vínculo normativo da [ADR-0009](ADR-0009-documentacao-visual-gate-configuravel.md): a ferramenta segue a categoria) e o acabamento. Acabamento é um **eixo ortogonal** à categoria, não um valor dela.

**2 — as convenções de HTML autocontido já existiam em duplicata, sem dono.** Três lugares do framework emitem HTML com o mesmo conjunto de regras, cada um pela sua conta: `skills/status-pmo/references/templates/styles-tokens.css` (tokens `:root`, tema claro default com escuro por toggle, `@media print`, SVG inline, zero lib), o CSS embutido em `skills/doc-entregavel/scripts/exporta_entregavel.py` (print-first, `@page`) e, a partir desta delta, a página de apresentação. Nenhum arquivo é dono da regra — violação direta da regra de ouro do `CLAUDE.md`.

O repositório [anthropics/html-effectiveness](https://github.com/anthropics/html-effectiveness) (Anthropic, MIT) entrou na avaliação como possível motor e **não é um**: é uma galeria de 20 páginas autocontidas sem build nem dependência. O que ele contribui é o catálogo de padrões (annotated flowchart, explainer, deck, status report) e a confirmação independente das convenções que a `status-pmo` já praticava — insumo de regra, não dependência nova.

Alternativas consideradas:

**1 — Manter a categoria e só trocar/somar o motor.** Diff mínimo, ADR-0018 sobreviveria intacta. Mas não resolve o furo 1: continua impossível pedir acabamento para a arquitetura sem abandonar o Structurizr.

**2 — Bloco `apresentacao` independente, listando as categorias que materializa.** Separa acabamento de diagrama, mas cria uma **segunda lista de categorias** que pode divergir do mapa `artefatos` — duas fontes para o mesmo fato, exatamente o que a regra de ouro proíbe.

**3 — Flag por artefato + regra canônica com dono.** `apresentacao: true` em cada artefato de `artefatos`; um bloco opcional só para o que varia (motor, saída, paleta); e os invariantes de HTML extraídos para um arquivo dono, consumido pelas três skills.

## Decision

Adotamos a **3** (decisão do usuário, 2026-08-10).

**Apresentação vira modo, não categoria.** `apresentacao: true` é uma flag booleana em cada artefato de `artefatos`; a categoria `apresentacao` sai do mapa. O vínculo normativo da ADR-0009 fica **intacto** — a ferramenta continua seguindo a categoria, e o fonte versionado (`.mmd`, `.dsl`, `.dbml`) continua sendo o dono do conteúdo. A flag só decide se aquele artefato **também** materializa com acabamento.

**Motor default nativo.** O agente escreve o HTML seguindo a regra canônica. `diagram-design` **permanece** como motor opcional, declarável em `apresentacao.motor` — a decisão do DT-019 (o plugin no `instala-motores.sh`) fica de pé e o contrato da ADR-0018 sobrevive por dentro desta. Renunciamos a torná-lo o default porque um acabamento que vai à alta gestão não deve depender por padrão de plugin com bus factor 1 e contrato nunca testado em execução; renunciamos a removê-lo porque a capacidade é real e o custo de mantê-lo opcional é uma linha de configuração.

**Saída: um arquivo por delta, com âncoras.** `docs/apresentacao/NNN-nome.html`, gerado **no archive** (conteúdo estabilizado — spec em rascunho apresentada à gestão é ruído e retrabalho), com uma seção ancorada por categoria marcada. Renunciamos a uma página por diagrama porque quem lê não navega pasta: âncora (`NNN-nome.html#arquitetura`) é HTML nativo e entrega o link avulso sem um segundo artefato. Renunciamos ao eixo `fase` configurável — mais um eixo de configuração para um caso que ninguém pediu ainda.

**O HTML autocontido ganha dono:** `skills/spec-feature/references/html-autocontido.md`, consumido pela página de apresentação, pela `status-pmo` e pela `doc-entregavel`. O arquivo é dono dos **invariantes** — um arquivo sem CDN, lib ou fetch externo; SVG inline; nove tokens CSS canônicos em `:root` (`--ink --paper --card --muted --line --acc` semânticos, herdados do `styles-tokens.css` já provado em repo de cliente, mais `--serif --sans --mono`); tema claro default com escuro só por toggle explícito; `@media print` imprimível; `lang`, hierarquia de headings e `focus-visible`. Vive na `spec-feature` porque o consumidor primário é a fase de archive e porque o precedente de referência cross-skill já existe (`doc-entregavel/SKILL.md` aponta para `spec-feature/references/adapters.md`).

**Não é uma folha de estilo compartilhada.** `styles-tokens.css` permanece dono do design system de dashboard da `status-pmo` (gantt, farol, chips — vocabulário próprio, não universal) e é citado pela regra como implementação de referência. A `doc-entregavel` conforma **parcialmente** — é print-first com tipografia serif fixa herdada dos contratos do caso de referência — e a divergência entra documentada na regra, com quando/como corrigir, nunca escondida.

**Renúncias registradas com gatilho:** (a) sem check mecânico do bloco no `check_cycle.py` — perímetro da [ADR-0006](ADR-0006-perimetro-dos-gates.md), mecanizar depois que o formato estabilizar (DT-038); (b) sem script gerador, o agente escreve — a página é narrativa e varia a cada delta, ao contrário do dashboard repetitivo que justifica o gerador da `status-pmo` (DT-039); (c) o caminho perfil → archive → página nasce **não exercitado de ponta a ponta**, porque este repo declara todos os artefatos `obrigatorio: false` com justificativa registrada e ligar a flag aqui contradiria a própria decisão que a ADR-0009 protege — a validação sai por um exemplo de referência executável na regra (DT-039); (d) sem dark mode automático por `prefers-color-scheme`, mesma renúncia já tomada pela `status-pmo` — o destino é tela e papel de reunião.

## Consequences

**Fica mais fácil:** pedir acabamento para qualquer categoria sem abandonar a ferramenta correta dela; entender o que o projeto decidiu (uma flag ao lado do artefato, não uma categoria à parte); manter o padrão visual coerente entre as três skills que emitem HTML, porque a regra tem um dono e as SKILL.md linkam em vez de reproduzir; e adotar a camada sem instalar nada — o default deixou de exigir plugin de terceiro.

**Fica mais difícil:** perfis existentes ficam atrás do template (a categoria `apresentacao` declarada continua válida, mas a migração para a flag é manual, relatada e nunca reescrita pelo `projeto-init`); a página só existe depois do archive, então aprovação prévia da gestão fica sem caminho suportado — porta fechada conscientemente, reabrível por delta futura se o uso reclamar; e três consumidores passam a depender de um arquivo de regra, o que torna qualquer mudança nele uma mudança de contrato.

**Nunca foi tocado:** o entregável congelado. O pipeline CLI da `doc-entregavel` permanece o caminho único do documento assinável — a camada de apresentação segue fora do caminho crítico, invariante herdado da ADR-0018 e preservado inteiro.
