FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
RUN groupadd --system keeper && \
    useradd --system --gid keeper --home-dir /nonexistent --shell /usr/sbin/nologin keeper
COPY --chown=keeper:keeper apps/api /app/apps/api
RUN pip install --no-cache-dir /app/apps/api
COPY --chown=keeper:keeper storage/dev_uploads/.gitkeep /app/storage/dev_uploads/.gitkeep

EXPOSE 8000
USER keeper
CMD ["uvicorn", "keeper_api.main:app", "--app-dir", "/app/apps/api/src", "--host", "0.0.0.0", "--port", "8000"]
