import {InMemoryCache, makeVar} from '@apollo/client';

export const USER_GUEST = 'guest';
export const USER_CUSTOMER = 'customer';

export const rxAppLoading = makeVar(true);
export const rxAppSnackbar = makeVar(null);
export const rxAppMaintenance = makeVar(false);
export const rxRemoteConfig = makeVar({
  pwaCheckout: false,
  forceUpdate: false,
  scannerEnabled: true,
});

export const rxUserToken = makeVar(null);
export const rxUserType = makeVar(USER_GUEST);
export const rxUserInformation = makeVar(null);
export const rxUserRewardPoint = makeVar(0);

export const rxCartItems = makeVar([]);
export const rxCartQty = makeVar(0);
export const rxSelectedCoupon = makeVar(null);
export const rxSelectedProduct = makeVar(null);

export const cache = new InMemoryCache({
  addTypename: true,
  typePolicies: {
    Query: {
      fields: {
        products: {
          merge: false,
        },
        coupons: {
          merge: false,
        },
      },
    },
  },
});

export const showSnackbar = message => {
  rxAppSnackbar({message, createdAt: Date.now()});
};

export const syncCartState = items => {
  rxCartItems(items);
  rxCartQty(items.reduce((sum, item) => sum + item.quantity, 0));
};
