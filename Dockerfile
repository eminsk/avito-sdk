# Dockerfile for Model Context Protocol (MCP) server automated testing & container runs
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies if any
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY . /app

RUN pip install --no-cache-dir ".[tls,excel]"

ENTRYPOINT ["avito-mcp"]
