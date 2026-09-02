#!/usr/bin/env python3
"""Gate do DT-064: a contagem/lista de skills vive em seis espelhos (2 manifestos + 4
pontos nos 2 READMEs) e o gate de 2026-07-20 cobria só os manifestos — na delta-068 os
quatro pontos do README ficaram todos defasados ao mesmo tempo (13 citado com 14 reais)
e só foi pego na revisão manual de release. `eu-tenho-tdah` é a única skill always-on,
descrita fora da tabela — nome hardcoded de propósito: é caso único documentado (R33),
não um padrão a generalizar.

O ordinal por extenso é detectado por lista estática (PT/EN, até a posição 25): número
por extenso em português não é regra simples o bastante para valer um algoritmo aqui.
# ponytail: lista fixa até a 25a posição; se a 26a skill nascer, estender as duas listas
"""

import json
import re
import sys
from pathlib import Path

SEMPRE_LIGADA = "eu-tenho-tdah"

ORDINAIS_PT = [None, "primeira", "segunda", "terceira", "quarta", "quinta", "sexta", "sétima",
               "oitava", "nona", "décima", "décima primeira", "décima segunda", "décima terceira",
               "décima quarta", "décima quinta", "décima sexta", "décima sétima", "décima oitava",
               "décima nona", "vigésima", "vigésima primeira", "vigésima segunda",
               "vigésima terceira", "vigésima quarta", "vigésima quinta"]
ORDINAIS_EN = [None, "first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth",
               "ninth", "tenth", "eleventh", "twelfth", "thirteenth", "fourteenth", "fifteenth",
               "sixteenth", "seventeenth", "eighteenth", "nineteenth", "twentieth",
               "twenty-first", "twenty-second", "twenty-third", "twenty-fourth", "twenty-fifth"]


def skills_no_disco(skills_dir: Path) -> list[str]:
    return sorted(p.name for p in skills_dir.iterdir() if (p / "SKILL.md").is_file())


def checar_manifestos(skills: list[str], plugin_desc: str, marketplace_desc: str) -> list[str]:
    """Mesma lógica do heredoc original (2026-07-20), case-insensitive."""
    achados = []
    for nome, desc in (("plugin.json", plugin_desc), ("marketplace.json", marketplace_desc)):
        for s in skills:
            if s.lower() not in desc.lower():
                achados.append(f"{nome}: não cita a skill '{s}'")
    return achados


def secao(texto: str, heading: str) -> str:
    """Trecho do markdown entre `heading` (linha '## ...' exata) e o próximo '## ' — ou fim do arquivo."""
    m = re.search(rf"^{re.escape(heading)}\s*$(.*?)(?=^## |\Z)", texto, re.M | re.S)
    return m.group(1) if m else ""


def checar_readme(skills: list[str], texto: str, *, heading: str, badge_re: re.Pattern,
                   instalacao_re: re.Pattern, ordinais: list[str]) -> list[str]:
    n = len(skills)
    achados = []
    m = badge_re.search(texto)
    if not m or int(m.group(1)) != n:
        achados.append(f"selo do topo não diz '{n} skills'")
    m = instalacao_re.search(texto)
    if not m or int(m.group(1)) != n:
        achados.append(f"texto de instalação não diz '{n} skills'")
    tabela = secao(texto, heading)
    for s in skills:
        if s == SEMPRE_LIGADA:
            continue
        if f"skills/{s}/SKILL.md".lower() not in tabela.lower():
            achados.append(f"tabela não lista a skill '{s}'")
    linha_sempre_ligada = next((l for l in tabela.splitlines() if f"{SEMPRE_LIGADA}/SKILL.md" in l), "")
    ordinal = ordinais[n] if 0 < n < len(ordinais) else None
    if not ordinal or ordinal.lower() not in linha_sempre_ligada.lower():
        achados.append(f"ordinal por extenso da posição {n} ('{ordinal}') ausente na linha da skill always-on")
    return achados


def selftest() -> int:
    assert checar_manifestos(["a", "b"], "cita A e nada mais", "cita a e B") == \
        ["plugin.json: não cita a skill 'b'"], "case-insensitive e só o que falta"
    assert checar_manifestos(["a"], "cita a", "cita a") == [], "tudo presente não acusa"

    badge = re.compile(r"·\s*(\d+)\s*skills\s*·")
    instalacao = re.compile(r"as\s+(\d+)\s+skills\s+aparecem")
    texto_ok = (
        "[v](x) · 2 skills · MIT\n\nPronto: as 2 skills aparecem com o prefixo.\n\n"
        "## 7. As skills\n\n| Skill | X |\n| --- | --- |\n| [`a`](skills/a/SKILL.md) | x |\n\n"
        "A segunda não é comando: [`eu-tenho-tdah`](skills/eu-tenho-tdah/SKILL.md) fica ligada.\n\n## 8. Outra coisa\nlixo\n"
    )
    assert checar_readme(["a", "eu-tenho-tdah"], texto_ok, heading="## 7. As skills",
                          badge_re=badge, instalacao_re=instalacao, ordinais=ORDINAIS_PT) == [], \
        "README consistente não deveria acusar nada"

    texto_ordinal_errado = texto_ok.replace("A segunda não é comando", "A terceira não é comando")
    achado = checar_readme(["a", "eu-tenho-tdah"], texto_ordinal_errado, heading="## 7. As skills",
                            badge_re=badge, instalacao_re=instalacao, ordinais=ORDINAIS_PT)
    assert any("ordinal" in a for a in achado), f"ordinal errado deveria acusar: {achado}"

    texto_sem_skill = texto_ok.replace("| [`a`](skills/a/SKILL.md) | x |\n", "")
    achado2 = checar_readme(["a", "eu-tenho-tdah"], texto_sem_skill, heading="## 7. As skills",
                             badge_re=badge, instalacao_re=instalacao, ordinais=ORDINAIS_PT)
    assert any("'a'" in a for a in achado2), f"skill ausente da tabela deveria acusar: {achado2}"

    # regressão: uma menção solta à skill always-on ANTES da seção 7 (o README real tem
    # uma na seção 6) não pode ser a linha lida — teria que buscar dentro da seção 7
    texto_com_decoy = (
        "[v](x) · 2 skills · MIT\n\n## 6. Outra seção\n"
        "Falando de [`eu-tenho-tdah`](skills/eu-tenho-tdah/SKILL.md) de passagem, sem ordinal.\n\n"
        + "Pronto: as 2 skills aparecem com o prefixo.\n\n" + texto_ok.split("Pronto:", 1)[1]
    )
    assert checar_readme(["a", "eu-tenho-tdah"], texto_com_decoy, heading="## 7. As skills",
                          badge_re=badge, instalacao_re=instalacao, ordinais=ORDINAIS_PT) == [], \
        "menção decoy antes da seção 7 não pode fazer o check ler a linha errada"
    print("inventario_skills selftest: OK (6 casos)")
    return 0


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    root = Path(__file__).resolve().parents[2]
    skills = skills_no_disco(root / "skills")
    manifesto = json.loads((root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    marketplace = json.loads((root / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
    achados = checar_manifestos(skills, manifesto["description"], marketplace["plugins"][0]["description"])

    badge_pt = re.compile(r"·\s*(\d+)\s*skills\s*·")
    instalacao_pt = re.compile(r"as\s+(\d+)\s+skills\s+aparecem")
    achados += checar_readme(skills, (root / "README.md").read_text(encoding="utf-8"),
                              heading="## 7. As skills", badge_re=badge_pt,
                              instalacao_re=instalacao_pt, ordinais=ORDINAIS_PT)

    badge_en = re.compile(r"·\s*(\d+)\s*skills\s*·")
    instalacao_en = re.compile(r"the\s+(\d+)\s+skills\s+show up")
    achados += checar_readme(skills, (root / "README.en.md").read_text(encoding="utf-8"),
                              heading="## 7. The skills", badge_re=badge_en,
                              instalacao_re=instalacao_en, ordinais=ORDINAIS_EN)

    if achados:
        print("\n".join(f"inventario_skills: {a}" for a in achados))
        return 1
    print(f"inventario_skills OK: {len(skills)} skills em paridade nos seis espelhos")
    return 0


if __name__ == "__main__":
    sys.exit(main())
