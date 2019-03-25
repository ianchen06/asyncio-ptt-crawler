FROM python:3.7-slim
WORKDIR /app
COPY requirements.txt .
RUN apt-get update && apt-get install -y build-essential && pip install -r requirements.txt
COPY . .
