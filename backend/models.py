# models.py - SQLAlchemy 数据模型
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    """用户表"""
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    uid = Column(String(20), unique=True, index=True, nullable=False)
    openid = Column(String(100), unique=True, index=True)
    nickname = Column(String(50), default="查崩崩用户")
    avatar = Column(String(500), default="")
    is_vip = Column(Boolean, default=False)
    vip_expire_at = Column(DateTime, nullable=True)
    vip_query_count = Column(Integer, default=0)
    privacy_agreed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    complaints = relationship("Complaint", back_populates="user")
    orders = relationship("Order", back_populates="user")
    query_history = relationship("QueryHistory", back_populates="user")

class Complaint(Base):
    """材料提交表"""
    __tablename__ = "complaints"
    id = Column(Integer, primary_key=True, index=True)
    order_no = Column(String(30), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    platform = Column(String(50), nullable=False)
    target_uid = Column(String(100), nullable=False, index=True)
    person_photos = Column(Text, default="[]")
    account_screenshots = Column(Text, default="[]")
    evidence_images = Column(Text, default="[]")
    description = Column(Text, default="")
    allow_contact = Column(Boolean, default=False)
    allow_staff_contact = Column(Boolean, default=False)
    agree_joint_rights = Column(Boolean, default=False)
    status = Column(String(20), default="待处理")
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="complaints")

class QueryHistory(Base):
    """查询历史表"""
    __tablename__ = "query_history"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    target_uid = Column(String(100), nullable=False, index=True)
    platform = Column(String(50), default="未知")
    risk_level = Column(String(20), default="none")
    query_type = Column(String(20), default="uid")
    cost_type = Column(String(20), default="vip")
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="query_history")

class Order(Base):
    """订单表"""
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String(50), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    product_type = Column(String(50), nullable=False)
    product_name = Column(String(100), default="")
    amount = Column(Float, default=0.0)
    pay_status = Column(String(20), default="pending")
    pay_time = Column(DateTime, nullable=True)
    vip_duration_days = Column(Integer, default=0)
    single_query_target_uid = Column(String(100), default="")
    related_complaint_id = Column(Integer, nullable=True)
    service_status = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="orders")

class SingleQueryUnlock(Base):
    """单次查询解锁记录表"""
    __tablename__ = "single_query_unlocks"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    target_uid = Column(String(100), index=True)
    order_id = Column(String(50), default="")
    expire_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class DisputeService(Base):
    """提起异议服务表"""
    __tablename__ = "dispute_services"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    complaint_id = Column(Integer, index=True)
    reason = Column(Text, default="")
    contact_info = Column(String(200), default="")
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)

class ContactService(Base):
    """联系处理服务表"""
    __tablename__ = "contact_services"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    complaint_id = Column(Integer, index=True)
    message = Column(Text, default="")
    contact_info = Column(String(200), default="")
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
