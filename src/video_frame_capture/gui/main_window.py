"""主窗口"""

from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QMenuBar, QMenu, QFileDialog, QMessageBox, QStatusBar,
    QSplitter
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QKeySequence

from .i18n import I18N
from .video_player import VideoPlayer
from .control_panel import ControlPanel
from .toast import Toast
from ..core.video_parser import VideoParser
from ..core.extraction_manager import ExtractionManager
from ..core.models import ImageWriteConfig, ExtractionTask, VideoMetadata
from ..core.exceptions import VideoFrameCaptureError


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        
        self.video_parser = VideoParser()
        self.extraction_manager = ExtractionManager()
        self.current_video_metadata: Optional[VideoMetadata] = None
        
        self._setup_ui()
        self._setup_menu()
        self._setup_connections()
    
    def _setup_ui(self):
        self.setWindowTitle(I18N.tr('app_title'))
        self.setMinimumSize(1000, 600)
        
        # 中央组件
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QHBoxLayout(central)
        
        # 分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：视频播放器
        self.video_player = VideoPlayer()
        splitter.addWidget(self.video_player)
        
        # 右侧：控制面板
        self.control_panel = ControlPanel()
        splitter.addWidget(self.control_panel)
        
        splitter.setSizes([700, 300])
        layout.addWidget(splitter)
        
        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(I18N.tr('ready'))
    
    def _setup_menu(self):
        # 文件菜单
        file_menu = self.menuBar().addMenu(I18N.tr('file'))
        
        open_action = QAction(I18N.tr('open'), self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self._open_video)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction(I18N.tr('exit'), self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 语言菜单
        lang_menu = self.menuBar().addMenu(I18N.tr('language'))
        
        zh_action = QAction(I18N.tr('chinese'), self)
        zh_action.triggered.connect(lambda: self._change_language('zh'))
        lang_menu.addAction(zh_action)
        
        en_action = QAction(I18N.tr('english'), self)
        en_action.triggered.connect(lambda: self._change_language('en'))
        lang_menu.addAction(en_action)
    
    def _setup_connections(self):
        self.video_player.duration_changed.connect(self._on_duration_changed)
        self.control_panel.capture_single_clicked.connect(self._capture_single)
        self.control_panel.capture_batch_clicked.connect(self._capture_batch)
        
        # 快捷键 S 截取
        self.capture_shortcut = QKeySequence(Qt.Key.Key_S)
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_S and self.current_video_metadata:
            self._capture_single()
        super().keyPressEvent(event)
    
    def _open_video(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            I18N.tr('open'),
            '',
            'Video Files (*.mp4 *.avi *.mkv *.mov *.wmv *.flv);;All Files (*)'
        )
        
        if file_path:
            self._load_video(file_path)
    
    def _load_video(self, file_path: str):
        try:
            self.current_video_metadata = self.video_parser.parse(file_path)
            self.video_player.load_video(file_path)
            self.status_bar.showMessage(f"{I18N.tr('video_loaded')}: {Path(file_path).name}")
        except VideoFrameCaptureError as e:
            self.status_bar.showMessage(f"{I18N.tr('error')}: {str(e)}")
    
    def _on_duration_changed(self, duration: float):
        self.control_panel.set_duration(duration)
    
    def _capture_single(self):
        if not self.current_video_metadata:
            return
        
        timestamp = self.video_player.get_current_position()
        
        config = ImageWriteConfig(
            format=self.control_panel.get_output_format(),
            quality=self.control_panel.get_quality(),
            output_dir=self.control_panel.get_output_dir()
        )
        
        task = ExtractionTask(
            video_path=self.current_video_metadata.file_path,
            timestamps=[timestamp],
            config=config
        )
        
        self._execute_task(task)
    
    def _capture_batch(self):
        if not self.current_video_metadata:
            return
        
        selector = self.extraction_manager.frame_selector
        timestamps = selector.select_by_interval(
            duration=self.current_video_metadata.duration,
            interval=self.control_panel.get_interval(),
            start_time=self.control_panel.get_start_time(),
            end_time=self.control_panel.get_end_time()
        )
        
        if not timestamps:
            return
        
        config = ImageWriteConfig(
            format=self.control_panel.get_output_format(),
            quality=self.control_panel.get_quality(),
            output_dir=self.control_panel.get_output_dir()
        )
        
        task = ExtractionTask(
            video_path=self.current_video_metadata.file_path,
            timestamps=timestamps,
            config=config
        )
        
        self._execute_task(task)
    
    def _execute_task(self, task: ExtractionTask):
        self.status_bar.showMessage(I18N.tr('capturing'))
        
        try:
            result = self.extraction_manager.execute(
                task,
                progress_callback=lambda c, t: self.status_bar.showMessage(
                    f"{I18N.tr('capturing')} {c}/{t}"
                )
            )
            
            if result.success_count > 0:
                msg = I18N.tr('frames_saved').format(result.success_count)
                self.status_bar.showMessage(I18N.tr('capture_complete') + f": {msg}")
                QMessageBox.information(self, I18N.tr('capture_complete'), msg)
            else:
                self.status_bar.showMessage(I18N.tr('capture_failed'))
                QMessageBox.warning(self, I18N.tr('error'), I18N.tr('capture_failed'))
                
        except Exception as e:
            error_msg = str(e)
            self.status_bar.showMessage(f"{I18N.tr('error')}: {error_msg}")
            QMessageBox.critical(self, I18N.tr('error'), error_msg)
    
    def _change_language(self, lang: str):
        I18N.set_language(lang)
        QMessageBox.information(
            self,
            I18N.tr('language'),
            "请重启应用以应用语言更改\nPlease restart the application to apply language changes"
        )
