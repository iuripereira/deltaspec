#!/usr/bin/env python3
"""A nota do dia no vault: nome, composição e o que do usuário sobrevive à regravação.

REGRAS — este texto é o dono; a SKILL.md aponta para cá e não as reescreve.

A nota é **regravada inteira** a cada execução, e por isso o que o usuário escreveu nela
precisa de um limite explícito. O bloco gerado vive entre marcadores; **tudo que estiver
fora deles volta verbatim**, sem o script interpretar uma vírgula. Quem interpreta é o
agente, depois, num bloco próprio — e é por isso que a ordem entre os dois deixa de
importar: mesmo que o agente nunca rode, nada do usuário se perde.

Texto solto que não pertence a nenhuma seção conhecida é **adotado** como anotação. Perder
texto é o único erro que esta camada não pode cometer; duplicar uma linha é reparável.

Nome do arquivo: `AAAA-MM-DD_<projeto>-<prioridade>.md`, com a prioridade derivada do
próximo passo — legível de fora, sem abrir.

**Gravação:** cópia da versão anterior para o diretório de estado ANTES de qualquer escrita,
depois temporário no mesmo diretório e substituição atômica. Falha no meio deixa a nota do
dia anterior íntegra, e a cópia é a única rede quando o vault não é versionado.

**Rename:** a prioridade muda ao longo do dia, e com ela o nome do arquivo. Renomear por
fora do editor de notas **não atualiza wikilink**, então o rename só acontece quando nenhuma
outra nota referencia o nome atual; havendo referência, o nome fica e o motivo volta ao
chamador, que o diz na saída.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

INICIO, FIM = "<!-- sessao:inicio -->", "<!-- sessao:fim -->"
H_ANOTACOES, H_RASTRO = "## Minhas anotações", "## Sua nota, processada"
LIMITE_SLUG = 60
CONVECTIVOS = ("de", "da", "do", "das", "dos", "e", "a", "o", "em", "no", "na", "para", "por", "com")
DICA = ("<!-- Escreva aqui o que quiser: esta seção volta intacta na próxima execução, e o agente\n"
        "     a converte em débito, pendência ou contexto, deixando o rastro na seção abaixo. -->")


def slug(texto, limite=LIMITE_SLUG):
    """Próximo passo → nome de arquivo: sem acento, minúsculo, cortado no primeiro travessão."""
    texto = (texto or "").split(" — ")[0].strip()
    plano = "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))
    plano = re.sub(r"[^a-zA-Z0-9]+", "-", plano).strip("-").lower()
    if len(plano) > limite:
        plano = plano[:limite].rsplit("-", 1)[0]
    partes = plano.split("-")
    while len(partes) > 1 and partes[-1] in CONVECTIVOS:
        partes.pop()
    return "-".join(p for p in partes if p)


def prioridade_de(item, tarefa=""):
    """O que vira o fim do nome do arquivo: a AÇÃO do próximo passo, não o rótulo dela.

    A tarefa chega como `T12 (dep: T10) — ação · arquivos: …`; sem tirar o prefixo, todo
    arquivo se chamaria `t12-dep-t10` e o nome não diria nada de fora.
    """
    if tarefa:
        corpo = tarefa.split(" — ", 1)[-1].split(" · ", 1)[0]
        if slug(corpo):
            return slug(corpo)
    item = item or {}
    return slug(str(item.get("titulo") or "") ) or slug(str(item.get("id") or "").replace("/", "-"))


def nome_da_nota(data, projeto, prioridade):
    fim = f"-{prioridade}" if prioridade else ""
    return f"{data.isoformat()}_{projeto}{fim}.md"


def extrair_anotacoes(texto):
    """O que é do usuário, verbatim: fora dos marcadores, fora do rastro, fora do frontmatter.

    "Fora dos marcadores" é dos DOIS lados — o que estiver acima do marcador de abertura conta
    tanto quanto o que estiver abaixo do de fechamento. Os marcadores são comentários HTML,
    invisíveis no editor de notas: apagar um sem perceber é fácil, e a única resposta aceitável
    a um marcador faltando é preservar mais, nunca menos.

    Nota sem marcador nenhum (escrita à mão, ou de uma versão anterior do formato) tem TODO
    o corpo tratado como do usuário — na dúvida, preserva.
    """
    texto = texto or ""
    if not texto.strip():
        return ""
    corpo = re.sub(r"\A---\n.*?\n---\n", "", texto, count=1, flags=re.S)
    if INICIO not in corpo and FIM not in corpo:
        partes = [corpo]                                   # sem marcador: tudo é do usuário
    else:
        antes = corpo.split(INICIO, 1)[0] if INICIO in corpo else ""
        if FIM in corpo:
            depois = corpo.split(FIM, 1)[1]
        elif H_ANOTACOES in corpo:
            # o marcador de fechamento sumiu; o heading da seção do usuário ainda ancora
            depois = H_ANOTACOES + corpo.split(H_ANOTACOES, 1)[1]
        else:
            depois = ""
        partes = [antes, depois]
    corpo = "\n".join(p.split(H_RASTRO, 1)[0] for p in partes)
    corpo = corpo.replace(H_ANOTACOES, "").replace(DICA, "")
    return re.sub(r"\n{3,}", "\n\n", corpo).strip()


def extrair_rastro(texto):
    """O bloco que o agente preenche. Volta intacto: o script não o reescreve nem o apaga."""
    partes = (texto or "").split(H_RASTRO, 1)
    return partes[1].strip() if len(partes) == 2 else ""


def render_nota(data, projeto, painel, anotacoes="", rastro="", segundos=None, versao="", svg=""):
    """A nota inteira. O bloco gerado é substituível; o resto é do usuário."""
    partes = [f"---\ncreated: {data.isoformat()}\ntags: [tipo/sessao, projeto/{projeto}]\n---", "",
              INICIO, painel.strip()]
    if svg:
        partes += ["", f"![[{svg}]]"]
    rodape = []
    if segundos is not None:
        rodape.append(f"gerado em {segundos:.1f}s")
    if versao:
        rodape.append(versao)
    if rodape:
        partes += ["", f"*{' · '.join(rodape)}*"]
    partes += [FIM, "", H_ANOTACOES, anotacoes.strip() or DICA, "", H_RASTRO, rastro.strip()]
    return "\n".join(partes).rstrip() + "\n"


# ---------- I/O ----------

def pasta_das_notas(cfg):
    return cfg["nota"]["vault"] / cfg["nota"]["pasta"]


def nota_do_dia(cfg, data, projeto):
    """Nota já existente deste dia e projeto, qualquer que seja a prioridade no nome."""
    pasta = pasta_das_notas(cfg)
    achadas = sorted(pasta.glob(f"{data.isoformat()}_{projeto}*.md")) if pasta.is_dir() else []
    return achadas[0] if achadas else None


def tem_backlink(vault, nome):
    """Alguma nota do vault referencia este nome? Busca textual, que é como o link existe."""
    alvo = f"[[{nome}"
    for arquivo in vault.rglob("*.md") if vault.is_dir() else []:
        if arquivo.stem == nome:
            continue
        try:
            if alvo in arquivo.read_text(encoding="utf-8", errors="ignore"):
                return True
        except OSError:
            continue
    return False


def gerar_svg(base, fonte_d2):
    """(nome do arquivo gerado, erro). Sem o renderizador, ou com ele falhando, devolve erro:
    desenho nunca derruba a sessão, e o diagrama embutido continua na nota de qualquer jeito."""
    binario = shutil.which("d2")
    if not binario:
        return "", "renderizador externo (d2) não está no PATH"
    fonte = base.with_suffix(".d2")
    svg = base.with_suffix(".svg")
    try:
        fonte.write_text(fonte_d2, encoding="utf-8")
        r = subprocess.run([binario, "--layout", "elk", str(fonte), str(svg)],
                           capture_output=True, text=True)
    except OSError as e:
        return "", f"renderizador externo não pôde ser executado: {e.strerror}"
    if r.returncode or not svg.is_file():
        bruto = (r.stderr or r.stdout).strip().splitlines()
        return "", f"renderizador externo falhou: {bruto[-1] if bruto else 'sem mensagem'}"
    return svg.name, ""


def gravar_nota(cfg, data, projeto, prioridade, painel, segundos=None, dir_estado=None, fonte_d2=""):
    """(caminho gravado, motivo). Motivo preenchido = algo foi decidido e precisa ser dito.

    Ordem obrigatória: ler o que existe → copiar para fora → escrever atômico → renomear.
    """
    pasta = pasta_das_notas(cfg)
    pasta.mkdir(parents=True, exist_ok=True)
    atual = nota_do_dia(cfg, data, projeto)
    anterior = ler_nota(atual)
    alvo = pasta / nome_da_nota(data, projeto, prioridade)
    motivo = ""

    if anterior and dir_estado:
        dir_estado.mkdir(parents=True, exist_ok=True)
        shutil.copy2(atual, dir_estado / "nota-anterior.md")

    if atual and atual != alvo:
        if tem_backlink(cfg["nota"]["vault"], atual.stem):
            alvo, motivo = atual, (f"nome mantido: outra nota do vault referencia "
                                   f"[[{atual.stem}]], e renomear por fora quebraria o link")
        else:
            os.replace(atual, alvo)

    svg = ""
    if fonte_d2:
        svg, erro_svg = gerar_svg(alvo.with_suffix(""), fonte_d2)
        if erro_svg:
            motivo = (motivo + " · " if motivo else "") + f"diagrama só no formato embutido: {erro_svg}"

    conteudo = render_nota(data, projeto, painel, anotacoes=extrair_anotacoes(anterior),
                           rastro=extrair_rastro(anterior), segundos=segundos, svg=svg)
    temporario = alvo.with_suffix(".md.tmp")
    temporario.write_text(conteudo, encoding="utf-8")
    os.replace(temporario, alvo)
    return alvo, motivo


def ler_nota(caminho):
    try:
        return caminho.read_text(encoding="utf-8") if caminho and caminho.is_file() else ""
    except OSError:
        return ""


# ---------- selftest ----------

def selftest():
    import datetime as dt

    # slug: sem acento, corta no travessão, cabe no limite, não termina em conectivo
    assert slug("Arquivar a delta-042 — consolidar no TRUTH") == "arquivar-a-delta-042"
    assert slug("Ação com acento, vírgula e  espaço duplo") == "acao-com-acento-virgula-e-espaco-duplo"
    s = slug("palavra " * 30)
    assert len(s) <= LIMITE_SLUG and not s.endswith("-")
    assert not slug("camada formula no core de").endswith("-de")  # conectivo pendurado sai
    assert slug("") == "" and slug(None) == ""
    assert nome_da_nota(dt.date(2026, 9, 17), "projeto-x", "arquivar-a-delta-042") \
        == "2026-09-17_projeto-x-arquivar-a-delta-042.md"
    assert nome_da_nota(dt.date(2026, 9, 17), "projeto-x", "") == "2026-09-17_projeto-x.md"

    # a prioridade é a ação, não o rótulo da tarefa
    assert prioridade_de({}, "T20 (dep: T12) — camada oferta no core · arquivos: a.ts") == "camada-oferta-no-core"
    assert prioridade_de({"titulo": "delta-004 — paridade-planilha"}, "") == "delta-004"
    assert prioridade_de({"id": "APP/004"}, "") == "app-004"  # sem título, o id serve
    assert prioridade_de({}, "") == "" and prioridade_de(None, None) == ""

    # a nota inteira, e a volta: o que é do usuário sobrevive verbatim
    nota = render_nota(dt.date(2026, 9, 17), "projeto-x", "# Painel\n## Estado agora\ntabela",
                       anotacoes="- decidi X\n- cobrar a planilha", segundos=18.5, versao="v1.0")
    assert nota.startswith("---\ncreated: 2026-09-17\ntags: [tipo/sessao, projeto/projeto-x]\n---")
    assert INICIO in nota and FIM in nota and "*gerado em 18.5s · v1.0*" in nota
    assert extrair_anotacoes(nota) == "- decidi X\n- cobrar a planilha"

    # painel novo, anotação velha: o ciclo completo não perde nada
    nova = render_nota(dt.date(2026, 9, 18), "projeto-x", "# Painel de outro dia",
                       anotacoes=extrair_anotacoes(nota))
    assert "- decidi X" in nova and "Painel de outro dia" in nova and "tabela" not in nova

    # o rastro do agente não volta como anotação — senão ele se acumularia sozinho
    com_rastro = render_nota(dt.date(2026, 9, 17), "projeto-x", "# Painel", anotacoes="- minha nota",
                             rastro='- "minha nota" → DT-161')
    assert extrair_anotacoes(com_rastro) == "- minha nota"

    # texto ACIMA do marcador de abertura é do usuário tanto quanto o de baixo
    acima = render_nota(dt.date(2026, 9, 17), "projeto-x", "# Painel", anotacoes="- de baixo")
    acima = acima.replace(INICIO, "- escrevi aqui em cima\n\n" + INICIO)
    # verbatim inclui o espaçamento: só três quebras ou mais viram duas
    assert extrair_anotacoes(acima) == "- escrevi aqui em cima\n\n- de baixo"

    # marcador de fechamento apagado sem querer: o heading da seção ainda salva as anotações
    sem_fim = render_nota(dt.date(2026, 9, 17), "projeto-x", "# Painel", anotacoes="- não posso sumir")
    sem_fim = sem_fim.replace(FIM + "\n", "")
    assert extrair_anotacoes(sem_fim) == "- não posso sumir"

    # os dois marcadores apagados: cai no caso sem marcador e preserva tudo
    sem_nada = sem_fim.replace(INICIO + "\n", "")
    assert "- não posso sumir" in extrair_anotacoes(sem_nada)

    # nota sem marcador (escrita à mão, ou formato anterior): na dúvida, preserva tudo
    assert extrair_anotacoes("---\ncreated: x\n---\n\ntexto sem marcador nenhum") == "texto sem marcador nenhum"
    assert extrair_anotacoes("## Estado agora\nx\n\ntexto solto no fim") == "## Estado agora\nx\n\ntexto solto no fim"
    assert extrair_anotacoes("") == "" and extrair_anotacoes(None) == ""

    # primeira nota do projeto: a seção nasce com a dica, e a dica não volta como anotação
    primeira = render_nota(dt.date(2026, 9, 17), "projeto-x", "# Painel")
    assert DICA in primeira and extrair_anotacoes(primeira) == ""

    # o rastro do agente sobrevive à regravação: o script não o reescreve nem o apaga
    assert extrair_rastro(com_rastro) == '- "minha nota" → DT-161'
    assert extrair_rastro("sem bloco nenhum") == "" and extrair_rastro("") == ""

    selftest_gravacao()
    print("selftest ok")


def selftest_gravacao():
    """Grava de verdade, num vault descartável — o real nunca é tocado por teste."""
    import datetime as dt
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp) / "vault"
        estado = Path(tmp) / "estado"
        cfg = {"nota": {"vault": vault, "pasta": "40-periodico/sessoes"}}
        hoje = dt.date(2026, 9, 17)

        # 1. primeira gravação: nasce a pasta e o arquivo com a prioridade no nome
        caminho, motivo = gravar_nota(cfg, hoje, "projeto-x", "arquivar-a-delta", "# Painel 1",
                                      segundos=1.0, dir_estado=estado)
        assert caminho.name == "2026-09-17_projeto-x-arquivar-a-delta.md" and motivo == ""
        assert "# Painel 1" in caminho.read_text(encoding="utf-8")
        assert not list(caminho.parent.glob("*.tmp"))  # nada de lixo atômico

        # 2. o usuário escreve na nota; a regravação com prioridade nova renomeia e preserva
        texto = caminho.read_text(encoding="utf-8").replace(DICA, "- decidi X\n- cobrar planilha")
        caminho.write_text(texto, encoding="utf-8")
        novo, motivo = gravar_nota(cfg, hoje, "projeto-x", "camada-formula", "# Painel 2",
                                   dir_estado=estado)
        assert novo.name == "2026-09-17_projeto-x-camada-formula.md" and motivo == ""
        assert not caminho.exists(), "o arquivo antigo do mesmo dia não pode sobreviver ao rename"
        conteudo = novo.read_text(encoding="utf-8")
        assert "- decidi X" in conteudo and "- cobrar planilha" in conteudo  # anotação preservada
        assert "# Painel 2" in conteudo and "# Painel 1" not in conteudo     # painel substituído
        assert "- decidi X" in (estado / "nota-anterior.md").read_text(encoding="utf-8")  # rede

        # 3. com backlink, o nome fica e o motivo é dito
        (vault / "outra.md").write_text("ver [[2026-09-17_projeto-x-camada-formula]]", encoding="utf-8")
        terceiro, motivo = gravar_nota(cfg, hoje, "projeto-x", "terceira-prioridade", "# Painel 3",
                                       dir_estado=estado)
        assert terceiro == novo and "referencia" in motivo and "quebraria o link" in motivo
        assert "# Painel 3" in terceiro.read_text(encoding="utf-8")  # o conteúdo atualiza mesmo assim
        assert len(list(novo.parent.glob("*.md"))) == 1  # um arquivo por dia e projeto, sempre

        # 4. grafo grande: o arquivo externo nasce ao lado e a nota o referencia
        quarto, motivo = gravar_nota(cfg, dt.date(2026, 9, 18), "projeto-x", "grafo-grande", "# Painel 4",
                                     fonte_d2="a -> b\n", dir_estado=estado)
        conteudo = quarto.read_text(encoding="utf-8")
        if shutil.which("d2"):
            assert "![[2026-09-18_projeto-x-grafo-grande.svg]]" in conteudo and motivo == ""
            assert quarto.with_suffix(".svg").is_file() and quarto.with_suffix(".d2").is_file()
        else:  # sem o binário, o embutido serve e a nota diz por quê
            assert "![[" not in conteudo and "formato embutido" in motivo


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true", help="valida as funções puras deste módulo")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
