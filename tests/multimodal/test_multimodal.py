"""
Tests for the multi-modal capabilities.
"""

import os
import pytest
import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import MagicMock, AsyncMock
import tempfile
import base64

from Daneel.core.loggers import ConsoleLogger
from Daneel.core.nlp.service import NLPService
from Daneel.core.nlp.generation_info import GenerationInfo
from Daneel.core.prompts import PromptBuilder

from Daneel.multimodal import (
    ImageProcessor,
    Image,
    ImageId,
    ImageMetadata,
    ImageFormat,
    ImageAnalysisResult,
    AudioProcessor,
    Audio,
    AudioId,
    AudioMetadata,
    AudioFormat,
    TranscriptionResult,
    AudioAnalysisResult,
    VideoProcessor,
    Video,
    VideoId,
    VideoMetadata,
    VideoFormat,
    VideoFrame,
    VideoAnalysisResult,
    MultiModalContextManager,
    MultiModalContext,
    MultiModalContent,
    ContentId,
    ContentType,
    MultiModalGenerator,
    GenerationOptions,
    GenerationResult,
    GenerationMode,
)


class MockNLPService(NLPService):
    """Mock NLP service for testing."""
    
    async def get_generator(self) -> Any:
        """Get a generator."""
        generator = MagicMock()
        generator.generate = AsyncMock(return_value=GenerationInfo(
            text="""DESCRIPTION:
A test image showing a landscape with mountains and a lake.

OBJECTS:
- Mountain
- Lake
- Tree
- Sky

TAGS:
- Landscape
- Nature
- Mountains
- Lake
- Scenic

TEXT:
No text visible

SENTIMENT:
Peaceful

COLORS:
- Blue
- Green
- White
- Brown""",
            usage={"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
        ))
        return generator


@pytest.fixture
def logger():
    return ConsoleLogger()


@pytest.fixture
def nlp_service():
    return MockNLPService()


@pytest.fixture
def image_processor(nlp_service, logger):
    return ImageProcessor(nlp_service, logger)


@pytest.fixture
def audio_processor(nlp_service, logger):
    return AudioProcessor(nlp_service, logger)


@pytest.fixture
def video_processor(nlp_service, image_processor, audio_processor, logger):
    return VideoProcessor(nlp_service, image_processor, audio_processor, logger)


@pytest.fixture
def context_manager(nlp_service, image_processor, audio_processor, video_processor, logger):
    return MultiModalContextManager(nlp_service, image_processor, audio_processor, video_processor, logger)


@pytest.fixture
def generator(nlp_service, image_processor, audio_processor, video_processor, logger):
    return MultiModalGenerator(nlp_service, image_processor, audio_processor, video_processor, logger)


@pytest.fixture
def test_image_path():
    # Create a temporary image file
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
        # Create a simple image
        from PIL import Image, ImageDraw
        img = Image.new("RGB", (100, 100), color=(73, 109, 137))
        draw = ImageDraw.Draw(img)
        draw.rectangle([(20, 20), (80, 80)], fill=(128, 0, 0))
        img.save(temp_file.name)
        
    yield temp_file.name
    
    # Clean up
    os.unlink(temp_file.name)


@pytest.fixture
def test_audio_path():
    # Create a temporary audio file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
        # Create a simple audio file
        import numpy as np
        import soundfile as sf
        
        # Generate a simple sine wave
        sample_rate = 44100
        duration = 1.0  # seconds
        t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
        data = np.sin(2 * np.pi * 440 * t)  # 440 Hz sine wave
        
        # Save the audio file
        sf.write(temp_file.name, data, sample_rate)
        
    yield temp_file.name
    
    # Clean up
    os.unlink(temp_file.name)


@pytest.fixture
def test_video_path():
    # Create a temporary video file
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
        # Create a simple video file
        import cv2
        import numpy as np
        
        # Create a video writer
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        fps = 30
        width, height = 100, 100
        out = cv2.VideoWriter(temp_file.name, fourcc, fps, (width, height))
        
        # Create frames
        for i in range(30):  # 1 second at 30 fps
            # Create a frame with a moving rectangle
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            x = i % (width - 20)
            cv2.rectangle(frame, (x, 40), (x + 20, 60), (0, 0, 255), -1)
            
            # Write the frame
            out.write(frame)
            
        # Release the video writer
        out.release()
        
    yield temp_file.name
    
    # Clean up
    os.unlink(temp_file.name)


async def test_image_processing(image_processor, test_image_path):
    """Test that images can be processed."""
    # Load an image
    image = await image_processor.load_image(test_image_path)
    
    # Check that the image was loaded
    assert image is not None
    assert image.id is not None
    assert image.data is not None
    assert image.metadata is not None
    assert image.metadata.width == 100
    assert image.metadata.height == 100
    assert image.metadata.format == ImageFormat.PNG
    
    # Resize the image
    resized = await image_processor.resize_image(image, 50, 50)
    
    # Check that the image was resized
    assert resized is not None
    assert resized.id is not None
    assert resized.id != image.id
    assert resized.metadata.width == 50
    assert resized.metadata.height == 50
    
    # Analyze the image
    analysis = await image_processor.analyze_image(image)
    
    # Check that the image was analyzed
    assert analysis is not None
    assert analysis.image_id == image.id
    assert analysis.description is not None
    assert analysis.objects is not None
    assert analysis.tags is not None
    
    # Save the image
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
        await image_processor.save_image(image, temp_file.name)
        
        # Check that the file exists
        assert os.path.exists(temp_file.name)
        
        # Clean up
        os.unlink(temp_file.name)


async def test_audio_processing(audio_processor, test_audio_path):
    """Test that audio can be processed."""
    # Load audio
    audio = await audio_processor.load_audio(test_audio_path)
    
    # Check that the audio was loaded
    assert audio is not None
    assert audio.id is not None
    assert audio.data is not None
    assert audio.metadata is not None
    assert audio.metadata.duration_seconds > 0
    assert audio.metadata.format == AudioFormat.WAV
    assert audio.metadata.sample_rate == 44100
    assert audio.metadata.channels == 1
    
    # Transcribe the audio
    transcription = await audio_processor.transcribe_audio(audio)
    
    # Check that the audio was transcribed
    assert transcription is not None
    assert transcription.audio_id == audio.id
    assert transcription.text is not None
    assert transcription.confidence >= 0
    assert transcription.language is not None
    assert transcription.segments is not None
    
    # Analyze the audio
    analysis = await audio_processor.analyze_audio(audio, transcription)
    
    # Check that the audio was analyzed
    assert analysis is not None
    assert analysis.audio_id == audio.id
    assert analysis.description is not None
    assert analysis.tags is not None
    
    # Save the audio
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
        await audio_processor.save_audio(audio, temp_file.name)
        
        # Check that the file exists
        assert os.path.exists(temp_file.name)
        
        # Clean up
        os.unlink(temp_file.name)


async def test_video_processing(video_processor, test_video_path):
    """Test that videos can be processed."""
    # Load a video
    video = await video_processor.load_video(test_video_path)
    
    # Check that the video was loaded
    assert video is not None
    assert video.id is not None
    assert video.data is not None
    assert video.metadata is not None
    assert video.metadata.width == 100
    assert video.metadata.height == 100
    assert video.metadata.duration_seconds > 0
    assert video.metadata.format == VideoFormat.MP4
    assert video.metadata.fps > 0
    
    # Extract frames
    frames = await video_processor.extract_frames(video, frame_interval=0.5)
    
    # Check that frames were extracted
    assert frames is not None
    assert len(frames) > 0
    assert frames[0].video_id == video.id
    assert frames[0].frame_number >= 0
    assert frames[0].timestamp_seconds >= 0
    assert frames[0].image is not None
    
    # Extract audio
    audio = await video_processor.extract_audio(video)
    
    # Audio might be None if the video has no audio
    if audio is not None:
        assert audio.id is not None
        assert audio.data is not None
        assert audio.metadata is not None
        assert audio.metadata.duration_seconds > 0
        
    # Analyze the video
    analysis = await video_processor.analyze_video(video, frames)
    
    # Check that the video was analyzed
    assert analysis is not None
    assert analysis.video_id == video.id
    assert analysis.description is not None
    assert analysis.tags is not None
    assert analysis.scenes is not None
    assert analysis.objects is not None
    assert analysis.actions is not None
    
    # Save the video
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
        await video_processor.save_video(video, temp_file.name)
        
        # Check that the file exists
        assert os.path.exists(temp_file.name)
        
        # Clean up
        os.unlink(temp_file.name)


async def test_context_integration(context_manager, image_processor, test_image_path):
    """Test that multi-modal content can be integrated into context."""
    # Load an image
    image = await image_processor.load_image(test_image_path)
    
    # Analyze the image
    analysis = await image_processor.analyze_image(image)
    
    # Add the image to context
    content = await context_manager.add_image_to_context(image, analysis)
    
    # Check that the content was created
    assert content is not None
    assert content.id is not None
    assert content.type == ContentType.IMAGE
    assert content.content_id == image.id
    
    # Create a context
    context = await context_manager.create_context([content])
    
    # Check that the context was created
    assert context is not None
    assert len(context.contents) == 1
    assert context.text_context is not None
    
    # Add context to a prompt
    prompt_builder = PromptBuilder()
    prompt_builder = await context_manager.add_context_to_prompt(prompt_builder, context)
    
    # Check that the prompt builder was updated
    assert prompt_builder is not None
    
    # Get the image from the cache
    cached_image = context_manager.get_image(image.id)
    
    # Check that the image was cached
    assert cached_image is not None
    assert cached_image[0].id == image.id
    assert cached_image[1].image_id == image.id


async def test_content_generation(generator):
    """Test that multi-modal content can be generated."""
    # Generate an image
    options = GenerationOptions(
        mode=GenerationMode.TEXT_TO_IMAGE,
        prompt="A beautiful landscape with mountains and a lake",
        width=512,
        height=512,
        format="png",
        style="realistic",
    )
    
    result = await generator.generate_content(options)
    
    # Check that the result was created
    assert result is not None
    assert result.mode == GenerationMode.TEXT_TO_IMAGE
    assert result.prompt == options.prompt
    assert result.content_type == "image"
    assert result.content_id is not None
    
    # Generate audio
    options = GenerationOptions(
        mode=GenerationMode.TEXT_TO_AUDIO,
        prompt="A calm piano melody",
        duration=5.0,
        format="mp3",
        style="classical",
    )
    
    result = await generator.generate_content(options)
    
    # Check that the result was created
    assert result is not None
    assert result.mode == GenerationMode.TEXT_TO_AUDIO
    assert result.prompt == options.prompt
    assert result.content_type == "audio"
    assert result.content_id is not None
    
    # Generate a video
    options = GenerationOptions(
        mode=GenerationMode.TEXT_TO_VIDEO,
        prompt="A timelapse of a sunset over the ocean",
        width=640,
        height=360,
        duration=5.0,
        format="mp4",
        style="cinematic",
    )
    
    result = await generator.generate_content(options)
    
    # Check that the result was created
    assert result is not None
    assert result.mode == GenerationMode.TEXT_TO_VIDEO
    assert result.prompt == options.prompt
    assert result.content_type == "video"
    assert result.content_id is not None
