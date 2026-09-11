# routers/order.py - 订单支付路由
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from database import get_db
from models import User, Order, SingleQueryUnlock
from schemas import OrderRequest, ApiResponse
from auth import get_current_user, generate_order_no
from config import VIP_YEAR_DAYS, VIP_QUERY_COUNT

router = APIRouter(prefix="/api/orders", tags=["订单支付"])

def fmt(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else None

@router.post("")
async def create_order(req: OrderRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    order_id = generate_order_no("O")
    while db.query(Order).filter(Order.order_id == order_id).first():
        order_id = generate_order_no("O")
    pt = req.product_type
    if pt == "vip_year": amount, name, days = 399.0, "VIP年卡", VIP_YEAR_DAYS
    elif pt == "single_query": amount, name, days = 9.9, "单次查询解锁", 0
    elif pt == "dispute_service": amount, name, days = 299.0, "提起异议服务", 0
    elif pt == "contact_service": amount, name, days = 299.0, "联系处理服务", 0
    else: raise HTTPException(status_code=400, detail="未知的产品类型")
    o = Order(order_id=order_id, user_id=user.id, product_type=pt, product_name=name, amount=amount,
              pay_status="pending", vip_duration_days=days, single_query_target_uid=req.target_uid or "",
              related_complaint_id=req.related_complaint_id,
              service_status="pending" if pt in ["dispute_service", "contact_service"] else None)
    db.add(o)
    db.commit()
    db.refresh(o)
    return ApiResponse(data={"order_id": o.order_id, "id": o.id, "product_type": o.product_type,
                             "product_name": o.product_name, "amount": o.amount, "pay_status": o.pay_status,
                             "created_at": fmt(o.created_at)})

@router.post("/{order_id}/pay")
async def pay_order(order_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    o = db.query(Order).filter(Order.order_id == order_id, Order.user_id == user.id).first()
    if not o: raise HTTPException(status_code=404, detail="订单不存在")
    if o.pay_status == "success":
        return ApiResponse(data={"pay_status": "success", "message": "订单已支付"})
    o.pay_status = "success"
    o.pay_time = datetime.utcnow()
    if o.product_type == "vip_year":
        if user.is_vip and user.vip_expire_at and user.vip_expire_at > datetime.utcnow():
            user.vip_expire_at = user.vip_expire_at + timedelta(days=o.vip_duration_days)
        else:
            user.vip_expire_at = datetime.utcnow() + timedelta(days=o.vip_duration_days)
        user.is_vip = True
        user.vip_query_count = user.vip_query_count + VIP_QUERY_COUNT
    elif o.product_type == "single_query" and o.single_query_target_uid:
        unlock = SingleQueryUnlock(user_id=user.id, target_uid=o.single_query_target_uid,
                                   order_id=o.order_id, expire_at=datetime.utcnow() + timedelta(days=7))
        db.add(unlock)
    elif o.product_type in ["dispute_service", "contact_service"]:
        o.service_status = "processing"
    db.commit()
    db.refresh(o)
    return ApiResponse(data={"order_id": o.order_id, "pay_status": o.pay_status, "pay_time": fmt(o.pay_time),
                             "message": "支付成功，权益已发放"})

@router.get("")
async def get_order_list(page: int = 1, page_size: int = 20, product_type: str = "",
                         db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    offset = (page - 1) * page_size
    query = db.query(Order).filter(Order.user_id == user.id)
    if product_type:
        if product_type == "vip": query = query.filter(Order.product_type.like("vip_%"))
        else: query = query.filter(Order.product_type == product_type)
    orders = query.order_by(Order.created_at.desc()).offset(offset).limit(page_size).all()
    list_data = [{"id": o.id, "order_id": o.order_id, "order_no": o.order_id, "product_type": o.product_type,
                  "product_name": o.product_name, "amount": o.amount, "pay_status": o.pay_status,
                  "pay_time": fmt(o.pay_time), "vip_duration_days": o.vip_duration_days,
                  "single_query_target_uid": o.single_query_target_uid, "related_complaint_id": o.related_complaint_id,
                  "service_status": o.service_status, "created_at": fmt(o.created_at)} for o in orders]
    return ApiResponse(data={"list": list_data, "total": len(list_data), "page": page, "page_size": page_size})
