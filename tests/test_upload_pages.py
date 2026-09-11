# tests/test_upload_pages.py
"""沙盒跑不了微信选图。这里只保证三个会选照片的页面，提交前会调用 store 上传。"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STORE = (ROOT / "components" / "utils" / "store.js").read_text(encoding="utf-8")
COMPLAINT = (ROOT / "components" / "pages" / "complaint" / "complaint.js").read_text(encoding="utf-8")
PROFILE_EDIT = (ROOT / "components" / "pages" / "profile-edit" / "profile-edit.js").read_text(encoding="utf-8")
PHOTO_MATCH = (ROOT / "components" / "pages" / "photo-match" / "photo-match.js").read_text(encoding="utf-8")
REQUEST = (ROOT / "components" / "utils" / "request.js").read_text(encoding="utf-8")


def _function_body(source: str, name: str) -> str:
    match = re.search(rf"(async\s+)?function\s+{re.escape(name)}\s*\([^)]*\)\s*\{{", source)
    assert match, f"找不到函数 {name}"
    start = match.end()
    depth = 1
    i = start
    while i < len(source) and depth:
        if source[i] == "{":
            depth += 1
        elif source[i] == "}":
            depth -= 1
        i += 1
    return source[start : i - 1]


def test_store_has_upload_helpers_that_throw():
    body = _function_body(STORE, "uploadImage")
    assert "/api/upload-json" in body
    assert "throw" in body
    assert "uploadImages" in STORE
    assert "wx.uploadFile" not in body


def test_upload_reads_bytes_instead_of_wx_upload_file():
    body = _function_body(STORE, "readImageAsBase64")
    assert "readFile" in body
    assert "getImageInfo" in body
    upload_body = _function_body(STORE, "uploadImage")
    assert "readImageAsBase64" in upload_body
    assert "post('/api/upload-json'" in upload_body or 'post("/api/upload-json"' in upload_body


def test_pages_use_choose_image_not_choose_media():
    assert "chooseMedia" not in COMPLAINT
    assert "chooseImage" in COMPLAINT
    assert "chooseMedia" not in PROFILE_EDIT
    assert "chooseImage" in PROFILE_EDIT
    assert "chooseMedia" not in PHOTO_MATCH
    assert "chooseImage" in PHOTO_MATCH


def test_complaint_uploads_before_add_complaint():
    assert "store.uploadImages" in COMPLAINT
    submit = COMPLAINT[COMPLAINT.index("async submitComplaint") :]
    upload_at = submit.index("store.uploadImages")
    add_at = submit.index("store.addComplaint")
    assert upload_at < add_at


def test_profile_edit_uploads_avatar_before_save():
    save = PROFILE_EDIT[PROFILE_EDIT.index("async save") :]
    assert "store.uploadImage" in save
    assert save.index("store.uploadImage") < save.index("store.updateUserInfo")


def test_photo_match_uploads_before_match():
    start = PHOTO_MATCH[PHOTO_MATCH.index("async startMatch") :]
    assert "store.uploadImage" in start
    assert start.index("store.uploadImage") < start.index("store.photoMatch")


def test_upload_file_helper_rejects_business_error():
    body = _function_body(REQUEST, "uploadFile")
    assert "code !== 0" in body or "code != 0" in body
    assert "reject" in body
