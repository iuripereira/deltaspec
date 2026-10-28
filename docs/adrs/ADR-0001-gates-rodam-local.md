# ADR-0001: Gates determinísticos rodam local, não no CI dos projetos gerados

- **Status:** Accepted
- **Data:** 2026-07-18
- **Supersedes:** —
- **Superseded by:** —

## Context

O framework passou a ter dois gates determinísticos (`check_cycle.py`, `validate_integrity.py`).
Eles moram em `~/.claude/skills/<skill>/scripts/`, que é o diretório de skills do Claude Code na
máquina do usuário — **não** existe dentro dos repositórios que o framework inicializa, e muito
menos num runner de CI do GitHub.

Isso cria um descompasso: a regra canônica manda gate mecânico ("grep ad-hoc não é garantia, o
script é"), e o `projeto-infra` já sabe injetar workflows nos projetos do usuário — mas um job que
invoque `python3 ~/.claude/skills/...` falha no runner.

Alternativas consideradas:

1. **Vendorizar** o script em cada projeto gerado (`scripts/check_cycle.py` copiado pelo init).
2. **Publicar** o framework como pacote instalável (`pip install sdd-iuri`) e chamar no CI.
3. **Rodar só local**, nas fases do ciclo que já são conduzidas por um agente.

## Decision

Adotamos a alternativa 3: os gates rodam **local**, invocados pela fase `analyze`, pelo `archive` e
pelo pré-commit. Nenhum workflow gerado pelo `projeto-infra` os executa.

Renunciamos ao vendoring (1) porque ele cria N cópias de um script que ainda está mudando: uma
correção no gate exigiria propagar para todo projeto já inicializado — exatamente a duplicação que
a regra de ouro do `CLAUDE.md` proíbe, e sem manifesto que a governe.

Renunciamos ao pacote (2) por custo desproporcional ao estágio: publicar, versionar e manter
compatibilidade de um pacote para dois scripts de ~250 linhas, antes de o framework ter usuários
além do autor, é infraestrutura especulativa.

O CI **deste** repositório continua rodando os `--selftest` dos gates — é o que impede o gate de
apodrecer calado. O que não existe é o gate rodando no CI dos *outros* projetos.

## Consequences

**Fica mais fácil:** o gate evolui numa cópia só; corrigir um falso positivo beneficia todos os
projetos na hora seguinte, sem migração. O `projeto-infra` continua com escopo estreito
(proteção de branch, commits, release) e não vira distribuidor de código.

**Fica mais difícil:** o gate é forte contra esquecimento do agente, mas **não** contra quem
empurra direto — um humano que commite sem rodar o script passa. É uma camada mais fraca do que o
ruleset da `main`, e o `STATE.md` registra isso como limitação conhecida, não como bug.

**Reabre quando:** o framework ganhar usuários fora do autor, ou o gate no CI do projeto virar
requisito de alguém. Aí a alternativa 2 (pacote) passa a ser a candidata natural, e esta ADR é
substituída — não editada.
