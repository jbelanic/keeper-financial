FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
RUN apt-get update && \
    apt-get install --no-install-recommends --yes libmagic1 && \
    rm -rf /var/lib/apt/lists/* && \
    groupadd --system keeper && \
    useradd --system --gid keeper --home-dir /nonexistent --shell /usr/sbin/nologin keeper
COPY --chown=keeper:keeper apps/api /app/apps/api
RUN python -m pip install --no-cache-dir --upgrade pip==26.1.2 && \
    pip install --no-cache-dir /app/apps/api
COPY --chown=keeper:keeper storage/dev_uploads/.gitkeep /app/storage/dev_uploads/.gitkeep

WORKDIR /app/apps/api
EXPOSE 8000
USER keeper
CMD ["uvicorn", "keeper_api.main:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000"]
