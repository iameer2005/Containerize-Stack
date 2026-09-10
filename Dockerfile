FROM python:3.13-slim

WORKDIR /app

# Prevent Python from writing .pyc files to disk and ensure direct console logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Copy dependency definition and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code and database initialization script
COPY app/ ./app/
COPY init.sql .

# Expose web application port
EXPOSE 3000

# Launch Uvicorn production server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3000"]
