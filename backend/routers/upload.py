# routers/upload.py - 图片上传
import base64
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from models import User
from schemas import ApiResponse, UploadBase64Request
from auth import get_current_user
from config import (
    UPLOAD_DIR,
    MAX_UPLOAD_BYTES,
    ALLOWED_IMAGE_EXTS,
    PUBLIC_BASE_URL,
)

router = APIRouter(tags=["上传"])

UPLOAD_ROOT = Path(UPLOAD_DIR).resolve()


def _ensure_upload_root() -> Path:
    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    return UPLOAD_ROOT


def _sniff_ext(content: bytes, filename: str) -> str:
    name = (filename or "").lower()
    ext = Path(name).suffix
    if ext == ".jpeg":
        ext = ".jpg"

    head = content[:12]
    magic_ext = None
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        magic_ext = ".png"
    elif head.startswith(b"\xff\xd8\xff"):
        magic_ext = ".jpg"
    elif head.startswith(b"GIF87a") or head.startswith(b"GIF89a"):
        magic_ext = ".gif"
    elif len(head) >= 12 and head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        magic_ext = ".webp"

    if magic_ext is None:
        raise HTTPException(status_code=400, detail="仅支持图片文件")
    if ext:
        if ext not in ALLOWED_IMAGE_EXTS and ext != ".jpg":
            raise HTTPException(status_code=400, detail="仅支持 jpg/png/gif/webp")
        if ext != magic_ext:
            raise HTTPException(status_code=400, detail="文件类型与后缀不一致")
    return magic_ext


def _save_image_bytes(content: bytes, filename: str) -> dict:
    if not content:
        raise HTTPException(status_code=400, detail="文件不能为空")
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="图片不能超过 5MB")

    ext = _sniff_ext(content, filename or "")
    root = _ensure_upload_root()
    saved_name = f"{uuid4().hex}{ext}"
    dest = (root / saved_name).resolve()
    if dest.parent != root:
        raise HTTPException(status_code=400, detail="非法文件名")

    dest.write_bytes(content)
    base = PUBLIC_BASE_URL.rstrip("/")
    return {"url": f"{base}/uploads/{saved_name}"}


@router.post("/api/upload")
async def upload_image(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    content = await file.read()
    return ApiResponse(data=_save_image_bytes(content, file.filename or ""))


@router.post("/api/upload-json")
async def upload_image_json(
    req: UploadBase64Request,
    user: User = Depends(get_current_user),
):
    # Windows 开发者工具里 wx.uploadFile 经常 file not found，前端改走这条
    if not req.content_base64:
        raise HTTPException(status_code=400, detail="文件不能为空")
    try:
        content = base64.b64decode(req.content_base64, validate=False)
    except Exception:
        raise HTTPException(status_code=400, detail="图片数据无法解析")
    return ApiResponse(data=_save_image_bytes(content, req.filename or ""))


@router.get("/uploads/{filename}")
async def serve_upload(filename: str):
    safe_name = Path(filename).name
    if safe_name != filename or filename in {".", ".."}:
        raise HTTPException(status_code=400, detail="非法文件名")
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_IMAGE_EXTS:
        raise HTTPException(status_code=404, detail="文件不存在")

    root = _ensure_upload_root()
    dest = (root / safe_name).resolve()
    if dest.parent != root or not dest.is_file():
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(dest)
