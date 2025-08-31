"""
Validation module for Jupyter MCP Setup.

This module handles validation of the Jupyter MCP server installation,
ensuring all components are properly installed and functional.
"""

import sys
from pathlib import Path
from typing import Optional

from .utils import (
    setup_logging, log_success, log_phase,
    ValidationError, check_python_version,
    run_command, get_virtual_env_path, get_virtual_env_python,
    validate_project_structure, check_file_permissions
)


class JupyterMCPValidator:
    """Handles validation of Jupyter MCP server installation."""
    
    def __init__(self, project_dir: Optional[Path] = None, verbose: bool = False):
        """
        Initialize validator.
        
        Args:
            project_dir: Project directory (defaults to current directory)
            verbose: Enable verbose logging
        """
        self.project_dir = project_dir or Path.cwd()
        self.logger = setup_logging(verbose)
        self.venv_dir = get_virtual_env_path(self.project_dir)
        
    def check_virtual_environment(self) -> bool:
        """
        Check if virtual environment exists and is valid.
        
        Returns:
            True if virtual environment is valid
            
        Raises:
            ValidationError: If virtual environment is invalid
        """
        self.logger.info("Checking virtual environment...")
        
        if not self.venv_dir.exists():
            raise ValidationError("Virtual environment not found")
        
        log_success(self.logger, "Virtual environment found")
        
        # Check structure
        if not validate_project_structure(self.project_dir):
            raise ValidationError("Virtual environment structure is invalid")
        
        log_success(self.logger, "Virtual environment structure is valid")
        return True
        
    def check_python_version_in_venv(self) -> bool:
        """
        Check Python version in virtual environment.
        
        Returns:
            True if Python version is sufficient
            
        Raises:
            ValidationError: If Python version is insufficient
        """
        self.logger.info("Checking Python version in virtual environment...")
        
        try:
            python_path = get_virtual_env_python(self.project_dir)
            result = run_command([
                str(python_path), "-c",
                "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
            ], timeout=10)
            
            version_str = result.stdout.strip()
            self.logger.info(f"Python version: {version_str}")
            
            # Check version in virtual environment
            result = run_command([
                str(python_path), "-c",
                "import sys; exit(0 if sys.version_info >= (3, 10) else 1)"
            ], timeout=10)
            
            if result.returncode != 0:
                raise ValidationError(f"Python version {version_str} is too old (requires >= 3.10)")
            
            log_success(self.logger, "Python version meets requirement (>=3.10)")
            return True
            
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(f"Failed to check Python version: {e}")
    
    def check_package_import(self) -> bool:
        """
        Check if jupyter_mcp_server package can be imported.
        
        Returns:
            True if package import succeeds
            
        Raises:
            ValidationError: If package import fails
        """
        self.logger.info("Testing package import...")
        
        try:
            python_path = get_virtual_env_python(self.project_dir)
            result = run_command([
                str(python_path), "-c",
                "import jupyter_mcp_server; print('Package import: OK')"
            ], timeout=10)
            
            if "Package import: OK" in result.stdout:
                log_success(self.logger, "Package import successful")
                return True
            else:
                raise ValidationError("Package import test failed")
                
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(f"Package import failed: {e}")
    
    def check_cli_availability(self) -> bool:
        """
        Check if CLI commands are available.
        
        Returns:
            True if CLI is available
            
        Raises:
            ValidationError: If CLI is not available
        """
        self.logger.info("Testing CLI availability...")
        
        try:
            python_path = get_virtual_env_python(self.project_dir)
            
            # Test module execution
            run_command([
                str(python_path), "-m", "jupyter_mcp_server", "--help"
            ], timeout=10)
            
            log_success(self.logger, "CLI module execution successful")
            
            # Check for jupyter-mcp-server script if it exists
            jupyter_mcp_script = self.venv_dir / "bin" / "jupyter-mcp-server"
            if jupyter_mcp_script.exists():
                # Test script execution
                run_command([str(jupyter_mcp_script), "--help"], timeout=10)
                log_success(self.logger, "CLI script execution successful")
            else:
                self.logger.info("CLI script not found (using module execution)")
            
            return True
            
        except Exception as e:
            raise ValidationError(f"CLI availability check failed: {e}")
    
    def check_jupyter_components(self) -> bool:
        """
        Check if Jupyter components are properly installed.
        
        Returns:
            True if Jupyter components are available
            
        Raises:
            ValidationError: If Jupyter components are missing
        """
        self.logger.info("Testing Jupyter components...")
        
        try:
            python_path = get_virtual_env_python(self.project_dir)
            
            # Test jupyter lab import
            run_command([
                str(python_path), "-c",
                "import jupyterlab; print('JupyterLab: OK')"
            ], timeout=10)
            
            # Test jupyter server import
            run_command([
                str(python_path), "-c",
                "import jupyter_server; print('Jupyter Server: OK')"
            ], timeout=10)
            
            # Test MCP components
            run_command([
                str(python_path), "-c",
                "import mcp; print('MCP: OK')"
            ], timeout=10)
            
            log_success(self.logger, "Jupyter components validation passed")
            return True
            
        except Exception as e:
            raise ValidationError(f"Jupyter components check failed: {e}")
    
    def run_comprehensive_test(self) -> bool:
        """
        Run comprehensive validation test.
        
        Returns:
            True if all tests pass
            
        Raises:
            ValidationError: If any test fails
        """
        self.logger.info("Running comprehensive validation test...")
        
        try:
            python_path = get_virtual_env_python(self.project_dir)
            
            # Test comprehensive functionality
            test_script = '''
import sys
import jupyter_mcp_server
import jupyterlab
import jupyter_server
import mcp

print("✓ All imports successful")
print(f"✓ Python version: {sys.version_info.major}.{sys.version_info.minor}")
print("✓ Comprehensive test passed")
'''
            
            result = run_command([
                str(python_path), "-c", test_script
            ], timeout=15)
            
            if "Comprehensive test passed" in result.stdout:
                log_success(self.logger, "Comprehensive validation test passed")
                return True
            else:
                raise ValidationError("Comprehensive test did not complete successfully")
                
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(f"Comprehensive test failed: {e}")
    
    def validate(self) -> bool:
        """
        Run complete validation process.
        
        Returns:
            True if validation successful
            
        Raises:
            ValidationError: If validation fails
        """
        log_phase(self.logger, "Validation Phase")
        
        try:
            # Check virtual environment
            self.check_virtual_environment()
            
            # Check Python version
            self.check_python_version_in_venv()
            
            # Check package import
            self.check_package_import()
            
            # Check CLI availability
            self.check_cli_availability()
            
            # Check Jupyter components
            self.check_jupyter_components()
            
            # Run comprehensive test
            self.run_comprehensive_test()
            
            log_success(self.logger, "Validation completed successfully!")
            return True
            
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"Unexpected validation error: {e}")


def validate_jupyter_mcp(
    project_dir: Optional[Path] = None,
    verbose: bool = False
) -> bool:
    """
    Validate Jupyter MCP server installation.
    
    Args:
        project_dir: Project directory (defaults to current directory)
        verbose: Enable verbose logging
        
    Returns:
        True if validation successful
        
    Raises:
        ValidationError: If validation fails
    """
    validator = JupyterMCPValidator(project_dir, verbose)
    return validator.validate()