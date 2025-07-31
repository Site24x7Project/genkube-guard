import strawberry
from typing import List
from strawberry.types import Info
import logging

from src.llm_handler import memory

logger = logging.getLogger("genkube")

@strawberry.type
class MemoryItem:
    prompt: str
    response: str

@strawberry.type
class AddMemoryResponse:
    status: str
    message: str

@strawberry.type
class Query:
    @strawberry.field(description="Search memory for relevant LLM prompts/responses.")
    def search_memory(self, q: str, k: int = 5) -> List[MemoryItem]:
        try:
            logger.info("GraphQL memory search called for query: %s", q)
            results = memory.search(q, k)
            parsed = []

            for i, text in enumerate(results[:k]):
                logger.debug("RAW TEXT FROM SEARCH: %s", text)

                if "\nResponse: " in text and "Prompt: " in text:
                    parts = text.split("\nResponse: ", 1)
                    prompt = parts[0].replace("Prompt: ", "").strip()
                    response = parts[1].strip()
                    logger.debug("✅ Parsed OK: %s | %s", prompt, response)
                else:
                    prompt = text[:60] + "..." if len(text) > 60 else text
                    response = text
                    logger.warning("⚠️ Fallback parser used for: %s", text)

                parsed.append(MemoryItem(prompt=prompt, response=response))

            return parsed

        except Exception as e:
            logger.exception("GraphQL memory search failed")
            return []

@strawberry.type
class Mutation:
    @strawberry.mutation(description="Clear the FAISS-backed memory store.")
    def clear_memory(self) -> str:
        try:
            memory.store.clear()
            memory.index.reset()
            memory.save("memory-data/memory.pkl")
            logger.info("GraphQL mutation: memory cleared")
            return "Memory cleared."
        except Exception as e:
            logger.exception("GraphQL clear_memory failed")
            return "Failed to clear memory."

    @strawberry.mutation(description="Add a memory text to FAISS store.")
    def add_memory(self, text: str) -> AddMemoryResponse:
        try:
            memory.add(text)
            logger.info("GraphQL mutation: memory added successfully")
            return AddMemoryResponse(status="success", message="Text added to memory.")
        except Exception as e:
            logger.exception("GraphQL add_memory failed")
            return AddMemoryResponse(status="error", message="Failed to add text to memory.")
