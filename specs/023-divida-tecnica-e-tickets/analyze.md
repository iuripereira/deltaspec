# Analyze — delta-023 · 2026-08-01
| # | Severidade | Onde | Inconsistência | Ação sugerida |
|---|---|---|---|---|

Checks mecânicos C1–C10: limpos, sem achado (1ª rodada).

**Check 3 (spec × plan).** O resumo do plan cobre R1, R2 e R3, sem item de plano fora da spec: `CLAUDE.md` entra pelo cenário da ADR-0021 no R3, e `CHANGELOG`/`HANDOFF` são mecânica do ciclo (`cobre: infra` no T9), não escopo novo. Nenhuma contradição entre plano e cenários de aceite.

**Check 4 (divergência com o TRUTH, juízo).** O bloco MUDA R18 repete integralmente os três cenários vigentes ainda válidos (linha `DT-NNN` com numeração global; quitado muda de status e nunca some; scaffold pelo `projeto-init`) e acrescenta dois — campos de fila e conjunto de estados. Nada de válido se perde na substituição integral do archive (ADR-0005). Os requisitos novos não colidem com R16 (pendência roteada segue igual) nem com R20 (o handoff continua escrevendo no DEBT).

**Check 5 (regras canônicas).** CHANGELOG é task explícita (T9); nenhuma sobrescrita de arquivo existente; identificadores e prosa em PT-BR; script stdlib pura; versão pela tag no merge do archive. **Split de PR:** o C7 não acusou porque os artefatos somam 113 linhas, bem dentro do limiar — mas o PR único (artefatos + script + 2 ADRs + política + migração) passaria do limiar canônico, então o split é feito por decisão do ciclo, não por medição: artefatos primeiro, implementação depois, archive por último.

**Pendência aberta na spec** (`- [ ]` propagar ao template distribuído): correta nesta fase — o C6 só a cobra em delta arquivada, e ela vira `DT-NNN` no archive (R16).

**Veredito:** LIBERADO

---

## Review em dois eixos (2026-08-01, subagentes paralelos — R35)

**Eixo Spec:** 13 de 14 cenários ATENDEM; R2.1 veio PARCIAL. **Eixo Qualidade:** APROVADO COM AJUSTES, com 6 must-fix e ~60 linhas de gordura.

**Convergente (apontado pelos dois eixos, tratado primeiro):** `parse_fila` aceitava qualquer `!nome(data)` como override e a chave de ordenação empatava override desconhecido com trilha — um typo em `!security` rebaixaria um impedimento em silêncio. Corrigido: vocabulário fechado contra `OVERRIDES` e `precedencia()` extraída como função pura.

**Achados do eixo Qualidade aplicados:**

| Achado | Correção |
|---|---|
| Script rejeitava todo projeto scaffoldado (template do `projeto-init` tem 7 colunas) — testado, exit 1 | `legado()`: tabela sem `Fila` degrada em vez de rejeitar, no padrão retrocompatível do R40 |
| `docs/tickets/` fora do `.gitignore` — o score derivado a um `git add -A` de virar segunda fonte | Entrada no `.gitignore`, com o porquê citando a ADR-0020 |
| `--selftest` do `debito.py` não rodava no CI | Adicionado ao step "Selftest dos gates" |
| `diff` estourava traceback com `--externo` ausente ou malformado | `try/except` + checagem de tipo na fronteira de confiança |
| `estado()` estourava `IndexError` com célula começando em `(` | Uma linha, sem o ternário e sem o `.get` duplicado |
| Dialeto do Jira emitido sem `projectKey` — o `acli` recusaria o lote | Só é emitido com `--projeto`; sem a flag, avisa em vez de gerar payload quebrado |
| `ESCALA` morta, faixas `9`/`3` mágicas, `COR_ETIQUETA` supérfluo, preâmbulo duplicado, `churn` chamado duas vezes, parser de args à mão | Constantes nomeadas, `carregar()` única, `lru_cache`, `argparse` |
| Comando `gh` copiado verbatim entre a SKILL e a política; regra do score repetida 8 vezes | A SKILL passou a apontar o reference; duas cópias cortadas |
| Lição datada dentro da política | Movida para a seção Lições do `DEBT.md`, que é a dona |
| Dívida confessada em prosa nas ADRs sem `DT-NNN` | DT-020 (limiares sem calibração) e DT-021 (dialeto Jira não executado) |

**Bug real revelado pela fixture cobrada:** o eixo Spec apontou que CT2 e CT7 estavam marcados sem a fixture que descreviam. Ao escrevê-las, o `stale` se mostrou cego a edição de linha — `git log -S` só conta quando a string passa a existir ou some. Trocado por `-G`. Lição registrada no `DEBT.md`.

**Recusa justificada:** o tamanho (~890 linhas) não foi reduzido além dos cortes acima. O script *é* a feature; os dois eixos concordaram que não é gordura, e o split já separou artefatos de implementação.
