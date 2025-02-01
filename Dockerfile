# Use Python 3.9 for better compatibility with TensorFlow and Magenta
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libasound2-dev \
    libjack-dev \
    portaudio19-dev \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python packages in order of dependency
RUN pip install --no-cache-dir numpy==1.23.5 \
    && pip install --no-cache-dir tensorflow==2.9.1 \
    && pip install --no-cache-dir protobuf==3.19.6 \
    && pip install --no-cache-dir six==1.16.0 \
    && pip install --no-cache-dir absl-py==1.2.0 \
    && pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PORT=5001

# Expose the port
EXPOSE $PORT

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "app:app"]
