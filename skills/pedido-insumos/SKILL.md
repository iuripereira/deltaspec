---
name: pedido-insumos
description: Use when pending client inputs need to be chased by e-mail in a project that keeps deltaspec discovery records (docs/discovery/questions.md, pedido-validacao-*.md, debts/) — produces one ready-to-paste e-mail per owner, ranked and with an explicit deadline. Triggers include "/deltaspec:pedido-insumos", "cobrar os insumos", "gerar e-mail de cobrança", "quem está devendo insumo", "pedir os dados que faltam", "cobrar o cliente". Not for the reconciliation of an input that already arrived — that is rodada-insumos.
---

# pedido-insumos

## Overview

Gera e-mails de cobrança de insumos pendentes — **um por destinatário**, prontos para colar. Argumento opcional: pessoas-alvo e prazo (sem argumento = todos os donos com pendência, prazo 2 dias úteis).

Fronteira com a `rodada-insumos`: esta skill **cobra o que ainda não chegou**; a `rodada-insumos` **concilia o que chegou**. Cobrança gerada aqui vira insumo lá quando a resposta voltar.

## Fontes (nesta ordem; use as que existirem no repo)

1. Registro vivo de perguntas (`docs/discovery/questions.md` ou equivalente) — status ⬜/🔶 com dono externo.
2. Pedido de validação/insumos anterior (`docs/discovery/pedido-validacao-*.md`) — checklist de artefatos não entregues.
3. Dossiês de reunião (`docs/discovery/*.md`) — promessas com timestamp ("enviar ainda hoje", "ficou de mandar").
4. `DEBT.md` / `debts/` — pendências cujo dono é do cliente, não do consultor.

## Regras de composição

1. **Um e-mail por pessoa; patrocinador do projeto em CC.** Nunca e-mail coletivo — responsabilidade diluída = ninguém responde.
2. Estrutura de cada e-mail: saudação de 1 linha que **reconhece o que a pessoa já entregou** (se algo chegou) → bloco **Insumos (enviar)** → bloco **Perguntas (responder neste e-mail, citando o código)** → **prazo com data explícita** (nunca "em breve") → referências por link.
3. Itens **ranqueados por prioridade** (🔴 trava regra/desenvolvimento · 🟡 refina). Máximo ~6 itens por pessoa — excedente fica para a próxima rodada; e-mail longo não é respondido.
4. Cite o **código estável** de cada item (GQ1, GT2, V-B1…) para a resposta voltar ao registro vivo.
5. Cada item em 1–2 linhas: o que se pede + por que trava (uma oração, de preferência com um número: "hoje 0 de 613 são dispensadas"). Contexto histórico vai por link, não no corpo.
6. Promessa antiga = **citar a data em que foi combinada** ("combinado em 05/08, ainda pendente"). Tom assertivo: sem "se possível", "quando puder", "gostaríamos".
7. Link só para página **publicada e verificada** (confira as URLs reais do site do projeto — ex.: `ls` no diretório de publicação ou o script de publicação); sem página, anexe o PDF.
8. **Nada de PII/dado sensível** no corpo do e-mail.

## Saída

1. Um bloco por e-mail: **Para / CC / Assunto / corpo**, pronto para colar.
2. Depois de gerar, registre a cobrança no registro do projeto (handoff ou DEBT) com data de envio e prazo — a cobrança sem registro não é cobrável na próxima rodada.

**Enviar é do usuário, nunca da skill.** A saída é texto para colar; disparar e-mail em nome de alguém é decisão de quem assina.
