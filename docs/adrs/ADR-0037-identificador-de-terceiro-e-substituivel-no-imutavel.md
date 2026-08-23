# ADR-0037: Identificador de terceiro é substituível no registro imutável — o fato que ele acompanha não é

- **Status:** Accepted (2026-08-15, delta-065)
- **Data:** 2026-08-15
- **Supersedes:** —
- **Superseded by:** —

## Context

A [ADR-0036](ADR-0036-publicacao-derivada-como-gate-de-confidencialidade.md) instituiu o repositório público como projeção deste, montada a partir de um allowlist e barrada por um gate que aborta a publicação se um identificador de terceiro atravessar. Na primeira execução o gate reprovou, como devia: **21 ocorrências em 9 arquivos** do payload — 8 ADRs aceitas e uma seção lançada do `CHANGELOG.md`.

Esses 9 arquivos são exatamente a classe que este repositório protege com mais rigor. A [ADR-0032](ADR-0032-erro-mecanico-de-caminho-e-corrigivel-no-imutavel.md) recortou a imutabilidade **por classe de achado** — erro mecânico de caminho é corrigível, conteúdo de época é intocável — e a [ADR-0035](ADR-0035-changelog-lancado-e-projecao-reescrevivel.md), ao liberar a *forma* da entrada lançada, foi explícita em não abrir mais nada: "`specs/_archive/**` e `docs/adrs/**` seguem sendo registro imutável, sem qualquer recorte novo — esta ADR não os toca". O nome do cliente numa ADR é, sob a régua vigente, conteúdo de época: trocá-lo muda o que se lê sobre o que aconteceu.

A saída de não tocar em nada foi avaliada e não fecha. Tirar `docs/adrs/` do allowlist deixaria o registro intacto e não publicado — mas o payload referencia **27 ADRs distintas a partir de 28 arquivos**, e as skills publicadas passariam a apontar para documentos que não existem do outro lado. O "porquê" do framework é parte do que ele entrega.

A alternativa de **substituir na publicação**, com um mapa fora do git aplicado por `publica-dist.sh`, preservaria a imutabilidade ao preço de fazer o texto público divergir do canônico e de tornar um arquivo gitignored responsável pela correção do que se publica. Foi levada ao usuário junto com esta e recusada por ele em 2026-08-15, pelo custo de manter duas versões da mesma ADR.

## Decision

Recortamos a imutabilidade uma terceira vez, e mais estreita que as duas anteriores.

**O identificador de terceiro é substituível por pseudônimo em registro imutável — e só ele.** Nome de organização, de projeto, de repositório ou de site interno de terceiro pode ser trocado numa ADR aceita ou numa seção lançada do `CHANGELOG.md`. Nenhuma outra palavra da decisão registrada muda no mesmo movimento.

**O fato técnico que o identificador acompanha é preservado integralmente.** "96 links mortos caíram para 3", "8 exports em 2 rodadas", "27 arquivos referenciados, 16 fantasmas", "235 docs, 1.053 nós", "149 issues atualizadas, 0 mutações na reexecução": é o fato que dá valor ao registro, e ele sobrevive à substituição sem arredondamento nem generalização. Um recorte que apagasse a medição junto com o nome não seria anonimização, seria perda de registro.

**O nome de época que não é identificador de terceiro permanece intocado.** `sdd-iuri` antes do rename, `STATE.md` antes da delta-010: a guarda do R47 e do [DT-010](../../debts/ativos/DEBT_DT-010-referencias-a-state-md.md) segue sem emenda, e esta ADR não a alcança.

O limite entre os dois: se a palavra identifica **um terceiro**, sai; se identifica **este projeto em outra época**, fica.

**O que continua valendo, reafirmado aqui:** `specs/_archive/**` não é tocado por esta ADR e segue integralmente imutável — é justamente onde o nome real permanece, e é isso que mantém a rastreabilidade que a substituição custa no payload. A garantia da fronteira segue mecânica: o C13 do `check_cycle.py` confere os links das deltas arquivadas, o C3 do `validate_integrity.py` segue cego ao archive, e nenhum gate ganha licença genérica para reescrever registro.

Renunciamos a duas alternativas além da já citada. **Marcar as 8 ADRs como `Superseded by` e reescrevê-las limpas** foi recusada porque `Supersedes` existe para registrar **mudança de decisão**, e nenhuma decisão mudou aqui — usá-lo para higiene de texto esvaziaria o significado do campo em todas as outras. **Aceitar a assimetria e publicar com os nomes** foi recusada pela razão que originou a ADR-0036: publicar é porta de mão única, e o dado é de terceiro, não nosso para expor.

## Consequences

Fica mais fácil: o payload passa no gate e o repositório pode ser publicado sem que o registro precise ser mutilado — a decisão, a renúncia e a medição de cada ADR continuam legíveis por inteiro.

Fica mais difícil: "registro imutável" passa a ter **três** ADRs recortando-o, e cada recorte novo enfraquece a leitura de que a regra é absoluta. A mitigação é a mesma que as duas anteriores adotaram e que se torna aqui um padrão declarado: a licença é **estreita e nomeada** — vale para identificador de terceiro, em ADR aceita e em seção lançada de CHANGELOG, e nada mais. Qualquer outra classe continua sem cobertura e sem respaldo, e a próxima que precisar pagará o mesmo preço de uma ADR própria.

Trade-off aceito: quem lê o registro público perde a identidade do caso — "um repo consumidor" não diz qual foi. É perda real de contexto para quem já tinha o contexto, e está aceita porque a rastreabilidade não some: ela migra para `specs/_archive/`, handoffs e `debts/`, que mantêm o nome e nunca são publicados. O registro fica honesto onde a honestidade custa alguma coisa, que é dentro.

Fora do recorte, e sem cobertura: a substituição é **manual, arquivo a arquivo**, porque cada ocorrência pede a frase que caiba no período — um `sed` produziria português quebrado num registro que não se reescreve duas vezes. Não há gate que verifique a *qualidade* da substituição; o `--varre` verifica apenas que o identificador saiu. E o gate confere conteúdo, não nome no caminho de arquivo, lacuna já declarada na ADR-0036.

<!--
Imutável após "Accepted". Mudou a decisão? Crie uma NOVA ADR com "Supersedes ADR-0037" e marque esta como "Superseded by ADR-YYYY". Nunca reescreva uma ADR aceita. Atualize o índice docs/adrs/README.md no mesmo PR. -->
