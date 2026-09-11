// pages/index/index.js
const store = require('../../utils/store.js')
const { guardPayment } = require('../../utils/platform.js')

Page({
  data: {
    privacyAgreed: false,
    searchKeyword: '',
    queryInfo: {},
    vipExpireText: '',
    recentQueries: [],
    // 付费弹窗
    showPay: false,
    selectedOption: 'vip',
    pendingSearchUid: ''
  },

  onLoad() {
    this.loadData()
  },

  onShow() {
    this.loadData()
  },

  async loadData() {
    try {
      const user = await store.getUser()
      const queryInfo = await store.getQueryCountInfo()
      // 最近查询（仅VIP/付费用户可见）
      let recentQueries = []
      if (queryInfo.isVip) {
        const history = await store.getQueryHistory(1, 5)
        recentQueries = history.slice(0, 5).map(item => ({
          ...item,
          timeText: this.formatTime(item.createdAt),
          riskText: store.getRiskLevelText(item.riskLevel)
        }))
      }
      this.setData({
        privacyAgreed: user.privacyAgreed,
        queryInfo,
        vipExpireText: user.vipExpireAt ? store.formatDate(user.vipExpireAt) : '',
        recentQueries
      })
    } catch (err) {
      console.error('加载数据失败:', err)
      store.notifyError('无法连接服务器')
    }
  },

  formatTime(dateStr) {
    const d = new Date(dateStr)
    const now = new Date()
    const diff = now - d
    if (diff < 60000) return '刚刚'
    if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前'
    if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前'
    return store.formatDate(dateStr)
  },

  // 隐私协议
  async agreePrivacy() {
    try {
      await store.agreePrivacy()
      this.setData({ privacyAgreed: true })
    } catch (err) {
      wx.showToast({ title: '操作失败', icon: 'none' })
    }
  },

  refusePrivacy() {
    wx.showModal({
      title: '提示',
      content: '拒绝协议将无法使用小程序功能',
      showCancel: false
    })
  },

  // 查看完整协议
  goAgreement(e) {
    const type = e.currentTarget.dataset.type
    wx.navigateTo({ url: `/pages/agreement/agreement?type=${type}` })
  },

  checkPrivacy() {
    if (!this.data.privacyAgreed) {
      wx.showToast({ title: '请先同意隐私协议', icon: 'none' })
      return false
    }
    return true
  },

  // 搜索
  onSearchInput(e) {
    this.setData({ searchKeyword: e.detail.value })
  },

  onSearch() {
    const keyword = this.data.searchKeyword.trim()
    if (!keyword) {
      wx.showToast({ title: '请输入账号UID', icon: 'none' })
      return
    }
    this.doSearch(keyword)
  },

  async doSearch(keyword) {
    if (!this.checkPrivacy()) return
    let queryInfo
    try {
      queryInfo = await store.getQueryCountInfo()
    } catch (err) {
      store.notifyError('无法连接服务器')
      return
    }
    // v1.4: 免费用户不可查询，直接弹付费墙；iOS 端拦截虚拟支付
    if (!queryInfo.isVip) {
      if (guardPayment('index-search')) return
      this.setData({
        pendingSearchUid: keyword,
        showPay: true,
        selectedOption: 'vip'
      })
      return
    }
    // VIP用户：检查次数
    if (!queryInfo.hasVipCount) {
      if (guardPayment('index-no-count')) return
      wx.showModal({
        title: '查询次数已用完',
        content: 'VIP查询次数已用完，可购买单次查询或续费VIP',
        confirmText: '购买单次',
        cancelText: '知道了',
        success: (res) => {
          if (res.confirm) {
            wx.navigateTo({
              url: `/pages/payment/payment?type=single&targetUid=${encodeURIComponent(keyword)}&amount=9.9&productName=${encodeURIComponent('单次查询解锁')}`
            })
          }
        }
      })
      return
    }
    // 有次数，跳转结果页
    wx.navigateTo({
      url: `/pages/result/result?uid=${encodeURIComponent(keyword)}`
    })
  },

  // 照片比对 - 跳转到照片比对页
  onPhotoMatch() {
    if (!this.checkPrivacy()) return
    if (!this.data.queryInfo.isVip) {
      if (guardPayment('index-photo-match')) return
      wx.showModal({
        title: 'VIP专属功能',
        content: '风险自查为VIP会员专属功能，开通年卡享80次查询（50次+赠30次）',
        confirmText: '开通VIP',
        cancelText: '知道了',
        success: (res) => {
          if (res.confirm) {
            wx.navigateTo({ url: '/pages/vip/vip' })
          }
        }
      })
      return
    }
    wx.navigateTo({ url: '/pages/photo-match/photo-match' })
  },

  // 导航
  goComplaint() {
    if (!this.checkPrivacy()) return
    wx.switchTab({ url: '/pages/complaint/complaint' })
  },

  goProfile() {
    wx.switchTab({ url: '/pages/profile/profile' })
  },

  goVip() {
    wx.navigateTo({ url: '/pages/vip/vip' })
  },

  goQueryHistory() {
    wx.navigateTo({ url: '/pages/query-history/query-history' })
  },

  onRecentClick(e) {
    const uid = e.currentTarget.dataset.uid
    this.doSearch(uid)
  },

  // 付费弹窗
  hidePayModal() {
    this.setData({ showPay: false, pendingSearchUid: '' })
  },

  stopPropagation() {},

  selectPayOption(e) {
    this.setData({ selectedOption: e.currentTarget.dataset.option })
  },

  confirmPay() {
    const { selectedOption, pendingSearchUid } = this.data
    this.setData({ showPay: false })
    if (selectedOption === 'vip') {
      wx.navigateTo({ url: '/pages/vip/vip' })
    } else {
      wx.navigateTo({
        url: `/pages/payment/payment?type=single&targetUid=${encodeURIComponent(pendingSearchUid)}&amount=9.9&productName=${encodeURIComponent('单次查询解锁')}`
      })
    }
  }
})
