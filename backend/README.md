# 风险查询小程序 - 后端服务 & 后台管理系统

基于 Python + FastAPI 开发的微信小程序后端服务，包含完整的后台管理系统（admin.html）。

## 项目结构

```
backend/
├── main.py              # 应用入口
├── config.py            # 配置（数据库/JWT/微信/VIP/管理员账号）
├── database.py          # 数据库连接与会话
├── models.py            # SQLAlchemy 数据模型（8张表）
├── schemas.py           # Pydantic 请求/响应模型
├── auth.py              # JWT认证、微信登录、工具函数
├── admin.html           # 后台管理系统（单文件HTML，直接打开可用）
├── requirements.txt     # Python依赖
├── README.md            # 说明文档
└── routers/
    ├── auth.py          # 小程序用户认证路由
    ├── user.py          # 小程序用户路由
    ├── query.py         # 对象查询、风险评估、查询历史
    ├── complaint.py     # 材料提交与详情
    ├── photo.py         # 照片匹配
    ├── order.py         # 订单与支付
    ├── vip.py           # VIP套餐
    ├── service.py       # 维权服务（异议/联系）
    └── admin.py         # 后台管理API（管理员登录+所有管理接口）
```

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 启动后端服务

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

启动后访问：
- API文档（Swagger）: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

### 3. 打开后台管理系统

直接用浏览器打开 `admin.html` 文件即可使用。

**默认管理员账号**：
- 账号：`admin`
- 密码：`admin123`

> 可通过环境变量 `ADMIN_USERNAME` 和 `ADMIN_PASSWORD` 修改。

### 4. 小程序前端对接

修改前端 `utils/request.js` 中的 `BASE_URL`：
```javascript
const BASE_URL = 'http://localhost:8000'
```

## 后台管理系统功能

### 📊 数据概览（仪表盘）
- 总用户数、VIP用户数、材料总数、查询总次数、订单总数、总收入
- 近7天新增数据统计
- 近7天数据趋势图表（用户/材料/订单）
- 待处理异议、待处理联系快捷入口
- 侧边栏实时显示待审核数量角标

### 👥 用户管理
- 用户列表（支持按UID/昵称搜索、按VIP状态筛选）
- 用户详情（基本信息、VIP信息、材料数、查询数、订单数、累计消费）
- 开通/取消VIP（开通默认365天+80次查询次数）
- 分页展示

### 📋 材料审核
- 材料列表（支持按状态筛选、按UID/平台搜索）
- 材料详情（平台、对象UID、说明、人物照片、账号截图、证据图片、提交用户信息）
- 审核操作：受理（处理中）、通过（处理完毕）、驳回（已驳回）
- 待审核数量角标实时提醒

### 💰 订单管理
- 订单列表（支持按支付状态、产品类型筛选）
- 订单详情：订单号、产品名称、金额、支付状态、用户信息、关联信息、支付时间
- 产品类型：VIP年卡、单次查询、异议服务、联系服务

### 🔍 查询记录
- 所有用户的查询历史记录
- 支持按UID/平台搜索
- 显示风险等级、查询类型、扣费类型、查询用户

### ⚖️ 异议服务
- 异议服务列表（支持按状态筛选）
- 异议原因、联系方式、提交用户
- 操作：开始处理、标记完成
- 待处理数量角标

### 💬 联系服务
- 联系服务列表（支持按状态筛选）
- 留言内容、联系方式、提交用户
- 操作：开始处理、标记完成
- 待处理数量角标

## 小程序端 API 接口

### 认证 `/api/auth`
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/auth/login | 微信登录 |
| POST | /api/auth/privacy | 同意隐私协议 |

### 用户 `/api/user`
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/user/info | 获取用户信息 |
| POST | /api/user/update | 更新昵称/头像 |
| GET | /api/user/query-count | 获取查询次数 |

### 查询 `/api/query`
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/query/search | 搜索对象（扣次数） |
| POST | /api/query/check-unlock | 检查单次解锁 |
| GET | /api/query/history | 查询历史 |

### 材料 `/api/complaint`
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/complaint | 提交材料 |
| GET | /api/complaint/list | 我的材料列表 |
| GET | /api/complaint/{id} | 材料详情 |
| POST | /api/complaint/{id}/contact | 更新允许联系 |

### 其他
- POST /api/photo/match - 照片匹配
- GET /api/vip/plans - VIP套餐
- POST /api/orders - 创建订单
- POST /api/orders/{id}/pay - 支付订单
- GET /api/orders - 订单列表
- POST /api/service/dispute - 提交异议
- POST /api/service/contact - 提交联系

## 后台管理 API `/api/admin`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/admin/login | 管理员登录 |
| GET | /api/admin/dashboard | 仪表盘统计数据 |
| GET | /api/admin/users | 用户列表 |
| GET | /api/admin/users/{id} | 用户详情 |
| POST | /api/admin/users/{id}/vip | 设置/取消VIP |
| GET | /api/admin/complaints | 材料列表 |
| GET | /api/admin/complaints/{id} | 材料详情 |
| POST | /api/admin/complaints/{id}/review | 审核材料 |
| GET | /api/admin/orders | 订单列表 |
| GET | /api/admin/query-history | 查询记录 |
| GET | /api/admin/disputes | 异议服务列表 |
| POST | /api/admin/disputes/{id}/handle | 处理异议 |
| GET | /api/admin/contacts | 联系服务列表 |
| POST | /api/admin/contacts/{id}/handle | 处理联系 |

## 配置说明

在 `config.py` 中配置，或通过环境变量覆盖：

| 配置项 | 环境变量 | 默认值 | 说明 |
|--------|----------|--------|------|
| 数据库 | DATABASE_URL | sqlite:///./app.db | 生产建议MySQL |
| JWT密钥 | SECRET_KEY | your-secret-key-... | **生产必须修改** |
| 管理员账号 | ADMIN_USERNAME | admin | 后台登录账号 |
| 管理员密码 | ADMIN_PASSWORD | admin123 | 后台登录密码 |
| 微信AppID | WECHAT_APPID | your-wechat-appid | 小程序AppID |
| 微信Secret | WECHAT_SECRET | your-wechat-secret | 小程序Secret |
| VIP年卡价格 | - | 399.0 | 年卡价格 |
| VIP查询次数 | - | 80 | 年卡总次数(50+赠30) |

## 核心业务逻辑

### 风险等级
- 累计材料≥3 → 高风险
- 累计材料≥1 → 中风险
- 累计材料=1 → 低风险
- 无材料 → 暂无数据

### 查询扣次
- VIP用户扣1次，同一UID 24小时内不重复扣
- 单次解锁用户不扣VIP次数（7天有效）
- 免费用户拒绝查询

### VIP开通
- 支付成功后 is_vip=true，有效期+365天，查询次数+80
- 已有VIP则续期，次数累加

## 生产部署建议

1. 数据库切换为MySQL/PostgreSQL
2. 修改 SECRET_KEY 为强随机字符串
3. 修改管理员默认密码
4. 填入真实微信AppID/Secret
5. 替换模拟支付为真实微信支付
6. 图片上传接入云存储
7. 照片匹配接入人脸识别API
8. 使用HTTPS
9. 用 gunicorn/uvicorn 生产模式部署

## 版本

v1.5.0
- 完整后端API（小程序端）
- 完整后台管理系统（admin.html）
- VIP年仅卡模式（399元/80次）
- 8张数据表，20+ API接口
