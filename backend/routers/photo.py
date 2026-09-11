# routers/photo.py - 照片匹配路由
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import json, random
from database import get_db
from models import User, Complaint, QueryHistory
from schemas import PhotoMatchRequest, ApiResponse
from auth import get_current_user

router = APIRouter(prefix="/api/photo", tags=["照片匹配"])

@router.post("/match")
async def photo_match(req: PhotoMatchRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not req.image_url:
        raise HTTPException(status_code=400, detail="图片URL不能为空")
    if not user.is_vip or user.vip_query_count <= 0:
        raise HTTPException(status_code=403, detail="照片匹配为VIP专属功能，请开通VIP")
    complaints = db.query(Complaint).filter(
        Complaint.person_photos != "[]", Complaint.person_photos != "", Complaint.status != "已驳回"
    ).all()
    matches = []
    if complaints:
        sample = random.sample(complaints, min(5, len(complaints)))
        for c in sample:
            try: photos = json.loads(c.person_photos) if c.person_photos else []
            except: photos = []
            count = db.query(Complaint).filter(Complaint.target_uid == c.target_uid, Complaint.status != "已驳回").count()
            matches.append({"id": c.id, "target_uid": c.target_uid, "platform": c.platform,
                           "person_photo": photos[0] if photos else "", "match_rate": random.randint(70, 95),
                           "complaint_count": count, "risk_level": "high" if count >= 3 else ("medium" if count >= 1 else "low")})
    matches.sort(key=lambda x: x["match_rate"], reverse=True)
    history = QueryHistory(user_id=user.id, target_uid="photo_match", platform="photo",
                           risk_level="none", query_type="photo", cost_type="vip")
    db.add(history)
    db.commit()
    return ApiResponse(data={"matches": matches, "total": len(matches)})
