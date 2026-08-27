import React from 'react';
import {useReactiveVar} from '@apollo/client';
import {StyleSheet, View} from 'react-native';
import {Text} from 'react-native-paper';

import ActionButton from '@app/components/ActionButton';
import Screen from '@app/components/Screen';
import {Storage} from '@app/helpers/storage';
import {
  USER_GUEST,
  rxAppMaintenance,
  rxCartItems,
  rxSelectedCoupon,
  rxUserInformation,
  rxUserRewardPoint,
  rxUserToken,
  rxUserType,
  showSnackbar,
  syncCartState,
} from '@app/services/cache';
import {colors} from '@app/styles/theme';

const AccountScreen = () => {
  const user = useReactiveVar(rxUserInformation);
  const userType = useReactiveVar(rxUserType);
  const points = useReactiveVar(rxUserRewardPoint);

  const logout = async () => {
    await Storage.clearLearningState();
    rxUserToken(null);
    rxUserType(USER_GUEST);
    rxUserInformation(null);
    rxUserRewardPoint(0);
    rxSelectedCoupon(null);
    syncCartState([]);
    showSnackbar('Mock session cleared');
  };

  return (
    <Screen title="Account" subtitle="A compact version of the original account center and initialization state.">
      <View style={styles.panel}>
        <Text>Name: {user?.name || 'Unknown'}</Text>
        <Text>User type: {userType}</Text>
        <Text>Reward points: {points}</Text>
        <Text>Cart items in reactive var: {rxCartItems().length}</Text>
      </View>
      <ActionButton mode="outlined" onPress={() => rxAppMaintenance(true)}>Enter Maintenance Mode</ActionButton>
      <ActionButton mode="text" onPress={logout}>Log Out</ActionButton>
    </Screen>
  );
};

const styles = StyleSheet.create({
  panel: {backgroundColor: colors.surface, borderColor: colors.border, borderRadius: 8, borderWidth: 1, gap: 8, padding: 14},
});

export default AccountScreen;
