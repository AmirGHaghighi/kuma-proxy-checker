# syntax=docker/dockerfile:1

FROM python:3.11-slim

ARG VERSION=unknown
ARG REVISION=unknown

LABEL org.opencontainers.image.title="kuma-proxy-checker" \
      org.opencontainers.image.description="Proxy health checker with per-proxy Uptime Kuma push reporting" \
      org.opencontainers.image.source="https://github.com/AmirGHaghighi/kuma-proxy-checker" \
      org.opencontainers.image.licenses="GPL-3.0" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.revision="${REVISION}"

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY config.example.json ./config.example.json

RUN pip install --no-cache-dir . \
    && rm -rf src pyproject.toml README.md

RUN useradd --system --uid 10001 --create-home appuser \
    && mkdir -p /etc/kuma-proxy-checker \
    && chown -R appuser:appuser /app /etc/kuma-proxy-checker

USER appuser

EXPOSE 8080

ENTRYPOINT ["kuma-proxy-checker"]
CMD ["-c", "/etc/kuma-proxy-checker/config.json"]
