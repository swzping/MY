import React from 'react';

import ActionButton from '@app/components/ActionButton';
import Screen from '@app/components/Screen';
import {Storage, storageKeys} from '@app/helpers/storage';
import {
  USER_CUSTOMER,
  USER_GUEST,
  rxUserInformation,
  rxUserRewardPoint,
  rxUserToken,
  rxUserType,
  showSnackbar,
} from '@app/services/cache';
import {mockGraphql} from '@app/services/mockGraphql';

const AuthLandingScreen = () => {
  const signIn = async () => {
    const result = await mockGraphql.login();
    await Storage.set(storageKeys.TOKEN, result.token);
    await Storage.set(storageKeys.USER_TYPE, USER_CUSTOMER);
    rxUserToken(result.token);
    rxUserType(USER_CUSTOMER);
    rxUserInformation(result.user);
    rxUserRewardPoint(result.rewardPoint);
    showSnackbar('Signed in with a mock token');
  };

  const continueAsGuest = async () => {
    await Storage.set(storageKeys.USER_TYPE, USER_GUEST);
    rxUserToken('guest-session');
    rxUserType(USER_GUEST);
    rxUserInformation({name: 'Guest Learner'});
    showSnackbar('Continuing as guest');
  };

  return (
    <Screen
      title="Guardian RN Learning"
      subtitle="A small app for learning the architecture behind app-guardian: auth switching, module config, reactive state, and mock commerce flows.">
      <ActionButton onPress={signIn}>Sign In</ActionButton>
      <ActionButton mode="outlined" onPress={continueAsGuest}>Continue As Guest</ActionButton>
    </Screen>
  );
};

export default AuthLandingScreen;
