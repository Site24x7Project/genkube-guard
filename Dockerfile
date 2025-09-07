FROM python:3.10-slim

# Ensure apt runs as root in the build stage
USER root

# System deps (no recommends to keep image small)
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates tar && \
    rm -rf /var/lib/apt/lists/*

# Install kube-linter (Linux binary)
RUN curl -fsSL https://github.com/stackrox/kube-linter/releases/download/v0.6.6/kube-linter-linux.tar.gz \
  | tar -xz && mv kube-linter /usr/local/bin/kube-linter

# Non-root runtime user
RUN useradd -m -u 1000 user

# App
WORKDIR /app
COPY --chown=user:user . .

# Python deps
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/app

# Drop privileges
USER user

# HF expects 7860; Cloud Run will override with PORT
EXPOSE 7860
CMD ["python","-c","import os,uvicorn; uvicorn.run('main:app', host='0.0.0.0', port=int(os.getenv('PORT','7860')))"]
