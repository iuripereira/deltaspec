# Digest da rodada de insumos — template

Única saída longa da rodada. Rodada vazia usa só o cabeçalho e a linha de fontes.

```markdown
## Rodada de insumos — AAAA-MM-DD
Fontes: <n arquivos · m reuniões · k respostas de formulário · exports manuais | "rodada vazia (fontes checadas: …)">
Dossiês: <docs/discovery/AAAA-MM-DD-<evento>.md ...>
Perguntas fechadas: <IDs com fonte> · novas: <IDs, cada uma com a proposta de encaminhamento>
Divergências: <#N em divergencias-<baseline>.md | nenhuma>
Gate de decisões: <n perguntas · respostas do usuário em AAAA-MM-DD | "pendente — atualização de PRD suspensa">
Presunções confirmadas: <lista com fonte | nenhuma>
PRD: <vX.Y → vX.Y+1 (o que mudou, 1 linha) | sem impacto>
Entregável congelado: <arquivo novo da versão | não gerado>
PR: <link — aberto, aguardando merge do humano>
Pós-merge (humano): <publicação de site/report · tag/release · promoção de baseline — o que se aplica>
```
