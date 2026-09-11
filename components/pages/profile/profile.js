// pages/profile/profile.js
const store = require('../../utils/store.js')
const { guardPayment } = require('../../utils/platform.js')

Page({
  data: {
    user: null,
    uid: '',
    nickname: '',
    avatar: '',
    isVip: false,
    vipExpireText: '',
    vipCount: 0,
    usedCount: 0,
    progressPercent: 0,
    complaints: []
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

      const totalCount = 80
      const vipCount = queryInfo.vipCount || 0
      const usedCount = totalCount - vipCount
      const progressPercent = user.isVip ? Math.min((usedCount / totalCount) * 100, 100) : 0

      const complaints = await store.getComplaints()
      const statusClassMap = { '待处理': 'pending', '处理中': 'processing', '处理完毕': 'done', '已驳回': 'rejected' }
      const formattedComplaints = complaints.slice(0, 3).map(item => ({
        ...item,
        timeText: store.formatDateTime(item.createdAt),
        statusClass: statusClassMap[item.status] || 'pending'
      }))

      this.setData({
        user,
        uid: user.uid || '',
        nickname: user.nickname || '点击设置昵称',
        avatar: user.avatar || '',
        isVip: user.isVip,
        vipExpireText: user.vipExpireAt ? store.formatDate(user.vipExpireAt) : '',
        vipCount,
        usedCount,
        progressPercent,
        complaints: formattedComplaints
      })
    } catch (err) {
      console.error('加载数据失败:', err)
      store.notifyError('无法连接服务器')
    }
  },

  // 复制UID
  copyUid() {
    wx.setClipboardData({
      data: this.data.uid,
      success: () => {
        wx.showToast({ title: 'UID已复制', icon: 'success' })
      }
    })
  },

  // 头像设置
  onAvatarTap() {
    wx.navigateTo({ url: '/pages/profile-edit/profile-edit?type=avatar' })
  },

  // 昵称设置
  onNicknameTap() {
    wx.navigateTo({ url: '/pages/profile-edit/profile-edit?type=nickname' })
  },

  // 导航
  goVip() {
    wx.navigateTo({ url: '/pages/vip/vip' })
  },

  goComplaint() {
    wx.switchTab({ url: '/pages/complaint/complaint' })
  },

  goComplaintList() {
    wx.showToast({ title: '投诉单列表', icon: 'none' })
  },

  goComplaintDetail(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({
      url: `/pages/complaint-detail/complaint-detail?id=${id}`
    })
  },

  goQueryHistory() {
    if (!this.data.isVip) {
      wx.showToast({ title: '开通VIP后可查看查询历史', icon: 'none' })
      return
    }
    wx.navigateTo({ url: '/pages/query-history/query-history' })
  },

  goOrderList() {
    wx.navigateTo({ url: '/pages/order-list/order-list' })
  },

  goAgreement(e) {
    const type = e.currentTarget.dataset.type
    wx.navigateTo({ url: `/pages/agreement/agreement?type=${type}` })
  },

  buySingle() {
    if (guardPayment('profile-single')) return
    wx.navigateTo({
      url: '/pages/payment/payment?type=single&amount=9.9&productName=' + encodeURIComponent('单次查询解锁')
    })
  },

  showHelp() {
    wx.showModal({
      title: '帮助与反馈',
      content: '如有问题请联系客服，我们会尽快为您解决。',
      showCancel: false
    })
  },

  showAbout() {
    wx.showModal({
      title: '关于我们',
      content: 'v1.5.0\n\n致力于为用户提供便捷的风险查询与维权辅助工具，帮助用户识别风险行为，维护自身合法权益。',
      showCancel: false
    })
  },

  contactService() {
    wx.showToast({ title: '客服功能开发中', icon: 'none' })
  }
})
