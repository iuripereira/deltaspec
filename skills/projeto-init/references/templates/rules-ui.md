---
paths:
  - "{{glob de UI do stack}}"
---

# UI: idioma, formato e acessibilidade

- **Todo texto de UI** em **{{idioma, ex.: PT-BR}}** salvo indicação contrária.
- **Moeda/data via helper único** (ex.: `Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" })`) — nunca formatar `R$` à mão. Datas ISO internas (`AAAA-MM-DD`), exibição `DD/MM/AAAA`.
- **Acessibilidade é requisito** (web): `label` em todo input, `aria-label` em controles, navegação por teclado, `skip-to-content`, alvos de toque ≥ 44px, mobile-first.
