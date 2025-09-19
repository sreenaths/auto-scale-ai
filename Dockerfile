FROM ghcr.io/astral-sh/uv:python3.10-bookworm
WORKDIR /src

# 1) deps only
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev --no-install-project || uv sync --no-dev --no-install-project

# 2) source + readme
COPY src/ ./src/
COPY README.md ./

# 3) make src/ layout importable
ENV PYTHONPATH=/src/src:$PYTHONPATH

EXPOSE 8000
# 4) point uvicorn explicitly at your source dir
CMD ["uv","run","uvicorn","--app-dir","/src/src","auto_scale_ai.main:app","--host","0.0.0.0","--port","8000"]
