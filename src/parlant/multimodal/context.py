"""
Multi-modal context integration for Parlant.

This module provides functionality for integrating multi-modal content into agent context.
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
from parlant.core.prompts import PromptBuilder

from parlant.multimodal.image import Image, ImageId, ImageProcessor, ImageAnalysisResult
from parlant.multimodal.audio import Audio, AudioId, AudioProcessor, TranscriptionResult, AudioAnalysisResult
from parlant.multimodal.video import Video, VideoId, VideoProcessor, VideoAnalysisResult


class ContentType(str, Enum):
    """Types of multi-modal content."""
    
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"


class ContentId(str):
    """Content ID."""
    pass


@dataclass
class MultiModalContent:
    """Multi-modal content."""
    
    id: ContentId
    type: ContentType
    content_id: str  # ID of the specific content (e.g., ImageId, AudioId, VideoId)
    creation_utc: datetime
    metadata: Dict[str, JSONSerializable] = field(default_factory=dict)


@dataclass
class MultiModalContext:
    """Multi-modal context for agent interactions."""
    
    contents: List[MultiModalContent]
    text_context: str
    metadata: Dict[str, JSONSerializable] = field(default_factory=dict)


class MultiModalContextManager:
    """Manager for multi-modal context."""
    
    def __init__(
        self,
        nlp_service: NLPService,
        image_processor: ImageProcessor,
        audio_processor: AudioProcessor,
        video_processor: VideoProcessor,
        logger: Logger,
    ):
        """Initialize the multi-modal context manager.
        
        Args:
            nlp_service: NLP service for multi-modal understanding
            image_processor: Image processor
            audio_processor: Audio processor
            video_processor: Video processor
            logger: Logger instance
        """
        self._nlp_service = nlp_service
        self._image_processor = image_processor
        self._audio_processor = audio_processor
        self._video_processor = video_processor
        self._logger = logger
        self._lock = ReaderWriterLock()
        
        # Cache for content
        self._image_cache: Dict[ImageId, Tuple[Image, Optional[ImageAnalysisResult]]] = {}
        self._audio_cache: Dict[AudioId, Tuple[Audio, Optional[TranscriptionResult], Optional[AudioAnalysisResult]]] = {}
        self._video_cache: Dict[VideoId, Tuple[Video, Optional[VideoAnalysisResult]]] = {}
        
    async def add_image_to_context(
        self,
        image: Image,
        analysis: Optional[ImageAnalysisResult] = None,
    ) -> MultiModalContent:
        """Add an image to the context.
        
        Args:
            image: Image to add
            analysis: Image analysis (if available)
            
        Returns:
            Multi-modal content
        """
        async with self._lock.writer_lock:
            # Analyze the image if not provided
            if analysis is None:
                analysis = await self._image_processor.analyze_image(image)
                
            # Cache the image and analysis
            self._image_cache[image.id] = (image, analysis)
            
            # Create multi-modal content
            content = MultiModalContent(
                id=ContentId(generate_id()),
                type=ContentType.IMAGE,
                content_id=image.id,
                creation_utc=datetime.now(timezone.utc),
                metadata={
                    "width": image.metadata.width,
                    "height": image.metadata.height,
                    "format": image.metadata.format.value,
                    "description": analysis.description,
                    "tags": analysis.tags,
                },
            )
            
            self._logger.info(f"Added image to context: {image.id}")
            
            return content
            
    async def add_audio_to_context(
        self,
        audio: Audio,
        transcription: Optional[TranscriptionResult] = None,
        analysis: Optional[AudioAnalysisResult] = None,
    ) -> MultiModalContent:
        """Add audio to the context.
        
        Args:
            audio: Audio to add
            transcription: Audio transcription (if available)
            analysis: Audio analysis (if available)
            
        Returns:
            Multi-modal content
        """
        async with self._lock.writer_lock:
            # Transcribe the audio if not provided
            if transcription is None:
                transcription = await self._audio_processor.transcribe_audio(audio)
                
            # Analyze the audio if not provided
            if analysis is None:
                analysis = await self._audio_processor.analyze_audio(audio, transcription)
                
            # Cache the audio, transcription, and analysis
            self._audio_cache[audio.id] = (audio, transcription, analysis)
            
            # Create multi-modal content
            content = MultiModalContent(
                id=ContentId(generate_id()),
                type=ContentType.AUDIO,
                content_id=audio.id,
                creation_utc=datetime.now(timezone.utc),
                metadata={
                    "duration": audio.metadata.duration_seconds,
                    "format": audio.metadata.format.value,
                    "transcription": transcription.text,
                    "description": analysis.description,
                    "tags": analysis.tags,
                },
            )
            
            self._logger.info(f"Added audio to context: {audio.id}")
            
            return content
            
    async def add_video_to_context(
        self,
        video: Video,
        analysis: Optional[VideoAnalysisResult] = None,
    ) -> MultiModalContent:
        """Add a video to the context.
        
        Args:
            video: Video to add
            analysis: Video analysis (if available)
            
        Returns:
            Multi-modal content
        """
        async with self._lock.writer_lock:
            # Analyze the video if not provided
            if analysis is None:
                analysis = await self._video_processor.analyze_video(video)
                
            # Cache the video and analysis
            self._video_cache[video.id] = (video, analysis)
            
            # Create multi-modal content
            content = MultiModalContent(
                id=ContentId(generate_id()),
                type=ContentType.VIDEO,
                content_id=video.id,
                creation_utc=datetime.now(timezone.utc),
                metadata={
                    "duration": video.metadata.duration_seconds,
                    "width": video.metadata.width,
                    "height": video.metadata.height,
                    "format": video.metadata.format.value,
                    "description": analysis.description,
                    "tags": analysis.tags,
                    "transcription": analysis.transcription.text if analysis.transcription else None,
                },
            )
            
            self._logger.info(f"Added video to context: {video.id}")
            
            return content
            
    async def create_context(
        self,
        contents: List[MultiModalContent],
    ) -> MultiModalContext:
        """Create a multi-modal context.
        
        Args:
            contents: Multi-modal contents
            
        Returns:
            Multi-modal context
        """
        async with self._lock.reader_lock:
            # Generate text context
            text_context = await self._generate_text_context(contents)
            
            # Create multi-modal context
            context = MultiModalContext(
                contents=contents,
                text_context=text_context,
            )
            
            self._logger.info(f"Created multi-modal context with {len(contents)} contents")
            
            return context
            
    async def _generate_text_context(
        self,
        contents: List[MultiModalContent],
    ) -> str:
        """Generate text context from multi-modal contents.
        
        Args:
            contents: Multi-modal contents
            
        Returns:
            Text context
        """
        text_parts = []
        
        for content in contents:
            if content.type == ContentType.IMAGE:
                # Get image and analysis from cache
                image_id = ImageId(content.content_id)
                if image_id in self._image_cache:
                    image, analysis = self._image_cache[image_id]
                    
                    text_parts.append(f"[Image: {analysis.description}]")
                    
                    if analysis.text:
                        text_parts.append(f"Text in image: {analysis.text}")
                        
                    if analysis.objects:
                        objects_text = ", ".join([obj["name"] for obj in analysis.objects])
                        text_parts.append(f"Objects in image: {objects_text}")
                        
            elif content.type == ContentType.AUDIO:
                # Get audio, transcription, and analysis from cache
                audio_id = AudioId(content.content_id)
                if audio_id in self._audio_cache:
                    audio, transcription, analysis = self._audio_cache[audio_id]
                    
                    text_parts.append(f"[Audio: {analysis.description}]")
                    
                    if transcription:
                        text_parts.append(f"Transcription: {transcription.text}")
                        
            elif content.type == ContentType.VIDEO:
                # Get video and analysis from cache
                video_id = VideoId(content.content_id)
                if video_id in self._video_cache:
                    video, analysis = self._video_cache[video_id]
                    
                    text_parts.append(f"[Video: {analysis.description}]")
                    
                    if analysis.transcription:
                        text_parts.append(f"Transcription: {analysis.transcription.text}")
                        
                    if analysis.scenes:
                        scenes_text = "\n".join([f"- [{scene['start_time']} - {scene['end_time']}] {scene['description']}" for scene in analysis.scenes])
                        text_parts.append(f"Scenes in video:\n{scenes_text}")
                        
                    if analysis.objects:
                        objects_text = "\n".join([f"- {obj['name']}: {obj['timestamps']}" for obj in analysis.objects])
                        text_parts.append(f"Objects in video:\n{objects_text}")
                        
            elif content.type == ContentType.TEXT:
                # Text content
                text_parts.append(content.metadata.get("text", ""))
                
        return "\n\n".join(text_parts)
        
    async def add_context_to_prompt(
        self,
        prompt_builder: PromptBuilder,
        context: MultiModalContext,
    ) -> PromptBuilder:
        """Add multi-modal context to a prompt.
        
        Args:
            prompt_builder: Prompt builder
            context: Multi-modal context
            
        Returns:
            Updated prompt builder
        """
        # Add text context
        prompt_builder.add_context(context.text_context)
        
        # Add multi-modal content
        for content in context.contents:
            if content.type == ContentType.IMAGE:
                # Get image from cache
                image_id = ImageId(content.content_id)
                if image_id in self._image_cache:
                    image, _ = self._image_cache[image_id]
                    
                    # Add image to prompt
                    prompt_builder.add_image(base64.b64encode(image.data).decode("utf-8"))
                    
            # Note: Audio and video are handled through their text representations
                    
        return prompt_builder
        
    def get_image(self, image_id: ImageId) -> Optional[Tuple[Image, Optional[ImageAnalysisResult]]]:
        """Get an image from the cache.
        
        Args:
            image_id: Image ID
            
        Returns:
            Image and analysis if found, None otherwise
        """
        return self._image_cache.get(image_id)
        
    def get_audio(self, audio_id: AudioId) -> Optional[Tuple[Audio, Optional[TranscriptionResult], Optional[AudioAnalysisResult]]]:
        """Get audio from the cache.
        
        Args:
            audio_id: Audio ID
            
        Returns:
            Audio, transcription, and analysis if found, None otherwise
        """
        return self._audio_cache.get(audio_id)
        
    def get_video(self, video_id: VideoId) -> Optional[Tuple[Video, Optional[VideoAnalysisResult]]]:
        """Get a video from the cache.
        
        Args:
            video_id: Video ID
            
        Returns:
            Video and analysis if found, None otherwise
        """
        return self._video_cache.get(video_id)
