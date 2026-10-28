# Busca de falhas — delta-{{NNN}}
<!-- escrito depois do implement; complementa o test-plan.md (confirmação) e nunca o substitui -->
Oráculo: {{TRUTH.md | degradado — <fonte citada por caminho:linha> | nenhum}}
Mapa: {{comando de cobertura rodado}} · antes: {{%}} · depois: {{%}} <!-- registro, não meta -->

## Alvos (não exercitado ou limite calado)
- {{arquivo:função}} — {{por que foi alvo: 0% / ramo sem teste / limite que o Rn cala}} · governado por: {{Rn | sem Rn}}

## Testes escritos
- {{arquivo:nome do teste}} · nível: {{unidade|integração|sistema}} · oráculo: {{Rn}} · resultado no 1º run: {{vermelho → falha Fn | verde (caracterização, cita Rn)}}

## Falhas encontradas
- F1 — {{o que o código faz × o que o Rn manda}} · destino: {{corrigido nesta delta (commit) | Tipo: bugfix NNN}}

## Pendências (OBRIGATÓRIO — "nenhuma" só é válido com zero `todo`)
- {{DT-NNN | #issue | pendencias.md#n}} — {{comportamento sem Rn, entrada}} · teste: {{arquivo:nome}} em `todo`
