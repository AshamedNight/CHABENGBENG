// pages/service-contact/service-contact.js
const store = require('../../utils/store.js')

Page({
  data: {
    complaintId: '',
    complaintNo: '',
    message: '',
    contactInfo: '',
    submitting: false
  },

  onLoad(options) {
    this.setData({
      complaintId: options.complaintId || '',
      complaintNo: decodeURIComponent(options.complaintNo || '')
    })
  },

  onMessageInput(e) {
    this.setData({ message: e.detail.value })
  },

  onContactInput(e) {
    this.setData({ contactInfo: e.detail.value })
  },

  async submit() {
    if (this.data.submitting) return

    if (!this.data.message.trim()) {
      wx.showToast({ title: '请填写沟通内容', icon: 'none' })
      return
    }
    if (!this.data.contactInfo.trim()) {
      wx.showToast({ title: '请填写联系方式', icon: 'none' })
      return
    }

    this.setData({ submitting: true })
    wx.showLoading({ title: '提交中...' })

    try {
      await store.submitContact(
        this.data.complaintId,
        this.data.message.trim(),
        this.data.contactInfo.trim()
      )
      wx.hideLoading()
      wx.showToast({ title: '提交成功', icon: 'success' })
      setTimeout(() => {
        wx.navigateBack()
      }, 1500)
    } catch (err) {
      wx.hideLoading()
      this.setData({ submitting: false })
      console.error('提交失败:', err)
      wx.showToast({ title: '提交失败，请重试', icon: 'none' })
    }
  }
})
