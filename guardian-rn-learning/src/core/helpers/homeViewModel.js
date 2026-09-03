const titleCase = value =>
  String(value || '')
    .split('-')
    .filter(Boolean)
    .map(part => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');

const pluralize = (count, label) => {
  const plural = label === 'category' ? 'categories' : `${label}s`;
  return `${count} ${count === 1 ? label : plural}`;
};

const formatNumber = value => new Intl.NumberFormat('en-US').format(Number(value) || 0);

const buildMemberSummary = ({
  user,
  userType,
  points = 0,
  couponCount = 0,
  cartQty = 0,
}) => {
  const signedIn = Boolean(user) && userType !== 'guest';

  return {
    greeting: signedIn ? `Hi, ${user.name}` : 'Welcome, Guest',
    level: signedIn
      ? user.level || 'Guardian Member'
      : 'Sign in to unlock member benefits',
    pointsLabel: `${formatNumber(points)} pts`,
    couponLabel: pluralize(couponCount, 'coupon'),
    cartLabel: pluralize(cartQty, 'item'),
    signedIn,
  };
};

const buildProductListSummary = (products, activeFilter = 'all') => {
  const brandCount = new Set(products.map(product => product.brand)).size;
  const categoryCount = new Set(products.map(product => product.category)).size;

  return {
    totalLabel: pluralize(products.length, 'result'),
    filterLabel: activeFilter === 'all' ? 'All Products' : titleCase(activeFilter),
    brandCountLabel: pluralize(brandCount, 'brand'),
    categoryCountLabel: pluralize(categoryCount, 'category'),
  };
};

module.exports = {
  buildMemberSummary,
  buildProductListSummary,
};
