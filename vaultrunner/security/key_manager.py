"""
Secure Key Management Module

Provides secure storage, encryption, and management of Vault keys and certificates.
Implements password-based encryption with SSL certificate generation.
"""

import json
import base64
import secrets
from pathlib import Path
from typing import Optional, Dict, Any
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography import x509
from cryptography.x509.oid import NameOID
from datetime import datetime, timedelta

from ..utils.logging import get_logger

logger = get_logger(__name__)


class SecureKeyManager:
    """Manages secure storage and encryption of Vault keys and certificates."""

    def __init__(self, vault_dir: Path):
        self.vault_dir = vault_dir
        self.keys_dir = vault_dir / "keys"
        self.certs_dir = vault_dir / "certs"
        self.keys_dir.mkdir(parents=True, exist_ok=True)
        self.certs_dir.mkdir(parents=True, exist_ok=True)

    def generate_ssl_certificate(self, common_name: str = "localhost") -> Dict[str, str]:
        """
        Generate SSL certificate and private key for Vault.

        Args:
            common_name: Common name for the certificate

        Returns:
            Dict containing cert and key file paths
        """
        logger.info("Generating SSL certificate for %s", common_name)

        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )

        # Generate certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "CA"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "VaultRunner"),
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        ])

        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName(common_name),
                x509.DNSName("localhost"),
                x509.DNSName("127.0.0.1"),
            ]),
            critical=False,
        ).sign(private_key, hashes.SHA256(), default_backend())

        # Save certificate
        cert_path = self.certs_dir / "vault.crt"
        with open(cert_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))

        # Save private key
        key_path = self.certs_dir / "vault.key"
        with open(key_path, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))

        logger.info("SSL certificate generated: %s", cert_path)
        logger.info("SSL private key generated: %s", key_path)

        return {
            "certificate": str(cert_path),
            "private_key": str(key_path)
        }

    def encrypt_vault_key(self, vault_key: str, password: str) -> str:
        """
        Encrypt the Vault root key with password-based encryption.

        Args:
            vault_key: The Vault root token/key to encrypt
            password: User password for encryption

        Returns:
            Encrypted key data as base64 string
        """
        logger.info("Encrypting Vault key with password protection")

        # Generate salt
        salt = secrets.token_bytes(16)

        # Derive key from password
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = kdf.derive(password.encode())

        # Generate IV
        iv = secrets.token_bytes(16)

        # Encrypt the vault key
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()

        # Pad the data to block size
        data = vault_key.encode()
        block_size = 16
        padding_length = block_size - (len(data) % block_size)
        padded_data = data + bytes([padding_length]) * padding_length

        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()

        # Combine salt, IV, and encrypted data
        combined = salt + iv + encrypted_data

        # Return as base64
        encrypted_b64 = base64.b64encode(combined).decode()

        logger.info("Vault key encrypted successfully")
        return encrypted_b64

    def decrypt_vault_key(self, encrypted_key: str, password: str) -> str:
        """
        Decrypt the Vault root key.

        Args:
            encrypted_key: Encrypted key data as base64 string
            password: User password for decryption

        Returns:
            Decrypted Vault root key
        """
        logger.info("Decrypting Vault key")

        # Decode from base64
        combined = base64.b64decode(encrypted_key)

        # Extract salt, IV, and encrypted data
        salt = combined[:16]
        iv = combined[16:32]
        encrypted_data = combined[32:]

        # Derive key from password
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = kdf.derive(password.encode())

        # Decrypt
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()

        padded_data = decryptor.update(encrypted_data) + decryptor.finalize()

        # Remove padding
        padding_length = padded_data[-1]
        data = padded_data[:-padding_length]

        vault_key = data.decode()
        logger.info("Vault key decrypted successfully")
        return vault_key

    def store_encrypted_key(self, encrypted_key: str, metadata: Dict[str, Any]) -> None:
        """
        Store encrypted key and metadata securely.

        Args:
            encrypted_key: Encrypted key data
            metadata: Additional metadata
        """
        key_data = {
            "encrypted_key": encrypted_key,
            "metadata": metadata,
            "created_at": datetime.utcnow().isoformat(),
            "version": "1.0"
        }

        key_file = self.keys_dir / "vault_key.enc"
        with open(key_file, "w", encoding="utf-8") as f:
            json.dump(key_data, f, indent=2)

        logger.info("Encrypted Vault key stored at: %s", key_file)

    def load_encrypted_key(self) -> Optional[Dict[str, Any]]:
        """
        Load encrypted key and metadata.

        Returns:
            Key data dict or None if not found
        """
        key_file = self.keys_dir / "vault_key.enc"
        if not key_file.exists():
            return None

        with open(key_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def export_vault_key(self, password: str) -> Optional[str]:
        """
        Export the Vault key after password verification.

        Args:
            password: User password to decrypt the key

        Returns:
            Vault root key or None if decryption fails
        """
        logger.info("Exporting Vault key")

        key_data = self.load_encrypted_key()
        if not key_data:
            logger.error("No encrypted key found")
            return None

        try:
            vault_key = self.decrypt_vault_key(key_data["encrypted_key"], password)
            logger.info("Vault key exported successfully")
            return vault_key
        except (ValueError, RuntimeError) as e:
            logger.error("Failed to decrypt Vault key: %s", e)
            return None

    def initialize_secure_vault(self, password: str) -> Dict[str, Any]:
        """
        Initialize a new secure Vault setup.

        Args:
            password: User password for key encryption

        Returns:
            Dict with vault key and certificate info
        """
        logger.info("Initializing secure Vault setup")

        # Generate SSL certificate
        ssl_info = self.generate_ssl_certificate()

        # Generate a secure Vault root token
        vault_key = secrets.token_hex(32)

        # Encrypt the vault key
        encrypted_key = self.encrypt_vault_key(vault_key, password)

        # Store encrypted key
        metadata = {
            "ssl_certificate": ssl_info["certificate"],
            "ssl_private_key": ssl_info["private_key"],
            "vault_initialized": datetime.utcnow().isoformat()
        }
        self.store_encrypted_key(encrypted_key, metadata)

        logger.info("Secure Vault initialization completed")

        return {
            "vault_key": vault_key,
            "ssl_certificate": ssl_info["certificate"],
            "ssl_private_key": ssl_info["private_key"]
        }

    def get_vault_config_with_ssl(self) -> Dict[str, Any]:
        """
        Get Vault configuration with SSL settings.

        Returns:
            Vault configuration dict
        """
        cert_path = self.certs_dir / "vault.crt"
        key_path = self.certs_dir / "vault.key"

        if not cert_path.exists() or not key_path.exists():
            raise FileNotFoundError("SSL certificates not found. Run secure initialization first.")

        return {
            "listener": {
                "tcp": {
                    "address": "0.0.0.0:8200",
                    "tls_cert_file": str(cert_path),
                    "tls_key_file": str(key_path)
                }
            },
            "storage": {
                "file": {
                    "path": "/vault/data"
                }
            },
            "ui": True
        }