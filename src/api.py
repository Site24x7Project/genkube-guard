from fastapi import FastAPI, UploadFile, File, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import strawberry
from strawberry.fastapi import GraphQLRouter
import yaml
import asyncio
import faiss
import logging

from src import linter_runner, llm_handler
from src.schema import Query as GQLQuery, Mutation as GQLMutation
from src import qloo_handler
from src.llm_handler import explain_with_qloo, memory

logger = logging.getLogger("genkube")

app = FastAPI()
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/analyze")
@limiter.limit("5/minute")
async def analyze_yaml(request: Request, file: UploadFile = File(...)):
    try:
        content = await file.read()
        logger.info("Received file for analysis: %s", file.filename)

        # ✅ Step 1: Pre-validate YAML syntax
        try:
          list(yaml.safe_load_all(content))  # <-- force parse!
        except yaml.YAMLError as e:

            logger.warning("Broken YAML file: %s", file.filename)
            return {
                "issues": ["Invalid or unparseable YAML."],
                "explanations": [
                    "The provided file could not be parsed due to syntax errors. Please ensure it is valid Kubernetes YAML."
                ],
            }
        try:
           yaml.safe_load_all(content)
        except yaml.YAMLError:
           return {
        "issues": ["Invalid or unparseable YAML."],
        "explanations": [
            "The provided file could not be parsed due to syntax errors. Please ensure it is valid Kubernetes YAML."
        ]
    }

        # Step 2: Proceed with linting if YAML is valid
        issues = linter_runner.run_kube_linter(content)

        if len(issues) == 1 and issues[0].strip().lower() == "no lint issues found.":
            logger.info("No issues found by kube-linter.")
            return {
                "issues": issues,
                "explanations": ["No issues, so no explanations needed."]
            }

        loop = asyncio.get_event_loop()

        async def run_explain(issue):
            return await loop.run_in_executor(None, llm_handler.explain, issue)

        explanations = await asyncio.gather(*(run_explain(issue) for issue in issues))
        return {"issues": issues, "explanations": explanations}

    except Exception as e:
        logger.exception("Error during /analyze endpoint")
        return {"error": "Internal Server Error during analysis."}



@app.post("/patch")
async def patch_yaml(file: UploadFile = File(...)):
    try:
        raw_bytes = await file.read()
        try:
            raw = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return {"error": "Uploaded file is not valid UTF-8."}

        if not raw.strip():
            return {"error": "Uploaded YAML is empty or unreadable."}

        logger.info("Received file for patching: %s", file.filename)

        try:
            docs = list(yaml.safe_load_all(raw))
        except yaml.YAMLError as e:
            logger.warning("YAML parsing failed: %s", e)
            return {"patched_yaml": "# Skipped: Invalid or unparseable YAML content."}

        has_patchable_kind = any(
            doc and doc.get("kind") in {"Deployment", "StatefulSet"} for doc in docs
        )

        if not has_patchable_kind:
            logger.info("No patchable resources found in YAML; skipping patch.")
            return {"patched_yaml": raw}

        patched = llm_handler.generate_patch(raw)
        logger.info("Patch generation complete.")
        return {"patched_yaml": patched}

    except Exception as e:
        logger.exception("Error during /patch endpoint")
        return {"error": "Internal Server Error during patching."}


@app.post("/suggest")
@limiter.limit("5/minute")
async def suggest_improvements(request: Request, file: UploadFile = File(...)):
    try:
        raw_bytes = await file.read()
        try:
            yaml_str = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return {"error": "Uploaded file is not valid UTF-8."}

        if not yaml_str.strip():
            return {"error": "Uploaded YAML is empty or unreadable."}

        logger.info("Suggest request received: %s", file.filename)

        # NEW: Validate YAML syntax before calling LLM
        try:
            list(yaml.safe_load_all(yaml_str))
        except yaml.YAMLError:
            return {"suggestions": "Invalid YAML. Could not parse structure. Please fix formatting or indentation."}

        suggestions = llm_handler.suggest(yaml_str)
        return {"suggestions": suggestions}
    except Exception as e:
        logger.exception("Error in /suggest")
        return {"error": "Internal Server Error during suggestion generation."}



@app.post("/suggest-persona")
async def suggest_for_persona(
    file: UploadFile = File(...),
    persona: str = Query("junior")
):
    try:
        raw_bytes = await file.read()
        try:
            yaml_str = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return {"error": "Uploaded file is not valid UTF-8."}

        if not yaml_str.strip():
            return {"error": "Uploaded YAML is empty or unreadable."}

        logger.info("Suggest-persona request: %s | Persona: %s", file.filename, persona)
        persona_suggestions = llm_handler.suggest_with_persona(yaml_str, persona)
        return {"persona_suggestions": persona_suggestions}
    except Exception as e:
        logger.exception("Error in /suggest-persona")
        return {"error": "Internal Server Error during persona-based suggestion."}


@app.get("/memory")
def get_recent_memories(q: str = Query(..., description="Query term for RAG memory")):
    try:
        logger.info("Memory query received: %s", q)
        results = llm_handler.memory.search(q)
        return {"related": results}
    except Exception as e:
        logger.exception("Error in /memory")
        return {"error": "Internal Server Error during memory retrieval."}


@app.post("/memory/clear")
def clear_memory():
    memory.store.clear()
    memory.index = faiss.IndexFlatL2(memory.dim)
    memory.save("memory-data/memory.pkl")
    return {"message": "Memory cleared."}


@app.get("/")
def root():
    return {"message": "GenKube Guard is running 🚀"}


from fastapi import FastAPI, Request, Query
from src import qloo_handler
from src.llm_handler import explain_with_qloo
from slowapi import Limiter
import logging



@app.get("/recommend")
@limiter.limit("10/minute")
def get_recommendation(
    request: Request,
    q: str = Query(..., description="Describe the user or cultural persona"),
    mode: str = Query("default", description="Mode: default or technical"),
    debug: bool = Query(False, description="If true, return raw Qloo + prompt")  # 👈 Optional
):
    try:
        logger.info("Recommend called: persona=%s | mode=%s", q, mode)
        qloo_data = qloo_handler.get_qloo_profile(q, mode=mode)

        if "error" in qloo_data:
            logger.warning("Qloo returned error for %s", q)
            return {"error": qloo_data["error"]}

        enriched_explanation = explain_with_qloo(q, qloo_data, mode=mode)

        if debug:
            return {
                "recommendation": enriched_explanation,
                "qloo_data": qloo_data,
                "mode": mode
            }

        return {"recommendation": enriched_explanation}

    except Exception as e:
        logger.exception("Error in /recommend")
        return {"error": "Internal Server Error during recommendation."}


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    logger.warning("Rate limit exceeded: %s", request.client.host)
    return JSONResponse(status_code=429, content={"error": "Rate limit exceeded. Try again later."})


schema = strawberry.Schema(query=GQLQuery, mutation=GQLMutation)
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")


