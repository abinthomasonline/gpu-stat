"""
Data collector module for GPU-Stat.
Collects GPU statistics from remote machines.
"""

import logging
import time
from datetime import datetime
from typing import Any, Dict, Optional

from .ssh_client import SSHClient

logger = logging.getLogger(__name__)

# Command to get GPU stats in JSON format
NVIDIA_SMI_CMD = "nvidia-smi --query-gpu=index,name,utilization.gpu,utilization.memory,memory.total,memory.used,memory.free,temperature.gpu,power.draw,power.limit,fan.speed --format=csv,noheader,nounits"

# Command to get process information
NVIDIA_SMI_PROCESS_CMD = "nvidia-smi --query-compute-apps=pid,process_name,gpu_uuid,used_memory --format=csv,noheader,nounits"

# Command to get GPU UUIDs
NVIDIA_SMI_UUID_CMD = "nvidia-smi --query-gpu=index,uuid --format=csv,noheader,nounits"


class GPUDataCollector:
    """Collects GPU statistics from remote machines."""

    def __init__(self, server_config: Dict[str, Any]):
        """
        Initialize GPU data collector.

        Args:
            server_config: Server configuration dictionary
        """
        self.server_config = server_config
        self.server_name = server_config["name"]

        # Create SSH client with appropriate authentication method
        ssh_params = {
            "host": server_config["host"],
            "username": server_config["user"],
            "port": server_config.get("port", 22),
            "key_path": server_config["key_path"],
        }
        self.ssh_client = SSHClient(**ssh_params)

    def collect_gpu_stats(self) -> Optional[Dict[str, Any]]:
        """
        Collect GPU statistics from remote server.

        Returns:
            Dictionary containing GPU stats or None if failed
        """
        # Get basic GPU stats
        success, gpu_stats_output, stderr = self.ssh_client.execute_command(
            NVIDIA_SMI_CMD
        )
        if not success:
            logger.error(
                f"Failed to collect GPU stats from {self.server_name}: {stderr}"
            )
            return None

        # Get GPU UUIDs
        success, gpu_uuid_output, stderr = self.ssh_client.execute_command(
            NVIDIA_SMI_UUID_CMD
        )
        if not success:
            logger.error(
                f"Failed to collect GPU UUIDs from {self.server_name}: {stderr}"
            )
            return None

        # Get process info
        success, process_output, stderr = self.ssh_client.execute_command(
            NVIDIA_SMI_PROCESS_CMD
        )
        if not success:
            logger.warning(
                f"Failed to collect process info from {self.server_name}: {stderr}"
            )
            return None

        # Parse the output
        timestamp = datetime.now().isoformat()

        # Parse GPU stats
        gpus = []
        uuid_map = {}

        # Parse UUID mapping
        for line in gpu_uuid_output.strip().split("\n"):
            if line.strip():
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 2:
                    idx, uuid = parts
                    uuid_map[idx] = uuid

        # Parse GPU stats
        for line in gpu_stats_output.strip().split("\n"):
            if line.strip():
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 11:
                    (
                        idx,
                        name,
                        util_gpu,
                        util_mem,
                        mem_total,
                        mem_used,
                        mem_free,
                        temp,
                        power_draw,
                        power_limit,
                        fan,
                    ) = parts

                    gpu_data = {
                        "index": int(idx),
                        "name": name,
                        "uuid": uuid_map.get(idx, "unknown"),
                        "utilization_gpu": float(util_gpu),
                        "utilization_memory": float(util_mem),
                        "memory_total": float(mem_total),
                        "memory_used": float(mem_used),
                        "memory_free": float(mem_free),
                        "temperature": float(temp),
                        "power_draw": float(power_draw),
                        "power_limit": float(power_limit),
                        "fan_speed": float(fan) if fan else 0,
                        "processes": [],
                    }
                    gpus.append(gpu_data)

        # Parse process info and add to corresponding GPUs
        for line in process_output.strip().split("\n"):
            if line.strip():
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 4:
                    pid, name, gpu_uuid, used_memory = parts

                    process_data = {
                        "pid": int(pid),
                        "name": name,
                        "used_memory": float(used_memory),
                    }

                    # Add process to corresponding GPU
                    for gpu in gpus:
                        if gpu["uuid"] == gpu_uuid:
                            gpu["processes"].append(process_data)
                            break

        # Combine data
        data = {
            "timestamp": timestamp,
            "server": self.server_name,
            "host": self.server_config["host"],
            "gpus": gpus,
        }

        return data

    def start_collection(
        self, interval: int = 5, callback=None, max_retries: int = 3
    ) -> None:
        """
        Start collecting GPU stats at regular intervals.

        Args:
            interval: Time between collections in seconds
            callback: Function to call with collected data
            max_retries: Maximum number of consecutive failed collections
        """
        retry_count = 0

        try:
            logger.info(
                f"Starting GPU stats collection for {self.server_name} every {interval} seconds"
            )

            while True:
                try:
                    # Collect stats
                    data = self.collect_gpu_stats()

                    if data:
                        # Reset retry counter on success
                        retry_count = 0

                        # Call the callback with the data if provided
                        if callback:
                            callback(data)
                    else:
                        retry_count += 1
                        if retry_count >= max_retries:
                            logger.error(
                                f"Max retries exceeded for {self.server_name}. Exiting..."
                            )
                            break
                        else:
                            logger.warning(
                                f"Failed to collect data from {self.server_name}. Retry {retry_count}/{max_retries}"
                            )
                            continue

                    # Wait for the next interval
                    time.sleep(interval)

                except KeyboardInterrupt:
                    logger.info(f"Collection stopped for {self.server_name}")
                    break

                except Exception as e:
                    logger.error(
                        f"Error during collection for {self.server_name}: {str(e)}"
                    )
                    break

        finally:
            # Ensure the connection is closed
            self.ssh_client.disconnect()
