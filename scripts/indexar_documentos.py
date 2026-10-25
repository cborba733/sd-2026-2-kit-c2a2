"""Envia todos os .txt da pasta documentos/ para o servico de ingestao.

Uso: python scripts/indexar_documentos.py [url_ingestao]
"""
import glob
import os
import sys

import requests

url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8001"
docs = []
for caminho in sorted(glob.glob("documentos/*.txt")):
    with open(caminho, encoding="utf-8") as f:
        docs.append({"texto": f.read().strip(), "origem": os.path.basename(caminho)})

r = requests.post(f"{url}/indexar", json=docs, timeout=10)
print(r.status_code, r.json())
