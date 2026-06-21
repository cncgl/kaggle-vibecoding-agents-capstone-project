# FeasiblePlan — single-container web app (Deployability concept).
# Build:  docker build -t feasibleplan .
# Run:    docker run -p 8000:8000 feasibleplan        # then open http://localhost:8000
# Deploy: gcloud run deploy feasibleplan --source .   # Cloud Run sets $PORT

FROM python:3.12-slim

WORKDIR /app
RUN pip install --no-cache-dir uv

# Install deps first (better layer caching), then the app.
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev

# A public deploy defaults to the deterministic MOCK backend: no API key, no quota,
# no LLM cost, and it never breaks — yet it tells the same verify→repair story. So a
# Cloud Run demo stays up forever for $0 of model spend. To use a real LLM instead,
# override at deploy time, e.g.:
#   gcloud run deploy ... --set-env-vars FEASIBLEPLAN_BACKEND=gemini,GOOGLE_API_KEY=...
ENV FEASIBLEPLAN_BACKEND=mock

EXPOSE 8000
# Bind 0.0.0.0 and honor Cloud Run's $PORT.
CMD ["sh", "-c", "uv run uvicorn kaggle_vibecoding_agents_capstone_project.web:app --host 0.0.0.0 --port ${PORT:-8000}"]
