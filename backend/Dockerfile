FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY packages/experiment_os_stats /app/packages/experiment_os_stats
COPY backend /app/backend

RUN pip install --no-cache-dir /app/packages/experiment_os_stats /app/backend

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--app-dir", "/app/backend", "--host", "0.0.0.0", "--port", "8000"]
