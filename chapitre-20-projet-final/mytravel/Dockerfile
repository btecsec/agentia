# The image Cloud Run starts. Small, and without any secret:
# the keys are given to Cloud Run, not baked into the image.
FROM python:3.13-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Never run as root inside the container.
RUN useradd --create-home mytravel && chown -R mytravel /app
USER mytravel

# Cloud Run tells the container which port to listen on: $PORT.
CMD exec uvicorn server:app --host 0.0.0.0 --port ${PORT:-8080}
