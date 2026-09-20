# syntax=docker/dockerfile:1
# Sinergia - single container: FastAPI serves the built React/Vite frontend.
# Stage 1 builds the frontend, stage 2 builds Python wheels, stage 3 is the slim runtime.

# ---- Stage 1: React / Vite build ----
FROM node:20-alpine AS frontend-build
WORKDIR /frontend
COPY frontend/package*.json ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi
COPY frontend/ ./
RUN npm run build

# ---- Stage 2: Python dependencies ----
FROM python:3.12-slim AS python-build
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---- Stage 3: Runtime ----
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home appuser
WORKDIR /app
COPY --from=python-build /install /usr/local
COPY --chown=appuser:appuser backend ./backend
COPY --from=frontend-build --chown=appuser:appuser /frontend/dist ./frontend/dist
USER appuser
EXPOSE 8000
# --proxy-headers lets slowapi see the real client IP behind Cloud Run's load balancer
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
