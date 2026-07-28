# delta-013 — higiene
Estado: arquivada · Data: 2026-07-28 · Branch: feat/013-higiene

## Contexto (≤3 linhas)
Fase 0 do plano de upgrade aprovado em 2026-07-28: drift de inventário nos dois manifestos (7 vs 8 vs 9 skills — reincidência da classe registrada nas Lições), DT-005 aberto há 10 dias (gate pré-commit prometido em 5 arquivos sem hook algum), ADR-0009 travada em `Proposed` bloqueando o MUDA RNF1, e a skill `eu-tenho-tdah` sem requisito no TRUTH.

## Mudanças

### R1 — ADICIONA: inventário de skills validado mecanicamente no CI
- DADO os manifestos `.claude-plugin/plugin.json` e `.claude-plugin/marketplace.json` QUANDO o job `ci` roda ENTÃO um step compara cada diretório `skills/<nome>/` com as descrições dos dois manifestos (case-insensitive, conforme lição de 2026-07-20) e falha nomeando a skill ausente e o manifesto omisso
- DADO os dois manifestos citando as 9 skills atuais QUANDO o check roda ENTÃO passa sem achado

### R2 — ADICIONA: gate pré-commit real por hooks versionados
- DADO este repositório com `core.hooksPath` configurado para `.githooks/` QUANDO um commit toca arquivo `.md` ou o `deps.toml` ENTÃO o hook `pre-commit` roda `validate_integrity.py .` e bloqueia o commit quando o validador sai com código ≠ 0
- DADO um projeto de usuário com `deps.toml` QUANDO a `guarding-doc-integrity` faz o bootstrap ENTÃO ela oferece a instalação do hook (template versionado + `git config core.hooksPath`), sem sobrescrever hook existente (RNF3) e sem quebrar quando o usuário recusa
- DADO os cinco arquivos promissores do DT-005 (`deps.toml`, SKILL da `guarding-doc-integrity`, `canonical-rules.md`, `README.md`, TRUTH.md) QUANDO a delta consolida ENTÃO a promessa descrita bate com o mecanismo real (hook versionado opt-in + CI), sem prometer validação que não existe

### R3 — ADICIONA: perfil de escrita `eu-tenho-tdah` reconhecido como skill do plugin
- DADO o plugin instalado QUANDO as skills são listadas ENTÃO `eu-tenho-tdah` está disponível sob o namespace `sdd-iuri:` como perfil de escrita always-on, fora do ciclo de features, e o README e os manifestos a documentam como tal

### RNF1 — MUDA RNF1 (delta-000): economia de tokens é requisito, não consequência
- Métrica: `TRUTH.md` ≤ 800 linhas (acima disso, particiona); o analyze lê só o cabeçalho-resumo do plan (≤15 linhas), nunca o plano inteiro
- Verificação: `check_cycle.py` C5; contrato de insumos em `analyze.md`
- Exceção (ADR-0009): documentação **cliente** é entregável jurídico — completude e fidelidade dominam e a economia de tokens não se aplica; documentação **interna** segue o RNF integralmente

## Fora de escopo
- Check mecânico do doc-profile no `check_cycle.py` (presença + schema) — perímetro do ADR-0006: mecanizar depois que o formato estabilizar; roteado como pendência abaixo.
- Fases 1–5 do plano de upgrade (deltas 014–018).
- Migração de referências imutáveis a `STATE.md` ou ao caminho legado (guardas DT-006/DT-010).
- Hook pré-commit obrigatório/auto-instalado em projetos de usuário — instalação é opt-in oferecida no bootstrap (RNF3).

## Dependências e riscos
- [x] Avaliar o check mecânico do doc-profile no `check_cycle.py` quando o formato do perfil estabilizar (condição da ADR-0009) — roteado como DT-013.
- A promoção da ADR-0009 a `Accepted` se apoia na evidência do piloto doc-profile+doc-entregavel (4 repos IMEX, 8 exports, 2026-07-20); a delta externa com gate do specify (travelplanner) segue pendente e continua sendo o gatilho do DT-004 — a promoção não o quita.
- `core.hooksPath` não se propaga por clone: cada checkout ativa o hook uma vez (documentado no bootstrap da skill).
