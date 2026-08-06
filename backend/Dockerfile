FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN groupadd --system --gid 10001 mailhub \
    && useradd --system --uid 10001 --gid mailhub --create-home mailhub

WORKDIR /app
COPY pyproject.toml README.md alembic.ini ./
COPY alembic ./alembic
COPY src ./src
COPY entrypoint.sh ./entrypoint.sh
RUN pip install --upgrade pip \
    && pip install . \
    && chmod +x /app/entrypoint.sh

USER mailhub
EXPOSE 8080
ENTRYPOINT ["/app/entrypoint.sh"]
