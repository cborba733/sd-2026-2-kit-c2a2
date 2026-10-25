"""
Servico 3 - GERACAO: monta o prompt com o contexto e chama o LLM.

TAREFA 3: a chamada ao LLM tem TEMPO-LIMITE (LLM_TIMEOUT em llm.py), RETENTATIVA
com espera crescente e CIRCUIT BREAKER por fora de tudo.

Rodar: uvicorn servicos.geracao.app:app --port 8003
"""
import os
import time

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from servicos.comum.circuit_breaker import CircuitBreaker, CircuitoAberto
from servicos.comum.llm import gerar
from servicos.comum.log import logger

app = FastAPI(title="Geracao - C2.A2")
URL_RECUPERACAO = os.getenv("URL_RECUPERACAO", "http://localhost:8002")

TENTATIVAS = int(os.getenv("LLM_TENTATIVAS", "3"))
ESPERA_BASE = float(os.getenv("LLM_ESPERA_BASE", "0.5"))     # 0.5s, 1s, 2s...

disjuntor = CircuitBreaker(limite_falhas=3, espera_segundos=20)


class Pergunta(BaseModel):
    pergunta: str


def gerar_com_retentativa(pergunta, contexto):
    """Tenta o LLM ate TENTATIVAS vezes, esperando mais a cada falha."""
    for tentativa in range(1, TENTATIVAS + 1):
        try:
            return gerar(pergunta, contexto)
        except Exception as erro:  # noqa: BLE001
            logger.warning("geracao: LLM falhou (tentativa %d/%d): %s",
                           tentativa, TENTATIVAS, erro)
            if tentativa == TENTATIVAS:
                raise
            time.sleep(ESPERA_BASE * 2 ** (tentativa - 1))


@app.post("/perguntar")
def perguntar(p: Pergunta):
    if not p.pergunta.strip():
        raise HTTPException(status_code=400, detail="pergunta vazia")
    inicio = time.time()

    # 1) recuperacao (REST). Se cair, o sistema responde 503 em vez de quebrar.
    try:
        r = requests.post(f"{URL_RECUPERACAO}/buscar",
                          json={"pergunta": p.pergunta, "top_k": 3}, timeout=10)
        r.raise_for_status()
    except requests.RequestException as erro:
        logger.warning("geracao: recuperacao indisponivel: %s", erro)
        raise HTTPException(status_code=503, detail="servico de recuperacao indisponivel")
    resultados = r.json()["resultados"]

    if not resultados:
        return {"pergunta": p.pergunta, "contexto": [], "fontes": [],
                "resposta": "Nao encontrei essa informacao nos documentos indexados."}
    contexto = [t["texto"] for t in resultados]
    fontes = [{"origem": t["origem"], "score": t["score"]} for t in resultados]

    # 2) LLM protegido: disjuntor por fora, retentativa + timeout por dentro
    try:
        resposta = disjuntor.chamar(gerar_com_retentativa, p.pergunta, contexto)
    except CircuitoAberto:
        logger.warning("geracao: disjuntor ABERTO, chamada recusada")
        raise HTTPException(status_code=503, detail={
            "erro": "LLM temporariamente indisponivel (disjuntor aberto)",
            "contexto": contexto})
    except Exception as erro:  # noqa: BLE001
        raise HTTPException(status_code=502, detail={
            "erro": f"falha ao chamar o LLM: {erro}", "contexto": contexto})

    logger.info("geracao: pergunta respondida trechos=%d tempo_ms=%.1f",
                len(contexto), (time.time() - inicio) * 1000)
    return {"pergunta": p.pergunta, "resposta": resposta,
            "contexto": contexto, "fontes": fontes}


@app.get("/saude")
def saude():
    return {"status": "ok", "disjuntor": disjuntor.estado}
