# auth.py - JWT认证与微信登录
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import get_db
from models import User
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, WECHAT_APPID, WECHAT_SECRET
import httpx
import random

security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> Optional[int]:
    try:
        # verify_sub=False: 用户ID是整数，不强制sub为字符串
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_sub": False})
        user_id = payload.get("sub")
        if user_id is None:
            return None
        return int(user_id)
    except (JWTError, ValueError, TypeError):
        return None

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    token = credentials.credentials
    user_id = verify_token(token)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的登录凭证")
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")
    return user

def generate_uid() -> str:
    num = random.randint(10000000, 99999999)
    return f"U{num}"

def generate_order_no(prefix: str = "W") -> str:
    now = datetime.now()
    date_str = now.strftime("%Y%m%d")
    rand = random.randint(1000, 9999)
    return f"{prefix}{date_str}{rand}"

async def wechat_code2session(code: str) -> dict:
    if WECHAT_APPID == "your-wechat-appid" or not code:
        return {"openid": f"dev_openid_{code[-6:] if code else '000000'}", "session_key": "dev_session"}
    url = "https://api.weixin.qq.com/sns/jscode2session"
    params = {"appid": WECHAT_APPID, "secret": WECHAT_SECRET, "js_code": code, "grant_type": "authorization_code"}
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params)
        data = resp.json()
    if "openid" not in data:
        raise HTTPException(status_code=400, detail=f"微信登录失败: {data.get('errmsg', '未知错误')}")
    return data
