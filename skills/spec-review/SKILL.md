---
name: spec-review
description: Use when a delta spec and plan (specs/NNN-name/) deserve adversarial review before implementation — especially when the spec touches security, persistent data, external contracts, or new dependencies. Triggers include "/deltaspec:spec-review", "revisão adversarial", "stress-test da spec", "essa spec aguenta", or a user asking for extra scrutiny on a spec/plan before implement.
---

# spec-review

## Overview

Revisão adversarial de spec + plan (toggle opcional do ciclo deltaspec, pré-implement). **Grilling É a revisão adversarial** — esta skill não reimplementa o mecanismo: invoca `mattpocock-skills:grilling` sobre os artefatos. Distinto do gate analyze (consistência mecânica entre artefatos); aqui o alvo é o **mérito**: premissas frágeis, buracos de requisito, riscos.

## Processo

1. **Input:** `specs/NNN-nome/` — `spec.md` + cabeçalho-resumo do `plan.md`. Leia também o `TRUTH.md` para conflitos com o vigente.
2. **Motor:** invoque `mattpocock-skills:grilling` tendo a spec como objeto da entrevista, com o enquadramento: *"interrogue esta spec adversarialmente: premissas, estados de erro, dados persistentes, contratos externos, o que falta"*. Sem o plugin mattpocock-skills → **fallback**: conduza o roteiro de `references/adversarial-questions.md`, uma pergunta por vez, com o aviso *"spec-review degradado: mattpocock-skills/grilling não instalado"*.
3. **Output:** lista de achados + **edições propostas** na spec (blocos antes/depois). **Nunca aplique direto** — o usuário aprova cada edição; só então atualize o `spec.md`.

## Quando usar

- Opcional em qualquer tipo com ciclo; **recomendada** quando a spec toca segurança, dados persistentes, contrato externo ou dependência nova (mesmos gatilhos que juntam `domain-modeling` ao clarify).
- Não substitui o analyze (que sempre roda no ciclo completo) nem o review de código.

## Erros comuns

| Erro | Correto |
|---|---|
| Aplicar edições na spec sem aprovação | Propor antes/depois; usuário aprova cada uma |
| Reimplementar entrevista própria com o plugin instalado | mattpocock-skills:grilling é o motor; fallback só na ausência |
| Rodar sobre o plan.md inteiro | Só o cabeçalho-resumo; o detalhe do plano é efêmero |
| Confundir com analyze | analyze = consistência entre artefatos; spec-review = mérito da spec |

## Arquivos da skill

- `references/adversarial-questions.md` — fallback: perguntas adversariais canônicas.
