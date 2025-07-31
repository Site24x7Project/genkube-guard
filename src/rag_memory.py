from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import pickle
import os
import logging

logger = logging.getLogger("genkube")

MAX_MEMORY = 200

class RagMemory:
    def __init__(self, dim=384):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.index = faiss.IndexFlatL2(dim)
        self.store = []
        self.dim = dim

    def embed(self, text: str) -> np.ndarray:
        if not isinstance(text, str) or not text.strip():
            logger.warning("Invalid input passed to embed()")
            return np.zeros(self.dim, dtype='float32')
        return self.model.encode([text])[0].astype("float32")

    def add(self, text: str):
        if not isinstance(text, str) or not text.strip():
            logger.warning("Attempted to add empty or invalid text to RAG memory")
            return
        if len(self.store) >= MAX_MEMORY:
            logger.info("RAG memory exceeded limit. Rebuilding index with recent entries.")
            self.store.pop(0)
            self.index = faiss.IndexFlatL2(self.dim)
            for t in self.store:
                self.index.add(np.array([self.embed(t)]))
        self.store.append(text)
        self.index.add(np.array([self.embed(text)]))
        logger.info("Text added to RAG memory. Store size: %d", len(self.store))

        from difflib import get_close_matches

    def search(self, query: str, k: int = 3):
        if not self.store:
           logger.info("RAG memory is empty. Nothing to search.")
           return []

    # Step 1: Semantic search using FAISS
        query_vec = self.embed(query.lower())
        _, I = self.index.search(np.array([query_vec]), k * 2)

        initial_matches = [self.store[i] for i in I[0] if i < len(self.store)]

    # Step 2: Post-filter by keyword
        keywords = query.lower().split()
        filtered = []
        seen = set()

        for entry in initial_matches:
            entry_str = str(entry).strip()
            entry_lower = entry_str.lower()

            if any(keyword in entry_lower for keyword in keywords):
               if entry_str not in seen:
                  filtered.append(entry_str)
                  seen.add(entry_str)
            if len(filtered) >= k:
               break

    # Step 3: Fallback keyword match if semantic + filter failed
        if not filtered:
           logger.warning("No filtered semantic matches. Trying fallback keyword match.")
           for entry in reversed(self.store):
               entry_str = str(entry).strip()
               entry_lower = entry_str.lower()
               if any(keyword in entry_lower for keyword in keywords):
                  if entry_str not in seen:
                    filtered.append(entry_str)
                    seen.add(entry_str)
               if len(filtered) >= k:
                break

        logger.info("Final memory search results for query='%s': %d match(es)", query, len(filtered))
        return filtered




    def save(self, path="memory.pkl"):
        try:
            with open(path, "wb") as f:
                pickle.dump((self.index, self.store), f)
            logger.info("RAG memory saved to %s", path)
        except Exception as e:
            logger.exception("Failed to save RAG memory")

    def load(self, path="memory.pkl"):
        if os.path.exists(path):
            try:
                with open(path, "rb") as f:
                     self.index, self.store = pickle.load(f)  
                self.index = faiss.IndexFlatL2(self.dim)
                for text in self.store:
                    self.index.add(np.array([self.embed(text)]))

                logger.info("RAG memory rebuilt from store with %d entries", len(self.store))

            except Exception as e:
                logger.exception("Failed to load RAG memory")
