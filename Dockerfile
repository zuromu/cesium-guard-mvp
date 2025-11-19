FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["sh", "-c", "echo PORT=$PORT && gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 120 app:app --log-level debug"]
