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

Fonte: https://code.claude.com/docs/en/claude-directory, conferida em 2026-09-21. `hooks/` não aparece como pasta na página, mas é onde os exemplos da doc põem os scripts de hook; `handoffs/` é do framework; `memory/` é do framework (delta-132): memória de projeto versionada, um arquivo por fato; `.gitignore` é do git, não da doc — é onde o D3 manda pôr a regra.

- **Permitidos:** `CLAUDE.md`, `settings.json`, `rules/`, `skills/`, `commands/`, `output-styles/`, `agents/`, `workflows/`, `agent-memory/`, `memory/`, `hooks/`, `handoffs/`, `.gitignore`
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

## Fluxo e fronteiras (herdados da SKILL.md da `project-review-dotclaude`)

Origem: texto da `SKILL.md` antiga, movido para cá na delta-143 quando a skill virou ponteiro `Obsoleto` — o catálogo é o dono da doutrina de `.claude/` (R190). A execução é o modo `.claude/` da `audit-workspace`.

### Fronteiras

| Skill | Objeto |
|---|---|
| `audit-workspace` (bloco D) | **o que mora** em `.claude/` (checks D) |
| `git-guard` | higiene de git; `.claude/` sem `settings.json` nem guarda de agente é o **G3** de lá, não um D |
| `audit-workspace` (bloco W) | consistência de referência entre repos; o **W7** mapeia o diário de bordo de cada repo, o **D7** cobra só `.claude/handoffs/` sem `HANDOFF.md` |

O motor é um só: `audit_workspace.py` descobre os repositórios, agrupa por achado e imprime. Os checks D moram em `scripts/dotclaude.py`. Os três blocos rodam disjuntos — uma flag por vez.

### Fluxo de auditoria

1. **Alvo.** Um repositório: rode dentro dele. Um workspace: rode na pasta-mãe e decida a profundidade — sem `--profundidade`, a varredura enxerga um nível só.
2. **Execução.** `python3 ${CLAUDE_PLUGIN_ROOT}/skills/audit-workspace/scripts/audit_workspace.py . --apenas-dotclaude` (com `--profundidade 3` para descer). Exit 0 = sem achado; 1 = achado(s); 2 = alvo não é repositório nem workspace reconhecível, ou `--apenas-dotclaude` junto de `--apenas-git`. A auditoria lê a **árvore de trabalho** de cada repositório — o branch em checkout, não o default: um `.gitignore` que já tem a regra na `develop` e não na branch corrente acusa D3.
3. **Triagem.** A saída vem agrupada por check, do ALTO ao MÉDIO, e o D6 vem no bloco informativo, que não derruba o resultado. O D8 substitui o D1 para o arquivo citado por arquivo vivo: o destino dele é `docs/` ou `scripts/`, não sair do repositório — sair quebraria quem cita.
4. **Relatório.** Reporte a saída bruta, sem resumir nem silenciar linha: cabeçalho `## .claude/ — <alvo> (N repositórios)`, `Resultado: PASS | FAIL (N achados)`, `Achados (bruto): <linhas [Dn]>`, `Informativo: <contagem + as linhas>`, `Próximo passo: confirmar achados → registro`.
5. **Registro.** O destino depende do repositório do achado, não de onde a varredura rodou. **Tem `debts/`** → `DT-NNN` por `python3 ${CLAUDE_PLUGIN_ROOT}/skills/handoff/scripts/debito.py novo <repo>`, um repositório por vez e com o dono de cada um de acordo — escrever em N repositórios na mesma execução da varredura é porta de mão única. **Sem registro** → uma linha no registro de captura, pela rota da `deltaspec:eu-tenho-tdah`, com `Origem: audit-workspace` e o caminho do repositório auditado.

### Erros comuns

| Erro | Correto |
|---|---|
| Corrigir o que a auditoria achou na mesma execução | O modo `auditar` é read-only por contrato; mover, apagar ou ignorar é decisão do dono, em execução própria |
| Mandar para fora do repositório um arquivo que o D8 acusou | O D8 diz que alguém vivo o cita: o destino é `docs/` ou `scripts/`, reescrevendo as citações |
| Tratar o D3 de `worktrees/` como resolvido porque "aqui está ignorado" | Ignorado por `.git/info/exclude` ou pelo ignore global só vale nesta máquina; um clone novo vê a pasta inteira |
| Cobrar `settings.local.json` ou `.cc-writes/` não rastreados | O próprio Claude Code os ignora na máquina; só rastreados são achado (D4) |
| Achar que a lista de permitidos é eterna | Ela tem fonte e data neste catálogo; conferir a doc oficial de novo quando o D1 acusar pasta que o Claude Code passou a ler |

### O que não existe ainda

- **Modo `migrar`** — copiar plano, prompt e handoff elegível para fora do repositório com rastro de origem. Pendência da delta que criou a skill.
- **D9** — descrito no parágrafo acima (gerador que segue link para `.claude/`); segue fora.
