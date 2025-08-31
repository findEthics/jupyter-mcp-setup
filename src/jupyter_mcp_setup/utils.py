"""
Shared utilities for Jupyter MCP Setup.

This module contains common utilities used across the package including
logging, path management, and system operations.
"""

import logging
import os
import sys
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log messages."""
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[0;36m',     # Cyan
        'INFO': '\033[0;34m',      # Blue
        'WARNING': '\033[1;33m',   # Yellow
        'ERROR': '\033[0;31m',     # Red
        'CRITICAL': '\033[1;31m',  # Bright Red
        'SUCCESS': '\033[0;32m',   # Green
        'PHASE': '\033[0;36m',     # Cyan
    }
    RESET = '\033[0m'  # Reset color
    
    def format(self, record):
        # Add color based on level
        level_name = record.levelname
        if level_name in self.COLORS:
            colored_level = f"{self.COLORS[level_name]}[{level_name}]{self.RESET}"
            record.levelname = colored_level
        
        return super().format(record)


def setup_logging(verbose: bool = False) -> logging.Logger:
    """
    Set up logging with appropriate level and formatting.
    
    Args:
        verbose: Enable verbose (DEBUG) logging
        
    Returns:
        Configured logger instance
    """
    level = logging.DEBUG if verbose else logging.INFO
    
    # Create logger
    logger = logging.getLogger('jupyter_mcp_setup')
    logger.setLevel(level)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    
    # Create formatter
    if verbose:
        formatter = ColoredFormatter(
            '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
        )
    else:
        formatter = ColoredFormatter('%(levelname)s %(message)s')
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger


def log_success(logger: logging.Logger, message: str):
    """Log a success message."""
    # Create a custom record with SUCCESS level
    record = logging.LogRecord(
        name=logger.name,
        level=logging.INFO,
        pathname='',
        lineno=0,
        msg=message,
        args=(),
        exc_info=None
    )
    record.levelname = 'SUCCESS'
    logger.handle(record)


def log_phase(logger: logging.Logger, message: str):
    """Log a phase message."""
    # Create a custom record with PHASE level
    record = logging.LogRecord(
        name=logger.name,
        level=logging.INFO,
        pathname='',
        lineno=0,
        msg=message,
        args=(),
        exc_info=None
    )
    record.levelname = 'PHASE'
    logger.handle(record)


class SetupError(Exception):
    """Base exception for setup errors."""
    pass


class InstallationError(SetupError):
    """Exception raised during installation phase."""
    pass


class ValidationError(SetupError):
    """Exception raised during validation phase."""
    pass


class ServerSetupError(SetupError):
    """Exception raised during server setup phase."""
    pass


def check_python_version(min_version: tuple = (3, 10)) -> bool:
    """
    Check if Python version meets minimum requirements.
    
    Args:
        min_version: Minimum required Python version as tuple
        
    Returns:
        True if version is sufficient, False otherwise
    """
    return sys.version_info >= min_version


def run_command(
    command: list, 
    cwd: Optional[Path] = None,
    env: Optional[Dict[str, str]] = None,
    timeout: Optional[int] = None,
    capture_output: bool = True
) -> subprocess.CompletedProcess:
    """
    Run a system command with proper error handling.
    
    Args:
        command: Command and arguments as list
        cwd: Working directory for command
        env: Environment variables
        timeout: Command timeout in seconds
        capture_output: Whether to capture stdout/stderr
        
    Returns:
        CompletedProcess result
        
    Raises:
        SetupError: If command fails
    """
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            timeout=timeout,
            capture_output=capture_output,
            text=True,
            check=True
        )
        return result
    except subprocess.CalledProcessError as e:
        raise SetupError(f"Command failed: {' '.join(command)}\nError: {e.stderr}")
    except subprocess.TimeoutExpired as e:
        raise SetupError(f"Command timed out: {' '.join(command)}")


def ensure_directory(path: Path, mode: int = 0o755) -> Path:
    """
    Ensure directory exists with proper permissions.
    
    Args:
        path: Directory path
        mode: Directory permissions
        
    Returns:
        Path object for the directory
        
    Raises:
        SetupError: If directory cannot be created
    """
    try:
        path.mkdir(parents=True, exist_ok=True, mode=mode)
        return path
    except OSError as e:
        raise SetupError(f"Cannot create directory {path}: {e}")


def check_file_permissions(path: Path, mode: int) -> bool:
    """
    Check if file has required permissions.
    
    Args:
        path: File path
        mode: Required permissions (e.g., os.R_OK, os.W_OK, os.X_OK)
        
    Returns:
        True if file has required permissions
    """
    return path.exists() and os.access(path, mode)


def get_virtual_env_path(project_dir: Path) -> Path:
    """
    Get the path to the virtual environment.
    
    Args:
        project_dir: Project directory path
        
    Returns:
        Path to virtual environment directory
    """
    return project_dir / "jupyter-mcp-env"


def get_virtual_env_python(project_dir: Path) -> Path:
    """
    Get the path to the virtual environment Python executable.
    
    Args:
        project_dir: Project directory path
        
    Returns:
        Path to Python executable
        
    Raises:
        SetupError: If Python executable not found
    """
    venv_path = get_virtual_env_path(project_dir)
    python_path = venv_path / "bin" / "python"
    
    if not python_path.exists():
        raise SetupError(f"Virtual environment Python not found: {python_path}")
    
    if not check_file_permissions(python_path, os.X_OK):
        raise SetupError(f"Virtual environment Python not executable: {python_path}")
    
    return python_path


def validate_notebook_path(notebook_path: str) -> Path:
    """
    Validate and resolve notebook path.
    
    Args:
        notebook_path: Path to notebook file
        
    Returns:
        Resolved Path object
        
    Raises:
        SetupError: If notebook path is invalid
    """
    try:
        path = Path(notebook_path)
        
        # Handle relative paths
        if not path.is_absolute():
            path = Path.cwd() / path
        
        # Resolve to canonical path
        resolved_path = path.resolve()
        
        # Validate file exists
        if not resolved_path.exists():
            raise SetupError(f"Notebook file not found: {resolved_path}")
        
        # Validate it's a file
        if not resolved_path.is_file():
            raise SetupError(f"Path is not a file: {resolved_path}")
        
        # Validate notebook extension
        if resolved_path.suffix.lower() != '.ipynb':
            raise SetupError(f"File must be a Jupyter notebook (.ipynb): {resolved_path}")
        
        # Validate JSON format
        import json
        try:
            with open(resolved_path, 'r') as f:
                json.load(f)
        except json.JSONDecodeError as e:
            raise SetupError(f"Invalid notebook JSON in {resolved_path}: {e}")
        
        return resolved_path
        
    except Exception as e:
        if isinstance(e, SetupError):
            raise
        raise SetupError(f"Path validation failed for '{notebook_path}': {e}")


def get_project_directory() -> Path:
    """
    Get the current project directory.
    
    Returns:
        Path to current working directory
    """
    return Path.cwd()


def validate_project_structure(project_dir: Path) -> bool:
    """
    Validate that project has required structure for Jupyter MCP setup.
    
    Args:
        project_dir: Project directory path
        
    Returns:
        True if structure is valid
    """
    venv_path = get_virtual_env_path(project_dir)
    
    required_paths = [
        venv_path / "bin" / "python",
        venv_path / "bin" / "activate",
    ]
    
    return all(path.exists() for path in required_paths)