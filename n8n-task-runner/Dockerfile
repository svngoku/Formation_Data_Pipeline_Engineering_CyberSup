ARG N8N_RUNNERS_VERSION=2.2.6
FROM n8nio/runners:${N8N_RUNNERS_VERSION}

USER root

# Add Python dependencies for the n8n Python task runner (Code node)
RUN uv pip install --system \
    pandas \
    pyarrow \
    requests \
    tenacity

USER runner
