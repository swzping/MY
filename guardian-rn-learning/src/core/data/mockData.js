const products = [
  {
    sku: 'SKU-001',
    barcode: '8991002100012',
    name: 'Daily Vitamin C',
    urlKey: 'daily-vitamin-c',
    category: 'vitamins',
    brand: 'guardian-health',
    price: 12,
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
    description: 'A larger cart item for subtotal and coupon examples.',
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

module.exports = {
  products,
  coupons,
  linkExamples,
};
