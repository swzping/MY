const products = [
  {
    sku: 'SKU-001',
    barcode: '8991002100012',
    name: 'Daily Vitamin C',
    urlKey: 'daily-vitamin-c',
    category: 'vitamins',
    brand: 'guardian-health',
    price: 12,
    originalPrice: 15,
    badge: 'Member Deal',
    rating: 4.8,
    stockLabel: 'In stock',
    description: 'A compact product used to learn catalog, detail, and cart flows.',
  },
  {
    sku: 'SKU-002',
    barcode: '8991002100029',
    name: 'Hydrating Cleanser',
    urlKey: 'hydrating-cleanser',
    category: 'skincare',
    brand: 'clean-lab',
    price: 18,
    originalPrice: 22,
    badge: 'Best Seller',
    rating: 4.7,
    stockLabel: 'Low stock',
    description: 'A second product used to test URL and QR routing.',
  },
  {
    sku: 'SKU-003',
    barcode: '8991002100036',
    name: 'Family First Aid Kit',
    urlKey: 'family-first-aid-kit',
    category: 'health',
    brand: 'guardian-health',
    price: 25,
    originalPrice: 29,
    badge: 'Online Only',
    rating: 4.6,
    stockLabel: 'In stock',
    description: 'A larger cart item for subtotal and coupon examples.',
  },
  {
    sku: 'SKU-004',
    barcode: '8991002100043',
    name: 'Kids Immunity Gummies',
    urlKey: 'kids-immunity-gummies',
    category: 'vitamins',
    brand: 'little-guardian',
    price: 16,
    originalPrice: 19,
    badge: 'New',
    rating: 4.9,
    stockLabel: 'In stock',
    description: 'A colorful learning item for two-column catalog layouts.',
  },
];

const coupons = [
  {
    code: 'WELCOME10',
    label: 'Welcome 10%',
    type: 'percent',
    value: 10,
  },
  {
    code: 'SAVE5',
    label: 'Save 5',
    type: 'fixed',
    value: 5,
  },
];

const linkExamples = [
  'https://guardian.test/product/daily-vitamin-c',
  'https://guardian.test/category/vitamins',
  'guardian://brand/guardian-health',
  'https://guardian.test/cms/membership-benefit',
];

const member = {
  name: 'Guardian Learner',
  email: 'learner@example.com',
  level: 'Gold Member',
  memberId: 'GL-1024',
  nextReward: 'Spend $18 more to unlock a bonus coupon',
};

module.exports = {
  products,
  coupons,
  linkExamples,
  member,
};
