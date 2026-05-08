"""图片写入器"""

import os
from pathlib import Path
from typing import Optional

import numpy as np
from PIL import Image

from .models import ImageWriteConfig, ImageFormat
from .exceptions import ImageWriteError


class ImageWriter:
    """图片写入器 - 将帧数据编码为指定格式并保存"""
    
    DEFAULT_FORMAT = ImageFormat.PNG
    DEFAULT_QUALITY = 85
    
    def generate_filename(
        self,
        video_name: str,
        timestamp: float,
        index: int,
        extension: str,
        output_dir: str,
        template: str = "{video_name}_{timestamp}"
    ) -> str:
        """生成文件名
        
        Args:
            video_name: 视频文件名（不含扩展名）
            timestamp: 时间戳（秒）
            index: 序号（从1开始）
            extension: 文件扩展名
            output_dir: 输出目录
            template: 命名模板
            
        Returns:
            str: 完整文件路径
        """
        # 格式化时间戳用于文件名
        hours = int(timestamp // 3600)
        minutes = int((timestamp % 3600) // 60)
        seconds = int(timestamp % 60)
        milliseconds = int((timestamp % 1) * 1000)
        timestamp_str = f"{hours:02d}-{minutes:02d}-{seconds:02d}-{milliseconds:03d}"
        
        # 替换模板变量
        filename = template.replace("{video_name}", video_name)
        filename = filename.replace("{timestamp}", timestamp_str)
        filename = filename.replace("{index}", f"{index:03d}")
        
        # 添加扩展名
        if not filename.endswith(f".{extension}"):
            filename = f"{filename}.{extension}"
        
        return os.path.join(output_dir, filename)
    
    def resolve_conflict(self, file_path: str) -> str:
        """处理文件名冲突，添加数字后缀
        
        Args:
            file_path: 原始文件路径
            
        Returns:
            str: 不冲突的文件路径
        """
        if not os.path.exists(file_path):
            return file_path
        
        base, ext = os.path.splitext(file_path)
        counter = 1
        
        while os.path.exists(f"{base}_{counter}{ext}"):
            counter += 1
        
        return f"{base}_{counter}{ext}"
    
    def write(
        self,
        frame: np.ndarray,
        config: ImageWriteConfig,
        video_name: str,
        timestamp: float,
        index: int = 1
    ) -> str:
        """将帧保存为图片
        
        Args:
            frame: 帧数据（RGB numpy 数组，形状为 [height, width, 3]）
            config: 写入配置
            video_name: 视频文件名（不含扩展名）
            timestamp: 时间戳（秒）
            index: 序号
            
        Returns:
            str: 保存路径
            
        Raises:
            ImageWriteError: 写入失败
        """
        try:
            # 确定扩展名
            extension = config.format.value
            
            # 生成文件名
            file_path = self.generate_filename(
                video_name=video_name,
                timestamp=timestamp,
                index=index,
                extension=extension,
                output_dir=config.output_dir,
                template=config.naming_template
            )
            
            # 处理冲突
            file_path = self.resolve_conflict(file_path)
            
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # 转换为 PIL Image
            image = Image.fromarray(frame)
            
            # 缩放（如果需要）
            if config.scale:
                image = image.resize(config.scale, Image.Resampling.LANCZOS)
            
            # 保存
            save_kwargs = {}
            if config.format == ImageFormat.JPEG:
                save_kwargs['quality'] = config.quality
            
            image.save(file_path, **save_kwargs)
            
            return file_path
            
        except Exception as e:
            raise ImageWriteError(
                file_path if 'file_path' in locals() else "unknown",
                str(e)
            )
