<!-- resumo sdd-iuri · ≤15 linhas · única parte do plano lida pelo analyze e pelo humano -->
**Objetivo:** versionar o conhecimento jurídico-comercial como reference canônico da `doc-entregavel` e ligar a SKILL.md a ele por tipo de documento, com a base jurisprudencial corrigida. **Cobre:** R1, R2, R3 (da delta-011) **Decisões duráveis → ADRs:** nenhuma (a decisão de fundo está na ADR-0009) **Riscos assumidos:** jurisprudência citada pode ser superada — a política de geração é conservadora e não depende dela; rodapé CONFIDENCIAL segue manual (pendência registrada).

---

## Passos

1. **`skills/doc-entregavel/references/juridico.md`** — novo, fonte canônica das regras de conteúdo jurídico. Organização: regras gerais (minuta, formatação de mercado, eficácia executiva, estrutura canônica) → um bloco por tipo (`juridico-nda`, `juridico-contrato-ti`, `requisitos-cliente`) → coleta de variáveis + checklist de eficácia. Migra o conteúdo de `prompt-doc-entregavel-juridico.md` **com as correções da auditoria**:
   - **Assinatura eletrônica** — corrigir a justificativa invertida. STJ (REsp 2.205.708-PR, 4ª T., 04/11/2025, Info 871; REsp 2.150.278-PR, 3ª T., 24/09/2024) admite **qualquer modalidade** de assinatura eletrônica em título executivo, dispensadas as testemunhas quando a integridade é conferida por provedor de assinatura (art. 784 §4º CPC, Lei 14.620/2023; art. 10 §2º MP 2.200-2/2001) — ICP-Brasil **não** é obrigatório. Manter a política conservadora (sempre gerar bloco de 2 testemunhas + recomendar provedor com trilha de auditoria) declarada **como redundância deliberada**, não como exigência legal.
   - **Titularidade autoral de PJ** — art. 11 caput da Lei 9.610/98 é o autor pessoa física; titularidade da CONTRATADA PJ vem de cessão/obra sob encomenda (art. 49). Corrigir a citação.
   - **Lei 14.063/2020** — é regime das interações com entes públicos; em relação estritamente privada o fundamento é o art. 10 §2º da MP 2.200-2/2001. Precisar a citação.
   - **NDA** — acrescentar art. 195, XI e XII da Lei 9.279/96 (concorrência desleal / segredo de negócio) como a proteção real da ideia e da arquitetura, que o direito autoral não cobre.
   - **Contrato de TI** — acrescentar cláusulas hoje padrão: reversibilidade/transição de saída (código-fonte, repositório, dados e credenciais no término), SLA quando houver suporte continuado, segurança e comunicação de incidente (art. 48 LGPD), licenças de terceiros/open source, e uso de IA generativa no desenvolvimento.
   - **RTD** — manter o alerta (efeitos a partir da data do registro desde 01/01/2024, retroação de 20 dias revogada — Lei 14.382/2022) e simplificar: a mesma lei acabou com a exigência de registro em múltiplas comarcas.
   - **`requisitos-cliente`** — declarar o recorte (requisitos de projeto e/ou de produto/serviço), seção de Visão conforme o recorte, e tornar obrigatórias previsão de orçamento por fase (com premissas e faixa), prazo total estimado e cronograma com marcos de pagamento. Versão A carrega faixa + prazo macro; Versão B, o detalhe.
   - Declarar no topo a data de verificação da base jurídica.
2. **`skills/doc-entregavel/SKILL.md`** — seção curta de dispatch por tipo apontando o reference (sem reproduzir regra), nota de que `tabela_cliente.py` vale para PRD/`requisitos-cliente` e não para os tipos `juridico-*`, linhas novas em "Erros comuns" (ABNT em contrato, entregar sem bloco de testemunhas, misturar Versão A e B), `description` do frontmatter com os triggers novos, e o reference listado em "Arquivos da skill".
3. **Remover** `skills/doc-entregavel/prompt-doc-entregavel-juridico.md` — substituído pelo reference (nunca foi rastreado pelo git).
4. **Gates** — `check_cycle.py specs/011-doc-juridico`, os dois `--selftest`, e o grep de caminho absoluto de máquina em `skills/`.
5. **Registro** — `CHANGELOG.md` em `[Não lançado]` (Adicionado), `HANDOFF.md`, PR com Conventional Commits no escopo `011-doc-juridico`.
6. **Archive** — `Estado: arquivada`, consolidação no `specs/TRUTH.md` (R1–R3 entram como próximos números R livres, domínio novo "Entregáveis para cliente"), pendência aberta → `DT-NNN` no `DEBT.md`, diretório para `specs/_archive/011-doc-juridico/`.

## TDD

Dispensado: a delta é conteúdo de skill (Markdown), sem lógica nova em script. A verificação é o gate `check_cycle.py` + os selftests existentes, que não mudam de comportamento.
