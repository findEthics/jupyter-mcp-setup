"""
Jupyter MCP Setup - A tool to setup and manage Jupyter MCP servers.

This package provides a unified command-line interface for installing,
validating, and running Jupyter MCP servers with automatic configuration
generation for Claude Code and other MCP clients.
"""

__version__ = "1.0.0"
__author__ = "Jupyter MCP Setup Team"
__description__ = "Unified setup tool for Jupyter MCP servers"

from .cli import main

__all__ = ["main"]