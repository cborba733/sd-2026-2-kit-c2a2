"""
Servico 2 - RECUPERACAO: dada uma pergunta, acha os trechos mais relevantes.

TAREFA 2: busca por similaridade (cosseno) sobre o indice do servico de ingestao.

Rodar: uvicorn servicos.recuperacao.app:app --port 8002
"""
import os
import time

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from servicos.comum.embeddings import Vetorizador, similaridade
from servicos.comum.log import logger

app = FastAPI(title="Recuperacao - C2.A2")
URL_INGESTAO = os.getenv("URL_INGESTAO", "http://localhost:8001")


class Consulta(BaseModel):
    pergunta: str
    top_k: int = 3


@app.post("/buscar")
def buscar(consulta: Consulta):
    """Devolve os top_k trechos mais parecidos com a pergunta."""
    inicio = time.time()
    try:
        r = requests.get(f"{URL_INGESTAO}/indice", timeout=10)
        r.raise_for_status()
    except requests.RequestException as erro:
        logger.warning("recuperacao: ingestao indisponivel: %s", erro)
        raise HTTPException(status_code=503, detail="servico de ingestao indisponivel")
    itens = r.json()["itens"]
    if not itens:
        return {"resultados": []}

    # o indice foi vetorizado com um TF-IDF ajustado nos textos dos itens;
    # ajustando de novo nos mesmos textos (mesma ordem) o vocabulario e identico
    vetorizador = Vetorizador()
    vetorizador.ajustar([i["texto"] for i in itens])
    vetor_pergunta = vetorizador.vetorizar(consulta.pergunta)

    pontuados = []
    for item in itens:
        nota = similaridade(vetor_pergunta, item["vetor"])
        if nota > 0:                                   # ignora o que nao tem nada a ver
            pontuados.append({"texto": item["texto"], "origem": item["origem"],
                              "score": round(nota, 4)})
    pontuados.sort(key=lambda x: x["score"], reverse=True)
    resultados = pontuados[:consulta.top_k]

    logger.info("recuperacao: tamanho_pergunta=%d candidatos=%d devolvidos=%d tempo_ms=%.1f",
                len(consulta.pergunta), len(itens), len(resultados),
                (time.time() - inicio) * 1000)
    return {"resultados": resultados}


@app.get("/saude")
def saude():
    return {"status": "ok"}
