FROM python:3.10-slim

ENV PORT 8000

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE $PORT

# Make sure start.sh is executable
RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]
