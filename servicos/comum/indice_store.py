"""
Armazenamento do indice vetorial em arquivo JSON (TAREFA 1).

O servico de ingestao (API) le o arquivo; o worker de ingestao escreve.
A escrita e atomica (arquivo temporario + os.replace), entao quem le nunca
pega um arquivo pela metade.
"""
import json
import os

CAMINHO = os.getenv("INDICE_PATH", "dados/indice.json")


def carregar():
    """Devolve a lista de itens do indice (vazia se o arquivo nao existir)."""
    if not os.path.exists(CAMINHO):
        return []
    with open(CAMINHO, encoding="utf-8") as f:
        return json.load(f)


def salvar(itens):
    """Grava o indice inteiro de forma atomica."""
    pasta = os.path.dirname(CAMINHO)
    if pasta:
        os.makedirs(pasta, exist_ok=True)
    temporario = CAMINHO + ".tmp"
    with open(temporario, "w", encoding="utf-8") as f:
        json.dump(itens, f, ensure_ascii=False)
    os.replace(temporario, CAMINHO)
