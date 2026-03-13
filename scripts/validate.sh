#!/bin/bash

echo "🚀 Validating Backstage + Temporal Setup..."

# Check if required tools are installed
echo "📋 Checking prerequisites..."

if ! command -v go &> /dev/null; then
    echo "❌ Go is not installed"
    exit 1
else
    echo "✅ Go is installed"
fi

if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed"
    exit 1
else
    echo "✅ Node.js is installed"
fi

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    exit 1
else
    echo "✅ Docker is installed"
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed"
    exit 1
else
    echo "✅ Docker Compose is installed"
fi

# Test backend build
echo ""
echo "🔧 Testing backend build..."
cd backend
if go build -o worker .; then
    echo "✅ Backend builds successfully"
    rm -f worker
else
    echo "❌ Backend build failed"
    exit 1
fi

# Test backend tests
echo "🧪 Testing backend..."
if go test; then
    echo "✅ Backend tests pass"
else
    echo "❌ Backend tests failed"
    exit 1
fi

# Test frontend dependencies
echo ""
echo "📦 Testing frontend dependencies..."
cd ../frontend
if yarn install --silent; then
    echo "✅ Frontend dependencies installed successfully"
else
    echo "❌ Frontend dependency installation failed"
    exit 1
fi

# Check file structure
echo ""
echo "📁 Checking project structure..."
required_files=(
    "backend/main.go"
    "backend/Dockerfile"
    "backend/docker-compose.yml"
    "frontend/package.json"
    "frontend/src/App.tsx"
    "frontend/src/plugins/temporal-integration/index.tsx"
    "scripts/dev.sh"
    "scripts/build.sh"
    "README.md"
    "LICENSE"
)

for file in "${required_files[@]}"; do
    if [ -f "../$file" ]; then
        echo "✅ $file exists"
    else
        echo "❌ $file missing"
        exit 1
    fi
done

echo ""
echo "🎉 All validations passed! The Backstage + Temporal sandbox is ready to use."
echo ""
echo "Next steps:"
echo "1. Start infrastructure: cd backend && docker-compose up -d"
echo "2. Start backend: cd backend && go run main.go"
echo "3. Start frontend: cd frontend && yarn start"
echo "4. Visit http://localhost:3000/temporal to test the integration"
