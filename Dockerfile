# Use a slim Python base image
FROM python:3.11-slim

# Install Node.js inside the container to execute the MCP filesystems natively
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    && curl -sL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install the MCP filesystems globally inside the container's standard Node path
RUN npm install -g @danielsuguimoto/readonly-server-filesystem @modelcontextprotocol/server-filesystem

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application script
COPY app.py .

# Expose the Flask port
EXPOSE 5001

CMD ["python", "app.py"]