# delta-035 — destino-declarativo
Estado: arquivada · Data: 2026-08-07 · Branch: feat/035-destino-declarativo · Perfil: enxuto — correção de inconsistência de configuração num único ponto, sem superfície nova, com o selftest existente já cobrindo a projeção (aprovado: 2026-08-07) · Test-plan: dispensado — perfil enxuto; os 4 cenários novos mapeiam 1:1 nos casos do `--selftest` do `projecao.py` e num E2E pelo `debito.py exportar`, e um test-plan aqui seria transcrição deles
<!-- Aprovação do perfil: pedido direto do Iuri "resolva o DT-033" em 2026-08-07, com o desenho da correção já escrito no próprio DT e lido por ele. Não houve escolha explícita de perfil — o enxuto é inferência de escopo desta sessão, não declaração do usuário. -->
Clarify: auto-avaliado (2026-08-07) — sem canal humano
<!-- O DT-033 nasceu de uma pergunta do Iuri e a direção de escopo é dele, mas nenhuma pergunta minha foi respondida: as decisões de desenho saíram do repo (fonte canônica única, RNF2, ADR-0023). Pela regra do R8 isso é auto-avaliado, não entrevistado. -->

## Contexto (≤3 linhas)
Quita o [DT-033](../../DEBT.md): a mesma decisão — para onde vai a projeção — tem dois mecanismos. `debito.py exportar` escolhe por flag `--projeto`; `tickets.py` escolhe por `motores.jira.projeto` do `doc-profile.yaml`. A rota dos débitos vive na memória de quem digita o comando, não declarada no repo, e dois comandos do mesmo ciclo respondem a fontes diferentes — o que contraria a fonte canônica única.

## Mudanças
### R1 — MUDA R52 (delta-017): ferramenta de ticket é projeção do registro, com ida mecânica e volta aprovada.
<!-- versão integral do R52 vigente + 2 cenários novos (origem da chave e leitor único); os demais são repetidos byte a byte porque o archive substitui integralmente -->
- DADO o `DEBT.md` QUANDO `debito.py exportar` roda ENTÃO ele emite o JSON canônico e os dialetos de importação em arquivos, **sem acessar a rede** — quem executa os comandos é a skill, nunca o script; o dialeto que exige chave de projeto só é emitido quando ela é informada
- DADO a chave do projeto Jira QUANDO a projeção precisa dela ENTÃO ela vem de `motores.jira.projeto` do `doc-profile.yaml` — declarada no repo, não digitada de memória —, com `--projeto` sobrepondo para exportação pontual, e **ausência da chave é a declaração de que a rota é o GitHub** (delta-035)
- DADO `debito.py` e `tickets.py` QUANDO ambos precisam do destino ENTÃO obtêm a chave da **mesma função** do módulo comum `projecao.py` — dois leitores do mesmo campo divergiriam em silêncio (delta-035)
- DADO o dialeto Jira emitido QUANDO ele é gerado ENTÃO é um `.sh` de `acli jira workitem create` **unitários** (padrão do `tickets-gh.sh`), preservando o corpo multi-linha dos itens — decisão da primeira execução real (DT-021, 2026-08-07: `create-bulk` rejeita `\n` na description; o lote bulk deixa de ser emitido) — e execução não interativa
- DADO um item projetado QUANDO o ticket é criado ENTÃO ele carrega a etiqueta determinística com o `DT-NNN` e o título prefixado pelo ID, e a chave devolvida (`gh#NNN`, `PROJ-NNN`) é gravada na coluna `Externo` — é ela, e não o título, que garante idempotência
- DADO o estado coletado da ferramenta QUANDO `debito.py diff` roda ENTÃO ele emite a tabela *DEBT.md diz × ferramenta diz × impacto × ação proposta* (formato do R27), cobrindo item sem ticket, ticket fechado com item ativo e ticket sem item correspondente
- DADO uma divergência detectada QUANDO ela vira mudança no `DEBT.md` ENTÃO a alteração é **proposta e só aplicada após aprovação humana** — a ferramenta externa nunca sobrescreve o arquivo, que permanece a fonte da verdade
- DADO a ferramenta ausente, sem autenticação ou sem projeto configurado QUANDO a projeção é invocada ENTÃO o `DEBT.md` segue valendo sozinho, com no máximo 1 linha de aviso (RNF2)

## Fora de escopo
- Chave `motores.github` própria: ausência de `jira` já declara a rota GitHub, e criar chave sem necessidade é a cerimônia que o repo recusa. Registrado como decisão, não como esquecimento.
- Rota GitHub no `tickets.py` (tasks de delta só projetam para Jira hoje) — o DT-033 é sobre *onde a decisão mora*, não sobre ampliar destinos.

## Ambiguidade residual
- A alternativa "chave `motores.github` explícita" foi decidida por mim contra a cerimônia, não pelo dono do processo. Se o Iuri preferir simetria explícita entre as duas rotas, é uma delta de uma linha.

## Dependências e riscos
- `projecao.py` passa a importar PyYAML, dependência já admitida ([ADR-0023](../../docs/adrs/ADR-0023-pyyaml-como-dependencia-admitida.md)). Diferente do `tickets.py`, que abortava sem ela, aqui a ausência **degrada** (RNF2): `debito.py` roda em repo sem `doc-profile.yaml` e deve seguir rodando sem yaml instalado — mas com aviso, senão "não declarei" e "não consigo ler" viram a mesma saída silenciosa.
- Nenhum consumidor declara `motores.jira` hoje (varredura de 2026-08-07 nos 4 repos IMEX), então o comportamento efetivo não muda para ninguém — a mudança é de *onde a decisão pode ser declarada*, e o default permanece GitHub.
