# Use Python 3.9 slim image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies for llama-cpp-python
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY agent.py ./
COPY enhanced-agent.py ./
COPY dashboard.py ./
COPY knowledge-base.md ./

# Create non-root user
RUN useradd -r -s /bin/false memoryagent && \
    mkdir -p /data && \
    chown memoryagent:memoryagent /data

# Switch to non-root user
USER memoryagent

EXPOSE 8080

# Run the agent
CMD ["python", "agent.py"]
