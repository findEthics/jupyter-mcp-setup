# Jupyter MCP Setup

A unified setup tool for Jupyter MCP (Model Context Protocol) servers with Claude Code integration.

## Overview

This tool provides a streamlined way to set up and manage Jupyter MCP servers that create a bridge between Jupyter notebooks and MCP clients like Claude Code. It combines installation, validation, and server management into a single command.

## Installation

### Recommended: Install as Python Package

```bash
pip install jupyter-mcp-setup
```

This installs the tool globally and provides a clean `jupyter-mcp-setup` command without cluttering your project directories.

### Alternative: Local Development

```bash
git clone <repository>
cd jupyter-mcp
./install-jupyter-mcp.sh
```

## Quick Start

After installation, use the unified command:

```bash
# Basic usage - one command does everything
jupyter-mcp-setup notebook.ipynb

# With specific port
jupyter-mcp-setup notebook.ipynb --port 8889

# With verbose logging
jupyter-mcp-setup notebook.ipynb --verbose
```

## Features

- **One-Command Setup**: Automatically handles installation, validation, and server startup
- **Smart Detection**: Skips installation if environment already exists and is valid
- **Claude Code Integration**: Automatically configures Claude Code settings
- **Flexible Configuration**: Supports extensive customization options
- **Cross-Platform**: Works on macOS, Linux, and Windows
- **Clean Installation**: No directory clutter when installed via pip

## Command Options

### Core Options
- `--port`, `-p`: Custom port for Jupyter Lab (default: auto-select)
- `--token`, `-t`: Custom token for Jupyter Lab (default: auto-generate)
- `--verbose`, `-v`: Enable verbose logging
- `--output-dir`, `-o`: Directory for configuration files (default: current directory)

### Claude Integration
- `--claude-config` / `--no-claude-config`: Enable/disable Claude Code configuration (default: enabled)

### Advanced Options
- `--port-detection-timeout`: Port detection timeout in seconds (default: 30)
- `--max-port-retries`: Maximum port detection retry attempts (default: 5)
- `--fallback-port`: Fallback port if auto-detection fails
- `--force-reinstall`: Force reinstallation even if environment exists
- `--skip-validation`: Skip validation phase for faster startup
- `--no-cleanup`: Don't clean up configuration files on exit

## Usage Examples

### Basic Usage
```bash
# Install and start server for notebook
jupyter-mcp-setup my-notebook.ipynb
```

### Development with Specific Configuration
```bash
# Development setup with verbose logging and specific port
jupyter-mcp-setup notebook.ipynb --port 8889 --verbose --claude-config
```

### Advanced Configuration
```bash
# Robust setup with fallback options
jupyter-mcp-setup notebook.ipynb \
  --port-detection-timeout 15 \
  --max-port-retries 2 \
  --fallback-port 8888 \
  --verbose
```

### Force Fresh Installation
```bash
# Force complete reinstallation and skip validation
jupyter-mcp-setup notebook.ipynb --force-reinstall --skip-validation
```

## What It Does

1. **Installation Phase**: Creates virtual environment and installs dependencies
2. **Validation Phase**: Verifies installation and components
3. **Server Setup Phase**: 
   - Starts Jupyter Lab
   - Starts MCP server with proper environment
   - Generates `.mcp.json` configuration
   - Updates Claude Code settings (if enabled)
   - Monitors processes

## Configuration Files Generated

- `.mcp.json`: MCP client configuration with server details
- `.claude/settings.local.json`: Claude Code specific settings (when `--claude-config` is used)

## Requirements

- Python ≥3.10
- Jupyter Lab
- MCP server dependencies (automatically installed)

## Architecture

The tool consists of several key components:

- **CLI Interface**: Unified command-line interface with comprehensive options
- **Installer**: Handles virtual environment and dependency installation
- **Validator**: Verifies installation integrity
- **Server Setup**: Manages Jupyter and MCP server lifecycle
- **Configuration Manager**: Generates and updates config files

## Troubleshooting

### Port Detection Issues
If port detection fails, use explicit port configuration:
```bash
jupyter-mcp-setup notebook.ipynb --port 8888 --fallback-port 8889
```

### Installation Issues
Force a fresh installation:
```bash
jupyter-mcp-setup notebook.ipynb --force-reinstall
```

### Validation Issues
Skip validation for faster startup (not recommended for production):
```bash
jupyter-mcp-setup notebook.ipynb --skip-validation
```

## Development

For local development:

```bash
git clone <repository>
cd jupyter-mcp-setup
pip install -e .
```

This installs the package in development mode.

## License

MIT License

## Contributing

Contributions are welcome! Please submit issues and pull requests on the project repository.