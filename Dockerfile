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

# Copy requirements file
COPY requirements.txt ./

# Install base dependencies first
RUN pip install --no-cache-dir \
    numpy \
    typing_extensions \
    six==1.16.0 \
    Pillow==9.2.0

# Install tensorflow separately to handle its dependencies
RUN pip install --no-cache-dir tensorflow==2.13.0

# Install remaining Python packages
RUN pip install --no-cache-dir -r requirements.txt

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
