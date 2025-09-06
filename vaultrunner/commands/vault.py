"""Vault deployment and management commands."""

import os
import yaml
import subprocess
from pathlib import Path
from typing import Optional
from ..utils.logging import get_logger

logger = get_logger(__name__)


def register_vault_parser(subparsers):
    """Register vault command parser."""
    parser = subparsers.add_parser("vault", help="Vault deployment and management")
    subparsers_vault = parser.add_subparsers(
        dest="vault_command", help="Vault commands"
    )

    # Deploy command
    deploy_parser = subparsers_vault.add_parser("deploy", help="Deploy Vault server")
    deploy_parser.add_argument(
        "--project-dir", help="Project directory to integrate with"
    )
    deploy_parser.add_argument("--network", help="Docker network to join")
    deploy_parser.add_argument(
        "--dev", action="store_true", help="Deploy in development mode"
    )
    deploy_parser.add_argument("--ui", action="store_true", help="Enable Vault UI")
    deploy_parser.add_argument(
        "--create-networks",
        action="store_true",
        help="Create external networks from docker-compose file",
    )

    # Status command
    status_parser = subparsers_vault.add_parser(
        "status", help="Show Vault server status"
    )

    # Stop command
    stop_parser = subparsers_vault.add_parser("stop", help="Stop Vault server")


class VaultCommand:
    """Vault deployment command handler."""

    def __init__(self, config):
        self.config = config

    def execute(self, args):
        """Execute vault command."""
        command = getattr(args, "vault_command", None)

        if command == "deploy":
            return self._deploy_vault(args)
        elif command == "status":
            return self._vault_status(args)
        elif command == "stop":
            return self._stop_vault(args)
        else:
            print("Vault deployment commands:")
            print("  deploy    - Deploy Vault server with network integration")
            print("  status    - Show Vault server status")
            print("  stop      - Stop Vault server")
            return 0

    def _deploy_vault(self, args) -> int:
        """Deploy Vault server with network integration."""
        try:
            project_dir = args.project_dir or os.getcwd()
            network_name = args.network

            # Detect existing networks if not specified
            if not network_name:
                network_name = self._detect_project_network(project_dir)

            if network_name:
                logger.info(f"Deploying Vault on network: {network_name}")
            else:
                logger.info("Deploying Vault on default network")

            # Create external networks if requested
            if getattr(args, "create_networks", False):
                self._create_external_networks(project_dir)

            # Deploy Vault server
            return self._start_vault_server(network_name, args.dev, args.ui)

        except Exception as e:
            logger.error(f"Failed to deploy Vault: {e}")
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

    def _create_external_networks(self, project_dir: str) -> None:
        """Create external networks from docker-compose file."""
        compose_files = self._find_compose_files(project_dir)

        for compose_file in compose_files:
            try:
                with open(compose_file, "r", encoding="utf-8") as f:
                    compose_data = yaml.safe_load(f)

                networks = compose_data.get("networks", {})
                if not networks:
                    continue

                for network_name, network_config in networks.items():
                    if self._network_exists_externally(network_name):
                        logger.info(f"External network '{network_name}' already exists")
                        continue

                    # Create the external network
                    self._create_external_network(network_name, network_config)

                    # Update the compose file to reference external network
                    self._update_compose_for_external_network(
                        compose_file, network_name
                    )

            except Exception as e:
                logger.warning(f"Failed to process networks in {compose_file}: {e}")

    def _network_exists_externally(self, network_name: str) -> bool:
        """Check if a Docker network exists externally."""
        try:
            result = subprocess.run(
                ["docker", "network", "ls", "--format", "{{.Name}}"],
                capture_output=True,
                text=True,
                check=True,
            )
            networks = result.stdout.strip().split("\n")
            return network_name in networks
        except subprocess.CalledProcessError:
            return False

    def _create_external_network(self, network_name: str, network_config: dict) -> None:
        """Create an external Docker network."""
        try:
            cmd = ["docker", "network", "create"]

            # Add network driver if specified
            driver = network_config.get("driver", "bridge")
            cmd.extend(["--driver", driver])

            # Add network options
            if "driver_opts" in network_config:
                for key, value in network_config["driver_opts"].items():
                    cmd.extend(["--opt", f"{key}={value}"])

            # Add network labels
            if "labels" in network_config:
                for key, value in network_config["labels"].items():
                    cmd.extend(["--label", f"{key}={value}"])

            cmd.append(network_name)

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"Created external network '{network_name}'")

        except subprocess.CalledProcessError as e:
            logger.error(
                f"Failed to create external network '{network_name}': {e.stderr}"
            )

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

    def _update_compose_for_external_network(
        self, compose_file: str, network_name: str
    ) -> None:
        """Update docker-compose file to reference external network."""
        try:
            with open(compose_file, "r", encoding="utf-8") as f:
                compose_data = yaml.safe_load(f)

            # Update network configuration to be external
            if "networks" not in compose_data:
                compose_data["networks"] = {}

            compose_data["networks"][network_name] = {
                "external": True,
                "name": network_name,
            }

            # Write back the updated compose file
            with open(compose_file, "w", encoding="utf-8") as f:
                yaml.dump(compose_data, f, default_flow_style=False, sort_keys=False)

            logger.info(
                f"Updated {compose_file} to use external network '{network_name}'"
            )

        except Exception as e:
            logger.error(f"Failed to update compose file for external network: {e}")

    def _start_vault_server(
        self,
        network_name: Optional[str] = None,
        dev_mode: bool = False,
        enable_ui: bool = False,
    ) -> int:
        """Start Vault server container."""
        try:
            cmd = ["docker", "run", "-d"]

            if network_name:
                cmd.extend(["--network", network_name])

            # Set container name based on network
            container_name = f"vault-{network_name}" if network_name else "vault"
            cmd.extend(["--name", container_name])

            # Basic Vault configuration
            cmd.extend(
                [
                    "--env",
                    "VAULT_DEV_ROOT_TOKEN_ID=myroot",
                    "--env",
                    "VAULT_DEV_LISTEN_ADDRESS=0.0.0.0:8200",
                    "--env",
                    "VAULT_ADDR=http://0.0.0.0:8200",
                    "--volume",
                    "vault-data:/vault/data",
                    "--volume",
                    "vault-config:/vault/config",
                    "--volume",
                    "vault-logs:/vault/logs",
                    "--cap-add",
                    "IPC_LOCK",
                ]
            )

            # Add port mapping for external access
            if dev_mode:
                cmd.extend(["--publish", "8200:8200"])

            # Add UI port if requested
            if enable_ui:
                cmd.extend(["--publish", "8201:8200"])

            # Use dev mode or server mode
            if dev_mode:
                cmd.extend(["hashicorp/vault:latest", "vault", "server", "-dev"])
            else:
                cmd.extend(
                    [
                        "hashicorp/vault:latest",
                        "vault",
                        "server",
                        "-config=/vault/config/vault.hcl",
                    ]
                )

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(
                    f"Vault server started successfully (container: {container_name})"
                )
                if dev_mode:
                    logger.info("Vault UI available at: http://localhost:8200")
                    logger.info("Root token: myroot")
                return 0
            else:
                logger.error(f"Failed to start Vault server: {result.stderr}")
                return 1

        except Exception as e:
            logger.error(f"Failed to start Vault server: {e}")
            return 1

    def _vault_status(self, args) -> int:
        """Show Vault server status."""
        try:
            # Check if Vault container is running
            result = subprocess.run(
                [
                    "docker",
                    "ps",
                    "--filter",
                    "name=vault",
                    "--format",
                    "table {{.Names}}\t{{.Status}}\t{{.Ports}}",
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                if "vault" in result.stdout:
                    print("Vault server status:")
                    print(result.stdout)
                    return 0
                else:
                    print("No Vault server containers found")
                    return 1
            else:
                logger.error(f"Failed to check Vault status: {result.stderr}")
                return 1
        except Exception as e:
            logger.error(f"Failed to check Vault status: {e}")
            return 1

    def _stop_vault(self, args) -> int:
        """Stop Vault server."""
        try:
            # Stop all vault containers
            result = subprocess.run(
                ["docker", "stop", "vault"], capture_output=True, text=True
            )
            if result.returncode == 0:
                logger.info("Vault server stopped")
                return 0
            else:
                logger.warning(f"Failed to stop Vault server: {result.stderr}")
                return 1
        except Exception as e:
            logger.error(f"Failed to stop Vault server: {e}")
            return 1
