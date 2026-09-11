# routers/complaint.py - 材料路由
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json
from database import get_db
from models import User, Complaint
from schemas import ComplaintRequest, ContactUpdateRequest, ApiResponse
from auth import get_current_user, generate_order_no

router = APIRouter(prefix="/api/complaint", tags=["材料提交"])

def fmt(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else None

@router.post("")
async def create_complaint(req: ComplaintRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not req.platform: raise HTTPException(status_code=400, detail="平台不能为空")
    if not req.target_uid: raise HTTPException(status_code=400, detail="相关对象UID不能为空")
    if not req.account_screenshots: raise HTTPException(status_code=400, detail="请上传相关对象平台帐号截图")
    if not req.evidence_images: raise HTTPException(status_code=400, detail="请上传证据照片")
    order_no = generate_order_no("W")
    while db.query(Complaint).filter(Complaint.order_no == order_no).first():
        order_no = generate_order_no("W")
    c = Complaint(order_no=order_no, user_id=user.id, platform=req.platform, target_uid=req.target_uid,
                  person_photos=json.dumps(req.person_photos, ensure_ascii=False),
                  account_screenshots=json.dumps(req.account_screenshots, ensure_ascii=False),
                  evidence_images=json.dumps(req.evidence_images, ensure_ascii=False),
                  description=req.description, allow_contact=req.allow_contact,
                  allow_staff_contact=req.allow_staff_contact, agree_joint_rights=req.agree_joint_rights,
                  status="待处理")
    db.add(c)
    db.commit()
    db.refresh(c)
    return ApiResponse(data={"id": c.id, "order_no": c.order_no, "status": c.status, "created_at": fmt(c.created_at)})

@router.get("/list")
async def get_complaint_list(page: int = 1, page_size: int = 20, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    offset = (page - 1) * page_size
    complaints = db.query(Complaint).filter(Complaint.user_id == user.id).order_by(
        Complaint.created_at.desc()).offset(offset).limit(page_size).all()
    def parse(s):
        try: return json.loads(s) if s else []
        except: return []
    list_data = [{"id": c.id, "order_no": c.order_no, "platform": c.platform, "target_uid": c.target_uid,
                  "person_photos": parse(c.person_photos), "account_screenshots": parse(c.account_screenshots),
                  "evidence_images": parse(c.evidence_images), "description": c.description,
                  "allow_contact": c.allow_contact, "allow_staff_contact": c.allow_staff_contact,
                  "agree_joint_rights": c.agree_joint_rights, "status": c.status, "created_at": fmt(c.created_at)}
                 for c in complaints]
    return ApiResponse(data={"list": list_data, "total": len(list_data), "page": page, "page_size": page_size})

@router.get("/{complaint_id}")
async def get_complaint_detail(complaint_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    c = db.query(Complaint).filter(Complaint.id == complaint_id, Complaint.user_id == user.id).first()
    if not c: raise HTTPException(status_code=404, detail="材料不存在")
    def parse(s):
        try: return json.loads(s) if s else []
        except: return []
    return ApiResponse(data={"id": c.id, "order_no": c.order_no, "platform": c.platform, "target_uid": c.target_uid,
        "person_photos": parse(c.person_photos), "account_screenshots": parse(c.account_screenshots),
        "evidence_images": parse(c.evidence_images), "description": c.description,
        "allow_contact": c.allow_contact, "allow_staff_contact": c.allow_staff_contact,
        "agree_joint_rights": c.agree_joint_rights, "status": c.status, "created_at": fmt(c.created_at)})

@router.post("/{complaint_id}/contact")
async def update_contact(complaint_id: int, req: ContactUpdateRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    c = db.query(Complaint).filter(Complaint.id == complaint_id, Complaint.user_id == user.id).first()
    if not c: raise HTTPException(status_code=404, detail="材料不存在")
    c.allow_contact = req.allow_contact
    db.commit()
    return ApiResponse(data={"allow_contact": c.allow_contact})
