FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py ./
COPY config.py ./
COPY blueprints ./blueprints
COPY utils ./utils
COPY rabbitmq ./rabbitmq
EXPOSE 5000
COPY wait_for_db.py ./
RUN chmod +x ./wait_for_db.py
ENTRYPOINT ["python", "./wait_for_db.py"]
