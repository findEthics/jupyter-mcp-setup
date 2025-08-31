"""
Command-line interface for Jupyter MCP Setup.

This module provides a unified CLI that combines installation, validation,
and server setup into a single command with comprehensive argument support.
"""

import sys
from pathlib import Path
from typing import Optional

import click

from . import __version__
from .installer import install_jupyter_mcp, InstallationError
from .validator import validate_jupyter_mcp, ValidationError
from .server_setup import setup_jupyter_mcp_server, ServerSetupError
from .utils import setup_logging, log_success, log_phase, SetupError


@click.command()
@click.argument('notebook', type=click.Path(exists=True, path_type=Path))
@click.option('--port', '-p', type=int, help='Custom port for Jupyter Lab (default: auto-select)')
@click.option('--token', '-t', help='Custom token for Jupyter Lab (default: auto-generate)')
@click.option('--output-dir', '-o', default='.', help='Directory for generated configuration files (default: current directory)')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--no-cleanup', is_flag=True, help="Don't clean up configuration files on exit")
@click.option('--claude-config/--no-claude-config', default=True, help='Enable/disable Claude Code configuration (default: enabled)')
@click.option('--port-detection-timeout', type=int, default=30, help='Timeout for port detection in seconds (default: 30)')
@click.option('--max-port-retries', type=int, default=5, help='Maximum port detection retry attempts (default: 5)')
@click.option('--fallback-port', type=int, help='Fallback port if auto-detection fails')
@click.option('--force-reinstall', is_flag=True, help='Force reinstallation even if environment exists')
@click.option('--skip-validation', is_flag=True, help='Skip validation phase for faster startup')
@click.version_option(__version__, prog_name='jupyter-mcp-setup')
def main(
    notebook: Path,
    port: Optional[int],
    token: Optional[str],
    output_dir: str,
    verbose: bool,
    no_cleanup: bool,
    claude_config: bool,
    port_detection_timeout: int,
    max_port_retries: int,
    fallback_port: Optional[int],
    force_reinstall: bool,
    skip_validation: bool
):
    """
    Jupyter MCP Server Unified Setup Tool.
    
    This tool combines installation, validation, and server setup into one command.
    It automatically detects if installation is needed and runs all phases.
    
    NOTEBOOK: Path to Jupyter notebook file (.ipynb)
    
    Examples:
    
    \b
    # Basic usage (auto-install, validate, and start server)
    jupyter-mcp-setup notebook.ipynb
    
    \b
    # With specific port
    jupyter-mcp-setup notebook.ipynb --port 8889
    
    \b
    # With verbose logging and custom configuration
    jupyter-mcp-setup notebook.ipynb --verbose --claude-config --port-detection-timeout 15
    
    \b
    # Force reinstall and skip validation
    jupyter-mcp-setup notebook.ipynb --force-reinstall --skip-validation --port 8889
    
    \b
    # Advanced usage with all options
    jupyter-mcp-setup notebook.ipynb --port 8889 --verbose --fallback-port 8888 --max-port-retries 3
    """
    # Setup logging
    logger = setup_logging(verbose)
    
    # Display header
    click.echo("=== Jupyter MCP Server Unified Setup ===")
    click.echo(f"Version: {__version__}")
    click.echo()
    
    logger.info(f"Notebook: {notebook}")
    if verbose:
        logger.info(f"Port: {port or 'auto-select'}")
        logger.info(f"Token: {'custom' if token else 'auto-generate'}")
        logger.info(f"Output directory: {output_dir}")
        logger.info(f"Claude config: {claude_config}")
        logger.info(f"Force reinstall: {force_reinstall}")
        logger.info(f"Skip validation: {skip_validation}")
    
    try:
        # Phase 1: Installation
        run_installation_phase(
            force_reinstall=force_reinstall,
            verbose=verbose,
            logger=logger
        )
        
        # Phase 2: Validation  
        if not skip_validation:
            run_validation_phase(verbose=verbose, logger=logger)
        else:
            logger.info("Skipping validation phase (--skip-validation flag used)")
        
        # Phase 3: Server Setup
        run_server_setup_phase(
            notebook_path=str(notebook),
            port=port,
            token=token,
            output_dir=output_dir,
            verbose=verbose,
            cleanup=not no_cleanup,
            claude_config=claude_config,
            port_detection_timeout=port_detection_timeout,
            max_port_detection_attempts=max_port_retries,
            fallback_port=fallback_port,
            logger=logger
        )
        
        log_success(logger, "All phases completed successfully!")
        
    except (InstallationError, ValidationError, ServerSetupError) as e:
        logger.error(str(e))
        sys.exit(1)
    except SetupError as e:
        logger.error(f"Setup error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Setup interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if verbose:
            import traceback
            logger.error(traceback.format_exc())
        sys.exit(1)


def run_installation_phase(
    force_reinstall: bool,
    verbose: bool,
    logger
) -> None:
    """Run the installation phase."""
    log_phase(logger, "Installation Phase")
    
    try:
        success = install_jupyter_mcp(
            project_dir=None,  # Use current directory
            force_reinstall=force_reinstall,
            verbose=verbose
        )
        
        if success:
            log_success(logger, "Installation phase completed")
        else:
            raise InstallationError("Installation phase failed")
            
    except InstallationError:
        raise
    except Exception as e:
        raise InstallationError(f"Installation phase error: {e}")


def run_validation_phase(verbose: bool, logger) -> None:
    """Run the validation phase."""
    log_phase(logger, "Validation Phase")
    
    try:
        success = validate_jupyter_mcp(
            project_dir=None,  # Use current directory
            verbose=verbose
        )
        
        if success:
            log_success(logger, "Validation phase completed")
        else:
            raise ValidationError("Validation phase failed")
            
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f"Validation phase error: {e}")


def run_server_setup_phase(
    notebook_path: str,
    port: Optional[int],
    token: Optional[str], 
    output_dir: str,
    verbose: bool,
    cleanup: bool,
    claude_config: bool,
    port_detection_timeout: int,
    max_port_detection_attempts: int,
    fallback_port: Optional[int],
    logger
) -> None:
    """Run the server setup phase."""
    log_phase(logger, "Server Setup Phase")
    
    try:
        # Prepare server setup arguments
        setup_kwargs = {
            'port': port,
            'token': token,
            'output_dir': output_dir,
            'verbose': verbose,
            'cleanup': cleanup,
            'claude_config': claude_config,
            'port_detection_timeout': port_detection_timeout,
            'max_port_detection_attempts': max_port_detection_attempts,
            'fallback_port': fallback_port,
        }
        
        # Remove None values to use defaults
        setup_kwargs = {k: v for k, v in setup_kwargs.items() if v is not None}
        
        success = setup_jupyter_mcp_server(notebook_path, **setup_kwargs)
        
        if success:
            log_success(logger, "Server setup phase completed")
        else:
            raise ServerSetupError("Server setup phase failed")
            
    except ServerSetupError:
        raise
    except Exception as e:
        raise ServerSetupError(f"Server setup phase error: {e}")


# Add subcommands for advanced usage

@click.group()
@click.version_option(__version__, prog_name='jupyter-mcp-setup')
def advanced():
    """Advanced Jupyter MCP Setup commands."""
    pass


@advanced.command()
@click.option('--force', is_flag=True, help='Force reinstallation')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
def install(force: bool, verbose: bool):
    """Install Jupyter MCP server environment only."""
    logger = setup_logging(verbose)
    
    try:
        success = install_jupyter_mcp(
            project_dir=None,
            force_reinstall=force,
            verbose=verbose
        )
        
        if success:
            log_success(logger, "Installation completed successfully!")
        else:
            logger.error("Installation failed")
            sys.exit(1)
            
    except InstallationError as e:
        logger.error(str(e))
        sys.exit(1)


@advanced.command()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
def validate(verbose: bool):
    """Validate Jupyter MCP server installation only."""
    logger = setup_logging(verbose)
    
    try:
        success = validate_jupyter_mcp(
            project_dir=None,
            verbose=verbose
        )
        
        if success:
            log_success(logger, "Validation completed successfully!")
        else:
            logger.error("Validation failed")
            sys.exit(1)
            
    except ValidationError as e:
        logger.error(str(e))
        sys.exit(1)


@advanced.command()
@click.argument('notebook', type=click.Path(exists=True, path_type=Path))
@click.option('--port', '-p', type=int, help='Custom port for Jupyter Lab')
@click.option('--token', '-t', help='Custom token for Jupyter Lab')
@click.option('--output-dir', '-o', default='.', help='Directory for configuration files')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--no-cleanup', is_flag=True, help="Don't clean up configuration files on exit")
@click.option('--claude-config/--no-claude-config', default=True, help='Enable/disable Claude Code configuration')
@click.option('--port-detection-timeout', type=int, default=30, help='Port detection timeout')
@click.option('--max-port-retries', type=int, default=5, help='Max port detection retries')
@click.option('--fallback-port', type=int, help='Fallback port')
def server(
    notebook: Path,
    port: Optional[int],
    token: Optional[str],
    output_dir: str,
    verbose: bool,
    no_cleanup: bool,
    claude_config: bool,
    port_detection_timeout: int,
    max_port_retries: int,
    fallback_port: Optional[int]
):
    """Start Jupyter MCP server only (assumes installation/validation done)."""
    logger = setup_logging(verbose)
    
    try:
        setup_kwargs = {
            'port': port,
            'token': token,
            'output_dir': output_dir,
            'verbose': verbose,
            'cleanup': not no_cleanup,
            'claude_config': claude_config,
            'port_detection_timeout': port_detection_timeout,
            'max_port_detection_attempts': max_port_retries,
            'fallback_port': fallback_port,
        }
        
        # Remove None values
        setup_kwargs = {k: v for k, v in setup_kwargs.items() if v is not None}
        
        success = setup_jupyter_mcp_server(str(notebook), **setup_kwargs)
        
        if not success:
            logger.error("Server setup failed")
            sys.exit(1)
            
    except ServerSetupError as e:
        logger.error(str(e))
        sys.exit(1)


if __name__ == '__main__':
    main()