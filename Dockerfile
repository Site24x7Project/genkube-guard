# ✅ 1. Use a slim Python base
FROM python:3.10-slim

# ✅ 2. Install system deps including curl
RUN apt-get update && \
    apt-get install -y build-essential curl && \
    rm -rf /var/lib/apt/lists/*

# ✅ 3. Install kube-linter CLI
RUN curl -L https://github.com/stackrox/kube-linter/releases/download/v0.6.6/kube-linter-linux.tar.gz \
  | tar -xz && chmod +x kube-linter && mv kube-linter /usr/local/bin/kube-linter

# ✅ 4. Set working directory
WORKDIR /app

# ✅ 5. Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ✅ 6. Copy source code
COPY . .

# ✅ 7. Set log level and expose port
ENV LOG_LEVEL=info
EXPOSE 8000

# ✅ 8. Run the app with production logging format
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
ENV OLLAMA_HOST=http://host.docker.internal:11434
