FROM python:3.9-slim as base

# Install system dependencies and build tools
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libssl-dev \
    libffi-dev \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    cython3 \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip, install setuptools, and wheel
RUN pip install --upgrade pip
RUN pip install setuptools wheel

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install dependencies with verbose logging
RUN pip install -v --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port
EXPOSE 8000

# Command to run the application
CMD ["gunicorn", "myproject.wsgi:application", "-b", "0.0.0.0:8000"]
