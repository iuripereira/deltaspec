# ADR-0023: PyYAML é dependência externa admitida nos gates — exceção declarada, não erosão do princípio

- **Status:** Accepted (2026-08-02, delta-026)
- **Data:** 2026-08-02
- **Supersedes:** —
- **Superseded by:** —

## Context

O framework promete, em quatro lugares vivos, que os gates rodam sem dependência externa: `CLAUDE.md` ("os gates usam stdlib pura — zero pacote externo"), `README.md` ("Sem dependência externa: só a biblioteca padrão do Python 3.11+"), `README.en.md` (idem em inglês) e `SECURITY.md`, que a usa como argumento de modelo de ameaça ("superfície de cadeia de dependências Python igual a zero") — o quarto espelho só apareceu no review da delta. É promessa de primeira linha, ao lado de "tudo roda na sua máquina" (ADR-0001) — parte do que torna o gate auditável e reprodutível.

O C11 da delta-026 precisa validar o schema do `doc-profile.yaml`. YAML não tem parser na stdlib, e o arquivo real não é trivial: a varredura de 2026-08-02 sobre 7 perfis mostrou mapas aninhados em dois níveis, mapas inline (`{ obrigatorio: false }`), listas inline, booleanos, comentários de fim de linha e strings com dois-pontos dentro.

Três alternativas tinham defensor.

1. **Parser mínimo próprio** (~40 linhas de regex/split cobrindo o subconjunto usado): mantém zero-dep e roda em qualquer máquina. Custo: código a manter, e — decisivo — falha **silenciosa** em YAML que o subconjunto não cobre. Um perfil válido lido errado produz `LIBERADO` falso, exatamente o modo de falha que a ADR-0006 usou para adiar este check em 2026-07-28. Este repositório tem três lições registradas de parser ingênuo produzindo falso resultado.
2. **PyYAML com degradação graciosa** (`try/except ImportError` → C11 se omite com aviso, no padrão RNF2 dos motores externos): parser correto de graça, sem quebrar quem não tem o pacote. Custo: o check desaparece em silêncio justamente na máquina menos preparada, e a degradação graciosa foi desenhada para **motores de terceiros opcionais** (ADR-0004), não para o gate, que é o núcleo do framework.
3. **PyYAML como dependência dura**, com a exceção declarada nos três espelhos e instalada explicitamente no CI.

## Decision

Decidida com o usuário em 2026-08-02 (clarify da delta-026): **alternativa 3.** `PyYAML` passa a ser dependência externa **declarada e admitida** dos gates — a única. Os quatro espelhos da promessa deixam de dizer "só a biblioteca padrão" e passam a nomear a exceção nos mesmos termos — no `SECURITY.md` a superfície de cadeia de dependências deixa de ser zero e passa a ser um pacote, nomeado; o job `ci` instala o pacote explicitamente, em vez de contar com o que o runner traz pré-instalado.

Renunciamos ao parser próprio (1) porque o modo de falha dele é o pior possível para um gate: silencioso e confiante. Um check que às vezes lê errado é pior que nenhum check, porque produz confiança injustificada — foi esse mesmo raciocínio que manteve o DT-013 aberto por cinco semanas, e resolvê-lo com um parser frágil seria trocar a dívida por outra pior.

Renunciamos à degradação graciosa (2) porque ela desloca o risco para onde não se pode observar: o C11 sumiria sem que ninguém percebesse, e o `LIBERADO` sairia igual. A degradação graciosa é contrato para motor de terceiro **opcional** (ADR-0004) — o gate não é opcional, é o produto.

A honestidade da promessa vale mais que a promessa: preferimos uma exceção nomeada em três arquivos a um zero-dep que só se sustenta escondendo um parser frágil.

## Consequences

**Fica mais fácil:** o C11 valida YAML de verdade, incluindo os construtos que os 7 perfis reais já usam; o DT-013 fecha sem trocar de dívida; futuros checks que precisem de YAML (o `doc-profile` tende a crescer) já têm o parser disponível.

**Fica mais difícil:** o framework deixa de ser instalável por cópia pura — quem clonar precisa de `pip install pyyaml` para rodar os gates, e isso tem que estar no README, não só no CI; a promessa "roda na sua máquina sem nada" perde a forma absoluta e passa a exigir uma linha de ressalva em quatro arquivos, que precisam ser mantidos em sincronia; e abre precedente — a próxima dependência vai citar esta ADR como jurisprudência, então cada uma nova exige o mesmo grau de justificativa, não um aceno para cá.

**Reabre quando:** a stdlib ganhar leitor de YAML, ou o `doc-profile.yaml` for substituído por um formato que a stdlib já lê (`tomllib` está disponível desde o 3.11 e o repo já o usa no `deps.toml`) — aí o zero-dep volta à mesa por nova ADR.
