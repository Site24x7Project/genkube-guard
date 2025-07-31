import logging
import os

logger = logging.getLogger("genkube")

QLOO_API_KEY = os.getenv("QLOO_API_KEY")
QLOO_BASE_URL = os.getenv("QLOO_BASE_URL", "https://hackathon.api.qloo.com")
QLOO_API_URL = f"{QLOO_BASE_URL}/v1/recommendations"


def get_qloo_profile(topic: str, entity_type: str = "person", mode: str = "default"):
    if not topic or not isinstance(topic, str) or not topic.strip():
        logger.warning("Invalid topic passed to Qloo profile: %s", topic)
        return {"mock": True, "topic": topic, "recommendations": []}

    topic = topic.strip().lower()

    # === TECHNICAL MODE ===
    if mode == "technical":
        logger.info("Returning mock technical recommendations for topic: %s", topic)
        return {
            "mock": True,
            "topic": topic,
            "recommendations": [
                {
                    "name": "Open Source K8s Security Toolkit",
                    "type": "tool",
                    "location": "GitHub",
                    "affinity": 0.91,
                    "affinity_reason": "Popular toolchain used by DevSecOps teams"
                },
                {
                    "name": "DevSecOps Zero Trust Bootcamp",
                    "type": "course",
                    "location": "Online",
                    "affinity": 0.88,
                    "affinity_reason": "Covers PoLP, RBAC, and Kubernetes policies"
                },
                {
                    "name": "KubeCon Security Track",
                    "type": "event",
                    "location": "San Francisco",
                    "affinity": 0.87,
                    "affinity_reason": "Premier event for Kubernetes security insights"
                }
            ]
        }

    # === CULTURE / LIFESTYLE MODE ===
    logger.info("Returning mock lifestyle/culture recommendations for topic: %s", topic)

    if "berlin" in topic:
        return {
            "mock": True,
            "topic": topic,
            "recommendations": [
                {
                    "name": "Vegan DevOps Circle",
                    "type": "event",
                    "location": "Berlin",
                    "affinity": 0.86,
                    "affinity_reason": "Combines ethical tech with CI/CD practices"
                },
                {
                    "name": "Techno GitOps Meetup",
                    "type": "event",
                    "location": "Berlin",
                    "affinity": 0.84,
                    "affinity_reason": "Berlin-style CI/CD + open-source flair"
                },
                {
                    "name": "SRE Espresso Guide",
                    "type": "tool",
                    "location": "GitHub",
                    "affinity": 0.83,
                    "affinity_reason": "Blends observability with rapid fixes (caffeine-boosted)"
                }
            ]
        }

    # DEFAULT
    return {
        "mock": True,
        "topic": topic,
        "recommendations": [
            {
                "name": "Kubernetes K-Pop Meetup",
                "type": "event",
                "location": "Seoul",
                "affinity": 0.89,
                "affinity_reason": "Example of combining pop culture and DevOps"
            },
            {
                "name": "Anime DevOps Bootcamp",
                "type": "course",
                "location": "Tokyo",
                "affinity": 0.85,
                "affinity_reason": "Teaches GitOps using anime-themed labs"
            },
            {
                "name": "Manga-themed CI/CD Plugin",
                "type": "tool",
                "location": "GitHub",
                "affinity": 0.82,
                "affinity_reason": "Fictional but illustrative DevOps plugin"
            }
        ]
    }
