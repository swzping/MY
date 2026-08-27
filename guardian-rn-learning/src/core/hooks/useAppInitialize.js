import {useEffect} from 'react';

import {Storage, storageKeys} from '@app/helpers/storage';
import {
  USER_CUSTOMER,
  USER_GUEST,
  rxAppLoading,
  rxAppMaintenance,
  rxRemoteConfig,
  rxSelectedCoupon,
  rxUserInformation,
  rxUserRewardPoint,
  rxUserToken,
  rxUserType,
  syncCartState,
} from '@app/services/cache';
import {mockGraphql} from '@app/services/mockGraphql';

const useAppInitialize = () => {
  useEffect(() => {
    let mounted = true;

    const initialize = async () => {
      rxAppLoading(true);

      const [token, userType, cartItems, selectedCoupon, remoteConfig] =
        await Promise.all([
          Storage.get(storageKeys.TOKEN),
          Storage.get(storageKeys.USER_TYPE),
          Storage.get(storageKeys.CART_ITEMS),
          Storage.get(storageKeys.SELECTED_COUPON),
          mockGraphql.getRemoteConfig(),
        ]);

      if (!mounted) {
        return;
      }

      rxRemoteConfig(remoteConfig);
      rxAppMaintenance(Boolean(remoteConfig.forceUpdate));
      rxUserToken(token);
      rxUserType(userType || (token ? USER_CUSTOMER : USER_GUEST));
      rxUserInformation(
        token
          ? {name: 'Guardian Learner', email: 'learner@example.com'}
          : null,
      );
      rxUserRewardPoint(token ? 1280 : 0);
      syncCartState(cartItems || []);
      rxSelectedCoupon(selectedCoupon || null);
      rxAppLoading(false);
    };

    initialize();

    return () => {
      mounted = false;
    };
  }, []);
};

export default useAppInitialize;
