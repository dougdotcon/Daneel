"""
Privacy-preserving data processing for Parlant.

This module provides functionality for privacy-preserving data processing.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Callable, Pattern
import re
import json
import hashlib
import uuid
import random

from parlant.core.common import JSONSerializable
from parlant.core.loggers import Logger


class PrivacyEntityType(str, Enum):
    """Types of privacy entities."""
    
    NAME = "name"
    EMAIL = "email"
    PHONE = "phone"
    ADDRESS = "address"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    IP_ADDRESS = "ip_address"
    DATE_OF_BIRTH = "date_of_birth"
    CUSTOM = "custom"


@dataclass
class PrivacyEntity:
    """Privacy entity for detection and anonymization."""
    
    type: PrivacyEntityType
    pattern: Pattern
    description: str
    anonymization_func: Callable[[str], str]


class PrivacyError(Exception):
    """Privacy error."""
    pass


@dataclass
class PrivacyDetectionResult:
    """Result of privacy entity detection."""
    
    text: str
    entities: List[Dict[str, Any]]
    anonymized_text: Optional[str] = None


class PrivacyManager:
    """Manager for privacy-preserving data processing."""
    
    def __init__(
        self,
        logger: Logger,
    ):
        """Initialize the privacy manager.
        
        Args:
            logger: Logger instance
        """
        self._logger = logger
        self._entities: Dict[PrivacyEntityType, PrivacyEntity] = {}
        
        # Register default privacy entities
        self._register_default_entities()
        
    def _register_default_entities(self):
        """Register default privacy entities."""
        # Name pattern (simplified)
        self.register_entity(
            type=PrivacyEntityType.NAME,
            pattern=re.compile(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b"),
            description="Full name (first and last)",
            anonymization_func=lambda x: "[REDACTED NAME]",
        )
        
        # Email pattern
        self.register_entity(
            type=PrivacyEntityType.EMAIL,
            pattern=re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b"),
            description="Email address",
            anonymization_func=lambda x: "[REDACTED EMAIL]",
        )
        
        # Phone pattern (US format)
        self.register_entity(
            type=PrivacyEntityType.PHONE,
            pattern=re.compile(r"\b(\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b"),
            description="Phone number",
            anonymization_func=lambda x: "[REDACTED PHONE]",
        )
        
        # Address pattern (simplified)
        self.register_entity(
            type=PrivacyEntityType.ADDRESS,
            pattern=re.compile(r"\b\d+\s+[A-Za-z\s]+,\s+[A-Za-z\s]+,\s+[A-Z]{2}\s+\d{5}\b"),
            description="Street address",
            anonymization_func=lambda x: "[REDACTED ADDRESS]",
        )
        
        # SSN pattern
        self.register_entity(
            type=PrivacyEntityType.SSN,
            pattern=re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
            description="Social Security Number",
            anonymization_func=lambda x: "[REDACTED SSN]",
        )
        
        # Credit card pattern
        self.register_entity(
            type=PrivacyEntityType.CREDIT_CARD,
            pattern=re.compile(r"\b(?:\d{4}[- ]?){3}\d{4}\b"),
            description="Credit card number",
            anonymization_func=lambda x: "[REDACTED CREDIT CARD]",
        )
        
        # IP address pattern
        self.register_entity(
            type=PrivacyEntityType.IP_ADDRESS,
            pattern=re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"),
            description="IP address",
            anonymization_func=lambda x: "[REDACTED IP]",
        )
        
        # Date of birth pattern
        self.register_entity(
            type=PrivacyEntityType.DATE_OF_BIRTH,
            pattern=re.compile(r"\b\d{1,2}/\d{1,2}/\d{4}\b"),
            description="Date of birth",
            anonymization_func=lambda x: "[REDACTED DOB]",
        )
        
    def register_entity(
        self,
        type: PrivacyEntityType,
        pattern: Pattern,
        description: str,
        anonymization_func: Callable[[str], str],
    ) -> None:
        """Register a privacy entity.
        
        Args:
            type: Entity type
            pattern: Regex pattern for detection
            description: Entity description
            anonymization_func: Function for anonymizing the entity
        """
        self._entities[type] = PrivacyEntity(
            type=type,
            pattern=pattern,
            description=description,
            anonymization_func=anonymization_func,
        )
        
        self._logger.info(f"Registered privacy entity: {type}")
        
    def unregister_entity(
        self,
        type: PrivacyEntityType,
    ) -> bool:
        """Unregister a privacy entity.
        
        Args:
            type: Entity type
            
        Returns:
            True if the entity was unregistered, False otherwise
        """
        if type in self._entities:
            del self._entities[type]
            self._logger.info(f"Unregistered privacy entity: {type}")
            return True
        else:
            return False
            
    def detect_entities(
        self,
        text: str,
        entity_types: Optional[List[PrivacyEntityType]] = None,
    ) -> PrivacyDetectionResult:
        """Detect privacy entities in text.
        
        Args:
            text: Text to analyze
            entity_types: Types of entities to detect (if None, all registered entities are used)
            
        Returns:
            Detection result
        """
        entities = []
        
        # Use all registered entities if not specified
        if entity_types is None:
            entity_types = list(self._entities.keys())
            
        # Detect entities
        for entity_type in entity_types:
            if entity_type not in self._entities:
                continue
                
            entity = self._entities[entity_type]
            
            # Find all matches
            for match in entity.pattern.finditer(text):
                entities.append({
                    "type": entity_type,
                    "value": match.group(),
                    "start": match.start(),
                    "end": match.end(),
                    "description": entity.description,
                })
                
        # Sort entities by start position
        entities.sort(key=lambda x: x["start"])
        
        return PrivacyDetectionResult(
            text=text,
            entities=entities,
        )
        
    def anonymize_text(
        self,
        text: str,
        entity_types: Optional[List[PrivacyEntityType]] = None,
    ) -> PrivacyDetectionResult:
        """Anonymize privacy entities in text.
        
        Args:
            text: Text to anonymize
            entity_types: Types of entities to anonymize (if None, all registered entities are used)
            
        Returns:
            Detection result with anonymized text
        """
        # Detect entities
        result = self.detect_entities(text, entity_types)
        
        # Anonymize text
        if result.entities:
            # Create a list of characters
            chars = list(text)
            
            # Replace entities from right to left to avoid index issues
            for entity in reversed(result.entities):
                entity_type = PrivacyEntityType(entity["type"])
                entity_value = entity["value"]
                start = entity["start"]
                end = entity["end"]
                
                # Get the anonymization function
                anonymization_func = self._entities[entity_type].anonymization_func
                
                # Replace the entity
                replacement = anonymization_func(entity_value)
                chars[start:end] = list(replacement)
                
            # Join the characters
            result.anonymized_text = "".join(chars)
        else:
            # No entities found, return the original text
            result.anonymized_text = text
            
        return result
        
    def hash_identifier(
        self,
        identifier: str,
        salt: Optional[str] = None,
    ) -> str:
        """Hash an identifier for pseudonymization.
        
        Args:
            identifier: Identifier to hash
            salt: Salt for hashing (if None, a random salt is generated)
            
        Returns:
            Hashed identifier
        """
        # Generate salt if not provided
        if salt is None:
            salt = uuid.uuid4().hex
            
        # Hash the identifier with the salt
        hashed = hashlib.sha256((identifier + salt).encode()).hexdigest()
        
        return hashed
        
    def pseudonymize_data(
        self,
        data: Dict[str, Any],
        fields: List[str],
        salt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Pseudonymize fields in data.
        
        Args:
            data: Data to pseudonymize
            fields: Fields to pseudonymize
            salt: Salt for hashing (if None, a random salt is generated)
            
        Returns:
            Pseudonymized data
        """
        # Generate salt if not provided
        if salt is None:
            salt = uuid.uuid4().hex
            
        # Create a copy of the data
        result = data.copy()
        
        # Pseudonymize fields
        for field in fields:
            if field in result and result[field]:
                result[field] = self.hash_identifier(str(result[field]), salt)
                
        return result
        
    def generate_synthetic_data(
        self,
        schema: Dict[str, Any],
        count: int = 1,
    ) -> List[Dict[str, Any]]:
        """Generate synthetic data based on a schema.
        
        Args:
            schema: Data schema with field types and constraints
            count: Number of records to generate
            
        Returns:
            List of synthetic data records
        """
        results = []
        
        for _ in range(count):
            record = {}
            
            for field, field_schema in schema.items():
                field_type = field_schema.get("type", "string")
                
                if field_type == "string":
                    min_length = field_schema.get("min_length", 5)
                    max_length = field_schema.get("max_length", 10)
                    length = random.randint(min_length, max_length)
                    record[field] = "".join(random.choices("abcdefghijklmnopqrstuvwxyz", k=length))
                    
                elif field_type == "integer":
                    min_value = field_schema.get("min", 0)
                    max_value = field_schema.get("max", 100)
                    record[field] = random.randint(min_value, max_value)
                    
                elif field_type == "float":
                    min_value = field_schema.get("min", 0.0)
                    max_value = field_schema.get("max", 100.0)
                    record[field] = random.uniform(min_value, max_value)
                    
                elif field_type == "boolean":
                    record[field] = random.choice([True, False])
                    
                elif field_type == "date":
                    # Generate a random date between 1970 and 2020
                    year = random.randint(1970, 2020)
                    month = random.randint(1, 12)
                    day = random.randint(1, 28)  # Simplified to avoid month-specific logic
                    record[field] = f"{year:04d}-{month:02d}-{day:02d}"
                    
                elif field_type == "enum":
                    values = field_schema.get("values", [])
                    if values:
                        record[field] = random.choice(values)
                    else:
                        record[field] = None
                        
                else:
                    record[field] = None
                    
            results.append(record)
            
        return results
        
    def k_anonymize(
        self,
        data: List[Dict[str, Any]],
        quasi_identifiers: List[str],
        k: int = 2,
    ) -> List[Dict[str, Any]]:
        """Apply k-anonymity to data.
        
        Args:
            data: Data to anonymize
            quasi_identifiers: Quasi-identifier fields
            k: Anonymity parameter (minimum group size)
            
        Returns:
            Anonymized data
            
        Raises:
            PrivacyError: If k-anonymity cannot be achieved
        """
        if not data:
            return []
            
        # Group records by quasi-identifiers
        groups = {}
        for record in data:
            key = tuple(str(record.get(qi, "")) for qi in quasi_identifiers)
            if key not in groups:
                groups[key] = []
            groups[key].append(record)
            
        # Check if any group has fewer than k records
        small_groups = [key for key, records in groups.items() if len(records) < k]
        
        if small_groups:
            # Generalize or suppress small groups
            result = []
            
            for key, records in groups.items():
                if len(records) >= k:
                    # Keep groups that satisfy k-anonymity
                    result.extend(records)
                else:
                    # Suppress small groups
                    for record in records:
                        anonymized_record = record.copy()
                        for qi in quasi_identifiers:
                            if qi in anonymized_record:
                                anonymized_record[qi] = "[SUPPRESSED]"
                        result.append(anonymized_record)
                        
            return result
        else:
            # All groups satisfy k-anonymity
            return data
