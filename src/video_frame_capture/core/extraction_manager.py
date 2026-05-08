"""提取管理器"""

from typing import Callable, Optional
from pathlib import Path

from .models import ExtractionTask, ExtractionResult, ImageWriteConfig
from .frame_selector import FrameSelector
from .frame_extractor import FrameExtractor
from .image_writer import ImageWriter
from .exceptions import FrameExtractionError


class ExtractionManager:
    """提取管理器 - 协调帧选择、提取和保存的完整流程"""
    
    def __init__(self):
        self.frame_selector = FrameSelector()
        self.image_writer = ImageWriter()
    
    def execute(
        self,
        task: ExtractionTask,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> ExtractionResult:
        """执行提取任务
        
        Args:
            task: 提取任务
            progress_callback: 进度回调函数，参数为 (current, total)
            
        Returns:
            ExtractionResult: 提取结果
        """
        video_path = task.video_path
        timestamps = task.timestamps
        config = task.config
        
        # 获取视频名称
        video_name = Path(video_path).stem
        
        # 确定输出目录
        output_dir = config.output_dir
        if not output_dir:
            output_dir = str(Path(video_path).parent)
        
        # 创建配置副本，设置输出目录
        config = ImageWriteConfig(
            format=config.format,
            quality=config.quality,
            output_dir=output_dir,
            naming_template=config.naming_template,
            scale=config.scale
        )
        
        # 创建帧提取器
        extractor = FrameExtractor(video_path)
        
        # 执行提取
        saved_paths = []
        failed_timestamps = []
        total_count = len(timestamps)
        
        for i, timestamp in enumerate(timestamps):
            try:
                # 提取帧
                frame = extractor.extract_frame_at(timestamp)
                
                # 保存图片
                saved_path = self.image_writer.write(
                    frame=frame,
                    config=config,
                    video_name=video_name,
                    timestamp=timestamp,
                    index=i + 1
                )
                
                saved_paths.append(saved_path)
                
            except (FrameExtractionError, Exception) as e:
                failed_timestamps.append(timestamp)
            
            # 进度回调
            if progress_callback:
                progress_callback(i + 1, total_count)
        
        return ExtractionResult(
            saved_paths=saved_paths,
            failed_timestamps=failed_timestamps,
            total_count=total_count,
            success_count=len(saved_paths)
        )
