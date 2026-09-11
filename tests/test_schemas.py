# tests/test_schemas.py
"""上一回合修过的契约，防止改别的东西时又改坏。"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from schemas import ApiResponse, OrderRequest  # noqa: E402
from pydantic import ValidationError


def test_api_response_accepts_list_for_vip_plans():
    obj = ApiResponse(data=[{"type": "vip_year", "price": 399.0}])
    assert isinstance(obj.data, list)
    assert obj.data[0]["type"] == "vip_year"


def test_api_response_still_accepts_dict_and_none():
    assert ApiResponse(data={"token": "abc"}).data["token"] == "abc"
    assert ApiResponse().data is None


def test_order_request_empty_string_related_id_becomes_none():
    obj = OrderRequest(product_type="vip_year", related_complaint_id="")
    assert obj.related_complaint_id is None


def test_order_request_numeric_related_id_still_works():
    obj = OrderRequest(product_type="dispute_service", related_complaint_id="7")
    assert obj.related_complaint_id == 7


def test_order_request_rejects_garbage_related_id():
    with pytest.raises(ValidationError):
        OrderRequest(product_type="vip_year", related_complaint_id="abc")
