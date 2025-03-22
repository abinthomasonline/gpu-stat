"""
GPU-Stat: Monitor NVIDIA GPU usage on remote machines.
"""

import logging

from ._version import __version__

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

from .cli import main
from .data_collector import GPUDataCollector
from .data_store import DataStore

# Import main components for easier access
from .ssh_client import SSHClient

__all__ = [
    "SSHClient",
    "GPUDataCollector",
    "DataStore",
    "main",
]
