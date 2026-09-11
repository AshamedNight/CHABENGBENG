# routers/user.py - 用户路由
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from database import get_db
from models import User
from schemas import UserUpdateRequest, ApiResponse
from auth import get_current_user

router = APIRouter(prefix="/api/user", tags=["用户"])

def fmt(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else None

@router.get("/info")
async def get_user_info(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return ApiResponse(data={
        "id": user.id, "uid": user.uid, "nickname": user.nickname, "avatar": user.avatar,
        "is_vip": user.is_vip, "vip_expire_at": fmt(user.vip_expire_at),
        "vip_query_count": user.vip_query_count, "privacy_agreed": user.privacy_agreed,
        "created_at": fmt(user.created_at)
    })

@router.post("/update")
async def update_user_info(req: UserUpdateRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if req.nickname is not None: user.nickname = req.nickname
    if req.avatar is not None: user.avatar = req.avatar
    db.commit()
    return ApiResponse(data={"id": user.id, "uid": user.uid, "nickname": user.nickname, "avatar": user.avatar})

@router.get("/query-count")
async def get_query_count(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.is_vip and user.vip_expire_at and user.vip_expire_at < datetime.utcnow():
        user.is_vip = False
        user.vip_query_count = 0
        db.commit()
    return ApiResponse(data={
        "is_vip": user.is_vip, "vip_expire_at": fmt(user.vip_expire_at),
        "vip_count": user.vip_query_count,
        "has_vip_count": user.is_vip and user.vip_query_count > 0,
        "can_query": user.is_vip and user.vip_query_count > 0
    })
