# Dockerfile
FROM python:3.11-slim
WORKDIR /app

# Copy and install dependencies
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application and client code
COPY client /app/client
# Copy the main application code (app/app.py, app/__init__.py, etc.)
COPY app /app/app

# Setup Entrypoint script
# Copy the entrypoint script and make it executable
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Define the Entrypoint and Command
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:${PORT:-5000}", "app.app:create_app"]