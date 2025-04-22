
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create tables and seed data on container start
CMD ["sh", "-c", "python -m scripts.seed_data && python run.py"]
