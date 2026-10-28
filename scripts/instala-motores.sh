#!/usr/bin/env bash
# Instala os motores de terceiros que o ciclo deltaspec delega.
# Degradação graciosa: falha em um motor não interrompe os demais.
set -u

MOTORES=(
  superpowers@claude-plugins-official
  ponytail@ponytail
  mattpocock-skills@claude-plugins-official
  max@max4c-skills
  diagram-design@diagram-design
)

# O diagram-design vem de marketplace próprio (ADR-0018; DT-019) — registro idempotente.
claude plugin marketplace add cathrynlavery/diagram-design >/dev/null 2>&1 || true

falhas=()
for motor in "${MOTORES[@]}"; do
  echo "==> claude plugin install ${motor}"
  claude plugin install "${motor}" || falhas+=("${motor}")
done

if ((${#falhas[@]})); then
  echo "AVISO: falha ao instalar: ${falhas[*]}" >&2
  echo "Talvez o marketplace precise ser registrado antes: claude plugin marketplace add <owner/repo>" >&2
  exit 1
fi
echo "Todos os motores instalados."
