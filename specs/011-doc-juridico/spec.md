# delta-011 — doc-juridico
Estado: proposta · Data: 2026-07-26 · Branch: feat/011-doc-juridico

## Contexto (≤3 linhas)
A `doc-entregavel` só sabe exportar PRD/spec congelado; documento jurídico-comercial (NDA, contrato de TI, documento de requisitos para cliente) tem estrutura, base legal e formatação próprias que a skill não conhece.
O conhecimento existia como prompt solto e não versionado, com base jurisprudencial desatualizada sobre assinatura eletrônica.
A delta versiona esse conhecimento como reference canônico e liga a SKILL.md a ele por tipo de documento.

## Mudanças

### R1 — ADICIONA: a doc-entregavel despacha por tipo de documento
- DADO um pedido de entregável QUANDO a skill roda ENTÃO ela identifica o `tipo` entre `prd-cliente` (fluxo vigente), `juridico-nda`, `juridico-contrato-ti` e `requisitos-cliente`, perguntando com opções fechadas apenas quando o pedido for ambíguo
- DADO um `tipo` `juridico-*` ou `requisitos-cliente` QUANDO a skill monta o conteúdo ENTÃO as regras de conteúdo, estrutura e base legal vêm de `skills/doc-entregavel/references/juridico.md` e o export continua sendo o pipeline vigente da SKILL.md (render de diagramas, capa, Sumário, PDF/DOCX)
- DADO a SKILL.md QUANDO ela cita uma regra jurídica ENTÃO referencia o reference sem reproduzir o texto da regra (fonte canônica única)

### R2 — ADICIONA: documento jurídico sai como minuta, com eficácia executiva verificável
- DADO um documento de tipo `juridico-*` QUANDO ele é gerado ENTÃO o topo do arquivo traz a nota de minuta ("sujeita a revisão por advogado(a)", gerada por IA, não é aconselhamento jurídico) e o fecho traz bloco de assinaturas com as partes e duas testemunhas identificadas por nome e CPF
- DADO uma base legal não listada no reference QUANDO o texto precisaria citá-la ENTÃO a skill grava `[VERIFICAR COM ADVOGADO]` no lugar, sem inventar dispositivo, número de lei ou julgado
- DADO um documento `juridico-*` concluído QUANDO a skill encerra ENTÃO imprime o checklist de eficácia do reference (testemunhas, assinatura eletrônica com integridade conferida por provedor, rubrica, duas vias, revisão por advogado, registro em RTD no dia da assinatura quando optado)
- DADO um pedido para "seguir ABNT" em instrumento contratual QUANDO a skill formata ENTÃO corrige a premissa (NBR 14724 é norma acadêmica) e aplica a convenção de mercado do reference

### R3 — ADICIONA: `requisitos-cliente` cobre projeto e produto, em duas versões, com orçamento, prazo e cronograma
- DADO um pedido de `requisitos-cliente` QUANDO a skill monta o documento ENTÃO ele declara explicitamente o recorte coberto — requisitos de projeto e/ou de produto/serviço — e traz seção de Visão do produto e/ou Visão do projeto conforme o recorte declarado
- DADO um documento `requisitos-cliente` QUANDO ele é gerado ENTÃO as seções de previsão de orçamento (por fase, com premissas da estimativa e faixa), prazo total estimado e cronograma (fases, marcos, dependências e marcos de pagamento vinculados) estão presentes e preenchidas ou marcadas com placeholder em destaque
- DADO o estado da negociação QUANDO a skill escolhe a versão ENTÃO gera a Versão A (proposta executiva, pré-NDA: visão, problema, macro-funcionalidades, faixa de investimento e prazo macro, sem arquitetura detalhada, modelagem de dados ou backlog decomposto) ou a Versão B (especificação completa, pós-NDA assinado, com rodapé `CONFIDENCIAL` e nota de titularidade), nunca as duas no mesmo arquivo
- DADO um documento `requisitos-cliente` QUANDO ele lista requisitos ENTÃO usa os IDs rastreáveis do framework (`OBJ-*`, `ESC-*`, `RF-*`, `RNF-*`, `RC-*`, `PRE-*`, `RSK-*`), compatíveis com o `tabela_cliente.py` da própria skill

## Fora de escopo
- Templates `.md` prontos dos três documentos — o reference instrui a geração; template pronto viraria segundo dono da mesma regra
- ADR nova sobre tipos de documento — a decisão de fundo (entregável cliente é congelado e isento do RNF1) já está na ADR-0009
- Check mecânico do `tipo` no `check_cycle.py` — a ADR-0009 renuncia ao check até o formato estabilizar
- Automação de export com marca d'água e rodapé `CONFIDENCIAL` no `exporta_entregavel.py` — a regra fica declarada no reference; a implementação no script é delta futura

## Dependências e riscos
- Precedente jurisprudencial citado no reference (STJ REsp 2.205.708-PR, Info 871, 04/11/2025; REsp 2.150.278-PR, 24/09/2024) pode ser superado — o reference declara data de verificação e a política conservadora não depende dele para funcionar
- O reference não substitui advogado: toda saída é minuta, por R2
- [ ] Rodapé `CONFIDENCIAL` e marca d'água em todas as páginas ainda são instrução manual — o `exporta_entregavel.py` não tem flag para isso
