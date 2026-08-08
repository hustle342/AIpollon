AIPOLLON is a self-building AI agent that investigates and resolves technical issues encountered on the Windows 11 operating system (e.g., a missing Bluetooth adapter), and transforms these solutions into permanent Model Context Protocol (MCP) tools.

Unlike traditional, fragile "screen-reading and mouse-clicking" agents, WinForge AI operates at the native level, directly utilizing PowerShell and WMI (Windows Management Instrumentation) architectures just like a real System Administrator.
🚀 Key Features

    GUI Independent (Native OS Interaction): It is completely unaffected by resolution changes or Windows UI updates. All operations are managed via CLI, the Registry, and WMI.

    Autonomous MCP Generation (Self-Building Toolset): When the agent solves a problem for the first time (e.g., resetting Bluetooth drivers), it doesn't just run the script; it autonomously converts it into a @mcp.tool() function. If a "Device Manager MCP" doesn't exist, it creates one from scratch; if it does, it appends the new capability as a tool inside it.

    Safety Net and Rollback: Right before making a permanent change to the system (such as deleting a driver or modifying a registry key), an automatic rollback point (Rollback Script / System Restore Point) is created. In the event of an error, the system reverts to its previous state.

    Future-Ready (Multi-Agent Fleet): The generated MCPs are designed to be exportable in a standardized JSON/Python format. This allows for future knowledge and capability sharing with other agents or different Windows devices.

🧠 System Architecture (How It Works)

    Request and Research: The user tells the agent, "Bluetooth is not showing up in the action center." The agent researches PowerShell/WMI-based solution strategies via RAG or web search.

    Solution Generation (Scripting): It autonomously writes a Windows PowerShell or Python-based remediation script (e.g., Restart-Service bthserv).

    Safety Check (Rollback): A safety script is prepared to reverse the operation (or back up the system state).

    MCP Synthesis: Using FastMCP, the working script is converted into a standard Model Context Protocol server. It is permanently added to the relevant category (e.g., device_manager_mcp.py).

    Integration and Execution: The new MCP is added to the agent's configuration, and the tool is used to solve the user's problem. The agent has now permanently "learned" how to reset Bluetooth.

🛠️ Installation (Development Setup)

The project is designed to run fully autonomously on your local machine using a local LLM (e.g., Qwen 2.5 Coder via Ollama).
Requirements

    Windows 11 Operating System

    Python 3.10+

    Administrator privileges

    FastMCP and mcp packages for development

Bash

# Clone the repository
git clone https://github.com/hustle342/aipollon.git
cd aipollon

# Create and activate a virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
