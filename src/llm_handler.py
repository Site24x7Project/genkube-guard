import ollama
import os
import yaml
import logging
from pathlib import Path
from src.rag_memory import RagMemory
from concurrent.futures import ThreadPoolExecutor, TimeoutError as LLMTimeout
import re

logger = logging.getLogger(__name__)

memory = RagMemory()
memory.load("memory-data/memory.pkl")
executor = ThreadPoolExecutor(max_workers=4)
#LLM_TIMEOUT_SECONDS = 60


def is_valid_response(text: str) -> bool:
    if not text.strip():
        return False
    if "LLM error" in text or "Error from LLM" in text:
        return False
    if "no improvements needed" in text.lower():
        return False
    if not any(kw in text.lower() for kw in ["recommend", "suggest", "securitycontext", "resources", "containers"]):
        return False

    return True

def preprocess_persona(persona: str) -> dict:
    """Extract tone and region hints from persona text"""
    persona = persona.lower()

    return {
        "tone": "playful" if any(x in persona for x in ["marvel", "k-pop", "anime", "junior", "vegan", "coffee"]) else "professional",
        "region": "berlin" if "berlin" in persona else "latam" if "latin" in persona or "brazil" in persona or "samba" in persona else "global"
    }


def is_valid_yaml_response(text: str) -> bool:
    try:
        clean_text = re.sub(r"^```(yaml)?", "", text.strip(), flags=re.IGNORECASE).strip()
        clean_text = re.sub(r"```$", "", clean_text.strip(), flags=re.IGNORECASE).strip()
        parsed = list(yaml.safe_load_all(clean_text))
        return bool(parsed)
    except Exception:
        return False



def run_llm_with_timeout(model, messages):
    try:
        response = ollama.chat(model=model, messages=messages)

        return response["message"]["content"]
    except LLMTimeout:
        logger.warning("LLM timed out after %s seconds", LLM_TIMEOUT_SECONDS)
        return "LLM error: Timed out."
    except Exception as e:
        logger.exception("LLM call failed.")
        return f"LLM error: {e}"


def load_prompt_template():
    with open("src/prompts/explain.txt", "r", encoding="utf-8") as f:
        return f.read()

PROMPT_TEMPLATE = load_prompt_template()


def explain(issue: str) -> str:
    prompt = PROMPT_TEMPLATE.replace("{{issue}}", issue.strip())
    try:
        #  Early handling for known kube-linter issues if LLM fails
        if "mismatching-selector" in issue.lower():
            return (
                "**Issue**: Missing or incorrect `selector` field in Deployment or StatefulSet.\n"
                "**Why it’s a problem**: Without a matching selector, your workload won’t know which pods to manage. This can result in zero pods being created or managed inconsistently.\n"
                "**How to fix it**: Add a `spec.selector` block that matches the pod template labels. Example:\n\n"
                "```yaml\n"
                "spec:\n"
                "  selector:\n"
                "    matchLabels:\n"
                "      app: my-app\n"
                "  template:\n"
                "    metadata:\n"
                "      labels:\n"
                "        app: my-app\n"
                "```"
            )

        if "no-anti-affinity" in issue.lower():
            return (
                "**Issue**: Missing `podAntiAffinity` configuration for high-availability replicas.\n"
                "**Why it’s a problem**: Without anti-affinity, multiple replicas might be scheduled on the same node. This increases the risk of single-node failure.\n"
                "**How to fix it**: Add anti-affinity rules like:\n\n"
                "```yaml\n"
                "spec:\n"
                "  affinity:\n"
                "    podAntiAffinity:\n"
                "      requiredDuringSchedulingIgnoredDuringExecution:\n"
                "      - labelSelector:\n"
                "          matchExpressions:\n"
                "          - key: app\n"
                "            operator: In\n"
                "            values:\n"
                "            - my-app\n"
                "        topologyKey: kubernetes.io/hostname\n"
                "```"
            )

        messages = [
            {
                "role": "system",
                "content": "You are a Kubernetes security expert. You respond with structured markdown advice."
            },
            {
                "role": "user",
                "content": prompt.strip()
            }
        ]

        content = run_llm_with_timeout("mistral", messages)

        if is_valid_response(content):
            memory.add(f"Prompt: {prompt}\nResponse: {content}")
            memory.save("memory-data/memory.pkl")
            return content
        else:
            logger.warning("Invalid or empty LLM response. Falling back to markdown template.")
            return (
                f"**Issue**: {issue.strip()}\n"
                "**Why it’s a problem**: See Kubernetes best practices\n"
                "**How to fix it**: Refer to the remediation hint from kube-linter or Kubernetes docs.\n"
            )

    except Exception as e:
        logger.exception("LLM explain() failed")
        return (
            f"**Issue**: {issue.strip()}\n"
            "**Why it’s a problem**: Explanation service failed\n"
            "**How to fix it**: Try again later or use kube-linter’s remediation field.\n"
        )


from yaml.parser import ParserError
from yaml.scanner import ScannerError

def generate_patch(yaml_text: str) -> str:
    try:
        docs = list(yaml.safe_load_all(yaml_text))
    except (ParserError, ScannerError, yaml.YAMLError):
        return "# Skipped: Invalid or unparseable YAML content."

    patched_docs = []

    for doc in docs:
        kind = doc.get("kind", "")
        if kind not in ["Deployment", "StatefulSet"]:
            # Leave non-patchable resources untouched
            patched_docs.append(doc)
            continue

        # Safely navigate to containers path
        spec = doc.setdefault("spec", {})
        template = spec.setdefault("template", {})
        pod_spec = template.setdefault("spec", {})

        containers = pod_spec.get("containers")

        if not isinstance(containers, list):
            # If malformed (e.g., string or dict), skip
            logger.warning("Skipping patch for resource with malformed containers: %s", doc.get("metadata", {}).get("name", "Unnamed"))
            patched_docs.append(doc)
            continue

        if len(containers) == 0:
           logger.warning("Skipping patch for resource with empty containers: %s", doc.get("metadata", {}).get("name", "Unnamed"))
           patched_docs.append(doc)
           continue

        else:
            for container in containers:
                if "securityContext" not in container:
                    container["securityContext"] = {
                        "runAsNonRoot": True,
                        "runAsUser": 1000,
                        "readOnlyRootFilesystem": True
                    }
                if "resources" not in container:
                    container["resources"] = {
                        "limits": {
                            "cpu": "250m",
                            "memory": "512Mi"
                        },
                        "requests": {
                            "cpu": "125m",
                            "memory": "256Mi"
                        }
                    }

        patched_docs.append(doc)

    return yaml.dump_all(patched_docs, sort_keys=False)




def suggest(yaml_str: str) -> str:
    try:
        prompt_path = os.path.join(os.path.dirname(__file__), "prompts", "suggest.txt")
        with open(prompt_path, "r") as f:
            prompt_template = f.read()

        # Build full prompt
        prompt = f"{prompt_template}\n\nYAML:\n{yaml_str.strip()}"

        messages = [
            {"role": "system", "content": "You are a helpful Kubernetes DevSecOps expert."},
            {"role": "user", "content": prompt}
        ]

        # Call Mistral via Ollama
        content = run_llm_with_timeout("mistral", messages)

        # Validate output
        if "no improvements needed" in content.lower():
            return "No improvements needed — this YAML is already valid and secure for its purpose."

        if is_valid_response(content):
            memory.add(f"Prompt: {prompt}\nResponse: {content}")
            memory.save("memory-data/memory.pkl")
            return content
        else:
            logger.warning("LLM suggestion response invalid. Using fallback.")
            return "Suggestion not available right now. Try again later or check YAML structure."

    except Exception as e:
        logger.exception("LLM suggest() failed")
        return "Suggestion service failed. Please try again later."

def load_prompt(filename):
    return Path(f"src/prompts/{filename}").read_text()


from datetime import datetime

def is_valid_persona_response(response: str) -> bool:
    """
    Allows more flexibility than is_valid_response() for persona use cases.
    Checks for at least one config keyword or suggestion tone.
    """
    if not response:
        return False
    keywords = [
        "resources:", "securityContext", "readinessProbe", "pinned image",
        "Here's what you can improve", "labels:", "annotations:", "volumeMounts",
        "runAsNonRoot", "cpu:", "memory:"
    ]
    return any(kw in response for kw in keywords)


def suggest_with_persona(yaml_text, persona="junior"):
    try:
        yaml_text = yaml_text.strip()

        # Reject invalid persona early
        if persona not in ["junior", "senior", "sre"]:
            logger.warning(f"Invalid persona: {persona}")
            return "Invalid persona. Choose from: junior, senior, sre."

        # Validate YAML before sending to LLM
        try:
            yaml.safe_load_all(yaml_text)
        except yaml.YAMLError:
            return "Invalid YAML structure detected. Please fix formatting or indentation first."

        # Load the appropriate persona prompt
        try:
           parsed_docs = list(yaml.safe_load_all(yaml_text))
           has_podspec = any(
               doc.get("kind") in ["Deployment", "StatefulSet", "DaemonSet", "Job"]
               for doc in parsed_docs if isinstance(doc, dict)
         )
        except yaml.YAMLError:
            logger.warning("Invalid YAML structure during persona analysis.")
            return "Invalid YAML. Please check indentation or formatting."

# Use lighter prompt for non-podspec YAML
        if not has_podspec:
           logger.info("Using simple persona prompt for non-PodSpec YAML.")
           persona_prompt = load_prompt(f"persona_{persona}_simple.txt")
        else:
           persona_prompt = load_prompt(f"persona_{persona}.txt")


        # Construct the LLM prompt
        prompt = f"{persona_prompt}\n\nHere is the YAML file:\n```yaml\n{yaml_text}\n```"
        messages = [
            {"role": "system", "content": "You are a helpful Kubernetes DevSecOps expert."},
            {"role": "user", "content": prompt.strip()}
        ]

        content = run_llm_with_timeout("mistral", messages)

        if is_valid_persona_response(content):

            memory.add(f"[{datetime.now()}] Prompt: {prompt}\nResponse: {content}")
            memory.save("memory-data/memory.pkl")
            return content
        else:
            logger.warning("LLM persona suggestion invalid. Fallback used.")
            return "No persona-based suggestion available. Try later."

    except Exception as e:
        logger.exception("LLM suggest_with_persona() failed")
        return "Error occurred in persona suggestion. Retry later."

def is_valid_recommendation_response(text: str) -> bool:
    if not text or not text.strip():
        return False

    # Must contain core elements of the required structure
    keywords = [
        "Event", "Tool", "CI/CD", "Security", "Cultural",  # required sections
        "recommend", "DevSecOps", "Kubernetes", "GitOps"   # good extras
    ]

    score = sum(1 for k in keywords if k.lower() in text.lower())
    return score >= 3  # must hit at least 3 keywords




from datetime import datetime
from src.llm_handler import memory, run_llm_with_timeout, is_valid_response, load_prompt
import logging

logger = logging.getLogger(__name__)

def explain_with_qloo(persona: str, qloo_data: dict, mode: str = "default") -> str:
    meta = preprocess_persona(persona)

    try:
        base_prompt = f"""You are a DevSecOps mentor advising a developer with this persona: "{persona}".

Your job is to generate a personalized DevOps + Kubernetes security recommendation based on their background, interests, and region.

Your response MUST include:
1. **Event or Course** — Online or cultural DevSecOps learning events
2. **Tool or Platform** — Real-world DevOps tools (like OPA, Argo CD, etc.)
3. **CI/CD Strategy** — E.g., GitOps, Jenkins, GitHub Actions
4. **Security Practice** — Zero Trust, PoLP, etc.
5. **Cultural Flavor** — Light cultural metaphor ONLY if user’s background implies it

You MUST:
- Provide brief affinity/explanation for each suggestion
- Keep it grounded in real-world tools (unless otherwise requested)
- Ensure the response is practical, clear, and helpful
"""

        # Add Qloo flavor if available
        if qloo_data:
            base_prompt += f"\n\nRelevant Cultural Data (from Qloo):\n{qloo_data}"

        # Guardrails for metaphors
        if "marvel" not in persona.lower():
            base_prompt += "\n\nIMPORTANT: Avoid excessive fictional or Marvel references. Stick to real tools unless explicitly requested."

        # Guardrails for fictional cultural events
        base_prompt += (
            "\n\nIMPORTANT: If suggesting fictional or cultural events (like a K-Pop Kubernetes meetup), label them clearly as *hypothetical examples*."
        )
        # Persona enrichment for abstract roles with no cultural or regional hook
        if any(word in persona.lower() for word in ["founder", "cybersecurity", "privacy", "startup"]):
            base_prompt += (
        "\n\nExtra Tip: Since this user is likely focused on early-stage infra or startup concerns, "
        "highlight cost-effective DevSecOps, compliance tools (like SOC2 automation), or cloud governance tips. "
        "Include founder-focused advice — not just enterprise patterns."
    )

        # Inject tone and regional awareness via system role
        messages = [
            {
                "role": "system",
                "content": f"You are a DevSecOps advisor crafting responses in a {meta['tone']} tone with {meta['region']} cultural awareness."
            },
            {
                "role": "user",
                "content": base_prompt.strip()
            }
        ]

        response = run_llm_with_timeout("mistral", messages)

        if is_valid_recommendation_response(response):
            memory.add(f"Persona: {persona}\nResponse: {response}")
            memory.save("memory-data/memory.pkl")
            return response

        return "Could not generate a recommendation at this time."

    except Exception as e:
        logger.exception("Error in explain_with_qloo")
        return "Internal error while generating recommendation."
