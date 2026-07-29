# Analyze — delta-019 (rename-deltaspec)

**Veredito: LIBERADO COM RESSALVAS** · 2026-07-28 · perfil enxuto (aprovado 2026-07-28)

## Metade mecânica (`check_cycle.py specs/019-rename-deltaspec`, exit 0)

| # | Severidade | Onde | Achado | Tratamento |
|---|---|---|---|---|
| 1 | BAIXO | test-plan.md | dispensado no cabeçalho — verificação mecânica declarada nas tasks | aceito: perfil enxuto aprovado (R36/delta-015); a delta não introduz lógica, só substitui identificador |

Achados corrigidos antes deste relatório: `R5` estava declarado como requisito funcional quando é MUDA de RNF (formato Métrica/Verificação) — reclassificado como `RNF1`, com as referências de `tasks.md` e `plan.md` ajustadas.

## Metade humana (checks 3 e 5 do `analyze.md`)

**Check 3 — scope creep spec × plan.** Sem creep. O plano não introduz artefato além do que a spec declara; a única decisão de projeto que ele acrescenta é a **renúncia** a uma camada de compatibilidade (`sdd-iuri.validator` como fallback), justificada porque o hook já instalado num projeto é cópia com a chave antiga embutida — o template novo não o alcança, então o fallback só serviria ao caso que a migração já cobre. Renúncia registrada no plano e coberta pelo terceiro cenário do R5.

**Check 5 — violação de regra canônica.** Nenhuma. Três regras foram confrontadas explicitamente:

- **Imutabilidade de ADR** (CLAUDE.md): a ADR-0016 não edita nem supersede as anteriores; ADRs 0001, 0004, 0008 e 0011 mantêm o nome de época intacto.
- **Fonte canônica única:** o nome novo tem um dono funcional (`plugin.json:name`); os demais arquivos citam. O `validate_integrity.py` roda PASS no repo (C1/C2/C3), então nenhum valor canônico foi materializado fora do dono.
- **Registro histórico:** `specs/_archive/**` (134 ocorrências) e as seções lançadas do `CHANGELOG.md` ficaram intactas — o grep de resíduo confirma que o que sobrou com o nome antigo é exatamente histórico congelado, a seção de migração do README e as citações deliberadas da ADR-0016.

## Ressalva assumida

Consumidor com o plugin instalado perde `/sdd-iuri:*` até reinstalar. Não é defeito da spec: é o custo declarado do breaking change, endereçado pela seção de migração do README (R5) e sinalizado pelo corte da v1.0.0.
