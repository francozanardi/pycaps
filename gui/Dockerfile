FROM python:3.10-slim

ENV HOME="/app"
WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

ENV PLAYWRIGHT_BROWSERS_PATH="/app/.playwright"
ENV XDG_CACHE_HOME="/app/.cache"
RUN playwright install-deps
RUN playwright install chromium
RUN python3 -c "import whisper; whisper.load_model('base', download_root='${XDG_CACHE_HOME}/whisper')"

RUN useradd -m -u 1000 user

COPY src/ ./src/

RUN chown -R user:user /app

USER user

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "src/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
