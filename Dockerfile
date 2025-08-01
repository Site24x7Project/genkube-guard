# ✅ 1. Use a slim Python base
FROM python:3.10-slim

# ✅ 2. Create a non-root user (required by Hugging Face)
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

# ✅ 3. Install system dependencies (including curl)
RUN apt-get update && \
    apt-get install -y build-essential curl && \
    rm -rf /var/lib/apt/lists/*

# ✅ 4. Install kube-linter CLI
RUN curl -L https://github.com/stackrox/kube-linter/releases/download/v0.6.6/kube-linter-linux.tar.gz \
  | tar -xz && chmod +x kube-linter && mv kube-linter /usr/local/bin/kube-linter

# ✅ 5. Set working directory
WORKDIR /app

# ✅ 6. Copy requirements and install them
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ✅ 7. Copy all source code into the image
COPY --chown=user . .

# ✅ 8. Set environment variables and expose port 7860
ENV LOG_LEVEL=info
ENV OLLAMA_HOST=http://host.docker.internal:11434
EXPOSE 7860

# ✅ 9. Launch app using correct port for Hugging Face
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860", "--log-level", "info"]
