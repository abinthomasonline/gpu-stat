"""
SSH client module for GPU-Stat.
Handles connections to remote machines to execute commands.
"""

import logging
import os
from typing import Tuple

import paramiko

logger = logging.getLogger(__name__)


class SSHClient:
    """SSH client to connect to remote servers and execute commands."""

    def __init__(
        self,
        host: str,
        username: str,
        key_path: str,
        port: int = 22,
        connect_timeout: int = 10,
    ):
        """
        Initialize SSH client.

        Args:
            host: Hostname or IP address
            username: SSH username
            key_path: Path to SSH private key
            port: SSH port (default: 22)
            connect_timeout: Connection timeout in seconds
        """
        self.host = host
        self.username = username
        self.key_path = os.path.expanduser(key_path) if key_path else None
        self.port = port
        self.connect_timeout = connect_timeout
        self.client = None

    def connect(self) -> bool:
        """
        Establish SSH connection to the remote server.

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            logger.info(f"Connecting to {self.username}@{self.host}:{self.port}")

            self.client.connect(
                self.host,
                self.port,
                self.username,
                key_filename=self.key_path,
                timeout=self.connect_timeout,
            )
            self.client.get_transport().set_keepalive(10)
            return True
        except Exception as e:
            logger.error(f"Error connecting to {self.host}: {str(e)}")
            return False

    def execute_command(self, command: str) -> Tuple[bool, str, str]:
        """
        Execute command on remote server.

        Args:
            command: Command to execute

        Returns:
            Tuple of (success, stdout, stderr)
        """
        if (
            self.client is None
            or self.client.get_transport() is None
            or not self.client.get_transport().is_active()
        ):
            connected = self.connect()
            if not connected:
                return False, "", "Unable to connect to server"

        try:
            logger.debug(f"Executing command: {command}")
            stdin, stdout, stderr = self.client.exec_command(command)

            stdout_str = stdout.read().decode("utf-8").strip()
            stderr_str = stderr.read().decode("utf-8").strip()
            exit_code = stdout.channel.recv_exit_status()

            if exit_code != 0:
                logger.warning(f"Command exited with code {exit_code}: {stderr_str}")
                return False, stdout_str, stderr_str

            return True, stdout_str, stderr_str

        except Exception as e:
            logger.error(f"Error executing command: {str(e)}")
            return False, "", str(e)

    def disconnect(self) -> None:
        """Close SSH connection."""
        if self.client:
            self.client.close()
            self.client = None
            logger.info(f"Disconnected from {self.host}")
