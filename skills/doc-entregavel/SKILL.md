---
name: doc-entregavel
description: Use when exporting a frozen client deliverable (PDF/DOCX with signature cover and embedded diagrams) from a project whose doc-profile.yaml declares publico.cliente true — at the moment declared in the profile (entrega-prd, fechamento-fase). Triggers include "/sdd-iuri:doc-entregavel", "exportar entregável", "gerar PDF para o cliente", "documento para assinatura", "congelar o PRD", or the visual-documentation gate of the sdd-iuri spec flow.
---

# doc-entregavel

## Overview

Exporta o **entregável congelado para o cliente**: renderiza os diagramas declarados no `doc-profile.yaml`, monta o documento final (PRD/spec + diagramas embutidos + capa de assinatura) e exporta **PDF e/ou DOCX** em `docs/entregaveis/`. Generalização do pipeline validado nos PRDs e contratos IMEX. Documentação cliente é **isenta da economia de tokens** (exceção registrada na ADR-0009 do sdd-iuri) — completude e fidelidade visual dominam; a renderização é via CLI, o custo de tokens é marginal.

Distinção central (ADR-0009): documentação **interna** é viva (Mermaid inline, mantida junto do código); o **entregável** é congelado — exportado em momento definido, versionado no nome do arquivo, re-assinado a cada baseline. **Nunca sobrescreva um entregável já enviado**: nova baseline → novo arquivo → nova assinatura.

## Processo

1. **Ler o `doc-profile.yaml`** da raiz do projeto. Exige `publico.cliente: true` — perfil ausente ou `cliente: false` → oriente o usuário a criar/ajustar o perfil (template no projeto-init) e **pare**; a decisão é dele, não sua.
2. **Renderizar os diagramas** declarados com `obrigatorio: true`, a partir dos fontes na pasta `saida` do perfil (ex.: `docs/diagrams/`):
   - `.mmd` → `mmdc -i arq.mmd -o arq.svg` (pdf) e `-o arq.png --width <largura nativa do SVG> --scale 2` (docx) — sem `--width`, o viewport default (800px) degrada diagramas largos
   - `.dbml` → `dbml-renderer -i schema.dbml -o schema.svg`
   - `.dsl` (Structurizr/C4) → exportar para C4-PlantUML e renderizar, tudo docker:
     `docker run --rm -u $(id -u):$(id -g) -v "$PWD":/usr/local/structurizr structurizr/structurizr export -workspace arq.dsl -format plantuml`
     → gera `structurizr-<view>.puml` → renderizar como `.puml` abaixo
   - `.puml` → `plantuml -tsvg arq.puml`; sem plantuml local:
     `docker run --rm -u $(id -u):$(id -g) -v "$PWD":/data plantuml/plantuml -tsvg arq.puml`
   - `.d2` → `d2 arq.d2 arq.svg`
   - `.excalidraw` → `npx -y excalidraw-brute-export-cli -i arq.excalidraw --format png --scale 2 -o arq.png --quiet` (headless via Playwright; na primeira vez `npx -y playwright install firefox`)
   Ferramenta ausente → reporte o comando de instalação (seção de setup do README do sdd-iuri) e pergunte se segue sem o diagrama — **nunca entregue silenciosamente incompleto**.
   **A ferramenta segue a categoria do diagrama** (tabela do ADR-0009): não reaproveite um diagrama pronto de outra categoria — arquitetura C4 em Mermaid migra para Structurizr DSL antes do export.
   SVG que precise virar PNG (docx): `rsvg-convert -z 2 arq.svg -o arq.png`; sem rsvg-convert, embrulhe num HTML mínimo (`<img src="arq.svg">`, margin 0) e capture com `google-chrome --headless=new --screenshot --hide-scrollbars --window-size=<LxA nativo do SVG>` — screenshot do SVG "cru" corta e captura scrollbar.
3. **Montar o markdown final**: documento base (PRD.md ou o que o usuário indicar) com os diagramas referenciados como imagem markdown — SVG no pdf, PNG no docx:
   ```markdown
   ![Arquitetura]({{saida do perfil}}/arquitetura.svg)
   ```
   PRD no padrão sdd-iuri (seções "Requisitos Funcionais"/"Requisitos Não Funcionais", localizadas pelo título — independem da numeração)? Aplique antes o **formato cliente**: `scripts/tabela_cliente.py entrada.md saida.md` tabela os cenários DADO/QUANDO/ENTÃO (Pré-condição · Ação · Resultado esperado) e os RNFs (Métrica · Verificação), e corrige o achatamento de listas do caminho pdf (indentação 2→4 — python-markdown só aninha com 4 espaços); paridade garantida por assert. Confirme com o usuário versão e data da baseline — **a data da capa é a da baseline do PRD** (a que o contrato pina), não a do export.

   **Regras de página (pdf):**
   - **Tabela inteira numa página** quando couber (`break-inside: avoid` já no CSS do exportador); se não couber, a quebra nunca corta uma linha ao meio e o cabeçalho repete na página seguinte (no docx, `cantSplit`/`tblHeader` aplicados pelo script).
   - **Diagrama/fluxograma preenche a própria página**: embrulhe a imagem markdown num `<div class="fig-pagina" markdown="1">…</div>` — **só no md do pdf** (ver regra do docx abaixo).
   - **Retrato × paisagem por diagrama**: diagrama mais largo que alto → adicione a classe `paisagem` (`<div class="fig-pagina paisagem" markdown="1">`), que vira página deitada no pdf. Escolha por diagrama, olhando a proporção do SVG — legibilidade manda. Proporção extrema (> ~3:1) fica ilegível mesmo em paisagem: re-layoute o **fonte** (ex.: `autolayout tb` em vez de `lr` no Structurizr) em vez de aceitar texto minúsculo.
   - **SVG precisa de width/height absolutos**: o mermaid emite `width="100%"` sem tamanho intrínseco e a imagem colapsa (página em branco) ou estoura a página no print do Chrome — antes de embutir, grave width/height reais (do viewBox) no SVG.
   - **Caminho docx: imagem como linha markdown pura**, sem o div (o pandoc gfm descarta `<img>` dentro de HTML cru — docx sai sem diagramas). PNG com **DPI (pHYs) coerente**: o pandoc dimensiona por ele; regrave o DPI para a figura caber na página (ex.: PNG 2x de um SVG de 5×8in → 288 dpi).

   **Prosa:** antes de congelar a baseline, rode o checklist de `skills/spec-feature/references/prosa.md` (uma regra por frase; regra combinatória em tabela de decisão; fluxo > 3 passos com diagrama + passos numerados). Entregável jurídico não comporta prosa aninhada.
4. **Exportar** com `${CLAUDE_PLUGIN_ROOT}/skills/doc-entregavel/scripts/exporta_entregavel.py`, uma chamada por formato em `entregaveis.formato`, capa vinda de `entregaveis.capa` do perfil:
   ```bash
   exporta_entregavel.py pdf  PRD.md docs/entregaveis/prd-<projeto>-v<versao>.pdf \
     --titulo "<capa.titulo>" --projeto "<nome>" --versao <v> --data "<data por extenso>" \
     --anexo "<capa.anexo>" --local "<capa.local>" --assinatura "<capa.assinaturas[0]>" ...
   ```
   O exportador aplica por padrão: **corpo justificado** (títulos/tabelas/código à esquerda; pdf com hifenização pt-BR) e **Sumário** em página própria após a capa, no formato de contrato (título pontilhado até o nº de página, subseções indentadas). No pdf os números vêm de **duas passadas de render** (a 1ª mede a página física de cada título via pdftotext/pypdf; sem nenhum dos dois, sai sem números com aviso no stderr). No docx o Sumário é campo TOC nativo com `updateFields` — **quem gera é o próprio Word ao abrir** (pontilhado e paginação dele; até lá o campo mostra um texto-guia com F9).
5. **Verificar e reportar**: abra/inspecione o resultado (tamanho > 0, diagramas presentes, capa correta, Sumário com números de página, corpo justificado) e liste os arquivos gerados. Dependências do host: `pip install pypandoc-binary python-docx markdown pypdf` (docx/pdf; `pypdf` só para os números do Sumário quando não há `pdftotext`) e google-chrome (pdf) — ausentes, reporte o comando e pare o formato afetado, sem quebrar o outro.

## Erros comuns

| Erro | Correto |
|---|---|
| Sobrescrever entregável de baseline anterior | Novo arquivo com a nova versão no nome; o antigo é histórico assinado |
| Exportar sem `publico.cliente: true` no perfil | Orientar a registrar a decisão no doc-profile primeiro (ADR-0009) |
| SVG no DOCX | PNG no docx (`--scale 2`); SVG só no pdf |
| Entregar sem um diagrama porque a CLI faltava | Reportar a ferramenta ausente e perguntar — nunca degradar em silêncio |
| Capa hardcoded no script | Capa vem de `entregaveis.capa` do doc-profile, por argumento |
| "Enxugar" o entregável por economia de tokens | Cliente é isento (ADR-0009); completude domina. RNF1 vale só para a doc interna |
| PNG renderizado no viewport default (800px) fica de baixa resolução em diagrama largo | Renderizar na largura nativa do SVG (`--width`) com `--scale 2` |
| Cenários DADO/QUANDO/ENTÃO achatados como lista plana no pdf (indentação de 2 espaços não aninha no python-markdown) | `scripts/tabela_cliente.py` na montagem — cenários e RNFs viram tabelas e a indentação aninhada é corrigida |
| Capa datada com o dia do export | A data da capa é a da **baseline** do PRD, não a da geração |
| Tabela cortada na extremidade da página | `break-inside: avoid` + cabeçalho repetido (pdf); `cantSplit`/`tblHeader` (docx) — já no exportador; verifique no resultado |
| Diagrama largo espremido em página retrato | `<div class="fig-pagina paisagem">` — página deitada, diagrama preenchendo a página |
| Reaproveitar diagrama de outra categoria (ex.: C4 em Mermaid) porque já existia | A ferramenta segue a categoria (ADR-0009); migre o fonte antes do export |
| Página em branco ou diagrama vazando por várias páginas no pdf | SVG do mermaid vem com `width="100%"` — gravar width/height absolutos (do viewBox) antes de embutir |
| DOCX sem diagramas | pandoc gfm descarta `<img>` dentro de div HTML — no md do docx a figura é linha de imagem markdown pura |
| Figura gigante/minúscula no docx | pandoc dimensiona pelo DPI (pHYs) do PNG — regravar o DPI para caber na página |
| Heading seguinte "engolido" como linha da tabela de cenários/RNFs | Corrigido no `tabela_cliente.py` (linha em branco garantida + preservação do conteúdo pós-RNF); rode a versão atual |
| Tabela de decisão dentro de item de lista (RNs do §5) vira texto com hífen literal no pdf | `deepen_indents` só aprofunda bullets, não blocos aninhados — na montagem, indente o bloco 2→4 e garanta linha em branco antes do item seguinte (achado IMEX 20-07; candidato a fix no script) |

## Arquivos da skill

- `scripts/exporta_entregavel.py` — md → docx (pypandoc + python-docx) e md → pdf (markdown → HTML+CSS → chrome headless), capa parametrizada, corpo justificado e Sumário formato contrato (pdf em 2 passadas com nº de página; docx via campo TOC do Word). `--selftest` valida o próprio script (inclui Sumário com nº de página no pdf e justificação no docx).
- `scripts/tabela_cliente.py` — formato cliente para PRD sdd-iuri: cenários e RNFs das seções de RF/RNF (localizadas pelo título, independentes da numeração) viram tabelas (Pré-condição · Ação · Resultado esperado; Métrica · Verificação); indentação aninhada corrigida para o caminho pdf. `--selftest` valida o próprio script.
