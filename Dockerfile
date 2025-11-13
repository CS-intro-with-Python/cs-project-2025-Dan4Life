FROM python:3.11-slim
WORKDIR /app
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app /app
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:create_app()"]