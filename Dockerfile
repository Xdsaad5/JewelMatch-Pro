FROM ubuntu:22.04

ENV ACCEPT_EULA=Y
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies and MS SQL ODBC driver
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    unixodbc \
    unixodbc-dev \
    gnupg2 \
    apt-transport-https \
    curl \
    # OpenCV dependencies
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 && \
    curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/ubuntu/22.04/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    apt-get install -y msodbcsql18 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip3 install --default-timeout=100 -r requirements.txt

# Copy application code
COPY app.py .
COPY image.py .
COPY image_matcher.py .
COPY templates/img-detector.html /app/templates/

# Create necessary folders
RUN mkdir -p /app/templates /app/static/matched_images

EXPOSE 5000

CMD ["python3", "app.py"]
