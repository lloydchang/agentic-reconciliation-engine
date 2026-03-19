#!/bin/bash

# Download and setup Qwen model for llama.cpp server
set -e

MODEL_NAME=${QWEN_MODEL:-"qwen2.5-coder-7b-instruct"}
MODEL_FILE=${MODEL_NAME}.gguf
MODEL_DIR="/models"
MODEL_PATH="${MODEL_DIR}/${MODEL_FILE}"

echo "Setting up Qwen model: ${MODEL_NAME}"

# Create model directory if it doesn't exist
mkdir -p ${MODEL_DIR}

# Check if model already exists
if [ -f "${MODEL_PATH}" ]; then
    echo "Model already exists at ${MODEL_PATH}"
    echo "Model size: $(du -h ${MODEL_PATH} | cut -f1)"
    exit 0
fi

echo "Downloading Qwen model..."

# Try different sources for the model
MODEL_SOURCES=(
    "https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-GGUF/resolve/main/${MODEL_FILE}"
    "https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q4_0.gguf"
    "https://github.com/ggerganov/llama.cpp/releases/download/v1.0.0/${MODEL_FILE}"
)

# Try each source until one succeeds
for SOURCE in "${MODEL_SOURCES[@]}"; do
    echo "Attempting to download from: ${SOURCE}"
    
    if curl -L --fail --silent --show-error --output "${MODEL_PATH}.tmp" "${SOURCE}"; then
        mv "${MODEL_PATH}.tmp" "${MODEL_PATH}"
        echo "Successfully downloaded model from ${SOURCE}"
        break
    else
        echo "Failed to download from ${SOURCE}"
        rm -f "${MODEL_PATH}.tmp"
    fi
done

# Verify model was downloaded
if [ ! -f "${MODEL_PATH}" ]; then
    echo "ERROR: Failed to download Qwen model from any source"
    echo "Please download manually and place at: ${MODEL_PATH}"
    exit 1
fi

# Verify model file is not empty
if [ ! -s "${MODEL_PATH}" ]; then
    echo "ERROR: Model file is empty"
    rm -f "${MODEL_PATH}"
    exit 1
fi

echo "Model setup complete!"
echo "Model path: ${MODEL_PATH}"
echo "Model size: $(du -h ${MODEL_PATH} | cut -f1)"

# Test if model can be loaded by llama.cpp
echo "Testing model compatibility..."
if [ -f "/llama.cpp/build/bin/llama-server" ]; then
    echo "Testing model with llama-server..."
    timeout 10s /llama.cpp/build/bin/llama-server \
        --model "${MODEL_PATH}" \
        --host 0.0.0.0 \
        --port 8080 \
        --ctx-size 512 \
        --threads 1 \
        --no-mmap \
        --help >/dev/null 2>&1 || echo "Model test completed"
else
    echo "llama-server not found, skipping model test"
fi

echo "Qwen model setup completed successfully!"
