// pages/profile-edit/profile-edit.js
const store = require('../../utils/store.js')

Page({
  data: {
    type: 'nickname', // avatar / nickname
    avatar: '',
    nickname: '',
    saving: false
  },

  onLoad(options) {
    const type = options.type || 'nickname'
    this.setData({ type })
    this.loadUserInfo()
  },

  async loadUserInfo() {
    try {
      const user = await store.getUser()
      this.setData({
        avatar: user.avatar || '',
        nickname: user.nickname || ''
      })
    } catch (err) {
      console.error('加载用户信息失败:', err)
      store.notifyError('无法连接服务器')
    }
  },

  // 选择头像
  chooseAvatar() {
    wx.chooseImage({
      count: 1,
      sizeType: ['compressed'],
      sourceType: ['album', 'camera'],
      success: (res) => {
        this.setData({ avatar: res.tempFilePaths[0] })
      }
    })
  },

  // 昵称输入
  onNicknameInput(e) {
    this.setData({ nickname: e.detail.value })
  },

  // 保存
  async save() {
    if (this.data.saving) return

    if (this.data.type === 'nickname') {
      const nickname = this.data.nickname.trim()
      if (!nickname) {
        wx.showToast({ title: '昵称不能为空', icon: 'none' })
        return
      }
      if (nickname.length < 2 || nickname.length > 12) {
        wx.showToast({ title: '昵称长度为2-12个字符', icon: 'none' })
        return
      }
    }

    this.setData({ saving: true })
    wx.showLoading({ title: '保存中...' })

    try {
      const updateData = {}
      if (this.data.type === 'avatar') {
        updateData.avatar = await store.uploadImage(this.data.avatar)
      } else {
        updateData.nickname = this.data.nickname.trim()
      }
      await store.updateUserInfo(updateData)
      wx.hideLoading()
      wx.showToast({ title: '保存成功', icon: 'success' })
      setTimeout(() => {
        wx.navigateBack()
      }, 1000)
    } catch (err) {
      wx.hideLoading()
      this.setData({ saving: false })
      console.error('保存失败:', err)
      wx.showToast({ title: '保存失败，请重试', icon: 'none' })
    }
  }
})
