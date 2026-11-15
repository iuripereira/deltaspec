---
name: project-review-dotclaude
description: Use when a repository's or a whole workspace's `.claude/` folder needs auditing against what Claude Code actually reads — plans, prompts, notes or scripts parked in `.claude/`, a legacy `commands/` folder, `worktrees/` or other runtime leftovers with no rule in the versioned `.gitignore`, a hook cited in `settings.json` that is not committed, `.claude/handoffs/` with no `HANDOFF.md` index, or a canonical document living in `.claude/` while live files cite it. Only the read-only `auditar` mode exists today; it never writes to the audited repository. A `migrar` mode is not implemented yet. Triggers include "/deltaspec:project-review-dotclaude", "auditar .claude", "o .claude está bagunçado", "boas práticas do .claude", "o que pode ficar no .claude", "planos e prompts no .claude", "revisar a pasta .claude".
---

# Project Review — `.claude/`

## Visão geral

`.claude/` é a pasta que o Claude Code lê: configuração, hooks, skills, agentes. Pasta que ele desconhece é inerte, sem custo e sem aviso — e por isso vira estacionamento de plano, prompt, auditoria, script e documento canônico, até alguém publicar um handoff interno por engano ou descobrir que um documento "dono" mora num lugar que ninguém procura.

Esta skill mede a distância entre o que está em `.claude/` e a doutrina "configuração que o Claude Code lê, mais `handoffs/`". O dono da doutrina, da lista do que pode ser versionado e da severidade de cada check é o [catálogo](references/catalogo.md); aqui só o fluxo.

## Fronteiras

| Skill | Objeto |
|---|---|
| `project-review-dotclaude` | **o que mora** em `.claude/` (checks D) |
| `git-guard` | higiene de git; `.claude/` sem `settings.json` nem guarda de agente é o **G3** de lá, não um D |
| `audit-workspace` | consistência de referência entre repos (W); o **W7** mapeia o diário de bordo de cada repo, o **D7** cobra só `.claude/handoffs/` sem `HANDOFF.md` |

O motor é um só: `audit_workspace.py` descobre os repositórios, agrupa por achado e imprime. Os checks D moram em `scripts/dotclaude.py`, desta skill. Os três blocos rodam disjuntos — uma flag por vez.

## Fluxo de auditoria

1. **Alvo.** Um repositório: rode dentro dele. Um workspace: rode na pasta-mãe e decida a profundidade — sem `--profundidade`, a varredura enxerga um nível só.

2. **Execução.**

   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/skills/audit-workspace/scripts/audit_workspace.py . --apenas-dotclaude
   python3 ${CLAUDE_PLUGIN_ROOT}/skills/audit-workspace/scripts/audit_workspace.py . --apenas-dotclaude --profundidade 3
   ```

   Exit 0 = sem achado; 1 = achado(s); 2 = alvo não é repositório nem workspace reconhecível, ou `--apenas-dotclaude` junto de `--apenas-git`.

   A auditoria lê a **árvore de trabalho** de cada repositório — o branch que está em checkout, não o default. Um `.gitignore` que já tem a regra na `develop` e não na branch corrente acusa D3.

3. **Triagem.** A saída vem agrupada por check, do ALTO ao MÉDIO, e o D6 vem no bloco informativo, que não derruba o resultado. O D8 substitui o D1 para o arquivo citado por arquivo vivo: o destino dele é `docs/` ou `scripts/`, não sair do repositório — sair quebraria quem cita.

4. **Relatório.** Reporte a saída bruta, sem resumir nem silenciar linha:

   ```markdown
   ## `.claude/` — <alvo> (N repositórios)
   Resultado: PASS | FAIL (N achados)
   Achados (bruto): <linhas [Dn]>
   Informativo: <contagem + as linhas>
   Próximo passo: confirmar achados → registro (passo 5)
   ```

5. **Registro.** O destino depende do repositório do achado, não de onde a varredura rodou:

   - **Tem `debts/`** → `DT-NNN` por `python3 ${CLAUDE_PLUGIN_ROOT}/skills/handoff/scripts/debito.py novo <repo>`, um repositório por vez e com o dono de cada um de acordo — escrever em N repositórios na mesma execução da varredura é porta de mão única.
   - **Sem registro** → uma linha no registro de captura, pela rota da `deltaspec:eu-tenho-tdah`, com `Origem: project-review-dotclaude` e o caminho do repositório auditado.

## Erros comuns

| Erro | Correto |
|---|---|
| Corrigir o que a auditoria achou na mesma execução | O modo `auditar` é read-only por contrato; mover, apagar ou ignorar é decisão do dono, em execução própria |
| Mandar para fora do repositório um arquivo que o D8 acusou | O D8 diz que alguém vivo o cita: o destino é `docs/` ou `scripts/`, reescrevendo as citações |
| Tratar o D3 de `worktrees/` como resolvido porque "aqui está ignorado" | Ignorado por `.git/info/exclude` ou pelo ignore global só vale nesta máquina; um clone novo vê a pasta inteira |
| Cobrar `settings.local.json` ou `.cc-writes/` não rastreados | O próprio Claude Code os ignora na máquina; só rastreados são achado (D4) |
| Achar que a lista de permitidos é eterna | Ela tem fonte e data no catálogo; conferir a doc oficial de novo quando o D1 acusar pasta que o Claude Code passou a ler |

## O que não existe ainda

- **Modo `migrar`** — copiar plano, prompt e handoff elegível para fora do repositório com rastro de origem. Pendência da delta que criou esta skill.
- **D9** — gerador ou publicador que segue link para `.claude/`. Ficou fora por ser heurística de um incidente só.

## Arquivos da skill

- `references/catalogo.md` — **dono canônico** da doutrina, da lista do que pode ser versionado (com fonte e data) e dos checks D1–D8.
- `scripts/dotclaude.py` — os checks: `auditar(repo)` devolve `(Dn, detalhe)`; espelha as listas e a severidade do catálogo, e o `--selftest` exige que coincidam.
