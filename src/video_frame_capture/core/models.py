"""核心数据模型"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ImageFormat(Enum):
    """输出图片格式"""
    PNG = 'png'
    JPEG = 'jpeg'


class ExtractionMode(Enum):
    """提取模式"""
    SINGLE = 'single'          # 单帧截取
    BATCH_INTERVAL = 'interval'  # 按间隔批量


@dataclass
class VideoMetadata:
    """视频元数据"""
    file_path: str
    duration: float  # 秒
    fps: float
    width: int  # 像素
    height: int  # 像素
    codec: str
    total_frames: int


@dataclass
class ImageWriteConfig:
    """图片写入配置"""
    format: ImageFormat = ImageFormat.PNG
    quality: int = 85  # 1-100，仅 JPEG 有效
    output_dir: str = ''  # 空字符串表示使用视频所在目录
    naming_template: str = '{video_name}_{timestamp}'
    scale: Optional[tuple[int, int]] = None  # (width, height) or None


@dataclass
class ExtractionTask:
    """提取任务"""
    video_path: str
    timestamps: list[float]
    config: ImageWriteConfig


@dataclass
class ExtractionResult:
    """提取结果"""
    saved_paths: list[str]
    failed_timestamps: list[float]
    total_count: int
    success_count: int
