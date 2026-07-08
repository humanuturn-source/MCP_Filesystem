docker build -t mcp-web-agent .

docker run -d \
  -p 5001:5001 \
  -v ./mcp-data/ReadOnlyDocs:/app/mcp-data/ReadOnlyDocs \
  -v ./mcp-data/ActiveWorkspace:/app/mcp-data/ActiveWorkspace \
  --name running-mcp-agent \
  mcp-web-agent

