# Test plan — delta-029
<!-- derivado dos cenários DADO/QUANDO/ENTÃO da spec e das verificações do tasks.md — não inventa cenário novo (R3, delta-015) -->
<!-- teste manual roteirizado conta como cobertura; todo Rn/RNFn da spec precisa de ≥1 caso (C8) -->
- [x] CT1 — a seção `[Não lançado]` continua verificada e a lançada não · cobre: R1 · tipo: auto · verificação: fixture com link morto nas duas seções → exatamente **1** `[C3] link morto`, o da seção viva
- [x] CT2 — o corte é na **primeira** seção lançada · cobre: R1 · tipo: auto · verificação: fixture com `[1.1.0]` e `[1.0.0]`, com link morto na segunda → nenhum achado; mutação trocando o padrão por `^## \[` (que engoliria `[Não lançado]`) quebra o selftest
- [x] CT3 — arquivo sem seção lançada é varrido inteiro · cobre: R1 · tipo: auto · verificação: a fixture `sujo`, vigente desde antes da delta, é markdown comum com link morto e segue acusando — fixture nova para o mesmo caminho foi cortada no review por não discriminar mutante nenhum
- [x] CT4 — o recorte olha conteúdo, não nome · cobre: R1 · tipo: auto · verificação: a fixture do CT1 não se chama `CHANGELOG.md` e mesmo assim é recortada
- [x] CT5 — link em crase é sintaxe citada · cobre: R1 · tipo: auto · verificação: fixture com o mesmo link morto dentro de crase (não acusa) e fora dela na linha seguinte (acusa) — as duas metades no mesmo caso, senão o teste passa por omissão
- [x] CT6 — link em bloco cercado também · cobre: R1 · tipo: auto · verificação: fixture com link morto entre ``` → nenhum achado; a cerca de fechamento restaura a varredura na linha seguinte
- [x] CT7 — nada da delta-027 regrediu · cobre: R1 · tipo: auto · verificação: as fixtures vigentes seguem verdes — conjunto próprio do C3, atalho `../../issues/N`, histórico imutável por default e por chave declarada
- [x] CT8 — aceite medido no repo que originou o débito · cobre: R1 · tipo: manual · verificação: `validate_integrity.py ~/code/imex/imex-travelplanner` sai de **96** para **3** links mortos, os 3 sendo o rot real do README de lá; e `validate_integrity.py .` continua `PASS`
