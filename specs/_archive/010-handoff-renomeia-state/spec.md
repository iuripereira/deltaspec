# delta-010 — handoff-renomeia-state
Estado: arquivada · Data: 2026-07-24 · Branch: feat/010-handoff-renomeia-state

## Contexto (≤3 linhas)
O `STATE.md` já é o handoff — suas 4 seções são "onde paramos / o que falta / próximos passos" — mas o nome não diz isso e retomar exige cruzar vários arquivos. Renomear STATE→HANDOFF (não criar arquivo novo, que duplicaria dono e feriria a regra de ouro) unifica o ponto de entrada da retomada, mantendo o digest que roteia.

## Mudanças
<!-- só o que muda; um bloco por requisito; ADICIONA/MUDA/REMOVE em relação ao TRUTH.md -->

### R19 — MUDA R19 (delta-007): HANDOFF.md é diário de bordo, não acumulador de estado
- DADO o template HANDOFF.md do projeto-init QUANDO o scaffold cria o arquivo ENTÃO o formato tem as seções "Agora", "Feito recentemente", "Problemas atuais" e "Próximos passos imediatos", com janela rolante declarada e a regra de merge "união das verdades" mantida
- DADO conteúdo que tem dono próprio (as-built → TRUTH.md/README, débito/pendência/lição → DEBT.md, decisão com renúncia → ADR, histórico → CHANGELOG) QUANDO ele surgir no HANDOFF.md ENTÃO é movido para o dono no mesmo bloco de trabalho e o HANDOFF.md apenas referencia
- DADO o conceito STATE.md nas referências ativas do framework (CLAUDE.md, canonical-rules.md, detection.md, deps.toml, README, template) QUANDO a delta é aplicada ENTÃO toda referência ativa passa a HANDOFF.md e não sobram dois donos de "onde paramos" — arquivos imutáveis (`specs/_archive/**`, ADRs Accepted) ficam intactos

### R20 — MUDA R20 (delta-008): a skill handoff compacta a sessão nos registros com dono
- DADO uma sessão de trabalho neste repositório ou num projeto do framework QUANDO o usuário invoca `/sdd-iuri:handoff [foco da próxima sessão]` ENTÃO o `HANDOFF.md` (diário de bordo) é atualizado nas quatro seções — Agora, Feito recentemente, Problemas atuais, Próximos passos imediatos — com o foco informado refletido nos próximos passos
- DADO débito, pendência ou lição descoberto na sessão e ainda sem registro QUANDO o handoff roda ENTÃO ele entra no `DEBT.md` (linha `DT-NNN` ou seção Lições) antes de o diário ser fechado
- DADO uma delta em curso em `specs/NNN-*/` QUANDO o handoff roda ENTÃO o diário cita a delta, a fase em que parou e o veredito do último gate
- DADO conteúdo já registrado em spec/plan/ADR/DEBT/CHANGELOG/commit QUANDO o handoff escreve ENTÃO referencia por caminho/ID em vez de duplicar, e segredo/PII não entra no diário
- DADO o handoff fechado QUANDO ele imprime o prompt de retomada ENTÃO é uma linha única apontando o `HANDOFF.md` com o foco — "Leia o HANDOFF.md deste repo e continue de onde paramos. Foco: <primeiro item de Próximos passos imediatos>" (variante multi-repo: os `HANDOFF.md` dos repos, âncora primeiro)
- DADO um projeto com `STATE.md` legado e sem `HANDOFF.md` QUANDO o handoff roda ENTÃO ele renomeia `STATE.md` → `HANDOFF.md` (`git mv`) antes de escrever, sem deixar os dois arquivos coexistirem

## Fora de escopo
- Copiar conteúdo de DEBT/TRUTH/delta para dentro do `HANDOFF.md` — é digest que **roteia** (referência por ID/caminho), não brief autocontido; a regra de ouro continua valendo.
- Editar `specs/_archive/**` e os ADRs Accepted (0001, 0007, 0008) que citam STATE.md — imutáveis; as referências mortas ficam e viram guarda no `DEBT.md`.
- Renomear as seções internas do diário ("Agora"/…): mantidas como estão — só o arquivo e o conceito mudam de nome.

## Dependências e riscos
<!-- pendência ABERTA = item `- [ ]` (o C6 acusa em delta arquivada); risco informativo = bullet comum -->
- Migração de repos consumidores: projetos já scaffoldados têm `STATE.md`; a auto-migração (`git mv`) no handoff cobre em runtime. Registrar `BREAKING CHANGE:` + caminho de migração no CHANGELOG e no commit.
- `deps.toml` `exclude_globs` deve trocar `STATE.md` → `HANDOFF.md` no mesmo change — senão o `HANDOFF.md` (que cita valores livremente) cai na validação de valores-espelho do `validate_integrity.py` e reprova.
- Tamanho do PR: a renomeação ampla pode exceder o limiar; o C7 mede e o split condicional (R17) resolve se necessário.
- ADR nova registra a renúncia (manter o nome STATE / criar um segundo arquivo HANDOFF) e a escolha (rename + ponto de entrada único), referenciando ADR-0007 e ADR-0008 sem editá-los — gravada antes do plan (cycle.md, passo 5).
