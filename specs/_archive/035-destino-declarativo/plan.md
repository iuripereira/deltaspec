# Plano — delta-035 destino-declarativo
**Objetivo:** dar um dono único à leitura do destino da projeção e fazer `debito.py` consumi-lo, quitando o DT-033. **Cobre:** R1 (MUDA R52) **Decisões duráveis → ADRs:** nenhuma (a renúncia à chave `motores.github` está na spec, em Fora de escopo — não há alternativa de arquitetura descartada que precise de registro próprio) **Riscos assumidos:** `projecao.py` ganha PyYAML como import, com degradação em vez de aborto; nenhum consumidor declara `motores.jira` hoje, então a mudança não é exercitada em produção nesta rodada.

## Desenho

A duplicação era a causa, não o sintoma: `ler_projeto_jira` existia só no `tickets.py`, então `debito.py` não tinha de onde ler e recorreu à flag. Mover a função para `projecao.py` — que já é o módulo comum do dialeto, importado pelos dois — resolve os dois lados com uma cópia a menos, em vez de acrescentar uma segunda leitura ao `debito.py`.

Precedência `--projeto` > perfil (e não o contrário): editar arquivo versionado para uma exportação de teste seria pior que digitar a flag, e é exatamente o caso do sandbox `SBX`.

## Tasks
Ver [tasks.md](tasks.md).
