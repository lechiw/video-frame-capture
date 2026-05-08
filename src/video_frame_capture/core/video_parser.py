# -*- coding: utf-8 -*-
"""Video parser module - extracts metadata from video files."""

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Optional

import imageio_ffmpeg

from .models import VideoMetadata
from .exceptions import UnsupportedFormatError, CorruptedFileError

# Lazy-init ffmpeg binary path
_FFMPEG_EXE: Optional[str] = None
_FFPROBE_EXE: Optional[str] = None


def _get_ffmpeg_exe() -> str:
    """获取 ffmpeg 路径（惰性初始化）"""
    global _FFMPEG_EXE
    if _FFMPEG_EXE is None:
        _FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
    return _FFMPEG_EXE


def _get_ffprobe_exe() -> Optional[str]:
    """获取 ffprobe 路径（可能不存在，惰性查找）"""
    global _FFPROBE_EXE
    if _FFPROBE_EXE is not None:
        return _FFPROBE_EXE

    ffmpeg_path = Path(_get_ffmpeg_exe())
    # ffprobe 通常与 ffmpeg 同目录
    candidates = [
        ffmpeg_path.parent / "ffprobe",
        ffmpeg_path.parent / "ffprobe.exe",
    ]
    for c in candidates:
        if c.exists():
            _FFPROBE_EXE = str(c)
            return _FFPROBE_EXE

    # fallback: 在 PATH 中查找
    for name in ["ffprobe", "ffprobe.exe"]:
        try:
            r = subprocess.run([name, "-version"], capture_output=True, timeout=5)
            if r.returncode == 0:
                _FFPROBE_EXE = name
                return name
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue

    _FFPROBE_EXE = ""
    return None


def _probe_with_ffprobe(file_path: str) -> dict:
    """用 ffprobe 解析视频元信息（JSON JSON，最稳定）"""
    ffprobe = _get_ffprobe_exe()
    if not ffprobe:
        raise FileNotFoundError("ffprobe not found")

    cmd = [
        ffprobe, "-v", "quiet", "-print_format", "json",
        "-show_streams", "-show_format", file_path,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=True)
        data = json.loads(result.stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError, subprocess.TimeoutExpired) as e:
        raise CorruptedFileError(file_path, f"ffprobe failed: {e}")

    video_stream = None
    for stream in data.get("streams", []):
        if stream.get("codec_type") == "video":
            video_stream = stream
            break

    if not video_stream:
        raise CorruptedFileError(file_path, "no video stream found")

    width = int(video_stream.get("width", 0))
    height = int(video_stream.get("height", 0))
    duration = float(data.get("format", {}).get("duration", 0) or video_stream.get("duration", 0))
    fps_str = video_stream.get("avg_frame_rate", "0/1")
    if "/" in fps_str:
        num, den = fps_str.split("/")
        fps = float(num) / float(den) if float(den) > 0 else 30.0
    else:
        fps = float(fps_str) or 30.0
    total_frames = int(video_stream.get("nb_frames", 0)) or max(1, int(duration * fps))
    codec = video_stream.get("codec_name", "unknown")

    return {
        "duration": duration,
        "fps": fps,
        "width": width,
        "height": height,
        "codec": codec,
        "total_frames": total_frames,
    }


def _probe_with_ffmpeg(file_path: str) -> dict:
    """Fallback: 解析 ffmpeg -i 的 stderr 输出获取元信息"""
    cmd = [_get_ffmpeg_exe(), "-i", file_path, "-f", "null", "-"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        stderr = result.stderr
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        raise CorruptedFileError(file_path, str(e))

    if not stderr:
        raise CorruptedFileError(file_path, "no output from ffmpeg")

    info = {"duration": 0.0, "fps": 0.0, "width": 0, "height": 0, "codec": "unknown"}

    dur_match = re.search(r"Duration:\s*(\d+):(\d+):(\d+)\.(\d+)", stderr)
    if dur_match:
        h, m, s, cs = dur_match.groups()
        info["duration"] = int(h) * 3600 + int(m) * 60 + int(s) + int(cs) / 100.0

    video_match = re.search(r"Stream\s+#\d+:\d+.*?Video:\s*(\w+).*?,\s*(\d+)x(\d+)", stderr)
    if video_match:
        info["codec"] = video_match.group(1)
        info["width"] = int(video_match.group(2))
        info["height"] = int(video_match.group(3))

    fps_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:fps|tbr)", stderr)
    if fps_match:
        info["fps"] = float(fps_match.group(1))

    return info


class VideoParser:
    """Video file parser."""

    SUPPORTED_FORMATS = [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"]

    def is_supported_format(self, file_path: str) -> bool:
        ext = Path(file_path).suffix.lower()
        return ext in self.SUPPORTED_FORMATS

    def parse(self, file_path: str) -> VideoMetadata:
        """解析视频文件，返回元数据"""
        file_path = str(Path(file_path).resolve())

        if not self.is_supported_format(file_path):
            raise UnsupportedFormatError(Path(file_path).suffix)

        if not os.path.exists(file_path):
            raise CorruptedFileError(file_path, "file not found")

        # 优先 ffprobe（稳定 JSON），fallback ffmpeg stderr
        try:
            info = _probe_with_ffprobe(file_path)
        except (FileNotFoundError, CorruptedFileError, Exception):
            try:
                info = _probe_with_ffmpeg(file_path)
            except Exception as e:
                raise CorruptedFileError(file_path, str(e))

        return VideoMetadata(
            file_path=file_path,
            duration=info["duration"],
            fps=info["fps"] or 30.0,
            width=info["width"],
            height=info["height"],
            codec=info["codec"],
            total_frames=int(info.get("total_frames", info["duration"] * (info["fps"] or 30))),
        )
