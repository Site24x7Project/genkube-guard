# GenKube Guard

> A DevSecOps LLM-powered Assistant for Secure Kubernetes YAMLs

GenKube Guard is a FastAPI-based backend that combines Large Language Model reasoning with Qloo’s Taste AI to offer culturally-aware and technically sound recommendations for Kubernetes YAML hardening. It automatically analyzes YAML files, suggests security enhancements, and provides patching logic for insecure workloads.

---

## 🚀 Features

- **LLM-Powered YAML Analysis** (`/analyze`) – Uses `kube-linter` to detect issues and explains them via LLM.
- **Secure Patch Generator** (`/patch`) – Automatically patches Deployments and StatefulSets with missing security fields.
- **DevSecOps Suggestions** (`/suggest`) – General best practices by resource kind.
- **Persona-Specific Guidance** (`/suggest-persona`) – Tailored YAML advice for juniors, seniors, and SREs.
- **Taste-Aware Recommendations** (`/recommend`) – Culturally flavored DevSecOps insights via Qloo mock API.
- **RAG Memory System** (`/memory`) – Stores and retrieves DevSecOps context across sessions.
- **GraphQL Memory Search** (`/graphql`) – Query memory semantically via Strawberry GraphQL.

---

## 🌐 About Qloo API Integration

We initially obtained a Qloo API key, but due to technical issues during the submission window, the `/recommend` endpoint uses a **mock implementation**. All logic and persona flavoring follow Qloo’s expected structure.

---

## 🧠 Memory & GraphQL Notes

- For short DevSecOps facts (e.g., `"Privileged containers are risky"`), the system uses a **fast fallback** parser.
- For deeper issues (e.g., unset `memoryLimits`, missing `probes`), it uses **full RAG + LLM** flow.
- All entries are searchable via `/memory/search` or `/graphql`.

This hybrid design optimizes both speed and cost while preserving intelligence.

---

## 🛠️ Technologies Used

- **FastAPI** – Python backend
- **Ollama + Mistral 7B** – LLM inference
- **FAISS** – Local memory vector store
- **Strawberry GraphQL** – Memory querying
- **kube-linter** – Static YAML issue detection
- **Docker + Docker Compose** – Deployment

---

## 🧪 How to Run Locally

```bash
git clone https://github.com/Site24x7Project/genkube-guard.git
cd genkube-guard
docker-compose up --build
```

Visit:

- Swagger: [http://localhost:8000/docs](http://localhost:8000/docs)
- GraphQL: [http://localhost:8000/graphql](http://localhost:8000/graphql)

---

## 📂 API Endpoints

| Endpoint                | Description                                              |
|------------------------|----------------------------------------------------------|
| `POST /analyze`         | Analyze YAML & explain issues via LLM                   |
| `POST /patch`           | Patch Deployment/StatefulSet with missing security best practices |
| `POST /suggest`         | Suggest generic DevSecOps improvements by kind         |
| `POST /suggest-persona` | Persona-based (junior/senior/SRE) YAML suggestions      |
| `POST /recommend`       | Recommend cultural-aware practices (mock Qloo)          |
| `POST /memory`          | Save prompt-response memory                             |
| `POST /memory/clear`    | Clear memory index                                      |
| `POST /graphql`         | Search memory semantically or by keyword                |

---

## 📄 Test YAMLs

All example YAMLs used for testing are included in the `k8s/` folder:

- `sample_deployment.yaml`
- `secure_deployment.yaml`
- `statefulset.yaml`
- `broken_yaml.yaml`
- `multi_resource_mixed.yaml`
- `service_and_configmap.yaml`

---

## ❌ No Frontend UI

This project is **backend-only by design** to focus on LLM reasoning and DevSecOps logic.  
All endpoints are available via REST or GraphQL, with no separate user interface.

---

## 🎥 Demo Video

🔗 [Demo – YouTube](https://youtube.com/shorts/1Z7KkgxuFQc?si=ukPMZ94mImA_IQMH)

---

## 🔍 Submission Details

- **GitHub**: [GenKube Guard Repository](https://github.com/Site24x7Project/genkube-guard)
- **Hackathon**: Qloo LLM Hackathon 2025
- **Built by**: Aswathi VK
- **Focus**: Cultural + DevSecOps synergy for secure YAMLs
- **Deployment**: Docker on local + portable cloud-ready stack

---

## 📜 License & Attribution

- MIT License
- kube-linter (via open source)
- Qloo mock fallback used
- Ollama with Mistral 7B for all LLM prompts

---

## 🙏 Acknowledgements

Thank you to the Qloo team and judges. Grateful to the OSS community building the future of LLMs and DevSecOps.

---

Made with ❤️ by **Aswathi VK**
