// pages/vip/vip.js
const store = require('../../utils/store.js')
const { guardPayment } = require('../../utils/platform.js')

Page({
  data: {
    isVip: false,
    vipExpireText: '',
    faqs: [
      { q: 'VIP查询次数用完了怎么办？', a: '可购买单次查询（9.9元/次），或续费VIP年卡获得80次查询额度。', open: false },
      { q: '提交材料会消耗查询次数吗？', a: '不会。提交材料永久免费。', open: false },
      { q: '同一UID重复查询会扣次数吗？', a: '同一账号UID在24小时内重复查询不重复扣次。', open: false },
      { q: 'VIP可以退款吗？', a: '虚拟商品一经开通不支持退款，请确认后购买。', open: false }
    ]
  },

  onLoad() {
    this.loadUserStatus()
  },
  onShow() {
    this.loadUserStatus()
  },

  async loadUserStatus() {
    try {
      const user = await store.getUser()
      this.setData({
        isVip: user.isVip,
        vipExpireText: user.vipExpireAt ? store.formatDate(user.vipExpireAt) : ''
      })
    } catch (err) {
      console.error('加载用户状态失败:', err)
      store.notifyError('无法连接服务器')
    }
  },

  toggleFaq(e) {
    const index = e.currentTarget.dataset.index
    const faqs = this.data.faqs.map((item, i) => ({
      ...item,
      open: i === index ? !item.open : false
    }))
    this.setData({ faqs })
  },

  goPay() {
    if (guardPayment('vip-year')) return
    wx.navigateTo({
      url: `/pages/payment/payment?type=vip&plan=vip_year&amount=399&productName=${encodeURIComponent('VIP年卡')}`
    })
  },

  goSinglePay() {
    if (guardPayment('vip-single')) return
    wx.navigateTo({
      url: '/pages/payment/payment?type=single&amount=9.9&productName=' + encodeURIComponent('单次查询解锁')
    })
  }
})
