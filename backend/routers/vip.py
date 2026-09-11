# routers/vip.py - VIP套餐路由
from fastapi import APIRouter
from schemas import ApiResponse
from config import VIP_YEAR_PRICE, VIP_YEAR_DAYS, VIP_QUERY_COUNT

router = APIRouter(prefix="/api/vip", tags=["VIP"])

@router.get("/plans")
async def get_vip_plans():
    return ApiResponse(data=[{
        "type": "vip_year", "name": "VIP年卡", "price": VIP_YEAR_PRICE, "days": VIP_YEAR_DAYS,
        "original_price": 598.8, "badge": "限时特惠", "query_count": VIP_QUERY_COUNT,
        "gift_count": 30, "base_count": 50, "description": "充50次送30次，共80次查询"
    }])
