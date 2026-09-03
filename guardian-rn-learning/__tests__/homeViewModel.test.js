const {
  buildMemberSummary,
  buildProductListSummary,
} = require('../src/core/helpers/homeViewModel');

test('builds signed-in member summary with points and coupon count', () => {
  expect(
    buildMemberSummary({
      user: {name: 'Guardian Learner', level: 'Gold Member'},
      userType: 'customer',
      points: 1280,
      couponCount: 2,
      cartQty: 3,
    }),
  ).toEqual({
    greeting: 'Hi, Guardian Learner',
    level: 'Gold Member',
    pointsLabel: '1,280 pts',
    couponLabel: '2 coupons',
    cartLabel: '3 items',
    signedIn: true,
  });
});

test('builds guest member summary with sign-in prompt', () => {
  expect(
    buildMemberSummary({
      user: null,
      userType: 'guest',
      points: 0,
      couponCount: 0,
      cartQty: 0,
    }),
  ).toEqual({
    greeting: 'Welcome, Guest',
    level: 'Sign in to unlock member benefits',
    pointsLabel: '0 pts',
    couponLabel: '0 coupons',
    cartLabel: '0 items',
    signedIn: false,
  });
});

test('builds product list summary from products and active filter', () => {
  const products = [
    {category: 'vitamins', brand: 'guardian-health'},
    {category: 'skincare', brand: 'clean-lab'},
    {category: 'vitamins', brand: 'guardian-health'},
  ];

  expect(buildProductListSummary(products, 'vitamins')).toEqual({
    totalLabel: '3 results',
    filterLabel: 'Vitamins',
    brandCountLabel: '2 brands',
    categoryCountLabel: '2 categories',
  });
});
