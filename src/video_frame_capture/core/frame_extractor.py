# -*- coding: utf-8 -*-
"""Frame extractor module."""

import subprocess
from pathlib import Path

import imageio_ffmpeg
import numpy as np

from .exceptions import FrameExtractionError
from .video_parser import VideoParser

_FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()


class FrameExtractor:
    """Extract frames from video at specified timestamps."""

    def __init__(self, video_path: str):
        self.video_path = str(Path(video_path).resolve())
        # Get video dimensions
        parser = VideoParser()
        metadata = parser.parse(self.video_path)
        self._width = metadata.width
        self._height = metadata.height

    def extract_frame_at(self, timestamp: float) -> np.ndarray:
        """Extract frame at timestamp, return RGB numpy array [h, w, 3]."""
        cmd = [
            _FFMPEG_EXE,
            '-ss', str(timestamp),
            '-i', self.video_path,
            '-vframes', '1',
            '-f', 'rawvideo',
            '-pix_fmt', 'rgb24',
            '-v', 'quiet',
            'pipe:1',
        ]

        try:
            result = subprocess.run(
                cmd, capture_output=True, timeout=30
            )

            if result.returncode != 0:
                stderr = result.stderr.decode(errors='replace')
                raise FrameExtractionError(timestamp, f"ffmpeg error: {stderr}")

            expected_size = self._width * self._height * 3
            if len(result.stdout) < expected_size:
                raise FrameExtractionError(
                    timestamp,
                    f"Incomplete frame data: got {len(result.stdout)}, expected {expected_size}"
                )

            frame = np.frombuffer(
                result.stdout[:expected_size], dtype=np.uint8
            ).reshape([self._height, self._width, 3])

            return frame

        except FrameExtractionError:
            raise
        except Exception as e:
            raise FrameExtractionError(timestamp, str(e))

    def extract_frames_at(self, timestamps: list[float]) -> list[np.ndarray]:
        """Extract frames at multiple timestamps."""
        frames = []
        for ts in timestamps:
            frames.append(self.extract_frame_at(ts))
        return frames
