# Use Alpine 3.21.0 as the base image
FROM alpine:3.21.0

# Install necessary dependencies using apk (Alpine package manager)
RUN apk update && apk upgrade && \
    apk add --no-cache \
    curl \
    python3 \
    libmagic \
    && rm -rf /var/cache/apk/*

# Install UV Astra
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Ensure the UV binary is in the PATH by setting it explicitly
ENV PATH="/root/.local/bin:${PATH}"

# Set the working directory for the application
WORKDIR /app

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Copy uv.lock and pyproject.toml before the application code to leverage Docker layer caching
COPY uv.lock pyproject.toml /app/

# Install the project's dependencies using UV Astra's sync command
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Copy the rest of the application code
COPY . /app    

# Expose a port (if your app listens on a port)
EXPOSE 8000

# Set the entrypoint to run your Python application with UV run command
ENTRYPOINT ["uv", "run", "blck.py"]
