# Use Python 3.11 slim image as base
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_CACHE_DIR=/app/.uv-cache \
    PATH="/root/.local/bin:${PATH}"

# Install system dependencies and uv (Astral version)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/install.sh | sh

# Copy uv configuration files
COPY pyproject.toml uv.lock ./

# Install dependencies into system env
RUN uv sync --frozen 
# Copy application code
COPY backend/ ./backend

# Expose port (FastAPI default)
EXPOSE 8000

# Run the application using uv
CMD ["uv", "run", "backend/main.py"]
