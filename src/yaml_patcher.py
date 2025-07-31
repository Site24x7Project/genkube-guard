from src import llm_handler
import logging

logger = logging.getLogger("genkube")

def generate_patch(yaml_str: str) -> str:
    """
    Delegates to the LLM handler to generate a patch for the given YAML input.
    """
    try:
        logger.info("Generating patch for YAML input")
        return llm_handler.generate_patch(yaml_str)
    except Exception as e:
        logger.exception("Failed to generate YAML patch")
        return f"# Error generating patch: {e}"
