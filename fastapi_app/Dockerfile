FROM python:3.10-slim

ENV PORT 8010

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . ./fastapi_app

EXPOSE $PORT

CMD ["sh", "-c", "uvicorn fastapi_app.main:app --host 0.0.0.0 --port $PORT"]
