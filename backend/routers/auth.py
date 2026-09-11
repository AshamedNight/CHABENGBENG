# routers/auth.py - 认证路由
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import User
from schemas import LoginRequest, PrivacyRequest, ApiResponse
from auth import create_access_token, generate_uid, wechat_code2session, get_current_user

router = APIRouter(prefix="/api/auth", tags=["认证"])

@router.post("/login")
async def login(req: LoginRequest, db: Session = Depends(get_db)):
    wx_data = await wechat_code2session(req.code)
    openid = wx_data["openid"]
    user = db.query(User).filter(User.openid == openid).first()
    if not user:
        uid = generate_uid()
        while db.query(User).filter(User.uid == uid).first():
            uid = generate_uid()
        user = User(uid=uid, openid=openid, nickname=req.nickname or "查崩崩用户", avatar=req.avatar or "")
        db.add(user)
        db.commit()
        db.refresh(user)
    token = create_access_token({"sub": user.id})
    return ApiResponse(data={"token": token, "user_id": user.id})

@router.post("/privacy")
async def agree_privacy(req: PrivacyRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    user.privacy_agreed = req.agreed
    db.commit()
    return ApiResponse(data={"agreed": user.privacy_agreed})
