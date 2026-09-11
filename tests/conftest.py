# tests/conftest.py
"""把后端接到一张临时空库上，避免动真实 app.db。"""
import os
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

_TEST_DB = Path(tempfile.mkdtemp()) / "test.db"
_TEST_UPLOAD = Path(tempfile.mkdtemp())
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB.as_posix()}"
os.environ["UPLOAD_DIR"] = str(_TEST_UPLOAD)
# 测试强制走开发假登录，不读 .env 里的真实微信密钥、不调真实 jscode2session
os.environ["WECHAT_APPID"] = "your-wechat-appid"
os.environ["WECHAT_SECRET"] = "your-wechat-secret"

from fastapi.testclient import TestClient  # noqa: E402
from main import app  # noqa: E402


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def auth_header(client, code: str, nickname: str = "测试用户") -> dict:
    res = client.post("/api/auth/login", json={"code": code, "nickname": nickname})
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["code"] == 0
    token = body["data"]["token"]
    return {"Authorization": f"Bearer {token}"}
