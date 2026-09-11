// pages/query-history/query-history.js
const store = require('../../utils/store.js')

Page({
  data: {
    history: []
  },

  onLoad() {
    this.loadHistory()
  },

  onShow() {
    this.loadHistory()
  },

  async loadHistory() {
    try {
      const history = await store.getQueryHistory()
      const formattedHistory = history.map(item => ({
        ...item,
        timeText: this.formatTime(item.createdAt),
        riskText: store.getRiskLevelText(item.riskLevel)
      }))
      this.setData({ history: formattedHistory })
    } catch (err) {
      console.error('加载查询历史失败:', err)
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

  async reQuery(e) {
    const uid = e.currentTarget.dataset.uid
    try {
      const queryInfo = await store.getQueryCountInfo()
      if (!queryInfo.isVip) {
        wx.showToast({ title: '开通VIP后可查询', icon: 'none' })
        return
      }
      if (!queryInfo.hasVipCount) {
        wx.showToast({ title: '查询次数已用完', icon: 'none' })
        return
      }
      wx.redirectTo({
        url: `/pages/result/result?uid=${encodeURIComponent(uid)}`
      })
    } catch (err) {
      console.error('重新查询失败:', err)
      store.notifyError('无法连接服务器')
    }
  },

  clearHistory() {
    wx.showModal({
      title: '提示',
      content: '确定清空所有查询历史吗？',
      success: (res) => {
        if (res.confirm) {
          store.clearQueryHistory()
          this.setData({ history: [] })
          wx.showToast({ title: '已清空', icon: 'success' })
        }
      }
    })
  },

  goIndex() {
    wx.switchTab({ url: '/pages/index/index' })
  }
})
