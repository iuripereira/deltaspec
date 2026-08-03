<!-- resumo deltaspec · ≤15 linhas · única parte do plano lida pelo analyze e pelo humano -->
**Objetivo:** dar ao C3 um conjunto próprio de arquivos varridos, em vez de herdar o do C2, para que link quebrado nos registros vivos deixe de sair como `PASS`. **Cobre:** R1 (da delta-027) **Decisões duráveis → ADRs:** nenhuma — a decisão de escopo (`_archive` fora) executa o R47 vigente, não renuncia a nada novo. **Riscos assumidos:** a chave nova no `deps.toml` propaga por default nomeado em vez de migração, então projeto-alvo com histórico imutável fora de `_archive/`/`docs/adrs/` vê achados na primeira execução — é link quebrado de verdade, mas chega sem aviso.

## Desenho

Uma função, `main()` do `validate_integrity.py`, hoje faz:

```python
scan = collect(root, cfg.get("scan_globs", ["**/*.md"]))
scan -= collect(root, cfg.get("exclude_globs", []))   # ← serve C2 e C3
```

Passa a ter dois conjuntos com nomes que dizem a que servem: `scan_valores` (C2, inalterado) e `scan_links` (C3, com exclusão própria). O C3 ganha também o corte do atalho `../../`, no mesmo lugar onde já corta `http://`, `mailto:` e `/`.

Constante nomeada, porque é o default que propaga sem migração:

```python
# Histórico imutável: registro de época (R47) — apontar rot que a política proíbe
# corrigir é ruído. Default para manifesto sem a chave (delta-027).
EXCLUDE_LINKS_PADRAO = ("**/_archive/**/*.md", "docs/adrs/**/*.md")
```

## Passos (TDD — tipo tooling, lógica pura)

1. **Vermelho.** Fixture no `selftest()`: manifesto com `exclude_globs = ["NOTAS.md"]`, arquivo `NOTAS.md` com link morto → hoje sai `PASS`, e o assert exige `FAIL` com `[C3]`.
2. **Verde.** Separar `scan_valores` de `scan_links` em `main()`; o C3 itera `scan_links`.
3. **Vermelho.** Fixture: `DEBT.md`-like com `[#88](../../issues/88)` → hoje viraria `[C3] link morto`; o assert exige `PASS`.
4. **Verde.** No laço do C3, somar `"../../"` ao `startswith` que já ignora `http://`/`mailto:`/`#`/`/`.
5. **Vermelho.** Fixture: link morto dentro de `docs/adrs/` e de `specs/_archive/`, manifesto **sem** `exclude_links_globs` → o assert exige `PASS` (default protege) e, com a chave declarada como `[]`, exige `FAIL` (a chave manda).
6. **Verde.** `exclude_links_globs` lido do manifesto com `EXCLUDE_LINKS_PADRAO` como default.
7. **Propagar o contrato:** chave no `templates/deps.toml` da `guarding-doc-integrity` com comentário do porquê, no `deps.toml` deste repo, e a docstring do módulo (linha do C2/C3) refletindo os dois conjuntos.
8. **Registrar:** DT-027 quitado no `DEBT.md`; CHANGELOG sob `[Não lançado]`; HANDOFF.

## Verificação

- `validate_integrity.py --selftest` verde, e cada fixture nova falhando antes do passo que a resolve.
- `validate_integrity.py .` neste repo → `PASS` com o número de links verificados **maior** que 105 (os registros vivos entraram).
- Mutação: trocar `scan_links` de volta por `scan_valores` no laço do C3 quebra o selftest.
