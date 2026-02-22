FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 7000
CMD ["gunicorn", "-b", "0.0.0.0:7000", "--workers", "2", "--threads", "4", "app:app"]