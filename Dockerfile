FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /app/model /app/indexes_with_overlap_100_chunks_500

COPY ./model1/* /app/model/
COPY ./indexes_with_overlap_100_chunks_500/* /app/indexes_with_overlap_100_chunks_500/
COPY main.py .
COPY init_elasticsearch.sh .
COPY fifa_laws_mapping.json .
COPY fifa_laws_data.json .

RUN chmod +x /app/init_elasticsearch.sh

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]