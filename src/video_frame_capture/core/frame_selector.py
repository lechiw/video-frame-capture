"""帧选择器"""

import re
from typing import Optional

from .exceptions import TimestampFormatError, TimestampOutOfRangeError, IntervalError


class FrameSelector:
    """帧选择器 - 根据用户参数计算需要提取的时间戳列表"""
    
    # 时间戳格式正则表达式
    TIMESTAMP_PATTERN_HMS = re.compile(r'^(\d+):(\d{2}):(\d{2})(?:\.(\d{1,3}))?$')
    TIMESTAMP_PATTERN_SECONDS = re.compile(r'^(\d+(?:\.\d+)?)$')
    
    MIN_INTERVAL = 0.1  # 最小间隔（秒）
    
    def parse_timestamp(self, timestamp_str: str) -> float:
        """解析时间戳字符串为秒数
        
        支持格式：
        - HH:MM:SS
        - HH:MM:SS.mmm
        - 秒数（支持小数）
        
        Args:
            timestamp_str: 时间戳字符串
            
        Returns:
            float: 秒数
            
        Raises:
            TimestampFormatError: 时间戳格式无效
        """
        timestamp_str = timestamp_str.strip()
        
        # 尝试匹配 HH:MM:SS[.mmm] 格式
        match = self.TIMESTAMP_PATTERN_HMS.match(timestamp_str)
        if match:
            hours = int(match.group(1))
            minutes = int(match.group(2))
            seconds = int(match.group(3))
            milliseconds = int(match.group(4)) if match.group(4) else 0
            
            return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0
        
        # 尝试匹配纯秒数格式
        match = self.TIMESTAMP_PATTERN_SECONDS.match(timestamp_str)
        if match:
            return float(match.group(1))
        
        raise TimestampFormatError(timestamp_str)
    
    def format_timestamp(self, timestamp: float) -> str:
        """将浮点秒数格式化为 HH:MM:SS.mmm 字符串
        
        Args:
            timestamp: 秒数
            
        Returns:
            str: 格式化的时间戳字符串
        """
        if timestamp < 0:
            timestamp = 0
        
        hours = int(timestamp // 3600)
        minutes = int((timestamp % 3600) // 60)
        seconds = int(timestamp % 60)
        milliseconds = int((timestamp % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
    
    def validate_timestamp(self, timestamp: float, duration: float) -> bool:
        """验证时间戳是否在视频时长范围内
        
        Args:
            timestamp: 时间戳（秒）
            duration: 视频时长（秒）
            
        Returns:
            bool: 是否有效
        """
        return 0 <= timestamp <= duration
    
    def validate_timestamp_or_raise(self, timestamp: float, duration: float) -> None:
        """验证时间戳，无效时抛出异常
        
        Args:
            timestamp: 时间戳（秒）
            duration: 视频时长（秒）
            
        Raises:
            TimestampOutOfRangeError: 时间戳超出范围
        """
        if not self.validate_timestamp(timestamp, duration):
            raise TimestampOutOfRangeError(timestamp, duration)
    
    def select_by_interval(
        self,
        duration: float,
        interval: float,
        start_time: float = 0.0,
        end_time: Optional[float] = None
    ) -> list[float]:
        """按时间间隔生成时间戳列表
        
        Args:
            duration: 视频时长（秒）
            interval: 时间间隔（秒）
            start_time: 起始时间（秒）
            end_time: 结束时间（秒），None 表示视频结尾
            
        Returns:
            list[float]: 时间戳列表
            
        Raises:
            IntervalError: 间隔小于最小值
            TimestampOutOfRangeError: 时间范围无效
        """
        if interval < self.MIN_INTERVAL:
            raise IntervalError(interval, self.MIN_INTERVAL)
        
        if end_time is None:
            end_time = duration
        
        # 验证范围
        if start_time < 0:
            start_time = 0
        if end_time > duration:
            end_time = duration
        if start_time >= end_time:
            return []
        
        timestamps = []
        current = start_time
        
        while current <= end_time:
            timestamps.append(round(current, 3))
            current += interval
        
        return timestamps
