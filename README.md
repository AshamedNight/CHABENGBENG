# 查崩崩 —— 风险查询小程序（个人全栈项目）

> 个人学习/演示项目，用于展示全栈工程能力。未接入真实支付与人脸比对；
> 风险查询类业务若正式运营，需企业主体资质、支付商户号与合规评估（见下方"已知边界"）。

微信原生小程序 + FastAPI 后端 + 单文件管理后台。

- 用户端：风险对象查询（VIP 扣次/单次解锁）、材料提交（截图+证据照片上传）、VIP 会员、订单与支付流程、个人中心
- 管理端（admin.html，单文件即开即用）：数据仪表盘、材料审核、订单管理、查询记录、异议/联系工单

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | Python 3.11 · FastAPI · SQLAlchemy（8 张表）· JWT(python-jose) + bcrypt · httpx |
| 前端 | 微信原生小程序（13 个页面：WXML/WXSS/JS）· 统一 request 封装 |
| 测试 | pytest（接口契约 / schema / 上传安全 共 5 组） |
| 安全 | 上传魔数校验 · 后缀一致性检查 · 大小限制 · UUID 重命名 · 路径穿越防护 · .env 密钥管理 |

## 本机运行

后端：

```bash
cd backend
pip install -r requirements.txt
copy .env.example .env      # 填入你的微信测试号 AppID/Secret
uvicorn main:app --reload   # http://localhost:8000/docs
```

后台管理：浏览器直接打开 `backend/admin.html`（默认账号 admin / admin123，可用环境变量覆盖）。

小程序端：微信开发者工具导入 `components/`，将 `components/utils/config.js` 中 BASE_URL 改为本机地址；登录走微信测试号（AppID 未配置时自动使用开发态 fallback，仍可跑通全流程）。

## 已知边界（诚实说明）

- 支付为模拟流程（无商户号）：订单-支付-权益发放的状态机完整，微信支付的统一下单/回调验签/幂等/对账为接入位
- 照片匹配为占位接口：腾讯云人脸识别的 1:1/1:N 选型、成本测算与《个人信息保护法》框架下的合规分析见《人脸比对API选型.md》
- 微信登录基于测试号；安卓真机联调通过，iOS 未测（已实现 iOS 虚拟支付限制的全入口兜底拦截）
- 已识别的改进项：扣次接口的并发竞态（check-then-set）、CORS 白名单收紧、SQLAlchemy lifespan 写法

## 目录结构

```
backend/    FastAPI 后端（routers/ 11个路由模块 + models/schemas/auth）
components/ 微信小程序源码（pages/ 13页面 + utils）
tests/      pytest 接口测试
人脸比对API选型.md
```
