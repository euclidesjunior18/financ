FROM python:3.12-slim

WORKDIR /app

# Instalar dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar arquivos do projeto
COPY . .

# Expor porta
EXPOSE 5000

# Executar com Gunicorn para produção
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
