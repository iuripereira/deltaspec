# ADR-0032: Erro mecânico de caminho é corrigível no registro imutável — conteúdo de época não é

- **Status:** Accepted (2026-08-11, delta-051)
- **Data:** 2026-08-11
- **Supersedes:** —
- **Superseded by:** [ADR-0035](ADR-0035-changelog-lancado-e-projecao-reescrevivel.md) — que reafirma integralmente o recorte de caminho e de conteúdo de época, e retira apenas a **forma** da entrada lançada do CHANGELOG da classe imutável

## Context

O framework trata `specs/_archive/**`, `docs/adrs/**` e as seções lançadas do `CHANGELOG.md` como **registro imutável**: o rename `sdd-iuri` → `deltaspec` não os reescreveu (R47), o C3 do `validate_integrity.py` os mantém fora da varredura de links por chave própria (`exclude_links_globs`, R13) e a justificativa registrada é explícita — "apontar rot que a política proíbe corrigir seria ruído".

Essa política nasceu para proteger **conteúdo**: o nome antigo do framework, a decisão como ela foi tomada, o número que valia naquela época. A imutabilidade é o que faz o archive servir de registro histórico confiável.

A delta-047 encontrou uma classe de estrago que a política não previu. O passo de archive move `specs/NNN-nome/` → `specs/_archive/NNN-nome/`, o que muda a profundidade de todo link relativo dos artefatos — e a regra 5 do archive nunca mandou recalculá-los. O resultado medido em 2026-08-11: **32 links quebrados em 17 deltas arquivadas**. Não é deriva de época; o conteúdo original apontava para o alvo certo, e foi a mecânica do move que o quebrou. Como o C3 não varre o archive, o apodrecimento é silencioso — e a delta-041 corrigiu os seus à mão sem que o passo estivesse escrito em lugar nenhum, o que produziu um archive internamente inconsistente (a 041 certa, a 040 quebrada).

Ler a imutabilidade como absoluta obriga a preservar deliberadamente 32 links quebrados enquanto se escreve a regra que os proíbe. Lê-la como negociável dissolve a garantia que faz o archive valer alguma coisa.

## Decision

Recortamos a política de imutabilidade **por classe de achado**, não por diretório:

- **Erro mecânico de caminho é corrigível** no registro imutável — link relativo cuja profundidade foi quebrada pelo próprio move do archive. O conteúdo pretendido não muda: o link volta a apontar para onde sempre apontou. A correção é verificável por máquina (o destino resolve ou não resolve), o que a torna auditável em vez de discricionária.
- **Conteúdo de época permanece intocável** — nome histórico, número medido, decisão como foi tomada, prosa do requisito vigente à época. Aqui o texto *é* o registro, e reescrevê-lo apaga o que aconteceu.

O limite entre as duas classes é este: se a edição muda **o que o documento afirma**, é conteúdo de época e não se toca; se ela apenas restaura **a resolução de uma referência** que o documento já fazia, é erro mecânico e se corrige.

Renunciamos a duas alternativas. **Manter a imutabilidade absoluta** (deixar os 34 quebrados) foi recusada porque produz um registro que não navega — o archive existe para ser lido, e link morto o degrada tanto quanto reescrita. **Abrir o archive para edição discricionária** foi recusada porque a garantia da imutabilidade não sobrevive a exceções julgadas caso a caso; a exceção só é segura porque é decidível por máquina.

A garantia da fronteira é mecânica, não disciplinar: o **C13** do `check_cycle.py` confere os links relativos das deltas arquivadas, e o C3 do `validate_integrity.py` **segue cego ao archive** — a fronteira é por classe, não por diretório, e nenhum gate ganha licença genérica para auditar registro imutável.

## Consequences

Fica mais fácil: o archive volta a ser navegável e passa a ter quem o defenda mecanicamente; a regra 5 do archive ganha a linha que faltava, e a correção pega carona na rodada de `check_cycle.py` que a regra 6 já torna obrigatória — zero disciplina nova.

Fica mais difícil: "o archive é imutável" deixa de ser uma frase de uma linha e passa a exigir a distinção desta ADR, que é sutil e vai precisar ser citada. Quem quiser editar `_archive/**` agora tem um precedente para apontar — o risco é ele ser esticado para além da classe recortada aqui, e a mitigação é que a única classe com gate mecânico é a de caminho: qualquer outra continua sem cobertura e sem respaldo.

Trade-off aceito: a delta-047 toca 17 diretórios em `specs/_archive/`, o maior volume de edição em registro imutável na história do repositório. É pagamento único — a partir da regra 5 nova, nenhum archive futuro gera essa dívida.

Fora do recorte, e sem cobertura: o atalho do GitHub (`(../)+issues|pull|discussions/N`) nasce errado dentro de artefato de delta e o C3 o ignora por forma (R13). É a mesma família de problema, com conta diferente, e segue como pendência roteada da delta-047 — esta ADR não o decide.

<!--
Imutável após "Accepted". Mudou a decisão? Crie uma NOVA ADR com "Supersedes ADR-0032" e marque esta como "Superseded by ADR-YYYY". Nunca reescreva uma ADR aceita. Atualize o índice docs/adrs/README.md no mesmo PR. -->
