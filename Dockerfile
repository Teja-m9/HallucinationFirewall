FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Create upload directory
RUN mkdir -p data/uploads

# Expose port 7860 (Hugging Face default)
EXPOSE 7860

# Start the server
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "7860"]
