# schemas.py - Pydantic 请求/响应模型
from pydantic import BaseModel, field_validator
from typing import Optional, List, Union
from datetime import datetime

class ApiResponse(BaseModel):
    code: int = 0
    message: str = "success"
    # VIP 套餐等接口返回 list；其余接口返回 dict
    data: Optional[Union[dict, list]] = None

class LoginRequest(BaseModel):
    code: str
    nickname: str = "查崩崩用户"
    avatar: str = ""

class PrivacyRequest(BaseModel):
    agreed: bool = True

class UserUpdateRequest(BaseModel):
    nickname: Optional[str] = None
    avatar: Optional[str] = None

class SearchRequest(BaseModel):
    target_uid: str

class CheckUnlockRequest(BaseModel):
    target_uid: str

class ComplaintRequest(BaseModel):
    platform: str
    target_uid: str
    person_photos: List[str] = []
    account_screenshots: List[str] = []
    evidence_images: List[str] = []
    description: str = ""
    allow_contact: bool = False
    allow_staff_contact: bool = False
    agree_joint_rights: bool = False

class ContactUpdateRequest(BaseModel):
    allow_contact: bool

class PhotoMatchRequest(BaseModel):
    image_url: str

class OrderRequest(BaseModel):
    product_type: str
    target_uid: str = ""
    related_complaint_id: Optional[int] = None

    @field_validator("related_complaint_id", mode="before")
    @classmethod
    def empty_related_id_to_none(cls, v):
        # 前端在没有关联材料时会传 ""，空字符串不是合法 int
        if v == "":
            return None
        return v

class DisputeRequest(BaseModel):
    complaint_id: int
    reason: str = ""
    contact_info: str = ""

class ContactRequest(BaseModel):
    complaint_id: int
    message: str = ""
    contact_info: str = ""

class UploadBase64Request(BaseModel):
    content_base64: str
    filename: str = "image"

    @field_validator("content_base64", mode="before")
    @classmethod
    def strip_data_url(cls, v):
        if not isinstance(v, str):
            return v
        s = v.strip().replace("\n", "").replace(" ", "")
        if s.lower().startswith("data:") and "," in s:
            s = s.split(",", 1)[1]
        return s
