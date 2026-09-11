// pages/payment/payment.js
const store = require('../../utils/store.js')
const { guardPayment } = require('../../utils/platform.js')

Page({
  data: {
    type: '',           // vip / single / dispute / contact
    plan: '',
    amount: '0',
    productName: '',
    productDesc: '',
    productIcon: '👑',
    targetUid: '',
    complaintId: '',
    complaintNo: '',
    paying: false,
    showSuccess: false,
    successDesc: '',
    successBtnText: '完成'
  },

  onLoad(options) {
    // iOS 虚拟支付兜底拦截：任何入口漏进来都挡在支付页之外
    if (guardPayment('payment-page')) {
      setTimeout(() => wx.navigateBack({ delta: 1 }), 1200)
      return
    }
    const type = options.type || 'vip'
    const plan = options.plan || ''
    const amount = options.amount || '0'
    const productName = decodeURIComponent(options.productName || '')
    const targetUid = decodeURIComponent(options.targetUid || '')
    const complaintId = options.complaintId || ''
    const complaintNo = decodeURIComponent(options.complaintNo || '')

    let productDesc = ''
    let productIcon = '👑'

    if (type === 'vip') {
      productDesc = '年卡80次查询（50次+赠30次）· 完整记录 · 风险自查 · 优先服务'
      productIcon = '👑'
    } else if (type === 'single') {
      productDesc = '解锁当前查询对象完整内容，7天内有效'
      productIcon = '🔍'
    } else if (type === 'dispute') {
      productDesc = '对投诉记录的真实性/处理结果提出异议，专业团队跟进'
      productIcon = '📝'
    } else if (type === 'contact') {
      productDesc = '联系该投诉的处理人员，沟通维权进展'
      productIcon = '💬'
    }

    this.setData({
      type,
      plan,
      amount,
      productName: productName || this.getDefaultName(type),
      productDesc,
      productIcon,
      targetUid,
      complaintId,
      complaintNo
    })
  },

  getDefaultName(type) {
    const map = {
      vip: 'VIP年卡',
      single: '单次查询解锁',
      dispute: '提起异议服务',
      contact: '联系处理服务'
    }
    return map[type] || '商品'
  },

  async doPay() {
    if (this.data.paying) return
    this.setData({ paying: true })

    try {
      const { type, plan, amount, productName, targetUid, complaintId } = this.data

      // 1. 创建订单
      const productTypeMap = {
        vip: plan,
        single: 'single_query',
        dispute: 'dispute_service',
        contact: 'contact_service'
      }
      const orderData = {
        productType: productTypeMap[type] || type,
        productName,
        amount: parseFloat(amount),
        singleQueryTargetUid: targetUid,
        relatedComplaintId: complaintId
      }
      const order = await store.addOrder(orderData)

      // 2. 模拟支付
      await store.payOrder(order.order_id || order.id)

      // 3. 支付成功处理
      let successDesc = ''
      let successBtnText = '完成'

      if (type === 'vip') {
        successDesc = 'VIP年卡已开通，80次查询权益（50次+赠30次）已生效'
        successBtnText = '返回会员专区'
      } else if (type === 'single') {
        successDesc = '单次查询已解锁，可查看当前对象完整报告'
        successBtnText = '查看查询结果'
      } else if (type === 'dispute') {
        successDesc = '异议服务已开通，专业团队将在24小时内联系您'
        successBtnText = '提交异议'
      } else if (type === 'contact') {
        successDesc = '联系处理服务已开通，处理人员将尽快与您对接'
        successBtnText = '联系处理'
      }

      this.setData({
        paying: false,
        showSuccess: true,
        successDesc,
        successBtnText
      })
    } catch (err) {
      console.error('支付失败:', err)
      this.setData({ paying: false })
      wx.showToast({ title: '支付失败，请重试', icon: 'none' })
    }
  },

  onSuccessConfirm() {
    const { type, targetUid, complaintId, complaintNo } = this.data

    if (type === 'single' && targetUid) {
      wx.redirectTo({
        url: `/pages/result/result?uid=${encodeURIComponent(targetUid)}`
      })
    } else if (type === 'vip') {
      wx.navigateBack()
    } else if (type === 'dispute') {
      wx.redirectTo({
        url: `/pages/service-dispute/service-dispute?complaintId=${complaintId}&complaintNo=${encodeURIComponent(complaintNo)}`
      })
    } else if (type === 'contact') {
      wx.redirectTo({
        url: `/pages/service-contact/service-contact?complaintId=${complaintId}&complaintNo=${encodeURIComponent(complaintNo)}`
      })
    } else {
      wx.navigateBack()
    }
  }
})
