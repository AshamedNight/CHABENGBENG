// utils/config.js - 环境配置（改环境只动这一个文件）
//
// 真机联调步骤：
// 1. 电脑上跑 ipconfig，找到局域网 IPv4 地址（如 192.168.1.23）
// 2. 把下面 DEV_HOST 改成这个 IP
// 3. 后端启动时绑 0.0.0.0，并把 PUBLIC_BASE_URL 设为同一个地址：
//      $env:PUBLIC_BASE_URL="http://192.168.1.23:8000"
//      python -m uvicorn main:app --host 0.0.0.0 --port 8000
// 4. 手机与电脑连同一 WiFi，开发者工具用「真机调试」扫码预览
//    （project.config.json 已关闭 urlCheck，开发期不校验域名）

const ENV = 'dev' // 'dev' 开发/真机联调 | 'prod' 生产上线

const DEV_HOST = '192.168.1.11' // 真机联调时改成电脑局域网IP，模拟器/开发者工具内保持 localhost

const CONFIG = {
  dev: {
    BASE_URL: `http://14c07d33.r17.cpolar.top`
  },
  prod: {
    BASE_URL: 'https://your-domain.com' // TODO: 上线前替换为已备案的 HTTPS 域名
  }
}

module.exports = CONFIG[ENV]
