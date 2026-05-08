# -*- coding: utf-8 -*-
"""Video parser module."""

import json
import os
import subprocess
from pathlib import Path

import imageio_ffmpeg

from .models import VideoMetadata
from .exceptions import UnsupportedFormatError, CorruptedFileError

_FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()


def _probe_with_ffmpeg(file_path: str) -> dict:
    """Use ffmpeg to get video metadata (since ffprobe may not be available)."""
    cmd = [
        _FFMPEG_EXE,
        '-v', 'quiet',
        '-print_format', 'json',
        '-show_format',
        '-show_streams',
        '-i', file_path,
    ]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30
        )
    except FileNotFoundError:
        raise CorruptedFileError(file_path, "ffmpeg not found")
    except subprocess.TimeoutExpired:
        raise CorruptedFileError(file_path, "ffmpeg timeout")

    # ffmpeg puts probe info on stderr when using -show_format/-show_streams
    # but that only works with ffprobe. Use a different approach:
    # Run ffmpeg -i and parse the output
    cmd2 = [_FFMPEG_EXE, '-i', file_path, '-f', 'null', '-']
    try:
        result2 = subprocess.run(
            cmd2, capture_output=True, text=True, timeout=30
        )
    except Exception as e:
        raise CorruptedFileError(file_path, str(e))

    stderr = result2.stderr
    if not stderr:
        raise CorruptedFileError(file_path, "No output from ffmpeg")

    return _parse_ffmpeg_output(stderr, file_path)


def _parse_ffmpeg_output(stderr: str, file_path: str) -> dict:
    """Parse ffmpeg -i output to extract metadata."""
    import re

    info = {
        'duration': 0.0,
        'fps': 0.0,
        'width': 0,
        'height': 0,
        'codec': 'unknown',
    }

    # Duration: 00:01:30.50
    dur_match = re.search(r'Duration:\s*(\d+):(\d+):(\d+)\.(\d+)', stderr)
    if dur_match:
        h, m, s, cs = dur_match.groups()
        info['duration'] = int(h) * 3600 + int(m) * 60 + int(s) + int(cs) / 100.0

    # Video stream: Stream #0:0...: Video: h264 ..., 1920x1080 ..., 30 fps
    video_match = re.search(
        r'Stream\s+#\d+:\d+.*?Video:\s*(\w+).*?,\s*(\d+)x(\d+)', stderr
    )
    if video_match:
        info['codec'] = video_match.group(1)
        info['width'] = int(video_match.group(2))
        info['height'] = int(video_match.group(3))

    # fps: "30 fps" or "29.97 fps" or "30 tbr"
    fps_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:fps|tbr)', stderr)
    if fps_match:
        info['fps'] = float(fps_match.group(1))

    return info


class VideoParser:
    """Video file parser."""

    SUPPORTED_FORMATS = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv']

    def is_supported_format(self, file_path: str) -> bool:
        ext = Path(file_path).suffix.lower()
        return ext in self.SUPPORTED_FORMATS

    def parse(self, file_path: str) -> VideoMetadata:
        """Parse video file and return metadata."""
        # Normalize path
        file_path = str(Path(file_path).resolve())

        if not self.is_supported_format(file_path):
            ext = Path(file_path).suffix
            raise UnsupportedFormatError(ext)

        if not os.path.exists(file_path):
            raise CorruptedFileError(file_path, "file not found")

        try:
            info = _probe_with_ffmpeg(file_path)
        except CorruptedFileError:
            raise
        except Exception as e:
            raise CorruptedFileError(file_path, str(e))

        duration = info['duration']
        fps = info['fps']
        total_frames = int(duration * fps) if fps > 0 else 0

        return VideoMetadata(
            file_path=file_path,
            duration=duration,
            fps=fps,
            width=info['width'],
            height=info['height'],
            codec=info['codec'],
            total_frames=total_frames,
        )
