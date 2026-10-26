FROM node:20-alpine AS css
WORKDIR /src
COPY package.json package-lock.json ./
RUN npm ci
COPY tailwind.config.js ./
COPY templates ./templates
COPY static/css/input.css ./static/css/input.css
RUN npm run build:css

FROM python:3.12-slim AS app
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY templates ./templates
COPY static ./static
COPY --from=css /src/static/css/app.css ./static/css/app.css

RUN useradd --create-home appuser \
    && mkdir -p /app/data \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
