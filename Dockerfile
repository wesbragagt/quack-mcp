FROM python:3.12-slim

# Install system dependencies for DuckDB and uv
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Create app directory
WORKDIR /app

# Create non-root user
RUN groupadd --gid 1001 appuser && \
    useradd --uid 1001 --gid 1001 --create-home appuser

# Copy project files
COPY pyproject.toml ./
COPY README.md ./

# Install dependencies
RUN uv sync --frozen

# Copy source code
COPY --chown=appuser:appuser src/ ./src/

# Switch to non-root user
USER appuser

# Activate virtual environment and start the application
CMD ["uv", "run", "python", "-m", "quack_mcp.server"]
