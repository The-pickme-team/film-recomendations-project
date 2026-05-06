FROM python:3.14-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/

WORKDIR /app
COPY pyproject.toml uv.lock ./

RUN uv sync --locked --compile-bytecode

FROM python:3.14-slim AS runtime

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv

COPY ./src ./src
COPY ./run.sh ./

RUN chmod +x ./run.sh

ENV PATH=/app/.venv/bin:$PATH \
  PYTHONOPTIMIZE=1 \
  PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1

ENTRYPOINT ["./run.sh"]