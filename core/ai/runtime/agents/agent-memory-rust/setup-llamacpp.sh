#!/bin/bash

# LLaMA.cpp Setup Script for Agent Memory Service
set -e

echo "Setting up LLaMA.cpp for Agent Memory Service..."

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Configuration
MODEL_NAME=${MODEL_NAME:-"qwen2.5-0.5b-instruct"}
MODEL_DIR=${MODEL_DIR:-"/models"}
LLAMACPP_DIR=${LLAMACPP_DIR:-"/opt/llama.cpp"}
PORT=${PORT:-8080}

# Create model directory
mkdir -p "$MODEL_DIR"

echo "Downloading Qwen model in GGUF format..."
# Download Qwen model in GGUF format
if [ ! -f "$MODEL_DIR/${MODEL_NAME}.gguf" ]; then
    echo "Model file not found. Downloading Qwen2.5-0.5B-Instruct GGUF..."
    # Download from Hugging Face
    wget https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_0.gguf \
        -O "$MODEL_DIR/qwen2.5-0.5b-instruct.gguf" || {
        echo "Failed to download model. Please download manually:"
        echo "wget https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_0.gguf -O $MODEL_DIR/qwen2.5-0.5b-instruct.gguf"
        exit 1
    }
    echo " Model downloaded successfully"
else
    echo " Model already exists: $MODEL_DIR/qwen2.5-0.5b-instruct.gguf"
fi

# Install LLaMA.cpp if not present
if [ ! -d "$LLAMACPP_DIR" ]; then
    echo "Installing LLaMA.cpp..."
    git clone https://github.com/ggml-org/llama.cpp.git "$LLAMACPP_DIR"
    cd "$LLAMACPP_DIR"
    
    # Build LLaMA.cpp
    echo "Building LLaMA.cpp..."
    make clean
    
    # Check for CUDA support
    if command -v nvcc &> /dev/null; then
        echo "Building with CUDA support..."
        make LLAMA_CUBLAS=1
    else
        echo "Building CPU-only version..."
        make
    fi
    
    echo " LLaMA.cpp built successfully"
    cd "$SCRIPT_DIR"
else
    echo " LLaMA.cpp already installed"
fi

# Create LLaMA.cpp server startup script
cat > "$SCRIPT_DIR/start-llamacpp-server.sh" << 'EOF'
#!/bin/bash
# LLaMA.cpp Server Startup Script

MODEL_PATH="$1"
PORT="${2:-8080}"
HOST="${3:-127.0.0.1}"
CTX_SIZE="${4:-4096}"
N_GPU_LAYERS="${5:-99}"

if [ -z "$MODEL_PATH" ]; then
    echo "Usage: $0 <model_path> [port] [host] [ctx_size] [n_gpu_layers]"
    exit 1
fi

if [ ! -f "$MODEL_PATH" ]; then
    echo "Error: Model file not found: $MODEL_PATH"
    exit 1
fi

LLAMACPP_DIR="/opt/llama.cpp"
if [ ! -f "$LLAMACPP_DIR/llama-server" ]; then
    echo "Error: llama-server not found. Please run setup-llamacpp.sh first."
    exit 1
fi

echo " Starting LLaMA.cpp server..."
echo " Model: $MODEL_PATH"
echo " Host: $HOST"
echo " Port: $PORT"
echo " Context Size: $CTX_SIZE"
echo " GPU Layers: $N_GPU_LAYERS"
echo ""
echo " API will be available at: http://$HOST:$PORT"
echo " Chat completions: http://$HOST:$PORT/v1/chat/completions"
echo " Health check: http://$HOST:$PORT/health"
echo ""

# Start the server
exec "$LLAMACPP_DIR/llama-server" \
    -m "$MODEL_PATH" \
    --host "$HOST" \
    --port "$PORT" \
    --ctx-size "$CTX_SIZE" \
    --n-gpu-layers "$N_GPU_LAYERS" \
    --threads 4 \
    --temp 0.7 \
    --batch-size 512 \
    -c 2048 \
    "$@"
EOF

chmod +x "$SCRIPT_DIR/start-llamacpp-server.sh"

# Create environment configuration
cat > "$SCRIPT_DIR/.env.llamacpp" << EOF
# LLaMA.cpp Configuration
LLAMACPP_API_URL=http://localhost:8080
LLAMACPP_MODEL=qwen2.5:0.5b

# Backend Priority (llamacpp should be first for local inference)
BACKEND_PRIORITY=llamacpp,openai,ollama

# Qwen Configuration (for fallback)
QWEN_MODEL=qwen2.5:0.5b
QWEN_API_KEY=agent-memory-api-key

# Model path for startup script
MODEL_PATH=$MODEL_DIR/qwen2.5-0.5b-instruct.gguf
EOF

echo ""
echo " LLaMA.cpp setup completed!"
echo ""
echo " Next steps:"
echo ""
echo "1. Start the LLaMA.cpp server:"
echo "   ./start-llamacpp-server.sh $MODEL_DIR/qwen2.5-0.5b-instruct.gguf"
echo ""
echo "2. Test the API:"
echo "   curl http://localhost:8080/health"
echo "   curl http://localhost:8080/v1/chat/completions \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"model\":\"qwen2.5:0.5b\",\"messages\":[{\"role\":\"user\",\"content\":\"Hello!\"}]}'"
echo ""
echo "3. Configure Agent Memory Service:"
echo "   cp .env.llamacpp .env"
echo "   cargo run"
echo ""
echo " Server options:"
echo "   ./start-llamacpp-server.sh <model> [port] [host] [ctx_size] [gpu_layers]"
echo "   ./start-llamacpp-server.sh $MODEL_DIR/qwen2.5-0.5b-instruct.gguf 8080 127.0.0.1 4096 99"
echo ""
echo " More info: https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md"
