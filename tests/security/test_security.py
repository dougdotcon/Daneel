"""
Tests for the security and privacy components.
"""

import os
import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import MagicMock, AsyncMock
import tempfile
import base64
import json

from Daneel.core.loggers import ConsoleLogger
from Daneel.core.persistence.document_database import DocumentDatabase, DocumentCollection
from Daneel.core.persistence.memory_document_database import MemoryDocumentDatabase

from Daneel.security import (
    AuthManager,
    User,
    UserId,
    Token,
    TokenId,
    AuthRole,
    AuthPermission,
    AuthenticationError,
    AuthorizationError,
    EncryptionManager,
    EncryptionType,
    EncryptionError,
    PrivacyManager,
    PrivacyEntity,
    PrivacyEntityType,
    PrivacyDetectionResult,
    PrivacyError,
    AuditLogger,
    AuditEvent,
    AuditEventId,
    AuditEventType,
    AuditEventSeverity,
    ComplianceManager,
    ComplianceFramework,
    ComplianceRequirement,
    ComplianceRequirementId,
    ComplianceRequirementStatus,
    DataSubjectRequest,
)


@pytest.fixture
def logger():
    return ConsoleLogger()


@pytest.fixture
async def document_db():
    db = MemoryDocumentDatabase()
    yield db


@pytest.fixture
async def auth_manager(document_db, logger):
    manager = AuthManager(document_db, logger, jwt_secret="test_secret")
    await manager.__aenter__()
    yield manager
    await manager.__aexit__(None, None, None)


@pytest.fixture
def encryption_manager(logger):
    return EncryptionManager(logger)


@pytest.fixture
def privacy_manager(logger):
    return PrivacyManager(logger)


@pytest.fixture
async def audit_logger(document_db, logger):
    audit = AuditLogger(document_db, logger)
    await audit.__aenter__()
    yield audit
    await audit.__aexit__(None, None, None)


@pytest.fixture
async def compliance_manager(document_db, audit_logger, privacy_manager, logger):
    manager = ComplianceManager(document_db, audit_logger, privacy_manager, logger)
    await manager.__aenter__()
    yield manager
    await manager.__aexit__(None, None, None)


async def test_auth_manager_create_user(auth_manager):
    """Test that users can be created."""
    # Create a user
    user = await auth_manager.create_user(
        username="testuser",
        email="test@example.com",
        password="password123",
    )
    
    # Check that the user was created
    assert user is not None
    assert user.id is not None
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.roles == [AuthRole.USER]
    assert user.permissions == {}
    assert user.is_active is True
    
    # Try to create a user with the same username
    with pytest.raises(ValueError):
        await auth_manager.create_user(
            username="testuser",
            email="another@example.com",
            password="password123",
        )
        
    # Try to create a user with the same email
    with pytest.raises(ValueError):
        await auth_manager.create_user(
            username="anotheruser",
            email="test@example.com",
            password="password123",
        )
        
    # Try to create a user with an invalid username
    with pytest.raises(ValueError):
        await auth_manager.create_user(
            username="u",  # Too short
            email="invalid@example.com",
            password="password123",
        )
        
    # Try to create a user with an invalid email
    with pytest.raises(ValueError):
        await auth_manager.create_user(
            username="invaliduser",
            email="invalid",  # Invalid email
            password="password123",
        )
        
    # Try to create a user with a short password
    with pytest.raises(ValueError):
        await auth_manager.create_user(
            username="shortpassuser",
            email="short@example.com",
            password="short",  # Too short
        )


async def test_auth_manager_authenticate(auth_manager):
    """Test that users can be authenticated."""
    # Create a user
    user = await auth_manager.create_user(
        username="authuser",
        email="auth@example.com",
        password="password123",
    )
    
    # Authenticate with username
    token = await auth_manager.authenticate(
        username_or_email="authuser",
        password="password123",
    )
    
    # Check that the token was created
    assert token is not None
    assert token.id is not None
    assert token.user_id == user.id
    assert token.token is not None
    assert token.expiration_utc > datetime.now(timezone.utc)
    assert token.is_revoked is False
    
    # Authenticate with email
    token = await auth_manager.authenticate(
        username_or_email="auth@example.com",
        password="password123",
    )
    
    # Check that the token was created
    assert token is not None
    
    # Try to authenticate with wrong password
    with pytest.raises(AuthenticationError):
        await auth_manager.authenticate(
            username_or_email="authuser",
            password="wrongpassword",
        )
        
    # Try to authenticate with non-existent user
    with pytest.raises(AuthenticationError):
        await auth_manager.authenticate(
            username_or_email="nonexistent",
            password="password123",
        )


async def test_auth_manager_verify_token(auth_manager):
    """Test that tokens can be verified."""
    # Create a user
    user = await auth_manager.create_user(
        username="verifyuser",
        email="verify@example.com",
        password="password123",
    )
    
    # Authenticate
    token = await auth_manager.authenticate(
        username_or_email="verifyuser",
        password="password123",
    )
    
    # Verify the token
    verified_user = await auth_manager.verify_token(token.token)
    
    # Check that the user was returned
    assert verified_user is not None
    assert verified_user.id == user.id
    assert verified_user.username == user.username
    
    # Try to verify a non-existent token
    with pytest.raises(AuthenticationError):
        await auth_manager.verify_token("nonexistenttoken")
        
    # Revoke the token
    result = await auth_manager.revoke_token(token.token)
    assert result is True
    
    # Try to verify a revoked token
    with pytest.raises(AuthenticationError):
        await auth_manager.verify_token(token.token)


async def test_encryption_manager(encryption_manager):
    """Test that data can be encrypted and decrypted."""
    # Encrypt data with symmetric encryption
    data = "This is a test"
    encrypted = encryption_manager.encrypt_symmetric(data)
    
    # Check that the data was encrypted
    assert encrypted is not None
    assert encrypted != data
    
    # Decrypt the data
    decrypted = encryption_manager.decrypt_symmetric(encrypted)
    
    # Check that the data was decrypted correctly
    assert decrypted.decode() == data
    
    # Encrypt data with asymmetric encryption
    encrypted = encryption_manager.encrypt_asymmetric(data)
    
    # Check that the data was encrypted
    assert encrypted is not None
    assert encrypted != data
    
    # Decrypt the data
    decrypted = encryption_manager.decrypt_asymmetric(encrypted)
    
    # Check that the data was decrypted correctly
    assert decrypted.decode() == data
    
    # Encrypt JSON data
    json_data = {"key": "value", "number": 123}
    encrypted = encryption_manager.encrypt_json(json_data)
    
    # Check that the data was encrypted
    assert encrypted is not None
    
    # Decrypt the JSON data
    decrypted = encryption_manager.decrypt_json(encrypted)
    
    # Check that the data was decrypted correctly
    assert decrypted == json_data
    
    # Encrypt with password
    password = "mypassword"
    encrypted, salt = encryption_manager.encrypt_with_password(data, password)
    
    # Check that the data was encrypted
    assert encrypted is not None
    assert encrypted != data
    assert salt is not None
    
    # Decrypt with password
    decrypted = encryption_manager.decrypt_with_password(encrypted, password, salt)
    
    # Check that the data was decrypted correctly
    assert decrypted.decode() == data


async def test_privacy_manager(privacy_manager):
    """Test that privacy entities can be detected and anonymized."""
    # Create a test text with privacy entities
    text = """
    John Doe lives at 123 Main St, Springfield, IL 12345.
    His email is john.doe@example.com and his phone number is (555) 123-4567.
    His credit card number is 4111-1111-1111-1111 and his SSN is 123-45-6789.
    """
    
    # Detect privacy entities
    result = privacy_manager.detect_entities(text)
    
    # Check that entities were detected
    assert result is not None
    assert len(result.entities) > 0
    
    # Check that specific entity types were detected
    entity_types = [PrivacyEntityType(entity["type"]) for entity in result.entities]
    assert PrivacyEntityType.NAME in entity_types
    assert PrivacyEntityType.EMAIL in entity_types
    assert PrivacyEntityType.PHONE in entity_types
    assert PrivacyEntityType.CREDIT_CARD in entity_types
    assert PrivacyEntityType.SSN in entity_types
    
    # Anonymize the text
    anonymized = privacy_manager.anonymize_text(text)
    
    # Check that the text was anonymized
    assert anonymized is not None
    assert anonymized.anonymized_text is not None
    assert anonymized.anonymized_text != text
    assert "[REDACTED NAME]" in anonymized.anonymized_text
    assert "[REDACTED EMAIL]" in anonymized.anonymized_text
    assert "[REDACTED PHONE]" in anonymized.anonymized_text
    assert "[REDACTED CREDIT CARD]" in anonymized.anonymized_text
    assert "[REDACTED SSN]" in anonymized.anonymized_text
    
    # Test pseudonymization
    data = {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "age": 30,
    }
    
    pseudonymized = privacy_manager.pseudonymize_data(data, ["name", "email"])
    
    # Check that the data was pseudonymized
    assert pseudonymized is not None
    assert pseudonymized["name"] != data["name"]
    assert pseudonymized["email"] != data["email"]
    assert pseudonymized["age"] == data["age"]  # Not pseudonymized
    
    # Test synthetic data generation
    schema = {
        "name": {"type": "string", "min_length": 5, "max_length": 10},
        "age": {"type": "integer", "min": 18, "max": 65},
        "is_active": {"type": "boolean"},
    }
    
    synthetic = privacy_manager.generate_synthetic_data(schema, count=5)
    
    # Check that synthetic data was generated
    assert synthetic is not None
    assert len(synthetic) == 5
    for record in synthetic:
        assert "name" in record
        assert "age" in record
        assert "is_active" in record
        assert isinstance(record["name"], str)
        assert 5 <= len(record["name"]) <= 10
        assert isinstance(record["age"], int)
        assert 18 <= record["age"] <= 65
        assert isinstance(record["is_active"], bool)


async def test_audit_logger(audit_logger):
    """Test that audit events can be logged and retrieved."""
    # Log an event
    event = await audit_logger.log_event(
        type=AuditEventType.USER_LOGIN,
        user_id="user123",
        resource="auth",
        action="login",
        status="success",
        severity=AuditEventSeverity.INFO,
        details={"ip_address": "127.0.0.1"},
    )
    
    # Check that the event was logged
    assert event is not None
    assert event.id is not None
    assert event.type == AuditEventType.USER_LOGIN
    assert event.user_id == "user123"
    assert event.resource == "auth"
    assert event.action == "login"
    assert event.status == "success"
    assert event.severity == AuditEventSeverity.INFO
    assert event.details == {"ip_address": "127.0.0.1"}
    
    # Get the event
    retrieved = await audit_logger.get_event(event.id)
    
    # Check that the event was retrieved
    assert retrieved is not None
    assert retrieved.id == event.id
    assert retrieved.type == event.type
    assert retrieved.user_id == event.user_id
    assert retrieved.resource == event.resource
    assert retrieved.action == event.action
    assert retrieved.status == event.status
    assert retrieved.severity == event.severity
    assert retrieved.details == event.details
    
    # Search for events
    events = await audit_logger.search_events(
        type=AuditEventType.USER_LOGIN,
        user_id="user123",
        resource="auth",
        action="login",
        status="success",
    )
    
    # Check that the event was found
    assert events is not None
    assert len(events) == 1
    assert events[0].id == event.id
    
    # Test the audit context manager
    async with audit_logger.audit_context(
        type=AuditEventType.DATA_ACCESS,
        user_id="user123",
        resource="data",
        action="read",
        severity=AuditEventSeverity.INFO,
        details={"data_id": "data123"},
    ):
        # Do something that should be audited
        pass
        
    # Check that the success event was logged
    events = await audit_logger.search_events(
        type=AuditEventType.DATA_ACCESS,
        user_id="user123",
        resource="data",
        action="read",
        status="success",
    )
    
    assert events is not None
    assert len(events) == 1
    
    # Test the audit context manager with an exception
    try:
        async with audit_logger.audit_context(
            type=AuditEventType.DATA_MODIFICATION,
            user_id="user123",
            resource="data",
            action="write",
            severity=AuditEventSeverity.INFO,
            details={"data_id": "data123"},
        ):
            # Do something that raises an exception
            raise ValueError("Test error")
    except ValueError:
        pass
        
    # Check that the failure event was logged
    events = await audit_logger.search_events(
        type=AuditEventType.DATA_MODIFICATION,
        user_id="user123",
        resource="data",
        action="write",
        status="failure",
    )
    
    assert events is not None
    assert len(events) == 1
    assert "error" in events[0].details
    assert events[0].details["error"] == "Test error"


async def test_compliance_manager(compliance_manager):
    """Test that compliance requirements can be managed."""
    # Add a requirement
    requirement = await compliance_manager.add_requirement(
        framework=ComplianceFramework.GDPR,
        code="TEST-1",
        name="Test Requirement",
        description="This is a test requirement",
        status=ComplianceRequirementStatus.PENDING,
        responsible_party="Test Team",
    )
    
    # Check that the requirement was added
    assert requirement is not None
    assert requirement.id is not None
    assert requirement.framework == ComplianceFramework.GDPR
    assert requirement.code == "TEST-1"
    assert requirement.name == "Test Requirement"
    assert requirement.description == "This is a test requirement"
    assert requirement.status == ComplianceRequirementStatus.PENDING
    assert requirement.responsible_party == "Test Team"
    
    # Update the requirement
    updated = await compliance_manager.update_requirement(
        requirement_id=requirement.id,
        status=ComplianceRequirementStatus.COMPLIANT,
        evidence="Test evidence",
    )
    
    # Check that the requirement was updated
    assert updated is not None
    assert updated.id == requirement.id
    assert updated.status == ComplianceRequirementStatus.COMPLIANT
    assert updated.evidence == "Test evidence"
    
    # Get the requirement
    retrieved = await compliance_manager.get_requirement(requirement.id)
    
    # Check that the requirement was retrieved
    assert retrieved is not None
    assert retrieved.id == requirement.id
    assert retrieved.status == ComplianceRequirementStatus.COMPLIANT
    
    # List requirements
    requirements = await compliance_manager.list_requirements(
        framework=ComplianceFramework.GDPR,
    )
    
    # Check that the requirement is in the list
    assert requirements is not None
    assert len(requirements) > 0
    assert any(r.id == requirement.id for r in requirements)
    
    # Create a data subject request
    request = await compliance_manager.create_data_subject_request(
        user_id="user123",
        request_type="access",
        notes="Test request",
    )
    
    # Check that the request was created
    assert request is not None
    assert request.id is not None
    assert request.user_id == "user123"
    assert request.request_type == "access"
    assert request.status == "pending"
    assert request.notes == "Test request"
    
    # Update the request
    updated = await compliance_manager.update_data_subject_request(
        request_id=request.id,
        status="completed",
        completion_utc=datetime.now(timezone.utc),
    )
    
    # Check that the request was updated
    assert updated is not None
    assert updated.id == request.id
    assert updated.status == "completed"
    assert updated.completion_utc is not None
    
    # Generate a compliance report
    report = await compliance_manager.generate_compliance_report(
        framework=ComplianceFramework.GDPR,
    )
    
    # Check that the report was generated
    assert report is not None
    assert "timestamp" in report
    assert "summary" in report
    assert "requirements" in report
    assert report["framework"] == ComplianceFramework.GDPR.value
    assert report["summary"]["total"] > 0
