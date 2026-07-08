# app.py
from flask import Flask, render_template_string, request, jsonify
import asyncio
import os
import sys
import logging
import re
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import ollama

# Configure clean console logging for your container environment
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Absolute container directory mappings
RO_DIR = "/app/mcp-data/ReadOnlyDocs"
RW_DIR = "/app/mcp-data/ActiveWorkspace"

# Points to standard global Node installation locations inside Linux containers
RO_PARAMS = StdioServerParameters(
    command="node", 
    args=["/usr/lib/node_modules/@danielsuguimoto/readonly-server-filesystem/dist/index.js", RO_DIR]
)
RW_PARAMS = StdioServerParameters(
    command="node", 
    args=["/usr/lib/node_modules/@modelcontextprotocol/server-filesystem/dist/index.js", RW_DIR]
)

# Host machine bridge initialization
ollama_client = ollama.Client(host='http://host.docker.internal:11434')

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MCP File System Agent</title>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
            background: #e2e4e7; 
            margin: 0; 
            padding: 0; 
            color: #1d1d1f;
            display: flex;
            height: 100vh;
            overflow: hidden;
        }
        .left-pane {
            flex: 1;
            padding: 40px;
            overflow-y: auto;
            border-right: 1px solid #c8ccd0;
            background: #f4f5f6;
            box-sizing: border-box;
        }
        .right-pane {
            flex: 1;
            padding: 40px;
            overflow-y: auto;
            background: #eef0f2;
            box-sizing: border-box;
            display: flex;
            flex-direction: column;
        }
        h1 { margin-top: 0; font-weight: 600; color: #111; font-size: 28px; margin-bottom: 30px; }
        h2 { margin-top: 0; font-weight: 500; color: #111; font-size: 20px; border-bottom: 1px solid #c8ccd0; padding-bottom: 10px; }
        label { font-weight: 500; display: block; margin-bottom: 5px; color: #424245; }
        textarea { width: 100%; height: 120px; padding: 12px; border: 1px solid #b0b5bb; border-radius: 8px; font-size: 16px; box-sizing: border-box; resize: vertical; margin-bottom: 15px; background: #ffffff; color: #1d1d1f; }
        textarea:focus { border-color: #0071e3; outline: none; }
        select { padding: 10px; font-size: 16px; border: 1px solid #b0b5bb; border-radius: 8px; background: #ffffff; color: #1d1d1f; margin-bottom: 20px; width: 100%; }
        select:focus { border-color: #0071e3; outline: none; }
        button { background: #0071e3; color: white; border: none; padding: 12px 24px; font-size: 16px; border-radius: 8px; cursor: pointer; font-weight: 500; width: 100%; }
        button:hover { background: #0077ed; }
        .status { margin-top: 20px; font-weight: bold; color: #0071e3; display: none; }
        .log-box { margin-top: 25px; background: #1d1d1f; color: #f5f5f7; padding: 20px; border-radius: 8px; font-family: "SFMono-Regular", Consolas, monospace; white-space: pre-wrap; font-size: 14px; max-height: 350px; overflow-y: auto; display: none; line-height: 1.5; }
        .preview-box {
            flex: 1;
            background: #ffffff;
            border: 1px solid #c8ccd0;
            border-radius: 8px;
            padding: 24px;
            font-size: 16px;
            line-height: 1.6;
            white-space: pre-wrap;
            overflow-y: auto;
            color: #333;
        }
        .empty-state {
            color: #86868b;
            font-style: italic;
            text-align: center;
            margin-top: 40px;
        }
    </style>
</head>
<body>

<div class="left-pane">
    <h1>MCP File System Agent</h1>
    
    <label for="model">Select Local Model:</label>
    <select id="model">
        <option value="llama3.3">Llama 3.3</option>
        <option value="gemma4">Gemma 4</option>
    </select>

    <label for="prompt">Your Command / Prompt:</label>
    <textarea id="prompt" placeholder="e.g., Read file sample.txt from ReadOnlyDocs, summarize it, and write it to summary.md in ActiveWorkspace."></textarea>
    
    <button onclick="submitPrompt()">Run</button>
    
    <div id="status" class="status">📦 Processing local filesystem operations inside Docker sandbox...</div>
    <div id="output" class="log-box"></div>
</div>

<div class="right-pane">
    <h2>Output Content Preview</h2>
    <div id="preview" class="preview-box">
        <div class="empty-state">Trigger an execution loop to populate output text response context...</div>
    </div>
</div>

<script>
    function submitPrompt() {
        const promptValue = document.getElementById('prompt').value;
        const modelValue = document.getElementById('model').value;
        const statusDiv = document.getElementById('status');
        const outputDiv = document.getElementById('output');
        const previewDiv = document.getElementById('preview');
        
        if(!promptValue.trim()) { alert('Please enter a prompt.'); return; }
        
        statusDiv.style.display = 'block';
        outputDiv.style.display = 'none';
        outputDiv.textContent = '';
        previewDiv.innerHTML = '<div class="empty-state">Generating workspace files...</div>';
        
        fetch('/run-agent', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ prompt: promptValue, model: modelValue })
        })
        .then(res => res.json())
        .then(data => {
            statusDiv.style.display = 'none';
            outputDiv.style.display = 'block';
            
            if (data.status === 'success') {
                outputDiv.textContent = data.logs;
                
                let rawContent = data.content || "File successfully generated without terminal output text.";
                rawContent = rawContent.replace(/^```[a-zA-Z0-9]*\\s*/, '');
                rawContent = rawContent.replace(/\\s*```$/, '');
                
                previewDiv.textContent = rawContent.trim();
            } else {
                outputDiv.textContent = '❌ Error:\\n' + data.error;
                previewDiv.innerHTML = `<div class="empty-state" style="color: #ff3b30;">❌ Workflow Stopped:<br>${data.error}</div>`;
            }
        })
        .catch(err => {
            statusDiv.style.display = 'none';
            outputDiv.style.display = 'block';
            outputDiv.textContent = '❌ Network Error: ' + err.message;
            previewDiv.innerHTML = '<div class="empty-state" style="color: #ff3b30;">❌ Network execution failed.</div>';
        });
    }
</script>
</body>
</html>
"""

def extract_target_filename(prompt_text):
    match = re.search(r'(?:names|file|to|create)\s+([a-zA-Z0-9_\-\.]+)', prompt_text, re.IGNORECASE)
    if match:
        filename = match.group(1).strip()
        filename = filename.rstrip('.')
        if '.' in filename:
            return filename
    return "summary.md"

def build_recursive_file_tree(base_directory):
    """
    Recursively maps directories, subfolders, and files down the system path tree,
    mirroring the comprehensive structural overview behavior of 'ls -lR'.
    """
    if not os.path.exists(base_directory):
        return {}
    
    tree_map = {}
    for root, dirs, files in os.walk(base_directory):
        # Calculate the relative structural root path anchor point inside the volume mount
        relative_path = os.path.relpath(root, base_directory)
        current_node = "." if relative_path == "." else relative_path
        
        tree_map[current_node] = {
            "subfolders": sorted(dirs),
            "files": sorted(files)
        }
    return tree_map

async def execute_mcp_workflow(user_prompt, model_name):
    logs = []
    llm_response = ""
    
    target_file = extract_target_filename(user_prompt)
    logs.append("⚙️ Initialize: Starting localized Model Context Protocol handler...")
    logs.append(f"🎯 Target File Identified: '{target_file}'")
    
    # Perform deep-recursive directory scans matching 'ls -lR'
    ro_tree = build_recursive_file_tree(RO_DIR)
    rw_tree = build_recursive_file_tree(RW_DIR)
    
    # Log the complete structural layout mapped out for transparency inside the dashboard box
    logs.append(f"📁 Deep-Scan [ReadOnlyDocs]: {list(ro_tree.keys())}")
    logs.append(f"📁 Deep-Scan [ActiveWorkspace]: {list(rw_tree.keys())}")

    file_contents = ""
    sample_path = os.path.join(RO_DIR, "sample.txt")
    if os.path.exists(sample_path):
        with open(sample_path, "r", encoding="utf-8") as f:
            file_contents = f.read()
            
    system_instruction = (
        "SYSTEM CONTEXT ENVIRONMENT RULES:\n"
        f"1. The FULL recursive directory tree map for 'ReadOnlyDocs' is: {ro_tree}\n"
        f"2. The FULL recursive directory tree map for 'ActiveWorkspace' is: {rw_tree}\n"
        f"3. You are performing an action to populate the file: '{target_file}'.\n"
        "4. Output only the content intended to live inside the file. Do not wrap the text response in explanation commentary unless desired inside the document."
    )

    logs.append(f"🧠 LLM Engine: Sending prompt parameters to local core ({model_name})...")
    ollama_prompt = (
        f"{system_instruction}\n\n"
        f"Sample File Text Content Reference:\n{file_contents}\n\n"
        f"User Instruction:\n{user_prompt}"
    )
    
    try:
        response = ollama_client.chat(
            model=model_name,
            messages=[{'role': 'user', 'content': ollama_prompt}]
        )
        llm_response = response['message']['content']
        logs.append("✨ LLM Engine: Secure generation block complete.")
    except Exception as e:
        logger.error("Failed connection chain to host machine loopback network: %s", str(e))
        raise RuntimeError(f"Ollama Unreachable: Ensure Ollama is running on your Mac Mini. Details: {e}")

    logs.append("💾 Pipeline: Opening write connection channel to ActiveWorkspace host...")
    try:
        async with stdio_client(RW_PARAMS) as (rw_r, rw_w):
            async with ClientSession(rw_r, rw_w) as rw_session:
                await asyncio.wait_for(rw_session.initialize(), timeout=10.0)
                
                await rw_session.call_tool("write_file", {
                    "path": target_file,
                    "content": llm_response
                })
        
        logs.append("\n==============================================")
        logs.append("🎉 SUCCESS: FILE PERSISTENCE WORKING")
        logs.append(f"📁 Folder Location : ActiveWorkspace")
        logs.append(f"📄 Generated File   : {target_file}")
        logs.append("==============================================")
        
    except Exception as mcp_err:
        logger.warning("ActiveWorkspace standard execution crashed: %s. Attempting native fallback save...", str(mcp_err))
        logs.append(f"⚠️ Channel Warning: Write server busy ({str(mcp_err)}). Routing via fallback container pipeline...")
        
        os.makedirs(RW_DIR, exist_ok=True)
        with open(os.path.join(RW_DIR, target_file), "w", encoding="utf-8") as f:
            f.write(llm_response)
            
        logs.append("\n==============================================")
        logs.append("🎉 SUCCESS: SECURED VIA CONTAINER FALLBACK")
        logs.append(f"📁 Folder Location : ActiveWorkspace (Direct Volume)")
        logs.append(f"📄 Generated File   : {target_file}")
        logs.append("==============================================")

    return "\n".join(logs), llm_response

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/run-agent', methods=['POST'])
def run_agent():
    data = request.json or {}
    user_prompt = data.get('prompt', '').strip()
    model_name = data.get('model', 'gemma4')
    
    if not user_prompt:
        return jsonify({"status": "error", "error": "User prompt cannot be empty."}), 400
        
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            execution_logs, response_content = loop.run_until_complete(execute_mcp_workflow(user_prompt, model_name))
            return jsonify({
                "status": "success", 
                "logs": execution_logs,
                "content": response_content
            })
        finally:
            loop.close()
    except RuntimeError as system_runtime_err:
        return jsonify({"status": "error", "error": str(system_runtime_err)}), 500
    except Exception as broad_uncaught_err:
        return jsonify({"status": "error", "error": f"Internal System Malfunction: {broad_uncaught_err}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)
