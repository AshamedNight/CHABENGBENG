# config.py - 应用配置
import os

# 密钥放 backend/.env（不提交、不外发），格式见 .env.example
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except ImportError:
    pass

# 数据库
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

# JWT
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production-2024")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 30  # 30天

# 管理员账号
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# 微信小程序
WECHAT_APPID = os.getenv("WECHAT_APPID", "your-wechat-appid")
WECHAT_SECRET = os.getenv("WECHAT_SECRET", "your-wechat-secret")

# 图片上传（只存本机 uploads 目录，不走云存储）
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.getenv("UPLOAD_DIR", os.path.join(BACKEND_DIR, "uploads"))
MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5MB
ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
# 返回给前端/后台的完整网址；服务本身仍只绑 127.0.0.1
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000")

# VIP配置
VIP_YEAR_PRICE = 399.0
VIP_YEAR_DAYS = 365
VIP_QUERY_COUNT = 80  # 年卡总查询次数（50+赠30）
SINGLE_QUERY_PRICE = 9.9
DISPUTE_SERVICE_PRICE = 299.0
CONTACT_SERVICE_PRICE = 299.0

# 风险等级阈值
RISK_HIGH_THRESHOLD = 3   # 累计>=3条记录为高风险
RISK_MEDIUM_THRESHOLD = 1 # 累计>=1条记录为中风险
