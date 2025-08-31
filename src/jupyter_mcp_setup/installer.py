"""
Installation module for Jupyter MCP Setup.

This module handles the installation of the Jupyter MCP server environment,
including virtual environment creation and dependency installation.
"""

import os
import sys
import subprocess
import venv
from pathlib import Path
from typing import Optional

from .utils import (
    setup_logging, log_success, log_phase, 
    InstallationError, check_python_version,
    run_command, get_virtual_env_path, get_virtual_env_python,
    validate_project_structure
)


class JupyterMCPInstaller:
    """Handles installation of Jupyter MCP server environment."""
    
    def __init__(self, project_dir: Optional[Path] = None, verbose: bool = False):
        """
        Initialize installer.
        
        Args:
            project_dir: Project directory (defaults to current directory)
            verbose: Enable verbose logging
        """
        self.project_dir = project_dir or Path.cwd()
        self.logger = setup_logging(verbose)
        self.venv_dir = get_virtual_env_path(self.project_dir)
        
    def check_prerequisites(self) -> bool:
        """
        Check installation prerequisites.
        
        Returns:
            True if prerequisites are met
            
        Raises:
            InstallationError: If prerequisites are not met
        """
        self.logger.info("Checking prerequisites...")
        
        # Check Python version
        if not check_python_version((3, 10)):
            version = f"{sys.version_info.major}.{sys.version_info.minor}"
            raise InstallationError(
                f"Python version {version} is too old (requires >= 3.10)"
            )
        
        version = f"{sys.version_info.major}.{sys.version_info.minor}"
        self.logger.info(f"Found Python {version}")
        
        log_success(self.logger, "Prerequisites check passed")
        return True
        
    def check_existing_installation(self) -> bool:
        """
        Check if installation already exists and is valid.
        
        Returns:
            True if valid installation exists
        """
        if not self.venv_dir.exists():
            self.logger.info("No existing installation found")
            return False
            
        self.logger.info("Found existing virtual environment")
        
        # Quick validation
        if validate_project_structure(self.project_dir):
            try:
                # Test package import
                python_path = get_virtual_env_python(self.project_dir)
                result = run_command([
                    str(python_path), "-c", 
                    "import jupyter_mcp_server; print('OK')"
                ], timeout=10)
                
                if result.returncode == 0:
                    log_success(self.logger, "Existing installation appears valid")
                    return True
                    
            except Exception as e:
                self.logger.warning(f"Existing installation validation failed: {e}")
        
        self.logger.warning("Existing installation appears invalid")
        return False
        
    def create_virtual_environment(self) -> None:
        """
        Create virtual environment.
        
        Raises:
            InstallationError: If virtual environment creation fails
        """
        self.logger.info("Creating virtual environment...")
        
        try:
            # Remove existing environment if it exists
            if self.venv_dir.exists():
                self.logger.info("Removing existing virtual environment...")
                import shutil
                shutil.rmtree(self.venv_dir)
            
            # Create new virtual environment
            venv.create(self.venv_dir, with_pip=True)
            
            log_success(self.logger, "Virtual environment created successfully")
            
        except Exception as e:
            raise InstallationError(f"Failed to create virtual environment: {e}")
    
    def upgrade_pip(self) -> None:
        """
        Upgrade pip in virtual environment.
        
        Raises:
            InstallationError: If pip upgrade fails
        """
        self.logger.info("Upgrading pip...")
        
        try:
            python_path = get_virtual_env_python(self.project_dir)
            run_command([
                str(python_path), "-m", "pip", "install", "--upgrade", "pip"
            ], timeout=60)
            
            log_success(self.logger, "Pip upgraded successfully")
            
        except Exception as e:
            raise InstallationError(f"Failed to upgrade pip: {e}")
    
    def install_dependencies(self) -> None:
        """
        Install package dependencies.
        
        Raises:
            InstallationError: If dependency installation fails
        """
        self.logger.info("Installing dependencies...")
        
        try:
            python_path = get_virtual_env_python(self.project_dir)
            
            # Define dependencies (from requirements-jupyter-mcp.txt)
            dependencies = [
                "jupyter-kernel-client>=0.7.3",
                "jupyter-nbmodel-client>=0.13.5", 
                "mcp[cli]>=1.10.1",
                "pydantic",
                "uvicorn",
                "click",
                "fastapi",
                "ipykernel",
                "jupyter_server>=1.6,<3",
                "jupyterlab==4.4.1",
                "jupyter-collaboration==4.0.2",
                "datalayer_pycrdt==0.12.17",
                "jupyter_mcp_server",
                "psutil>=5.0.0",
            ]
            
            # Install dependencies
            for dep in dependencies:
                self.logger.debug(f"Installing {dep}...")
                run_command([
                    str(python_path), "-m", "pip", "install", dep
                ], timeout=120)
            
            log_success(self.logger, "Dependencies installed successfully")
            
        except Exception as e:
            raise InstallationError(f"Failed to install dependencies: {e}")
    
    def validate_installation(self) -> None:
        """
        Validate the installation.
        
        Raises:
            InstallationError: If validation fails
        """
        self.logger.info("Validating installation...")
        
        try:
            python_path = get_virtual_env_python(self.project_dir)
            
            # Test package import
            run_command([
                str(python_path), "-c", 
                "import jupyter_mcp_server; print('Package import: OK')"
            ], timeout=10)
            
            # Test module execution
            run_command([
                str(python_path), "-m", "jupyter_mcp_server", "--help"
            ], timeout=10)
            
            log_success(self.logger, "Installation validation passed")
            
        except Exception as e:
            raise InstallationError(f"Installation validation failed: {e}")
    
    def install(self, force_reinstall: bool = False) -> bool:
        """
        Run complete installation process.
        
        Args:
            force_reinstall: Force reinstallation even if valid installation exists
            
        Returns:
            True if installation successful
            
        Raises:
            InstallationError: If installation fails
        """
        log_phase(self.logger, "Installation Phase")
        
        try:
            # Check prerequisites
            self.check_prerequisites()
            
            # Check existing installation
            if not force_reinstall and self.check_existing_installation():
                self.logger.info("Skipping installation (use force_reinstall=True to override)")
                return True
            
            # Create virtual environment
            self.create_virtual_environment()
            
            # Upgrade pip
            self.upgrade_pip()
            
            # Install dependencies
            self.install_dependencies()
            
            # Validate installation
            self.validate_installation()
            
            log_success(self.logger, "Installation completed successfully!")
            return True
            
        except InstallationError:
            raise
        except Exception as e:
            raise InstallationError(f"Unexpected installation error: {e}")


def install_jupyter_mcp(
    project_dir: Optional[Path] = None,
    force_reinstall: bool = False,
    verbose: bool = False
) -> bool:
    """
    Install Jupyter MCP server environment.
    
    Args:
        project_dir: Project directory (defaults to current directory)
        force_reinstall: Force reinstallation even if valid installation exists
        verbose: Enable verbose logging
        
    Returns:
        True if installation successful
        
    Raises:
        InstallationError: If installation fails
    """
    installer = JupyterMCPInstaller(project_dir, verbose)
    return installer.install(force_reinstall)