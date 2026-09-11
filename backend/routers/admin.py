# routers/admin.py - 后台管理API路由
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
import json
from pydantic import BaseModel
from jose import JWTError, jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from database import get_db
from models import User, Complaint, QueryHistory, Order, DisputeService, ContactService
from schemas import ApiResponse
from config import ADMIN_USERNAME, ADMIN_PASSWORD, SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/api/admin", tags=["后台管理"])
security = HTTPBearer()

class AdminLoginRequest(BaseModel):
    username: str
    password: str

class SetVipRequest(BaseModel):
    is_vip: bool
    days: int = 365
    query_count: int = 80

class ReviewRequest(BaseModel):
    status: str
    remark: str = ""

class HandleRequest(BaseModel):
    status: str
    remark: str = ""

def create_admin_token(username):
    expire = datetime.utcnow() + timedelta(hours=12)
    return jwt.encode({"sub": username, "role": "admin", "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)

def verify_admin_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("role") == "admin"
    except JWTError:
        return False

async def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not verify_admin_token(credentials.credentials):
        raise HTTPException(status_code=401, detail="管理员登录已过期，请重新登录")
    return True

def fmt(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else None

# ===== 登录 =====
@router.post("/login")
async def admin_login(req: AdminLoginRequest):
    if req.username != ADMIN_USERNAME or req.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    return ApiResponse(data={"token": create_admin_token(req.username), "username": req.username})

# ===== 仪表盘 =====
@router.get("/dashboard")
async def dashboard(db: Session = Depends(get_db), admin: bool = Depends(get_current_admin)):
    total_users = db.query(func.count(User.id)).scalar()
    total_vip = db.query(func.count(User.id)).filter(User.is_vip == True).scalar()
    total_complaints = db.query(func.count(Complaint.id)).scalar()
    pending_complaints = db.query(func.count(Complaint.id)).filter(Complaint.status == "待处理").scalar()
    total_queries = db.query(func.count(QueryHistory.id)).scalar()
    total_orders = db.query(func.count(Order.id)).scalar()
    paid_orders = db.query(func.count(Order.id)).filter(Order.pay_status == "success").scalar()
    total_revenue = db.query(func.coalesce(func.sum(Order.amount), 0)).filter(Order.pay_status == "success").scalar()
    pending_disputes = db.query(func.count(DisputeService.id)).filter(DisputeService.status == "pending").scalar()
    pending_contacts = db.query(func.count(ContactService.id)).filter(ContactService.status == "pending").scalar()
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    new_users_7d = db.query(func.count(User.id)).filter(User.created_at >= seven_days_ago).scalar()
    new_complaints_7d = db.query(func.count(Complaint.id)).filter(Complaint.created_at >= seven_days_ago).scalar()
    new_orders_7d = db.query(func.count(Order.id)).filter(Order.created_at >= seven_days_ago).scalar()
    daily_data = []
    for i in range(6, -1, -1):
        ds = (datetime.utcnow() - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        de = ds + timedelta(days=1)
        du = db.query(func.count(User.id)).filter(User.created_at >= ds, User.created_at < de).scalar()
        dc = db.query(func.count(Complaint.id)).filter(Complaint.created_at >= ds, Complaint.created_at < de).scalar()
        do = db.query(func.count(Order.id)).filter(Order.created_at >= ds, Order.created_at < de).scalar()
        dr = db.query(func.coalesce(func.sum(Order.amount), 0)).filter(
            Order.pay_status == "success", Order.pay_time >= ds, Order.pay_time < de).scalar()
        daily_data.append({"date": ds.strftime("%m-%d"), "users": du, "complaints": dc, "orders": do, "revenue": round(dr, 2)})
    return ApiResponse(data={
        "total_users": total_users, "total_vip_users": total_vip, "total_complaints": total_complaints,
        "pending_complaints": pending_complaints, "total_queries": total_queries, "total_orders": total_orders,
        "paid_orders": paid_orders, "total_revenue": round(total_revenue, 2),
        "pending_disputes": pending_disputes, "pending_contacts": pending_contacts,
        "new_users_7d": new_users_7d, "new_complaints_7d": new_complaints_7d, "new_orders_7d": new_orders_7d,
        "daily_data": daily_data
    })

# ===== 用户管理 =====
@router.get("/users")
async def admin_users(page: int = 1, page_size: int = 20, keyword: str = "", is_vip: str = "",
                      db: Session = Depends(get_db), admin: bool = Depends(get_current_admin)):
    query = db.query(User)
    if keyword: query = query.filter((User.uid.like(f"%{keyword}%")) | (User.nickname.like(f"%{keyword}%")))
    if is_vip == "true": query = query.filter(User.is_vip == True)
    elif is_vip == "false": query = query.filter(User.is_vip == False)
    total = query.count()
    users = query.order_by(User.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    list_data = [{"id": u.id, "uid": u.uid, "nickname": u.nickname, "avatar": u.avatar, "is_vip": u.is_vip,
                  "vip_expire_at": fmt(u.vip_expire_at), "vip_query_count": u.vip_query_count,
                  "privacy_agreed": u.privacy_agreed, "created_at": fmt(u.created_at)} for u in users]
    return ApiResponse(data={"list": list_data, "total": total, "page": page, "page_size": page_size})

@router.get("/users/{user_id}")
async def admin_user_detail(user_id: int, db: Session = Depends(get_db), admin: bool = Depends(get_current_admin)):
    u = db.query(User).filter(User.id == user_id).first()
    if not u: raise HTTPException(status_code=404, detail="用户不存在")
    cc = db.query(func.count(Complaint.id)).filter(Complaint.user_id == user_id).scalar()
    qc = db.query(func.count(QueryHistory.id)).filter(QueryHistory.user_id == user_id).scalar()
    oc = db.query(func.count(Order.id)).filter(Order.user_id == user_id).scalar()
    ts = db.query(func.coalesce(func.sum(Order.amount), 0)).filter(Order.user_id == user_id, Order.pay_status == "success").scalar()
    return ApiResponse(data={"id": u.id, "uid": u.uid, "nickname": u.nickname, "avatar": u.avatar, "is_vip": u.is_vip,
        "vip_expire_at": fmt(u.vip_expire_at), "vip_query_count": u.vip_query_count, "privacy_agreed": u.privacy_agreed,
        "created_at": fmt(u.created_at), "complaint_count": cc, "query_count": qc, "order_count": oc, "total_spent": round(ts, 2)})

@router.post("/users/{user_id}/vip")
async def admin_set_vip(user_id: int, req: SetVipRequest, db: Session = Depends(get_db), admin: bool = Depends(get_current_admin)):
    u = db.query(User).filter(User.id == user_id).first()
    if not u: raise HTTPException(status_code=404, detail="用户不存在")
    if req.is_vip:
        u.is_vip = True
        if u.vip_expire_at and u.vip_expire_at > datetime.utcnow():
            u.vip_expire_at = u.vip_expire_at + timedelta(days=req.days)
        else:
            u.vip_expire_at = datetime.utcnow() + timedelta(days=req.days)
        u.vip_query_count = u.vip_query_count + req.query_count
    else:
        u.is_vip = False
        u.vip_query_count = 0
    db.commit()
    return ApiResponse(data={"is_vip": u.is_vip, "vip_expire_at": fmt(u.vip_expire_at), "vip_query_count": u.vip_query_count})

# ===== 材料审核 =====
@router.get("/complaints")
async def admin_complaints(page: int = 1, page_size: int = 20, status: str = "", keyword: str = "",
                           db: Session = Depends(get_db), admin: bool = Depends(get_current_admin)):
    query = db.query(Complaint)
    if status: query = query.filter(Complaint.status == status)
    if keyword: query = query.filter((Complaint.target_uid.like(f"%{keyword}%")) | (Complaint.platform.like(f"%{keyword}%")))
    total = query.count()
    complaints = query.order_by(Complaint.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    list_data = []
    for c in complaints:
        u = db.query(User).filter(User.id == c.user_id).first()
        list_data.append({"id": c.id, "order_no": c.order_no, "platform": c.platform, "target_uid": c.target_uid,
                          "description": c.description, "status": c.status, "allow_contact": c.allow_contact,
                          "user_nickname": u.nickname if u else "未知", "user_uid": u.uid if u else "", "created_at": fmt(c.created_at)})
    return ApiResponse(data={"list": list_data, "total": total, "page": page, "page_size": page_size})

@router.get("/complaints/{complaint_id}")
async def admin_complaint_detail(complaint_id: int, db: Session = Depends(get_db), admin: bool = Depends(get_current_admin)):
    c = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not c: raise HTTPException(status_code=404, detail="材料不存在")
    u = db.query(User).filter(User.id == c.user_id).first()
    def parse(s):
        try: return json.loads(s) if s else []
        except: return []
    return ApiResponse(data={"id": c.id, "order_no": c.order_no, "platform": c.platform, "target_uid": c.target_uid,
        "person_photos": parse(c.person_photos), "account_screenshots": parse(c.account_screenshots),
        "evidence_images": parse(c.evidence_images), "description": c.description,
        "allow_contact": c.allow_contact, "allow_staff_contact": c.allow_staff_contact,
        "agree_joint_rights": c.agree_joint_rights, "status": c.status, "created_at": fmt(c.created_at),
        "user": {"id": u.id if u else None, "uid": u.uid if u else "", "nickname": u.nickname if u else "未知"}})

@router.post("/complaints/{complaint_id}/review")
async def admin_review(complaint_id: int, req: ReviewRequest, db: Session = Depends(get_db), admin: bool = Depends(get_current_admin)):
    if req.status not in ["处理中", "处理完毕", "已驳回", "待处理"]:
        raise HTTPException(status_code=400, detail="无效的状态")
    c = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not c: raise HTTPException(status_code=404, detail="材料不存在")
    c.status = req.status
    db.commit()
    return ApiResponse(data={"id": c.id, "status": c.status})

# ===== 订单管理 =====
@router.get("/orders")
async def admin_orders(page: int = 1, page_size: int = 20, pay_status: str = "", product_type: str = "",
                       db: Session = Depends(get_db), admin: bool = Depends(get_current_admin)):
    query = db.query(Order)
    if pay_status: query = query.filter(Order.pay_status == pay_status)
    if product_type: query = query.filter(Order.product_type == product_type)
    total = query.count()
    orders = query.order_by(Order.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    list_data = []
    for o in orders:
        u = db.query(User).filter(User.id == o.user_id).first()
        list_data.append({"id": o.id, "order_id": o.order_id, "product_type": o.product_type, "product_name": o.product_name,
                          "amount": o.amount, "pay_status": o.pay_status, "pay_time": fmt(o.pay_time),
                          "vip_duration_days": o.vip_duration_days, "single_query_target_uid": o.single_query_target_uid,
                          "related_complaint_id": o.related_complaint_id, "service_status": o.service_status,
                          "user_nickname": u.nickname if u else "未知", "user_uid": u.uid if u else "", "created_at": fmt(o.created_at)})
    return ApiResponse(data={"list": list_data, "total": total, "page": page, "page_size": page_size})

# ===== 查询记录 =====
@router.get("/query-history")
async def admin_query_history(page: int = 1, page_size: int = 20, keyword: str = "",
                              db: Session = Depends(get_db), admin: bool = Depends(get_current_admin)):
    query = db.query(QueryHistory)
    if keyword: query = query.filter((QueryHistory.target_uid.like(f"%{keyword}%")) | (QueryHistory.platform.like(f"%{keyword}%")))
    total = query.count()
    history = query.order_by(QueryHistory.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    list_data = []
    for h in history:
        u = db.query(User).filter(User.id == h.user_id).first()
        list_data.append({"id": h.id, "target_uid": h.target_uid, "platform": h.platform, "risk_level": h.risk_level,
                          "query_type": h.query_type, "cost_type": h.cost_type,
                          "user_nickname": u.nickname if u else "未知", "user_uid": u.uid if u else "", "created_at": fmt(h.created_at)})
    return ApiResponse(data={"list": list_data, "total": total, "page": page, "page_size": page_size})

# ===== 维权服务 =====
@router.get("/disputes")
async def admin_disputes(page: int = 1, page_size: int = 20, status: str = "",
                         db: Session = Depends(get_db), admin: bool = Depends(get_current_admin)):
    query = db.query(DisputeService)
    if status: query = query.filter(DisputeService.status == status)
    total = query.count()
    disputes = query.order_by(DisputeService.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    list_data = []
    for d in disputes:
        u = db.query(User).filter(User.id == d.user_id).first()
        list_data.append({"id": d.id, "complaint_id": d.complaint_id, "reason": d.reason, "contact_info": d.contact_info,
                          "status": d.status, "user_nickname": u.nickname if u else "未知", "user_uid": u.uid if u else "",
                          "created_at": fmt(d.created_at)})
    return ApiResponse(data={"list": list_data, "total": total, "page": page, "page_size": page_size})

@router.post("/disputes/{dispute_id}/handle")
async def admin_handle_dispute(dispute_id: int, req: HandleRequest, db: Session = Depends(get_db), admin: bool = Depends(get_current_admin)):
    d = db.query(DisputeService).filter(DisputeService.id == dispute_id).first()
    if not d: raise HTTPException(status_code=404, detail="异议服务不存在")
    d.status = req.status
    db.commit()
    return ApiResponse(data={"id": d.id, "status": d.status})

@router.get("/contacts")
async def admin_contacts(page: int = 1, page_size: int = 20, status: str = "",
                         db: Session = Depends(get_db), admin: bool = Depends(get_current_admin)):
    query = db.query(ContactService)
    if status: query = query.filter(ContactService.status == status)
    total = query.count()
    contacts = query.order_by(ContactService.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    list_data = []
    for c in contacts:
        u = db.query(User).filter(User.id == c.user_id).first()
        list_data.append({"id": c.id, "complaint_id": c.complaint_id, "message": c.message, "contact_info": c.contact_info,
                          "status": c.status, "user_nickname": u.nickname if u else "未知", "user_uid": u.uid if u else "",
                          "created_at": fmt(c.created_at)})
    return ApiResponse(data={"list": list_data, "total": total, "page": page, "page_size": page_size})

@router.post("/contacts/{contact_id}/handle")
async def admin_handle_contact(contact_id: int, req: HandleRequest, db: Session = Depends(get_db), admin: bool = Depends(get_current_admin)):
    c = db.query(ContactService).filter(ContactService.id == contact_id).first()
    if not c: raise HTTPException(status_code=404, detail="联系服务不存在")
    c.status = req.status
    db.commit()
    return ApiResponse(data={"id": c.id, "status": c.status})
