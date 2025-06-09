"""
Multi-modal capabilities module for Daneel.

This module provides functionality for working with different types of data beyond text,
such as images, audio, and video.
"""

from Daneel.multimodal.image import (
    ImageProcessor,
    Image,
    ImageId,
    ImageMetadata,
    ImageFormat,
    ImageAnalysisResult,
)

from Daneel.multimodal.audio import (
    AudioProcessor,
    Audio,
    AudioId,
    AudioMetadata,
    AudioFormat,
    TranscriptionResult,
    AudioAnalysisResult,
)

from Daneel.multimodal.video import (
    VideoProcessor,
    Video,
    VideoId,
    VideoMetadata,
    VideoFormat,
    VideoFrame,
    VideoAnalysisResult,
)

from Daneel.multimodal.context import (
    MultiModalContextManager,
    MultiModalContext,
    MultiModalContent,
    ContentId,
    ContentType,
)

from Daneel.multimodal.generation import (
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
