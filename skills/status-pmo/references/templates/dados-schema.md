# dados.json — contrato de dados do site de status

> O gerador separa **coleta** (`montar_dados` → este dict, serializado como `dados.json` ao lado das páginas) de **render** (consome só o dict). A integração externa (Jira etc.) substitui campos da coleta **mantendo este schema**; o render nunca muda. Datas em ISO `AAAA-MM-DD`; textos em markdown-lite (`**negrito**`, `_itálico_`, `` `código` ``).

```jsonc
{
  "gerado_em": "31/07/2026 20:15",       // carimbo da geração
  "hoje": "2026-07-31",
  "d0": "2026-08-03",                     // âncora do cronograma
  "semana": {
    "id": "2026-W31", "periodo": "27/07–02/08/2026",
    "resumo": "…",                        // string
    "realizado": [["Nome do Projeto", ["item", "…"]]],
    "reunioes": ["…"], "decisoes": ["…"], "pendencias": ["…"]
  },
  "projetos": [{
    "nome": "…", "dir": "repo-dir", "curto": "…",
    "prazo": "2026-09-02", "prazo_nota": "D0 + 30d — contrato", "fonte": "repo/PRD.md:534",
    "jira": "TP",                         // chave do projeto no sistema externo ("" se não houver)
    "etapas": [["Etapa", "feita|em curso|prevista"]],
    "epicos": [{                          // 1 por etapa, mesma ordem (docs/epicos/<dir>.md)
      "id": "E1", "nome": "…", "dep": ["E0"], "notas": ["…"],
      "status": "…",                      // espelho do status da etapa (dono: cronograma)
      "tarefas": [{"id": "E1-T1", "nome": "RF-01 — …", "dep": ["E1-T0"], "status": "prevista"}]
    }],
    "notas": ["…"],
    "pct": 38,                            // derivado: feita=1 · em curso=0,5 · prevista=0
    "fase": "…",                          // primeira etapa em curso (senão prevista, senão "Concluído")
    "cal_pct": 12,                        // % de calendário decorrido D0→prazo
    "farol": "verde|amarelo|vermelho",    // vermelho=prazo estourado; verde=pct ≥ cal_pct − 10 p.p.
    "dias_restantes": 33,
    "marcos": [{"nome": "…", "data": "2026-09-02", "projeto": "…|todos"}],
    "visao": "…",                         // 1º parágrafo do § Objetivo/Visão do PRD (allowlist)
    "visao_fonte": "repo/PRD.md",
    "painel": {"updated": "…", "prd": "1.6", "debt_open": 1, "debt_total": 3,
                "released": "0.2.0", "pending": 2, "next_step": "…"}
  }],
  "marcos": [{"nome": "…", "data": "…", "projeto": "…"}],   // todos os marcos do cronograma
  "painel_extra": [{ /* repos fora do cronograma (ex.: contratos), campos do painel */ }]
}
```

Regras: campo ausente na fonte → `"—"`/`null`/`0` (geração tolerante); `pct` sempre em `[0,100]` (self-check); novos campos são **aditivos** — remover ou renomear campo é breaking change do contrato e pede delta.
