# tests/test_api_contract.py
"""打真实 HTTP 接口（TestClient，不占端口）。绿 = 后端按约定干活。"""
from tests.conftest import auth_header


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_vip_plans_returns_list(client):
    res = client.get("/api/vip/plans")
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert isinstance(body["data"], list)
    assert body["data"][0]["type"] == "vip_year"
    assert body["data"][0]["price"] == 399.0


def test_user_info_requires_login(client):
    res = client.get("/api/user/info")
    # FastAPI HTTPBearer 没带 Authorization 时是 403；无效 token 才是 401
    assert res.status_code in (401, 403)


def test_login_then_user_info(client):
    headers = auth_header(client, "wx_login_aaa111", "小测")
    res = client.get("/api/user/info", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["nickname"] == "小测"
    assert data["uid"].startswith("U")
    assert data["is_vip"] is False


def test_create_vip_order_with_empty_related_id(client):
    headers = auth_header(client, "wx_order_bbb222")
    res = client.post(
        "/api/orders",
        headers=headers,
        json={"product_type": "vip_year", "target_uid": "", "related_complaint_id": ""},
    )
    assert res.status_code == 200, res.text
    data = res.json()["data"]
    assert data["product_type"] == "vip_year"
    assert data["amount"] == 399.0
    assert data["pay_status"] == "pending"
    assert data["order_id"].startswith("O")


def test_pay_vip_order_grants_query_count(client):
    headers = auth_header(client, "wx_pay_ccc333")
    created = client.post(
        "/api/orders",
        headers=headers,
        json={"product_type": "vip_year"},
    )
    order_id = created.json()["data"]["order_id"]
    paid = client.post(f"/api/orders/{order_id}/pay", headers=headers)
    assert paid.status_code == 200, paid.text
    assert paid.json()["data"]["pay_status"] == "success"

    count = client.get("/api/user/query-count", headers=headers)
    data = count.json()["data"]
    assert data["is_vip"] is True
    assert data["vip_count"] == 80
    assert data["can_query"] is True


def test_free_user_cannot_search(client):
    headers = auth_header(client, "wx_free_ddd444")
    res = client.post("/api/query/search", headers=headers, json={"target_uid": "1234566"})
    assert res.status_code == 403


def test_vip_user_can_search_even_if_no_records(client):
    headers = auth_header(client, "wx_vip_eee555")
    created = client.post("/api/orders", headers=headers, json={"product_type": "vip_year"})
    client.post(f"/api/orders/{created.json()['data']['order_id']}/pay", headers=headers)

    res = client.post("/api/query/search", headers=headers, json={"target_uid": "nobody_999"})
    assert res.status_code == 200, res.text
    body = res.json()["data"]
    assert body["target"]["found"] is False
    assert body["target"]["target_uid"] == "nobody_999"
    assert body["cost_type"] == "vip"
