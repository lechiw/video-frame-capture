# -*- coding: utf-8 -*-
"""CLI 命令行入口 - 支持无 GUI 环境的帧提取"""

import argparse
import sys
from pathlib import Path

from ..core.video_parser import VideoParser
from ..core.frame_selector import FrameSelector
from ..core.frame_extractor import FrameExtractor
from ..core.image_writer import ImageWriter
from ..core.models import ImageWriteConfig, ImageFormat, ExtractionTask
from ..core.extraction_manager import ExtractionManager
from .. import __version__


def cmd_info(args):
    """查看视频信息"""
    parser = VideoParser()
    try:
        meta = parser.parse(args.video)
        print(f"📹 {Path(args.video).name}")
        print(f"   分辨率: {meta.width}x{meta.height}")
        print(f"   时长:   {_fmt_time(meta.duration)}")
        print(f"   帧率:   {meta.fps:.2f} fps")
        print(f"   总帧数: {meta.total_frames}")
        print(f"   编码:   {meta.codec}")
        return 0
    except Exception as e:
        print(f"❌ {e}")
        return 1


def cmd_extract(args):
    """提取帧"""
    video_path = args.video
    output_dir = Path(args.output)

    # 解析视频
    parser = VideoParser()
    try:
        meta = parser.parse(video_path)
    except Exception as e:
        print(f"❌ 无法解析视频: {e}")
        return 1

    # 计算时间戳
    selector = FrameSelector()
    start_sec = args.start
    end_sec = args.end if args.end is not None else meta.duration

    if args.timestamps:
        # 用户指定了具体时间点
        timestamps = []
        for ts_str in args.timestamps:
            try:
                timestamps.append(selector.parse_timestamp(ts_str))
            except Exception as e:
                print(f"⚠️  时间戳格式错误 '{ts_str}': {e}")
                return 1
    else:
        # 按间隔提取
        timestamps = selector.select_by_interval(
            duration=meta.duration,
            interval=args.interval,
            start_time=start_sec,
            end_time=end_sec,
        )

    if not timestamps:
        print("⚠️  没有需要提取的帧")
        return 0

    # 输出格式
    fmt = ImageFormat.PNG if args.format == "png" else ImageFormat.JPEG

    # 确保输出目录存在
    output_dir.mkdir(parents=True, exist_ok=True)

    # 提取帧
    extractor = FrameExtractor(video_path)
    writer = ImageWriter()

    print(f"🎬  {Path(video_path).name}")
    print(f"📐  {meta.width}x{meta.height}")
    print(f"⏱   {_fmt_time(start_sec)} → {_fmt_time(end_sec)}  ({len(timestamps)} 帧)")
    print(f"📁  → {output_dir}")
    print()

    config = ImageWriteConfig(
        format=fmt,
        quality=args.quality,
        output_dir=str(output_dir),
        scale=(args.width, args.height) if args.width else None,
    )

    manager = ExtractionManager()
    task = ExtractionTask(video_path=video_path, timestamps=timestamps, config=config)
    result = manager.execute(task, progress_callback=lambda c, t: _show_progress(c, t))

    print()
    if result.failed_timestamps:
        print(f"⚠️  失败: {len(result.failed_timestamps)}/{result.total_count}")
        return 1
    else:
        print(f"✅ 成功: {result.success_count}/{result.total_count} 帧 → {output_dir}")
        return 0


def cmd_ls(args):
    """列出支持的格式"""
    from ..core.video_parser import VideoParser
    print("支持的视频格式:")
    for ext in VideoParser.SUPPORTED_FORMATS:
        print(f"  {ext}")
    return 0


def _fmt_time(sec: float) -> str:
    h, r = divmod(int(sec), 3600)
    m, s = divmod(r, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def _show_progress(current: int, total: int):
    bar_len = 30
    filled = int(bar_len * current / total)
    bar = "█" * filled + "░" * (bar_len - filled)
    print(f"\r  [{bar}] {current}/{total}", end="", flush=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="vfc",
        description="视频帧截取工具 - 从视频中提取帧为图片",
        epilog="更多信息: https://github.com/lechiw/video-frame-capture",
    )
    parser.add_argument("--version", action="version", version=f"vfc {__version__}")

    sub = parser.add_subparsers(dest="command", help="可用命令")

    # info
    info_p = sub.add_parser("info", help="查看视频文件信息")
    info_p.add_argument("video", help="视频文件路径")
    info_p.set_defaults(func=cmd_info)

    # extract
    ext_p = sub.add_parser("extract", help="从视频中提取帧")
    ext_p.add_argument("video", help="视频文件路径")
    ext_p.add_argument("-o", "--output", default="./frames", help="输出目录 (默认: ./frames)")
    ext_p.add_argument("-i", "--interval", type=float, default=1.0, help="提取间隔秒数 (默认: 1)")
    ext_p.add_argument("--start", type=float, default=0.0, help="起始秒数 (默认: 0)")
    ext_p.add_argument("--end", type=float, default=None, help="结束秒数 (默认: 视频末尾)")
    ext_p.add_argument("-t", "--timestamps", nargs="+", help="指定时间戳 (HH:MM:SS 或秒数)")
    ext_p.add_argument("-f", "--format", choices=["png", "jpg"], default="png", help="输出格式 (默认: png)")
    ext_p.add_argument("-q", "--quality", type=int, default=85, help="JPEG 质量 1-100 (默认: 85)")
    ext_p.add_argument("--width", type=int, help="缩放宽度 (高度自动比例)")
    ext_p.add_argument("--height", type=int, help="缩放高度 (宽度自动比例)")
    ext_p.set_defaults(func=cmd_extract)

    # ls
    ls_p = sub.add_parser("ls", help="列出支持的视频格式")
    ls_p.set_defaults(func=cmd_ls)

    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
