# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from pathlib import Path

# Find imageio_ffmpeg binary
import imageio_ffmpeg
ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
ffmpeg_dir = str(Path(ffmpeg_exe).parent)

a = Analysis(
    ['run.py'],
    pathex=['src'],
    binaries=[(ffmpeg_exe, 'imageio_ffmpeg/binaries')],
    datas=[],
    hiddenimports=[
        'video_frame_capture',
        'video_frame_capture.core',
        'video_frame_capture.core.models',
        'video_frame_capture.core.exceptions',
        'video_frame_capture.core.video_parser',
        'video_frame_capture.core.frame_selector',
        'video_frame_capture.core.frame_extractor',
        'video_frame_capture.core.image_writer',
        'video_frame_capture.core.extraction_manager',
        'video_frame_capture.gui',
        'video_frame_capture.gui.main_window',
        'video_frame_capture.gui.video_player',
        'video_frame_capture.gui.control_panel',
        'video_frame_capture.gui.i18n',
        'video_frame_capture.gui.toast',
        'imageio_ffmpeg',
        'imageio_ffmpeg.binaries',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='VideoFrameCapture',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
