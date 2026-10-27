#!/bin/bash
# Testa o fluxo completo: pergunta -> recuperacao -> geracao -> resposta.
# Uso: bash scripts/testar_fluxo.sh [url_geracao]
URL=${1:-http://localhost:8003}

perguntar() {
  curl -s -w "\n[HTTP %{http_code}]\n" -X POST "$URL/perguntar" \
    -H 'content-type: application/json' -d "{\"pergunta\":\"$1\"}"
}

echo "1) Pergunta dentro dos documentos:"
perguntar "O que diz o teorema CAP?" | cut -c1-250
echo
echo "2) Pergunta fora dos documentos (deve dizer que nao encontrou):"
perguntar "Qual a receita de bolo de cenoura?" | cut -c1-250
echo
echo "3) Pergunta vazia (deve dar 400):"
perguntar "   " | cut -c1-250
