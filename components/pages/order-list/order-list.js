// pages/order-list/order-list.js
const store = require('../../utils/store.js')

Page({
  data: {
    activeTab: 'all',
    orders: [],
    filteredOrders: []
  },

  onLoad() {
    this.loadOrders()
  },

  onShow() {
    this.loadOrders()
  },

  async loadOrders() {
    try {
      const statusMap = { success: '已支付', pending: '待支付', failed: '支付失败', refunded: '已退款' }
      const orders = await store.getOrders()
      const formattedOrders = orders.map(item => ({
        ...item,
        statusText: statusMap[item.payStatus] || item.payStatus,
        timeText: store.formatDateTime(item.payTime || item.createdAt)
      }))
      this.setData({ orders: formattedOrders })
      this.filterOrders()
    } catch (err) {
      console.error('加载订单失败:', err)
    }
  },

  switchTab(e) {
    const tab = e.currentTarget.dataset.tab
    this.setData({ activeTab: tab })
    this.filterOrders()
  },

  filterOrders() {
    const { activeTab, orders } = this.data
    let filtered = orders
    if (activeTab === 'vip') {
      filtered = orders.filter(o => o.productType && o.productType.startsWith('vip_'))
    } else if (activeTab === 'single') {
      filtered = orders.filter(o => o.productType === 'single_query')
    } else if (activeTab === 'service') {
      filtered = orders.filter(o => o.productType === 'dispute_service' || o.productType === 'contact_service')
    }
    this.setData({ filteredOrders: filtered })
  }
})
