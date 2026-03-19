# Dockerfile for llama.cpp server with Qwen model
FROM ubuntu:22.04

# Install dependencies
RUN apt-get update && apt-get install -y \
    git \
    cmake \
    build-essential \
    libcurl4-openssl-dev \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Clone and build llama.cpp
RUN git clone https://github.com/ggerganov/llama.cpp.git /llama.cpp
WORKDIR /llama.cpp
RUN mkdir build && cd build && cmake .. -DLLAMA_CURL=ON && make -j$(nproc) llama-server

# Download Qwen model (you may want to use a specific model file)
# For now, we'll create a placeholder and assume the model will be mounted
RUN mkdir -p /models

# Expose the server port
EXPOSE 8080

# Set environment variables
ENV LLAMA_CPP_MODEL_PATH=/models/qwen2.5-coder-7b-instruct.gguf
ENV LLAMA_CPP_HOST=0.0.0.0
ENV LLAMA_CPP_PORT=8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the server
CMD ["./build/bin/llama-server", \
     "--model", "/models/qwen2.5-coder-7b-instruct.gguf", \
     "--host", "0.0.0.0", \
     "--port", "8080", \
     "--ctx-size", "2048", \
     "--threads", "4"]
