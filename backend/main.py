# main.py - FastAPI 应用入口
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from routers import auth, user, query, complaint, photo, order, vip, service, admin, upload
from config import UPLOAD_DIR

app = FastAPI(
    title="风险查询小程序后端 API",
    description="基于FastAPI的微信小程序后端服务，含后台管理API",
    version="1.5.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(query.router)
app.include_router(complaint.router)
app.include_router(photo.router)
app.include_router(order.router)
app.include_router(vip.router)
app.include_router(service.router)
app.include_router(admin.router)
app.include_router(upload.router)

@app.on_event("startup")
async def startup_event():
    Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    init_db()
    print("数据库初始化完成")

@app.get("/")
async def root():
    return {"code": 0, "message": "API服务运行中", "version": "1.5.0"}

@app.get("/health")
async def health():
    return {"status": "ok"}
