# Security and Privacy

This document describes the security and privacy features in the Parlant framework.

## Overview

The security and privacy module provides a comprehensive set of tools for implementing security measures and privacy controls in Parlant applications. It includes:

1. Authentication and authorization for secure access control
2. Data encryption for protecting sensitive information
3. Privacy-preserving data processing techniques
4. Audit logging and monitoring for security events
5. Compliance frameworks for meeting regulatory requirements

## Components

### Authentication and Authorization

The authentication and authorization component provides functionality for user management and access control:

- User creation and management
- Password hashing and verification
- JWT token-based authentication
- Role-based access control
- Permission-based authorization

Example usage:

```python
from parlant.security import AuthManager, AuthRole, AuthPermission

# Create an authentication manager
auth_manager = AuthManager(document_db, logger, jwt_secret="your_secret_key")

# Create a user
user = await auth_manager.create_user(
    username="johndoe",
    email="john.doe@example.com",
    password="secure_password",
    roles=[AuthRole.USER],
    permissions={
        "documents": [AuthPermission.READ, AuthPermission.WRITE],
        "settings": [AuthPermission.READ],
    },
)

# Authenticate a user
token = await auth_manager.authenticate(
    username_or_email="johndoe",
    password="secure_password",
)

# Verify a token
user = await auth_manager.verify_token(token.token)

# Check permissions
has_permission = auth_manager.has_permission(
    user=user,
    resource="documents",
    permission=AuthPermission.WRITE,
)

# Require a permission (raises AuthorizationError if not allowed)
auth_manager.require_permission(
    user=user,
    resource="documents",
    permission=AuthPermission.WRITE,
)
```

### Data Encryption

The data encryption component provides functionality for protecting sensitive information:

- Symmetric encryption for fast, secure data protection
- Asymmetric encryption for secure key exchange
- Password-based encryption
- JSON data encryption
- Field-level encryption

Example usage:

```python
from parlant.security import EncryptionManager, EncryptionType

# Create an encryption manager
encryption_manager = EncryptionManager(logger)

# Encrypt data with symmetric encryption
encrypted = encryption_manager.encrypt_symmetric("sensitive data")

# Decrypt data
decrypted = encryption_manager.decrypt_symmetric(encrypted)

# Encrypt JSON data
json_data = {"username": "johndoe", "ssn": "123-45-6789"}
encrypted_json = encryption_manager.encrypt_json(json_data)

# Decrypt JSON data
decrypted_json = encryption_manager.decrypt_json(encrypted_json)

# Encrypt specific fields in a dictionary
data = {"name": "John Doe", "ssn": "123-45-6789", "age": 30}
protected_data = encryption_manager.encrypt_field(
    data=data,
    field="ssn",
    encryption_type=EncryptionType.SYMMETRIC,
)
```

### Privacy-Preserving Data Processing

The privacy component provides functionality for protecting personal data:

- Detection of privacy entities (PII) in text
- Anonymization of sensitive information
- Pseudonymization of identifiers
- Synthetic data generation
- K-anonymity implementation

Example usage:

```python
from parlant.security import PrivacyManager, PrivacyEntityType

# Create a privacy manager
privacy_manager = PrivacyManager(logger)

# Detect privacy entities in text
text = "John Doe's email is john.doe@example.com and his phone is (555) 123-4567."
detection_result = privacy_manager.detect_entities(text)

# Anonymize text
anonymized_result = privacy_manager.anonymize_text(text)
print(anonymized_result.anonymized_text)
# Output: "[REDACTED NAME]'s email is [REDACTED EMAIL] and his phone is [REDACTED PHONE]."

# Pseudonymize data
data = {"name": "John Doe", "email": "john.doe@example.com", "age": 30}
pseudonymized = privacy_manager.pseudonymize_data(
    data=data,
    fields=["name", "email"],
)

# Generate synthetic data
schema = {
    "name": {"type": "string", "min_length": 5, "max_length": 10},
    "age": {"type": "integer", "min": 18, "max": 65},
    "is_active": {"type": "boolean"},
}
synthetic_data = privacy_manager.generate_synthetic_data(schema, count=10)
```

### Audit Logging

The audit logging component provides functionality for tracking security events:

- Comprehensive event logging
- Severity levels for events
- User and resource tracking
- Searchable audit trail
- Context manager for operation auditing

Example usage:

```python
from parlant.security import AuditLogger, AuditEventType, AuditEventSeverity

# Create an audit logger
audit_logger = AuditLogger(document_db, logger)

# Log an event
await audit_logger.log_event(
    type=AuditEventType.USER_LOGIN,
    user_id="user123",
    resource="auth",
    action="login",
    status="success",
    severity=AuditEventSeverity.INFO,
    details={"ip_address": "192.168.1.1"},
)

# Search for events
events = await audit_logger.search_events(
    type=AuditEventType.USER_LOGIN,
    user_id="user123",
    start_time=datetime(2023, 1, 1),
    end_time=datetime(2023, 12, 31),
)

# Use the audit context manager
async with audit_logger.audit_context(
    type=AuditEventType.DATA_MODIFICATION,
    user_id="user123",
    resource="customer",
    action="update",
    severity=AuditEventSeverity.INFO,
    details={"customer_id": "cust123"},
):
    # Perform the operation
    # If an exception occurs, a failure event is logged
    # Otherwise, a success event is logged
    await update_customer(customer_id="cust123", data={"name": "New Name"})
```

### Compliance Frameworks

The compliance component provides functionality for meeting regulatory requirements:

- Support for GDPR, HIPAA, CCPA, SOC2, and PCI DSS
- Compliance requirement tracking
- Data subject request handling
- Compliance reporting
- Evidence management

Example usage:

```python
from parlant.security import (
    ComplianceManager,
    ComplianceFramework,
    ComplianceRequirementStatus,
)

# Create a compliance manager
compliance_manager = ComplianceManager(document_db, audit_logger, privacy_manager, logger)

# Add a compliance requirement
requirement = await compliance_manager.add_requirement(
    framework=ComplianceFramework.GDPR,
    code="GDPR-7.1",
    name="Data Subject Access Request",
    description="Implement mechanisms to handle data subject access requests.",
    status=ComplianceRequirementStatus.PARTIALLY_COMPLIANT,
    responsible_party="Privacy Team",
)

# Update a requirement
updated = await compliance_manager.update_requirement(
    requirement_id=requirement.id,
    status=ComplianceRequirementStatus.COMPLIANT,
    evidence="Implemented DSAR handling in v2.3",
)

# Create a data subject request
request = await compliance_manager.create_data_subject_request(
    user_id="user123",
    request_type="access",
    notes="User requested all data we have about them",
)

# Generate a compliance report
report = await compliance_manager.generate_compliance_report(
    framework=ComplianceFramework.GDPR,
)
```

## Integration with Parlant

The security and privacy features are integrated with the Parlant framework:

1. **API Integration**: Authentication and authorization for API endpoints
2. **Data Protection**: Encryption for sensitive data in storage and transit
3. **Privacy Controls**: Privacy-preserving techniques for user data
4. **Audit Trail**: Comprehensive logging of security events
5. **Compliance**: Tools for meeting regulatory requirements

## Implementation Details

### Dependencies

The security and privacy module depends on several external libraries:

- **PyJWT**: For JWT token generation and verification
- **Cryptography**: For encryption and hashing
- **Hashlib**: For secure hashing algorithms
- **Regex**: For pattern matching in privacy detection

### Performance Considerations

When implementing security and privacy features, consider the following:

- **Authentication Caching**: Cache authentication results to improve performance
- **Encryption Overhead**: Encryption adds processing overhead, use selectively
- **Audit Log Size**: Implement retention policies for audit logs
- **Privacy Scanning**: Privacy entity detection can be resource-intensive for large texts

### Security Best Practices

Follow these best practices when using the security and privacy module:

1. **Secure Secrets**: Store JWT secrets and encryption keys securely
2. **Password Policies**: Enforce strong password policies
3. **Token Expiration**: Use short-lived tokens and implement refresh mechanisms
4. **Least Privilege**: Grant minimal permissions required for operations
5. **Regular Audits**: Review audit logs regularly for suspicious activity
6. **Data Minimization**: Collect and store only necessary personal data
7. **Encryption Layers**: Use multiple layers of encryption for highly sensitive data

## Future Enhancements

Potential future enhancements for the security and privacy module:

1. **Multi-factor Authentication**: Add support for MFA
2. **OAuth Integration**: Support for OAuth 2.0 and OpenID Connect
3. **Hardware Security**: Integration with hardware security modules
4. **Advanced Privacy**: Differential privacy and homomorphic encryption
5. **Threat Detection**: Real-time security threat detection
6. **Automated Compliance**: Automated compliance checks and reporting
