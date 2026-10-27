import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

# palavras muito comuns do portugues: sem isso, "de", "a", "que" fazem
# perguntas sem relacao parecerem parecidas com os documentos
STOPWORDS_PT = [
    "a", "o", "as", "os", "um", "uma", "uns", "umas", "de", "do", "da", "dos", "das",
    "em", "no", "na", "nos", "nas", "por", "para", "com", "sem", "sobre", "ao", "aos",
    "e", "ou", "mas", "que", "se", "como", "qual", "quais", "quando", "onde", "quem",
    "ser", "sao", "foi", "era", "ha", "isso", "isto", "esse", "essa", "este",
    "esta", "seu", "sua", "seus", "suas", "mais", "muito", "ja", "tambem", "pelo", "pela",
    "ele", "ela", "eles", "elas", "nao", "sim", "entre", "ate", "so", "apenas", "pode",
    "podem", "uso", "faz", "fazer", "diz", "funciona",
]


class Vetorizador:

    def __init__(self):
        self._tfidf = TfidfVectorizer(ngram_range=(1, 2), min_df=1,
                                      stop_words=STOPWORDS_PT)
        self._ajustado = False

    def ajustar(self, textos):
        self._tfidf.fit(textos)
        self._ajustado = True

    def vetorizar(self, texto):
        if not self._ajustado:
            raise RuntimeError("chame ajustar() antes de vetorizar()")
        return self._tfidf.transform([texto]).toarray()[0].tolist()


def similaridade(a, b):
    va, vb = np.array(a), np.array(b)
    na, nb = np.linalg.norm(va), np.linalg.norm(vb)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(va, vb) / (na * nb))
