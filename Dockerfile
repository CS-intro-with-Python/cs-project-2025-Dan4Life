FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py /app/server.py
COPY templates /app/templates
COPY static /app/static
COPY tests /app/tests

ENV PYTHONPATH=/app

EXPOSE 8080

CMD gunicorn -w 2 -b 0.0.0.0:${PORT:-8080} server:app
