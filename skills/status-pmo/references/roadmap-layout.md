# Roadmap do portfólio — layout

> Dono do layout de `roadmap.html`, a página do portfólio orientada a **prazos, marcos e cumprimento de requisitos**. Mesmo estilo do [one page do projeto](onepage-layout.md) — as regras de saúde, tendência, criticidade e objetivos vivem lá e valem aqui sem cópia. Campos: [dados-schema.md](templates/dados-schema.md) (`portfolio` na raiz; o resto por projeto).

## Princípios

- **Tempo no eixo principal.** O leitor vê primeiro quando cada projeto entrega o quê, e o que já passou do prazo.
- **Uma linha por projeto, um clique para o one page.** O roadmap resume; o detalhe é o one page de cada projeto.
- **Cada iniciativa diz o resultado, não só a entrega**: saúde · objetivos (dor e impacto) · próximo marco · prazo × previsão · requisitos N/M · dependências do cliente.

## Seções, na ordem

### 1. Faixa do portfólio

Seis indicadores numa faixa: **Projetos** · **No prazo** · **Em risco** · **Atrasados** · **Marcos entregues N/M** · **Próximo prazo contratual** (data + projeto). "No prazo / Em risco / Atrasados" contam projetos pela saúde verde / amarela / vermelha. Cada indicador é link para a tabela da seção 3 filtrada.

### 2. Linha do tempo de marcos

- Uma linha por projeto; colunas por mês, de D0 até o último prazo do portfólio.
- Barra do projeto de D0 (ou início presumido) ao prazo contratual; o prazo contratual marcado na barra.
- Um losango por marco, na data: **entregue** (cheio) · **previsto** (vazado) · **aguardando aceite** (tracejado) · **atrasado** (vermelho, com "+N dias" no título). O losango é link para a página da entrega.
- Marcador vertical "hoje".
- Nome do projeto é link para o one page.
- Sem data por etapa na fonte, a barra fica no nível projeto — nunca se inventa data.

### 3. Tabela por projeto

| Coluna | Conteúdo |
|---|---|
| Saúde | forma + cor + tendência (regra do one page) |
| Projeto | nome, link para o one page |
| Objetivos | glifos `● ◐ ○` por objetivo, com a dor no título; ou "sem objetivo de impacto" |
| Próximo marco | nome e data; atrasado em vermelho com "+N dias" |
| Prazo × previsão | prazo contratual e previsão de término; previsão em âmbar quando passa do prazo |
| Requisitos | N/M cumpridos, com barra |
| Com o cliente | nº de pendências aguardando o cliente, link para a área do cliente do projeto |

Ordem das linhas: saúde (vermelho primeiro) → dias até o próximo prazo.

### 4. Próximos marcos do portfólio

Tabela única: atrasados no topo (mais atrasado primeiro), depois os marcos dos próximos 60 dias (`JANELA_MARCOS_DIAS = 60`, constante nomeada no gerador) por data. Colunas: situação · marco · projeto · data · base (contratual, portfólio, presumida).

### 5. Depois do contrato

O horizonte **Agora / Próximo / Depois** por tema, compacto (tema · problema que resolve · confiança), para o que ainda não tem data contratual. Sem datas — a única seção do roadmap que não as tem.

## Página inicial

A página inicial do site fica enxuta: cabeçalho, destaque da semana, a faixa do portfólio (seção 1), a tabela por projeto (seção 3) e o link "Roadmap →". A linha do tempo completa mora no roadmap.
