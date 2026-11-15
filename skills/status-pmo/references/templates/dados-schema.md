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
    "marcos": [{"nome": "…", "data": "2026-09-02", "projeto": "…|todos",
                "id": "M1",               // prefixo do nome (M1, S2…); "" sem prefixo
                "entrega": "…",           // coluna `Entrega` do cronograma; "—" sem ela
                "situacao": "entregue|aguardando aceite|atrasada|prevista",
                "dias_atraso": 0}],
    "visao": "…",                         // 1º parágrafo do § Objetivo/Visão do PRD (allowlist)
    "visao_fonte": "repo/PRD.md",
    "painel": {"updated": "…", "prd": "1.6", "debt_open": 1, "debt_total": 3,
                "released": "0.2.0", "pending": 2, "next_step": "…"},

    // ---- one page (delta-122; regras em ../onepage-layout.md) ----
    "saude": {"nivel": "verde|amarelo|vermelho|nao-iniciado",
              "forma": "●|▲|◆|○",
              "regra": "prazo e ritmo|marcos|itens abertos",   // a que definiu o nível
              "motivo": "marco M2 atrasado +6 dias",          // texto curto da seção #saude
              "tendencia": "↑|→|↓|—"},
    "objetivos": [{"id": "O1", "dor": "…", "impacto": "…|—", "evidencia": "…|—",
                   "situacao": "●|◐|○", "entregas": ["E1", "E3"]}],   // 1 a 4
    "objetivos_dispensa": false,          // true = "projeto operacional, sem objetivo de impacto"
    //   epicos[*].tarefas[*] ganha: "esperado": "…|—", "entregue": true|false
    "escopo": {"requisitos": {"ok": 7, "total": 18, "vencidos": 1},
               "entregas":   {"ok": 2, "total": 6,  "vencidas": 1}},
    "defeitos":           [/* item */],
    "pendencias_cliente": [/* item + "solicitacao_url": "…|null" */],
    "impedimentos":       [/* item */],
    "riscos":             [/* item + "situacao": "aberto|mitigado|materializado" */]
    //   item = {"id": "DT-012|KEY-45", "resumo": "…", "nivel": "Crítica|Alta|Média|Baixa",
    //           "prazo": "AAAA-MM-DD|null", "dias_atraso": 0, "etapa": "E2|null",
    //           "href": "página de detalhe|null"} — listas já ORDENADAS (nível, atraso, id)
  }],
  "marcos": [{"nome": "…", "data": "…", "projeto": "…"}],   // todos os marcos do cronograma
  "portfolio": {"projetos": 5, "no_prazo": 2, "em_risco": 2, "atrasados": 1,   // roadmap (delta-122)
                "marcos_ok": 4, "marcos_total": 19,
                "proximo_prazo": {"data": "2026-10-02", "projeto": "…"}},
  "painel_extra": [{ /* repos fora do cronograma (ex.: contratos), campos do painel */ }]
}
```

Regras: campo ausente na fonte → `"—"`/`null`/`0` (geração tolerante); `pct` sempre em `[0,100]` (self-check); novos campos são **aditivos** — remover ou renomear campo é breaking change do contrato e pede delta. Os campos do one page e do roadmap (delta-122) são calculados na coleta (`montar_dados`), nunca no render: nível, ordem e situação chegam prontos, e o render só escolhe os `TOP_N` primeiros. Mais de 4 `objetivos`, ou lista vazia com `objetivos_dispensa: false`, reprova o self-check.
