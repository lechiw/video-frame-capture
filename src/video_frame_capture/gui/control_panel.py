"""控制面板组件"""

from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QRadioButton,
    QButtonGroup, QDoubleSpinBox, QLabel, QComboBox,
    QSlider, QPushButton, QFileDialog, QHBoxLayout
)
from PyQt6.QtCore import Qt, pyqtSignal

from .i18n import I18N
from ..core.models import ImageFormat


class ControlPanel(QWidget):
    """控制面板"""
    
    capture_single_clicked = pyqtSignal()
    capture_batch_clicked = pyqtSignal()
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 截取模式
        mode_group = QGroupBox(I18N.tr('capture_mode'))
        mode_layout = QVBoxLayout(mode_group)
        
        self.mode_button_group = QButtonGroup(self)
        
        self.single_radio = QRadioButton(I18N.tr('single_frame'))
        self.single_radio.setChecked(True)
        self.mode_button_group.addButton(self.single_radio, 0)
        mode_layout.addWidget(self.single_radio)
        
        self.batch_radio = QRadioButton(I18N.tr('batch_interval'))
        self.mode_button_group.addButton(self.batch_radio, 1)
        mode_layout.addWidget(self.batch_radio)
        
        layout.addWidget(mode_group)
        
        # 批量设置
        batch_group = QGroupBox(I18N.tr('batch_interval'))
        batch_layout = QVBoxLayout(batch_group)
        
        # 间隔
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel(I18N.tr('interval')))
        self.interval_spin = QDoubleSpinBox()
        self.interval_spin.setRange(0.1, 9999.0)
        self.interval_spin.setValue(1.0)
        self.interval_spin.setSingleStep(0.1)
        interval_layout.addWidget(self.interval_spin)
        batch_layout.addLayout(interval_layout)
        
        # 起始时间
        start_layout = QHBoxLayout()
        start_layout.addWidget(QLabel(I18N.tr('start_time')))
        self.start_time_spin = QDoubleSpinBox()
        self.start_time_spin.setRange(0, 999999.0)
        self.start_time_spin.setValue(0.0)
        start_layout.addWidget(self.start_time_spin)
        batch_layout.addLayout(start_layout)
        
        # 结束时间
        end_layout = QHBoxLayout()
        end_layout.addWidget(QLabel(I18N.tr('end_time')))
        self.end_time_spin = QDoubleSpinBox()
        self.end_time_spin.setRange(0, 999999.0)
        self.end_time_spin.setValue(0.0)
        end_layout.addWidget(self.end_time_spin)
        batch_layout.addLayout(end_layout)
        
        layout.addWidget(batch_group)
        
        # 输出设置
        output_group = QGroupBox(I18N.tr('output_settings'))
        output_layout = QVBoxLayout(output_group)
        
        # 格式
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel(I18N.tr('output_format')))
        self.format_combo = QComboBox()
        self.format_combo.addItem("PNG", ImageFormat.PNG.value)
        self.format_combo.addItem("JPEG", ImageFormat.JPEG.value)
        format_layout.addWidget(self.format_combo)
        output_layout.addLayout(format_layout)
        
        # 质量
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel(I18N.tr('quality')))
        self.quality_slider = QSlider(Qt.Orientation.Horizontal)
        self.quality_slider.setRange(1, 100)
        self.quality_slider.setValue(85)
        quality_layout.addWidget(self.quality_slider)
        self.quality_label = QLabel("85")
        self.quality_slider.valueChanged.connect(lambda v: self.quality_label.setText(str(v)))
        quality_layout.addWidget(self.quality_label)
        output_layout.addLayout(quality_layout)
        
        # 输出目录
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel(I18N.tr('output_dir')))
        self.dir_button = QPushButton(I18N.tr('select_dir'))
        self.dir_button.clicked.connect(self._select_dir)
        dir_layout.addWidget(self.dir_button)
        output_layout.addLayout(dir_layout)
        
        self.output_dir_label = QLabel("")
        output_layout.addWidget(self.output_dir_label)
        
        layout.addWidget(output_group)
        
        # 截取按钮
        self.capture_button = QPushButton(I18N.tr('capture'))
        self.capture_button.clicked.connect(self._on_capture)
        layout.addWidget(self.capture_button)
        
        layout.addStretch()
    
    def _select_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, I18N.tr('select_dir'))
        if dir_path:
            self.output_dir_label.setText(dir_path)
    
    def _on_capture(self):
        if self.single_radio.isChecked():
            self.capture_single_clicked.emit()
        else:
            self.capture_batch_clicked.emit()
    
    def get_output_format(self) -> ImageFormat:
        return ImageFormat(self.format_combo.currentData())
    
    def get_quality(self) -> int:
        return self.quality_slider.value()
    
    def get_output_dir(self) -> str:
        return self.output_dir_label.text()
    
    def get_interval(self) -> float:
        return self.interval_spin.value()
    
    def get_start_time(self) -> float:
        return self.start_time_spin.value()
    
    def get_end_time(self) -> float:
        return self.end_time_spin.value()
    
    def set_duration(self, duration: float):
        self.start_time_spin.setMaximum(duration)
        self.end_time_spin.setMaximum(duration)
        self.end_time_spin.setValue(duration)
