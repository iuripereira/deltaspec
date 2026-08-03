<!-- resumo deltaspec · ≤15 linhas · única parte do plano lida pelo analyze e pelo humano -->
**Objetivo:** parar de recomendar aos projetos mecanismos que o próprio framework não usa — tirar do `doc-profile.yaml` um campo que ninguém lê e pôr a política de dependência sob o manifesto que a `guarding-doc-integrity` oferece. **Cobre:** R1, R2, RNF1 (da delta-028) **Decisões duráveis → ADRs:** nenhuma — matar o `version` e reduzir espelhos executam regras vigentes (regra de ouro, teto de espelhos da própria skill), não renunciam a alternativa nova. **Riscos assumidos:** o `SECURITY.md` deixa de nomear a ADR-0023 e passa a apontar, e a metade negativa do RNF6 continua como `grep` no CI, agora declarada como exceção em vez de silêncio.

## Desenho

Três frentes independentes entre si:

1. **C11 sem `version`** — a constante `NUCLEO_TOPO` perde o primeiro item; o campo sai do template distribuído. Afrouxa o check, então nenhum perfil existente quebra.
2. **Espelhos sob manifesto** — `[[owner]]` novo no `deps.toml`: dono `CLAUDE.md`, espelhos `README.md`, `README.en.md` e `specs/TRUTH.md`, padrão `ADR-0023`. O `SECURITY.md` perde o identificador e ganha ponteiro. O step do CI encolhe para a metade negativa, com comentário dizendo por que ela ficou.
3. **Relato do perfil desatualizado no `projeto-init`** — prosa normativa na `SKILL.md`: comparar categorias do perfil existente com as do template, relatar o que falta, escrever só com aprovação. Nada de decisão registrada é tocado.

**Ordem obrigatória entre 2 e o archive:** o `[[owner]]` nasce já com `specs/TRUTH.md` entre os espelhos. Sancioná-lo depois faz o C2 acusar o TRUTH no primeiro pré-commit — o TRUTH cita a ADR e só é reescrito no archive.

## Passos

### T1 — C11 e template sem `version` (TDD)

1. **Vermelho.** Em `selftest_c11`, a fixture `nucleo.replace("version: 1\n", "")` hoje espera 1 ALTO; passa a esperar 0.
2. **Verde.** `NUCLEO_TOPO = ("decisao", "publico", "artefatos")`.
3. Fixture nova: perfil **com** `version` continua válido (0 achado) — chave fora do núcleo nunca é erro.
4. `version` sai de `skills/projeto-init/references/templates/doc-profile.yaml`, com uma linha no comentário do topo dizendo que o campo foi retirado e por quê.
5. O `doc-profile.yaml` da raiz deste repo perde o campo junto — dogfood.

### T2 — política de dependência sob o `deps.toml`

1. `SECURITY.md`: as duas menções passam a apontar para o `CLAUDE.md` sem repetir `ADR-0023`.
2. `deps.toml`: `[[owner]]` com dono, os três espelhos e `pattern = 'ADR-0023'`.
3. `.github/workflows/ci.yml`: o loop `grep -q ADR-0023` sai (o C1 cobre); fica o grep negativo, com comentário nomeando a lacuna (`validate_integrity` não tem check de padrão proibido).
4. `validate_integrity.py .` tem de sair `PASS` — C1 achando o padrão nos quatro, C2 não achando fora deles.

### T3 — relato do perfil desatualizado no `projeto-init`

Prosa na `SKILL.md` da skill: a comparação, o relato e a regra de só escrever com aprovação, ancorada no R2/RNF3 (idempotência). Sem script — é passo do agente, como o resto do init.

### T4 — registros

DT-025 e DT-026 quitam no archive (precedente da 026/027: quitação com o `Encerrado` apontando para `_archive/`, que só existe lá). Aqui entra o progresso, o CHANGELOG sob `[Não lançado]` e o HANDOFF.

## Verificação

- `check_cycle.py --selftest` verde, com a fixture do `version` invertida e a nova.
- `validate_integrity.py .` → `PASS`; mutação: apagar `ADR-0023` de um dos espelhos derruba o C1.
- `check_cycle.py specs/028-propagacao-e-espelhos` sem CRÍTICO.
- O `doc-profile.yaml` da raiz sem `version` continua com zero achado no C11.
