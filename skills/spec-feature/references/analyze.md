# Gate analyze — verificação cruzada spec × plan × tasks × regras canônicas

**Read-only.** Roda entre `tasks` e `implement`, sempre, no ciclo completo (é barato — não pule "porque a spec é simples"). Não corrige nada: reporta e, quando CRÍTICO, bloqueia.

Insumos: `spec.md`, `tasks.md`, **só o cabeçalho-resumo** do `plan.md` (o bloco do template resumo-plan.md no topo do arquivo, do comentário inicial até a linha `**Riscos assumidos:**`), `TRUTH.md`, `canonical-rules.md` da skill projeto-init + `CLAUDE.md` do projeto. As regras canônicas consideradas são as dos **módulos aplicáveis ao tipo** (matriz de detection.md), mesmo que o CLAUDE.md do projeto não as monte.

## Metade mecânica: rode o script primeiro

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/spec-feature/scripts/check_cycle.py specs/NNN-nome
```

Cobre os checks **1 e 2** abaixo, a verificação de archive (cycle.md, regra 6), o limiar do TRUTH.md, a pendência roteada do archive (cycle.md, regra 7 — C6), a medição do split de PR (C7, ver abaixo) e a cobertura do plano de testes (C8, delta-015), a validade do grafo de tasks (C9) e a convergência mínima no archive (C10, delta-016) — emite as linhas da tabela já no formato do relatório. Exit 1 = há ALTO/CRÍTICO. Os checks **3 e 5** são juízo (scope creep, regra canônica): continuam com o modelo, sempre. Diligência não substitui o script; o script não substitui a leitura.

## Ordem de checagem (do barato ao caro)

1. **Aceite verificável** — todo Rn da spec tem DADO/QUANDO/ENTÃO bem-formado (os três campos, ENTÃO com resultado verificável). Validação estrita: Rn sem cenário = ALTO. Todo RNFn tem Métrica com limiar verificável e Verificação preenchidas — RNF em prosa ("rápido", "seguro") ou qualidade redigida como Rn sem limiar = ALTO.
2. **Cobertura spec ↔ tasks** — cada Rn/RNFn tem ≥1 task (`cobre: Rn`/`RNFn`); cada task mapeia a um requisito ou declara `cobre: infra`. Detecta órfãos nos dois sentidos (requisito sem task = ALTO; task sem requisito nem `infra` = MÉDIO).
3. **Consistência spec × plan** — o resumo do plan cobre os mesmos Rn; nada no plano sem base na spec (scope creep); plano não contradiz cenários de aceite.
4. **Duplicação/divergência com o TRUTH.md** — requisito novo que duplica ou conflita com requisito vigente não marcado como MUDA/REMOVE (= ALTO); bloco MUDA que não repete cenário vigente aparentemente ainda válido (= ALTO — o archive substitui integralmente; cenário não repetido se perde).
5. **Regras canônicas** — plano/tasks não violam `canonical-rules.md` + CLAUDE.md do projeto. Exemplos: changelog em EN, sobrescrita de arquivo existente (clobber), PR acima do limiar canônico de tamanho planejado num único passo, versão com fonte da verdade ≠ tag git. Violação = CRÍTICO.

## Severidades e veredito

- **CRÍTICO** — viola regra canônica → **bloqueia** o implement até correção.
- **ALTO** — Rn sem task · task sem verificação · conflito com TRUTH.md → recomenda corrigir antes.
- **MÉDIO/BAIXO** — reporta apenas. Achado fora dos enums acima → MÉDIO por default.

**Veredito:** `BLOQUEADO` somente com ≥1 CRÍTICO · `LIBERADO COM RESSALVAS` com ALTO/MÉDIO pendentes · `LIBERADO` sem achados relevantes. Ressalvas: o usuário decide seguir ou corrigir.

**Forma do PR (split condicional, delta-003):** o **C7** do `check_cycle.py` mede as linhas adicionadas em `specs/NNN-nome/` contra o merge-base e reporta BAIXO quando passam do limiar de PR da regra canônica — não bloqueia (a medição informa; o split é decisão do ciclo). Achado do C7 → o ciclo abre primeiro o PR só dos artefatos (regra em cycle.md, "PR da delta — split condicional"). Sem git ou sem merge-base o C7 se omite; nesse caso meça à mão com `git diff origin/main --shortstat -- specs/NNN-nome/`.

## Formato do relatório (gravar em `specs/NNN-nome/analyze.md`)

```markdown
# Analyze — delta-{{NNN}} · {{AAAA-MM-DD}}
| # | Severidade | Onde | Inconsistência | Ação sugerida |
|---|---|---|---|---|
| 1 | CRÍTICO | tasks.md T3 | {{...}} | {{...}} |

**Veredito:** LIBERADO | LIBERADO COM RESSALVAS | BLOQUEADO
```

Sem achados: tabela vazia + veredito LIBERADO (o relatório existe mesmo limpo — é o registro de que o gate rodou). Após correções de um BLOQUEADO, rode o gate de novo e sobrescreva o relatório.
