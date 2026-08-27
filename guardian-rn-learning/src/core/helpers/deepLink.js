const {products} = require('../data/mockData');

const routeByType = {
  product: 'ProductDetail',
  category: 'Catalog',
  brand: 'Catalog',
  cms: 'CmsPage',
  campaign: 'Campaign',
};

const normalizePathParts = url => {
  try {
    const parsed = new URL(url);

    if (parsed.protocol === 'guardian:') {
      return [parsed.hostname, ...parsed.pathname.split('/').filter(Boolean)];
    }

    if (parsed.hostname !== 'guardian.test') {
      return [];
    }

    return parsed.pathname.split('/').filter(Boolean);
  } catch (error) {
    return [];
  }
};

const parseGuardianLink = url => {
  const [type, value] = normalizePathParts(url);

  if (!type || !value || !routeByType[type]) {
    return null;
  }

  return {
    type,
    value,
    route: routeByType[type],
  };
};

const resolveProductParams = value => ({
  productUrlKey: value,
});

const resolveScannerInput = input => {
  const scanValue = String(input || '').trim();
  const product = products.find(item => item.barcode === scanValue);

  if (product) {
    return {
      type: 'barcode',
      route: 'ProductDetail',
      params: {
        productSku: product.sku,
        productUrlKey: product.urlKey,
      },
      message: 'Product found from barcode',
    };
  }

  const parsed = parseGuardianLink(scanValue);

  if (parsed) {
    return {
      type: 'qr',
      route: parsed.route,
      params: parsed.type === 'product' ? resolveProductParams(parsed.value) : {
        type: parsed.type,
        value: parsed.value,
      },
      message: 'Guardian link resolved',
    };
  }

  return {
    type: 'unknown',
    route: null,
    params: {},
    message: 'Unsupported QR or barcode',
  };
};

module.exports = {
  parseGuardianLink,
  resolveScannerInput,
};
