# ADR-0034: TRUTH como índice + partições, com requisito como heading e cenário atômico

- **Status:** Accepted
- **Data:** 2026-08-13
- **Supersedes:** —
- **Superseded by:** —

## Context

O `specs/TRUTH.md` deste repo chegou a 400 linhas, ~30k tokens aproximados e 12 domínios (limiar exato do C5) com 81 requisitos em formato de bullet de 2 níveis: requisito não aparece em outline de editor nem TOC do GitHub, cenários DADO/QUANDO/ENTÃO chegam a 1.348 chars numa linha, e 7 requisitos do registro de débitos vivem sob "Inicialização de projeto". O formato nunca teve ADR — vivia em comentário de template, prosa do `cycle.md` e no débito DT-036 (registro `debts/`), cujo gatilho dizia "a delta do particionamento nasce da acusação do C5, nunca antes dela". O DT-042 registrou o custo colateral: MUDA integral de requisito gigante quase perdeu 5 requisitos na delta-047. A comparação com o OpenSpec (handoff de 2026-08-09) apontou as duas divergências estruturais reais: lá a verdade é particionada por capability com requisito-como-heading e *Purpose* por domínio.

## Decision

O TRUTH adota (delta-055) o formato navegável: **requisito como heading `### Rn (delta-NNN) — título`**, **um cenário DADO/QUANDO/ENTÃO por bullet em linha única** (efeitos atômicos do mesmo commit como sub-bullets de 1 linha), **`> Propósito:` por domínio**, e — neste repo — **`specs/TRUTH.md` como índice enxuto** com a verdade em `specs/truth/<dominio>.md` (~10 partições; domínio de 1 requisito agrupa). O gatilho do DT-036 ("só quando o C5 acusar") é **revogado por decisão do usuário (2026-08-13)**: a dor de legibilidade humana bastou, e migrar em dois tempos (reformatar agora, particionar depois) custaria duas reescritas em massa do mesmo arquivo. A âncora `Rn (delta-NNN)` permanece na mesma linha física do heading, então a regex `ALVO` do `check_cycle.py` casa sem mudança de script.

Renúncias registradas:

- **Manter bullets e só particionar** — rejeitado: resolve custo de contexto, não legibilidade; requisito continuaria fora do outline e o cenário-parágrafo continuaria ilegível.
- **Renumerar os IDs na reorganização** — rejeitado: `Rn`/`RNFn` são citados em ADRs, debts, specs arquivados e commits; renumerar quebraria a rastreabilidade que é o ponto do framework.
- **Índice com lista de IDs por domínio** — rejeitado: sem gerador é duplicação que apodrece a cada archive (a mesma razão que fez o `DEBT.md` virar índice gerado na ADR-0031); a âncora do heading + grep respondem "onde está R42".
- **Particionar o template para projetos novos desde o dia 1 (à la OpenSpec)** — rejeitado: greenfield com 3 requisitos e 10 arquivos de verdade é overhead; nasce monolítico no formato novo e particiona quando o C5 acusar.
- **Gate mecânico contra perda semântica na reescrita editorial** — rejeitado como gate permanente (é juízo, perímetro da ADR-0006); a delta usa um contador descartável de cenários por requisito, que morre com ela.

## Consequences

- Cada requisito ganha âncora linkável e aparece em outline/TOC; leitura por domínio custa uma partição, não o arquivo inteiro; o sinal de domínios do C5 deixa de acusar (partições presentes o omitem por design, R66).
- O suporte a `specs/truth/*.md` (C4/C5/`--proximo-numero`), até então só exercitado em selftest, passa a rodar em produção — este repo é o dogfood.
- Custo aceito: "grep na verdade" varre ~10 arquivos em vez de 1; links internos das partições ganham um nível de profundidade; `deps.toml` passa a apontar `specs/truth/nao-funcionais.md` como dono dos limiares do RNF1.
- O template da spec-feature e as regras de archive do `cycle.md` passam a escrever o formato novo; projetos existentes em bullets seguem válidos — nenhum gate exige migração.
