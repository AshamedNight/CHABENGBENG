# tests/test_upload.py
"""图片上传：登录后能存到本地静态目录；空文件 / 非图片 / 超大文件要拒绝。"""
import base64

from tests.conftest import auth_header

# 1x1 透明 PNG
PNG_1X1 = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000a49444154789c63000100000500010d0a2db40000000049454e44ae426082"
)

MAX_UPLOAD_BYTES = 5 * 1024 * 1024


def test_upload_requires_login(client):
    res = client.post(
        "/api/upload",
        files={"file": ("tiny.png", PNG_1X1, "image/png")},
    )
    assert res.status_code in (401, 403)


def test_upload_image_success_and_can_download(client):
    headers = auth_header(client, "wx_upload_ok_111")
    res = client.post(
        "/api/upload",
        headers=headers,
        files={"file": ("tiny.png", PNG_1X1, "image/png")},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["code"] == 0
    url = body["data"]["url"]
    assert "/uploads/" in url
    assert url.endswith(".png")

    filename = url.rstrip("/").rsplit("/", 1)[-1]
    static = client.get(f"/uploads/{filename}")
    assert static.status_code == 200
    assert static.content == PNG_1X1


def test_upload_rejects_empty_file(client):
    headers = auth_header(client, "wx_upload_empty_222")
    res = client.post(
        "/api/upload",
        headers=headers,
        files={"file": ("empty.png", b"", "image/png")},
    )
    assert res.status_code == 400


def test_upload_rejects_non_image(client):
    headers = auth_header(client, "wx_upload_txt_333")
    res = client.post(
        "/api/upload",
        headers=headers,
        files={"file": ("notes.txt", b"hello world", "text/plain")},
    )
    assert res.status_code == 400


def test_upload_rejects_file_over_5mb(client):
    headers = auth_header(client, "wx_upload_big_444")
    payload = PNG_1X1[:8] + b"\x00" * (MAX_UPLOAD_BYTES)
    res = client.post(
        "/api/upload",
        headers=headers,
        files={"file": ("big.png", payload, "image/png")},
    )
    assert res.status_code == 400


def test_upload_json_requires_login(client):
    res = client.post(
        "/api/upload-json",
        json={"filename": "tiny.png", "content_base64": "iVBORw0KGgo="},
    )
    assert res.status_code in (401, 403)


def test_upload_json_image_success_and_can_download(client):
    headers = auth_header(client, "wx_upload_json_555")
    res = client.post(
        "/api/upload-json",
        headers=headers,
        json={
            "filename": "tiny.png",
            "content_base64": base64.b64encode(PNG_1X1).decode("ascii"),
        },
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["code"] == 0
    url = body["data"]["url"]
    assert "/uploads/" in url
    filename = url.rstrip("/").rsplit("/", 1)[-1]
    static = client.get(f"/uploads/{filename}")
    assert static.status_code == 200
    assert static.content == PNG_1X1


def test_upload_json_rejects_non_image(client):
    headers = auth_header(client, "wx_upload_json_txt_666")
    res = client.post(
        "/api/upload-json",
        headers=headers,
        json={
            "filename": "notes.txt",
            "content_base64": base64.b64encode(b"hello world").decode("ascii"),
        },
    )
    assert res.status_code == 400


def test_static_uploads_cannot_escape_directory(client):
    res = client.get("/uploads/../config.py")
    assert res.status_code in (400, 404, 422)
