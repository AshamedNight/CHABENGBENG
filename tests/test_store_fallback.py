# tests/test_store_fallback.py
"""
前端 store 没有微信运行时，沙盒测不了真机请求。
这里检查身份相关函数失败时不得再捏假用户 / 假查询结果。
函数体改写可以，但不能再走「失败当成功」那条路。
"""
import re
from pathlib import Path

STORE_PATH = Path(__file__).resolve().parents[1] / "components" / "utils" / "store.js"
STORE = STORE_PATH.read_text(encoding="utf-8")

IDENTITY_FNS = [
    "initUser",
    "getUser",
    "updateUserInfo",
    "agreePrivacy",
    "getQueryCountInfo",
]


def _function_body(name: str) -> str:
    match = re.search(rf"(async\s+)?function\s+{re.escape(name)}\s*\([^)]*\)\s*\{{", STORE)
    assert match, f"store.js 里找不到函数 {name}"
    start = match.end()
    depth = 1
    i = start
    while i < len(STORE) and depth:
        if STORE[i] == "{":
            depth += 1
        elif STORE[i] == "}":
            depth -= 1
        i += 1
    return STORE[start : i - 1]


def test_identity_functions_do_not_call_get_local_user():
    for name in IDENTITY_FNS:
        body = _function_body(name)
        assert "getLocalUser()" not in body, f"{name} 失败时还在调用 getLocalUser() 假装登录成功"


def test_identity_failures_must_throw():
    for name in IDENTITY_FNS:
        body = _function_body(name)
        assert "throw" in body, f"{name} 失败时必须把错误抛出去，不能悄悄返回假数据"


def test_photo_match_does_not_invent_a_person():
    assert "mock_user_888" not in STORE


def test_search_target_does_not_disguise_errors_as_no_data():
    body = _function_body("searchTarget")
    assert "costMessage: '查询失败'" not in body
    assert "throw" in body
