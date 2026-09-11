// app.js
const store = require('./utils/store.js')
const { getToken } = require('./utils/request.js')

App({
  async onLaunch() {
    // 检查是否已登录
    const token = getToken()
    if (!token) {
      // 未登录，执行微信登录
      await this.wxLogin()
    } else {
      // 已登录，刷新用户信息
      try {
        await store.getUser()
      } catch (err) {
        console.error('刷新用户信息失败:', err)
        // token 可能过期，重新登录
        await this.wxLogin()
      }
    }
  },

  /**
   * 微信登录
   */
  async wxLogin() {
    try {
      // 获取微信登录 code
      const loginRes = await new Promise((resolve, reject) => {
        wx.login({
          success: resolve,
          fail: reject
        })
      })

      if (!loginRes.code) {
        throw new Error('获取微信登录 code 失败')
      }

      // 调用后端登录接口
      await store.initUser(loginRes.code, '查崩崩用户', '')
      console.log('登录成功')
    } catch (err) {
      console.error('微信登录失败:', err)
      wx.showToast({ title: '无法连接服务器', icon: 'none' })
    }
  },

  globalData: {
    userInfo: null
  }
})
