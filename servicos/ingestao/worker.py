"""
Worker de INGESTAO: consome a fila, gera os embeddings e grava o indice.

Rodar: python -m servicos.ingestao.worker
"""
import time

from servicos.comum import fila, indice_store
from servicos.comum.embeddings import Vetorizador
from servicos.comum.log import logger

MAX_TENTATIVAS = 3


def processar(docs):
    """Junta os documentos novos ao indice e recalcula os vetores."""
    itens = indice_store.carregar()
    ja_indexados = {i["texto"] for i in itens}
    for d in docs:
        if d["texto"] not in ja_indexados:        # reenviar o mesmo doc nao duplica
            itens.append({"texto": d["texto"], "origem": d.get("origem", "desconhecida")})
            ja_indexados.add(d["texto"])

    vetorizador = Vetorizador()
    vetorizador.ajustar([i["texto"] for i in itens])     # vocabulario novo
    for item in itens:
        item["vetor"] = vetorizador.vetorizar(item["texto"])
    indice_store.salvar(itens)
    return len(itens)


def main():
    logger.info("worker de ingestao pronto, aguardando lotes (Ctrl+C para sair)")
    while True:
        docs = fila.proximo_lote(timeout=5)
        if docs is None:
            continue
        for tentativa in range(1, MAX_TENTATIVAS + 1):
            try:
                inicio = time.time()
                total = processar(docs)
                logger.info("worker: lote indexado quantidade=%d total_no_indice=%d tempo_ms=%.1f",
                            len(docs), total, (time.time() - inicio) * 1000)
                break
            except Exception as erro:  # noqa: BLE001
                logger.warning("worker: erro (tentativa %d/%d): %s",
                               tentativa, MAX_TENTATIVAS, erro)
                if tentativa == MAX_TENTATIVAS:
                    fila.descartar(docs, str(erro))
                    logger.error("worker: lote descartado para a fila de falhas")
                else:
                    time.sleep(1)


if __name__ == "__main__":
    main()
