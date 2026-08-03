# Política de Segurança

## Versões suportadas

A versão canônica vive nas tags git `vX.Y.Z` ([CLAUDE.md](CLAUDE.md)). Correção de segurança sai sempre na **última versão publicada** — versões anteriores não recebem patch; atualize o plugin (`/plugin update deltaspec`) para receber a correção.

| Versão            | Suportada          |
| ----------------- | ------------------ |
| Última tag        | :white_check_mark: |
| Qualquer anterior | :x:                |

## Como reportar uma vulnerabilidade

**Não abra issue pública.** Reporte em privado pelo GitHub Security Advisories: [Report a vulnerability](https://github.com/iuripereira/deltaspec/security/advisories/new).

Inclua o que puder: versão afetada (tag), passos de reprodução e o impacto que você enxerga.

O que esperar:

- **Confirmação de recebimento em até 3 dias úteis.**
- **Correção ou decisão fundamentada em até 30 dias.** Aceito → correção na última versão e advisory publicado com crédito a quem reportou (salvo pedido de anonimato). Recusado → a justificativa fica registrada no próprio advisory.
- Sem resposta no prazo, escreva para <iuripereira@gmail.com> com `[SECURITY]` no assunto.

## Modelo de ameaça

O deltaspec é um **plugin local do Claude Code**: skills em Markdown + scripts de gate em Python (biblioteca padrão mais uma única dependência externa admitida, `PyYAML`; a política e a decisão que a admite têm dono no [CLAUDE.md, seção Clean Code](CLAUDE.md#clean-code)). Não tem servidor, não abre porta, não envia telemetria e não acessa a rede. Os scripts leem e escrevem apenas no repositório em que você os roda, com as suas permissões de usuário.

Isso define o que é e o que não é vulnerabilidade aqui:

| No escopo | Fora do escopo |
| --- | --- |
| Execução de código disparada pelo parse de um artefato malicioso (spec, delta, `deps.toml`, template) pelos scripts de gate | Ler ou escrever um caminho que você mesmo passou ao script |
| Injeção de comando nos `subprocess` dos scripts a partir de conteúdo não confiável | Negação de serviço contra a sua própria máquina com o seu próprio input |
| Escrita fora do diretório do projeto a partir de input não confiável | Achado de análise estática sem input não confiável alcançável |
| Instrução maliciosa embutida num artefato do ciclo (spec/PRD vindo de terceiro) que leve uma skill a ação destrutiva fora do fluxo previsto | Vulnerabilidade no Claude Code em si — reporte à [Anthropic no HackerOne](https://hackerone.com/anthropic) |

Na dúvida se algo está na fronteira, reporte — a triagem é responsabilidade de quem mantém, não de quem reporta.

## Práticas do repositório

As práticas que sustentam esta política têm dono no [CLAUDE.md](CLAUDE.md) — Segurança para as práticas abaixo, Clean Code para a política de dependência: GitHub Actions pinadas por SHA, gates com superfície de cadeia de dependências Python de **um** pacote (`PyYAML`, admitido por decisão registrada — dependência nova exige ADR própria) e secrets fora do versionamento.
