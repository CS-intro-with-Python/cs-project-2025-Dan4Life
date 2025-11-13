FROM python:3.11-slim
WORKDIR /app
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app /app
CMD ["sh", "-c", "gunicorn -w 4 -b 0.0.0.0:${PORT:-5000} 'app.app:create_app()'" ]