FROM python:3.10-slim
WORKDIR /src
COPY requirements.txt .
RUN apt-get update && apt-get install -y gcc libpq-dev \
    && pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "src/main.py"]
