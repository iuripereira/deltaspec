# delta-031 — rodapé CONFIDENCIAL e marca d'água saem do export
Estado: proposta · Data: 2026-08-04 · Branch: feat/031-rodape-marca-dagua · Perfil: enxuto — duas flags opcionais num script estável, comportamento já normatizado no juridico.md; risco coberto por selftest (aprovado: 2026-08-04)

Clarify: entrevistado (2026-08-04) — 1 decisão do usuário
<!-- trilha do clarify (R8): o review apontou que a marca d'água no juridico-nda ampliava a regra sem respaldo do juridico.md; decisão do usuário: o NDA também leva marca d'água, com a regra ampliada no dono (juridico.md, texto CONFIDENCIAL nomeado lá). Decisões de desenho (elemento fixo no pdf, VML no docx) são do plan; o perfil foi aprovado em entrevista — trilha do R36 no cabeçalho. -->
Test-plan: dispensado — perfil enxuto; a verificação vive no selftest do próprio script (RNF4), caso a caso nas tasks

## Contexto (≤3 linhas)
Rodapé `CONFIDENCIAL` e marca d'água em todas as páginas são instrução manual do `juridico.md` — o `exporta_entregavel.py` não tem flag para nenhum dos dois, então todo entregável `juridico-nda`/`requisitos-cliente` Versão B depende de o operador aplicar à mão no DOCX/PDF ([DT-011](../../DEBT.md), aberto desde a delta-011).
O modo de falha é humano e silencioso: documento confidencial de cliente circula sem a marca. É o 2º item da fila de dívida por risco real de cliente (`P1·J3·Pr3`).

## Mudanças

### R1 — MUDA R21 (delta-011): a `doc-entregavel` despacha por tipo de documento, e a marcação de confidencialidade sai do export
- DADO um pedido de entregável QUANDO a skill roda ENTÃO ela identifica o `tipo` entre `prd-cliente` (fluxo vigente), `juridico-nda`, `juridico-contrato-ti` e `requisitos-cliente`, perguntando com opções fechadas apenas quando o pedido for ambíguo
- DADO um `tipo` `juridico-*` ou `requisitos-cliente` QUANDO a skill monta o conteúdo ENTÃO as regras de conteúdo, estrutura e base legal vêm de `skills/doc-entregavel/references/juridico.md` e o export continua sendo o pipeline vigente da SKILL.md (render de diagramas, capa, Sumário, PDF/DOCX)
- DADO a SKILL.md QUANDO ela cita uma regra jurídica ENTÃO referencia o reference sem reproduzir o texto da regra (fonte canônica única)
- DADO um export com `--rodape TEXTO` e/ou `--marca-dagua TEXTO` QUANDO o `exporta_entregavel.py` roda ENTÃO o rodapé sai em todas as páginas e a marca d'água atravessa cada página, nos dois formatos — no pdf por elemento fixo repetido na impressão, no docx por rodapé de seção e marca d'água de cabeçalho no formato do próprio Word — e a SKILL.md manda usá-los nos tipos que o `juridico.md` marca como confidenciais (`juridico-nda`, `requisitos-cliente` Versão B), sem etapa manual
- DADO um export sem as duas flags QUANDO o script roda ENTÃO a saída permanece a vigente — flags opcionais, nenhum entregável existente muda

## Fora de escopo
- **Paginação `X/Y` no rodapé do pdf** (o `juridico.md` a pede na versão de assinatura): o Chrome headless não expõe contador de página em elemento fixo; no docx a paginação já é campo nativo do Word. Mecanizar exigiria pós-processamento (pypdf) — fica no passo manual, outra delta se o atrito aparecer.
- **Nota de titularidade em todas as páginas** (Versão B): é conteúdo do documento (nota legal), não marcação de página — permanece no corpo do markdown.
- **Rubrica em todas as páginas** (versão física): ato humano de assinatura, fora do export por natureza.

## Dependências e riscos
- Extração de texto de pdf com marca d'água rotacionada varia por ferramenta: o selftest asserta o rodapé página a página e a marca d'água com normalização de espaços; sem `pdftotext`/`pypdf` o caso degrada com aviso, como o Sumário sem número já faz (mesmo padrão de RNF2).
- `python-docx` não tem API de marca d'água: a implementação insere no cabeçalho o VML canônico que o próprio Word gera para watermark. Compatibilidade de risco baixo — é o artefato nativo do formato — e o selftest confere o shape no XML.
