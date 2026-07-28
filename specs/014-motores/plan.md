<!-- resumo sdd-iuri · ≤15 linhas · única parte do plano lida pelo analyze e pelo humano -->
**Objetivo:** recontratar os motores (Fase 1 do upgrade) — pin do max como fork deliberado documentado com divergência/gatilho, verificação datada de versões, review em dois eixos paralelos. **Cobre:** R1, R2 (da delta-014) **Decisões duráveis → ADRs:** ADR-0012 (manter fork max 0.8.0; renúncias: migrar já, contrato duplo) **Riscos assumidos:** fork congela ganhos do upstream até a delta-017; verificação de versão é pontual (data na tabela denuncia staleness).

---

## Contexto para execução sem sessão

Repo do framework. Motores instalados: max 0.8.0 (pin), superpowers 6.0.3 local (testada declarada 6.1.1, upstream 6.2.0 de 2026-07-24, faixa 6.x), ponytail 4.8.4. Upstream do max divergiu (write-prd removido, grilling fatorado) — fonte: pesquisa verificada de 2026-07-28. Decisão do usuário: manter pin.

## Passo 1 — ADR-0012 (R1)

`docs/adrs/ADR-0012-recontratacao-motores.md` (template Nygard do repo): Context (divergência upstream vs plugin distribuído 0.8.0; R30 do TRUTH contrata write-prd na descoberta), Decision (manter pin 0.8.0 como fork deliberado; adapters ganham verificação datada + nota de divergência; gatilho de migração = delta-017/Fase 4, quando to-tickets importa — ou breaking do fork), Consequences (ganhos congelados: wayfinder/to-tickets; renúncias: migrar já — MUDA R30 + retrabalho da descoberta sem ganho imediato; contrato duplo — flexibilidade sem consumidor).

## Passo 2 — adapters.md (R1 + R2)

- **Tabela de política de dependência:** nova coluna "Verificado em"; linha do max ganha "fork deliberado (ADR-0012) — upstream divergiu (write-prd removido, grilling fatorado); reavaliar na delta-017"; linha do superpowers ganha "upstream 6.2.0 verificada em 2026-07-28 (faixa ok); testada 6.1.1"; ponytail "4.8.4 verificada em 2026-07-28".
- **Seção grill-me:** nota de 1 linha sobre a fatoração upstream (`grilling` é o motor por trás de grill-me/grill-with-docs no upstream; contrato aqui permanece nas skills do plugin 0.8.0).
- **Seção review (nova redação):** dois eixos independentes — **Spec** (motor `superpowers:requesting-code-review`, conformidade Rn×diff) e **Qualidade** (`ponytail:ponytail-review`, delete-list) — **em subagentes paralelos quando o harness suporta**, cada eixo cego ao outro; achados convergentes tratados antes do PR. Fallbacks vigentes intactos (inline sequencial + avisos).

## Passo 3 — cycle.md (R2)

Linha da fase review na tabela: saída passa a citar os dois eixos ("eixo Spec ok; eixo Qualidade ok com delete-list tratada") e a execução paralela por subagentes quando disponível, senão inline (adapters.md é o dono do contrato — cycle.md referencia).

## Passo 4 — CHANGELOG + HANDOFF (infra)

`[Não lançado]`: Adicionado (ADR-0012; verificação datada na política de pins; review em dois eixos paralelos) / Mudado (adapters/cycle refletem o contrato). HANDOFF: delta-014 em curso → concluída ao fim.

## Verificação de conjunto

`check_cycle.py specs/014-motores` sem ALTO/CRÍTICO · `validate_integrity.py .` PASS (adapters.md está nos scan_globs — não materializar valores governados) · links do ADR-0012 vivos (C3) · grep confirma: nenhuma seção dos adapters ainda descreve o review como sequencial-único.

## Archive (pós-merge)

R1→R34, R2→R35 no TRUTH (domínio "Ciclo de features" para R35; R34 em "Ciclo de features" junto de R8/R9 — motores); sem MUDA; mover para `_archive/`; `check_cycle.py` pós-consolidação; tag `v0.10.0` no merge do archive (feat = MINOR).
