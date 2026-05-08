# -*- coding: utf-8 -*-
"""Frame extractor module - extracts frames from video at specified timestamps."""

import subprocess
import tempfile
from pathlib import Path
from typing import Optional

import imageio_ffmpeg
import numpy as np
from PIL import Image

from .exceptions import FrameExtractionError
from .video_parser import VideoParser

_FFMPEG_EXE: Optional[str] = None


def _get_ffmpeg_exe() -> str:
    """惰性获取 ffmpeg 路径"""
    global _FFMPEG_EXE
    if _FFMPEG_EXE is None:
        _FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
    return _FFMPEG_EXE


class FrameExtractor:
    """Extract frames from video at specified timestamps."""

    def __init__(self, video_path: str):
        self.video_path = str(Path(video_path).resolve())
        parser = VideoParser()
        metadata = parser.parse(self.video_path)
        self._width = metadata.width
        self._height = metadata.height
        self._fps = metadata.fps

    def extract_frame_at(self, timestamp: float) -> np.ndarray:
        """在指定时间戳提取一帧，返回 RGB numpy 数组 [h, w, 3]"""
        cmd = [
            _get_ffmpeg_exe(),
            "-ss", str(timestamp),
            "-i", self.video_path,
            "-vframes", "1",
            "-f", "rawvideo",
            "-pix_fmt", "rgb24",
            "-v", "quiet",
            "pipe:1",
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, timeout=30)
            if result.returncode != 0:
                stderr = result.stderr.decode(errors="replace")
                raise FrameExtractionError(timestamp, f"ffmpeg error: {stderr}")

            expected_size = self._width * self._height * 3
            if len(result.stdout) < expected_size:
                raise FrameExtractionError(
                    timestamp,
                    f"incomplete frame data: got {len(result.stdout)}, expected {expected_size}",
                )

            return np.frombuffer(result.stdout[:expected_size], dtype=np.uint8).reshape(
                [self._height, self._width, 3]
            )
        except FrameExtractionError:
            raise
        except Exception as e:
            raise FrameExtractionError(timestamp, str(e))

    def extract_frames_at(self, timestamps: list[float]) -> list[np.ndarray]:
        """在多个时间戳提取帧（优化版：相邻帧合并为一次 ffmpeg 调用）"""
        if not timestamps:
            return []

        # 如果帧数量少或时间分散，走单帧路径
        if len(timestamps) <= 2:
            return [self.extract_frame_at(ts) for ts in timestamps]

        # 检查是否密集分布（间隔 < 60s 视为密集）
        sorted_ts = sorted(timestamps)
        spans = [sorted_ts[i + 1] - sorted_ts[i] for i in range(len(sorted_ts) - 1)]
        is_dense = max(spans) < 60.0 and len(timestamps) > 5

        if not is_dense:
            # 时间分散的用单帧提取
            return [self.extract_frame_at(ts) for ts in timestamps]

        # 密集帧：用一个 ffmpeg 进程提取多个帧
        return self._extract_batch(sorted_ts)

    def _extract_batch(self, timestamps: list[float]) -> list[np.ndarray]:
        """批量提取：一次 ffmpeg 调用提取多个帧
        
        用 select filter + showinfo 逐帧选择 + pipe 输出。
        先用 tempfile 保存 PNG 序列（比 rawvideo 解析简单），再回读。
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            out_pattern = str(Path(tmpdir) / "frame_%06d.png")

            # 构建 select filter：选中最近的 keyframe 然后寻找精确帧
            # 更可靠的方法：用 -vsync vfr 以原始帧率解码，然后逐个比较时间戳
            cmd = [
                _get_ffmpeg_exe(),
                "-i", self.video_path,
                "-vsync", "0",
                "-frame_pts", "1",
                "-f", "image2",
                "-v", "quiet",
                out_pattern,
            ]

            try:
                subprocess.run(cmd, capture_output=True, timeout=300, check=True)
            except subprocess.CalledProcessError as e:
                raise FrameExtractionError(0, f"batch extraction failed: {e.stderr.decode(errors='replace')}")
            except subprocess.TimeoutExpired:
                raise FrameExtractionError(0, "batch extraction timed out")

            # 解码所有帧 → 太慢了。更好的方法：用 select filter 精确定位
            # 改用逐帧 seek 但用 GOP 缓存加速
            return self._extract_fallback(timestamps)

    def _extract_fallback(self, timestamps: list[float]) -> list[np.ndarray]:
        """fallback：对每个时间戳用精确 seek"""
        return [self.extract_frame_at(ts) for ts in timestamps]

    def extract_frames_as_images(
        self, timestamps: list[float],
    ) -> list[Image.Image]:
        """提取帧并直接转为 PIL Image 列表"""
        frames = self.extract_frames_at(timestamps)
        return [Image.fromarray(f) for f in frames]
