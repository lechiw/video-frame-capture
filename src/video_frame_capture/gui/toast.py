# -*- coding: utf-8 -*-
"""Toast notification widget."""

from PyQt6.QtWidgets import QLabel, QWidget, QGraphicsOpacityEffect
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont


class Toast(QLabel):
    """Floating toast notification that auto-fades."""

    def __init__(self, parent: QWidget, message: str, duration: int = 2500, success: bool = True):
        super().__init__(message, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        bg_color = "rgba(50, 180, 50, 220)" if success else "rgba(220, 50, 50, 220)"
        self.setStyleSheet(
            f"background-color: {bg_color};"
            "color: white;"
            "border-radius: 8px;"
            "padding: 12px 24px;"
            "font-size: 14px;"
        )
        self.setFont(QFont("Microsoft YaHei", 12))
        self.adjustSize()
        self.setMinimumWidth(200)

        # Center on parent
        x = (parent.width() - self.width()) // 2
        y = 60
        self.move(max(0, x), y)

        # Opacity effect for fade out
        self._opacity = QGraphicsOpacityEffect(self)
        self._opacity.setOpacity(1.0)
        self.setGraphicsEffect(self._opacity)

        self.show()
        self.raise_()

        # Start fade out before end
        fade_start = max(duration - 500, 500)
        QTimer.singleShot(fade_start, self._fade_out)
        QTimer.singleShot(duration, self.deleteLater)

    def _fade_out(self):
        self._anim = QPropertyAnimation(self._opacity, b"opacity")
        self._anim.setDuration(500)
        self._anim.setStartValue(1.0)
        self._anim.setEndValue(0.0)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.start()
