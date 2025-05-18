"""
Multi-modal capabilities module for Parlant.

This module provides functionality for working with different types of data beyond text,
such as images, audio, and video.
"""

from parlant.multimodal.image import (
    ImageProcessor,
    Image,
    ImageId,
    ImageMetadata,
    ImageFormat,
    ImageAnalysisResult,
)

from parlant.multimodal.audio import (
    AudioProcessor,
    Audio,
    AudioId,
    AudioMetadata,
    AudioFormat,
    TranscriptionResult,
    AudioAnalysisResult,
)

from parlant.multimodal.video import (
    VideoProcessor,
    Video,
    VideoId,
    VideoMetadata,
    VideoFormat,
    VideoFrame,
    VideoAnalysisResult,
)

from parlant.multimodal.context import (
    MultiModalContextManager,
    MultiModalContext,
    MultiModalContent,
    ContentId,
    ContentType,
)

from parlant.multimodal.generation import (
    MultiModalGenerator,
    GenerationOptions,
    GenerationResult,
    GenerationMode,
)

__all__ = [
    # Image
    "ImageProcessor",
    "Image",
    "ImageId",
    "ImageMetadata",
    "ImageFormat",
    "ImageAnalysisResult",
    
    # Audio
    "AudioProcessor",
    "Audio",
    "AudioId",
    "AudioMetadata",
    "AudioFormat",
    "TranscriptionResult",
    "AudioAnalysisResult",
    
    # Video
    "VideoProcessor",
    "Video",
    "VideoId",
    "VideoMetadata",
    "VideoFormat",
    "VideoFrame",
    "VideoAnalysisResult",
    
    # Context
    "MultiModalContextManager",
    "MultiModalContext",
    "MultiModalContent",
    "ContentId",
    "ContentType",
    
    # Generation
    "MultiModalGenerator",
    "GenerationOptions",
    "GenerationResult",
    "GenerationMode",
]
