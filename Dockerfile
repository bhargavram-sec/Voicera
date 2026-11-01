# Use lightweight Python 3.11 image
FROM python:3.11-slim

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies (FFmpeg is mandatory for audio/video processing)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependency specifications first to leverage Docker layer caching
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Ensure working directories exist
RUN mkdir -p uploads outputs temp

# Expose default port
EXPOSE 9090

# Run with Gunicorn on dynamic PORT
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-9090} --workers 1 --threads 4 --timeout 300 app:app"]
