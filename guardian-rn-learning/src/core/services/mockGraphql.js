import {ApolloClient, HttpLink} from '@apollo/client';

import {cache} from '@app/services/cache';
import {coupons, products} from '@app/data/mockData';
import {parseGuardianLink} from '@app/helpers/deepLink';

const wait = (value, delay = 120) =>
  new Promise(resolve => {
    setTimeout(() => resolve(value), delay);
  });

export const client = new ApolloClient({
  cache,
  link: new HttpLink({uri: 'https://guardian-learning.invalid/graphql'}),
});

export const mockGraphql = {
  login: async () =>
    wait({
      token: 'learning-token',
      user: {
        name: 'Guardian Learner',
        email: 'learner@example.com',
      },
      rewardPoint: 1280,
    }),
  logout: async () => wait({success: true}),
  getRemoteConfig: async () =>
    wait({
      pwaCheckout: false,
      forceUpdate: false,
      scannerEnabled: true,
    }),
  getProducts: async filters => {
    const filtered = products.filter(product => {
      if (filters?.category && product.category !== filters.category) {
        return false;
      }
      if (filters?.brand && product.brand !== filters.brand) {
        return false;
      }
      return true;
    });

    return wait({items: filtered, totalCount: filtered.length});
  },
  getProductByUrlKey: async urlKey =>
    wait(products.find(product => product.urlKey === urlKey) || null),
  getProductByBarcode: async barcode =>
    wait(products.find(product => product.barcode === barcode) || null),
  getCoupons: async () => wait({items: coupons, totalCount: coupons.length}),
  resolveUrl: async url => wait(parseGuardianLink(url)),
};
