"""测试帧选择器"""

import pytest
from ..core.frame_selector import FrameSelector
from ..core.exceptions import TimestampFormatError, TimestampOutOfRangeError, IntervalError


class TestFrameSelector:
    def setup_method(self):
        self.selector = FrameSelector()

    # ── 时间戳解析 ──

    def test_parse_hh_mm_ss(self):
        assert self.selector.parse_timestamp("01:30:15") == pytest.approx(5415.0)

    def test_parse_hh_mm_ss_mmm(self):
        assert self.selector.parse_timestamp("00:01:30.500") == pytest.approx(90.5)

    def test_parse_seconds(self):
        assert self.selector.parse_timestamp("120") == pytest.approx(120.0)

    def test_parse_seconds_float(self):
        assert self.selector.parse_timestamp("30.5") == pytest.approx(30.5)

    def test_parse_zero(self):
        assert self.selector.parse_timestamp("0") == pytest.approx(0.0)

    def test_parse_invalid_format(self):
        with pytest.raises(TimestampFormatError):
            self.selector.parse_timestamp("not-a-time")

    # ── 时间戳格式化 ──

    def test_format_zero(self):
        assert self.selector.format_timestamp(0) == "00:00:00.000"

    def test_format_seconds(self):
        assert self.selector.format_timestamp(3661.5) == "01:01:01.500"

    # ── 时间戳验证 ──

    def test_validate_valid(self):
        assert self.selector.validate_timestamp(5.0, 10.0) is True

    def test_validate_edge_zero(self):
        assert self.selector.validate_timestamp(0.0, 10.0) is True

    def test_validate_edge_end(self):
        assert self.selector.validate_timestamp(10.0, 10.0) is True

    def test_validate_out_of_range(self):
        assert self.selector.validate_timestamp(10.1, 10.0) is False

    def test_validate_negative(self):
        assert self.selector.validate_timestamp(-1.0, 10.0) is False

    def test_validate_or_raise_ok(self):
        self.selector.validate_timestamp_or_raise(5.0, 10.0)

    def test_validate_or_raise_out_of_range(self):
        with pytest.raises(TimestampOutOfRangeError):
            self.selector.validate_timestamp_or_raise(15.0, 10.0)

    # ── 按间隔选择 ──

    def test_select_by_interval_basic(self):
        result = self.selector.select_by_interval(duration=10.0, interval=2.0)
        assert len(result) == 6  # 0, 2, 4, 6, 8, 10
        assert result[0] == 0.0
        assert result[-1] == 10.0

    def test_select_by_interval_with_range(self):
        result = self.selector.select_by_interval(
            duration=10.0, interval=1.0, start_time=3.0, end_time=6.0
        )
        assert len(result) == 4  # 3, 4, 5, 6
        assert result[0] == 3.0
        assert result[-1] == 6.0

    def test_select_by_interval_clamp_range(self):
        result = self.selector.select_by_interval(
            duration=10.0, interval=1.0, start_time=-5.0, end_time=15.0
        )
        assert result[0] == 0.0
        assert result[-1] == 10.0

    def test_select_by_interval_empty(self):
        result = self.selector.select_by_interval(duration=10.0, interval=1.0, start_time=20.0, end_time=30.0)
        assert result == []

    def test_select_interval_too_small(self):
        with pytest.raises(IntervalError):
            self.selector.select_by_interval(duration=10.0, interval=0.01)
