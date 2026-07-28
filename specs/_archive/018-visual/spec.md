# delta-018 — visual
Estado: arquivada · Data: 2026-07-28 · Branch: feat/018-visual · Perfil: enxuto — delta só de contrato/documentação (categoria no doc-profile, ADR, adapters, references), sem código de gate; risco baixo (aprovado: 2026-07-28) · Test-plan: dispensado — delta só de prosa/contrato; as verificações (YAML parseável, links vivos, leitura) vivem nas tasks
<!-- Numeração: a regra mecânica daria 017, mas o usuário reservou 017 para a Fase 4 (Jira) e nomeou esta delta 018 (decisão de 2026-07-28). O mecanismo normativo da reserva entra pelo R3 (MUDA R5) abaixo — preserva o gatilho "delta-017" da ADR-0012 e do R34. -->

## Contexto (≤3 linhas)
Fase 5 do plano de upgrade: implementar o veredito da pesquisa (2026-07-28) — Mermaid em git como fonte da verdade dos diagramas e Figma/FigJam como camada de apresentação a cliente, sem virar segunda fonte. O próprio caminho oficial do Figma valida o desenho: o `generate_diagram` do Figma MCP só aceita Mermaid como input. A ADR desta delta **complementa** a ADR-0009 (Accepted, imutável) — mesmo mecanismo da categoria `prototipo` (delta-015/ADR-0013); C4 segue no Structurizr.

## Mudanças

### R1 — ADICIONA: Figma/FigJam como camada de apresentação a cliente, com Mermaid fonte
- DADO um projeto cujo `doc-profile.yaml` declara a categoria `apresentacao` QUANDO um diagrama Mermaid versionado precisa de acabamento para stakeholder ENTÃO ele é materializado no FigJam a partir do `.mmd` fonte (fluxo Mermaid → `generate_diagram` do Figma MCP → retoque manual), e o arquivo `.mmd` em git permanece a única fonte da verdade
- DADO um diagrama já materializado no Figma QUANDO o `.mmd` fonte muda ENTÃO a materialização é refeita a partir do fonte; edição feita direto no Figma nunca retorna ao git como fonte — em divergência, o `.mmd` governa
- DADO um `.mmd` de tipo não suportado pelo `generate_diagram` (a pesquisa registra ~6 tipos aceitos, só FigJam, sem ajuste fino) QUANDO a materialização roda ENTÃO o fallback é render CLI (pipeline vigente) com a imagem colada no FigJam para retoque — limitação registrada na ADR desta delta
- DADO o template `doc-profile.yaml` QUANDO a delta consolida ENTÃO a categoria `apresentacao` existe no bloco `artefatos:` como opcional (`obrigatorio: false` por default), com comentário apontando ferramenta (`figma-figjam`), fluxo e a ADR desta delta — mesmo padrão da categoria `prototipo` (delta-015)

### R2 — ADICIONA: entregável congelado fora do caminho do Figma, com contrato de motor e degradação graciosa
- DADO um entregável congelado (PDF/DOCX da `doc-entregavel`) QUANDO ele é gerado ENTÃO o pipeline CLI vigente (mmdc/dbml-renderer → export) permanece o caminho único — a camada Figma não entra no caminho crítico do documento assinável — e a SKILL.md da `doc-entregavel` documenta o papel do Figma (camada de apresentação, nunca no export) no mesmo change
- DADO a tabela de contrato de `adapters.md` QUANDO a delta consolida ENTÃO existe a linha do Figma MCP (contexto: categoria `apresentacao`) com ponto sensível a breaking (`generate_diagram` beta → "usage-based paid feature" anunciada) e fallback declarado, e a política de versões ganha a entrada com verificação datada (R34; versão "n/a — serviço remoto" com nota)
- DADO o Figma MCP ausente, não autenticado ou a categoria `apresentacao` não declarada QUANDO o ciclo ou a doc-entregavel rodam ENTÃO o fluxo atual segue com no máximo 1 linha de aviso — degradação graciosa (RNF2)
- DADO um cliente que exige o acabamento FigJam no documento congelado QUANDO o export é montado ENTÃO o caminho é retoque/export manual, registrado na ADR desta delta como limitação **não verificada** (claim de fonte única, 2026-07-28: FigJam sem export SVG confiável) — verificar na primeira materialização real

### R3 — MUDA R5 (delta-001): numeração global admite reserva explícita do usuário
- DADO um incremento novo QUANDO a skill `spec-feature` abre a delta ENTÃO cria `specs/NNN-nome/` com `NNN` = max(`specs/`, `specs/_archive/`) + 1 e a branch `tipo/NNN-nome`
- DADO uma versão maior do projeto QUANDO uma delta nova é aberta ENTÃO a numeração continua do maior existente e nunca reinicia
- DADO uma reserva de número declarada explicitamente pelo usuário QUANDO uma delta abre ENTÃO ela pode saltar o número reservado (ou consumi-lo, se for a delta reservada), mantendo a unicidade global — nenhum número é reutilizado, e tanto a delta que salta quanto a que consome citam a reserva de forma citável no spec (padrão R43)

## Fora de escopo
- C4/arquitetura formal — segue Structurizr (regra vigente da tabela normativa, ADR-0009; nada muda)
- Figma como fonte da verdade de qualquer diagrama — renúncia registrada na ADR desta delta (refutada pela pesquisa: até o `generate_diagram` consome Mermaid)
- Automação do retoque/round-trip Figma→git — o fluxo é deliberadamente unidirecional
- Editar a ADR-0009 (imutável) — o papel do Figma entra na ADR nova, que a complementa
- Jira/tickets.md (Fase 4, delta-017 — reservada, consome a reserva do R3)

## Dependências e riscos
- Depende do plano de upgrade aprovado (2026-07-28) e das Fases 0–3 arquivadas (deltas 013–016)
- Risco aceito: `generate_diagram` é beta e "will eventually be a usage-based paid feature" — fora do caminho crítico por design (R2)
- [x] Pendência: reavaliar a camada Figma quando o preço do `generate_diagram` for anunciado — roteada como DT-014 no DEBT.md (archive, 2026-07-28)
