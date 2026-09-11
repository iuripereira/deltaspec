# ADR-0036: O repositório público é derivado por allowlist, e é a publicação — não o CI — que porta o gate de confidencialidade

- **Status:** Accepted (2026-08-15, delta-064)
- **Data:** 2026-08-15
- **Supersedes:** —
- **Superseded by:** —

## Context

Este framework documenta o próprio processo de engenharia citando casos concretos, e é dessa virtude que nasce o problema: o identificador do cliente escorrega junto com o fato técnico. A medição de 2026-08-15 encontrou **80 arquivos versionados** carregando algum dos 7 termos da lista confidencial — 43 em `specs/_archive/`, 17 em `.claude/handoffs/`, 10 em `debts/`, 8 em `docs/adrs/`, mais o `CHANGELOG.md` e o `DEBT.md`. No histórico, **28 mensagens de commit** e **129 pontos de introdução em diff**, recuperáveis por `git log --grep` e `git log -S` em qualquer clone.

O repositório é **privado** hoje — 0 forks, 1 star, nenhuma exposição consumada — mas o `CLAUDE.md` e o docstring do `guarda-confidencialidade.py` afirmavam o contrário, e a intenção declarada sempre foi publicá-lo. A janela ainda estava fechada quando esta decisão foi tomada, o que é a única razão pela qual as opções baratas continuavam disponíveis: publicar é porta de mão única, com clone, arquivo público e crawler do outro lado.

O [DT-053](../../debts/_archive/DEBT_DT-053-gate-confidencialidade-so-local_2026_08_15.md) já registrava a metade do problema: o hook de escrita depende de `.claude/nomes-confidenciais.txt`, gitignored por desenho, e por isso o gate existia numa ponta só — a sessão do agente na máquina de quem tem o arquivo. O DT propunha três caminhos: **secret de repositório** com a lista lida por step do `ci`, **heurística sem lista** (nome próprio recorrente, domínio de Jira, `github.com/<org>/` fora de allowlist), ou **aceitar a assimetria** com revisão humana. Os três partem do mesmo diagnóstico — "o CI não pode executar o gate porque não tem a lista" — e o diagnóstico está uma camada acima do defeito.

O hook, além disso, cobre menos do que aparenta. Ele intercepta `PreToolUse` com matcher `Edit|Write`, e portanto não vê mensagem de commit, escrita feita por script chamado via `Bash`, renomeação de arquivo, nem nome no próprio caminho. E nada dele alcança o conteúdo **já commitado**: é gate de escrita, não varredura de repositório.

## Decision

Separamos o **produto** do **caderno de laboratório**, e movemos o gate para a fronteira onde a decisão de fato acontece.

**Este repositório continua privado e é a fonte canônica.** Histórico completo, `specs/_archive/`, handoffs e `debts/` seguem com nome real. É onde o ciclo roda e onde o registro é honesto.

**O repositório público é derivado, nunca editado.** `scripts/publica-dist.sh` monta uma árvore a partir de um **allowlist** declarado no topo do script, e a publica no remote público como **um commit órfão por release**, com tag e Release do GitHub. Nenhum commit do histórico privado é transplantado.

A propriedade que faz o resto cair: **o dado de cliente não é removido do público — ele mora em caminhos que nunca são copiados.** Não há filtro que possa falhar, não há narrativa residual, não há histórico a reescrever. O allowlist é a defesa que **não depende de a lista de nomes estar completa**, e essa independência é a razão de ele ser a defesa principal.

**O gate de confidencialidade roda na publicação.** `guarda-confidencialidade.py` ganha `--varre <dir>`, que aplica a mesma `achar_nomes` sobre a árvore do snapshot e sai 1 se achar. É a segunda ponta, e ali a degradação graciosa **se inverte**: no hook, lista ausente avisa e libera (RNF2); na publicação, lista ausente reprova, porque sem gate não se atravessa uma porta de mão única.

Renunciamos a quatro alternativas.

**Reescrever o histórico com `git-filter-repo`** foi recusada por ser a resposta certa para o problema errado. Ela substitui **tokens**; a exposição aqui é **narrativa** — "generalização do pipeline validado em X", "defeito real medido, 149 issues", setor mais volume mais sistema mais estágio contratual. Tirado o nome, sobra o retrato falado, e quem conhece o mercado remonta. Some-se que o resultado seria publicar 229 commits de notas de consultoria, ao custo de 59 tags re-apontadas, 31 Releases com SHA órfão e a proteção da `main` desativada para o force-push — para então destruir o registro honesto que o princípio de débito honesto deste repositório exige preservar.

**Criar o repositório público como fork e arquivar este** tinha o instinto certo — separar — e a mecânica errada — arquivar. Perderia as 59 tags e as 31 Releases; reprovaria no primeiro `ci` porque `versao_manifesto.py` compara o manifesto com a maior tag `v*` e num repositório sem tags a comparação não fecha; deixaria 27 ocorrências de URL do próprio repositório em 19 arquivos apontando para um slug morto; e quebraria `/plugin marketplace add` para os 10 repositórios consumidores, repetindo o custo que a [ADR-0016](ADR-0016-rename-deltaspec.md) já mediu no rename anterior.

**Secret de repositório com a lista, lido pelo job `ci`** (candidato 1 do DT-053) foi recusada porque paga o preço de transformar a lista em segredo de CI — rotação, superfície de log, o step tendo de nunca ecoar o que casou — para cobrir uma ponta que, com o allowlist no lugar, deixou de ser a ponta crítica. O `ci` valida o *privado*, e o privado é justamente onde os nomes **devem** estar.

**Heurística sem lista** (candidato 2) foi recusada por falhar exatamente no caso que importa: nome de cliente que parece palavra comum. O ruído seria pago em todo PR, e a captura, incerta onde mais custa.

## Consequences

Fica mais fácil: o trabalho retroativo cai de 80 arquivos para **9** — os 8 ADRs e o `CHANGELOG.md`, únicos itens do allowlist ainda contaminados —, porque `specs/`, `debts/` e handoffs simplesmente não são publicados; as 28 mensagens de commit e os 129 pontos de diff do histórico deixam de importar, já que nada do histórico privado atravessa; o DT-053 se resolve sem segredo de CI nem heurística; e a URL de instalação é preservada, porque o privado libera o slug ao renomear e o público nasce nele — zero reinstalação nos consumidores.

Fica mais difícil: passam a existir **dois repositórios com o mesmo nome de produto e papéis distintos**, e confundi-los é a falha de operação mais provável — commitar no público, ou esperar que o `git log` de lá conte a história. A mitigação é que o público é gerado e sobrescrito a cada release: qualquer edição feita nele é perdida na publicação seguinte, o que torna o erro barulhento em vez de silencioso. O allowlist também vira ponto de manutenção: caminho novo que devesse ser público e não foi declarado simplesmente não aparece lá, e o sintoma (arquivo faltando) é bem mais legível que o inverso.

Trade-off aceito: o público não terá as 59 tags nem as 31 Releases históricas (decisão do usuário em 2026-08-15) — ele nasce na versão corrente. E o rodapé de links de comparação do `CHANGELOG.md`, instituído pelo R80 na delta-062, é truncado no snapshot: ele pertence ao repositório que tem o histórico, e no público apontaria para commits que nunca existiram.

Fora do recorte, e sem cobertura: o gate confere **conteúdo**, não **nome no caminho de arquivo** — um arquivo chamado com o nome do cliente dentro do allowlist passaria. Não há caso hoje, e mecanizar exigiria aplicar `achar_nomes` também ao path; fica registrado como lacuna conhecida em vez de resolvido por antecipação. Igualmente fora: a **auditoria de segurança** da árvore publicável — superfície de GitHub Actions em repositório público, o `curl … | bash` do instalador de motores, os scripts das skills passando a ser executados por terceiros — que é condição para a primeira publicação real e não é coisa que um gate de nomes resolva.

<!--
Imutável após "Accepted". Mudou a decisão? Crie uma NOVA ADR com "Supersedes ADR-0036" e marque esta como "Superseded by ADR-YYYY". Nunca reescreva uma ADR aceita. Atualize o índice docs/adrs/README.md no mesmo PR. -->
