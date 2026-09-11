# 怎么确认这次改对了

测试是给程序出的考题。改完代码，先让考题过，再让你在微信开发者工具里点一遍。绿了只代表「这一题的约定没被打破」，不代表小程序已经在真机上能用。

## 改多少测一次

**每做完一件看得见的事，立刻测那一件。** 不要攒 4、5 个功能再一起测。

| 改了什么 | 先跑什么 | 绿了代表什么 |
|----------|----------|--------------|
| 后端接口 / 数据模型 | `python -m pytest tests/ -v` | 登录、下单、查询这些约定还在 |
| 前端「失败就假登录」 | 同一条命令里的 `test_store_fallback.py` | 身份函数失败会报错，不再捏用户 |
| 页面 toast、按钮、跳转 | 微信开发者工具，按下面手测清单 | 人能看见失败，而不是假成功 |

沙盒或本机 pytest **起不了微信**，也替代不了开发者工具。

## Windows 上跑自动测试（PowerShell）

第一次：

```powershell
cd 你的项目目录\v1.5
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
python -m pip install pytest==7.4.4
python -m pytest tests/ -v
```

以后每次改完：

```powershell
cd 你的项目目录\v1.5
.\.venv\Scripts\Activate.ps1
python -m pytest tests/ -v
```

如果提示「无法加载，因为在此系统上禁止运行脚本」，只对当前用户开一次：

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

这是允许跑本机脚本，不是关掉安全。

自动测试用临时空库，**不会改** `backend\app.db`。

## 微信开发者工具手测（收紧降级之后）

1. 后端先不要开。编译小程序，打开首页。「我的」不应出现一个随机 UID 的已登录用户，应提示连不上服务器或登录失败。
2. 再开后端（只绑本机）：

```powershell
cd 你的项目目录\v1.5\backend
..\\.venv\Scripts\Activate.ps1
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

3. 重新编译小程序。应能登录，「我的」出现 `U` 开头的 UID。
4. 关掉后端，再进「我的」。应报错，不应继续显示成正常会员。

把截图或报错原文发回来。

## 真机联调（手机扫码跑通）

开发期不用域名，走局域网直连（`project.config.json` 已关闭域名校验）：

1. 电脑查局域网 IP（PowerShell 跑 `ipconfig`，找「IPv4 地址」，假设是 `192.168.1.23`）。
2. 改前端 `components/utils/config.js`：`DEV_HOST = '192.168.1.23'`。
3. 启动后端（绑 0.0.0.0，并告诉它图片的公开地址）：

```powershell
cd 你的项目目录\v1.5\backend
..\.venv\Scripts\Activate.ps1
$env:PUBLIC_BASE_URL="http://192.168.1.23:8000"
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

4. Windows 防火墙第一次会弹窗，选「允许访问」（专用网络）。
5. 手机连**同一个 WiFi**，微信开发者工具点「真机调试」扫码。

验证顺序：手机浏览器先开 `http://192.168.1.23:8000/health`，能看到 `{"status":"ok"}` 说明网络通了，再进小程序。看不到就是防火墙或不在同一 WiFi。

> 切换环境只改 `config.js` 里的 `ENV` 和地址，`request.js` 不用动。
