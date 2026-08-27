const {
  addCartItem,
  changeCartQuantity,
  removeCartItem,
  applyCoupon,
  getCartTotals,
} = require('../src/core/helpers/cartLogic');

const product = {
  sku: 'SKU-001',
  name: 'Daily Vitamin C',
  price: 12,
};

test('adds a product and increases quantity when the sku already exists', () => {
  const firstCart = addCartItem([], product);
  const secondCart = addCartItem(firstCart, product);

  expect(secondCart).toEqual([
    {
      sku: 'SKU-001',
      name: 'Daily Vitamin C',
      price: 12,
      quantity: 2,
    },
  ]);
});

test('changes quantity and removes items when quantity reaches zero', () => {
  const cart = addCartItem([], product);
  const updated = changeCartQuantity(cart, 'SKU-001', 3);
  const removed = removeCartItem(updated, 'SKU-001');

  expect(updated[0].quantity).toBe(3);
  expect(removed).toEqual([]);
});

test('applies valid coupon discounts and rejects invalid coupon codes', () => {
  const cart = changeCartQuantity(addCartItem([], product), 'SKU-001', 2);
  const valid = applyCoupon(cart, 'WELCOME10');
  const invalid = applyCoupon(cart, 'NOPE');

  expect(valid).toEqual({code: 'WELCOME10', discount: 2.4, message: 'Coupon applied'});
  expect(invalid).toEqual({code: null, discount: 0, message: 'Invalid coupon'});
});

test('calculates subtotal, discount, and grand total', () => {
  const cart = changeCartQuantity(addCartItem([], product), 'SKU-001', 2);
  const coupon = applyCoupon(cart, 'WELCOME10');

  expect(getCartTotals(cart, coupon)).toEqual({
    subtotal: 24,
    discount: 2.4,
    grandTotal: 21.6,
  });
});
