# Teste de software — referencial teórico e diretrizes

Transcrição focada da dissertação *Avaliação da efetividade de uma suíte de teste de sistema aplicada ao contexto do Middleware Ginga* (Iuri Guerra de Freitas Pereira, UFRN/IMD, 2019). Mantém o texto dos conceitos (capítulo 2) e extrai do restante o objetivo e as conclusões que valem como diretriz para escrever testes. O contexto Ginga/SBTVD foi deixado de fora, salvo quando sustenta uma conclusão.

## 1. Problema e objetivo (cap. 1)

O Teste de Software pode ser definido como a verificação dinâmica de que um programa provê comportamentos esperados, de acordo com alguma especificação, quando exercitado por um conjunto finito de casos de testes.

Razões que dificultam adotar um processo de teste (Crespo et al., 2004): falta de profissionais especializados; o teste é um processo caro; pouco conhecimento sobre a relação custo-benefício dos testes; desconhecimento sobre como planejar o processo.

Problema de pesquisa: é comum usar critérios de cobertura para avaliar suítes de teste, pois são de fácil compreensão e seu critério de parada é bem estabelecido. A cobertura mede qual parte do código foi executada pelos testes, porém não leva em conta se um método foi testado com uma afirmação correta ou se foi executado sem nenhuma afirmação ou com afirmações incompletas (Niedermayr; Juergens; Wagner, 2016). Estudos divergem sobre a correlação entre cobertura e efetividade; Inozemtseva e Holmes (2014) sugerem que a cobertura, útil para identificar partes não testadas, não deveria ser usada como indicador de efetividade de uma suíte. Quase todos esses estudos são em nível unitário; em nível de sistema há dificuldade de encontrar critérios bem definidos para avaliar a efetividade de uma suíte.

Objetivo geral: realizar um estudo sobre a abordagem de automatização dos testes de sistema com o propósito de analisar a sua efetividade. Objetivos específicos: avaliar a efetividade da suíte automatizada; identificar limitações e melhorias na abordagem de automatização; explorar possibilidades de melhorá-la.

## 2. Teste de software (cap. 2.1)

Teste de Software é definido por Myers e Sandler (2004) como o processo de executar um programa com o objetivo de encontrar erros. Quando se testa um programa, deseja-se adicionar algum valor a ele: incrementar a qualidade ou confiabilidade, o que significa achar e remover erros. Não se testa um programa para provar que ele funciona; ao invés disso, é assumido que o programa contém erros e testamos o programa para encontrá-los.

Os Testes de Software se dividem em três dimensões ortogonais (modelo adaptado de Crespo et al., 2004):

- **Quando testar** — fase do desenvolvimento → níveis de teste: Unidade, Integração, Sistema.
- **O que testar** — atributo de qualidade em foco → tipos de teste: Funcionalidade, Não-Funcional (características), Regressão.
- **Como testar** — técnica escolhida → Funcional (caixa-preta), Estrutural (caixa-branca), Mutação.

### 2.1 Níveis de teste

Os níveis de teste estão relacionados com as fases do desenvolvimento do software e dizem respeito a quando determinado teste deve ser empregado.

**Teste de Unidade.** Focaliza o esforço na verificação da unidade, isto é, da menor unidade testável do projeto, tipicamente um componente ou módulo (Pressman, 2009). Foca na lógica de processamento e nas estruturas de dados dentro dos limites de uma unidade. O projeto do teste de unidade pode ocorrer antes mesmo da codificação começar ou após o código ter sido gerado.

**Teste de Integração.** Busca verificar se as interdependências das unidades contêm erros, ou seja, se duas ou mais unidades conseguem se comunicar corretamente entre si. É a fase intermediária: após verificar a corretude das unidades, verifica-se a comunicação entre elas; em seguida, propriedades de mais alto nível, pelos testes de sistema.

**Teste de Sistema.** Tem o objetivo de verificar se todas as funcionalidades e todos os atributos de qualidade especificados nos documentos de requisitos estão corretamente implementados. São verificados não apenas os requisitos funcionais, mas também os não-funcionais: segurança, performance, usabilidade, portabilidade etc.

### 2.2 Tipos de teste

Relacionados a "o que" testar, ao objetivo a ser alcançado.

**Teste de Funcionalidade.** Processo que busca encontrar discrepâncias entre o comportamento do programa e suas especificações externas. Uma especificação externa é uma descrição precisa do comportamento do programa pela perspectiva do usuário final. É geralmente uma atividade de técnica caixa-preta (Myers; Sandler, 2004).

**Teste Não-Funcional.** Verifica se um determinado atributo de qualidade é atendido num determinado grau: segurança, desempenho, confiabilidade, dentre outros.

**Teste de Regressão.** Objetiva identificar se funcionalidades do software regrediram ao longo da evolução do sistema — casos em que funcionalidades que antes funcionavam deixaram de funcionar devido a mudanças. É realizado após mudanças no sistema (melhoria funcional ou correção), usualmente por um subconjunto de casos de teste. É importante porque defeitos tendem a ser introduzidos no código durante a realização de mudanças e correções de erros.

### 2.3 Técnicas de teste

Relacionadas a como testar o programa.

**Teste funcional (caixa-preta).** Baseado na especificação: os casos de teste são construídos baseados apenas no que o documento de especificação diz que ele tem que fazer e não no que está implementado. Consideram-se apenas entradas e saídas da unidade, módulo ou componente (Delamaro; Maldonado; Jino, 2016).

**Teste estrutural (caixa-branca).** Estabelece os requisitos de teste baseado em uma implementação, requerendo a execução de partes ou componentes elementares do programa. Os caminhos lógicos são testados, fornecendo-se casos que põem à prova tanto um conjunto específico de condições e/ou laços como valores limites de suas variáveis (Delamaro; Maldonado; Jino, 2016).

**Critérios de cobertura.** Métricas tipicamente associadas ao teste estrutural que expressam qual proporção de um determinado elemento de código é executada quando se roda uma suíte de testes:

- cobertura por função — quantas funções ou sub-rotinas foram executadas;
- cobertura por statements (linhas) — quantas vezes uma linha foi executada;
- cobertura por branches — quantas vezes uma estrutura de controle (if..else) foi executada;
- cobertura por condição (predicado) — se cada condição booleana foi testada.

Cobertura de código é uma métrica meramente quantitativa que não deve ser utilizada para aferir qualidade do conjunto de teste por si só. Tem por objetivo demonstrar quanto do código foi exercitado e deve ser levada em consideração para verificar em quais pontos o teste passou ou nunca passou. Aumentar os índices de cobertura nem sempre significa que a suíte estará sendo efetiva em descobrir falhas (Inozemtseva; Holmes, 2014; Niedermayr; Juergens; Wagner, 2016). Por outro lado, suítes que não tenham bom nível de cobertura necessitam de atenção, pois levantam a suspeita de que o código não exercitado pode esconder falhas.

## 3. O que a pesquisa mediu (caps. 3–5, resumo)

- Suíte de 2.812 casos de teste de sistema, caixa-preta, automatizada por comparação de imagem (golden sample) com espera fixa de 5 s para todos os casos.
- Cobertura por linha: 56,7% em 40.003 LOC, 476 arquivos; 27,1% dos arquivos com cobertura ~0% e 22,5% com 100%. Sem correlação entre tamanho do arquivo e cobertura (Pearson 0,006).
- Entrevistas e survey apontaram três causas para o código não coberto: código legado nunca removido; automatização que não executa a especificação inteira (espera fixa, sem interação, sem áudio/vídeo); escopo da suíte menor que o escopo do produto.
- Teste exploratório 1: reconfigurar 542 casos (19,27%) para seguir a especificação subiu a cobertura só 0,9%.
- Teste exploratório 2: **um** caso de teste novo, escrito para alcançar código nunca exercitado (âncora temporal UTC), subiu 0,4%, levou 4 arquivos de 0% a cobertura relevante e expôs uma falha de segmentação (destrutor mal implementado) que ficou adormecida enquanto aquela parte nunca era exercitada.

## 4. Conclusões que viram diretriz (cap. 7)

1. A suíte de conformidade não garante por si só a conformidade com todas as funcionalidades da norma. Novos testes precisam ser criados com o objetivo de exercitar partes não cobertas do código.
2. Criar testes novos, dirigidos a partes não cobertas, traz retorno mais rápido — tanto em expor falha quanto em cobertura — do que reconfigurar em massa os testes existentes.
3. Exercitar partes nunca exercitadas em nível de sistema expõe vulnerabilidades que passaram despercebidas nas fases anteriores do ciclo. A falha só pôde ser descoberta através da execução de partes do código que nunca haviam sido exercitadas antes.
4. O teste automatizado detecta regressão e falha fatal cedo; não substitui a validação no ambiente final quando os ambientes diferem.
5. Código legado inflaciona o denominador da cobertura; remover o que não participa do fluxo deixa o índice próximo do real.
6. Baixa cobertura em nível de sistema indica suíte a melhorar; alta cobertura não prova efetividade.
7. Suspeita de trabalho futuro: casos de teste equivalentes (que exercitam as mesmas linhas) abrem margem para minimização da suíte.

## 5. Diretriz derivada (não está na dissertação — é a regra de uso)

Teste existe para encontrar falha, não para provar que funciona. Quando um teste falha, há duas saídas legítimas: corrigir o software ou corrigir o teste porque **o requisito mudou**. Nunca se altera o requisito, o oráculo ou o dado esperado para que o teste passe. Um teste só muda para acompanhar o requisito novo, nunca para acomodar o comportamento atual.
