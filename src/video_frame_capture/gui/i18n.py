"""国际化支持"""

from typing import Dict


class I18N:
    """国际化类 - 支持中英文切换"""
    
    _current_lang = 'zh'
    
    TRANSLATIONS: Dict[str, Dict[str, str]] = {
        'zh': {
            # 菜单
            'file': '文件',
            'open': '打开视频',
            'exit': '退出',
            'language': '语言',
            'chinese': '中文',
            'english': 'English',
            
            # 主窗口
            'app_title': '视频帧截取工具',
            'video_preview': '视频预览',
            'control_panel': '控制面板',
            'output_settings': '输出设置',
            
            # 控制面板
            'capture_mode': '截取模式',
            'single_frame': '单帧截取',
            'batch_interval': '按间隔批量',
            'interval': '间隔(秒)',
            'start_time': '起始时间',
            'end_time': '结束时间',
            'output_format': '输出格式',
            'quality': '质量',
            'output_dir': '输出目录',
            'select_dir': '选择目录',
            'capture': '截取',
            'start_capture': '开始截取',
            
            # 播放器
            'play': '播放',
            'pause': '暂停',
            'stop': '停止',
            'timestamp': '时间戳',
            
            # 状态
            'ready': '就绪',
            'video_loaded': '已加载视频',
            'capturing': '正在截取...',
            'capture_complete': '截取完成',
            'capture_failed': '截取失败',
            'frames_saved': '已保存 {} 帧',
            
            # 错误
            'error': '错误',
            'file_not_found': '文件不存在',
            'unsupported_format': '不支持的格式',
            'corrupted_file': '文件损坏',
        },
        'en': {
            # Menu
            'file': 'File',
            'open': 'Open Video',
            'exit': 'Exit',
            'language': 'Language',
            'chinese': '中文',
            'english': 'English',
            
            # Main window
            'app_title': 'Video Frame Capture',
            'video_preview': 'Video Preview',
            'control_panel': 'Control Panel',
            'output_settings': 'Output Settings',
            
            # Control panel
            'capture_mode': 'Capture Mode',
            'single_frame': 'Single Frame',
            'batch_interval': 'Batch by Interval',
            'interval': 'Interval (s)',
            'start_time': 'Start Time',
            'end_time': 'End Time',
            'output_format': 'Output Format',
            'quality': 'Quality',
            'output_dir': 'Output Directory',
            'select_dir': 'Select Directory',
            'capture': 'Capture',
            'start_capture': 'Start Capture',
            
            # Player
            'play': 'Play',
            'pause': 'Pause',
            'stop': 'Stop',
            'timestamp': 'Timestamp',
            
            # Status
            'ready': 'Ready',
            'video_loaded': 'Video loaded',
            'capturing': 'Capturing...',
            'capture_complete': 'Capture complete',
            'capture_failed': 'Capture failed',
            'frames_saved': '{} frames saved',
            
            # Errors
            'error': 'Error',
            'file_not_found': 'File not found',
            'unsupported_format': 'Unsupported format',
            'corrupted_file': 'Corrupted file',
        }
    }
    
    @classmethod
    def set_language(cls, lang: str):
        """设置语言"""
        if lang in cls.TRANSLATIONS:
            cls._current_lang = lang
    
    @classmethod
    def get_language(cls) -> str:
        """获取当前语言"""
        return cls._current_lang
    
    @classmethod
    def tr(cls, key: str) -> str:
        """翻译文本"""
        return cls.TRANSLATIONS.get(cls._current_lang, {}).get(key, key)
