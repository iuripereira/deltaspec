<!-- resumo deltaspec · ≤15 linhas · única parte do plano lida pelo analyze e pelo humano -->
**Objetivo:** `--rodape TEXTO` e `--marca-dagua TEXTO` no `exporta_entregavel.py`, aplicados nos dois formatos, para que o entregável confidencial não dependa de edição manual (quita o DT-011). **Cobre:** R1 (da delta-031). **Decisões duráveis → ADRs:** nenhuma — mecanização de instrução já normatizada no `juridico.md`, sem dependência nova (python-docx e Chrome já são o pipeline). **Riscos assumidos:** marca d'água em pdf depende de `position: fixed` repetir por página no print do Chrome (comportamento estável do headless); extração de texto rotacionado no selftest degrada com aviso se a ferramenta local não a suportar.

## Desenho

**PDF (Chrome headless):** elemento `position: fixed` repete em toda página impressa. Dois blocos injetados no HTML quando a flag vem: `.rodape-conf` (fixo, base da página, centralizado, 8pt) e `.marca-dagua` (fixo, centro, `rotate(-45deg)`, ~90pt, `opacity .08`, `z-index -1` — atrás do texto). Nada muda sem flag.

**DOCX (python-docx):** rodapé via `section.footer` (parágrafo centralizado, 8pt). Marca d'água = VML `v:shape` com `v:textpath` no cabeçalho da seção — o mesmo XML que o Word gera em Design → Marca-d'água; inserido por `parse_xml`, cinza claro, diagonal. Funções puras separadas do I/O onde couber (montagem do VML é string → testável).

**CLI:** dois `add_argument` opcionais, default `''` (= desligado). `selftest` ganha um caso com as duas flags: docx — rodapé no XML do footer e `textpath` da marca no header; pdf — texto do rodapé presente em **todas** as páginas extraídas e o da marca em ao menos uma (normalizando espaços), degradando com aviso sem extrator.

## Passos (TDD)

1. **Vermelho:** caso novo no selftest com `--rodape CONFIDENCIAL --marca-dagua CONFIDENCIAL` — asserts de docx e pdf falham (flags nem existem).
2. **Verde pdf:** CSS + injeção condicional dos dois divs em `monta()`.
3. **Verde docx:** `_rodape()` e `_marca_dagua_vml()` aplicados em toda seção do documento.
4. **Regressão:** caso vigente do selftest (sem flags) continua verde — saída inalterada.
5. SKILL.md (passo 4 do export) cita as flags para os tipos confidenciais; `juridico.md` aponta a mecanização onde hoje diz aplicação manual.
6. Registros: CHANGELOG `[Não lançado]`, HANDOFF; quito do DT-011 no archive.

## Verificação

- `exporta_entregavel.py --selftest` verde com o caso novo falhando antes da implementação (vermelho registrado no commit de TDD).
- Mutação: remover a injeção do rodapé no pdf e o VML no docx — cada uma quebra o selftest.
- `check_cycle.py specs/031-rodape-marca-dagua` sem ALTO/CRÍTICO; `validate_integrity.py .` PASS.
