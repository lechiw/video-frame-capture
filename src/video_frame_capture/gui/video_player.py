# -*- coding: utf-8 -*-
"""Video player widget."""

from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QSlider, QLabel, QStyle
)
from PyQt6.QtCore import Qt, QUrl, pyqtSignal
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget


class VideoPlayer(QWidget):
    position_changed = pyqtSignal(float)
    duration_changed = pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._duration_ms = 0.0
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumSize(640, 360)
        layout.addWidget(self.video_widget, 1)
        control_layout = QHBoxLayout()
        self.play_button = QPushButton()
        self.play_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.play_button.clicked.connect(self._toggle_play)
        control_layout.addWidget(self.play_button)
        self.stop_button = QPushButton()
        self.stop_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaStop))
        self.stop_button.clicked.connect(self.stop)
        control_layout.addWidget(self.stop_button)
        self.timeline_slider = QSlider(Qt.Orientation.Horizontal)
        self.timeline_slider.setRange(0, 1000)
        self.timeline_slider.setValue(0)
        self.timeline_slider.sliderMoved.connect(self._seek)
        control_layout.addWidget(self.timeline_slider, 1)
        self.time_label = QLabel("00:00:00.000 / 00:00:00.000")
        control_layout.addWidget(self.time_label)
        layout.addLayout(control_layout)
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.positionChanged.connect(self._on_position_changed)
        self.media_player.durationChanged.connect(self._on_duration_changed)
        self.media_player.playbackStateChanged.connect(self._on_state_changed)

    def load_video(self, file_path):
        self.media_player.setSource(QUrl.fromLocalFile(file_path))
        self.media_player.pause()

    def _toggle_play(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()

    def play(self):
        self.media_player.play()

    def pause(self):
        self.media_player.pause()

    def stop(self):
        self.media_player.stop()

    def _seek(self, position):
        if self._duration_ms > 0:
            self.media_player.setPosition(int(position * self._duration_ms / 1000))

    def get_current_position(self):
        return self.media_player.position() / 1000.0

    def _on_position_changed(self, position):
        if self._duration_ms > 0:
            self.timeline_slider.blockSignals(True)
            self.timeline_slider.setValue(int(position / self._duration_ms * 1000))
            self.timeline_slider.blockSignals(False)
        current_sec = position / 1000.0
        duration_sec = self._duration_ms / 1000.0
        self.time_label.setText(f"{self._format_time(current_sec)} / {self._format_time(duration_sec)}")
        self.position_changed.emit(current_sec)

    def _on_duration_changed(self, duration):
        self._duration_ms = float(duration)
        self.duration_changed.emit(duration / 1000.0)
        self.time_label.setText(f"00:00:00.000 / {self._format_time(duration / 1000.0)}")

    def _on_state_changed(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause))
        else:
            self.play_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))

    @staticmethod
    def _format_time(seconds):
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"
