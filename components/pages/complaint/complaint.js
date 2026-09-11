// pages/complaint/complaint.js
const store = require('../../utils/store.js')

Page({
  data: {
    form: {
      platform: '',
      customPlatform: '',
      targetUid: '',
      personPhotos: [],           // 相关对象照片（可选，最多4张）
      accountScreenshots: [],     // 相关对象平台帐号截图（必填，最多2张）
      evidenceImages: [],         // 证据照片（必填，最多9张）
      description: '',
      allowContact: false,        // 允许当事人联系
      allowStaffContact: false,   // 允许平台工作人员联系
      agreeJointRights: false     // 同意将证据用于联合维权
    },
    showPlatformPicker: false,
    platformCategories: store.PLATFORM_CATEGORIES,
    submitting: false
  },

  onInput(e) {
    const field = e.currentTarget.dataset.field
    this.setData({ [`form.${field}`]: e.detail.value })
  },

  onCustomPlatformInput(e) {
    this.setData({ 'form.customPlatform': e.detail.value })
  },

  // 统一开关处理
  onSwitchChange(e) {
    const field = e.currentTarget.dataset.field
    this.setData({ [`form.${field}`]: e.detail.value })
  },

  // 平台选择器
  openPlatformPicker() {
    this.setData({ showPlatformPicker: true })
  },
  closePlatformPicker() {
    this.setData({ showPlatformPicker: false })
  },
  stopPropagation() {},
  selectPlatform(e) {
    const platform = e.currentTarget.dataset.platform
    if (platform === '其他') {
      this.setData({
        'form.platform': '其他',
        'form.customPlatform': '',
        showPlatformPicker: false
      })
    } else {
      this.setData({
        'form.platform': platform,
        'form.customPlatform': '',
        showPlatformPicker: false
      })
    }
  },

  // 人物照片上传（最多4张）
  choosePersonPhoto() {
    const remain = 4 - this.data.form.personPhotos.length
    if (remain <= 0) return
    wx.chooseImage({
      count: remain,
      sizeType: ['compressed'],
      sourceType: ['album', 'camera'],
      success: (res) => {
        const newPhotos = res.tempFilePaths.map((p, idx) => ({
          id: Date.now() + idx,
          url: p
        }))
        this.setData({
          'form.personPhotos': [...this.data.form.personPhotos, ...newPhotos]
        })
      }
    })
  },
  removePersonPhoto(e) {
    const index = e.currentTarget.dataset.index
    const photos = this.data.form.personPhotos.filter((_, i) => i !== index)
    this.setData({ 'form.personPhotos': photos })
  },

  // 相关对象平台帐号截图上传（最多2张）
  chooseAccountScreenshot() {
    const remain = 2 - this.data.form.accountScreenshots.length
    if (remain <= 0) return
    wx.chooseImage({
      count: remain,
      sizeType: ['compressed'],
      sourceType: ['album', 'camera'],
      success: (res) => {
        const newShots = res.tempFilePaths.map((p, idx) => ({
          id: Date.now() + idx,
          url: p
        }))
        this.setData({
          'form.accountScreenshots': [...this.data.form.accountScreenshots, ...newShots]
        })
      }
    })
  },
  removeAccountScreenshot(e) {
    const index = e.currentTarget.dataset.index
    const shots = this.data.form.accountScreenshots.filter((_, i) => i !== index)
    this.setData({ 'form.accountScreenshots': shots })
  },

  // 证据照片上传（最多9张）
  chooseEvidenceImage() {
    const remain = 9 - this.data.form.evidenceImages.length
    if (remain <= 0) return
    wx.chooseImage({
      count: remain,
      sizeType: ['compressed'],
      sourceType: ['album', 'camera'],
      success: (res) => {
        const newImages = res.tempFilePaths.map((p, idx) => ({
          id: Date.now() + idx,
          url: p
        }))
        this.setData({
          'form.evidenceImages': [...this.data.form.evidenceImages, ...newImages]
        })
      }
    })
  },
  removeEvidenceImage(e) {
    const index = e.currentTarget.dataset.index
    const images = this.data.form.evidenceImages.filter((_, i) => i !== index)
    this.setData({ 'form.evidenceImages': images })
  },

  // 预览图片
  previewImage(e) {
    const url = e.currentTarget.dataset.url
    wx.previewImage({
      current: url,
      urls: [url]
    })
  },

  // 提交
  async submitComplaint() {
    if (this.data.submitting) return
    const { form } = this.data

    if (!form.platform) {
      wx.showToast({ title: '请选择被投诉平台', icon: 'none' })
      return
    }
    if (form.platform === '其他' && !form.customPlatform.trim()) {
      wx.showToast({ title: '请输入平台名称', icon: 'none' })
      return
    }
    if (!form.targetUid.trim()) {
      wx.showToast({ title: '请填写对方UID', icon: 'none' })
      return
    }
    if (form.accountScreenshots.length === 0) {
      wx.showToast({ title: '请上传相关对象平台帐号截图', icon: 'none' })
      return
    }
    if (form.evidenceImages.length === 0) {
      wx.showToast({ title: '请上传证据照片', icon: 'none' })
      return
    }
    if (!form.description.trim()) {
      wx.showToast({ title: '请填写说明', icon: 'none' })
      return
    }

    const platformName = form.platform === '其他' ? form.customPlatform : form.platform
    this.setData({ submitting: true })
    wx.showLoading({ title: '上传图片中...' })

    try {
      const personPhotos = await store.uploadImages(form.personPhotos)
      const accountScreenshots = await store.uploadImages(form.accountScreenshots)
      const evidenceImages = await store.uploadImages(form.evidenceImages)

      wx.showLoading({ title: '提交中...' })
      await store.addComplaint({
        platform: platformName,
        targetUid: form.targetUid.trim(),
        personPhotos,
        accountScreenshots,
        evidenceImages,
        description: form.description,
        allowContact: form.allowContact,
        allowStaffContact: form.allowStaffContact,
        agreeJointRights: form.agreeJointRights
      })

      wx.hideLoading()
      wx.showToast({ title: '提交成功，感谢您的贡献！', icon: 'success', duration: 1500 })

      this.setData({
        form: {
          platform: '',
          customPlatform: '',
          targetUid: '',
          personPhotos: [],
          accountScreenshots: [],
          evidenceImages: [],
          description: '',
          allowContact: false,
          allowStaffContact: false,
          agreeJointRights: false
        },
        submitting: false
      })

      setTimeout(() => {
        wx.switchTab({ url: '/pages/profile/profile' })
      }, 1500)
    } catch (err) {
      wx.hideLoading()
      this.setData({ submitting: false })
      console.error('提交失败:', err)
      const msg = (err && err.message) ? String(err.message) : '提交失败，请重试'
      wx.showToast({ title: msg.length > 20 ? '提交失败，请重试' : msg, icon: 'none', duration: 2500 })
    }
  }
})
