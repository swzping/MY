export const mockData = {
  products: [
    { id: 'sku-001', name: 'Daily Shield Sunscreen', price: 89000, category: 'Skin Care' },
    { id: 'sku-002', name: 'Vitamin C Bright Serum', price: 129000, category: 'Skin Care' },
    { id: 'sku-003', name: 'Family Health Test Kit', price: 249000, category: 'Health' }
  ],
  customer: {
    id: 'member-1001',
    name: 'Guardian Learner',
    email: 'learner@example.test',
    points: 1280,
    storeCredit: 75000
  },
  orders: [
    { id: 'ORD-9001', status: 'Delivered', total: 318000 },
    { id: 'ORD-9002', status: 'On the road', total: 129000 }
  ],
  coupons: [
    { code: 'HEALTH10', label: '10% health service discount' },
    { code: 'GIFTREADY', label: 'Free gift unlocked' }
  ],
  healthRecords: [
    { id: 'health-1', title: 'Apoteker consultation', status: 'Completed' },
    { id: 'health-2', title: 'Medical test result', status: 'Ready' }
  ],
  events: [
    { id: 'event-1', title: 'Skin Care Class', seats: 12 },
    { id: 'event-2', title: 'Family Health Weekend', seats: 8 }
  ]
};
