# Documentos jurídico-comerciais — regras de conteúdo

Fonte canônica das regras de **conteúdo** dos entregáveis jurídico-comerciais da `doc-entregavel`. O **export** (render de diagramas, capa, Sumário, PDF/DOCX) é o pipeline da [SKILL.md](../SKILL.md), passos 3–5 — este arquivo não o repete.

Mercado brasileiro, contratação **privada**. Base jurídica verificada em **2026-07-26** — jurisprudência citada com número e data, para que a próxima revisão saiba o que reconferir.

| `tipo` | Documento | Natureza |
|---|---|---|
| `juridico-nda` | Instrumento Particular de Confidencialidade, Não Circunvenção e Propriedade Intelectual | jurídico |
| `juridico-contrato-ti` | Instrumento Particular de Contrato de Prestação de Serviços de TI / Desenvolvimento de Software / Consultoria | jurídico |
| `requisitos-cliente` | Documento de Requisitos e Visão | técnico-comercial (vira Anexo I do contrato) |

---

## Regras gerais dos tipos `juridico-*`

### Minuta e honestidade da fonte

- O topo do arquivo gerado DEVE trazer, como nota removível: **"MINUTA — sujeita a revisão por advogado(a). Documento gerado por IA; não constitui aconselhamento jurídico."**
- NÃO DEVE inventar dispositivo legal, número de lei ou julgado. Base legal ausente desta página → gravar `[VERIFICAR COM ADVOGADO]` no texto.
- Tudo que o usuário não informou vira placeholder em destaque: `[EM_DESTAQUE: valor da multa]`.

### Formatação (convenção de mercado — não existe norma ABNT para contrato)

A NBR 14724 é norma de **trabalho acadêmico**. Pedido de "seguir ABNT" em instrumento contratual → corrigir a premissa e aplicar isto:

- A4, margens 2,5–3 cm, Arial ou Times New Roman 11–12 pt, espaçamento 1,5.
- Paginação `X/Y` no rodapé. Rodapé `CONFIDENCIAL` em todas as páginas nos tipos `juridico-nda` e `requisitos-cliente`.
- Cláusulas em caixa alta e negrito, ordinal por extenso: `CLÁUSULA PRIMEIRA – DO OBJETO`. Parágrafos `§1º`, `§2º`; incisos `I`, `II`, `III`; alíneas `a)`, `b)`.
- Saída em Markdown (versionável no repo) e export para DOCX/PDF na versão de assinatura.
- Prosa: uma regra por frase, sem aninhamento — ver [../../spec-feature/references/prosa.md](../../spec-feature/references/prosa.md).

### Eficácia executiva

Base: art. 784, III e §4º, CPC (Lei 13.105/2015).

1. **Duas testemunhas** com nome completo e CPF no bloco de assinaturas. Sem elas o documento vale entre as partes, mas não é título executivo extrajudicial na via do inciso III — sobra a ação monitória (art. 700 CPC), não a execução direta.
2. **Assinatura eletrônica.** O §4º do art. 784 (Lei 14.620/2023) admite **qualquer modalidade** de assinatura eletrônica e dispensa testemunhas quando a integridade for conferida por provedor de assinatura. O STJ confirmou que a certificação ICP-Brasil **não** é obrigatória: REsp 2.205.708-PR (4ª Turma, 04/11/2025, Informativo 871) e REsp 2.150.278-PR (3ª Turma, 24/09/2024) — o fundamento privado é o art. 10, §2º, da MP 2.200-2/2001 (meio aceito pelas partes). A Lei 14.063/2020 classifica os níveis de assinatura, mas rege as interações com **entes públicos**; não é o fundamento da relação privada.
   **Política da skill:** gerar sempre o bloco de duas testemunhas **e** recomendar plataforma com trilha de auditoria (ou ICP-Brasil). É **redundância deliberada** — barata, e o custo de errar aqui é a execução do título, não um formalismo.
3. **Duas vias de igual teor** e rubrica em todas as páginas, na versão física.
4. **Parte PJ**: razão social, CNPJ, endereço, representante legal com poderes verificáveis no contrato social.
5. **Foro**: cláusula final elegendo a comarca (padrão do usuário: Natal/RN, parametrizável).
6. **Registro em RTD** (opcional, recomendar em nota): confere data certa e oponibilidade a terceiros (art. 221 CC; arts. 127–130 LRP). Desde 01/01/2024 os efeitos valem **a partir da data do registro** — a retroação de 20 dias foi revogada pela Lei 14.382/2022, que também dispensou o registro em múltiplas comarcas. Consequência prática: registrar no mesmo dia da assinatura.

### Estrutura canônica do instrumento particular

Ordem fixa: (1) título centralizado em caixa alta; (2) qualificação das partes; (3) preâmbulo de considerandos — "CONSIDERANDO que…", onde entra o histórico fático (data do primeiro contato, trabalho já executado, intenção das partes); (4) fórmula de vinculação — "RESOLVEM as Partes celebrar o presente [nome], mediante as seguintes cláusulas e condições:"; (5) cláusulas numeradas; (6) cláusula de foro; (7) fecho — "E, por estarem justas e contratadas, assinam o presente em duas vias de igual teor e forma, na presença das testemunhas abaixo."; (8) local e data; (9) bloco de assinaturas: partes + duas testemunhas com nome e CPF.

---

## `juridico-nda`

**Uso:** fase pré-contratual de projeto de software ou consultoria — proteger especificação, arquitetura e orçamento apresentados antes do contrato de execução.

**Base legal:** arts. 104, 122, 408, 413, 416, 421 e 422 (boa-fé objetiva) e 593–609 CC; **art. 195, XI e XII, da Lei 9.279/96** (concorrência desleal por violação de segredo de negócio); Lei 9.610/98 (arts. 7º, 8º, 11 e 49); art. 784, III, CPC; LGPD (Lei 13.709/2018) quando houver dado pessoal.

**Alerta de PI que a skill DEVE embutir como nota ao usuário:** o art. 8º da Lei 9.610/98 (I e VII) **exclui** da proteção autoral as ideias, os métodos, os sistemas, os projetos e o aproveitamento comercial das ideias contidas na obra — jurisprudência do STJ consolidada. Direito autoral protege o **documento** (a expressão), não a **arquitetura** que ele descreve. Daí a ordem de prioridade das cláusulas: **não circunvenção** é a proteção principal; **segredo de negócio** (art. 195, XI e XII, Lei 9.279/96) é o fundamento que alcança a ideia e a solução; a cláusula de **PI autoral** é reforço sobre o documento.

**Titularidade da CONTRATADA PJ:** o art. 11, *caput*, da Lei 9.610/98 diz que autor é a pessoa **física** criadora. A titularidade patrimonial da pessoa jurídica vem de cessão ou de obra sob encomenda (art. 49) — a cláusula redige assim, não como "obra da CONTRATADA por força do art. 11".

**Cláusulas obrigatórias, nesta ordem:**

1. **Definições** — o que é "Informação Confidencial": informação técnica, comercial, financeira, know-how, especificação, arquitetura, modelagem de dados, cronograma e orçamento, por qualquer meio. Listar nominalmente os artefatos do projeto.
2. **Objeto** — regular sigilo, não circunvenção e titularidade do material da fase de especificação.
3. **Confidencialidade bilateral com retroatividade** — vigência retroativa à data do primeiro contato (`[DD/MM/AAAA]`); duração de 5 anos após o término da relação; obrigações da receptora (não divulgar, não reproduzir, limitar acesso a quem precisa saber).
4. **Exceções** — informação (a) de domínio público sem culpa da receptora; (b) já em posse legítima anterior; (c) exigida por lei ou ordem judicial, com comunicação prévia por escrito à reveladora antes da divulgação.
5. **Segredo de negócio** — declarar que a especificação e a arquitetura constituem conhecimento confidencial utilizável na prestação de serviços, cuja divulgação ou exploração sem autorização configura concorrência desleal (art. 195, XI e XII, Lei 9.279/96).
6. **Propriedade intelectual** — especificação, documentação e artefatos são obra intelectual cuja titularidade patrimonial é da CONTRATADA (arts. 7º e 49, Lei 9.610/98); licença de uso restrita a avaliação interna; cessão condicionada à quitação do contrato de execução. Separar explicitamente: eventual liberalidade quanto à cobrança **não** implica renúncia, cessão ou licença de PI.
7. **Não circunvenção** — vedado à CONTRATANTE executar, contratar ou fazer executar por terceiro solução baseada na especificação apresentada, por `[18-24]` meses, sem participação da CONTRATADA ou sem remunerar a fase de especificação.
8. **Trabalho adicional pré-contratual** (quando aplicável) — alteração de escopo pedida após `[data]` exige estimativa escrita (horas × R$/h) com aceite formal por e-mail ou mensagem; sem aceite, nada é executado nem devido.
9. **Remuneração condicionada** (quando aplicável) — trabalho aprovado e executado + contrato não celebrado no prazo de validade = pagamento das horas em 15 dias; contrato celebrado = valor integralmente abatido do preço.
10. **Marco de decisão** — validade da proposta: `[60]` dias; o decurso sem contratação caracteriza não continuidade, subsistindo confidencialidade, não circunvenção e PI.
11. **Cláusula penal** — multa compensatória pré-fixada, valor certo, exigível sem alegação de prejuízo (art. 416 CC), sem prejuízo de perdas e danos suplementares se convencionado. Valor proporcional: multa abusiva é reduzida pelo juiz (art. 413 CC).
12. **Proteção de dados** (quando houver dado pessoal) — finalidade, dever de segurança e devolução ou eliminação ao término.
13. **Disposições gerais** — alteração só por escrito assinado; ausência de vínculo societário ou trabalhista; tolerância não é novação.
14. **Foro** — comarca de Natal/RN (parametrizável).

---

## `juridico-contrato-ti`

**Base legal:** arts. 593–609 CC (prestação de serviço); **Lei 9.609/98, art. 4º** (software desenvolvido no âmbito de contrato de prestação de serviço pertence ao contratante, **salvo estipulação em contrário**); Lei 9.610/98 (arts. 7º, 49); LGPD (Lei 13.709/2018), com o art. 48 para comunicação de incidente; Marco Civil da Internet (Lei 12.965/2014) quando houver guarda de registro; art. 784, III, CPC. Arbitragem, se eleita: Lei 9.307/96.

**Alerta que a skill DEVE embutir:** por padrão legal, software sob encomenda pertence ao **CONTRATANTE**. Para reter framework, biblioteca e componente próprio reutilizável, a cláusula de PI DEVE separar: (a) **Componentes Pré-Existentes / de Fundação** — permanecem da CONTRATADA, licenciados ao cliente em caráter perpétuo e não exclusivo para operar o entregável; (b) **Entregáveis Específicos** — cedidos ao cliente após quitação integral.

**Cláusulas obrigatórias:**

1. **Objeto e escopo** — referenciar o Documento de Requisitos (`requisitos-cliente`) como **Anexo I**, parte integrante do contrato, com versão e data da baseline.
2. **Escopo negativo** — o que não está incluído; mudança de escopo só por aditivo formal.
3. **Metodologia e execução** — fases, sprints, entregáveis por fase; critérios de aceite objetivos e testáveis por entregável; prazo de aceite ou recusa fundamentada (ex.: 10 dias úteis; silêncio = aceite tácito).
4. **Obrigações da CONTRATADA.**
5. **Obrigações da CONTRATANTE** — informação, acesso e homologação nos prazos; atraso do cliente suspende o cronograma proporcionalmente.
6. **Preço e condições de pagamento** — pagamento vinculado a marco e aceite; reajuste por IPCA (ou IGP-M) para contrato acima de 12 meses, na data de aniversário; multa e juros de mora por atraso (ex.: 2% + 1% a.m. + correção).
7. **Prazo e cronograma** — cronograma como **Anexo II**; regras de replanejamento e efeito de dependência não atendida.
8. **Propriedade intelectual** — separação componentes pré-existentes × entregáveis específicos (ver alerta); cessão condicionada à quitação integral.
9. **Licenças de terceiros e open source** — relação das dependências de terceiros e suas licenças; a CONTRATADA declara não embarcar componente com licença incompatível com o uso pretendido pelo cliente; custo de licença proprietária é do cliente, salvo previsão diversa.
10. **Uso de IA generativa no desenvolvimento** (quando aplicável) — declarar se há uso de assistente de IA, com que salvaguardas (revisão humana, verificação de licença de código sugerido) e a quem cabe a responsabilidade pelo entregável — que continua sendo da CONTRATADA.
11. **Confidencialidade** — bilateral, sobrevive ao término por 5 anos, ou referência ao NDA já firmado (número e data).
12. **Proteção de dados (LGPD)** — papéis (controlador/operador), finalidade, base legal, medidas de segurança, término do tratamento, subcontratação de suboperador.
13. **Segurança e incidentes** — dever de comunicar incidente de segurança relevante à outra parte em prazo certo, para permitir o cumprimento do art. 48 da LGPD.
14. **Garantia e suporte** — prazo de garantia de correção de defeito pós-aceite (ex.: 90 dias), com a distinção entre **defeito** (desvio do critério de aceite — correção sem custo) e **melhoria** (escopo novo — aditivo).
15. **SLA** (quando houver suporte ou manutenção continuada) — disponibilidade mínima, tempo de resposta e de solução por severidade, janela de atendimento, penalidade por descumprimento. Pode ser Anexo III.
16. **Limitação de responsabilidade** — teto (ex.: valor total do contrato); exclusão de lucro cessante e dano indireto. Ressalvar dolo e o que a lei não permite limitar.
17. **Reversibilidade e transição de saída** — no término, por qualquer causa, a CONTRATADA entrega código-fonte dos entregáveis cedidos, repositório, dados do cliente em formato aberto, documentação e credenciais, em prazo certo, com período de transição remunerado se solicitado. É a cláusula anti-lock-in; sem ela o cliente fica dependente do fornecedor.
18. **Rescisão** — hipóteses, aviso prévio, pagamento proporcional do executado e das fases em andamento.
19. **Não aliciamento de equipe** — vedação recíproca de contratar profissional da outra parte por 12–24 meses.
20. **Disposições gerais** — independência das partes (sem vínculo trabalhista), cessão vedada sem anuência, comunicação válida (e-mail com confirmação), anticorrupção (Lei 12.846/2013) quando o cliente exigir.
21. **Foro** — Natal/RN (parametrizável). Opcional: mediação ou arbitragem prévia (Lei 9.307/96).

---

## `requisitos-cliente`

**Natureza:** entregável **técnico-comercial**, não jurídico. Vira Anexo I do `juridico-contrato-ti`. Não confundir com "Termo de Referência" da Lei 14.133/2021 (licitação pública) — no privado o nome é Documento de Requisitos, Especificação Funcional ou Documento de Visão.

**Recorte declarado no início do documento.** O documento cobre requisitos **do projeto** e/ou **do produto/serviço**, e a seção de Visão acompanha o recorte:

| Recorte | O que a Visão contém |
|---|---|
| Produto/serviço | visão de produto: problema, usuários, proposta de valor, resultado esperado, o que fica fora do produto |
| Projeto | visão de projeto: objetivo da contratação, entregas, fases, papéis, premissas de execução, critérios de sucesso |
| Ambos | as duas seções, na ordem produto → projeto |

**Duas versões — regra crítica de proteção de PI.** Este documento é o ativo que o NDA protege. Gerar **uma** versão por arquivo, nunca as duas juntas:

| | Versão A — Proposta Executiva | Versão B — Especificação Completa |
|---|---|---|
| Quando | pré-NDA / pré-contrato | pós-NDA assinado |
| Conteúdo | visão, problema, objetivos, macro-funcionalidades, fases em alto nível, **faixa** de investimento, prazo macro | tudo: arquitetura, modelagem de dados, backlog decomposto, decisões técnicas justificadas, orçamento e cronograma detalhados |
| Não contém | arquitetura detalhada, modelagem de dados, backlog decomposto, justificativa técnica | — |
| Marcação | validade da proposta | rodapé `CONFIDENCIAL` + marca d'água + nota de titularidade em todas as páginas |

**Estrutura da Versão B** (IDs rastreáveis, compatíveis com o `tabela_cliente.py` da skill):

1. Controle de versão e distribuição — versão, data, autor, mudanças; quem recebeu
2. Sumário executivo — problema, solução, resultado esperado (1 página)
3. Visão — conforme o recorte declarado (tabela acima)
4. Contexto e objetivos de negócio — mensuráveis (`OBJ-*`)
5. Escopo — incluído (`ESC-*`) e explicitamente excluído
6. Personas e jornadas principais
7. Requisitos funcionais — `RF-*`, priorizados (MoSCoW ou equivalente), com critério de aceite testável
8. Requisitos não funcionais — `RNF-*` (desempenho, segurança, LGPD, disponibilidade, compatibilidade), cada um com métrica e verificação
9. Restrições e premissas — `RC-*` / `PRE-*`, incluindo as premissas de responsabilidade do cliente (acesso, dado, homologação)
10. Arquitetura proposta — visão de alto nível, diagrama pela ferramenta da categoria (ADR-0009), stack justificada
11. **Fases e cronograma** — entregável por fase, dependências, marcos, datas ou durações, e os marcos de pagamento vinculados; base do Anexo II do contrato
12. **Previsão de orçamento** — valor por fase e total; **premissas da estimativa** (horas, perfis, R$/h, o que está e o que não está incluído); faixa quando a incerteza é real (ex.: ±20%) em vez de número falsamente preciso; condições de pagamento; validade da proposta (`[60]` dias); gatilhos de reestimativa
13. **Prazo total estimado** — duração e data provável de conclusão, com as dependências do cliente que a condicionam
14. Critérios de aceite por fase — objetivos e verificáveis
15. Riscos identificados — `RSK-*` com mitigação
16. Glossário
17. Nota legal de rodapé — titularidade da CONTRATADA, uso restrito a avaliação interna, referência ao NDA firmado (número e data)

Orçamento, prazo e cronograma (11–13) são **obrigatórios**: sem valor informado, entram como placeholder em destaque, nunca omitidos — é a parte que o cliente lê primeiro e a que o contrato pina.

**Formatação:** pode usar identidade visual da contratada; headers escaneáveis; tabela para requisito; sem juridiquês no corpo — a proteção jurídica fica na nota legal e no NDA.

---

## Coleta de variáveis e fechamento

Antes de gerar, coletar: partes com qualificação completa; datas (primeiro contato, assinatura, validade da proposta); valores (R$/h, multa, teto de responsabilidade); prazos (não circunvenção, confidencialidade, garantia, SLA); foro. O que faltar vira `[EM_DESTAQUE: …]`.

**Checklist de eficácia, impresso ao final de todo documento `juridico-*`:**

- [ ] duas testemunhas com nome e CPF
- [ ] assinatura por provedor com trilha de auditoria ou ICP-Brasil — a integridade conferida por provedor é o que dispensa testemunhas (art. 784, §4º, CPC); as testemunhas ficam por redundância
- [ ] rubrica em todas as páginas (versão física)
- [ ] duas vias de igual teor
- [ ] revisão por advogado(a)
- [ ] registro em RTD no dia da assinatura, se optado
