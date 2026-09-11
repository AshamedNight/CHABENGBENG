// utils/store.js
// 数据管理工具类 - v1.5
const { request, get, post, setToken, clearToken, getToken } = require('./request.js')

// 平台配置（按分类）
const PLATFORM_CATEGORIES = [
  {
    name: '交友社交',
    platforms: ['他趣', '心遇', '陌陌', '探探', 'Soul', '积目', '红蓝', '觅伊', '暖聊', '友糖', '轻甜', '爱聊']
  },
  {
    name: '短视频/直播',
    platforms: ['抖音', '快手', '视频号', 'B站', '小红书']
  },
  {
    name: '电商交易',
    platforms: ['闲鱼', '转转', '淘宝', '拼多多', '京东', '得物']
  },
  {
    name: '通讯工具',
    platforms: ['微信', 'QQ', 'Telegram']
  },
  {
    name: '其他',
    platforms: ['其他']
  }
]

// ========== 图片上传 ==========

function isAlreadyUploaded(path) {
  return typeof path === 'string' && path.indexOf('/uploads/') !== -1
}

function wxCall(api, options) {
  return new Promise((resolve, reject) => {
    api({
      ...options,
      success: resolve,
      fail: reject
    })
  })
}

function fsReadBase64(filePath) {
  return new Promise((resolve, reject) => {
    wx.getFileSystemManager().readFile({
      filePath,
      encoding: 'base64',
      success: (res) => resolve(res.data),
      fail: reject
    })
  })
}

function arrayBufferToBase64(buffer) {
  if (typeof wx.arrayBufferToBase64 === 'function') {
    return wx.arrayBufferToBase64(buffer)
  }
  const bytes = new Uint8Array(buffer)
  const chunk = 0x8000
  let binary = ''
  for (let i = 0; i < bytes.length; i += chunk) {
    binary += String.fromCharCode.apply(null, bytes.subarray(i, i + chunk))
  }
  return btoa(binary)
}

function httpGetAsBase64(url) {
  return new Promise((resolve, reject) => {
    wx.request({
      url,
      method: 'GET',
      responseType: 'arraybuffer',
      success: (res) => {
        if (res.statusCode < 200 || res.statusCode >= 300) {
          reject(new Error('读取图片失败'))
          return
        }
        resolve(arrayBufferToBase64(res.data))
      },
      fail: reject
    })
  })
}

async function readImageAsBase64(filePath) {
  const tried = []

  const tryRead = async (label, fn) => {
    try {
      const data = await fn()
      if (data) return data
    } catch (err) {
      tried.push(label + ': ' + (err.errMsg || err.message || err))
    }
    return ''
  }

  let data = await tryRead('readFile', () => fsReadBase64(filePath))
  if (data) return data

  if (/^https?:\/\//.test(filePath)) {
    data = await tryRead('httpGet', () => httpGetAsBase64(filePath))
    if (data) return data
    data = await tryRead('downloadFile', async () => {
      const dl = await wxCall(wx.downloadFile, { url: filePath })
      if (!dl.tempFilePath) throw new Error('download empty')
      return fsReadBase64(dl.tempFilePath)
    })
    if (data) return data
  }

  let info
  try {
    info = await wxCall(wx.getImageInfo, { src: filePath })
  } catch (err) {
    tried.push('getImageInfo: ' + (err.errMsg || err.message || err))
  }

  const localSrc = (info && info.path) || filePath
  if (localSrc && localSrc !== filePath) {
    data = await tryRead('readFile(info.path)', () => fsReadBase64(localSrc))
    if (data) return data
    if (/^https?:\/\//.test(localSrc)) {
      data = await tryRead('httpGet(info.path)', () => httpGetAsBase64(localSrc))
      if (data) return data
    }
  }

  const w = (info && info.width) || 0
  const h = (info && info.height) || 0
  if (w && h && typeof wx.createOffscreenCanvas === 'function') {
    data = await tryRead('offscreenCanvas', async () => {
      const canvas = wx.createOffscreenCanvas({ type: '2d', width: w, height: h })
      const ctx = canvas.getContext('2d')
      const img = canvas.createImage()
      await new Promise((resolve, reject) => {
        img.onload = resolve
        img.onerror = () => reject(new Error('图片无法绘制'))
        img.src = localSrc
      })
      ctx.drawImage(img, 0, 0, w, h)
      const tmp = await wxCall(wx.canvasToTempFilePath, { canvas })
      if (!tmp.tempFilePath) throw new Error('canvas empty')
      return fsReadBase64(tmp.tempFilePath)
    })
    if (data) return data
  }

  console.error('读取图片失败，已尝试:', tried.join(' | '), '原始路径:', filePath)
  throw new Error('无法读取所选图片，请重新选择')
}

/**
 * 把选中的图读成数据，用 wx.request POST 到后端（不走 wx.uploadFile）。
 * Windows 开发者工具里 uploadFile 会对 http://tmp/... 报 file not found。
 */
async function uploadImage(filePath) {
  if (!filePath) {
    throw new Error('没有要上传的图片')
  }
  if (isAlreadyUploaded(filePath)) {
    return filePath
  }
  try {
    const content_base64 = await readImageAsBase64(filePath)
    const res = await post('/api/upload-json', {
      filename: 'image',
      content_base64
    })
    const url = res.data && res.data.url
    if (!url) {
      throw new Error('上传失败：服务器未返回图片地址')
    }
    return url
  } catch (err) {
    console.error('上传图片失败:', err)
    throw err
  }
}

async function uploadImages(items) {
  const urls = []
  for (const item of items || []) {
    const path = typeof item === 'string' ? item : (item && item.url)
    urls.push(await uploadImage(path))
  }
  return urls
}

// ========== 用户管理 ==========

/**
 * 生成用户UID（U+8位数字）
 */
function generateUid() {
  const num = Math.floor(10000000 + Math.random() * 90000000)
  return 'U' + num
}

/**
 * 初始化用户
 */
async function initUser(code = '', nickname = '查崩崩用户', avatar = '') {
  try {
    const res = await post('/api/auth/login', { code, nickname, avatar })
    if (res.data && res.data.token) {
      setToken(res.data.token)
      const userInfo = await getUser()
      updateLocalUserCache(userInfo)
      return userInfo
    }
    throw new Error('登录失败')
  } catch (err) {
    console.error('初始化用户失败:', err)
    throw err
  }
}

/**
 * 获取当前用户信息
 */
async function getUser() {
  try {
    const res = await get('/api/user/info')
    const data = res.data
    return {
      id: data.id,
      uid: data.uid || '',
      nickname: data.nickname || '查崩崩用户',
      avatar: data.avatar || '',
      isVip: data.is_vip,
      vipExpireAt: data.vip_expire_at,
      vipMonthlyQueryCount: data.vip_query_count || 0,
      privacyAgreed: data.privacy_agreed,
      createdAt: data.created_at
    }
  } catch (err) {
    console.error('获取用户信息失败:', err)
    throw err
  }
}

/**
 * 更新用户信息（昵称、头像）
 */
async function updateUserInfo(data) {
  try {
    await post('/api/user/update', data)
    const user = await getUser()
    updateLocalUserCache(user)
    return user
  } catch (err) {
    console.error('更新用户信息失败:', err)
    throw err
  }
}

function updateLocalUserCache(user) {
  wx.setStorageSync('wq_user_cache', user)
}

/**
 * 同意隐私协议
 */
async function agreePrivacy() {
  try {
    await post('/api/auth/privacy', { agreed: true })
    const user = await getUser()
    updateLocalUserCache({ ...user, privacyAgreed: true })
    return true
  } catch (err) {
    console.error('同意隐私协议失败:', err)
    throw err
  }
}

// ========== VIP与查询次数 ==========

/**
 * 获取查询次数信息
 * v1.5: VIP年卡80次查询（50次+赠30次）
 */
async function getQueryCountInfo() {
  try {
    const res = await get('/api/user/query-count')
    const data = res.data
    return {
      isVip: data.is_vip,
      vipExpireAt: data.vip_expire_at,
      vipCount: data.vip_count || 0,
      hasVipCount: data.is_vip && data.vip_count > 0,
      canQuery: data.is_vip && data.vip_count > 0
    }
  } catch (err) {
    console.error('获取查询次数失败:', err)
    throw err
  }
}

/**
 * 检查24小时内是否已查询过该UID
 */
async function hasQueriedIn24h(targetUid) {
  try {
    const history = await getQueryHistory()
    const now = Date.now()
    return history.some(item =>
      item.targetUid === targetUid && (now - new Date(item.createdAt).getTime()) < 24 * 60 * 60 * 1000
    )
  } catch (err) {
    return false
  }
}

/**
 * 检查单次付费是否已解锁该对象
 */
async function isSingleQueryUnlocked(targetUid) {
  try {
    const res = await post('/api/query/check-unlock', { target_uid: targetUid })
    return res.data?.unlocked || false
  } catch (err) {
    console.error('检查解锁状态失败:', err)
    return false
  }
}

/**
 * 开通VIP（支付回调后刷新）
 */
async function activateVip(plan) {
  return await getUser()
}

// ========== 投诉单管理 ==========

/**
 * 获取投诉列表
 */
async function getComplaints(page = 1, pageSize = 20) {
  try {
    const res = await get('/api/complaint/list', { page, page_size: pageSize })
    const list = res.data?.list || []
    return list.map(item => ({
      id: item.id,
      orderNo: item.order_no,
      platform: item.platform,
      targetUid: item.target_uid,
      personPhotos: item.person_photos || [],
      accountScreenshots: item.account_screenshots || [],
      evidenceImages: item.evidence_images || [],
      description: item.description,
      allowContact: item.allow_contact,
      allowStaffContact: item.allow_staff_contact,
      agreeJointRights: item.agree_joint_rights,
      status: item.status,
      createdAt: item.created_at
    }))
  } catch (err) {
    console.error('获取投诉列表失败:', err)
    return []
  }
}

/**
 * 提交投诉
 * v1.4: 新增 personPhotos, accountScreenshot 字段；移除 agreeAssist
 */
async function addComplaint(data) {
  try {
    // 将图片对象数组 [{id,url}] 转换为 URL 字符串数组（后端要求 List[str]）
    const extractUrls = (arr) => (arr || []).map(item => typeof item === 'string' ? item : (item.url || ''))
    const res = await post('/api/complaint', {
      platform: data.platform,
      target_uid: data.targetUid,
      person_photos: extractUrls(data.personPhotos),
      account_screenshots: extractUrls(data.accountScreenshots),
      evidence_images: extractUrls(data.evidenceImages),
      description: data.description || '',
      allow_contact: data.allowContact !== false,
      allow_staff_contact: data.allowStaffContact === true,
      agree_joint_rights: data.agreeJointRights === true
    })
    return res.data
  } catch (err) {
    console.error('提交材料失败:', err)
    throw err
  }
}

/**
 * 获取投诉详情
 */
async function getComplaintById(id) {
  try {
    const res = await get(`/api/complaint/${id}`)
    const item = res.data
    if (!item) return null
    return {
      id: item.id,
      orderNo: item.order_no,
      platform: item.platform,
      targetUid: item.target_uid,
      personPhotos: item.person_photos || [],
      accountScreenshots: item.account_screenshots || [],
      evidenceImages: item.evidence_images || [],
      description: item.description,
      allowContact: item.allow_contact,
      allowStaffContact: item.allow_staff_contact,
      agreeJointRights: item.agree_joint_rights,
      status: item.status,
      createdAt: item.created_at
    }
  } catch (err) {
    console.error('获取投诉详情失败:', err)
    return null
  }
}

/**
 * 更新投诉单允许联系状态
 */
async function updateComplaintContact(id, allowContact) {
  try {
    await post(`/api/complaint/${id}/contact`, { allow_contact: allowContact })
    return true
  } catch (err) {
    console.error('更新联系状态失败:', err)
    return false
  }
}

// ========== 查询历史 ==========

/**
 * 获取查询历史
 */
async function getQueryHistory(page = 1, pageSize = 50) {
  try {
    const res = await get('/api/query/history', { page, page_size: pageSize })
    const list = res.data?.list || []
    return list.map(item => ({
      id: item.id,
      targetUid: item.target_uid,
      platform: item.platform,
      riskLevel: item.risk_level,
      queryType: item.query_type,
      costType: item.cost_type,
      createdAt: item.created_at
    }))
  } catch (err) {
    console.error('获取查询历史失败:', err)
    return []
  }
}

function clearQueryHistory() {
  console.warn('清空查询历史功能暂未实现后端接口')
}

// ========== 订单管理 ==========

/**
 * 获取订单列表
 */
async function getOrders(page = 1, pageSize = 20, productType = '') {
  try {
    const params = { page, page_size: pageSize }
    if (productType) params.product_type = productType
    const res = await get('/api/orders', params)
    const list = res.data?.list || []
    return list.map(item => ({
      id: item.id,
      productType: item.product_type,
      productName: item.product_name,
      amount: item.amount,
      payStatus: item.pay_status,
      payTime: item.pay_time,
      vipDurationDays: item.vip_duration_days,
      singleQueryTargetUid: item.single_query_target_uid,
      relatedComplaintId: item.related_complaint_id,
      serviceStatus: item.service_status,
      createdAt: item.created_at
    }))
  } catch (err) {
    console.error('获取订单列表失败:', err)
    return []
  }
}

/**
 * 创建订单
 * v1.4: 支持 dispute_service / contact_service 维权服务类型
 */
async function addOrder(data) {
  try {
    const res = await post('/api/orders', {
      product_type: data.productType,
      target_uid: data.singleQueryTargetUid || '',
      related_complaint_id: data.relatedComplaintId ? Number(data.relatedComplaintId) : null
    })
    return res.data
  } catch (err) {
    console.error('创建订单失败:', err)
    throw err
  }
}

/**
 * 支付订单（模拟支付）
 */
async function payOrder(orderId) {
  try {
    const res = await post(`/api/orders/${orderId}/pay`)
    return res.data
  } catch (err) {
    console.error('支付订单失败:', err)
    throw err
  }
}

// ========== 相关对象查询 ==========

/**
 * 搜索对象（调用后端查询接口）
 * v1.4: 返回结构调整，records 包含投诉人昵称、投诉编号、证据图片、状态
 */
async function searchTarget(targetUid) {
  try {
    const res = await post('/api/query/search', { target_uid: targetUid })
    const data = res.data
    return {
      found: data.target.found,
      data: {
        targetUid: data.target.target_uid,
        platform: data.target.platform,
        complaintCount: data.target.complaint_count,
        riskLevel: data.target.risk_level,
        status: data.target.status,
        personPhotos: data.target.person_photos || [],
        records: (data.target.records || []).map(r => ({
          id: r.id,
          orderNo: r.order_no,
          userNickname: r.user_nickname || '匿名用户',
          allowContact: r.allow_contact || false,
          createdAt: r.created_at,
          evidenceImages: r.evidence_images || [],
          status: r.status
        }))
      },
      costType: data.cost_type,
      costMessage: data.cost_message,
      isUnlocked: data.is_unlocked
    }
  } catch (err) {
    console.error('搜索对象失败:', err)
    throw err
  }
}

// ========== 照片比对 ==========

/**
 * 照片比对 - 返回相关人列表
 */
async function photoMatch(imageUrl) {
  try {
    const res = await post('/api/photo/match', { image_url: imageUrl })
    const list = res.data?.matches || []
    return list.map(item => ({
      id: item.id,
      targetUid: item.target_uid,
      platform: item.platform,
      personPhoto: item.person_photo || '',
      matchRate: item.match_rate || 0,
      complaintCount: item.complaint_count || 0,
      riskLevel: item.risk_level || 'none'
    }))
  } catch (err) {
    console.error('照片比对失败:', err)
    throw err
  }
}

// ========== VIP套餐 ==========

/**
 * 获取VIP套餐列表
 * v1.5: 仅保留年卡399元/365天，80次查询（50次+赠30次）
 */
async function getVipPlans() {
  try {
    const res = await get('/api/vip/plans')
    return res.data || []
  } catch (err) {
    console.error('获取VIP套餐失败:', err)
    throw err
  }
}

// ========== 维权服务 ==========

/**
 * 提交提起异议
 */
async function submitDispute(complaintId, reason, contactInfo) {
  try {
    const res = await post('/api/service/dispute', {
      complaint_id: complaintId,
      reason,
      contact_info: contactInfo
    })
    return res.data
  } catch (err) {
    console.error('提交异议失败:', err)
    throw err
  }
}

/**
 * 提交联系处理请求
 */
async function submitContact(complaintId, message, contactInfo) {
  try {
    const res = await post('/api/service/contact', {
      complaint_id: complaintId,
      message,
      contact_info: contactInfo
    })
    return res.data
  } catch (err) {
    console.error('提交联系处理失败:', err)
    throw err
  }
}

// ========== 工具函数 ==========

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toISOString().split('T')[0]
}

function formatDateTime(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const pad = n => n.toString().padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function getRiskLevelText(level) {
  const map = { high: '高风险', medium: '中风险', low: '低风险', none: '暂无数据' }
  return map[level] || '未知'
}

function getRiskLevelClass(level) {
  return 'risk-' + level
}

function getStatusClass(status) {
  const map = {
    '待处理': 'tag-danger',
    '处理中': 'tag-info',
    '处理完毕': 'tag-success',
    '已驳回': 'tag-danger'
  }
  return map[status] || 'tag-info'
}

function notifyError(title) {
  wx.showToast({ title: title || '无法连接服务器', icon: 'none' })
}

// ========== 导出 ==========
module.exports = {
  PLATFORM_CATEGORIES,
  // 上传
  uploadImage,
  uploadImages,
  // 用户
  initUser,
  getUser,
  updateUserInfo,
  agreePrivacy,
  generateUid,
  // VIP与查询
  getQueryCountInfo,
  hasQueriedIn24h,
  isSingleQueryUnlocked,
  activateVip,
  // 投诉单
  getComplaints,
  addComplaint,
  getComplaintById,
  updateComplaintContact,
  // 查询历史
  getQueryHistory,
  clearQueryHistory,
  // 订单
  getOrders,
  addOrder,
  payOrder,
  // 对象查询
  searchTarget,
  // 照片比对
  photoMatch,
  // VIP套餐
  getVipPlans,
  // 维权服务
  submitDispute,
  submitContact,
  // 工具
  formatDate,
  formatDateTime,
  getRiskLevelText,
  getRiskLevelClass,
  getStatusClass,
  notifyError
}
