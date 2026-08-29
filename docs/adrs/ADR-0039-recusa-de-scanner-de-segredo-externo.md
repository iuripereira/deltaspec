# ADR-0039: Detecção de segredo fica em stdlib, com o buraco de cobertura declarado no catálogo

- **Status:** Accepted (2026-08-22, delta-076)
- **Data:** 2026-08-22
- **Supersedes:** —
- **Superseded by:** —

## Context

O G1 da skill `git-guard` audita segredo versionado. Nos dois rankings do catálogo de anti-padrões ele é o pior caso de **dano**: credencial viva entra em história imutável, `revert` não resolve, e a correção obrigatória é rotacionar a credencial — custo que recai sobre quem a emitiu, que nem sempre é quem a vazou.

A comunidade resolveu isso há anos, e o consenso é claro: `gitleaks` no pré-commit, `trufflehog` na varredura profunda de história, e a proteção de push do GitHub como portão sempre-ligado. Os três alcançam o que casamento por padrão conhecido não alcança.

Três coisas restringem essa saída aqui.

1. **A política de dependência.** O `CLAUDE.md` admite stdlib mais um pacote externo — `PyYAML` — e a [ADR-0023](ADR-0023-pyyaml-como-dependencia-admitida.md) fecha dizendo, com todas as letras, que a próxima dependência vai citá-la como jurisprudência e que por isso "cada uma nova exige o mesmo grau de justificativa, não um aceno para cá". Um scanner externo é um binário Go, não um pacote Python: acrescenta um passo de instalação fora do `pip`, com versionamento e distribuição próprios.
2. **A proteção de push do GitHub é gratuita só em repositório público.** Os repositórios em questão são privados. A única trava verdadeiramente não contornável do lado do servidor está atrás de um produto pago por commiter ativo — decisão de custo, não de arquitetura, e que de todo modo não alcança os repositórios sem remoto.
3. **O que o casamento por padrão conhecido de fato alcança foi medido, não estimado.** A primeira varredura real sobre 30 repositórios produziu 21 achados de segredo. Vinte eram falso positivo, em cinco classes: nome de função capturado como valor, expansão de shell com valor default, documentação mandando *gerar* o valor, `SCREAMING_SNAKE_CASE` como convenção de placeholder, e placeholder codificado em base64. O único achado que sobreviveu — um `.env` fora do git num repositório sem `.gitignore` — não veio de casamento de padrão nenhum: veio de uma regra estrutural.

O terceiro ponto é o que muda a conversa. A pergunta deixa de ser "stdlib ou scanner?" e passa a ser "o que este check realmente entrega, e o que ele deixa passar?".

## Decision

**A detecção de segredo fica em stdlib**, no módulo `skills/git-guard/scripts/segredos.py`, e o alcance dela é **declarado no catálogo** em vez de subentendido.

Três compromissos que a decisão carrega:

**O mesmo código nas duas pontas.** `casar()` é núcleo puro, sem I/O. O G1 o importa hoje; o hook pré-commit e o passo de CI o importam na delta seguinte. Hook e CI invocando o mesmo código é o que impede o gate documentado de divergir do gate executado — e o CI é o que sobrevive a `--no-verify`, que o próprio catálogo classifica como o multiplicador de todos os outros anti-padrões.

**O valor casado nunca sai da função.** `casar()` devolve `(nome_do_padrão, número_da_linha)` e nada mais. Um relatório de auditoria que imprime o segredo transporta o segredo — para o terminal, para o histórico da sessão, e para onde quer que o relatório vá depois. É o mesmo cuidado que o W2 já toma ao comparar remotes sem imprimir a URL.

**O buraco é escrito, não escondido.** A seção "O que fica sem trava" do catálogo nomeia: segredo sem enquadramento reconhecível, proteção de push ausente em repositório privado, `git` chamado de dentro de script escrito pelo agente, e repositório sem remoto. Débito honesto é regra do projeto, e um check de segurança que não diz o que não vê produz confiança injustificada — exatamente o modo de falha que a ADR-0023 usou para recusar o parser YAML próprio.

Renunciamos ao **scanner externo** porque a justificativa própria que a ADR-0023 exige não se sustentou na medição: o que o scanner acrescenta sobre o que temos é a cauda de segredos sem enquadramento, e nenhum caso dessa cauda apareceu nos 30 repositórios varridos. Adotá-lo agora seria pagar a segunda dependência do projeto por uma melhoria que ainda não foi observada.

Renunciamos à **compra de proteção de segredo no servidor** neste momento pelo mesmo motivo — e porque ela não cobre os dois repositórios que existem só em disco, que são justamente os de perfil mais frágil.

## Consequences

**Fica mais fácil:** o G1 roda em qualquer máquina com Python 3.11, sem passo de instalação; o mesmo núcleo serve auditoria, hook e CI sem duplicar regra; o filtro de placeholder, que é onde mora quase todo o custo de um scanner ingênuo, ficou sob teste de regressão com casos colhidos de repositórios reais, não inventados.

**Fica mais difícil:** o alcance depende de manter a lista de padrões atualizada à mão, e provedor novo não chega sozinho; a fronteira entre placeholder e credencial é heurística e vai errar nos dois sentidos — a assimetria escolhida é **acusar na dúvida**, porque deixar de acusar custa rotação e acusar custa uma linha de relatório; e o repositório privado segue sem trava não contornável de servidor, o que faz do par pré-commit + CI a única defesa real contra o anti-padrão de maior dano do catálogo.

**Reabre quando:** um segredo real escapar do G1 — esse é o gatilho, e ele vale mais que qualquer estimativa prévia; ou a proteção de segredo do GitHub passar a cobrir repositório privado sem custo adicional; ou um scanner externo passar a ser instalável pelo mesmo `pip` que já é pré-requisito, o que reduziria o custo da dependência ao patamar que a ADR-0023 já admitiu.
