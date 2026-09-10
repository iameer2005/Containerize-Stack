FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY main_ai.py .
CMD ["uvicorn", "main_ai:app", "--host", "0.0.0.0", "--port", "3000"]
