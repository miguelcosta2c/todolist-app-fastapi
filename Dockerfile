# =====================================================================
# ESTÁGIO 1: Builder — gera o .venv com UV
# =====================================================================
FROM python:3.13-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /code

COPY --link pyproject.toml uv.lock README.md ./

RUN UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy \
    uv sync --frozen --no-install-project --no-dev

# =====================================================================
# ESTÁGIO 2: Desenvolvimento
# =====================================================================
FROM python:3.13-slim AS development

WORKDIR /code

COPY --from=builder /code/.venv /code/.venv

ENV PATH="/code/.venv/bin:$PATH"

COPY --link ./src/app /code/app
COPY --link ./alembic /code/alembic
COPY --link ./alembic.ini /code/alembic.ini

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]


# =====================================================================
# ESTÁGIO 3: Produção
# =====================================================================
FROM python:3.13-slim AS production

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/code/.venv/bin:$PATH"

WORKDIR /code

RUN groupadd --gid 1001 appgroup \
 && useradd --uid 1001 --gid appgroup --no-create-home appuser

COPY --from=builder /code/.venv /code/.venv
COPY --link ./src/app /code/app

RUN chown -R appuser:appgroup /code

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
