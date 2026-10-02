# Catálogo D — `.claude/` só com o que o Claude Code lê

> Dono canônico da doutrina de `.claude/` (delta-123). O `dotclaude.py` espelha as listas e a severidade abaixo, e o selftest dele exige que coincidam.

## Doutrina

`.claude/` guarda a **configuração que o Claude Code lê**, mais `handoffs/` — convenção do framework, inerte para o Claude Code (ADR-0025). Tudo o mais tem outro dono:

| Artefato | Dono |
|---|---|
| plano do ciclo | `specs/NNN-nome/plan.md` |
| plano ou prompt de sessão | fora do repo (notas do dono) |
| documento canônico citado por `CLAUDE.md` ou script | `docs/` |
| tooling | `scripts/` |
| artefato de execução | `.gitignore` versionado |

## O que pode ser versionado

Fonte: https://code.claude.com/docs/en/claude-directory, conferida em 2026-09-21. `hooks/` não aparece como pasta na página, mas é onde os exemplos da doc põem os scripts de hook; `handoffs/` é do framework; `.gitignore` é do git, não da doc — é onde o D3 manda pôr a regra.

- **Permitidos:** `CLAUDE.md`, `settings.json`, `rules/`, `skills/`, `commands/`, `output-styles/`, `agents/`, `workflows/`, `agent-memory/`, `hooks/`, `handoffs/`, `.gitignore`
- **Execução:** `worktrees/`, `.cc-writes/`, `__pycache__/`, `settings.local.json`, `agent-memory-local/`, `*.lock`

`commands/` é permitido pelo D1 e cobrado pelo D2: funciona, mas é o formato antigo de `skills/`. `settings.local.json` e `.cc-writes/` o próprio Claude Code grava no ignore global da máquina, então o D3 não os cobra; rastreados, seguem sendo D4.

## Checks

| ID | Achado | Severidade | Detecção | Correção |
|---|---|---|---|---|
| D1 | caminho rastreado em `.claude/` fora dos permitidos | ALTO | `git ls-files .claude/` agrupado pela entrada de primeiro nível | plano ou prompt sai do repo; o resto vai para o dono da tabela acima |
| D2 | `.claude/commands/` rastreado | MÉDIO | `git ls-files .claude/commands/` | um `skills/<nome>/SKILL.md` por comando |
| D3 | item não rastreado em `.claude/` sem regra no `.gitignore` versionado | ALTO | `git check-ignore -v` na entrada; fonte fora dos arquivos rastreados (`.git/info/exclude`, `excludesFile` global) conta como sem regra; vale para a entrada de primeiro nível e para artefato de execução aninhado em entrada rastreada (`hooks/__pycache__/`). Entrada permitida não versionada fica fora: é configuração em andamento, e o conselho seria versioná-la | regra no `.gitignore` versionado |
| D4 | artefato de execução rastreado | MÉDIO | caminho rastreado com entrada da lista Execução | `git rm --cached` e regra no `.gitignore` |
| D5 | hook citado no `settings.json` rastreado e não rastreado ele mesmo | ALTO | `.claude/hooks/...` nos comandos da chave `hooks`; `settings.json` que não é JSON válido também é D5 — nenhum hook dele roda | versionar o script, ou tirar a citação |
| D6 | handoff mais antigo que a retenção e sem citação no `HANDOFF.md` | informativo | data do nome `HANDOFF_<tópico>_<AAAA>_<MM>_<DD>.md` | sai do repo pela regra de retenção do projeto |
| D7 | `.claude/handoffs/` rastreado sem `HANDOFF.md` na raiz | ALTO | `HANDOFF.md` ausente dos rastreados | criar o índice na raiz |
| D8 | arquivo que o D1 acusaria, citado por arquivo vivo | ALTO | `<pasta>/<nome>` no texto de arquivo rastreado fora do histórico | mover para `docs/` ou `scripts/` e reescrever as citações — sair do repo quebraria quem cita |

Arquivo vivo: todo texto rastreado (o `git grep -I` decide o que é texto), exceto o que está em qualquer pasta `_archive/`, o `CHANGELOG.md`, o `HANDOFF.md`, `debts/` — registrar o achado não pode mudar o achado — e, dentro de `.claude/`, `handoffs/` e o que não é permitido. Histórico não ancora.

O D9 da issue #483 (gerador que segue link para `.claude/`) ficou fora: heurística de texto nascida de um incidente só. É pendência da delta-123.
