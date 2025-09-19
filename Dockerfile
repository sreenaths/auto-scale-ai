FROM ghcr.io/astral-sh/uv:python3.10-bookworm

WORKDIR /src
COPY pyproject.toml uv.lock* ./

# Install deps only (don’t install the project yet)
RUN uv sync --frozen --no-dev --no-install-project || \
    (uv lock && uv sync --no-dev --no-install-project)

# Now add your source tree (src layout)
COPY src/ ./src/
COPY README.md ./

# Install the project so imports work
RUN uv sync --frozen --no-dev || uv sync --no-dev

EXPOSE 8000
CMD ["uv","run","uvicorn","auto_scale_ai.main:app","--host","0.0.0.0","--port","8000"]
