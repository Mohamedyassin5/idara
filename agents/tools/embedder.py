"""
Embedder
========

Local multilingual embeddings (fastembed, ONNX on CPU, no API key). Used by every RAG knowledge base
and by the shared PgVector knowledge in db/session.py. apinex does not expose an embeddings endpoint.
"""

from agno.knowledge.embedder.fastembed import FastEmbedEmbedder

EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDING_DIMENSIONS = 384


def make_embedder() -> FastEmbedEmbedder:
    return FastEmbedEmbedder(id=EMBEDDING_MODEL, dimensions=EMBEDDING_DIMENSIONS)
