---
name: guarding-doc-integrity
description: Use when editing docs in a repo that has a deps.toml manifest; when a business-rule value duplicated across files (PRD, CLAUDE.md, data dictionary) changed; when the user asks to set up doc integrity tracking, canonical-source governance, or mirrored-value validation; or before committing changes to canonical docs.
---

# Guarding Doc Integrity

## Visão geral

Governança de fontes de verdade: **um assunto tem um arquivo dono; valor concreto só existe no dono + espelhos sancionados; todo o resto do repo linka.** O mapa dono→espelhos vive num manifesto `deps.toml` versionado no repo, e um validador roda como gate determinístico em duas camadas: **hook pré-commit versionado (opt-in, instalado no bootstrap)** e **gate de sessão** (o comando manual abaixo, para quem não instalou o hook). A integridade não pode depender da diligência de uma sessão — greps ad-hoc não são garantia; o script é.

## Quando usar

- O repo tem `deps.toml` e a mudança toca qualquer `.md`.
- Um valor de regra de negócio mudou e está (ou pode estar) duplicado em vários arquivos.
- O usuário pede rastreamento de integridade documental / consolidação de fontes de verdade.

Quando NÃO usar: repo sem docs canônicos, ou mudança que não toca arquivo mapeado. Auditoria estrutural pós-reorganização (rename/split/merge, workspace multi-repo, path hardcoded, gate sem hook, cópia órfã de script) é escopo de `deltaspec:audit-workspace` — esta skill governa valores e links dentro de um repo com manifesto.

## Fluxos

### 1. Bootstrap (repo ainda sem deps.toml)

1. Levante valores duplicados: `grep -rnE '[0-9]+ ?(km|h|%)|R\$ ?[0-9.]+' --include='*.md' .` + leitura de CLAUDE.md/PRD/README.
2. Proponha ao usuário: dono de cada assunto, espelhos sancionados (máx. 2–3 por dono), valores a rastrear.
3. Crie `deps.toml` na raiz a partir de `templates/deps.toml` (desta skill).
4. Rode o validador e corrija as violações do estado atual (duplicata fora dos sancionados vira **link** para o dono) até PASS. Esse é o baseline do repo.
5. **Ofereça o hook pré-commit** (opt-in — recusa segue sem hook, sem insistir) **via `/deltaspec:git-guard instalar`**: desde a delta-090 o template `pre-commit` é da `git-guard`, e o bloco de integridade documental (roda `validate_integrity.py .` quando o commit toca `.md` ou `deps.toml` **e a raiz tem o manifesto** — sem `deps.toml` o bloco se omite com aviso, delta-094) é o primeiro dos quatro blocos dele. O `instalar` grava `core.hooksPath .githooks` e `deltaspec.plugin-root` na config local (não versionada — o template não carrega caminho de máquina) e **nunca sobrescreve** hook nem `core.hooksPath` existentes. Instalação anterior a esta delta, com `git config deltaspec.validator`, continua funcionando — o template aceita a chave como fallback; migrar é reinstalar. Avise que a ativação é por clone (`core.hooksPath` não se propaga).

### 2. Mudança de valor canônico (cascata)

1. Edite o **dono** primeiro.
2. Atualize o `pattern` correspondente no `deps.toml` para o valor novo.
3. Edite cada **espelho** listado no manifesto.
4. `grep -rn '<valor antigo>' .` — zero ocorrências fora de históricos/changelogs (`exclude_globs`).
5. Rode o validador → só commite com PASS.

### 3. Gate pré-commit (hook opt-in + gate de sessão)

Com o hook do passo 5 do bootstrap instalado, o commit que toca `.md`/`deps.toml` valida sozinho. Sem o hook, o gate é de sessão — antes de QUALQUER commit que toque `.md` num repo com `deps.toml`:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/guarding-doc-integrity/scripts/validate_integrity.py <repo>
```

Exit 1 = corrigir antes de commitar. Nunca commitar com FAIL; reporte o resultado (PASS/FAIL + violações) ao usuário, sem silenciar.

### 4. Só links, sem manifesto (`--links-only`)

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/guarding-doc-integrity/scripts/validate_integrity.py --links-only <dir>
```

Roda **só o C3** (links markdown mortos) em qualquer diretório, sem exigir `deps.toml` — para repo ainda sem manifesto ou varredura pontual de links. Mesmos recortes do C3 (`_archive/`, ADRs, seções lançadas, crases, blocos cercados). É o núcleo que a `deltaspec:audit-workspace` importa no W1 (R60, TRUTH.md) — esta skill continua a dona única da resolução de link.

## Referência rápida

| Situação | Ação |
|---|---|
| Valor aparece fora de dono+espelhos (C2) | Substituir por link ao dono; ou promover a espelho no manifesto (decisão consciente) |
| Grafia variante (`R$2.000` vs `R$ 2.000`) | `pattern` cobre variantes: `R\$ ?2\.000` |
| Valor citado em CR/changelog/arquivo morto | Adicionar caminho a `exclude_globs` — que dispensa do C2 e **não** do C3 |
| Link morto (C3) | Corrigir o alvo; ao arquivar um doc, varrer e reescrever toda referência |
| Link em registro imutável (archive, ADR) | Fora do C3 por `exclude_links_globs`, que tem esse default quando a chave é omitida — é registro de época, não se corrige |
| Link em seção lançada do changelog, em crase ou em bloco cercado | Fora do C3 por desenho (delta-029): release publicado é imutável e link em crase é sintaxe citada. **Contrapartida:** referência de verdade dentro de bloco cercado (docstring, pseudocódigo) deixa de ser vigiada — tire-a da cerca se quiser cobertura |

## Erros comuns

- Editar só o dono e commitar — espelho drifta (C1 pega).
- "Eu greppei, tá ok" em vez de rodar o gate — diligência ≠ garantia; rode o script.
- Atualizar os arquivos e esquecer o `pattern` no manifesto — C1 falha no próprio dono; manifesto acompanha a mudança.
- Criar duplicata nova "só dessa vez" sem registrar — C2 falha; ou vira espelho no manifesto, ou vira link.
