from src.api import app
import uvicorn
import logging

# Setup structured logging (production-friendly)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.info(" Starting GenKube Guard...")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
