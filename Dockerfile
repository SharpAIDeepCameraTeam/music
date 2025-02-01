# Use Python 3.9 for better compatibility with TensorFlow and Magenta
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libasound2-dev \
    libjack-dev \
    portaudio19-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt ./

# Install numpy and typing_extensions first
RUN pip install --no-cache-dir numpy typing_extensions

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PORT=5001

# Expose the port
EXPOSE $PORT

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "app:app"]
