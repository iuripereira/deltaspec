# Handoff: {{título curto e descritivo da sessão}}

**Data:** {{AAAA-MM-DD HH:MM}}
**Status:** {{Concluída | Em andamento | Bloqueada | Aguardando decisão}}
**Branch / Commit:** {{branch}} / {{hash, se aplicável}}

<!-- Nome do arquivo: .claude/handoffs/HANDOFF_<topico>_<AAAA>_<MM>_<DD>.md — tópico em
     kebab-case curto, que desambigua sessões do mesmo dia. Foco em INTENÇÃO e PROGRESSO:
     nada do que a próxima sessão lê sozinha no código-fonte. Seção sem dado real sai.
     Referencie por caminho/ID (DT-NNN, specs/_archive/NNN-*/, #PR) — nunca duplique. -->

## 1. Objetivo
{{2–4 frases: o que está sendo construído/corrigido nesta tarefa e por quê}}

## 2. Contexto essencial e decisões congeladas
- **Stack/arquitetura:** {{restrições técnicas e dependências principais}}
- **Decisões tomadas:** {{o que já foi decidido e por quê — evita que a próxima sessão rediscuta}}
- **Caminhos descartados:** {{o que foi tentado e abandonado, com a justificativa}}

## 3. Estado atual do código
- **Arquivos modificados/criados:** {{caminhos exatos}}
- **Testes e validações:** {{o que roda com sucesso; pendências conhecidas}}

## 4. Próximos passos imediatos
- [ ] {{tarefa acionável no imperativo, com refs a funções/linhas se necessário}}

## 5. Skills / ferramentas recomendadas
- {{skills/comandos que a próxima sessão deve carregar (ex.: /deltaspec:spec-feature, selftests locais)}}
