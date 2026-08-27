const {coupons} = require('../data/mockData');

const roundMoney = value => Math.round((Number(value) + Number.EPSILON) * 100) / 100;

const normalizeQuantity = quantity => Math.max(0, Number(quantity) || 0);

const addCartItem = (items, product) => {
  const existing = items.find(item => item.sku === product.sku);

  if (existing) {
    return items.map(item =>
      item.sku === product.sku
        ? {...item, quantity: item.quantity + 1}
        : item,
    );
  }

  return [
    ...items,
    {
      sku: product.sku,
      name: product.name,
      price: product.price,
      quantity: 1,
    },
  ];
};

const changeCartQuantity = (items, sku, quantity) => {
  const nextQuantity = normalizeQuantity(quantity);

  return items
    .map(item => (item.sku === sku ? {...item, quantity: nextQuantity} : item))
    .filter(item => item.quantity > 0);
};

const removeCartItem = (items, sku) => items.filter(item => item.sku !== sku);

const getSubtotal = items =>
  roundMoney(items.reduce((sum, item) => sum + item.price * item.quantity, 0));

const applyCoupon = (items, code) => {
  const normalizedCode = String(code || '').trim().toUpperCase();
  const coupon = coupons.find(item => item.code === normalizedCode);

  if (!coupon) {
    return {code: null, discount: 0, message: 'Invalid coupon'};
  }

  const subtotal = getSubtotal(items);
  const discount =
    coupon.type === 'percent'
      ? roundMoney(subtotal * (coupon.value / 100))
      : roundMoney(Math.min(coupon.value, subtotal));

  return {
    code: coupon.code,
    discount,
    message: 'Coupon applied',
  };
};

const getCartTotals = (items, coupon = null) => {
  const subtotal = getSubtotal(items);
  const discount = roundMoney(coupon?.discount || 0);

  return {
    subtotal,
    discount,
    grandTotal: roundMoney(Math.max(0, subtotal - discount)),
  };
};

module.exports = {
  addCartItem,
  changeCartQuantity,
  removeCartItem,
  applyCoupon,
  getCartTotals,
};
