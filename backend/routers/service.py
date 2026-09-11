# routers/service.py - 维权服务路由
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from database import get_db
from models import User, Complaint, DisputeService, ContactService
from schemas import DisputeRequest, ContactRequest, ApiResponse
from auth import get_current_user

router = APIRouter(prefix="/api/service", tags=["维权服务"])

def fmt(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else None

@router.post("/dispute")
async def submit_dispute(req: DisputeRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    c = db.query(Complaint).filter(Complaint.id == req.complaint_id).first()
    if not c: raise HTTPException(status_code=404, detail="关联材料不存在")
    d = DisputeService(user_id=user.id, complaint_id=req.complaint_id, reason=req.reason,
                       contact_info=req.contact_info, status="pending")
    db.add(d)
    db.commit()
    db.refresh(d)
    return ApiResponse(data={"id": d.id, "complaint_id": d.complaint_id, "status": d.status,
                             "created_at": fmt(d.created_at), "message": "异议已提交，专业团队将在24小时内联系您"})

@router.post("/contact")
async def submit_contact(req: ContactRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    c = db.query(Complaint).filter(Complaint.id == req.complaint_id).first()
    if not c: raise HTTPException(status_code=404, detail="关联材料不存在")
    ct = ContactService(user_id=user.id, complaint_id=req.complaint_id, message=req.message,
                        contact_info=req.contact_info, status="pending")
    db.add(ct)
    db.commit()
    db.refresh(ct)
    return ApiResponse(data={"id": ct.id, "complaint_id": ct.complaint_id, "status": ct.status,
                             "created_at": fmt(ct.created_at), "message": "联系请求已提交，处理人员将尽快与您对接"})
