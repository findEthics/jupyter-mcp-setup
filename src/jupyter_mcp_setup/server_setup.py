"""
Server setup module for Jupyter MCP Setup.

This module handles the core server setup functionality including
Jupyter Lab startup, MCP server management, and configuration generation.
"""

import json
import os
import re
import signal
import subprocess
import sys
import time
import threading
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import urllib.parse

from .utils import (
    setup_logging, log_success, log_phase,
    ServerSetupError, run_command, validate_notebook_path,
    get_virtual_env_python, ensure_directory
)


class PathManager:
    """Enhanced path management for Jupyter MCP Server setup."""
    
    def __init__(self, project_dir: Path, logger=None):
        self.project_dir = Path(project_dir).resolve()
        self.logger = logger or setup_logging()
    
    def validate_and_resolve_notebook_path(self, notebook_path: str) -> Path:
        """Validate and resolve notebook path with comprehensive error checking."""
        return validate_notebook_path(notebook_path)
    
    def get_relative_path_for_document_id(self, notebook_path: Path) -> str:
        """Calculate relative path for DOCUMENT_ID environment variable."""
        try:
            # Try to make path relative to project directory
            try:
                relative_path = notebook_path.relative_to(self.project_dir)
                result = str(relative_path)
            except ValueError:
                # Notebook is outside project directory, use absolute path
                result = str(notebook_path)
            
            self.logger.debug(f"✓ DOCUMENT_ID path: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to calculate relative path: {e}")
            # Fallback to absolute path
            return str(notebook_path)
    
    def resolve_configuration_paths(self, output_dir: str) -> Tuple[Path, Path]:
        """Resolve and validate configuration file paths."""
        try:
            output_path = Path(output_dir).resolve()
            
            # Create output directory if it doesn't exist
            ensure_directory(output_path)
            
            # Validate write permissions
            if not os.access(output_path, os.W_OK):
                raise PermissionError(f"No write permission for output directory: {output_path}")
            
            mcp_config_path = output_path / ".mcp.json"
            settings_config_path = output_path / "settings.local.json"
            
            self.logger.debug(f"✓ Configuration paths resolved:")
            self.logger.debug(f"  - MCP config: {mcp_config_path}")
            
            return mcp_config_path, settings_config_path
            
        except Exception as e:
            self.logger.error(f"Failed to resolve configuration paths: {e}")
            raise ServerSetupError(f"Failed to resolve configuration paths: {e}")


class ClaudeConfigManager:
    """Claude Code specific configuration management."""
    
    def __init__(self, path_manager: PathManager, logger=None):
        self.path_manager = path_manager
        self.logger = logger or setup_logging()
    
    def get_claude_config_path(self) -> Path:
        """Get the path to Claude Code settings file."""
        claude_dir = self.path_manager.project_dir / ".claude"
        claude_config = claude_dir / "settings.local.json"
        return claude_config
    
    def ensure_claude_directory(self) -> bool:
        """Ensure .claude directory exists with proper permissions."""
        try:
            claude_dir = self.path_manager.project_dir / ".claude"
            ensure_directory(claude_dir)
            
            # Validate write permissions
            if not os.access(claude_dir, os.W_OK):
                raise PermissionError(f"No write permission for Claude directory: {claude_dir}")
            
            self.logger.debug(f"✓ Claude directory ready: {claude_dir}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create Claude directory: {e}")
            return False
    
    def load_existing_claude_settings(self) -> Dict[str, Any]:
        """Load existing Claude settings, preserving all current configuration."""
        claude_config_path = self.get_claude_config_path()
        
        if not claude_config_path.exists():
            self.logger.debug("No existing Claude settings found, starting fresh")
            return {}
        
        try:
            with open(claude_config_path, 'r') as f:
                settings = json.load(f)
            self.logger.debug(f"✓ Loaded existing Claude settings from {claude_config_path}")
            return settings
        except json.JSONDecodeError as e:
            self.logger.warning(f"Invalid JSON in Claude settings, starting fresh: {e}")
            return {}
        except Exception as e:
            self.logger.error(f"Error loading Claude settings: {e}")
            return {}
    
    def update_enabled_mcp_servers(self, server_name: str, existing_settings: Dict[str, Any]) -> Dict[str, Any]:
        """Add server to enabledMcpjsonServers array, preserving existing settings."""
        # Ensure enabledMcpjsonServers exists
        if "enabledMcpjsonServers" not in existing_settings:
            existing_settings["enabledMcpjsonServers"] = []
        
        # Add server if not already present
        if server_name not in existing_settings["enabledMcpjsonServers"]:
            existing_settings["enabledMcpjsonServers"].append(server_name)
            self.logger.debug(f"✓ Added '{server_name}' to enabledMcpjsonServers")
        else:
            self.logger.debug(f"'{server_name}' already in enabledMcpjsonServers")
        
        return existing_settings
    
    def generate_claude_settings(self, server_name: str = "jupyter") -> bool:
        """Generate Claude Code specific settings, preserving existing configuration."""
        try:
            # Ensure Claude directory exists
            if not self.ensure_claude_directory():
                return False
            
            # Load existing settings
            settings = self.load_existing_claude_settings()
            
            # Update with MCP server enablement
            settings = self.update_enabled_mcp_servers(server_name, settings)
            
            # Write updated settings
            claude_config_path = self.get_claude_config_path()
            with open(claude_config_path, 'w') as f:
                json.dump(settings, f, indent=2)
            
            self.logger.info(f"✓ Claude Code settings updated: {claude_config_path}")
            self.logger.debug(f"  Enabled MCP servers: {settings.get('enabledMcpjsonServers', [])}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to generate Claude settings: {e}")
            return False


class EnvironmentManager:
    """Advanced environment variable management for MCP server configuration."""
    
    def __init__(self, logger=None):
        self.logger = logger or setup_logging()
        self.validated_env = {}
    
    def validate_url(self, url: str, name: str = "URL") -> bool:
        """Validate URL format."""
        try:
            result = urllib.parse.urlparse(url)
            if not all([result.scheme, result.netloc]):
                raise ValueError(f"Invalid {name} format: {url}")
            return True
        except Exception as e:
            self.logger.error(f"{name} validation failed: {e}")
            return False
    
    def validate_token(self, token: str, name: str = "token") -> bool:
        """Validate token format."""
        if not token or len(token) < 8:
            self.logger.error(f"Invalid {name}: too short (minimum 8 characters)")
            return False
        if not re.match(r'^[a-f0-9]+$', token):
            self.logger.error(f"Invalid {name}: must be hexadecimal")
            return False
        return True
    
    def create_jupyter_environment(self, jupyter_url: str, jupyter_token: str, 
                                 notebook_path: str) -> Dict[str, str]:
        """Create and validate complete Jupyter environment variables."""
        try:
            # Validate inputs
            if not self.validate_url(jupyter_url, "Jupyter URL"):
                raise ValueError(f"Invalid Jupyter URL: {jupyter_url}")
            
            if not self.validate_token(jupyter_token, "Jupyter token"):
                raise ValueError(f"Invalid Jupyter token format")
            
            # Create environment dictionary
            env_vars = {
                "TRANSPORT": "stdio",
                "PROVIDER": "jupyter",
                "DOCUMENT_URL": jupyter_url,
                "DOCUMENT_TOKEN": jupyter_token,
                "DOCUMENT_ID": notebook_path,
                "RUNTIME_URL": jupyter_url,
                "RUNTIME_TOKEN": jupyter_token,
                "START_NEW_RUNTIME": "true"
            }
            
            # Validate all environment variables
            for key, value in env_vars.items():
                if not value:
                    raise ValueError(f"Empty environment variable: {key}")
            
            self.validated_env = env_vars.copy()
            self.logger.debug("✓ Jupyter environment variables validated:")
            for key, value in env_vars.items():
                if "TOKEN" in key:
                    self.logger.debug(f"  - {key}: {value[:8]}...")
                else:
                    self.logger.debug(f"  - {key}: {value}")
            
            return env_vars
            
        except Exception as e:
            self.logger.error(f"Failed to create Jupyter environment: {e}")
            raise ServerSetupError(f"Failed to create Jupyter environment: {e}")
    
    def merge_with_system_env(self, custom_env: Dict[str, str]) -> Dict[str, str]:
        """Merge custom environment with system environment."""
        system_env = os.environ.copy()
        system_env.update(custom_env)
        return system_env


class JupyterMCPServerSetup:
    """Main orchestrator for Jupyter MCP Server setup."""
    
    def __init__(self, notebook_path: str, **kwargs):
        # Configuration options
        self.custom_port = kwargs.get('port')
        self.custom_token = kwargs.get('token')
        self.output_dir = kwargs.get('output_dir', '.')
        self.verbose = kwargs.get('verbose', False)
        self.cleanup_on_exit = kwargs.get('cleanup', True)
        
        # Claude integration options
        self.claude_config = kwargs.get('claude_config', True)  # Default: enabled
        
        # Port detection configuration options
        self.port_detection_timeout = kwargs.get('port_detection_timeout', 30)
        self.max_port_detection_attempts = kwargs.get('max_port_detection_attempts', 5)
        self.port_detection_retry_delay = kwargs.get('port_detection_retry_delay', 2)
        self.fallback_port = kwargs.get('fallback_port', None)
        
        # Setup logging
        self.logger = setup_logging(self.verbose)
        
        # Initialize managers
        self.working_dir = Path.cwd()
        self.project_dir = self.working_dir
        self.path_manager = PathManager(self.project_dir, self.logger)
        self.env_manager = EnvironmentManager(self.logger)
        self.claude_manager = ClaudeConfigManager(self.path_manager, self.logger)
        
        # Enhanced path resolution using PathManager
        try:
            self.notebook_path = self.path_manager.validate_and_resolve_notebook_path(notebook_path)
            self.mcp_config_path, self.settings_config_path = self.path_manager.resolve_configuration_paths(self.output_dir)
        except Exception as e:
            self.logger.error(f"Path validation failed: {e}")
            raise ServerSetupError(f"Path validation failed: {e}")
        
        # Process tracking
        self.jupyter_process = None
        self.mcp_process = None
        self.jupyter_port = None
        self.jupyter_token = None
        self.jupyter_url = None
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.cleanup()
        sys.exit(0)
    
    def start_jupyter_lab(self) -> bool:
        """Start Jupyter Lab and extract runtime details."""
        self.logger.info("Starting Jupyter Lab...")
        
        # Get virtual environment path
        try:
            venv_python = get_virtual_env_python(self.project_dir)
        except Exception as e:
            raise ServerSetupError(f"Virtual environment not found: {e}")
        
        # Build Jupyter Lab command
        jupyter_cmd = [str(venv_python), "-m", "jupyter", "lab"]
        
        # Add custom port if specified
        if self.custom_port:
            jupyter_cmd.extend(["--port", str(self.custom_port)])
        else:
            jupyter_cmd.extend(["--port", "0"])  # Let Jupyter choose available port
        
        # Add custom token if specified
        if self.custom_token:
            jupyter_cmd.extend(["--IdentityProvider.token", self.custom_token])
        
        # Add other necessary options
        jupyter_cmd.extend([
            "--no-browser",
            "--allow-root",
            f"--notebook-dir={self.notebook_path.parent}"
        ])
        
        try:
            # Start Jupyter process
            self.jupyter_process = subprocess.Popen(
                jupyter_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=str(self.project_dir)
            )
            
            # Monitor output for startup information
            startup_timeout = 30  # seconds
            start_time = time.time()
            
            while time.time() - start_time < startup_timeout:
                if self.jupyter_process.poll() is not None:
                    raise ServerSetupError("Jupyter Lab process exited unexpectedly")
                
                try:
                    line = self.jupyter_process.stdout.readline()
                    if not line:
                        time.sleep(0.1)
                        continue
                    
                    if self.verbose:
                        self.logger.debug(f"Jupyter: {line.strip()}")
                    
                    # Extract token and port from Jupyter output
                    if self._extract_jupyter_details(line):
                        self.logger.info(f"✓ Jupyter Lab started successfully")
                        self.logger.info(f"  URL: {self.jupyter_url}")
                        self.logger.info(f"  Port: {self.jupyter_port}")
                        self.logger.info(f"  Token: {self.jupyter_token[:8]}...")
                        return True
                
                except Exception as e:
                    if self.verbose:
                        self.logger.debug(f"Error reading Jupyter output: {e}")
                    time.sleep(0.1)
            
            raise ServerSetupError("Timeout waiting for Jupyter Lab to start")
            
        except Exception as e:
            if isinstance(e, ServerSetupError):
                raise
            raise ServerSetupError(f"Failed to start Jupyter Lab: {e}")
    
    def _extract_jupyter_details(self, line: str) -> bool:
        """Extract token, port, and URL from Jupyter output line."""
        # Enhanced patterns to handle various Jupyter output formats
        patterns = [
            r'http://localhost:(\d+)/lab\?token=([a-f0-9]+)',
            r'http://localhost:(\d+)/\?token=([a-f0-9]+)', 
            r'http://127\.0\.0\.1:(\d+)/lab\?token=([a-f0-9]+)',
            r'http://127\.0\.0\.1:(\d+)/\?token=([a-f0-9]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                port = int(match.group(1))
                if port > 0:  # Valid port number
                    self.jupyter_port = port
                    self.jupyter_token = match.group(2)
                    self.jupyter_url = f"http://localhost:{self.jupyter_port}"
                    self.logger.debug(f"✓ Extracted Jupyter details: port={port}, token={self.jupyter_token[:8]}...")
                    return True
        
        return False
    
    def start_mcp_server(self) -> bool:
        """Start MCP server with dynamic configuration."""
        if not self.jupyter_port or not self.jupyter_token:
            raise ServerSetupError("Cannot start MCP server: Jupyter details not available")
        
        self.logger.info("Starting MCP server...")
        
        # Use EnvironmentManager for enhanced environment variable handling
        try:
            # Get the proper DOCUMENT_ID path using PathManager
            document_id = self.path_manager.get_relative_path_for_document_id(self.notebook_path)
            
            # Create validated environment variables using EnvironmentManager
            jupyter_env = self.env_manager.create_jupyter_environment(
                jupyter_url=self.jupyter_url,
                jupyter_token=self.jupyter_token,
                notebook_path=document_id
            )
            
            # Merge with system environment
            env = self.env_manager.merge_with_system_env(jupyter_env)
            
        except Exception as e:
            raise ServerSetupError(f"Failed to create MCP environment: {e}")
        
        # Start MCP server
        try:
            venv_python = get_virtual_env_python(self.project_dir)
            mcp_cmd = [str(venv_python), "-m", "jupyter_mcp_server"]
            
            self.mcp_process = subprocess.Popen(
                mcp_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                cwd=str(self.project_dir)
            )
            
            # Give the server a moment to start
            time.sleep(2)
            
            # Check if process is still running
            if self.mcp_process.poll() is None:
                self.logger.info("✓ MCP server started successfully")
                return True
            else:
                raise ServerSetupError("MCP server process exited immediately")
                
        except Exception as e:
            if isinstance(e, ServerSetupError):
                raise
            raise ServerSetupError(f"Failed to start MCP server: {e}")
    
    def generate_configurations(self) -> bool:
        """Generate dynamic MCP client configuration files including Claude integration."""
        if not self.jupyter_port or not self.jupyter_token:
            raise ServerSetupError("Cannot generate configurations: Jupyter details not available")
        
        self.logger.info("Generating MCP client configuration files...")
        
        try:
            # Generate .mcp.json
            self._generate_mcp_config()
            
            # Generate Claude Code specific configuration
            if self.claude_config:
                claude_success = self.claude_manager.generate_claude_settings("jupyter")
                if claude_success:
                    self.logger.info(f"  Claude config: {self.claude_manager.get_claude_config_path()}")
                else:
                    self.logger.warning("Claude configuration generation failed, but continuing...")
            
            self.logger.info("✓ Configuration files generated successfully")
            self.logger.info(f"  MCP config: {self.mcp_config_path}")
            
            return True
            
        except Exception as e:
            raise ServerSetupError(f"Failed to generate configurations: {e}")
    
    def _generate_mcp_config(self):
        """Generate .mcp.json configuration file."""
        # Get paths and environment variables
        document_id = self.path_manager.get_relative_path_for_document_id(self.notebook_path)
        env_vars = self.env_manager.create_jupyter_environment(
            jupyter_url=self.jupyter_url,
            jupyter_token=self.jupyter_token,
            notebook_path=document_id
        )
        
        config = {
            "mcpServers": {
                "jupyter": {
                    "command": sys.executable,
                    "args": ["-m", "jupyter_mcp_server"],
                    "env": env_vars
                }
            }
        }
        
        with open(self.mcp_config_path, 'w') as f:
            json.dump(config, f, indent=2)
    
    def monitor_processes(self) -> bool:
        """Monitor running processes and handle failures."""
        self.logger.info("Monitoring Jupyter Lab and MCP server processes...")
        self.logger.info("Press Ctrl+C to stop all processes and exit")
        
        try:
            while True:
                # Check Jupyter process
                if self.jupyter_process and self.jupyter_process.poll() is not None:
                    raise ServerSetupError("Jupyter Lab process has stopped unexpectedly")
                
                # Check MCP process
                if self.mcp_process and self.mcp_process.poll() is not None:
                    raise ServerSetupError("MCP server process has stopped unexpectedly")
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal, shutting down...")
            return True
    
    def cleanup(self):
        """Clean up processes and temporary files."""
        self.logger.info("Cleaning up processes...")
        
        # Terminate MCP server
        if self.mcp_process:
            try:
                self.mcp_process.terminate()
                self.mcp_process.wait(timeout=5)
                self.logger.info("✓ MCP server stopped")
            except subprocess.TimeoutExpired:
                self.mcp_process.kill()
                self.logger.info("✓ MCP server force killed")
            except Exception as e:
                self.logger.error(f"Error stopping MCP server: {e}")
        
        # Terminate Jupyter
        if self.jupyter_process:
            try:
                self.jupyter_process.terminate()
                self.jupyter_process.wait(timeout=10)
                self.logger.info("✓ Jupyter Lab stopped")
            except subprocess.TimeoutExpired:
                self.jupyter_process.kill()
                self.logger.info("✓ Jupyter Lab force killed")
            except Exception as e:
                self.logger.error(f"Error stopping Jupyter Lab: {e}")
        
        # Clean up configuration files if requested
        if self.cleanup_on_exit:
            try:
                if self.mcp_config_path.exists():
                    self.mcp_config_path.unlink()
                    self.logger.info(f"✓ Cleaned up {self.mcp_config_path}")
            except Exception as e:
                self.logger.error(f"Error cleaning up configuration files: {e}")
    
    def run(self) -> bool:
        """Main execution flow."""
        try:
            log_phase(self.logger, "Server Setup Phase")
            self.logger.info(f"Notebook: {self.notebook_path}")
            self.logger.info(f"Working directory: {self.working_dir}")
            
            # Step 1: Start Jupyter Lab
            if not self.start_jupyter_lab():
                return False
            
            # Step 2: Start MCP server
            if not self.start_mcp_server():
                return False
            
            # Step 3: Generate configurations
            if not self.generate_configurations():
                return False
            
            # Step 4: Monitor processes
            success = self.monitor_processes()
            
            return success
            
        except Exception as e:
            if isinstance(e, ServerSetupError):
                self.logger.error(str(e))
            else:
                self.logger.error(f"Unexpected error: {e}")
                if self.verbose:
                    import traceback
                    self.logger.error(traceback.format_exc())
            return False
        
        finally:
            self.cleanup()


def setup_jupyter_mcp_server(notebook_path: str, **kwargs) -> bool:
    """
    Set up and run Jupyter MCP server.
    
    Args:
        notebook_path: Path to Jupyter notebook file
        **kwargs: Additional configuration options
        
    Returns:
        True if setup successful
        
    Raises:
        ServerSetupError: If setup fails
    """
    server_setup = JupyterMCPServerSetup(notebook_path, **kwargs)
    return server_setup.run()