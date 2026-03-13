FROM python:3.11-slim

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar dependencias
COPY requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Exponer puerto del gateway
EXPOSE 7001

# Ejecutar aplicación
CMD ["gunicorn", "-b", "0.0.0.0:7001", "app:app"]