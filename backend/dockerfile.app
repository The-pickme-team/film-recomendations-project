FROM python:3.14-slim AS builder
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY ./pyproject.toml ./uv.lock ./
RUN uv sync --locked --compile-bytecode

FROM python:3.14-slim

COPY --from=builder /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src:$PYTHONPATH"

WORKDIR /app

COPY ./src ./src
COPY ./run.sh ./run.sh

RUN chmod +x run.sh
ENTRYPOINT [ "./run.sh" ]