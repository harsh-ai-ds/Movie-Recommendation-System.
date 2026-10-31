# Use a lightweight Python base image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Install basic system build essentials (useful for compiling certain Python packages if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker's caching layer
COPY requirements.txt .

# Install Python dependencies without caching to keep the image slim
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files (app.py, templates, static, and .pkl model files) into the container
COPY . /app

# Expose the standard port required by Hugging Face Spaces
EXPOSE 7860

# Run your Flask application
CMD ["python", "app.py"]