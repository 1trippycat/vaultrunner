"""Docker integration commands for VaultRunner."""

import os
import yaml
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
from ..utils.logging import get_logger

logger = get_logger(__name__)


def register_docker_parser(subparsers):
    """Register docker command parser."""
    parser = subparsers.add_parser("docker", help="Docker integration")
    subparsers_docker = parser.add_subparsers(
        dest="docker_command", help="Docker commands"
    )

    # Start command
    start_parser = subparsers_docker.add_parser(
        "start", help="Start VaultRunner with network integration"
    )
    start_parser.add_argument(
        "--project-dir", help="Project directory to scan for docker-compose files"
    )
    start_parser.add_argument("--network", help="Specific network to join")
    start_parser.add_argument(
        "--sidecar",
        action="store_true",
        help="Add VaultRunner as sidecar to existing compose",
    )

    # Stop command
    stop_parser = subparsers_docker.add_parser("stop", help="Stop VaultRunner")

    # Status command
    status_parser = subparsers_docker.add_parser(
        "status", help="Show VaultRunner status"
    )

    # Network command
    network_parser = subparsers_docker.add_parser("network", help="Network management")
    network_parser.add_argument(
        "action", choices=["detect", "join", "list"], help="Network action"
    )
    network_parser.add_argument("--project-dir", help="Project directory to scan")


class DockerCommand:
    """Docker integration command handler."""

    def __init__(self, config):
        self.config = config

    def execute(self, args):
        """Execute docker command."""
        command = getattr(args, "docker_command", None)

        if command == "start":
            return self._start_vault(args)
        elif command == "stop":
            return self._stop_vault(args)
        elif command == "status":
            return self._show_status(args)
        elif command == "network":
            return self._handle_network(args)
        else:
            print("Docker integration commands:")
            print("  start     - Start VaultRunner with network integration")
            print("  stop      - Stop VaultRunner")
            print("  status    - Show VaultRunner status")
            print("  network   - Network management")
            return 0

    def _start_vault(self, args) -> int:
        """Start VaultRunner with network integration."""
        try:
            project_dir = args.project_dir or os.getcwd()
            network_name = args.network

            # Detect existing networks if not specified
            if not network_name:
                network_name = self._detect_project_network(project_dir)

            if network_name:
                logger.info(f"Detected/joining network: {network_name}")
            else:
                logger.info("No existing network detected, using default")

            # If sidecar mode requested, modify docker-compose
            if args.sidecar:
                self._add_sidecar_to_compose(project_dir)

            # Start VaultRunner with network configuration
            return self._start_vault_container(network_name)

        except Exception as e:
            logger.error(f"Failed to start VaultRunner: {e}")
            return 1

    def _detect_project_network(self, project_dir: str) -> Optional[str]:
        """Detect Docker network from existing docker-compose files."""
        compose_files = self._find_compose_files(project_dir)

        for compose_file in compose_files:
            try:
                with open(compose_file, "r") as f:
                    compose_data = yaml.safe_load(f)

                networks = compose_data.get("networks", {})
                if networks:
                    # Return the first network name
                    network_name = list(networks.keys())[0]
                    logger.info(f"Found network '{network_name}' in {compose_file}")
                    return network_name

            except Exception as e:
                logger.warning(f"Failed to parse {compose_file}: {e}")
                continue

        return None

    def _find_compose_files(self, project_dir: str) -> list:
        """Find docker-compose files in project directory."""
        compose_files = []
        project_path = Path(project_dir)

        # Check current directory and parent directories
        for path in [project_path] + list(project_path.parents):
            for filename in [
                "docker-compose.yml",
                "docker-compose.yaml",
                "compose.yml",
                "compose.yaml",
            ]:
                compose_file = path / filename
                if compose_file.exists():
                    compose_files.append(str(compose_file))

        return compose_files

    def _add_sidecar_to_compose(self, project_dir: str) -> None:
        """Add VaultRunner as a sidecar service to existing docker-compose file."""
        compose_files = self._find_compose_files(project_dir)

        if not compose_files:
            logger.warning("No docker-compose file found to modify")
            return

        compose_file = compose_files[0]  # Use the first one found
        logger.info(f"Adding VaultRunner sidecar to {compose_file}")

        try:
            with open(compose_file, "r") as f:
                compose_data = yaml.safe_load(f) or {}

            # Ensure services section exists
            if "services" not in compose_data:
                compose_data["services"] = {}

            # Add VaultRunner service
            compose_data["services"]["vaultrunner"] = {
                "image": "vaultrunner:latest",
                "container_name": "vaultrunner-sidecar",
                "environment": {
                    "VAULT_ADDR": "http://vault:8200",
                    "VAULT_TOKEN": "${VAULT_TOKEN:-}",
                    "VAULTRUNNER_ENV": "docker",
                },
                "volumes": [
                    ".:/workspace:rw",
                    "/var/run/docker.sock:/var/run/docker.sock:ro",
                ],
                "working_dir": "/workspace",
                "depends_on": ["vault"] if "vault" in compose_data["services"] else [],
                "profiles": ["vaultrunner"],
            }

            # Ensure networks section exists and add vaultrunner network
            if "networks" not in compose_data:
                compose_data["networks"] = {}

            # Write back the modified compose file
            with open(compose_file, "w") as f:
                yaml.dump(compose_data, f, default_flow_style=False, sort_keys=False)

            logger.info("VaultRunner sidecar added to docker-compose file")

        except Exception as e:
            logger.error(f"Failed to modify docker-compose file: {e}")

    def _start_vault_container(self, network_name: Optional[str] = None) -> int:
        """Start VaultRunner container with network configuration."""
        try:
            cmd = ["docker", "run", "-d"]

            if network_name:
                cmd.extend(["--network", network_name])

            cmd.extend(
                [
                    "--name",
                    "vaultrunner",
                    "--env",
                    f'VAULT_ADDR={self.config.vault_addr or "http://vault:8200"}',
                    "--env",
                    f'VAULT_TOKEN={self.config.vault_token or ""}',
                    "--volume",
                    f"{os.getcwd()}:/workspace:rw",
                    "--volume",
                    "/var/run/docker.sock:/var/run/docker.sock:ro",
                    "vaultrunner:latest",
                ]
            )

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("VaultRunner container started successfully")
                return 0
            else:
                logger.error(f"Failed to start container: {result.stderr}")
                return 1

        except Exception as e:
            logger.error(f"Failed to start VaultRunner container: {e}")
            return 1

    def _stop_vault(self, args) -> int:
        """Stop VaultRunner container."""
        try:
            result = subprocess.run(
                ["docker", "stop", "vaultrunner"], capture_output=True, text=True
            )
            if result.returncode == 0:
                logger.info("VaultRunner container stopped")
                return 0
            else:
                logger.warning(f"Failed to stop container: {result.stderr}")
                return 1
        except Exception as e:
            logger.error(f"Failed to stop VaultRunner: {e}")
            return 1

    def _show_status(self, args) -> int:
        """Show VaultRunner status."""
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", "name=vaultrunner"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                if "vaultrunner" in result.stdout:
                    print("VaultRunner container is running")
                    return 0
                else:
                    print("VaultRunner container is not running")
                    return 1
            else:
                logger.error(f"Failed to check status: {result.stderr}")
                return 1
        except Exception as e:
            logger.error(f"Failed to check VaultRunner status: {e}")
            return 1

    def _handle_network(self, args) -> int:
        """Handle network-related commands."""
        if args.action == "detect":
            project_dir = args.project_dir or os.getcwd()
            network = self._detect_project_network(project_dir)
            if network:
                print(f"Detected network: {network}")
                return 0
            else:
                print("No network detected")
                return 1

        elif args.action == "join":
            print("Network joining is handled automatically during 'docker start'")
            return 0

        elif args.action == "list":
            try:
                result = subprocess.run(
                    ["docker", "network", "ls"], capture_output=True, text=True
                )
                if result.returncode == 0:
                    print(result.stdout)
                    return 0
                else:
                    logger.error(f"Failed to list networks: {result.stderr}")
                    return 1
            except Exception as e:
                logger.error(f"Failed to list networks: {e}")
                return 1

        return 0
