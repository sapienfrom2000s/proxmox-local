FROM python:3.14-slim AS deps
WORKDIR /app
COPY requirements.prod.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.prod.txt

FROM python:3.14-slim
WORKDIR /app
COPY --from=deps /install /usr/local
COPY . .
RUN adduser --disabled-password --no-create-home appuser
USER appuser
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:create_app()"]
