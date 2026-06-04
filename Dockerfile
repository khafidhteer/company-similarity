FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./
RUN python -m pip install --no-cache-dir --upgrade pip && \
    python -m pip install --no-cache-dir -r requirements.txt

COPY match_companies.py ./

ENTRYPOINT ["python", "match_companies.py"]
