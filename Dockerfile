FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

RUN rm -f gunicorn.conf.py

CMD gunicorn --bind 0.0.0.0:$PORT app:app --log-level debug --access-logfile - --error-logfile -
