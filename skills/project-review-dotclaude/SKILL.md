---
name: project-review-dotclaude
description: Obsoleta desde a delta-143 — a auditoria da pasta .claude/ é o modo .claude/ da audit-workspace (audit_workspace.py --apenas-dotclaude, bloco D, só-leitura). Será removida na próxima versão MAJOR.
disable-model-invocation: true
---

# project-review-dotclaude (obsoleta)

Use a [`audit-workspace`](../audit-workspace/SKILL.md) no modo `.claude/`: `python3 ${CLAUDE_PLUGIN_ROOT}/skills/audit-workspace/scripts/audit_workspace.py --apenas-dotclaude <alvo>`. Só-leitura — nunca escreve no repositório auditado. A doutrina continua em [`references/catalogo.md`](references/catalogo.md) e os checks D1–D8 em [`scripts/dotclaude.py`](scripts/dotclaude.py), que o `audit_workspace.py` importa; o registro dos achados (DT-NNN pelo `debito.py novo`, ou o registro de captura) é o mesmo.
