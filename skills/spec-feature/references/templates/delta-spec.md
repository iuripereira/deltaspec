# delta-{{NNN}} — {{nome-da-feature}}
Estado: proposta | aplicada | arquivada · Data: {{AAAA-MM-DD}} · Branch: {{tipo}}/{{NNN}}-{{nome}} · Perfil: {{completo|enxuto}} ({{aprovado: AAAA-MM-DD}})
<!-- Perfil enxuto (R1, delta-015): clarify sob demanda; test-plan dispensável com "Test-plan: dispensado — <motivo>" no cabeçalho; review com eixos fundidos. Sem campo Perfil = completo. O perfil é proposta da IA — só vale com a aprovação do usuário registrada. -->

## Contexto (≤3 linhas)
{{por que esta mudança, agora}}

## Mudanças
<!-- só o que muda; um bloco por requisito; ADICIONA/MUDA/REMOVE em relação ao TRUTH.md -->
### R1 — {{ADICIONA|MUDA|REMOVE}}: {{requisito}}
- DADO {{estado inicial}} QUANDO {{ação}} ENTÃO {{resultado verificável}}

## Requisitos não funcionais
<!-- só se a delta tem RNF (desempenho, segurança, acessibilidade, capacidade, ...); numeração RNFn separada dos Rn; qualidade sem limiar fechado NÃO entra aqui — vira pendência em "Dependências e riscos" -->
### RNF1 — {{ADICIONA|MUDA|REMOVE}}: {{qualidade}}
- Métrica: {{limiar verificável — ex.: p95 < 300ms sob 100 req/s}}
- Verificação: {{como medir — ex.: teste de carga no CI, axe-core, checklist}}

## Fora de escopo
- {{o que deliberadamente não entra}}

## Dependências e riscos
<!-- pendência ABERTA = item checkbox `- [ ]` (o C6 acusa se sobrar em delta arquivada); risco informativo = bullet comum. No archive, pendência aberta vira DT-NNN no DEBT.md (natureza: pendência, origem: delta-NNN) e o item aqui vira `- [x]`. -->
- {{deltas anteriores, libs, decisões pendentes}}
