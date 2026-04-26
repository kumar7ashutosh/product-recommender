# Parent image
FROM python:3.10-slim

# Env vars
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Workdir
WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 🔥 Copy only requirements first (for caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy full project
COPY . .

# (Optional) If you still want editable install
RUN pip install --no-cache-dir -e .

# Expose port
EXPOSE 5000

# Run app
CMD ["python", "app.py"]