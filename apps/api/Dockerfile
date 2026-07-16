FROM python:3.12.10-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app
COPY pyproject.toml ./
COPY src ./src
COPY alembic.ini ./
COPY alembic ./alembic
RUN pip install --no-cache-dir .

USER app
EXPOSE 8000
CMD ["uvicorn", "civicsignal_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
