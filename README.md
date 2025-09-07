# GenKube Guard

GenKube Guard is an AI-powered Kubernetes YAML security assistant designed to help teams analyze, patch, and improve Kubernetes manifests with intelligent suggestions. It combines **GenAI capabilities** like LLM-driven recommendations and semantic memory (RAG) with strong backend engineering practices.

---

## 📊 Features

* **Analyze** Kubernetes YAML for issues with `/analyze` (integrates `kube-linter`).
* **Auto-Patch** YAML for security and performance best practices via `/patch`.
* **Suggest** improvements using `/suggest` or persona-based `/suggest-persona`.
* **Mock Recommendations** via `/recommend` endpoint (Qloo API is mocked for demo purposes).
* **Memory Search** to recall past prompts and responses with `/memory` and `/graphql`.
* **REST + GraphQL APIs** to integrate into diverse tooling.
* **Rate limiting** built-in via SlowAPI for controlled usage.

---

## 🔧 Architecture Highlights

GenKube Guard isn't just a YAML analyzer — it’s a **full GenAI backend** built for real-world scale in 2025:

* **Dual Memory System** – Combines a fast FAISS store for `/memory` with a semantic RAG engine (`memory.pkl`) for deep LLM context recall.
* **Secure Auto-Patching** – `/patch` enforces DevSecOps best practices (runAsNonRoot, resource limits, probes) directly in Kubernetes YAML.
* **GraphQL + REST APIs** – Memory can be queried via REST **or** GraphQL using Strawberry.
* **Security-First Containers** – Non-root Docker builds and integrated `kube-linter` binary for runtime linting.
* **Persona-Aware Prompting** – 10 carefully engineered prompt templates for juniors, seniors, and SREs, mixing cultural and technical context.
* **Production-like Testing** – Includes comprehensive test suite with multiple sample YAMLs for broken, mixed, and secure deployments.

**Why it matters in 2025:**
Companies like **Twilio** and **Glean** increasingly demand **GenAI-powered developer tools** that go beyond simple chatbots. This project demonstrates how **retrieval-augmented generation (RAG)**, persona-driven LLMs, and backend engineering can come together to solve real DevSecOps challenges.

---

## 🔒 Example Auto-Patch

**Input YAML:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  template:
    spec:
      containers:
      - name: app
        image: nginx:latest
```

**Output YAML:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  template:
    spec:
      containers:
      - name: app
        image: nginx:1.21.1
        securityContext:
          runAsNonRoot: true
          runAsUser: 1000
          readOnlyRootFilesystem: true
        resources:
          requests:
            cpu: "125m"
            memory: "256Mi"
          limits:
            cpu: "250m"
            memory: "512Mi"
```

This demonstrates GenKube Guard's ability to enforce strong security practices automatically.

---

## 📹 Demo Video

Watch the project in action: [YouTube Demo](https://www.youtube.com/watch?v=YOUR_VIDEO_LINK)

---

## 🛠️ Local Setup

```bash
# Clone repository
git clone https://github.com/yourusername/genkube-guard.git
cd genkube-guard

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn main:app --reload
```

### Docker Run

```bash
# Build Docker image
docker build -t genkube-guard .

# Run container
docker run -p 7860:7860 genkube-guard
```

> **Note:** Default port for Hugging Face is `7860`.

---

## 🛠️ Endpoints

| Endpoint           | Method | Description                           |
| ------------------ | ------ | ------------------------------------- |
| `/analyze`         | POST   | Analyze uploaded YAML for lint issues |
| `/patch`           | POST   | Auto-secure Kubernetes YAML           |
| `/suggest`         | POST   | Suggest improvements                  |
| `/suggest-persona` | POST   | Persona-driven suggestions            |
| `/recommend`       | GET    | Mock recommendation data              |
| `/memory`          | GET    | View simple FAISS memory              |
| `/graphql`         | POST   | Query memory with GraphQL             |

---

## 💡 Why This Matters

In 2025, developer tooling is shifting towards **intelligent, context-aware assistants**. GenKube Guard showcases how **GenAI and traditional engineering** can combine to:

* Improve cloud-native security.
* Automate repetitive DevOps work.
* Provide explainable, persona-based insights for diverse teams.
* Serve as a blueprint for scalable GenAI backends with RAG.

This isn't just a student project — it's a **production-grade demonstration** of what next-gen developer assistants will look like.

---

## 📊 Kubernetes Sample YAMLs for Testing

* `broken_yaml.yaml` – malformed YAML
* `multi_resource_mixed.yaml` – multiple resource types
* `sample_deployment.yaml` – minimal valid deployment
* `secure_deployment.yaml` – already hardened deployment
* `service_and_configmap.yaml` – service and configmap example
* `statefulset.yaml` – statefulset example

These files are used in automated tests to validate GenKube Guard's capabilities.

---

## 📄 License

MIT License

---

> Built with 💖 for modern DevSecOps teams.
