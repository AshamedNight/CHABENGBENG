// utils/request.js
// 网络请求封装 - 自动携带 token，统一错误处理

const { BASE_URL } = require('./config.js') // 环境配置集中在 config.js，改环境不用动这里

// 存储 token 的 key
const TOKEN_KEY = 'wq_token'

/**
 * 获取存储的 token
 */
function getToken() {
  return wx.getStorageSync(TOKEN_KEY) || ''
}

/**
 * 设置 token
 */
function setToken(token) {
  wx.setStorageSync(TOKEN_KEY, token)
}

/**
 * 清除 token
 */
function clearToken() {
  wx.removeStorageSync(TOKEN_KEY)
}

/**
 * 发起请求
 * @param {Object} options - 请求配置
 * @param {string} options.url - 请求路径（相对路径，自动拼接 BASE_URL）
 * @param {string} options.method - HTTP 方法，默认 GET
 * @param {Object} options.data - 请求体数据
 * @param {Object} options.header - 额外请求头
 * @returns {Promise} 响应数据
 */
function request(options) {
  return new Promise((resolve, reject) => {
    const token = getToken()
    const url = options.url.startsWith('http') ? options.url : BASE_URL + options.url

    wx.request({
      url,
      method: options.method || 'GET',
      data: options.data || {},
      header: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : '',
        ...options.header
      },
      success: (res) => {
        // HTTP 状态码错误
        if (res.statusCode < 200 || res.statusCode >= 300) {
          // 401 未授权，清除 token 并跳转登录
          if (res.statusCode === 401) {
            clearToken()
            wx.showToast({ title: '登录已过期', icon: 'none' })
            // 可以在这里触发重新登录逻辑
          }
          reject(new Error(`HTTP ${res.statusCode}: ${res.data?.detail || '请求失败'}`))
          return
        }

        // 业务错误码（后端返回 code != 0）
        if (res.data && res.data.code !== 0) {
          reject(new Error(res.data.message || '业务处理失败'))
          return
        }

        resolve(res.data)
      },
      fail: (err) => {
        console.error('请求失败:', err)
        reject(new Error(err.errMsg || '网络请求失败'))
      }
    })
  })
}

/**
 * GET 请求
 */
function get(url, data = {}) {
  // GET 请求参数拼接到 URL
  const query = Object.keys(data)
    .map(k => `${encodeURIComponent(k)}=${encodeURIComponent(data[k])}`)
    .join('&')
  const fullUrl = query ? `${url}?${query}` : url
  return request({ url: fullUrl, method: 'GET' })
}

/**
 * POST 请求
 */
function post(url, data = {}) {
  return request({ url, method: 'POST', data })
}

/**
 * PUT 请求
 */
function put(url, data = {}) {
  return request({ url, method: 'PUT', data })
}

/**
 * DELETE 请求
 */
function del(url, data = {}) {
  return request({ url, method: 'DELETE', data })
}

/**
 * 上传文件
 */
function uploadFile(options) {
  return new Promise((resolve, reject) => {
    const token = getToken()
    const url = options.url.startsWith('http') ? options.url : BASE_URL + options.url

    wx.uploadFile({
      url,
      filePath: options.filePath,
      name: options.name || 'file',
      formData: options.formData || {},
      header: {
        'Authorization': token ? `Bearer ${token}` : ''
      },
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          try {
            const data = JSON.parse(res.data)
            if (data && data.code !== undefined && data.code !== 0) {
              reject(new Error(data.message || '上传失败'))
              return
            }
            resolve(data)
          } catch (e) {
            reject(new Error('上传失败：服务器响应无法解析'))
          }
        } else {
          reject(new Error(`上传失败: HTTP ${res.statusCode}`))
        }
      },
      fail: (err) => {
        reject(new Error(err.errMsg || '上传失败'))
      }
    })
  })
}

module.exports = {
  BASE_URL,
  getToken,
  setToken,
  clearToken,
  request,
  get,
  post,
  put,
  del,
  uploadFile
}
