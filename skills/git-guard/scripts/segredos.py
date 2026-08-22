#!/usr/bin/env python3
"""Casamento de padrões de segredo em texto — skill git-guard, delta-076.

Núcleo puro, sem I/O e sem dependência externa. O `audit_workspace.py` importa `casar()`
para o check G1; a delta seguinte acrescenta as portas `--staged` (hook pré-commit) e
`--diff` (CI) sem tocar neste núcleo — hook e CI têm de invocar o MESMO código, senão o
gate documentado passa a divergir do gate executado.

Alcance e limite, declarados de propósito (ADR-0039):
  - alcança credencial com forma característica (prefixo de provedor, bloco PEM);
  - alcança valor opaco longo atribuído a chave de nome sensível, inclusive em base64 —
    mas DECODIFICA antes de acusar: placeholder codificado é ilegível para quem revisa e
    para o regex, e foi o falso positivo mais caro da primeira varredura real;
  - NÃO alcança segredo sem nenhum enquadramento reconhecível. Scanner externo foi
    recusado por política de dependência; o buraco está no catálogo, não escondido.

Uso: segredos.py --selftest
Requer Python 3.11+ (mesma linha de base do restante do plugin).
"""
import base64
import re
import sys

# Sufixo de arquivo que nunca é achado: exemplo é feito para ter valor de mentira dentro.
# Sem este recorte a esmagadora maioria dos casamentos num workspace real é ruído de
# arquivo de exemplo — e auditoria ruidosa é auditoria ignorada.
SUFIXOS_IGNORADOS = (".example", ".sample", ".template", ".dist")

# Marcas de placeholder, em duas camadas — a divisão existe porque num check de segredo o
# falso NEGATIVO é o erro caro: marca curta casando por acaso dentro de uma credencial
# aleatória faz a auditoria calar sobre um segredo real.
#
# Inequívocas: longas o bastante para não ocorrerem por acaso num valor opaco. Valem sempre.
MARCAS_INEQUIVOCAS = (
    "example", "exemplo", "placeholder", "substitua", "changeme", "change-me", "replace",
    "dummy", "xxxx", "<", ">", "...", "sample", "redacted",
)
# Fracas: curtas, plausíveis por acaso em base64/hex. Só valem quando o valor tem cara de
# escrito por gente — contém separador. Blob opaco não passa por aqui.
MARCAS_FRACAS = (
    "your", "seu", "sua", "aqui", "here", "todo", "fake", "insert", "coloque", "troque",
    # verbos de instrução em PT-BR: medidos em falso positivo real ("NEXTAUTH_SECRET=GERE_
    # COM_OPENSSL..."), que é doc de deploy mandando gerar o valor, não o valor.
    "gere", "gerar", "defina", "preencha", "informe", "altere", "insira",
)
SEPARADORES_DE_VALOR_HUMANO = ("_", "-", " ")

# Valor com forma de identificador de código (snake_case sem dígito). Credencial é de alta
# entropia; isto é nome de função. Medido: `uso_tokens = _chamar_llm_com_ferramentas` casava
# o padrão genérico porque o identificador contém "token" e o valor tem 20+ caracteres.
RE_IDENTIFICADOR = re.compile(r"^[a-z_][a-z0-9_]*$")
# SCREAMING_SNAKE_CASE sem dígito: convenção universal de placeholder em doc de deploy
# ("NEXTAUTH_SECRET=SEGREDO_FORTE_STAGE", vizinho de "DATABASE_URL=...SENHA_FORTE_STAGE").
# Credencial real de 20+ caracteres praticamente sempre traz dígito ou minúscula.
RE_GRITO = re.compile(r"^[A-Z][A-Z_]*$")
# Base64 puro, para tentar decodificar antes de decidir — foi assim que um placeholder
# ("insira sua chave aqui") sobreviveu à triagem: ilegível para o humano e para o regex.
RE_BASE64 = re.compile(r"^[A-Za-z0-9+/]+={0,2}$")

# Comprimento mínimo do valor opaco para o padrão genérico. Abaixo disto é quase sempre
# nome de variável, booleano ou número de porta — ruído, não credencial.
MIN_VALOR_OPACO = 20

PADROES: list[tuple[str, re.Pattern]] = [
    ("chave-aws", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("bloco-pem-privado", re.compile(r"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----")),
    ("token-github", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36}\b")),
    ("chave-openai", re.compile(r"\bsk-[A-Za-z0-9_\-]{20,}")),
    ("token-slack", re.compile(r"\bxox[baprs]-[A-Za-z0-9\-]{10,}")),
    ("chave-google", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("token-stripe", re.compile(r"\b[sr]k_(?:live|test)_[A-Za-z0-9]{20,}\b")),
    # Genérico: chave de nome sensível recebendo valor opaco longo. É o que alcança o caso
    # do valor em base64 dentro de um manifesto, que nenhum prefixo de provedor denuncia.
    (
        "valor-opaco-em-chave-sensivel",
        re.compile(
            r"(?i)\b[A-Z0-9_\-]*(?:api[_\-]?key|secret|token|password|passwd|credential)"
            r"[A-Z0-9_\-]*\b\s*[:=]\s*[\"']?([A-Za-z0-9+/=_\-]{%d,})" % MIN_VALOR_OPACO
        ),
    ),
]


def arquivo_ignorado(nome: str) -> bool:
    """Puro: nome de arquivo que é exemplo por convenção nunca vira achado."""
    minusculo = nome.lower()
    return any(minusculo.endswith(s) or f"{s}." in minusculo for s in SUFIXOS_IGNORADOS)


def e_exemplo_documentado(valor: str, _ja_decodificado: bool = False) -> bool:
    """Puro: texto que se denuncia como material de documentação, não credencial viva.

    Aplicável a QUALQUER casamento, inclusive ao bloco PEM inteiro — só olha marcas e
    repetição, nunca forma sintática, porque forma de credencial característica é
    justamente o que estes padrões procuram.

    Assimetria deliberada — na dúvida, ACUSA. Deixar de acusar um segredo real custa
    rotação de credencial; acusar um exemplo custa uma linha de relatório.
    """
    limpo = valor.strip("\"'")
    minusculo = limpo.lower()
    if any(marca in minusculo for marca in MARCAS_INEQUIVOCAS):
        return True
    if any(sep in limpo for sep in SEPARADORES_DE_VALOR_HUMANO):
        if any(marca in minusculo for marca in MARCAS_FRACAS):
            return True
    # Placeholder escondido em base64: ilegível para o humano que revisa e para o regex.
    # Decodificar antes de decidir é o que separa "chave viva" de "insira sua chave aqui".
    if not _ja_decodificado and len(limpo) >= 8 and RE_BASE64.match(limpo):
        try:
            claro = base64.b64decode(limpo, validate=True).decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            claro = ""
        if claro and claro.isprintable() and e_exemplo_documentado(claro, _ja_decodificado=True):
            return True
    # Repetição de um ou dois caracteres ("aaaa…", "0101…") nunca é credencial real.
    return len(set(limpo)) <= 2


def e_placeholder(valor: str) -> bool:
    """Puro: filtro do VALOR capturado pelo padrão genérico.

    Acrescenta as guardas de forma de código, que só fazem sentido aqui: o padrão genérico
    casa "identificador sensível = qualquer coisa longa", e "qualquer coisa longa" pega
    nome de função e expansão de shell. Aplicar estas guardas a um casamento característico
    seria desastroso — um bloco PEM começa com `-----` e cairia na regra do `${VAR:-...}`.
    """
    limpo = valor.strip("\"'")
    # Nome de função ou variável capturado como se fosse valor — é código, não credencial.
    if RE_IDENTIFICADOR.match(limpo) or RE_GRITO.match(limpo):
        return True
    # Expansão de shell com valor default: `${VAR:-default}` faz o casamento começar em "-".
    if limpo.startswith("-"):
        return True
    return e_exemplo_documentado(valor)


def casar(texto: str) -> list[tuple[str, int]]:
    """Puro: devolve [(nome_do_padrao, numero_da_linha)] ordenado por linha.

    NUNCA devolve o trecho casado — o relatório nomeia arquivo e padrão, e o valor não
    sai daqui. É o mesmo cuidado que o W2 toma ao comparar remotes sem imprimir a URL.
    """
    achados: list[tuple[str, int]] = []
    for numero, linha in enumerate(texto.splitlines(), 1):
        for nome, padrao in PADROES:
            m = padrao.search(linha)
            if not m:
                continue
            # Grupo 1 existe só no padrão genérico. Com ele, o filtro forte (inclui forma
            # de código); sem ele, só o filtro de documentação — a chave de exemplo
            # canônica da AWS tem forma de credencial real e aparece em todo tutorial,
            # então filtrar é necessário, mas filtrar por sintaxe mataria o bloco PEM.
            if m.groups():
                descartar = e_placeholder(m.group(1))
            else:
                descartar = e_exemplo_documentado(m.group(0))
            if descartar:
                continue
            achados.append((nome, numero))
    return sorted(achados, key=lambda a: (a[1], a[0]))


def selftest() -> int:
    # Credenciais sintéticas montadas em TEMPO DE EXECUÇÃO, nunca escritas como literal.
    # Não é firula: o G1 do audit_workspace.py varre os arquivos rastreados deste próprio
    # repositório, e um fixture literal faria o scanner acusar o seu próprio selftest —
    # falso positivo que o autor do check é o primeiro a encontrar e o último a entender.
    AWS_FALSA = "AK" + "IA" + "3KJ7QWNP2LXVDR8T"
    AWS_DOC = "AK" + "IA" + "IOSFODNN7EXAMPLE"
    GH_FALSO = "gh" + "p_" + "a" * 36
    STRIPE_FALSO = "sk" + "_live_" + "b" * 24
    OPACO = "QmFzZTY0" + "T3BhY29EZVZlcmRhZGU5OTk"
    OPACO_LONGO = "Z3NrX2xpdmVf" + "YWJjZGVmZ2hpMTIzNDU2Nzg5MA=="
    COM_HERE = "ZzHeRe" + "QwErTyUiOpAsDfGhJkL123"

    # --- arquivo_ignorado ------------------------------------------------------------
    assert arquivo_ignorado(".env.example")
    assert arquivo_ignorado("config.yaml.template")
    assert arquivo_ignorado("secrets.json.dist")
    assert arquivo_ignorado("Settings.SAMPLE")           # case-insensitive
    assert arquivo_ignorado(".env.example.md")           # sufixo no meio do nome
    assert not arquivo_ignorado(".env")
    assert not arquivo_ignorado("k8s/secret.yml")
    assert not arquivo_ignorado("exemplos.py")           # "exemplo" no nome não é sufixo

    # --- e_placeholder: marcas inequívocas, valem sempre ------------------------------
    assert e_placeholder("SUBSTITUA_PELO_VALOR_REAL")
    assert e_placeholder("<coloque a chave>")
    assert e_placeholder(AWS_DOC)         # sem separador, mas "example" é inequívoca
    assert e_placeholder("xxxxxxxxxxxxxxxxxxxxxxxx")
    assert e_placeholder("aaaaaaaaaaaaaaaaaaaaaaaa")     # um caractere só
    assert e_placeholder("010101010101010101010101")     # dois caracteres

    # --- e_placeholder: marcas fracas, só em valor com cara de escrito por gente ------
    # É a defesa contra o falso NEGATIVO: "here" cai por acaso dentro de base64, e uma
    # marca curta valendo sempre faria a auditoria calar sobre um segredo real.
    assert e_placeholder("token-here")                   # tem separador → marca fraca vale
    assert e_placeholder("your_api_key")
    assert not e_placeholder(COM_HERE), \
        "blob opaco que contém 'here' por acaso não pode ser tratado como placeholder"
    assert not e_placeholder(OPACO)
    assert not e_placeholder(AWS_FALSA)

    # --- casar: prefixos de provedor -------------------------------------------------
    # A chave de exemplo canônica da AWS tem forma de credencial real e está em todo
    # tutorial — o filtro de placeholder precisa alcançá-la, senão a auditoria acusa doc.
    assert casar(f"AWS_KEY = {AWS_DOC}\n") == [], \
        "chave de exemplo documentada não pode virar achado"
    aws = casar(f"cred = {AWS_FALSA}\n")
    assert ("chave-aws", 1) in aws, aws

    pem = casar("x\n-----BEGIN RSA PRIVATE KEY-----\ny\n")
    assert pem == [("bloco-pem-privado", 2)], pem

    gh = casar(f"token: {GH_FALSO}\n")
    assert any(n == "token-github" for n, _ in gh), gh

    stripe = casar(f"k = {STRIPE_FALSO}\n")
    assert any(n == "token-stripe" for n, _ in stripe), stripe

    # --- casar: o caso que motivou o padrão genérico ---------------------------------
    # Chave em base64 dentro de um manifesto: nenhum prefixo de provedor a denuncia.
    yaml_real = (
        "apiVersion: v1\n"
        "data:\n"
        f"  GROQ_API_KEY: {OPACO_LONGO}\n"
    )
    generico = casar(yaml_real)
    assert generico == [("valor-opaco-em-chave-sensivel", 3)], generico

    # ...e o mesmo manifesto com placeholder não acusa
    yaml_placeholder = (
        "data:\n"
        "  GROQ_API_KEY: SUBSTITUA_PELO_VALOR_DA_SUA_CHAVE\n"
    )
    assert casar(yaml_placeholder) == [], casar(yaml_placeholder)

    # --- regressão: os falsos positivos medidos na primeira varredura real ------------
    # Rodar a varredura contra 30 repositórios de verdade produziu 20 achados de segredo,
    # dos quais 20 eram ruído — 5 classes distintas. Cada uma virou um caso aqui, e a
    # última asserção é a contraprova. Fixture sintética não teria
    # encontrado nenhuma delas — foi o oráculo real que mediu o check.
    assert casar("dados_llm, uso_tokens = _chamar_llm_com_ferramentas\n") == [], \
        "nome de função capturado como valor: é código, não credencial"
    assert casar("  POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-alumnus_dev_senha}\n") == [], \
        "expansão de shell com default faz o casamento começar em '-'"
    assert casar("NEXTAUTH_SECRET=GERE_COM_OPENSSL_RAND_BASE64_32\n") == [], \
        "doc de deploy mandando GERAR o valor não é o valor"
    assert casar("NEXTAUTH_SECRET=SEGREDO_FORTE_DE_STAGE\n") == [], \
        "SCREAMING_SNAKE_CASE sem dígito é convenção de placeholder, não credencial"
    assert casar("NEXTAUTH_SECRET=SEGREDO_FORTE_DE_STAGE9\n") != [], \
        "...mas um dígito já o tira da convenção: volta a ser candidato"
    escondido = base64.b64encode("insira sua chave aqui".encode()).decode()
    assert casar(f"  GROQ_API_KEY: {escondido}\n") == [], \
        "placeholder em base64 é ilegível para o humano que revisa E para o regex"

    # ...e a contraprova: chave de verdade em base64 continua sendo pega
    viva = base64.b64encode(("gs" + "k_R7QmXv92LpNd4KwEy8Ts").encode()).decode()
    assert casar(f"  GROQ_API_KEY: {viva}\n") == [("valor-opaco-em-chave-sensivel", 1)], \
        "decodificar não pode virar desculpa para deixar passar credencial real"

    # --- casar: bordas ---------------------------------------------------------------
    assert casar("") == []
    assert casar("PORT = 8080\nDEBUG = true\n") == [], "valor curto não é credencial"
    assert casar("# api_key: ver o cofre da equipe\n") == [], "prosa não é atribuição"

    multi = casar(
        f"k1 = {AWS_FALSA}\n"
        "linha limpa\n"
        f"senha_token: {OPACO}\n"
    )
    assert [n for n, _ in multi] == ["chave-aws", "valor-opaco-em-chave-sensivel"], multi
    assert [ln for _, ln in multi] == [1, 3], multi

    # --- contrato: o valor casado nunca sai ------------------------------------------
    saida = casar(f"GROQ_API_KEY: {OPACO_LONGO}\n")
    assert all(isinstance(n, str) and isinstance(ln, int) for n, ln in saida)
    assert "Z3Nr" not in str(saida), "o trecho casado nunca pode aparecer na saída"

    print("selftest: OK (segredos.py — 8 padrões, filtro de exemplo e de placeholder em "
          "duas camadas, 6 regressões de falso positivo medidas em varredura real, "
          "e o contrato de nunca devolver o trecho casado)")
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        sys.exit(selftest())
    print(__doc__.strip().splitlines()[0], file=sys.stderr)
    print("uso: segredos.py --selftest", file=sys.stderr)
    sys.exit(2)
