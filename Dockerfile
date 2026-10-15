FROM python:3.11-slim

WORKDIR /app

# instalar dependencias del sistema necesarias para playwright
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
    git \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install https://github.com/explosion/spacy-models/releases/download/es_core_news_sm-3.7.0/es_core_news_sm-3.7.0.tar.gz

# instalar navegadores playwright
RUN playwright install --with-deps

COPY . .

EXPOSE 8090

CMD ["python", "-m", "app.main"]