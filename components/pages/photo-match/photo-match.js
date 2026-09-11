// pages/photo-match/photo-match.js
const store = require('../../utils/store.js')
const { guardPayment } = require('../../utils/platform.js')

Page({
  data: {
    uploadedImage: '',
    matching: false,
    matched: false,
    matches: [],
    isVip: false
  },

  onLoad() {
    this.loadUserStatus()
  },

  async loadUserStatus() {
    try {
      const user = await store.getUser()
      this.setData({ isVip: user.isVip })
      if (!user.isVip) {
        if (guardPayment('photo-match-entry')) {
          setTimeout(() => wx.navigateBack({ delta: 1 }), 1200)
          return
        }
        wx.showModal({
          title: 'VIP专属功能',
          content: '风险自查为VIP会员专属功能，开通年卡享80次查询',
          confirmText: '开通VIP',
          cancelText: '返回',
          success: (res) => {
            if (res.confirm) {
              wx.redirectTo({ url: '/pages/vip/vip' })
            } else {
              wx.navigateBack()
            }
          }
        })
      }
    } catch (err) {
      console.error('加载用户状态失败:', err)
      store.notifyError('无法连接服务器')
    }
  },

  // 选择照片
  choosePhoto() {
    wx.chooseImage({
      count: 1,
      sizeType: ['compressed'],
      sourceType: ['album', 'camera'],
      success: (res) => {
        this.setData({
          uploadedImage: res.tempFilePaths[0],
          matched: false,
          matches: []
        })
      }
    })
  },

  // 重新选择
  rechoose() {
    this.setData({
      uploadedImage: '',
      matched: false,
      matches: []
    })
  },

  // 开始比对
  async startMatch() {
    if (!this.data.uploadedImage) {
      wx.showToast({ title: '请先上传照片', icon: 'none' })
      return
    }
    this.setData({ matching: true })
    try {
      const imageUrl = await store.uploadImage(this.data.uploadedImage)
      // 模拟比对延迟
      await new Promise(resolve => setTimeout(resolve, 1500))
      const matches = await store.photoMatch(imageUrl)
      this.setData({
        matching: false,
        matched: true,
        matches
      })
    } catch (err) {
      console.error('比对失败:', err)
      this.setData({ matching: false })
      wx.showToast({ title: '比对失败，请重试', icon: 'none' })
    }
  },

  // 点击相关人 → 进入查询结果页（计一次查询）
  async onMatchTap(e) {
    const match = e.currentTarget.dataset.match
    let queryInfo
    try {
      queryInfo = await store.getQueryCountInfo()
    } catch (err) {
      store.notifyError('无法连接服务器')
      return
    }

    // 免费用户弹付费墙；iOS 端拦截虚拟支付
    if (!queryInfo.isVip) {
      if (guardPayment('photo-match-detail')) return
      wx.showModal({
        title: '开通VIP',
        content: '查看相关对象详情需要开通VIP或购买单次查询',
        confirmText: '去开通',
        cancelText: '单次查询',
        success: (res) => {
          if (res.confirm) {
            wx.navigateTo({ url: '/pages/vip/vip' })
          } else {
            wx.navigateTo({
              url: `/pages/payment/payment?type=single&targetUid=${encodeURIComponent(match.targetUid)}&amount=9.9&productName=${encodeURIComponent('单次查询解锁')}`
            })
          }
        }
      })
      return
    }

    // VIP次数检查
    if (!queryInfo.hasVipCount) {
      wx.showToast({ title: '查询次数已用完', icon: 'none' })
      return
    }

    // 跳转结果页
    wx.navigateTo({
      url: `/pages/result/result?uid=${encodeURIComponent(match.targetUid)}`
    })
  },

  // 去投诉
  goComplaint() {
    wx.switchTab({ url: '/pages/complaint/complaint' })
  }
})
