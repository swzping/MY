const {
  parseGuardianLink,
  resolveScannerInput,
} = require('../src/core/helpers/deepLink');

test('parses Guardian product, category, brand, and CMS links', () => {
  expect(parseGuardianLink('https://guardian.test/product/daily-vitamin-c')).toEqual({
    type: 'product',
    value: 'daily-vitamin-c',
    route: 'ProductDetail',
  });
  expect(parseGuardianLink('https://guardian.test/category/vitamins')).toEqual({
    type: 'category',
    value: 'vitamins',
    route: 'Catalog',
  });
  expect(parseGuardianLink('guardian://brand/guardian-health')).toEqual({
    type: 'brand',
    value: 'guardian-health',
    route: 'Catalog',
  });
  expect(parseGuardianLink('https://guardian.test/cms/membership-benefit')).toEqual({
    type: 'cms',
    value: 'membership-benefit',
    route: 'CmsPage',
  });
});

test('scanner resolves barcode to product route', () => {
  expect(resolveScannerInput('8991002100012')).toEqual({
    type: 'barcode',
    route: 'ProductDetail',
    params: {
      productSku: 'SKU-001',
      productUrlKey: 'daily-vitamin-c',
    },
    message: 'Product found from barcode',
  });
});

test('scanner resolves Guardian QR links and rejects unsupported values', () => {
  expect(resolveScannerInput('https://guardian.test/product/hydrating-cleanser')).toEqual({
    type: 'qr',
    route: 'ProductDetail',
    params: {
      productUrlKey: 'hydrating-cleanser',
    },
    message: 'Guardian link resolved',
  });

  expect(resolveScannerInput('https://example.com/not-guardian')).toEqual({
    type: 'unknown',
    route: null,
    params: {},
    message: 'Unsupported QR or barcode',
  });
});
