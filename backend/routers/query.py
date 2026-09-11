# routers/query.py - 查询路由
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json
from database import get_db
from models import User, Complaint, QueryHistory, SingleQueryUnlock
from schemas import SearchRequest, CheckUnlockRequest, ApiResponse
from auth import get_current_user
from config import RISK_HIGH_THRESHOLD, RISK_MEDIUM_THRESHOLD

router = APIRouter(prefix="/api/query", tags=["查询"])

def fmt(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else None

def calc_risk(count):
    if count >= RISK_HIGH_THRESHOLD: return "high"
    if count >= RISK_MEDIUM_THRESHOLD: return "medium"
    if count > 0: return "low"
    return "none"

@router.post("/search")
async def search_target(req: SearchRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    target_uid = req.target_uid.strip()
    if not target_uid:
        raise HTTPException(status_code=400, detail="目标UID不能为空")
    unlocked = db.query(SingleQueryUnlock).filter(
        SingleQueryUnlock.user_id == user.id, SingleQueryUnlock.target_uid == target_uid,
        SingleQueryUnlock.expire_at > datetime.utcnow()
    ).first()
    is_unlocked = unlocked is not None
    cost_type = "free"
    if not is_unlocked:
        if not user.is_vip or user.vip_query_count <= 0:
            raise HTTPException(status_code=403, detail="查询次数不足，请开通VIP或购买单次查询")
        recent = db.query(QueryHistory).filter(
            QueryHistory.user_id == user.id, QueryHistory.target_uid == target_uid,
            QueryHistory.created_at > datetime.utcnow() - timedelta(hours=24)
        ).first()
        if not recent:
            user.vip_query_count -= 1
            db.commit()
        cost_type = "vip"
    else:
        cost_type = "single"

    complaints = db.query(Complaint).filter(
        Complaint.target_uid == target_uid, Complaint.status != "已驳回"
    ).order_by(Complaint.created_at.desc()).all()
    count = len(complaints)
    risk = calc_risk(count)
    platform = complaints[0].platform if complaints else "未知"
    photos = []
    for c in complaints:
        try: photos.extend(json.loads(c.person_photos) if c.person_photos else [])
        except: pass
    photos = list(set(photos))[:4]
    records = []
    for c in complaints:
        try: ev = json.loads(c.evidence_images) if c.evidence_images else []
        except: ev = []
        records.append({
            "id": c.id, "order_no": c.order_no,
            "user_nickname": c.user.nickname if c.user else "匿名用户",
            "allow_contact": c.allow_contact, "created_at": fmt(c.created_at),
            "evidence_images": ev, "status": c.status
        })
    history = QueryHistory(user_id=user.id, target_uid=target_uid, platform=platform,
                           risk_level=risk, query_type="uid", cost_type=cost_type)
    db.add(history)
    db.commit()
    found = count > 0
    return ApiResponse(data={
        "target": {"found": found, "target_uid": target_uid, "platform": platform,
                   "complaint_count": count, "risk_level": risk,
                   "status": "已收录" if found else "未收录",
                   "person_photos": photos, "records": records},
        "cost_type": cost_type,
        "cost_message": "VIP查询" if cost_type == "vip" else ("单次解锁" if cost_type == "single" else "免费"),
        "is_unlocked": is_unlocked
    })

@router.post("/check-unlock")
async def check_unlock(req: CheckUnlockRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    unlocked = db.query(SingleQueryUnlock).filter(
        SingleQueryUnlock.user_id == user.id, SingleQueryUnlock.target_uid == req.target_uid,
        SingleQueryUnlock.expire_at > datetime.utcnow()
    ).first()
    return ApiResponse(data={"unlocked": unlocked is not None})

@router.get("/history")
async def get_query_history(page: int = 1, page_size: int = 50, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    offset = (page - 1) * page_size
    history = db.query(QueryHistory).filter(QueryHistory.user_id == user.id).order_by(
        QueryHistory.created_at.desc()).offset(offset).limit(page_size).all()
    list_data = [{"id": h.id, "target_uid": h.target_uid, "platform": h.platform,
                  "risk_level": h.risk_level, "query_type": h.query_type,
                  "cost_type": h.cost_type, "created_at": fmt(h.created_at)} for h in history]
    return ApiResponse(data={"list": list_data, "total": len(list_data), "page": page, "page_size": page_size})
