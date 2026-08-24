# delta-{{NNN}} — {{nome-da-feature}}
Estado: proposta | aplicada | arquivada · Data: {{AAAA-MM-DD}} · Branch: {{tipo}}/{{NNN}}-{{nome}} · Perfil: {{completo|enxuto}} — {{justificativa em 1 linha (escopo/risco)}} ({{aprovado: AAAA-MM-DD}})
<!-- Perfil (R1, delta-015): regras e sintaxe de dispensa na tabela "Perfil de execução" do cycle.md; sem campo = completo; só vale com a aprovação do usuário registrada -->
Clarify: {{entrevistado|auto-avaliado}} ({{AAAA-MM-DD}}) — {{<N> decisões do usuário|sem canal humano}}
<!-- Trilha do clarify (R8, delta-026): âncora canônica lida pelo C12. `entrevistado` só quando o usuário respondeu de fato — ambiguidade resolvida por exploração do repo é `auto-avaliado`. Perfil enxuto e delta bugfix dispensam (clarify sob demanda). -->

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
<!-- pendência ABERTA = item checkbox `- [ ]` (o C6 acusa se sobrar em delta arquivada); risco informativo = bullet comum. No archive, pendência aberta vira arquivo DT-NNN em debts/ativos/ (natureza: pendência, origem: delta-NNN) e o item aqui vira `- [x]`. -->
- {{deltas anteriores, libs, decisões pendentes}}
