FROM python:3.10-slim as base

# Install SQLite 3.31 or later
RUN apt-get update && \
    apt-get install -y --no-install-recommends sqlite3 libsqlite3-dev && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port
EXPOSE 8000

# Command to run the application
CMD ["gunicorn", "myproject.wsgi:application", "-b", "0.0.0.0:8000"]