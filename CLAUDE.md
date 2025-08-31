# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Jupyter MCP (Model Context Protocol) Server setup project that creates a bridge between Jupyter notebooks and MCP clients like Claude Code and Gemini CLI. The project has a multi-phase setup process and includes automated installation, validation, and runtime management scripts.

## Key Commands

### Installable Package (Recommended)
```bash
# Install once globally or in virtual environment
pip install jupyter-mcp-setup

# Basic usage - one command does everything: install, validate, and start server
jupyter-mcp-setup notebook.ipynb

# With specific port (default is now 8888)
jupyter-mcp-setup notebook.ipynb --port 8889

# With Claude Code integration (default enabled)
jupyter-mcp-setup notebook.ipynb --verbose --claude-config --port-detection-timeout 15

# With Gemini CLI integration
jupyter-mcp-setup notebook.ipynb --gemini-cli --verbose

# With both Claude Code and Gemini CLI integration
jupyter-mcp-setup notebook.ipynb --claude-config --gemini-cli --port 8889

# Force reinstall and skip validation
jupyter-mcp-setup notebook.ipynb --force-reinstall --skip-validation --port 8889

# Advanced usage with all options
jupyter-mcp-setup notebook.ipynb --port 8889 --verbose --fallback-port 8888 --max-port-retries 3
```

### Local Shell Script (Legacy)
```bash
# One command to do everything: install, validate, and start server
./jupyter-mcp-setup.sh notebook.ipynb

# With specific port
./jupyter-mcp-setup.sh notebook.ipynb --port 8889
```

### Individual Components (Advanced Usage)
```bash
# Phase 2: Install and setup the MCP server environment  
./install-jupyter-mcp.sh

# Validate the installation
./validate-setup.sh

# Running the MCP Server directly
python setup-jupyter-mcp.py notebook.ipynb --port 8889 --verbose
```

### Development Commands
```bash
# Activate the virtual environment (manual activation if needed)
source jupyter-mcp-env/bin/activate

# Test package import
python -c "import jupyter_mcp_server; print('Package import: OK')"

# Test CLI functionality  
jupyter-mcp-server --help
jupyter-mcp-server start --help
```

## Architecture Overview

### Core Components

1. **jupyter-mcp-setup (pip package)** - Installable Python package (RECOMMENDED)
   - One-command solution after `pip install jupyter-mcp-setup`
   - No directory clutter: installs cleanly without loose script files
   - Cross-platform: works consistently across different systems
   - Standard Python packaging: follows community best practices
   - Auto dependency management: handles all requirements automatically

2. **jupyter-mcp-setup.sh** - Unified setup script (Legacy)
   - One-command solution: combines installation, validation, and server startup
   - Smart detection: skips installation if environment already exists and is valid
   - Full pass-through: supports all setup-jupyter-mcp.py flags and options
   - Master script flags: `--force-reinstall`, `--skip-validation`

3. **setup-jupyter-mcp.py** - Main orchestrator script (Phase 3)
   - Manages complete lifecycle: validation → Jupyter startup → MCP server startup → configuration generation → process monitoring
   - Contains sophisticated path management, environment variable handling, and Claude Code integration
   - Supports complex notebook path scenarios (relative, absolute, symbolic links, spaces in paths)

4. **Installation Scripts**
   - `install-jupyter-mcp.sh` - Automated installation (Phase 2) 
   - `validate-setup.sh` - Installation validation
   - Creates `jupyter-mcp-env/` virtual environment
   - Installs dependencies from `requirements-jupyter-mcp.txt`

### Key Classes in setup-jupyter-mcp.py

- **PathManager**: Comprehensive path validation and resolution for notebooks, handles relative/absolute paths, validates JSON format
- **ClaudeConfigManager**: Manages Claude Code `.claude/settings.local.json` integration, preserves existing settings
- **GeminiConfigManager**: Manages Gemini CLI `~/.gemini/settings.json` integration, preserves existing settings
- **McpConfigManager**: Manages `.mcp.json` with dynamic editing that preserves existing MCP servers
- **EnvironmentManager**: Advanced environment variable management and validation for MCP server configuration  
- **JupyterMCPSetup**: Main orchestrator class that coordinates all setup phases

### Process Flow

1. **Prerequisites Validation**: Checks Phase 2 installation, virtual environment, notebook validity
2. **Jupyter Lab Startup**: Starts Jupyter with port auto-detection, token extraction, handles port 0 scenarios
3. **MCP Server Startup**: Starts the MCP server with validated environment variables
4. **Configuration Generation**: Creates/updates `.mcp.json` (preserves existing servers) and optionally updates Claude Code and Gemini CLI settings
5. **Process Monitoring**: Monitors both processes with graceful shutdown handling

### Configuration Files Generated

- `.mcp.json` - MCP client configuration with server details (dynamically preserves existing servers)
- `.claude/settings.local.json` - Claude Code specific settings (when `--claude-config` is used)
- `~/.gemini/settings.json` - Gemini CLI specific settings (when `--gemini-cli` is used)
- Configuration includes dynamic Jupyter URL, token, and environment variables

### Port Detection Features

The system includes sophisticated port detection:
- Auto-detection from Jupyter output with configurable timeouts
- Fallback port strategies
- Support for Jupyter's port 0 (auto-select) behavior
- Process inspection using psutil when available
- Common port fallbacks (8888, 8889, 8890, 8080)

### Environment Variables

The MCP server uses these key environment variables:
- `TRANSPORT`: "stdio"
- `PROVIDER`: "jupyter" 
- `DOCUMENT_URL`: Jupyter server URL
- `DOCUMENT_TOKEN`: Jupyter authentication token
- `DOCUMENT_ID`: Relative path to notebook
- `RUNTIME_URL`: Jupyter runtime URL
- `RUNTIME_TOKEN`: Runtime authentication token
- `START_NEW_RUNTIME`: "true"

## File Structure

### Python Package Structure (Recommended)
```
jupyter-mcp-setup/
├── src/
│   └── jupyter_mcp_setup/
│       ├── __init__.py           # Package initialization
│       ├── cli.py                # Command-line interface
│       ├── installer.py          # Installation logic
│       ├── validator.py          # Validation logic
│       ├── server_setup.py       # Server setup and management
│       └── utils.py              # Shared utilities
├── pyproject.toml                # Modern Python packaging config
├── README.md
└── CLAUDE.md                     # This documentation
```

### Legacy Structure
```
jupyter-mcp/
├── jupyter-mcp-setup.sh          # Unified setup script (Legacy)
├── setup-jupyter-mcp.py          # Main setup orchestrator
├── install-jupyter-mcp.sh        # Installation script
├── validate-setup.sh             # Validation script  
├── requirements-jupyter-mcp.txt  # Python dependencies
├── jupyter-mcp-env/              # Virtual environment (created by install)
└── .claude/                      # Claude Code settings (created when --claude-config used)
```

## Development Notes

### Installation Methods
- **Recommended**: Install as Python package with `pip install jupyter-mcp-setup`
- **Legacy**: Use shell scripts for local development or when pip installation isn't preferred

### Requirements
- Python ≥3.10
- Virtual environment isolation (`jupyter-mcp-env/`) for local installations
- All dependencies automatically managed when installed via pip

### Features
- Extensive configuration options for different deployment scenarios
- Robust error handling and process cleanup
- Multi-client support: Claude Code integration (enabled by default) and Gemini CLI integration (optional)
- Dynamic configuration preservation: preserves existing MCP server configurations
- Supports notebooks in various path configurations (current dir, subdirectories, absolute paths)
- Cross-platform compatibility
- Standard Python packaging practices

### Usage Benefits
- **Clean Installation**: No clutter in project directories
- **Easy Updates**: `pip install --upgrade jupyter-mcp-setup`  
- **Dependency Management**: Automatic handling of all requirements
- **System Integration**: Works with virtual environments, conda, etc.