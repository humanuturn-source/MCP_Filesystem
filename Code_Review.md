
# High-Level Summary 

This script builds a localized, web-based Model Context Protocol (MCP) File System Agent dashboard. It allows a user to interact with sandboxed filesystem directories on a local machine using open-weights LLMs via Ollama.
The application can be broken down into three core layers:

## 1. User Interface Layer (HTML_TEMPLATE)
•	Dual-Pane Web Dashboard: Provides a clean, split-screen web browser interface using Flask's render_template_string.
•	Left Control Panel: Contains a model selection dropdown (supporting models like Llama 3.3 and Gemma 4) and an asynchronous prompt execution terminal to send natural language directives.
•	Right Preview Panel: Live-renders the final document generation dynamically once the background execution cycle finishes.

## 2. Environment Mapping Layer (build_recursive_file_tree)
•	Deep Directory Scanning: Utilizes Python's native os.walk function to act like a recursive Unix ls -lR command.
•	Tree Mapping: Before any prompt is processed, it maps out the entire nested subdirectory structural layouts inside the isolated paths (ReadOnlyDocs and ActiveWorkspace). This ensures the underlying local LLM is fully aware of folders and files hidden deep inside subdirectories.


## 3. Orchestration & Execution Layer (execute_mcp_workflow)
•	Prompt Engineering injection: Combines the user's natural language command, the full recursive directory tree map, a target output file parser, and any default context references (like a base text file) into a structured instructions payload.
•	Local Inference Integration: Forwards this context payload to the host machine's native Ollama service using Docker's internal networking bridge (http://host.docker.internal:11434) to perform local text generation safely offline.
•	MCP Tool Operations: Leverages an asynchronous protocol client connection loop to natively trigger write_file tool call bindings via the official Model Context Protocol server packages.
•	Robust Saving Fallback: If the active workspace's MCP pipe communication drops or encounters a conflict, the script safely catches the exception and routes the text file save directly through the standard containerized volume mount path so no workflow outputs are lost.
