"""自定义异常类"""


class VideoFrameCaptureError(Exception):
    """基础异常类"""
    pass


class VideoParseError(VideoFrameCaptureError):
    """视频解析错误"""
    pass


class UnsupportedFormatError(VideoParseError):
    """不支持的格式"""
    def __init__(self, extension: str):
        self.extension = extension
        self.supported = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv']
        super().__init__(f"不支持的格式: {extension}。支持的格式: {', '.join(self.supported)}")


class CorruptedFileError(VideoParseError):
    """文件损坏"""
    def __init__(self, file_path: str, reason: str = ""):
        self.file_path = file_path
        message = f"文件损坏或无法读取: {file_path}"
        if reason:
            message += f" ({reason})"
        super().__init__(message)


class TimestampError(VideoFrameCaptureError):
    """时间戳相关错误"""
    pass


class TimestampOutOfRangeError(TimestampError):
    """时间戳超出范围"""
    def __init__(self, timestamp: float, duration: float):
        self.timestamp = timestamp
        self.duration = duration
        super().__init__(f"时间戳 {timestamp:.3f}s 超出视频时长范围 [0, {duration:.3f}s]")


class TimestampFormatError(TimestampError):
    """时间戳格式无效"""
    def __init__(self, timestamp_str: str):
        self.timestamp_str = timestamp_str
        super().__init__(f"时间戳格式无效: {timestamp_str}。支持格式: HH:MM:SS, HH:MM:SS.mmm, 秒数")


class IntervalError(VideoFrameCaptureError):
    """间隔参数错误"""
    def __init__(self, interval: float, min_interval: float = 0.1):
        self.interval = interval
        self.min_interval = min_interval
        super().__init__(f"间隔 {interval}s 小于最小值 {min_interval}s")


class ImageWriteError(VideoFrameCaptureError):
    """图片写入错误"""
    def __init__(self, file_path: str, reason: str = ""):
        self.file_path = file_path
        message = f"图片写入失败: {file_path}"
        if reason:
            message += f" ({reason})"
        super().__init__(message)


class FrameExtractionError(VideoFrameCaptureError):
    """帧提取错误"""
    def __init__(self, timestamp: float, reason: str = ""):
        self.timestamp = timestamp
        message = f"帧提取失败: 时间戳 {timestamp:.3f}s"
        if reason:
            message += f" ({reason})"
        super().__init__(message)
