FROM python:3.9-slim-buster

# Install dependencies for building the rpi-rgb-led-matrix library
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    python3-dev \
    python3-pillow \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Clone the rpi-rgb-led-matrix repository
RUN git clone https://github.com/hzeller/rpi-rgb-led-matrix.git

# Build and install the Python bindings
WORKDIR /app/rpi-rgb-led-matrix
RUN make build-python
RUN make install-python

# Return to app directory
WORKDIR /app

# Copy requirements file
COPY requirements-pi.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-pi.txt

# Copy the application code
COPY . .

# Create runtime_artifacts directory if it doesn't exist
RUN mkdir -p runtime_artifacts

# Run the application
CMD ["python", "run.py"]
