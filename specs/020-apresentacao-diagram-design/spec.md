# delta-020 — apresentação por diagram-design + design-sync
Estado: proposta · Data: 2026-07-30 · Branch: feat/020-apresentacao-diagram-design · Perfil: enxuto — troca de motor em camada opcional fora do caminho crítico, sem código de gate; mesmo perímetro da delta-018 (aprovado: 2026-07-30)
<!-- Perfil (R1, delta-015): regras e sintaxe de dispensa na tabela "Perfil de execução" do cycle.md; sem campo = completo; só vale com a aprovação do usuário registrada -->
Test-plan: dispensado — mudança é texto de contrato/skill, sem lógica nova; verificação = gate C1–C10 + grep de menção (mesma dispensa sancionada na delta-018)

## Contexto (≤3 linhas)
O DT-014 pedia reavaliar a camada Figma quando o preço do `generate_diagram` fosse anunciado; a decisão do usuário (2026-07-30) antecipou o gatilho: sair do motor remoto beta/pago e adotar **diagram-design** (diagramas editoriais HTML+SVG brandados, local, MIT) com publicação opcional via **design-sync** (claude.ai/design) — prioridade para documentação que vai a cliente, gestão ou stakeholders. A numeração salta a 017, reservada para a Fase 4 (R5). Quita o DT-014 e supersede a ADR-0015.

## Mudanças
<!-- só o que muda; um bloco por requisito; ADICIONA/MUDA/REMOVE em relação ao TRUTH.md -->

### R1 — MUDA R45 (delta-018): diagram-design como camada de apresentação a cliente, com Mermaid fonte
- DADO um projeto cujo `doc-profile.yaml` declara a categoria `apresentacao` QUANDO um diagrama Mermaid versionado precisa de acabamento para cliente, gestão ou stakeholder ENTÃO ele é materializado com a skill `diagram-design` (HTML+SVG autocontido, brandado) tendo o `.mmd` fonte como dono do conteúdo, saída em `docs/apresentacao/`, e o `.mmd` em git permanece a única fonte da verdade
- DADO um diagrama já materializado QUANDO o `.mmd` fonte muda ENTÃO a materialização é refeita a partir do fonte; edição feita na materialização (HTML ou projeto claude.ai/design) nunca retorna ao git como fonte — em divergência, o `.mmd` governa
- DADO identidade visual disponível (onboarding do diagram-design a partir do site do cliente/projeto, ou tokens declarados no doc-profile) QUANDO a materialização roda ENTÃO os tokens de marca são aplicados; identidade ausente → paleta default da skill, sem bloquear
- DADO materializações prontas QUANDO o usuário pede publicação para stakeholders ENTÃO a ferramenta `design-sync` publica os HTML num projeto claude.ai/design (fluxo incremental list → plan → write, nunca replace integral) — publicação é opcional e por pedido explícito, nunca automática
- DADO o template `doc-profile.yaml` QUANDO a delta consolida ENTÃO a categoria `apresentacao` aponta ferramenta `diagram-design` (+ `design-sync` como publicação opcional) no lugar de `figma-figjam`, mantendo `obrigatorio: false` por default

### R2 — MUDA R46 (delta-018): entregável congelado fora da camada de apresentação, com contrato de motor e degradação graciosa
- DADO um entregável congelado (PDF/DOCX da `doc-entregavel`) QUANDO ele é gerado ENTÃO o pipeline CLI vigente (mmdc/dbml-renderer → export) permanece o caminho único — a camada de apresentação nunca entra no caminho crítico do documento assinável — e a SKILL.md da `doc-entregavel` documenta o papel da camada (apresentação, nunca no export)
- DADO a tabela de contrato de `adapters.md` QUANDO a delta consolida ENTÃO a linha do Figma MCP é substituída pelas linhas do `diagram-design` (plugin de terceiro, local) e do `design-sync` (ferramenta do harness, serviço claude.ai), cada uma com ponto sensível a breaking e fallback declarado, e a política de versões tem as entradas com verificação datada (R34) — diagram-design sem pin até a primeira adoção real, mesmo padrão do graphify
- DADO o plugin `diagram-design` ausente, ou o `design-sync` sem autorização claude.ai, ou a categoria `apresentacao` não declarada QUANDO o ciclo ou a doc-entregavel rodam ENTÃO o fluxo atual (render CLI do Mermaid) segue com no máximo 1 linha de aviso — degradação graciosa (RNF2)
- DADO um cliente que exige o acabamento da camada dentro do documento congelado QUANDO o export é montado ENTÃO o caminho é exportar o HTML materializado para PNG/SVG (`diagram-design:export`, Playwright) e embutir a imagem no pipeline CLI — sem etapa manual não reprodutível

## Fora de escopo
- Tradução/abertura à comunidade (DT-015 — branch própria, fora do ciclo).
- Qualquer mudança no pipeline de export PDF/DOCX (`exporta_entregavel.py`) — inclusive DT-011.
- Round-trip da camada de apresentação para o git (renúncia mantida da ADR-0015).
- Migração de materializações Figma existentes em projetos-alvo (não há nenhuma — a camada nunca foi materializada de fato, DT-014).

## Dependências e riscos
- `diagram-design` (cathrynlavery, MIT) é plugin de terceiro com bus factor 1 e **contrato definido pela doc upstream, não testado em execução** — mesmo tratamento do graphify (delta-016): a primeira adoção real define o pin e valida o contrato.
- `design-sync` depende de login claude.ai com escopo de design; sessões headless/cron podem não ter — coberto pela degradação graciosa (R2).
- ADR-0018 supersede a ADR-0015; a ADR antiga permanece imutável, marcada `Superseded by` (regra do índice de ADRs).
- Quita o DT-014 no archive (a reavaliação que ele pedia é esta delta; o claim não verificado do export FigJam morre junto com a camada Figma).
