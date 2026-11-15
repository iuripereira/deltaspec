---
name: gerar-diagrama
description: Use when someone describes a flow, structure, rule or concept in natural language and wants it turned into a versioned diagram source — the skill classifies the diagram's CATEGORY and derives the tool from the normative table (ADR-0009), instead of letting the requester pick the tool. Generates Mermaid, DBML, Structurizr DSL, PlantUML, D2 or Excalidraw sources; the .excalidraw JSON comes from a stdlib Python generator, with no npm dependency. Triggers include "/deltaspec:gerar-diagrama", "gerar diagrama", "desenha esse fluxo", "diagrama de", "faz um diagrama disso", "quero visualizar esse processo", "monta o fluxograma".
---

# gerar-diagrama

## Overview

Transforma uma descrição em linguagem natural no **fonte versionado** do diagrama, na ferramenta certa. O fonte é o dono do conteúdo (R45): a materialização com acabamento e o export congelado consomem o que esta skill produz, nunca o contrário.

**A escolha da ferramenta não é do usuário.** A tabela normativa categoria→ferramenta vive na [ADR-0009](../../docs/adrs/ADR-0009-documentacao-visual-gate-configuravel.md), que é a dona única — esta skill não a reproduz, lê. O que se confirma com o usuário é a **categoria**; a ferramenta é consequência dela. O reuso cross-categoria ("já tenho isso em Mermaid, aproveita") foi o modo de falha medido no piloto da ADR-0009 e é recusado aqui.

## Fluxo

1. **Classificar a categoria** a partir do pedido, pelos sinais da tabela abaixo.
2. **Confirmar a categoria com o usuário** — em uma linha, dizendo qual ferramenta ela implica e por quê. Nunca ofereça uma lista de ferramentas para escolher.
3. **Derivar a ferramenta** pela tabela da ADR-0009, com o desempate abaixo.
4. **Checar o perfil**: se o `doc-profile.yaml` do projeto não declara essa categoria como `obrigatorio: true`, pergunte antes de gerar (exigência da ADR-0009).
5. **Gerar o fonte** e informar o caminho. Texto é escrito direto; `.excalidraw` sai do script.

## Classificar a categoria

Sinais no pedido, não palavras literais — quem pede raramente usa o nome da categoria.

| Sinais no que foi pedido | Categoria |
|---|---|
| Sequência de passos, decisão/condição, "primeiro… depois…", quem chama quem, ordem no tempo | Fluxogramas / sequência |
| Entidades, campos, chaves, cardinalidade ("um para muitos"), o que o banco guarda | Modelo de dados |
| Serviços, contêineres, limites de sistema, o que fala com o quê, deploy | Arquitetura |
| Ator com um objetivo, "como usuário eu quero", papéis e permissões | Casos de uso |
| Conceito, regra de negócio, analogia, "explica visualmente", o que a prosa não sustenta | Explicativos |

**Ambíguo entre duas categorias → pergunte.** É mais barato que gerar na ferramenta errada e migrar depois.

**Apresentação não é categoria** — é a flag `apresentacao: true` do artefato (ADR-0029). Pedido de "deixar bonito para o cliente" não muda a ferramenta; muda o acabamento, no archive.

## Derivar a ferramenta

- A tabela da ADR-0009 é a fonte. Leia-a, não decore.
- **Linha com duas opções** (arquitetura visual moderna admite D2 ou Excalidraw): desempate pelo `doc-profile.yaml` do projeto. Perfil silente → primeiro da linha, avisando em 1 linha.
- **Sem `doc-profile.yaml`**: gere assim mesmo, avisando em uma linha que o projeto não tem decisão visual registrada e que o `deltaspec:projeto-init` a cria. Degradação graciosa, nunca aborte (RNF2).
- **Perfil malformado**: avise e siga com os defaults da tabela.

## Gerar o fonte

**Ferramentas de texto** (Mermaid `.mmd`, DBML, Structurizr `.dsl`, PlantUML `.puml`, D2) — escreva o arquivo direto. Não há script: o fonte é o texto.

**Excalidraw** (`.excalidraw`) — é JSON com ~25 campos obrigatórios por elemento. Use o gerador:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/gerar-diagrama/scripts/gera_excalidraw.py < esboco.json > diagrama.excalidraw
```

O esboço traz só o que varia:

```json
[
  {"tipo": "rectangle", "x": 0, "y": 0, "largura": 220, "altura": 90, "fundo": "#e7f5ff"},
  {"tipo": "text", "x": 30, "y": 35, "largura": 170, "altura": 25, "texto": "Publicar"}
]
```

Tipos: `rectangle`, `ellipse`, `diamond`, `text`. O script preenche os campos constantes, carimba ids e seeds de forma determinística (mesmo esboço → mesmo arquivo) e valida a si mesmo com `--selftest`.

Para virar imagem, o pipeline é o vigente da `doc-entregavel` — esta skill não exporta.

## Erros comuns

| Erro | Correto |
|---|---|
| Perguntar "quer Mermaid ou Excalidraw?" | Pergunte a categoria; a ferramenta é derivada dela |
| Reaproveitar diagrama pronto de outra categoria | Migre para a ferramenta da categoria certa (ADR-0009) |
| Reproduzir a tabela categoria→ferramenta aqui | Linke a ADR-0009; ela é dona única |
| Gerar categoria fora do `doc-profile.yaml` sem avisar | Pergunte antes |
| Abortar porque falta `doc-profile.yaml` | Avise em 1 linha e gere (RNF2) |
| Montar o JSON do `.excalidraw` à mão | Use o gerador — errar um campo obrigatório produz arquivo que abre torto |
| Instalar `@excalidraw/excalidraw` para gerar o JSON | Não carrega em Node headless e não é publicável pelo allowlist (delta-068) |
