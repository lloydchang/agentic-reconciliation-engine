# Pi-Mono Agent Dockerfile (Multi-Arch Optimized)
# Third agent execution method alongside Temporal and other containers

FROM node:18-alpine

# Install system dependencies
RUN apk add --no-cache \
    git \
    curl \
    bash \
    ca-certificates \
    python3 \
    make \
    g++ \
    && rm -rf /var/cache/apk/*

# Create app directory
WORKDIR /app

# Install pi-mono globally
RUN npm install -g @mariozechner/pi-coding-agent \
    && npm cache clean --force

# Create pi-mono user and directories
RUN addgroup -g 1001 -S pi \
    && adduser -S pi -u 1001 -G pi \
    && mkdir -p /home/pi/.pi/agent/{skills,extensions,prompts,themes,sessions} \
    && mkdir -p /workspace \
    && mkdir -p /logs

# Set ownership
RUN chown -R pi:pi /home/pi \
    && chown -R pi:pi /workspace \
    && chown -R pi:pi /logs

# Switch to non-root user
USER pi

# Set environment
ENV HOME=/home/pi
ENV PI_WORKSPACE_DIR=/workspace
ENV NODE_ENV=production

# Copy configuration
COPY --chown=pi:pi config/ /home/pi/.pi/agent/

# Copy GitOps integration skills
COPY --chown=pi:pi skills/ /home/pi/.pi/agent/skills/

# Set working directory
WORKDIR /workspace

# Health check for RPC mode
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD echo '{"type":"ping"}' | timeout 5 pi --mode rpc --no-session >/dev/null 2>&1 || exit 1

# Expose RPC port
EXPOSE 8080

# Default command - RPC mode for container integration
CMD ["pi", "--mode", "rpc", "--no-session", "--session-dir", "/home/pi/.pi/agent/sessions"]
