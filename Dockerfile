# Use official Python 3.12 base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system packages for native libs (lxml, pymupdf, pdf2image etc.)
RUN apt-get update && apt-get install -y \
    build-essential \
    libxml2-dev \
    libxslt1-dev \
    libgl1-mesa-glx \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of the app code
COPY . .

# Run with gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:app"]
