"""
Servico 1 - INGESTAO (API): recebe documentos e os coloca numa FILA.

TAREFA 1: o indice agora fica em arquivo (servicos/comum/indice_store.py).
TAREFA 4: /indexar nao indexa na hora; enfileira o lote no Redis e responde 202.
          Quem gera os embeddings e grava o indice e o worker (worker.py).

Rodar: uvicorn servicos.ingestao.app:app --port 8001
"""
import redis
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from servicos.comum import fila, indice_store
from servicos.comum.log import logger

app = FastAPI(title="Ingestao - C2.A2")


class Documento(BaseModel):
    texto: str
    origem: str = "desconhecida"


@app.post("/indexar", status_code=202)
def indexar(docs: list[Documento]):
    """Enfileira o lote e responde na hora (processamento assincrono)."""
    if not docs:
        raise HTTPException(status_code=400, detail="nenhum documento enviado")
    try:
        fila.enfileirar([d.model_dump() for d in docs])
    except redis.RedisError as erro:
        logger.warning("ingestao: fila indisponivel: %s", erro)
        raise HTTPException(status_code=503, detail="fila indisponivel")
    logger.info("ingestao: lote enfileirado quantidade=%d", len(docs))
    return {"enfileirados": len(docs)}


@app.get("/indice")
def indice():
    """Consumido pelo servico de recuperacao."""
    itens = indice_store.carregar()
    return {"total": len(itens), "itens": itens}


@app.get("/saude")
def saude():
    try:
        pendentes = fila.tamanho()
    except redis.RedisError:
        pendentes = None
    return {"status": "ok", "documentos": len(indice_store.carregar()),
            "na_fila": pendentes}
