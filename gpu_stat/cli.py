"""
Command-line interface for GPU-Stat.
"""

import logging
import os
import threading

import click
import yaml

from ._version import __version__
from .data_collector import GPUDataCollector
from .data_store import DataStore

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version=__version__)
def cli():
    """GPU-Stat: Monitor GPU statistics on remote machines."""
    pass


@cli.command()
@click.option("--config", "-c", help="Path to config file", default="config.yaml")
def run(config: str = "config.yaml"):
    """Run GPU-Stat monitor."""
    if not config:
        logger.error("Config file path is required")
        return

    # Read the configuration file
    with open(config, "r") as f:
        config_data = yaml.safe_load(f)

    servers = config_data.get("servers", [])
    settings = config_data.get("settings", {})

    if not servers:
        logger.error("No servers found in the configuration")
        return

    # Create DataStore instance
    data_dir = settings.get("data_dir", "./data")
    data_store = DataStore(base_dir=data_dir)

    # Create and start a thread for each server
    threads = []
    for server_config in servers:
        collector = GPUDataCollector(server_config)
        interval = server_config.get("interval", settings.get("default_interval", 5))
        thread = threading.Thread(
            target=collector.start_collection, args=(interval, data_store.store_data)
        )
        thread.start()
        threads.append(thread)

    # Start the dashboard
    dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard.py")
    streamlit_command = f"streamlit run {dashboard_path} -- --data-dir {data_dir}"
    os.system(streamlit_command)

    # Wait for all threads to complete
    for thread in threads:
        thread.join()


def main():
    """Main entry point for CLI."""
    return cli()
