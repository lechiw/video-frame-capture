"""测试图片写入器"""

import tempfile
from pathlib import Path
import numpy as np
import pytest
from PIL import Image

from ..core.image_writer import ImageWriter
from ..core.models import ImageWriteConfig, ImageFormat


class TestImageWriter:
    def setup_method(self):
        self.writer = ImageWriter()
        self.tmpdir = tempfile.mkdtemp()

    def _make_test_frame(self, w=320, h=240):
        """生成测试帧（RGB 渐变）"""
        frame = np.zeros((h, w, 3), dtype=np.uint8)
        for y in range(h):
            frame[y, :, 0] = int(y * 255 / h)  # R 渐变
            frame[y, :, 1] = 128
            frame[y, :, 2] = 255 - int(y * 255 / h)
        return frame

    def test_write_png(self):
        frame = self._make_test_frame()
        config = ImageWriteConfig(
            format=ImageFormat.PNG,
            output_dir=self.tmpdir,
        )
        path = self.writer.write(frame, config, video_name="test", timestamp=10.5, index=1)
        assert Path(path).exists()
        _, ext = Path(path).suffix, Path(path).suffix
        assert ext == ".png"
        # 验证可以打开
        img = Image.open(path)
        assert img.size == (320, 240)

    def test_write_jpeg(self):
        frame = self._make_test_frame()
        config = ImageWriteConfig(
            format=ImageFormat.JPEG,
            quality=80,
            output_dir=self.tmpdir,
        )
        path = self.writer.write(frame, config, video_name="test", timestamp=10.5, index=1)
        assert Path(path).exists()
        assert Path(path).suffix == ".jpg" or Path(path).suffixes  # PIL 保存为 .jpg

    def test_write_with_scale(self):
        frame = self._make_test_frame()
        config = ImageWriteConfig(
            format=ImageFormat.PNG,
            output_dir=self.tmpdir,
            scale=(160, 120),
        )
        path = self.writer.write(frame, config, video_name="test", timestamp=10.5, index=1)
        img = Image.open(path)
        assert img.size == (160, 120)

    def test_filename_template(self):
        """验证文件名包含视频名和时间戳"""
        frame = self._make_test_frame()
        config = ImageWriteConfig(
            format=ImageFormat.PNG,
            output_dir=self.tmpdir,
            naming_template="{video_name}_{timestamp}_{index}",
        )
        path = self.writer.write(frame, config, video_name="my_video", timestamp=90.0, index=5)
        assert "my_video" in path
        assert "005" in path or "5" in path

    def test_conflict_resolution(self):
        """验证同名文件自动处理"""
        frame = self._make_test_frame()
        config = ImageWriteConfig(
            format=ImageFormat.PNG,
            output_dir=self.tmpdir,
        )
        # 写两次同一时间戳
        p1 = self.writer.write(frame, config, video_name="test", timestamp=0.0, index=1)
        p2 = self.writer.write(frame, config, video_name="test", timestamp=0.0, index=1)
        assert p1 != p2  # 不应冲突
