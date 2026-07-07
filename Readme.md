# 📦 Deep-Dive: Building a Local Dockerized MCP File System Agent
This guide walks you through setting up a web-based agent dashboard that safely interfaces with local, sandboxed file volumes strictly using the **Model Context Protocol (MCP)** and local open-weights LLMs via **Ollama**.

---

## 🛠️ Prerequisites
Before starting, ensure your local system has the following installed:
* **Docker Desktop** (running and configured)
* **Ollama** (installed natively on your host machine)
* A text editor or IDE (e.g., VS Code or Cursor)

---

## 📂 Step 1: Project Architecture Setup
Create a dedicated project directory on your host machine and establish the isolation folders required for the read-only referencing and active workspace directories.

Open your terminal and run:

```bash
mkdir -p local-mcp-agent/mcp-data/ActiveWorkspace
mkdir -p local-mcp-agent/mcp-data/ReadOnlyDocs
cd local-mcp-agent
```

Your resulting folder structure will look like this:
local-mcp-agent/
├── app.py              # Flask Web Interface & Agent Logic
├── Dockerfile          # Linux Image Construction Layers
├── requirements.txt    # Frozen Python Dependencies
├── run_docker.sh       # Automation Container Management Script
└── mcp-data/
    ├── ActiveWorkspace/ # Target directory for agent file output modifications
    └── ReadOnlyDocs/    # Guarded storage folder containing context material (e.g., sample.txt)

---

📦 Step 2: Define Dependencies (requirements.txt)
Create a requirements.txt file in the root of your project folder to explicitly lock down core libraries inside the container ecosystem:

```text
flask==3.0.3
mcp==0.1.0
ollama==0.2.1
```
---

🐋 Step 3: Build the Container Environment (Dockerfile)
Create a file named Dockerfile in your root directory. This configures a multi-runtime container layer initializing Python, installing Node.js natively, and fetching the official global Model Context Protocol filesystem packages.


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
    
---

🚀 Step 4: Write Your Flask Application (app.py)
Create your app.py script. This script automatically handles natural-language extraction of file targets from the web dashboard panel, builds state mapping updates via terminal logs, and executes MCP tools natively.

You can copy the file app.py from the link in the description. 

---

⚡ Step 5: Automate Orchestration (run_docker.sh)
Create an automation file called run_docker.sh to quickly tear down existing test container instances, rebuild current changes, and mount local directory paths cleanly.

```bash
    docker build -t mcp-web-agent .

    docker run -d \
    -p 5001:5001 \
    -v ./mcp-data/ReadOnlyDocs:/app/mcp-data/ReadOnlyDocs \
    -v ./mcp-data/ActiveWorkspace:/app/mcp-data/ActiveWorkspace \
    --name running-mcp-agent \
    mcp-web-agent

```

Make your shell script executable by executing the following in your terminal:
chmod +x run_docker.sh

---

🖥️ Step 6: Verify and Run Your Local System
1. Ensure Ollama is running on your host machine.
2. In your project directory, execute the shell script: ./run_docker.sh
3. Open http://localhost:5001 in any web browser to view the interface.
4. Try dropping a text file (e.g., sample.txt) into your local mcp-data/ReadOnlyDocs folder, and prompt the agent loop to extract or summarize data directly into a custom filename inside your active workspace.

---

🛠️ Crucial Local Network Troubleshooting
1. Ollama Connection Error (Unreachable Core)
Because the Flask engine runs inside an isolated Docker network, it cannot use localhost:11434 to reach your machine's native Ollama service.
• The Fix: Your script utilizes the special loopback routing handle http://host.docker.internal:11434.
• Mac / Windows Users: Ensure your native desktop settings allow host machine requests.
• Linux Users: If using native Linux configurations, add --add-host=host.docker.internal:host-gateway to your docker run command string within run_docker.sh.
2. Ollama "Origin Not Allowed" Errors
If your Docker app fails to get text generations from Ollama, the local Ollama daemon is likely filtering out container origin calls.
• The Fix: You must launch Ollama with the environment filter open to external bindings. Stop Ollama, and restart it from your terminal using the following environment variable override: OLLAMA_ORIGINS="*" ollama serve
