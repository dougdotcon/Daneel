"""
Data encryption for Daneel.

This module provides functionality for encrypting and decrypting sensitive data.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Callable
import os
import base64
import json
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.serialization import (
    load_pem_private_key,
    load_pem_public_key,
    Encoding,
    PrivateFormat,
    PublicFormat,
    NoEncryption,
)

from Daneel.core.common import JSONSerializable
from Daneel.core.loggers import Logger


class EncryptionType(str, Enum):
    """Types of encryption."""
    
    SYMMETRIC = "symmetric"
    ASYMMETRIC = "asymmetric"


class EncryptionError(Exception):
    """Encryption error."""
    pass


class EncryptionManager:
    """Manager for data encryption."""
    
    def __init__(
        self,
        logger: Logger,
        symmetric_key: Optional[str] = None,
        private_key_path: Optional[str] = None,
        public_key_path: Optional[str] = None,
    ):
        """Initialize the encryption manager.
        
        Args:
            logger: Logger instance
            symmetric_key: Symmetric encryption key (if None, a new key is generated)
            private_key_path: Path to the private key file (for asymmetric encryption)
            public_key_path: Path to the public key file (for asymmetric encryption)
        """
        self._logger = logger
        
        # Initialize symmetric encryption
        if symmetric_key:
            self._symmetric_key = symmetric_key.encode()
        else:
            self._symmetric_key = Fernet.generate_key()
            
        self._fernet = Fernet(self._symmetric_key)
        
        # Initialize asymmetric encryption
        self._private_key = None
        self._public_key = None
        
        if private_key_path and os.path.exists(private_key_path):
            with open(private_key_path, "rb") as f:
                private_key_data = f.read()
                self._private_key = load_pem_private_key(private_key_data, password=None)
                
        if public_key_path and os.path.exists(public_key_path):
            with open(public_key_path, "rb") as f:
                public_key_data = f.read()
                self._public_key = load_pem_public_key(public_key_data)
                
        # Generate keys if not provided
        if not self._private_key and not self._public_key:
            self._private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )
            self._public_key = self._private_key.public_key()
            
            # Save the keys if paths are provided
            if private_key_path:
                private_key_data = self._private_key.private_bytes(
                    encoding=Encoding.PEM,
                    format=PrivateFormat.PKCS8,
                    encryption_algorithm=NoEncryption(),
                )
                
                with open(private_key_path, "wb") as f:
                    f.write(private_key_data)
                    
            if public_key_path:
                public_key_data = self._public_key.public_bytes(
                    encoding=Encoding.PEM,
                    format=PublicFormat.SubjectPublicKeyInfo,
                )
                
                with open(public_key_path, "wb") as f:
                    f.write(public_key_data)
                    
    def get_symmetric_key(self) -> str:
        """Get the symmetric encryption key.
        
        Returns:
            Symmetric encryption key
        """
        return self._symmetric_key.decode()
        
    def encrypt_symmetric(self, data: Union[str, bytes]) -> str:
        """Encrypt data using symmetric encryption.
        
        Args:
            data: Data to encrypt
            
        Returns:
            Encrypted data (base64-encoded)
        """
        try:
            # Convert string to bytes if needed
            if isinstance(data, str):
                data = data.encode()
                
            # Encrypt the data
            encrypted = self._fernet.encrypt(data)
            
            # Convert to base64
            return base64.b64encode(encrypted).decode()
            
        except Exception as e:
            self._logger.error(f"Symmetric encryption error: {e}")
            raise EncryptionError(f"Symmetric encryption failed: {e}")
            
    def decrypt_symmetric(self, encrypted_data: str) -> bytes:
        """Decrypt data using symmetric encryption.
        
        Args:
            encrypted_data: Encrypted data (base64-encoded)
            
        Returns:
            Decrypted data
            
        Raises:
            EncryptionError: If decryption fails
        """
        try:
            # Decode from base64
            encrypted = base64.b64decode(encrypted_data)
            
            # Decrypt the data
            decrypted = self._fernet.decrypt(encrypted)
            
            return decrypted
            
        except Exception as e:
            self._logger.error(f"Symmetric decryption error: {e}")
            raise EncryptionError(f"Symmetric decryption failed: {e}")
            
    def encrypt_asymmetric(self, data: Union[str, bytes]) -> str:
        """Encrypt data using asymmetric encryption.
        
        Args:
            data: Data to encrypt
            
        Returns:
            Encrypted data (base64-encoded)
            
        Raises:
            EncryptionError: If encryption fails
        """
        try:
            # Check if public key is available
            if not self._public_key:
                raise EncryptionError("Public key not available for asymmetric encryption")
                
            # Convert string to bytes if needed
            if isinstance(data, str):
                data = data.encode()
                
            # Encrypt the data
            encrypted = self._public_key.encrypt(
                data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )
            
            # Convert to base64
            return base64.b64encode(encrypted).decode()
            
        except Exception as e:
            self._logger.error(f"Asymmetric encryption error: {e}")
            raise EncryptionError(f"Asymmetric encryption failed: {e}")
            
    def decrypt_asymmetric(self, encrypted_data: str) -> bytes:
        """Decrypt data using asymmetric encryption.
        
        Args:
            encrypted_data: Encrypted data (base64-encoded)
            
        Returns:
            Decrypted data
            
        Raises:
            EncryptionError: If decryption fails
        """
        try:
            # Check if private key is available
            if not self._private_key:
                raise EncryptionError("Private key not available for asymmetric decryption")
                
            # Decode from base64
            encrypted = base64.b64decode(encrypted_data)
            
            # Decrypt the data
            decrypted = self._private_key.decrypt(
                encrypted,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )
            
            return decrypted
            
        except Exception as e:
            self._logger.error(f"Asymmetric decryption error: {e}")
            raise EncryptionError(f"Asymmetric decryption failed: {e}")
            
    def encrypt_json(
        self,
        data: Dict[str, Any],
        encryption_type: EncryptionType = EncryptionType.SYMMETRIC,
    ) -> str:
        """Encrypt JSON data.
        
        Args:
            data: JSON data to encrypt
            encryption_type: Type of encryption to use
            
        Returns:
            Encrypted data (base64-encoded)
            
        Raises:
            EncryptionError: If encryption fails
        """
        try:
            # Convert to JSON
            json_data = json.dumps(data)
            
            # Encrypt the data
            if encryption_type == EncryptionType.SYMMETRIC:
                return self.encrypt_symmetric(json_data)
            else:
                return self.encrypt_asymmetric(json_data)
                
        except Exception as e:
            self._logger.error(f"JSON encryption error: {e}")
            raise EncryptionError(f"JSON encryption failed: {e}")
            
    def decrypt_json(
        self,
        encrypted_data: str,
        encryption_type: EncryptionType = EncryptionType.SYMMETRIC,
    ) -> Dict[str, Any]:
        """Decrypt JSON data.
        
        Args:
            encrypted_data: Encrypted data (base64-encoded)
            encryption_type: Type of encryption used
            
        Returns:
            Decrypted JSON data
            
        Raises:
            EncryptionError: If decryption fails
        """
        try:
            # Decrypt the data
            if encryption_type == EncryptionType.SYMMETRIC:
                decrypted = self.decrypt_symmetric(encrypted_data)
            else:
                decrypted = self.decrypt_asymmetric(encrypted_data)
                
            # Parse JSON
            return json.loads(decrypted)
            
        except Exception as e:
            self._logger.error(f"JSON decryption error: {e}")
            raise EncryptionError(f"JSON decryption failed: {e}")
            
    def derive_key_from_password(
        self,
        password: str,
        salt: Optional[bytes] = None,
    ) -> Tuple[bytes, bytes]:
        """Derive a key from a password.
        
        Args:
            password: Password
            salt: Salt for key derivation (if None, a new salt is generated)
            
        Returns:
            Tuple of (key, salt)
        """
        # Generate salt if not provided
        if salt is None:
            salt = os.urandom(16)
            
        # Derive the key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        
        return key, salt
        
    def encrypt_with_password(
        self,
        data: Union[str, bytes],
        password: str,
        salt: Optional[bytes] = None,
    ) -> Tuple[str, bytes]:
        """Encrypt data using a password.
        
        Args:
            data: Data to encrypt
            password: Password for encryption
            salt: Salt for key derivation (if None, a new salt is generated)
            
        Returns:
            Tuple of (encrypted data, salt)
            
        Raises:
            EncryptionError: If encryption fails
        """
        try:
            # Derive the key
            key, salt = self.derive_key_from_password(password, salt)
            
            # Create a Fernet instance
            fernet = Fernet(key)
            
            # Convert string to bytes if needed
            if isinstance(data, str):
                data = data.encode()
                
            # Encrypt the data
            encrypted = fernet.encrypt(data)
            
            # Convert to base64
            return base64.b64encode(encrypted).decode(), salt
            
        except Exception as e:
            self._logger.error(f"Password encryption error: {e}")
            raise EncryptionError(f"Password encryption failed: {e}")
            
    def decrypt_with_password(
        self,
        encrypted_data: str,
        password: str,
        salt: bytes,
    ) -> bytes:
        """Decrypt data using a password.
        
        Args:
            encrypted_data: Encrypted data (base64-encoded)
            password: Password for decryption
            salt: Salt used for key derivation
            
        Returns:
            Decrypted data
            
        Raises:
            EncryptionError: If decryption fails
        """
        try:
            # Derive the key
            key, _ = self.derive_key_from_password(password, salt)
            
            # Create a Fernet instance
            fernet = Fernet(key)
            
            # Decode from base64
            encrypted = base64.b64decode(encrypted_data)
            
            # Decrypt the data
            decrypted = fernet.decrypt(encrypted)
            
            return decrypted
            
        except Exception as e:
            self._logger.error(f"Password decryption error: {e}")
            raise EncryptionError(f"Password decryption failed: {e}")
            
    def encrypt_field(
        self,
        data: Dict[str, Any],
        field: str,
        encryption_type: EncryptionType = EncryptionType.SYMMETRIC,
    ) -> Dict[str, Any]:
        """Encrypt a field in a dictionary.
        
        Args:
            data: Dictionary containing the field to encrypt
            field: Field to encrypt
            encryption_type: Type of encryption to use
            
        Returns:
            Dictionary with the encrypted field
            
        Raises:
            EncryptionError: If encryption fails
        """
        if field not in data:
            return data
            
        # Create a copy of the data
        result = data.copy()
        
        # Encrypt the field
        if encryption_type == EncryptionType.SYMMETRIC:
            result[field] = self.encrypt_symmetric(str(data[field]))
        else:
            result[field] = self.encrypt_asymmetric(str(data[field]))
            
        return result
        
    def decrypt_field(
        self,
        data: Dict[str, Any],
        field: str,
        encryption_type: EncryptionType = EncryptionType.SYMMETRIC,
    ) -> Dict[str, Any]:
        """Decrypt a field in a dictionary.
        
        Args:
            data: Dictionary containing the field to decrypt
            field: Field to decrypt
            encryption_type: Type of encryption used
            
        Returns:
            Dictionary with the decrypted field
            
        Raises:
            EncryptionError: If decryption fails
        """
        if field not in data:
            return data
            
        # Create a copy of the data
        result = data.copy()
        
        # Decrypt the field
        if encryption_type == EncryptionType.SYMMETRIC:
            result[field] = self.decrypt_symmetric(data[field]).decode()
        else:
            result[field] = self.decrypt_asymmetric(data[field]).decode()
            
        return result
