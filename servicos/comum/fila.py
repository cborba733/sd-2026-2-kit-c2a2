"""Fila de mensagens em Redis, usada na etapa de ingestao (TAREFA 4)."""
import json
import os

import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
FILA = "fila_ingestao"
FILA_FALHAS = "fila_ingestao_falhas"      # dead-letter

_cliente = redis.Redis.from_url(REDIS_URL, decode_responses=True)


def enfileirar(docs):
    """Coloca um lote de documentos na fila (RPUSH)."""
    _cliente.rpush(FILA, json.dumps(docs, ensure_ascii=False))


def proximo_lote(timeout=5):
    """Espera ate 'timeout' segundos por um lote (BLPOP). None se nao veio nada."""
    item = _cliente.blpop(FILA, timeout=timeout)
    return json.loads(item[1]) if item else None


def descartar(docs, erro):
    """Manda um lote que falhou para a fila de falhas."""
    _cliente.rpush(FILA_FALHAS, json.dumps({"docs": docs, "erro": erro},
                                           ensure_ascii=False))


def tamanho():
    return _cliente.llen(FILA)
