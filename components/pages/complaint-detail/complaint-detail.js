// pages/complaint-detail/complaint-detail.js
const store = require('../../utils/store.js')

Page({
  data: {
    complaint: null,
    allowContact: false
  },

  async onLoad(options) {
    const id = options.id
    try {
      const complaint = await store.getComplaintById(id)
      if (complaint) {
        this.setData({
          complaint: {
            ...complaint,
            timeText: store.formatDateTime(complaint.createdAt)
          },
          allowContact: complaint.allowContact
        })
      }
    } catch (err) {
      console.error('加载投诉详情失败:', err)
      wx.showToast({ title: '加载失败', icon: 'none' })
    }
  },

  // 修改允许联系状态
  async onAllowContactChange(e) {
    const allowContact = e.detail.value
    this.setData({ allowContact })
    try {
      await store.updateComplaintContact(this.data.complaint.id, allowContact)
      wx.showToast({ title: '设置已更新', icon: 'success' })
    } catch (err) {
      console.error('更新失败:', err)
      this.setData({ allowContact: !allowContact })
      wx.showToast({ title: '更新失败', icon: 'none' })
    }
  },

  // 查询该对象
  async queryTarget() {
    const targetUid = this.data.complaint.targetUid
    let queryInfo
    try {
      queryInfo = await store.getQueryCountInfo()
    } catch (err) {
      store.notifyError('无法连接服务器')
      return
    }
    if (!queryInfo.isVip) {
      wx.showToast({ title: '开通VIP后可查询', icon: 'none' })
      return
    }
    if (!queryInfo.hasVipCount) {
      wx.showToast({ title: '查询次数已用完', icon: 'none' })
      return
    }
    wx.navigateTo({
      url: `/pages/result/result?uid=${encodeURIComponent(targetUid)}`
    })
  },

  // 预览图片
  previewImage(e) {
    const url = e.currentTarget.dataset.url
    const urls = e.currentTarget.dataset.urls || [url]
    wx.previewImage({ current: url, urls })
  },

  contactService() {
    wx.showToast({ title: '客服功能开发中', icon: 'none' })
  }
})
