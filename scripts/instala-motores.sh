#!/usr/bin/env bash
# Instala os motores de terceiros que o ciclo deltaspec delega.
# Degradação graciosa: falha em um motor não interrompe os demais.
set -u

MOTORES=(
  superpowers@claude-plugins-official
  ponytail@ponytail
  max@max4c-skills
)

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
