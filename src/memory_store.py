import faiss
import numpy as np
import os
import pickle
import logging

logger = logging.getLogger("genkube")

class MemoryStore:
    def __init__(self, dim=384):
        self.dim = dim
        self.index = faiss.IndexFlatL2(dim)
        self.texts = []

    def embed(self, text):
        if not isinstance(text, str) or not text.strip():
            logger.warning("Empty or invalid text passed to embed()")
            return np.zeros(self.dim, dtype='float32')

        vec = np.zeros(self.dim, dtype='float32')
        for i, c in enumerate(text.encode('utf-8')[:self.dim]):
            vec[i] = float(c)
        return vec

    def add(self, text):
        try:
            vec = self.embed(text)
            self.index.add(np.array([vec]))
            self.texts.append(text)
            logger.info("Memory added: %s", text[:80])
        except Exception as e:
            logger.exception("Failed to add memory")

    def search(self, query, top_k=3):
        try:
            vec = self.embed(query)
            D, I = self.index.search(np.array([vec]), top_k)
            results = [self.texts[i] for i in I[0] if i < len(self.texts)]
            logger.info("Search for '%s' returned %d results", query, len(results))
            return results
        except Exception as e:
            logger.exception("Memory search failed")
            return []

    def save(self, path):
        try:
            with open(path, "wb") as f:
                pickle.dump((self.index, self.texts), f)
            logger.info("Memory saved to %s", path)
        except Exception as e:
            logger.exception("Failed to save memory")

    def load(self, path):
        if os.path.exists(path):
            try:
                with open(path, "rb") as f:
                    self.index, self.texts = pickle.load(f)
                logger.info("Memory loaded from %s", path)
            except Exception as e:
                logger.exception("Failed to load memory from %s", path)
