"""
MCP Server Command - Model Context Protocol Server

Provides MCP server functionality for VaultRunner, exposing tools for
secret management, deployment automation, and migration workflows.
"""

import json
import sys
from typing import Any, Dict, List, Optional

from ..utils.logging import get_logger
from ..security.key_manager import SecureKeyManager
from ..models.config import VaultRunnerConfig

logger = get_logger(__name__)


class VaultRunnerMCPServer:
    """MCP Server implementation for VaultRunner."""

    def __init__(self, port: int = 3000, vault_addr: Optional[str] = None, vault_token: Optional[str] = None):
        self.port = port
        self.vault_addr = vault_addr
        self.vault_token = vault_token
        self.config = VaultRunnerConfig()
        self.key_manager = SecureKeyManager(self.config.vault_dir)

    def initialize(self):
        """Initialize the MCP server with VaultRunner components."""
        try:
            if self.vault_addr:
                self.config.vault_addr = self.vault_addr
            if self.vault_token:
                self.config.vault_token = self.vault_token

            logger.info("MCP Server initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize MCP server: {e}")
            raise

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available MCP tools."""
        tools = [
            {
                "name": "vault_secure_init",
                "description": "Initialize secure vault with password protection",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "password": {"type": "string", "description": "Master password for vault"}
                    },
                    "required": ["password"]
                }
            },
            {
                "name": "vault_generate_ssl",
                "description": "Generate SSL certificates for Vault",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "common_name": {"type": "string", "description": "Common name for certificate"}
                    }
                }
            },
            {
                "name": "vault_encrypt_key",
                "description": "Encrypt a vault key with password protection",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "vault_key": {"type": "string", "description": "Vault key to encrypt"},
                        "password": {"type": "string", "description": "Password for encryption"}
                    },
                    "required": ["vault_key", "password"]
                }
            },
            {
                "name": "vault_decrypt_key",
                "description": "Decrypt a vault key",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "encrypted_key": {"type": "string", "description": "Encrypted key data"},
                        "password": {"type": "string", "description": "Password for decryption"}
                    },
                    "required": ["encrypted_key", "password"]
                }
            },
            {
                "name": "vault_export_key",
                "description": "Export encrypted vault key for backup",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "password": {"type": "string", "description": "Password to decrypt key"}
                    },
                    "required": ["password"]
                }
            }
        ]
        return tools

    def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP tool calls."""
        try:
            if tool_name == "vault_secure_init":
                return self._handle_secure_init(arguments)
            elif tool_name == "vault_generate_ssl":
                return self._handle_generate_ssl(arguments)
            elif tool_name == "vault_encrypt_key":
                return self._handle_encrypt_key(arguments)
            elif tool_name == "vault_decrypt_key":
                return self._handle_decrypt_key(arguments)
            elif tool_name == "vault_export_key":
                return self._handle_export_key(arguments)
            else:
                return {"error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            logger.error(f"Error handling tool call {tool_name}: {e}")
            return {"error": str(e)}

    def _handle_secure_init(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle vault_secure_init tool call."""
        try:
            password = args["password"]
            result = self.key_manager.initialize_secure_vault(password)
            return {
                "result": "Secure vault initialized successfully",
                "vault_key": result["vault_key"],
                "ssl_certificate": result["ssl_certificate"],
                "ssl_private_key": result["ssl_private_key"]
            }
        except Exception as e:
            return {"error": f"Failed to initialize secure vault: {e}"}

    def _handle_generate_ssl(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle vault_generate_ssl tool call."""
        try:
            common_name = args.get("common_name", "localhost")
            result = self.key_manager.generate_ssl_certificate(common_name)
            return {
                "result": "SSL certificate generated successfully",
                "certificate": result["certificate"],
                "private_key": result["private_key"]
            }
        except Exception as e:
            return {"error": f"Failed to generate SSL certificate: {e}"}

    def _handle_encrypt_key(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle vault_encrypt_key tool call."""
        try:
            vault_key = args["vault_key"]
            password = args["password"]
            encrypted_key = self.key_manager.encrypt_vault_key(vault_key, password)
            return {
                "result": "Vault key encrypted successfully",
                "encrypted_key": encrypted_key
            }
        except Exception as e:
            return {"error": f"Failed to encrypt vault key: {e}"}

    def _handle_decrypt_key(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle vault_decrypt_key tool call."""
        try:
            encrypted_key = args["encrypted_key"]
            password = args["password"]
            vault_key = self.key_manager.decrypt_vault_key(encrypted_key, password)
            return {
                "result": "Vault key decrypted successfully",
                "vault_key": vault_key
            }
        except Exception as e:
            return {"error": f"Failed to decrypt vault key: {e}"}

    def _handle_export_key(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle vault_export_key tool call."""
        try:
            password = args["password"]
            vault_key = self.key_manager.export_vault_key(password)
            if vault_key:
                return {
                    "result": "Vault key exported successfully",
                    "vault_key": vault_key
                }
            else:
                return {"error": "Failed to export vault key - invalid password or no key found"}
        except Exception as e:
            return {"error": f"Failed to export vault key: {e}"}

    def start_server(self):
        """Start the MCP server."""
        self.initialize()

        # Simple HTTP server using built-in modules
        from http.server import HTTPServer, BaseHTTPRequestHandler
        import urllib.parse

        class MCPHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/tools":
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    tools = self.server.mcp_server.get_available_tools()  # type: ignore
                    self.wfile.write(json.dumps({"tools": tools}).encode())
                else:
                    self.send_response(404)
                    self.end_headers()

            def do_POST(self):
                if self.path == "/call":
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    try:
                        data = json.loads(post_data.decode())
                        tool_name = data.get("tool")
                        arguments = data.get("arguments", {})

                        result = self.server.mcp_server.handle_tool_call(tool_name, arguments)  # type: ignore
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps(result).encode())
                    except Exception as e:
                        self.send_response(500)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({"error": str(e)}).encode())
                else:
                    self.send_response(404)
                    self.end_headers()

        # Create server with MCP server instance
        server = HTTPServer(('localhost', self.port), MCPHandler)
        # Store reference to MCP server instance
        server.mcp_server = self  # type: ignore

        logger.info(f"Starting MCP server on port {self.port}")
        logger.info("Available endpoints:")
        logger.info("  GET  /tools - List available tools")
        logger.info("  POST /call  - Execute tool calls")

        try:
            server.serve_forever()
        except KeyboardInterrupt:
            logger.info("MCP Server stopped by user")
            server.shutdown()


def register_mcp_parser(subparsers):
    """Register MCP server parser."""
    mcp_parser = subparsers.add_parser(
        "mcp-server",
        help="Run VaultRunner as an MCP server",
        description="Start VaultRunner as a Model Context Protocol server"
    )

    mcp_parser.add_argument(
        "--port",
        type=int,
        default=3000,
        help="Port to run MCP server on (default: 3000)"
    )

    mcp_parser.add_argument(
        "--vault-addr",
        type=str,
        help="Vault server address"
    )

    mcp_parser.add_argument(
        "--vault-token",
        type=str,
        help="Vault authentication token"
    )

    mcp_parser.set_defaults(func=run_mcp_server)


def run_mcp_server(args):
    """Run the MCP server."""
    server = VaultRunnerMCPServer(
        port=args.port,
        vault_addr=args.vault_addr,
        vault_token=args.vault_token
    )

    try:
        server.start_server()
    except KeyboardInterrupt:
        logger.info("MCP Server stopped by user")
    except Exception as e:
        logger.error(f"MCP Server error: {e}")
        return 1

    return 0