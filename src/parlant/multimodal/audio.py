"""
Audio processing and transcription for Daneel.

This module provides functionality for processing and transcribing audio.
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

from Daneel.core.common import JSONSerializable, generate_id
from Daneel.core.loggers import Logger
from Daneel.core.async_utils import ReaderWriterLock
from Daneel.core.nlp.service import NLPService
from Daneel.core.nlp.generation_info import GenerationInfo


class AudioFormat(str, Enum):
    """Audio formats."""
    
    MP3 = "mp3"
    WAV = "wav"
    OGG = "ogg"
    FLAC = "flac"
    AAC = "aac"
    M4A = "m4a"
    OTHER = "other"


class AudioId(str):
    """Audio ID."""
    pass


@dataclass
class AudioMetadata:
    """Metadata for an audio file."""
    
    duration_seconds: float
    format: AudioFormat
    sample_rate: int
    channels: int
    creation_utc: datetime
    size_bytes: int
    mime_type: str
    bit_rate: Optional[int] = None
    metadata: Dict[str, JSONSerializable] = field(default_factory=dict)


@dataclass
class Audio:
    """Audio data and metadata."""
    
    id: AudioId
    data: bytes
    metadata: AudioMetadata
    tags: List[str] = field(default_factory=list)
    description: Optional[str] = None


@dataclass
class TranscriptionResult:
    """Result of audio transcription."""
    
    audio_id: AudioId
    text: str
    confidence: float
    language: str
    segments: List[Dict[str, Any]]
    speakers: Optional[List[str]] = None
    metadata: Dict[str, JSONSerializable] = field(default_factory=dict)


@dataclass
class AudioAnalysisResult:
    """Result of audio analysis."""
    
    audio_id: AudioId
    description: str
    tags: List[str]
    sentiment: Optional[str] = None
    noise_level: Optional[float] = None
    background_sounds: Optional[List[str]] = None
    metadata: Dict[str, JSONSerializable] = field(default_factory=dict)


class AudioProcessor:
    """Processor for audio."""
    
    def __init__(
        self,
        nlp_service: NLPService,
        logger: Logger,
    ):
        """Initialize the audio processor.
        
        Args:
            nlp_service: NLP service for audio transcription and understanding
            logger: Logger instance
        """
        self._nlp_service = nlp_service
        self._logger = logger
        self._lock = ReaderWriterLock()
        
    async def load_audio(
        self,
        path: Union[str, Path],
    ) -> Audio:
        """Load an audio file.
        
        Args:
            path: Path to the audio file
            
        Returns:
            Loaded audio
        """
        try:
            # Import libraries only when needed
            import librosa
            import soundfile as sf
            
            # Load the audio
            y, sr = librosa.load(path, sr=None)
            
            # Get audio metadata
            duration = librosa.get_duration(y=y, sr=sr)
            format_str = os.path.splitext(path)[1][1:].lower()
            audio_format = AudioFormat(format_str) if format_str in [f.value for f in AudioFormat] else AudioFormat.OTHER
            channels = 1 if y.ndim == 1 else y.shape[1]
            
            # Get file size
            file_size = os.path.getsize(path)
            
            # Get MIME type
            mime_type = f"audio/{format_str}"
            
            # Read the file as bytes
            with open(path, "rb") as f:
                audio_bytes = f.read()
            
            # Create metadata
            metadata = AudioMetadata(
                duration_seconds=duration,
                format=audio_format,
                sample_rate=sr,
                channels=channels,
                creation_utc=datetime.now(timezone.utc),
                size_bytes=file_size,
                mime_type=mime_type,
            )
            
            # Create audio
            audio = Audio(
                id=AudioId(generate_id()),
                data=audio_bytes,
                metadata=metadata,
            )
            
            self._logger.info(f"Loaded audio: {path} ({duration:.2f}s, {format_str}, {sr}Hz, {channels} channels, {file_size} bytes)")
            
            return audio
            
        except Exception as e:
            self._logger.error(f"Error loading audio: {e}")
            raise
            
    async def load_audio_from_bytes(
        self,
        data: bytes,
        format: Optional[str] = None,
    ) -> Audio:
        """Load audio from bytes.
        
        Args:
            data: Audio data
            format: Audio format (if known)
            
        Returns:
            Loaded audio
        """
        try:
            # Import libraries only when needed
            import librosa
            import soundfile as sf
            import tempfile
            
            # Create a temporary file
            with tempfile.NamedTemporaryFile(suffix=f".{format}" if format else ".wav", delete=False) as temp_file:
                temp_file.write(data)
                temp_path = temp_file.name
                
            try:
                # Load the audio
                y, sr = librosa.load(temp_path, sr=None)
                
                # Get audio metadata
                duration = librosa.get_duration(y=y, sr=sr)
                format_str = format or os.path.splitext(temp_path)[1][1:].lower()
                audio_format = AudioFormat(format_str) if format_str in [f.value for f in AudioFormat] else AudioFormat.OTHER
                channels = 1 if y.ndim == 1 else y.shape[1]
                
                # Get file size
                file_size = len(data)
                
                # Get MIME type
                mime_type = f"audio/{format_str}"
                
                # Create metadata
                metadata = AudioMetadata(
                    duration_seconds=duration,
                    format=audio_format,
                    sample_rate=sr,
                    channels=channels,
                    creation_utc=datetime.now(timezone.utc),
                    size_bytes=file_size,
                    mime_type=mime_type,
                )
                
                # Create audio
                audio = Audio(
                    id=AudioId(generate_id()),
                    data=data,
                    metadata=metadata,
                )
                
                self._logger.info(f"Loaded audio from bytes: {duration:.2f}s, {format_str}, {sr}Hz, {channels} channels, {file_size} bytes")
                
                return audio
                
            finally:
                # Remove the temporary file
                os.unlink(temp_path)
                
        except Exception as e:
            self._logger.error(f"Error loading audio from bytes: {e}")
            raise
            
    async def save_audio(
        self,
        audio: Audio,
        path: Union[str, Path],
    ) -> None:
        """Save audio to a file.
        
        Args:
            audio: Audio to save
            path: Path to save the audio to
        """
        try:
            # Save the audio
            with open(path, "wb") as f:
                f.write(audio.data)
                
            self._logger.info(f"Saved audio: {path}")
            
        except Exception as e:
            self._logger.error(f"Error saving audio: {e}")
            raise
            
    async def transcribe_audio(
        self,
        audio: Audio,
    ) -> TranscriptionResult:
        """Transcribe audio.
        
        Args:
            audio: Audio to transcribe
            
        Returns:
            Transcription result
        """
        try:
            # Convert audio to base64
            base64_audio = base64.b64encode(audio.data).decode("utf-8")
            
            # Create a prompt for audio transcription
            prompt = self._create_transcription_prompt(base64_audio, audio.metadata)
            
            # Generate transcription
            generator = await self._nlp_service.get_generator()
            generation_result = await generator.generate(prompt)
            
            # Parse the transcription
            transcription = self._parse_transcription(audio.id, generation_result.text)
            
            self._logger.info(f"Transcribed audio: {audio.id}")
            
            return transcription
            
        except Exception as e:
            self._logger.error(f"Error transcribing audio: {e}")
            raise
            
    async def analyze_audio(
        self,
        audio: Audio,
        transcription: Optional[TranscriptionResult] = None,
    ) -> AudioAnalysisResult:
        """Analyze audio.
        
        Args:
            audio: Audio to analyze
            transcription: Transcription result (if available)
            
        Returns:
            Analysis result
        """
        try:
            # Convert audio to base64
            base64_audio = base64.b64encode(audio.data).decode("utf-8")
            
            # Create a prompt for audio analysis
            prompt = self._create_audio_analysis_prompt(base64_audio, audio.metadata, transcription)
            
            # Generate audio analysis
            generator = await self._nlp_service.get_generator()
            generation_result = await generator.generate(prompt)
            
            # Parse the analysis
            analysis = self._parse_audio_analysis(audio.id, generation_result.text)
            
            self._logger.info(f"Analyzed audio: {audio.id}")
            
            return analysis
            
        except Exception as e:
            self._logger.error(f"Error analyzing audio: {e}")
            raise
            
    def _create_transcription_prompt(
        self,
        base64_audio: str,
        metadata: AudioMetadata,
    ) -> str:
        """Create a prompt for audio transcription.
        
        Args:
            base64_audio: Base64-encoded audio
            metadata: Audio metadata
            
        Returns:
            Prompt for audio transcription
        """
        prompt = """You are an AI assistant tasked with transcribing audio.
I will provide you with a base64-encoded audio file and its metadata. Your task is to transcribe the audio and provide:
1. The full text of the transcription
2. The confidence level of the transcription (0.0 to 1.0)
3. The detected language
4. Segments with timestamps
5. Speaker identification (if multiple speakers are detected)

Format your response as follows:
TRANSCRIPTION:
[Full text of the transcription]

CONFIDENCE:
[Confidence level as a decimal between 0.0 and 1.0]

LANGUAGE:
[Detected language code, e.g., "en-US"]

SEGMENTS:
- [00:00:00 - 00:00:05] [Speaker 1]: [Text]
- [00:00:06 - 00:00:10] [Speaker 2]: [Text]
...

SPEAKERS:
- Speaker 1: [Description, e.g., "Male, adult"]
- Speaker 2: [Description, e.g., "Female, adult"]
...

Here is the audio (base64-encoded):
"""
        
        prompt += f"\n{base64_audio}\n\nAudio metadata:\n"
        prompt += f"Duration: {metadata.duration_seconds:.2f} seconds\n"
        prompt += f"Format: {metadata.format.value}\n"
        prompt += f"Sample rate: {metadata.sample_rate} Hz\n"
        prompt += f"Channels: {metadata.channels}\n"
        
        return prompt
        
    def _parse_transcription(
        self,
        audio_id: AudioId,
        transcription_text: str,
    ) -> TranscriptionResult:
        """Parse transcription from transcription text.
        
        Args:
            audio_id: Audio ID
            transcription_text: Transcription text
            
        Returns:
            Transcription result
        """
        # Extract sections
        text = ""
        confidence = 0.0
        language = "en-US"
        segments = []
        speakers = []
        
        # Extract transcription
        if "TRANSCRIPTION:" in transcription_text:
            transcription_section = transcription_text.split("TRANSCRIPTION:", 1)[1].split("CONFIDENCE:", 1)[0].strip()
            text = transcription_section
            
        # Extract confidence
        if "CONFIDENCE:" in transcription_text:
            confidence_section = transcription_text.split("CONFIDENCE:", 1)[1].split("LANGUAGE:", 1)[0].strip()
            try:
                confidence = float(confidence_section)
            except ValueError:
                confidence = 0.0
                
        # Extract language
        if "LANGUAGE:" in transcription_text:
            language_section = transcription_text.split("LANGUAGE:", 1)[1].split("SEGMENTS:", 1)[0].strip()
            language = language_section
            
        # Extract segments
        if "SEGMENTS:" in transcription_text:
            segments_section = transcription_text.split("SEGMENTS:", 1)[1]
            if "SPEAKERS:" in segments_section:
                segments_section = segments_section.split("SPEAKERS:", 1)[0]
            segments_section = segments_section.strip()
            
            segment_lines = segments_section.split("\n")
            for line in segment_lines:
                if line.strip().startswith("-"):
                    segment_text = line.strip()[1:].strip()
                    if segment_text:
                        # Parse segment
                        try:
                            time_range, rest = segment_text.split("]", 1)
                            time_range = time_range.strip()[1:].strip()
                            start_time, end_time = time_range.split("-")
                            start_time = start_time.strip()
                            end_time = end_time.strip()
                            
                            speaker = None
                            if "[" in rest and "]" in rest:
                                speaker_part = rest.split("]", 1)[0].strip()[1:].strip()
                                if speaker_part:
                                    speaker = speaker_part
                                    
                            text_part = rest.split("]", 1)[1].strip() if "]" in rest else rest.strip()
                            
                            segment = {
                                "start_time": start_time,
                                "end_time": end_time,
                                "speaker": speaker,
                                "text": text_part,
                            }
                            
                            segments.append(segment)
                        except Exception:
                            # Skip malformed segments
                            pass
                            
        # Extract speakers
        if "SPEAKERS:" in transcription_text:
            speakers_section = transcription_text.split("SPEAKERS:", 1)[1].strip()
            
            speaker_lines = speakers_section.split("\n")
            for line in speaker_lines:
                if line.strip().startswith("-"):
                    speaker_text = line.strip()[1:].strip()
                    if speaker_text:
                        speakers.append(speaker_text)
                        
        return TranscriptionResult(
            audio_id=audio_id,
            text=text,
            confidence=confidence,
            language=language,
            segments=segments,
            speakers=speakers if speakers else None,
        )
        
    def _create_audio_analysis_prompt(
        self,
        base64_audio: str,
        metadata: AudioMetadata,
        transcription: Optional[TranscriptionResult] = None,
    ) -> str:
        """Create a prompt for audio analysis.
        
        Args:
            base64_audio: Base64-encoded audio
            metadata: Audio metadata
            transcription: Transcription result (if available)
            
        Returns:
            Prompt for audio analysis
        """
        prompt = """You are an AI assistant tasked with analyzing audio.
I will provide you with a base64-encoded audio file and its metadata. Your task is to analyze the audio and provide:
1. A detailed description of the audio
2. Tags that describe the audio
3. The overall sentiment of the audio
4. The noise level (0.0 to 1.0)
5. Background sounds detected

Format your response as follows:
DESCRIPTION:
[Detailed description of the audio]

TAGS:
- [Tag 1]
- [Tag 2]
...

SENTIMENT:
[Overall sentiment of the audio]

NOISE_LEVEL:
[Noise level as a decimal between 0.0 and 1.0]

BACKGROUND_SOUNDS:
- [Sound 1]
- [Sound 2]
...

Here is the audio (base64-encoded):
"""
        
        prompt += f"\n{base64_audio}\n\nAudio metadata:\n"
        prompt += f"Duration: {metadata.duration_seconds:.2f} seconds\n"
        prompt += f"Format: {metadata.format.value}\n"
        prompt += f"Sample rate: {metadata.sample_rate} Hz\n"
        prompt += f"Channels: {metadata.channels}\n"
        
        if transcription:
            prompt += f"\nTranscription:\n{transcription.text}\n"
            
        return prompt
        
    def _parse_audio_analysis(
        self,
        audio_id: AudioId,
        analysis_text: str,
    ) -> AudioAnalysisResult:
        """Parse audio analysis from analysis text.
        
        Args:
            audio_id: Audio ID
            analysis_text: Analysis text
            
        Returns:
            Audio analysis result
        """
        # Extract sections
        description = ""
        tags = []
        sentiment = None
        noise_level = None
        background_sounds = []
        
        # Extract description
        if "DESCRIPTION:" in analysis_text:
            description_section = analysis_text.split("DESCRIPTION:", 1)[1].split("TAGS:", 1)[0].strip()
            description = description_section
            
        # Extract tags
        if "TAGS:" in analysis_text:
            tags_section = analysis_text.split("TAGS:", 1)[1].split("SENTIMENT:", 1)[0].strip()
            tag_lines = tags_section.split("\n")
            for line in tag_lines:
                if line.strip().startswith("-"):
                    tag = line.strip()[1:].strip()
                    if tag:
                        tags.append(tag)
                        
        # Extract sentiment
        if "SENTIMENT:" in analysis_text:
            sentiment_section = analysis_text.split("SENTIMENT:", 1)[1].split("NOISE_LEVEL:", 1)[0].strip()
            sentiment = sentiment_section
            
        # Extract noise level
        if "NOISE_LEVEL:" in analysis_text:
            noise_level_section = analysis_text.split("NOISE_LEVEL:", 1)[1].split("BACKGROUND_SOUNDS:", 1)[0].strip()
            try:
                noise_level = float(noise_level_section)
            except ValueError:
                noise_level = None
                
        # Extract background sounds
        if "BACKGROUND_SOUNDS:" in analysis_text:
            sounds_section = analysis_text.split("BACKGROUND_SOUNDS:", 1)[1].strip()
            sound_lines = sounds_section.split("\n")
            for line in sound_lines:
                if line.strip().startswith("-"):
                    sound = line.strip()[1:].strip()
                    if sound:
                        background_sounds.append(sound)
                        
        return AudioAnalysisResult(
            audio_id=audio_id,
            description=description,
            tags=tags,
            sentiment=sentiment,
            noise_level=noise_level,
            background_sounds=background_sounds if background_sounds else None,
        )
