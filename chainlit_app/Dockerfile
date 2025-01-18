FROM python:3.10-slim

ENV PORT 8000

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE $PORT

CMD ["sh", "-c", "python -m chainlit run app.py --host 0.0.0.0 --port $PORT"]
