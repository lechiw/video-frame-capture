# -*- coding: utf-8 -*-
"""
Web 服务器 - 在浏览器中预览视频并提取帧

启动:
    vfc-web          # CLI 命令
    python -m vfc.web.server  # 直接运行
"""

import io
import json
import os
import tempfile
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

import uvicorn

from ..core.video_parser import VideoParser
from ..core.frame_selector import FrameSelector
from ..core.frame_extractor import FrameExtractor
from ..core.image_writer import ImageWriter
from ..core.models import ImageWriteConfig, ImageFormat, ExtractionTask
from ..core.extraction_manager import ExtractionManager
from .. import __version__

# ── 常量 ──

HERE = Path(__file__).parent
TEMPLATES_DIR = str(HERE / "templates")
STATIC_DIR = str(HERE / "static")

# 临时文件清理周期（秒）
CLEANUP_INTERVAL = 3600
# 文件最大保留时间（秒）
MAX_FILE_AGE = 7200

# ── FastAPI ──

app = FastAPI(
    title="Video Frame Capture",
    description="浏览器端视频帧提取工具",
    version=__version__,
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# 临时存储管理
_UPLOAD_DIR: Optional[Path] = None

# ── 启动 / 关闭事件 ──


@app.on_event("startup")
async def startup():
    global _UPLOAD_DIR
    _UPLOAD_DIR = Path(tempfile.mkdtemp(prefix="vfc_uploads_"))
    _UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    print(f"📁 上传目录: {_UPLOAD_DIR}")


@app.on_event("shutdown")
async def shutdown():
    """清理临时文件"""
    if _UPLOAD_DIR and _UPLOAD_DIR.exists():
        import shutil
        shutil.rmtree(_UPLOAD_DIR, ignore_errors=True)
        print(f"🧹 已清理: {_UPLOAD_DIR}")

# ── 辅助函数 ──


def _get_upload_dir() -> Path:
    if _UPLOAD_DIR is None:
        raise RuntimeError("服务器未初始化")
    return _UPLOAD_DIR


def _allowed_file(filename: str) -> bool:
    ext = Path(filename).suffix.lower()
    return ext in VideoParser.SUPPORTED_FORMATS


def _cleanup_old_files():
    """清理过期文件"""
    upload_dir = _get_upload_dir()
    now = os.path.getmtime(upload_dir)
    for f in upload_dir.iterdir():
        if f.is_file():
            age = now - os.path.getmtime(f)
            if age > MAX_FILE_AGE:
                f.unlink(missing_ok=True)

# ── 页面路由 ──


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "version": __version__},
    )

# ── API 路由 ──


@app.post("/api/upload")
async def upload_video(file: UploadFile = File(...)):
    """上传视频文件"""
    if not file.filename:
        raise HTTPException(400, "未选择文件")
    if not _allowed_file(file.filename):
        raise HTTPException(400, f"不支持的格式: {Path(file.filename).suffix}")

    # 生成唯一 ID 保存文件
    file_id = str(uuid.uuid4())[:8]
    ext = Path(file.filename).suffix
    save_name = f"{file_id}{ext}"
    save_path = _get_upload_dir() / save_name

    content = await file.read()
    save_path.write_bytes(content)

    # 解析视频信息
    parser = VideoParser()
    try:
        meta = parser.parse(str(save_path))
    except Exception as e:
        save_path.unlink(missing_ok=True)
        raise HTTPException(400, f"无法解析视频: {e}")

    return {
        "file_id": file_id,
        "filename": file.filename,
        "path": save_name,
        "metadata": {
            "duration": round(meta.duration, 1),
            "fps": round(meta.fps, 2),
            "width": meta.width,
            "height": meta.height,
            "codec": meta.codec,
            "total_frames": meta.total_frames,
            "size": len(content),
        },
    }


@app.get("/api/video/{file_path:path}")
async def serve_video(file_path: str):
    """提供视频文件流，用于浏览器预览"""
    video_path = _get_upload_dir() / file_path
    if not video_path.exists():
        raise HTTPException(404, "视频文件未找到")

    return FileResponse(
        str(video_path),
        media_type="video/mp4",
        headers={"Accept-Ranges": "bytes"},
    )


@app.post("/api/extract")
async def extract_frames(
    file_path: str = Form(...),
    mode: str = Form("interval"),
    interval: float = Form(1.0),
    start_time: float = Form(0.0),
    end_time: Optional[float] = Form(None),
    timestamps: Optional[str] = Form(None),
    output_format: str = Form("png"),
    quality: int = Form(85),
    width: Optional[int] = Form(None),
    height: Optional[int] = Form(None),
):
    """提取帧并返回 ZIP 文件"""
    video_path = _get_upload_dir() / file_path
    if not video_path.exists():
        raise HTTPException(404, "视频文件未找到")

    # 解析视频
    parser = VideoParser()
    try:
        meta = parser.parse(str(video_path))
    except Exception as e:
        raise HTTPException(400, f"无法解析视频: {e}")

    # 计算时间戳
    selector = FrameSelector()
    if mode == "custom" and timestamps:
        ts_list = []
        for ts_str in json.loads(timestamps):
            try:
                ts_list.append(selector.parse_timestamp(ts_str))
            except Exception as e:
                raise HTTPException(400, f"时间戳格式错误 '{ts_str}': {e}")
    else:
        end = end_time if end_time is not None else meta.duration
        if start_time >= end:
            raise HTTPException(400, "起始时间必须小于结束时间")
        ts_list = selector.select_by_interval(
            duration=meta.duration,
            interval=interval,
            start_time=start_time,
            end_time=end,
        )

    if not ts_list:
        raise HTTPException(400, "没有需要提取的帧")

    # 提取帧
    fmt = ImageFormat.PNG if output_format == "png" else ImageFormat.JPEG
    video_name = video_path.stem
    output_dir = _get_upload_dir() / f"frames_{video_path.stem}_{uuid.uuid4().hex[:6]}"
    output_dir.mkdir(exist_ok=True)

    config = ImageWriteConfig(
        format=fmt,
        quality=quality,
        output_dir=str(output_dir),
        scale=(width, height) if width and height else None,
    )

    manager = ExtractionManager()
    task = ExtractionTask(video_path=str(video_path), timestamps=ts_list, config=config)
    result = manager.execute(task)

    if result.success_count == 0:
        raise HTTPException(500, "提取全部失败")

    # 打包为 ZIP
    import zipfile
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for saved_path in result.saved_paths:
            p = Path(saved_path)
            zf.write(str(p), arcname=p.name)
    zip_buf.seek(0)

    # 清理输出目录
    import shutil
    shutil.rmtree(output_dir, ignore_errors=True)

    # 清理旧文件（非阻塞）
    _cleanup_old_files()

    zip_filename = f"{video_name}_frames_{uuid.uuid4().hex[:6]}.zip"

    return StreamingResponse(
        zip_buf,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{zip_filename}"',
            "Content-Length": str(zip_buf.getbuffer().nbytes),
        },
    )


@app.get("/api/health")
async def health():
    """健康检查"""
    return {"status": "ok", "version": __version__}


# ── 命令行入口 ──


def main():
    """启动 Web 服务器"""
    import argparse

    parser = argparse.ArgumentParser(description="Video Frame Capture Web 服务")
    parser.add_argument("--host", default="0.0.0.0", help="监听地址 (默认: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8765, help="监听端口 (默认: 8765)")
    parser.add_argument("--reload", action="store_true", help="开发模式自动重载")
    args = parser.parse_args()

    print(f"""
╔══════════════════════════════════╗
║   🎬 Video Frame Capture Web    ║
║   {__version__}                       ║
╚══════════════════════════════════╝

    🌐 http://{args.host}:{args.port}
    📁 上传视频后即可预览并提取帧
    🔒 仅建议内网使用
""")
    uvicorn.run(
        "video_frame_capture.web.server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
