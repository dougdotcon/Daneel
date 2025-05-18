"""
Image processing and understanding for Parlant.

This module provides functionality for processing and understanding images.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import uuid
import json
import base64
import io
import os
from pathlib import Path

from parlant.core.common import JSONSerializable, generate_id
from parlant.core.loggers import Logger
from parlant.core.async_utils import ReaderWriterLock
from parlant.core.nlp.service import NLPService
from parlant.core.nlp.generation_info import GenerationInfo


class ImageFormat(str, Enum):
    """Image formats."""
    
    JPEG = "jpeg"
    PNG = "png"
    GIF = "gif"
    BMP = "bmp"
    WEBP = "webp"
    TIFF = "tiff"
    SVG = "svg"
    OTHER = "other"


class ImageId(str):
    """Image ID."""
    pass


@dataclass
class ImageMetadata:
    """Metadata for an image."""
    
    width: int
    height: int
    format: ImageFormat
    channels: int
    creation_utc: datetime
    size_bytes: int
    mime_type: str
    metadata: Dict[str, JSONSerializable] = field(default_factory=dict)


@dataclass
class Image:
    """Image data and metadata."""
    
    id: ImageId
    data: bytes
    metadata: ImageMetadata
    tags: List[str] = field(default_factory=list)
    description: Optional[str] = None


@dataclass
class ImageAnalysisResult:
    """Result of image analysis."""
    
    image_id: ImageId
    description: str
    objects: List[Dict[str, Any]]
    tags: List[str]
    text: Optional[str] = None
    sentiment: Optional[str] = None
    colors: Optional[List[str]] = None
    metadata: Dict[str, JSONSerializable] = field(default_factory=dict)


class ImageProcessor:
    """Processor for images."""
    
    def __init__(
        self,
        nlp_service: NLPService,
        logger: Logger,
    ):
        """Initialize the image processor.
        
        Args:
            nlp_service: NLP service for image understanding
            logger: Logger instance
        """
        self._nlp_service = nlp_service
        self._logger = logger
        self._lock = ReaderWriterLock()
        
    async def load_image(
        self,
        path: Union[str, Path],
    ) -> Image:
        """Load an image from a file.
        
        Args:
            path: Path to the image file
            
        Returns:
            Loaded image
        """
        try:
            # Import PIL only when needed
            from PIL import Image as PILImage
            
            # Load the image
            pil_image = PILImage.open(path)
            
            # Get image metadata
            width, height = pil_image.size
            format_str = pil_image.format.lower() if pil_image.format else "unknown"
            image_format = ImageFormat(format_str) if format_str in [f.value for f in ImageFormat] else ImageFormat.OTHER
            channels = len(pil_image.getbands())
            
            # Get file size
            file_size = os.path.getsize(path)
            
            # Get MIME type
            mime_type = f"image/{format_str}"
            
            # Convert to bytes
            img_byte_arr = io.BytesIO()
            pil_image.save(img_byte_arr, format=pil_image.format)
            img_bytes = img_byte_arr.getvalue()
            
            # Create metadata
            metadata = ImageMetadata(
                width=width,
                height=height,
                format=image_format,
                channels=channels,
                creation_utc=datetime.now(timezone.utc),
                size_bytes=file_size,
                mime_type=mime_type,
            )
            
            # Create image
            image = Image(
                id=ImageId(generate_id()),
                data=img_bytes,
                metadata=metadata,
            )
            
            self._logger.info(f"Loaded image: {path} ({width}x{height}, {format_str}, {channels} channels, {file_size} bytes)")
            
            return image
            
        except Exception as e:
            self._logger.error(f"Error loading image: {e}")
            raise
            
    async def load_image_from_bytes(
        self,
        data: bytes,
        format: Optional[str] = None,
    ) -> Image:
        """Load an image from bytes.
        
        Args:
            data: Image data
            format: Image format (if known)
            
        Returns:
            Loaded image
        """
        try:
            # Import PIL only when needed
            from PIL import Image as PILImage
            
            # Load the image
            img_byte_arr = io.BytesIO(data)
            pil_image = PILImage.open(img_byte_arr)
            
            # Get image metadata
            width, height = pil_image.size
            format_str = format or (pil_image.format.lower() if pil_image.format else "unknown")
            image_format = ImageFormat(format_str) if format_str in [f.value for f in ImageFormat] else ImageFormat.OTHER
            channels = len(pil_image.getbands())
            
            # Get file size
            file_size = len(data)
            
            # Get MIME type
            mime_type = f"image/{format_str}"
            
            # Create metadata
            metadata = ImageMetadata(
                width=width,
                height=height,
                format=image_format,
                channels=channels,
                creation_utc=datetime.now(timezone.utc),
                size_bytes=file_size,
                mime_type=mime_type,
            )
            
            # Create image
            image = Image(
                id=ImageId(generate_id()),
                data=data,
                metadata=metadata,
            )
            
            self._logger.info(f"Loaded image from bytes: {width}x{height}, {format_str}, {channels} channels, {file_size} bytes")
            
            return image
            
        except Exception as e:
            self._logger.error(f"Error loading image from bytes: {e}")
            raise
            
    async def save_image(
        self,
        image: Image,
        path: Union[str, Path],
    ) -> None:
        """Save an image to a file.
        
        Args:
            image: Image to save
            path: Path to save the image to
        """
        try:
            # Import PIL only when needed
            from PIL import Image as PILImage
            
            # Convert bytes to PIL image
            img_byte_arr = io.BytesIO(image.data)
            pil_image = PILImage.open(img_byte_arr)
            
            # Save the image
            pil_image.save(path)
            
            self._logger.info(f"Saved image: {path}")
            
        except Exception as e:
            self._logger.error(f"Error saving image: {e}")
            raise
            
    async def resize_image(
        self,
        image: Image,
        width: int,
        height: int,
    ) -> Image:
        """Resize an image.
        
        Args:
            image: Image to resize
            width: New width
            height: New height
            
        Returns:
            Resized image
        """
        try:
            # Import PIL only when needed
            from PIL import Image as PILImage
            
            # Convert bytes to PIL image
            img_byte_arr = io.BytesIO(image.data)
            pil_image = PILImage.open(img_byte_arr)
            
            # Resize the image
            resized_image = pil_image.resize((width, height))
            
            # Convert back to bytes
            resized_byte_arr = io.BytesIO()
            resized_image.save(resized_byte_arr, format=pil_image.format)
            resized_bytes = resized_byte_arr.getvalue()
            
            # Create new metadata
            metadata = ImageMetadata(
                width=width,
                height=height,
                format=image.metadata.format,
                channels=image.metadata.channels,
                creation_utc=datetime.now(timezone.utc),
                size_bytes=len(resized_bytes),
                mime_type=image.metadata.mime_type,
                metadata=image.metadata.metadata,
            )
            
            # Create new image
            resized = Image(
                id=ImageId(generate_id()),
                data=resized_bytes,
                metadata=metadata,
                tags=image.tags.copy(),
                description=image.description,
            )
            
            self._logger.info(f"Resized image: {image.id} to {width}x{height}")
            
            return resized
            
        except Exception as e:
            self._logger.error(f"Error resizing image: {e}")
            raise
            
    async def analyze_image(
        self,
        image: Image,
    ) -> ImageAnalysisResult:
        """Analyze an image.
        
        Args:
            image: Image to analyze
            
        Returns:
            Analysis result
        """
        try:
            # Convert image to base64
            base64_image = base64.b64encode(image.data).decode("utf-8")
            
            # Create a prompt for image analysis
            prompt = self._create_image_analysis_prompt(base64_image, image.metadata)
            
            # Generate image analysis
            generator = await self._nlp_service.get_generator()
            generation_result = await generator.generate(prompt)
            
            # Parse the analysis
            analysis = self._parse_image_analysis(image.id, generation_result.text)
            
            self._logger.info(f"Analyzed image: {image.id}")
            
            return analysis
            
        except Exception as e:
            self._logger.error(f"Error analyzing image: {e}")
            raise
            
    def _create_image_analysis_prompt(
        self,
        base64_image: str,
        metadata: ImageMetadata,
    ) -> str:
        """Create a prompt for image analysis.
        
        Args:
            base64_image: Base64-encoded image
            metadata: Image metadata
            
        Returns:
            Prompt for image analysis
        """
        prompt = """You are an AI assistant tasked with analyzing an image.
I will provide you with a base64-encoded image and its metadata. Your task is to analyze the image and provide:
1. A detailed description of the image
2. A list of objects in the image
3. Tags that describe the image
4. Any text visible in the image
5. The overall sentiment of the image
6. The dominant colors in the image

Format your response as follows:
DESCRIPTION:
[Detailed description of the image]

OBJECTS:
- [Object 1]
- [Object 2]
...

TAGS:
- [Tag 1]
- [Tag 2]
...

TEXT:
[Text visible in the image, or "No text visible" if none]

SENTIMENT:
[Overall sentiment of the image]

COLORS:
- [Color 1]
- [Color 2]
...

Here is the image (base64-encoded):
"""
        
        prompt += f"\n{base64_image}\n\nImage metadata:\n"
        prompt += f"Width: {metadata.width}\n"
        prompt += f"Height: {metadata.height}\n"
        prompt += f"Format: {metadata.format.value}\n"
        prompt += f"Channels: {metadata.channels}\n"
        
        return prompt
        
    def _parse_image_analysis(
        self,
        image_id: ImageId,
        analysis_text: str,
    ) -> ImageAnalysisResult:
        """Parse image analysis from analysis text.
        
        Args:
            image_id: Image ID
            analysis_text: Analysis text
            
        Returns:
            Image analysis result
        """
        # Extract sections
        description = ""
        objects = []
        tags = []
        text = None
        sentiment = None
        colors = []
        
        # Extract description
        if "DESCRIPTION:" in analysis_text:
            description_section = analysis_text.split("DESCRIPTION:", 1)[1].split("OBJECTS:", 1)[0].strip()
            description = description_section
            
        # Extract objects
        if "OBJECTS:" in analysis_text:
            objects_section = analysis_text.split("OBJECTS:", 1)[1].split("TAGS:", 1)[0].strip()
            object_lines = objects_section.split("\n")
            for line in object_lines:
                if line.strip().startswith("-"):
                    object_name = line.strip()[1:].strip()
                    if object_name:
                        objects.append({"name": object_name})
                        
        # Extract tags
        if "TAGS:" in analysis_text:
            tags_section = analysis_text.split("TAGS:", 1)[1].split("TEXT:", 1)[0].strip()
            tag_lines = tags_section.split("\n")
            for line in tag_lines:
                if line.strip().startswith("-"):
                    tag = line.strip()[1:].strip()
                    if tag:
                        tags.append(tag)
                        
        # Extract text
        if "TEXT:" in analysis_text:
            text_section = analysis_text.split("TEXT:", 1)[1].split("SENTIMENT:", 1)[0].strip()
            text = text_section if text_section != "No text visible" else None
            
        # Extract sentiment
        if "SENTIMENT:" in analysis_text:
            sentiment_section = analysis_text.split("SENTIMENT:", 1)[1].split("COLORS:", 1)[0].strip()
            sentiment = sentiment_section
            
        # Extract colors
        if "COLORS:" in analysis_text:
            colors_section = analysis_text.split("COLORS:", 1)[1].strip()
            color_lines = colors_section.split("\n")
            for line in color_lines:
                if line.strip().startswith("-"):
                    color = line.strip()[1:].strip()
                    if color:
                        colors.append(color)
                        
        return ImageAnalysisResult(
            image_id=image_id,
            description=description,
            objects=objects,
            tags=tags,
            text=text,
            sentiment=sentiment,
            colors=colors,
        )
