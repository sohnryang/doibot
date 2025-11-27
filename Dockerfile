# Stage 1: Builder
FROM python:3.12-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Copy dependency definitions
COPY pyproject.toml uv.lock ./

# Export dependencies to requirements.txt
RUN uv export --frozen --no-dev --no-emit-project --format requirements-txt --output-file requirements.txt

# Stage 2: Final
FROM python:3.12-slim

WORKDIR /app

# Copy requirements from builder
COPY --from=builder /app/requirements.txt .

# Install dependencies directly into system python
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Install the application package
RUN pip install --no-cache-dir .

# Run the bot
CMD ["doibot"]
