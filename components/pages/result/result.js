// pages/result/result.js
const store = require('../../utils/store.js')
const { guardPayment } = require('../../utils/platform.js')

Page({
  data: {
    targetUid: '',
    targetData: null,
    riskLevelText: '',
    isVip: false,
    isUnlocked: false,
    showPay: false,
    selectedOption: 'vip',
    // 维权服务操作菜单
    showActionMenu: false,
    selectedRecord: null,
    from: ''
  },

  onLoad(options) {
    const targetUid = decodeURIComponent(options.uid || options.id || '')
    const from = options.from || ''
    this.setData({ targetUid, from })
    this.loadTargetData()
  },

  onShow() {
    this.loadUserStatus()
  },

  async loadTargetData() {
    try {
      wx.showLoading({ title: '查询中...' })
      const result = await store.searchTarget(this.data.targetUid)
      const riskLevelText = store.getRiskLevelText(result.data.riskLevel)
      this.setData({
        targetData: result,
        riskLevelText
      })
      wx.hideLoading()
      this.loadUserStatus()
    } catch (err) {
      wx.hideLoading()
      console.error('加载对象数据失败:', err)
      wx.showToast({ title: '查询失败，请检查网络或是否已登录', icon: 'none' })
    }
  },

  async loadUserStatus() {
    try {
      const user = await store.getUser()
      const isUnlocked = await store.isSingleQueryUnlocked(this.data.targetUid)
      this.setData({
        isVip: user.isVip,
        isUnlocked
      })
    } catch (err) {
      console.error('加载用户状态失败:', err)
      store.notifyError('无法连接服务器')
    }
  },

  // 格式化时间
  formatRecordTime(dateStr) {
    return store.formatDateTime(dateStr)
  },

  // 付费弹窗
  showPayModal() {
    if (guardPayment('result-unlock')) return
    this.setData({ showPay: true, selectedOption: 'vip' })
  },
  hidePayModal() {
    this.setData({ showPay: false })
  },
  stopPropagation() {},
  selectOption(e) {
    this.setData({ selectedOption: e.currentTarget.dataset.option })
  },
  confirmPay() {
    const { selectedOption, targetUid } = this.data
    this.setData({ showPay: false })
    if (selectedOption === 'vip') {
      wx.navigateTo({ url: '/pages/vip/vip' })
    } else {
      wx.navigateTo({
        url: `/pages/payment/payment?type=single&targetUid=${encodeURIComponent(targetUid)}&amount=9.9&productName=${encodeURIComponent('单次查询解锁')}`
      })
    }
  },

  // 点击投诉记录 → 弹出操作菜单
  onRecordTap(e) {
    // 仅付费用户可点击
    if (!this.data.isVip && !this.data.isUnlocked) {
      this.showPayModal()
      return
    }
    const record = e.currentTarget.dataset.record
    this.setData({
      showActionMenu: true,
      selectedRecord: record
    })
  },

  closeActionMenu() {
    this.setData({ showActionMenu: false, selectedRecord: null })
  },

  // 提起异议
  goDispute() {
    const record = this.data.selectedRecord
    this.setData({ showActionMenu: false })
    if (guardPayment('result-dispute')) return
    wx.navigateTo({
      url: `/pages/payment/payment?type=dispute&complaintId=${record.id}&complaintNo=${encodeURIComponent(record.orderNo)}&amount=299&productName=${encodeURIComponent('提起异议服务')}`
    })
  },

  // 联系处理
  goContact() {
    const record = this.data.selectedRecord
    this.setData({ showActionMenu: false })
    if (guardPayment('result-contact')) return
    wx.navigateTo({
      url: `/pages/payment/payment?type=contact&complaintId=${record.id}&complaintNo=${encodeURIComponent(record.orderNo)}&amount=299&productName=${encodeURIComponent('联系处理服务')}`
    })
  },

  // 预览证据图片
  previewEvidence(e) {
    const urls = e.currentTarget.dataset.urls
    const current = e.currentTarget.dataset.url
    wx.previewImage({ current, urls })
  },

  // 去投诉
  goComplaint() {
    wx.switchTab({ url: '/pages/complaint/complaint' })
  }
})
