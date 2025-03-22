"""
Data storage module for GPU-Stat.
Handles saving GPU statistics to local storage.
"""

import csv
import logging
import os
from datetime import datetime
from typing import Any, Dict

logger = logging.getLogger(__name__)


class DataStore:
    """Handles storing GPU statistics to local files."""

    def __init__(self, base_dir: str = "./data"):
        """
        Initialize data store.

        Args:
            base_dir: Base directory for data storage
        """
        self.base_dir = os.path.abspath(os.path.expanduser(base_dir))
        self._ensure_dirs()

    def _ensure_dirs(self):
        """Ensure required directories exist."""
        os.makedirs(self.base_dir, exist_ok=True)

    def _get_server_dir(self, server_name: str) -> str:
        """
        Get directory for server data.

        Args:
            server_name: Name of the server

        Returns:
            Path to server data directory
        """
        server_dir = os.path.join(self.base_dir, server_name)
        os.makedirs(server_dir, exist_ok=True)
        return server_dir

    def _get_date_filename(self, server_name: str) -> str:
        """
        Get filename for current date.

        Args:
            server_name: Name of the server

        Returns:
            Path to current date's data file
        """
        date_str = datetime.now().strftime("%Y-%m-%d")
        server_dir = self._get_server_dir(server_name)
        return os.path.join(server_dir, f"gpu_stats_{date_str}.csv")

    def store_data(self, data: Dict[str, Any]) -> bool:
        """
        Store GPU statistics data.

        Args:
            data: Dictionary containing GPU stats

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            server_name = data.get("server")
            if not server_name:
                logger.error("Server name not found in data")
                return False

            # Get the current date's file
            filename = self._get_date_filename(server_name)
            file_exists = os.path.exists(filename)

            # Extract GPU data
            timestamp = data.get("timestamp")

            # Process each GPU
            for gpu in data.get("gpus", []):
                gpu_idx = gpu.get("index")
                gpu_name = gpu.get("name")

                # Prepare row data for CSV
                row = {
                    "timestamp": timestamp,
                    "gpu_index": gpu_idx,
                    "gpu_name": gpu_name,
                    "utilization_gpu": gpu.get("utilization_gpu"),
                    "utilization_memory": gpu.get("utilization_memory"),
                    "memory_total": gpu.get("memory_total"),
                    "memory_used": gpu.get("memory_used"),
                    "memory_free": gpu.get("memory_free"),
                    "temperature": gpu.get("temperature"),
                    "power_draw": gpu.get("power_draw"),
                    "power_limit": gpu.get("power_limit"),
                    "fan_speed": gpu.get("fan_speed"),
                    "process_count": len(gpu.get("processes", [])),
                }

                # Write to CSV
                with open(filename, "a", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=row.keys())

                    # Write header if file doesn't exist
                    if not file_exists:
                        writer.writeheader()
                        file_exists = True

                    writer.writerow(row)

                # Write process data to a separate file if processes exist
                processes = gpu.get("processes", [])
                if processes:
                    process_file = os.path.join(
                        self._get_server_dir(server_name),
                        f"gpu_{gpu_idx}_processes_{datetime.now().strftime('%Y-%m-%d')}.csv",
                    )

                    process_file_exists = os.path.exists(process_file)

                    with open(process_file, "a", newline="") as f:
                        for proc in processes:
                            proc_row = {
                                "timestamp": timestamp,
                                "gpu_index": gpu_idx,
                                "pid": proc.get("pid"),
                                "process_name": proc.get("name"),
                                "used_memory": proc.get("used_memory"),
                            }

                            writer = csv.DictWriter(f, fieldnames=proc_row.keys())

                            # Write header if file doesn't exist
                            if not process_file_exists:
                                writer.writeheader()
                                process_file_exists = True

                            writer.writerow(proc_row)

            return True

        except Exception as e:
            logger.error(f"Error storing data: {str(e)}")
            return False
