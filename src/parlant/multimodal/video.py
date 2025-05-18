"""
Video analysis for Parlant.

This module provides functionality for analyzing video content.
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
import tempfile

from parlant.core.common import JSONSerializable, generate_id
from parlant.core.loggers import Logger
from parlant.core.async_utils import ReaderWriterLock
from parlant.core.nlp.service import NLPService
from parlant.core.nlp.generation_info import GenerationInfo

from parlant.multimodal.image import Image, ImageId, ImageProcessor, ImageAnalysisResult
from parlant.multimodal.audio import Audio, AudioId, AudioProcessor, TranscriptionResult


class VideoFormat(str, Enum):
    """Video formats."""
    
    MP4 = "mp4"
    AVI = "avi"
    MOV = "mov"
    MKV = "mkv"
    WMV = "wmv"
    FLV = "flv"
    WEBM = "webm"
    OTHER = "other"


class VideoId(str):
    """Video ID."""
    pass


@dataclass
class VideoMetadata:
    """Metadata for a video."""
    
    width: int
    height: int
    duration_seconds: float
    format: VideoFormat
    fps: float
    creation_utc: datetime
    size_bytes: int
    mime_type: str
    has_audio: bool
    audio_channels: Optional[int] = None
    audio_sample_rate: Optional[int] = None
    metadata: Dict[str, JSONSerializable] = field(default_factory=dict)


@dataclass
class Video:
    """Video data and metadata."""
    
    id: VideoId
    data: bytes
    metadata: VideoMetadata
    tags: List[str] = field(default_factory=list)
    description: Optional[str] = None


@dataclass
class VideoFrame:
    """A frame from a video."""
    
    video_id: VideoId
    frame_number: int
    timestamp_seconds: float
    image: Image


@dataclass
class VideoAnalysisResult:
    """Result of video analysis."""
    
    video_id: VideoId
    description: str
    tags: List[str]
    scenes: List[Dict[str, Any]]
    objects: List[Dict[str, Any]]
    actions: List[Dict[str, Any]]
    transcription: Optional[TranscriptionResult] = None
    sentiment: Optional[str] = None
    metadata: Dict[str, JSONSerializable] = field(default_factory=dict)


class VideoProcessor:
    """Processor for videos."""
    
    def __init__(
        self,
        nlp_service: NLPService,
        image_processor: ImageProcessor,
        audio_processor: AudioProcessor,
        logger: Logger,
    ):
        """Initialize the video processor.
        
        Args:
            nlp_service: NLP service for video understanding
            image_processor: Image processor for frame analysis
            audio_processor: Audio processor for audio analysis
            logger: Logger instance
        """
        self._nlp_service = nlp_service
        self._image_processor = image_processor
        self._audio_processor = audio_processor
        self._logger = logger
        self._lock = ReaderWriterLock()
        
    async def load_video(
        self,
        path: Union[str, Path],
    ) -> Video:
        """Load a video from a file.
        
        Args:
            path: Path to the video file
            
        Returns:
            Loaded video
        """
        try:
            # Import libraries only when needed
            import cv2
            
            # Open the video
            cap = cv2.VideoCapture(str(path))
            
            # Get video metadata
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            
            # Check if the video has audio
            has_audio = False
            audio_channels = None
            audio_sample_rate = None
            
            try:
                import moviepy.editor as mp
                video_clip = mp.VideoFileClip(str(path))
                has_audio = video_clip.audio is not None
                if has_audio:
                    audio_channels = video_clip.audio.nchannels
                    audio_sample_rate = video_clip.audio.fps
                video_clip.close()
            except Exception:
                # If moviepy fails, assume no audio
                pass
                
            # Get file format
            format_str = os.path.splitext(path)[1][1:].lower()
            video_format = VideoFormat(format_str) if format_str in [f.value for f in VideoFormat] else VideoFormat.OTHER
            
            # Get file size
            file_size = os.path.getsize(path)
            
            # Get MIME type
            mime_type = f"video/{format_str}"
            
            # Read the file as bytes
            with open(path, "rb") as f:
                video_bytes = f.read()
                
            # Release the video capture
            cap.release()
            
            # Create metadata
            metadata = VideoMetadata(
                width=width,
                height=height,
                duration_seconds=duration,
                format=video_format,
                fps=fps,
                creation_utc=datetime.now(timezone.utc),
                size_bytes=file_size,
                mime_type=mime_type,
                has_audio=has_audio,
                audio_channels=audio_channels,
                audio_sample_rate=audio_sample_rate,
            )
            
            # Create video
            video = Video(
                id=VideoId(generate_id()),
                data=video_bytes,
                metadata=metadata,
            )
            
            self._logger.info(f"Loaded video: {path} ({width}x{height}, {duration:.2f}s, {fps:.2f} fps, {format_str}, {file_size} bytes)")
            
            return video
            
        except Exception as e:
            self._logger.error(f"Error loading video: {e}")
            raise
            
    async def save_video(
        self,
        video: Video,
        path: Union[str, Path],
    ) -> None:
        """Save a video to a file.
        
        Args:
            video: Video to save
            path: Path to save the video to
        """
        try:
            # Save the video
            with open(path, "wb") as f:
                f.write(video.data)
                
            self._logger.info(f"Saved video: {path}")
            
        except Exception as e:
            self._logger.error(f"Error saving video: {e}")
            raise
            
    async def extract_frames(
        self,
        video: Video,
        frame_interval: float = 1.0,
        max_frames: Optional[int] = None,
    ) -> List[VideoFrame]:
        """Extract frames from a video.
        
        Args:
            video: Video to extract frames from
            frame_interval: Interval between frames in seconds
            max_frames: Maximum number of frames to extract
            
        Returns:
            List of extracted frames
        """
        try:
            # Import libraries only when needed
            import cv2
            import numpy as np
            
            # Create a temporary file
            with tempfile.NamedTemporaryFile(suffix=f".{video.metadata.format.value}", delete=False) as temp_file:
                temp_file.write(video.data)
                temp_path = temp_file.name
                
            try:
                # Open the video
                cap = cv2.VideoCapture(temp_path)
                
                # Calculate frame interval
                fps = video.metadata.fps
                frame_step = int(frame_interval * fps)
                if frame_step < 1:
                    frame_step = 1
                    
                # Extract frames
                frames = []
                frame_number = 0
                frame_count = 0
                
                while True:
                    # Check if we've reached the maximum number of frames
                    if max_frames is not None and frame_count >= max_frames:
                        break
                        
                    # Set the frame position
                    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
                    
                    # Read the frame
                    ret, frame = cap.read()
                    if not ret:
                        break
                        
                    # Convert the frame to an image
                    _, buffer = cv2.imencode(".jpg", frame)
                    frame_bytes = buffer.tobytes()
                    
                    # Create an image
                    image = await self._image_processor.load_image_from_bytes(frame_bytes, "jpeg")
                    
                    # Calculate timestamp
                    timestamp = frame_number / fps
                    
                    # Create a video frame
                    video_frame = VideoFrame(
                        video_id=video.id,
                        frame_number=frame_number,
                        timestamp_seconds=timestamp,
                        image=image,
                    )
                    
                    frames.append(video_frame)
                    frame_count += 1
                    
                    # Move to the next frame
                    frame_number += frame_step
                    
                # Release the video capture
                cap.release()
                
                self._logger.info(f"Extracted {len(frames)} frames from video: {video.id}")
                
                return frames
                
            finally:
                # Remove the temporary file
                os.unlink(temp_path)
                
        except Exception as e:
            self._logger.error(f"Error extracting frames: {e}")
            raise
            
    async def extract_audio(
        self,
        video: Video,
    ) -> Optional[Audio]:
        """Extract audio from a video.
        
        Args:
            video: Video to extract audio from
            
        Returns:
            Extracted audio, or None if the video has no audio
        """
        if not video.metadata.has_audio:
            return None
            
        try:
            # Import libraries only when needed
            import moviepy.editor as mp
            
            # Create a temporary file for the video
            with tempfile.NamedTemporaryFile(suffix=f".{video.metadata.format.value}", delete=False) as temp_video_file:
                temp_video_file.write(video.data)
                temp_video_path = temp_video_file.name
                
            try:
                # Create a temporary file for the audio
                temp_audio_path = f"{temp_video_path}.wav"
                
                # Extract audio
                video_clip = mp.VideoFileClip(temp_video_path)
                audio_clip = video_clip.audio
                
                if audio_clip is None:
                    return None
                    
                audio_clip.write_audiofile(temp_audio_path, logger=None)
                
                # Close the clips
                audio_clip.close()
                video_clip.close()
                
                # Load the audio
                audio = await self._audio_processor.load_audio(temp_audio_path)
                
                self._logger.info(f"Extracted audio from video: {video.id}")
                
                return audio
                
            finally:
                # Remove the temporary files
                if os.path.exists(temp_video_path):
                    os.unlink(temp_video_path)
                if os.path.exists(f"{temp_video_path}.wav"):
                    os.unlink(f"{temp_video_path}.wav")
                
        except Exception as e:
            self._logger.error(f"Error extracting audio: {e}")
            return None
            
    async def analyze_video(
        self,
        video: Video,
        frames: Optional[List[VideoFrame]] = None,
        audio: Optional[Audio] = None,
        transcription: Optional[TranscriptionResult] = None,
    ) -> VideoAnalysisResult:
        """Analyze a video.
        
        Args:
            video: Video to analyze
            frames: Extracted frames (if available)
            audio: Extracted audio (if available)
            transcription: Audio transcription (if available)
            
        Returns:
            Analysis result
        """
        try:
            # Extract frames if not provided
            if frames is None:
                frames = await self.extract_frames(video, frame_interval=5.0, max_frames=10)
                
            # Extract audio if not provided
            if audio is None and video.metadata.has_audio:
                audio = await self.extract_audio(video)
                
            # Transcribe audio if not provided
            if transcription is None and audio is not None:
                transcription = await self._audio_processor.transcribe_audio(audio)
                
            # Analyze frames
            frame_analyses = []
            for frame in frames:
                analysis = await self._image_processor.analyze_image(frame.image)
                frame_analyses.append((frame, analysis))
                
            # Create a prompt for video analysis
            prompt = self._create_video_analysis_prompt(video, frame_analyses, transcription)
            
            # Generate video analysis
            generator = await self._nlp_service.get_generator()
            generation_result = await generator.generate(prompt)
            
            # Parse the analysis
            analysis = self._parse_video_analysis(video.id, generation_result.text, transcription)
            
            self._logger.info(f"Analyzed video: {video.id}")
            
            return analysis
            
        except Exception as e:
            self._logger.error(f"Error analyzing video: {e}")
            raise
            
    def _create_video_analysis_prompt(
        self,
        video: Video,
        frame_analyses: List[Tuple[VideoFrame, ImageAnalysisResult]],
        transcription: Optional[TranscriptionResult] = None,
    ) -> str:
        """Create a prompt for video analysis.
        
        Args:
            video: Video to analyze
            frame_analyses: Frame analyses
            transcription: Audio transcription (if available)
            
        Returns:
            Prompt for video analysis
        """
        prompt = """You are an AI assistant tasked with analyzing a video.
I will provide you with metadata about the video, analyses of key frames, and a transcription of the audio (if available). Your task is to analyze the video and provide:
1. A detailed description of the video
2. Tags that describe the video
3. Scenes detected in the video
4. Objects detected in the video
5. Actions detected in the video
6. The overall sentiment of the video

Format your response as follows:
DESCRIPTION:
[Detailed description of the video]

TAGS:
- [Tag 1]
- [Tag 2]
...

SCENES:
- [00:00:00 - 00:00:10] [Scene description]
- [00:00:11 - 00:00:20] [Scene description]
...

OBJECTS:
- [Object 1]: [Timestamps where it appears]
- [Object 2]: [Timestamps where it appears]
...

ACTIONS:
- [Action 1]: [Timestamps where it occurs]
- [Action 2]: [Timestamps where it occurs]
...

SENTIMENT:
[Overall sentiment of the video]

Video metadata:
"""
        
        prompt += f"Duration: {video.metadata.duration_seconds:.2f} seconds\n"
        prompt += f"Resolution: {video.metadata.width}x{video.metadata.height}\n"
        prompt += f"FPS: {video.metadata.fps:.2f}\n"
        prompt += f"Format: {video.metadata.format.value}\n"
        prompt += f"Has audio: {video.metadata.has_audio}\n\n"
        
        prompt += "Frame analyses:\n"
        for i, (frame, analysis) in enumerate(frame_analyses):
            prompt += f"\nFrame {i+1} (Timestamp: {frame.timestamp_seconds:.2f}s):\n"
            prompt += f"Description: {analysis.description}\n"
            prompt += f"Objects: {', '.join([obj['name'] for obj in analysis.objects])}\n"
            if analysis.text:
                prompt += f"Text: {analysis.text}\n"
                
        if transcription:
            prompt += f"\nTranscription:\n{transcription.text}\n"
            
            if transcription.segments:
                prompt += "\nSegments:\n"
                for segment in transcription.segments:
                    speaker = f"[{segment['speaker']}]" if segment.get('speaker') else ""
                    prompt += f"[{segment['start_time']} - {segment['end_time']}] {speaker} {segment['text']}\n"
                    
        return prompt
        
    def _parse_video_analysis(
        self,
        video_id: VideoId,
        analysis_text: str,
        transcription: Optional[TranscriptionResult] = None,
    ) -> VideoAnalysisResult:
        """Parse video analysis from analysis text.
        
        Args:
            video_id: Video ID
            analysis_text: Analysis text
            transcription: Audio transcription (if available)
            
        Returns:
            Video analysis result
        """
        # Extract sections
        description = ""
        tags = []
        scenes = []
        objects = []
        actions = []
        sentiment = None
        
        # Extract description
        if "DESCRIPTION:" in analysis_text:
            description_section = analysis_text.split("DESCRIPTION:", 1)[1].split("TAGS:", 1)[0].strip()
            description = description_section
            
        # Extract tags
        if "TAGS:" in analysis_text:
            tags_section = analysis_text.split("TAGS:", 1)[1].split("SCENES:", 1)[0].strip()
            tag_lines = tags_section.split("\n")
            for line in tag_lines:
                if line.strip().startswith("-"):
                    tag = line.strip()[1:].strip()
                    if tag:
                        tags.append(tag)
                        
        # Extract scenes
        if "SCENES:" in analysis_text:
            scenes_section = analysis_text.split("SCENES:", 1)[1].split("OBJECTS:", 1)[0].strip()
            scene_lines = scenes_section.split("\n")
            for line in scene_lines:
                if line.strip().startswith("-"):
                    scene_text = line.strip()[1:].strip()
                    if scene_text:
                        # Parse scene
                        try:
                            time_range, description = scene_text.split("]", 1)
                            time_range = time_range.strip()[1:].strip()
                            start_time, end_time = time_range.split("-")
                            start_time = start_time.strip()
                            end_time = end_time.strip()
                            
                            scene = {
                                "start_time": start_time,
                                "end_time": end_time,
                                "description": description.strip(),
                            }
                            
                            scenes.append(scene)
                        except Exception:
                            # Skip malformed scenes
                            pass
                            
        # Extract objects
        if "OBJECTS:" in analysis_text:
            objects_section = analysis_text.split("OBJECTS:", 1)[1].split("ACTIONS:", 1)[0].strip()
            object_lines = objects_section.split("\n")
            for line in object_lines:
                if line.strip().startswith("-"):
                    object_text = line.strip()[1:].strip()
                    if object_text and ":" in object_text:
                        object_name, timestamps = object_text.split(":", 1)
                        object_name = object_name.strip()
                        timestamps = timestamps.strip()
                        
                        obj = {
                            "name": object_name,
                            "timestamps": timestamps,
                        }
                        
                        objects.append(obj)
                        
        # Extract actions
        if "ACTIONS:" in analysis_text:
            actions_section = analysis_text.split("ACTIONS:", 1)[1].split("SENTIMENT:", 1)[0].strip()
            action_lines = actions_section.split("\n")
            for line in action_lines:
                if line.strip().startswith("-"):
                    action_text = line.strip()[1:].strip()
                    if action_text and ":" in action_text:
                        action_name, timestamps = action_text.split(":", 1)
                        action_name = action_name.strip()
                        timestamps = timestamps.strip()
                        
                        action = {
                            "name": action_name,
                            "timestamps": timestamps,
                        }
                        
                        actions.append(action)
                        
        # Extract sentiment
        if "SENTIMENT:" in analysis_text:
            sentiment_section = analysis_text.split("SENTIMENT:", 1)[1].strip()
            sentiment = sentiment_section
            
        return VideoAnalysisResult(
            video_id=video_id,
            description=description,
            tags=tags,
            scenes=scenes,
            objects=objects,
            actions=actions,
            transcription=transcription,
            sentiment=sentiment,
        )
