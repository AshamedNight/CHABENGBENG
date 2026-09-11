// utils/platform.js - 平台能力判断
// 微信小程序 iOS 端禁止虚拟商品支付（VIP/查询次数/维权服务均属虚拟商品），
// iOS 用户统一拦截付费入口，仅安卓开放。

let cachedSystem = null

function isIOS() {
  if (cachedSystem === null) {
    try {
      const info = wx.getDeviceInfo ? wx.getDeviceInfo() : wx.getSystemInfoSync()
      cachedSystem = (info.platform || info.system || '').toLowerCase().indexOf('ios') >= 0 ||
                     (info.system || '').toLowerCase().indexOf('ios') >= 0
    } catch (e) {
      cachedSystem = false
    }
  }
  return cachedSystem
}

/**
 * 付费入口守卫。iOS 下弹提示并返回 true（调用方应直接 return）。
 * 用法：if (guardPayment()) return
 */
function guardPayment(scene) {
  if (!isIOS()) return false
  wx.showModal({
    title: '提示',
    content: '因平台规则限制，iOS 端暂不支持购买虚拟服务',
    showCancel: false,
    confirmText: '我知道了'
  })
  console.log('[paywall] iOS 付费拦截:', scene || '')
  return true
}

module.exports = { isIOS, guardPayment }
