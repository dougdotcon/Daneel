"""
Authentication and authorization for Daneel.

This module provides functionality for user authentication and authorization.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Callable
import uuid
import json
import hashlib
import secrets
import re
import jwt
from jwt.exceptions import InvalidTokenError

from Daneel.core.common import JSONSerializable, generate_id
from Daneel.core.loggers import Logger
from Daneel.core.async_utils import ReaderWriterLock
from Daneel.core.persistence.document_database import DocumentCollection, DocumentDatabase
from Daneel.core.persistence.common import ItemNotFoundError, ObjectId, UniqueId, Where


class AuthRole(str, Enum):
    """Authentication roles."""

    ADMIN = "admin"
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"
    GUEST = "guest"


class AuthPermission(str, Enum):
    """Authentication permissions."""

    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    DELETE = "delete"
    ADMIN = "admin"


class UserId(str):
    """User ID."""
    pass


class TokenId(str):
    """Token ID."""
    pass


@dataclass
class User:
    """User for authentication."""

    id: UserId
    username: str
    email: str
    password_hash: str
    salt: str
    roles: List[AuthRole]
    permissions: Dict[str, List[AuthPermission]]
    creation_utc: datetime
    last_login_utc: Optional[datetime] = None
    is_active: bool = True
    metadata: Dict[str, JSONSerializable] = field(default_factory=dict)


@dataclass
class Token:
    """Authentication token."""

    id: TokenId
    user_id: UserId
    token: str
    expiration_utc: datetime
    creation_utc: datetime
    is_revoked: bool = False
    metadata: Dict[str, JSONSerializable] = field(default_factory=dict)


class _UserDocument(Dict[str, Any]):
    """User document for storage."""
    pass


class _TokenDocument(Dict[str, Any]):
    """Token document for storage."""
    pass


class AuthenticationError(Exception):
    """Authentication error."""
    pass


class AuthorizationError(Exception):
    """Authorization error."""
    pass


class AuthManager:
    """Manager for authentication and authorization."""

    VERSION = "0.1.0"

    def __init__(
        self,
        document_db: DocumentDatabase,
        logger: Logger,
        jwt_secret: str,
        token_expiration_minutes: int = 60,
    ):
        """Initialize the authentication manager.

        Args:
            document_db: Document database
            logger: Logger instance
            jwt_secret: Secret for JWT tokens
            token_expiration_minutes: Token expiration time in minutes
        """
        self._document_db = document_db
        self._logger = logger
        self._jwt_secret = jwt_secret
        self._token_expiration_minutes = token_expiration_minutes

        self._user_collection: Optional[DocumentCollection[_UserDocument]] = None
        self._token_collection: Optional[DocumentCollection[_TokenDocument]] = None
        self._lock = ReaderWriterLock()

    async def __aenter__(self) -> AuthManager:
        """Enter the context manager."""
        self._user_collection = await self._document_db.get_or_create_collection(
            name="auth_users",
            schema=_UserDocument,
        )

        self._token_collection = await self._document_db.get_or_create_collection(
            name="auth_tokens",
            schema=_TokenDocument,
        )

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager."""
        pass

    def _serialize_user(self, user: User) -> _UserDocument:
        """Serialize a user.

        Args:
            user: User to serialize

        Returns:
            Serialized user document
        """
        return {
            "id": user.id,
            "version": self.VERSION,
            "username": user.username,
            "email": user.email,
            "password_hash": user.password_hash,
            "salt": user.salt,
            "roles": [role.value for role in user.roles],
            "permissions": {
                resource: [perm.value for perm in perms]
                for resource, perms in user.permissions.items()
            },
            "creation_utc": user.creation_utc.isoformat(),
            "last_login_utc": user.last_login_utc.isoformat() if user.last_login_utc else None,
            "is_active": user.is_active,
            "metadata": user.metadata,
        }

    def _deserialize_user(self, document: _UserDocument) -> User:
        """Deserialize a user document.

        Args:
            document: User document

        Returns:
            Deserialized user
        """
        return User(
            id=UserId(document["id"]),
            username=document["username"],
            email=document["email"],
            password_hash=document["password_hash"],
            salt=document["salt"],
            roles=[AuthRole(role) for role in document["roles"]],
            permissions={
                resource: [AuthPermission(perm) for perm in perms]
                for resource, perms in document["permissions"].items()
            },
            creation_utc=datetime.fromisoformat(document["creation_utc"]),
            last_login_utc=datetime.fromisoformat(document["last_login_utc"]) if document.get("last_login_utc") else None,
            is_active=document.get("is_active", True),
            metadata=document.get("metadata", {}),
        )

    def _serialize_token(self, token: Token) -> _TokenDocument:
        """Serialize a token.

        Args:
            token: Token to serialize

        Returns:
            Serialized token document
        """
        return {
            "id": token.id,
            "version": self.VERSION,
            "user_id": token.user_id,
            "token": token.token,
            "expiration_utc": token.expiration_utc.isoformat(),
            "creation_utc": token.creation_utc.isoformat(),
            "is_revoked": token.is_revoked,
            "metadata": token.metadata,
        }

    def _deserialize_token(self, document: _TokenDocument) -> Token:
        """Deserialize a token document.

        Args:
            document: Token document

        Returns:
            Deserialized token
        """
        return Token(
            id=TokenId(document["id"]),
            user_id=UserId(document["user_id"]),
            token=document["token"],
            expiration_utc=datetime.fromisoformat(document["expiration_utc"]),
            creation_utc=datetime.fromisoformat(document["creation_utc"]),
            is_revoked=document.get("is_revoked", False),
            metadata=document.get("metadata", {}),
        )

    def _hash_password(self, password: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """Hash a password.

        Args:
            password: Password to hash
            salt: Salt for hashing (if None, a new salt is generated)

        Returns:
            Tuple of (password_hash, salt)
        """
        if salt is None:
            salt = secrets.token_hex(16)

        # Hash the password with the salt
        password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            100000,
        ).hex()

        return password_hash, salt

    def _verify_password(self, password: str, password_hash: str, salt: str) -> bool:
        """Verify a password.

        Args:
            password: Password to verify
            password_hash: Hash to verify against
            salt: Salt used for hashing

        Returns:
            True if the password is correct, False otherwise
        """
        # Hash the password with the salt
        hashed, _ = self._hash_password(password, salt)

        # Compare the hashes
        return hashed == password_hash

    def _generate_jwt_token(self, user_id: UserId, roles: List[AuthRole]) -> str:
        """Generate a JWT token.

        Args:
            user_id: User ID
            roles: User roles

        Returns:
            JWT token
        """
        # Set the expiration time
        expiration = datetime.now(timezone.utc) + timedelta(minutes=self._token_expiration_minutes)

        # Create the payload
        payload = {
            "sub": user_id,
            "roles": [role.value for role in roles],
            "exp": int(expiration.timestamp()),
            "iat": int(datetime.now(timezone.utc).timestamp()),
        }

        # Generate the token
        token = jwt.encode(payload, self._jwt_secret, algorithm="HS256")

        return token

    def _verify_jwt_token(self, token: str) -> Dict[str, Any]:
        """Verify a JWT token.

        Args:
            token: JWT token

        Returns:
            Token payload

        Raises:
            AuthenticationError: If the token is invalid
        """
        try:
            # Decode the token
            payload = jwt.decode(token, self._jwt_secret, algorithms=["HS256"])

            return payload
        except InvalidTokenError as e:
            raise AuthenticationError(f"Invalid token: {e}")

    async def create_user(
        self,
        username: str,
        email: str,
        password: str,
        roles: List[AuthRole] = None,
        permissions: Dict[str, List[AuthPermission]] = None,
    ) -> User:
        """Create a user.

        Args:
            username: Username
            email: Email address
            password: Password
            roles: User roles
            permissions: User permissions

        Returns:
            Created user

        Raises:
            ValueError: If the username or email is invalid
        """
        # Validate username
        if not re.match(r"^[a-zA-Z0-9_]{3,20}$", username):
            raise ValueError("Invalid username. Must be 3-20 characters, alphanumeric or underscore.")

        # Validate email
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
            raise ValueError("Invalid email address.")

        # Validate password
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters.")

        async with self._lock.writer_lock:
            # Check if the username or email already exists
            existing_user = await self._user_collection.find_one(
                filters={"$or": [
                    {"username": {"$eq": username}},
                    {"email": {"$eq": email}},
                ]}
            )

            if existing_user:
                if existing_user["username"] == username:
                    raise ValueError(f"Username already exists: {username}")
                else:
                    raise ValueError(f"Email already exists: {email}")

            # Hash the password
            password_hash, salt = self._hash_password(password)

            # Set default roles and permissions
            if roles is None:
                roles = [AuthRole.USER]

            if permissions is None:
                permissions = {}

            # Create the user
            user = User(
                id=UserId(generate_id()),
                username=username,
                email=email,
                password_hash=password_hash,
                salt=salt,
                roles=roles,
                permissions=permissions,
                creation_utc=datetime.now(timezone.utc),
            )

            # Save the user
            await self._user_collection.insert_one(
                document=self._serialize_user(user)
            )

            self._logger.info(f"Created user: {username} ({user.id})")

            return user

    async def authenticate(
        self,
        username_or_email: str,
        password: str,
    ) -> Token:
        """Authenticate a user.

        Args:
            username_or_email: Username or email
            password: Password

        Returns:
            Authentication token

        Raises:
            AuthenticationError: If authentication fails
        """
        async with self._lock.reader_lock:
            # Find the user
            user_doc = await self._user_collection.find_one(
                filters={"$or": [
                    {"username": {"$eq": username_or_email}},
                    {"email": {"$eq": username_or_email}},
                ]}
            )

            if not user_doc:
                raise AuthenticationError("Invalid username or password.")

            user = self._deserialize_user(user_doc)

            # Check if the user is active
            if not user.is_active:
                raise AuthenticationError("User account is inactive.")

            # Verify the password
            if not self._verify_password(password, user.password_hash, user.salt):
                raise AuthenticationError("Invalid username or password.")

            # Generate a JWT token
            jwt_token = self._generate_jwt_token(user.id, user.roles)

            # Create a token
            token = Token(
                id=TokenId(generate_id()),
                user_id=user.id,
                token=jwt_token,
                expiration_utc=datetime.now(timezone.utc) + timedelta(minutes=self._token_expiration_minutes),
                creation_utc=datetime.now(timezone.utc),
            )

            # Save the token
            await self._token_collection.insert_one(
                document=self._serialize_token(token)
            )

            # Update the user's last login time
            await self._user_collection.update_one(
                filters={"id": {"$eq": user.id}},
                params={"last_login_utc": datetime.now(timezone.utc).isoformat()},
            )

            self._logger.info(f"User authenticated: {user.username} ({user.id})")

            return token

    async def verify_token(
        self,
        token_str: str,
    ) -> User:
        """Verify a token and get the associated user.

        Args:
            token_str: Token string

        Returns:
            User associated with the token

        Raises:
            AuthenticationError: If the token is invalid
        """
        async with self._lock.reader_lock:
            try:
                # Verify the JWT token
                payload = self._verify_jwt_token(token_str)

                # Get the user ID
                user_id = UserId(payload["sub"])

                # Check if the token is in the database and not revoked
                token_doc = await self._token_collection.find_one(
                    filters={
                        "token": {"$eq": token_str},
                        "is_revoked": {"$eq": False},
                    }
                )

                if not token_doc:
                    raise AuthenticationError("Token not found or revoked.")

                token = self._deserialize_token(token_doc)

                # Check if the token has expired
                if token.expiration_utc < datetime.now(timezone.utc):
                    raise AuthenticationError("Token has expired.")

                # Get the user
                user_doc = await self._user_collection.find_one(
                    filters={"id": {"$eq": user_id}}
                )

                if not user_doc:
                    raise AuthenticationError("User not found.")

                user = self._deserialize_user(user_doc)

                # Check if the user is active
                if not user.is_active:
                    raise AuthenticationError("User account is inactive.")

                return user

            except Exception as e:
                raise AuthenticationError(f"Token verification failed: {e}")

    async def revoke_token(
        self,
        token_str: str,
    ) -> bool:
        """Revoke a token.

        Args:
            token_str: Token string

        Returns:
            True if the token was revoked, False otherwise
        """
        async with self._lock.writer_lock:
            # Find the token
            token_doc = await self._token_collection.find_one(
                filters={"token": {"$eq": token_str}}
            )

            if not token_doc:
                return False

            # Revoke the token
            await self._token_collection.update_one(
                filters={"token": {"$eq": token_str}},
                params={"is_revoked": True},
            )

            self._logger.info(f"Token revoked: {token_doc['id']}")

            return True

    async def revoke_all_user_tokens(
        self,
        user_id: UserId,
    ) -> int:
        """Revoke all tokens for a user.

        Args:
            user_id: User ID

        Returns:
            Number of tokens revoked
        """
        async with self._lock.writer_lock:
            # Find all tokens for the user
            token_docs = await self._token_collection.find(
                filters={
                    "user_id": {"$eq": user_id},
                    "is_revoked": {"$eq": False},
                }
            )

            if not token_docs:
                return 0

            # Revoke all tokens
            for token_doc in token_docs:
                await self._token_collection.update_one(
                    filters={"id": {"$eq": token_doc["id"]}},
                    params={"is_revoked": True},
                )

            self._logger.info(f"Revoked all tokens for user: {user_id}")

            return len(token_docs)

    async def change_password(
        self,
        user_id: UserId,
        current_password: str,
        new_password: str,
    ) -> bool:
        """Change a user's password.

        Args:
            user_id: User ID
            current_password: Current password
            new_password: New password

        Returns:
            True if the password was changed, False otherwise

        Raises:
            AuthenticationError: If the current password is incorrect
            ValueError: If the new password is invalid
        """
        # Validate new password
        if len(new_password) < 8:
            raise ValueError("New password must be at least 8 characters.")

        async with self._lock.writer_lock:
            # Get the user
            user_doc = await self._user_collection.find_one(
                filters={"id": {"$eq": user_id}}
            )

            if not user_doc:
                return False

            user = self._deserialize_user(user_doc)

            # Verify the current password
            if not self._verify_password(current_password, user.password_hash, user.salt):
                raise AuthenticationError("Current password is incorrect.")

            # Hash the new password
            password_hash, salt = self._hash_password(new_password)

            # Update the user
            await self._user_collection.update_one(
                filters={"id": {"$eq": user_id}},
                params={
                    "password_hash": password_hash,
                    "salt": salt,
                },
            )

            # Revoke all tokens for the user
            await self.revoke_all_user_tokens(user_id)

            self._logger.info(f"Password changed for user: {user.username} ({user.id})")

            return True

    async def update_user(
        self,
        user_id: UserId,
        username: Optional[str] = None,
        email: Optional[str] = None,
        roles: Optional[List[AuthRole]] = None,
        permissions: Optional[Dict[str, List[AuthPermission]]] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[User]:
        """Update a user.

        Args:
            user_id: User ID
            username: New username
            email: New email
            roles: New roles
            permissions: New permissions
            is_active: New active status

        Returns:
            Updated user, or None if the user was not found

        Raises:
            ValueError: If the username or email is invalid
        """
        # Validate username
        if username is not None and not re.match(r"^[a-zA-Z0-9_]{3,20}$", username):
            raise ValueError("Invalid username. Must be 3-20 characters, alphanumeric or underscore.")

        # Validate email
        if email is not None and not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
            raise ValueError("Invalid email address.")

        async with self._lock.writer_lock:
            # Get the user
            user_doc = await self._user_collection.find_one(
                filters={"id": {"$eq": user_id}}
            )

            if not user_doc:
                return None

            # Check if the username or email already exists
            if username is not None or email is not None:
                filters = {"$or": []}

                if username is not None:
                    filters["$or"].append({"username": {"$eq": username}})

                if email is not None:
                    filters["$or"].append({"email": {"$eq": email}})

                if filters["$or"]:
                    existing_user = await self._user_collection.find_one(
                        filters=filters
                    )

                    if existing_user and existing_user["id"] != user_id:
                        if username is not None and existing_user["username"] == username:
                            raise ValueError(f"Username already exists: {username}")
                        else:
                            raise ValueError(f"Email already exists: {email}")

            # Update the user
            params = {}

            if username is not None:
                params["username"] = username

            if email is not None:
                params["email"] = email

            if roles is not None:
                params["roles"] = [role.value for role in roles]

            if permissions is not None:
                params["permissions"] = {
                    resource: [perm.value for perm in perms]
                    for resource, perms in permissions.items()
                }

            if is_active is not None:
                params["is_active"] = is_active

            if params:
                await self._user_collection.update_one(
                    filters={"id": {"$eq": user_id}},
                    params=params,
                )

                self._logger.info(f"Updated user: {user_id}")

            # Get the updated user
            user_doc = await self._user_collection.find_one(
                filters={"id": {"$eq": user_id}}
            )

            return self._deserialize_user(user_doc)

    async def delete_user(
        self,
        user_id: UserId,
    ) -> bool:
        """Delete a user.

        Args:
            user_id: User ID

        Returns:
            True if the user was deleted, False otherwise
        """
        async with self._lock.writer_lock:
            # Delete the user
            result = await self._user_collection.delete_one(
                filters={"id": {"$eq": user_id}}
            )

            if result.deleted_count == 0:
                return False

            # Revoke all tokens for the user
            await self.revoke_all_user_tokens(user_id)

            self._logger.info(f"Deleted user: {user_id}")

            return True

    async def get_user(
        self,
        user_id: UserId,
    ) -> Optional[User]:
        """Get a user by ID.

        Args:
            user_id: User ID

        Returns:
            User if found, None otherwise
        """
        async with self._lock.reader_lock:
            # Get the user
            user_doc = await self._user_collection.find_one(
                filters={"id": {"$eq": user_id}}
            )

            if not user_doc:
                return None

            return self._deserialize_user(user_doc)

    async def get_user_by_username(
        self,
        username: str,
    ) -> Optional[User]:
        """Get a user by username.

        Args:
            username: Username

        Returns:
            User if found, None otherwise
        """
        async with self._lock.reader_lock:
            # Get the user
            user_doc = await self._user_collection.find_one(
                filters={"username": {"$eq": username}}
            )

            if not user_doc:
                return None

            return self._deserialize_user(user_doc)

    async def get_user_by_email(
        self,
        email: str,
    ) -> Optional[User]:
        """Get a user by email.

        Args:
            email: Email

        Returns:
            User if found, None otherwise
        """
        async with self._lock.reader_lock:
            # Get the user
            user_doc = await self._user_collection.find_one(
                filters={"email": {"$eq": email}}
            )

            if not user_doc:
                return None

            return self._deserialize_user(user_doc)

    async def list_users(
        self,
        role: Optional[AuthRole] = None,
        is_active: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[User]:
        """List users.

        Args:
            role: Filter by role
            is_active: Filter by active status
            limit: Maximum number of users to return
            offset: Offset for pagination

        Returns:
            List of users
        """
        async with self._lock.reader_lock:
            # Build filters
            filters = {}

            if role is not None:
                filters["roles"] = {"$in": [role.value]}

            if is_active is not None:
                filters["is_active"] = {"$eq": is_active}

            # Get users
            user_docs = await self._user_collection.find(
                filters=filters,
                sort=[("username", 1)],
                limit=limit,
                skip=offset,
            )

            return [self._deserialize_user(doc) for doc in user_docs]

    def has_permission(
        self,
        user: User,
        resource: str,
        permission: AuthPermission,
    ) -> bool:
        """Check if a user has a permission.

        Args:
            user: User
            resource: Resource
            permission: Permission

        Returns:
            True if the user has the permission, False otherwise
        """
        # Check if the user is an admin
        if AuthRole.ADMIN in user.roles:
            return True

        # Check if the user has the permission for the resource
        if resource in user.permissions:
            # Check for admin permission
            if AuthPermission.ADMIN in user.permissions[resource]:
                return True

            # Check for the specific permission
            if permission in user.permissions[resource]:
                return True

        return False

    def require_permission(
        self,
        user: User,
        resource: str,
        permission: AuthPermission,
    ) -> None:
        """Require a permission.

        Args:
            user: User
            resource: Resource
            permission: Permission

        Raises:
            AuthorizationError: If the user does not have the permission
        """
        if not self.has_permission(user, resource, permission):
            raise AuthorizationError(f"User {user.username} does not have permission {permission.value} for resource {resource}")

    def create_permission_decorator(
        self,
        resource: str,
        permission: AuthPermission,
    ) -> Callable:
        """Create a permission decorator.

        Args:
            resource: Resource
            permission: Permission

        Returns:
            Permission decorator
        """
        def decorator(func):
            async def wrapper(self, user: User, *args, **kwargs):
                # Check if the user has the permission
                if not self.has_permission(user, resource, permission):
                    raise AuthorizationError(f"User {user.username} does not have permission {permission.value} for resource {resource}")

                # Call the function
                return await func(self, user, *args, **kwargs)

            return wrapper

        return decorator
