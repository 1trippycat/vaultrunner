# Multi-stage Dockerfile for VaultRunner
# Optimized for security and minimal attack surface

# Build stage
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user for security
RUN groupadd -r vaultrunner && useradd -r -g vaultrunner vaultrunner

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim as production

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    jq \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    jq \
    ca-certificates \
    gnupg \
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

# Install Vault CLI
RUN curl -fsSL https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" > /etc/apt/sources.list.d/hashicorp.list \
    && apt-get update \
    && apt-get install -y vault \
    && rm -rf /var/lib/apt/lists/*

# Create app user for security
RUN groupadd -r vaultrunner && useradd -r -g vaultrunner vaultrunner

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder stage
COPY --from=builder /root/.local /home/vaultrunner/.local

# Copy application code
COPY --chown=vaultrunner:vaultrunner . .

# Make sure the user can access their local packages
ENV PATH="/home/vaultrunner/.local/bin:$PATH"

# Make shell wrapper executable
RUN chmod +x vaultrunner

# Create .vault directory with proper permissions
RUN mkdir -p /app/.vault && chown vaultrunner:vaultrunner /app/.vault

# Switch to non-root user
USER vaultrunner

# Set default command
ENTRYPOINT ["./vaultrunner"]
CMD ["--help"]

# Metadata
LABEL maintainer="VaultRunner Team <team@vaultrunner.dev>"
LABEL description="HashiCorp Vault Docker Integration Tool"
LABEL version="1.0.0"