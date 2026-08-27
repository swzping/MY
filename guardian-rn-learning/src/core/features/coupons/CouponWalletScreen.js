import React, {useEffect, useState} from 'react';
import {useReactiveVar} from '@apollo/client';
import {StyleSheet, View} from 'react-native';
import {Text, TextInput} from 'react-native-paper';

import ActionButton from '@app/components/ActionButton';
import Screen from '@app/components/Screen';
import {applyCoupon} from '@app/helpers/cartLogic';
import {Storage, storageKeys} from '@app/helpers/storage';
import {rxCartItems, rxSelectedCoupon, showSnackbar} from '@app/services/cache';
import {mockGraphql} from '@app/services/mockGraphql';
import {colors} from '@app/styles/theme';

const CouponWalletScreen = ({navigation}) => {
  const cartItems = useReactiveVar(rxCartItems);
  const selectedCoupon = useReactiveVar(rxSelectedCoupon);
  const [coupons, setCoupons] = useState([]);
  const [manualCode, setManualCode] = useState('');

  useEffect(() => {
    mockGraphql.getCoupons().then(result => setCoupons(result.items));
  }, []);

  const applyCode = async code => {
    const result = applyCoupon(cartItems, code);
    rxSelectedCoupon(result.code ? result : null);
    await Storage.set(storageKeys.SELECTED_COUPON, result.code ? result : null);
    showSnackbar(result.message);
  };

  return (
    <Screen title="Coupon Wallet" subtitle="Mirrors the source app coupon wallet and checkout coupon apply flow with mock data.">
      <Text>Selected: {selectedCoupon?.code || 'None'}</Text>
      <TextInput label="Coupon code" value={manualCode} onChangeText={setManualCode} mode="outlined" />
      <ActionButton onPress={() => applyCode(manualCode)}>Apply Manual Code</ActionButton>
      {coupons.map(coupon => (
        <View key={coupon.code} style={styles.card}>
          <Text variant="titleMedium">{coupon.label}</Text>
          <Text>{coupon.code}</Text>
          <ActionButton mode="outlined" onPress={() => applyCode(coupon.code)}>Use</ActionButton>
        </View>
      ))}
      <ActionButton mode="text" onPress={() => navigation.goBack()}>Back</ActionButton>
    </Screen>
  );
};

const styles = StyleSheet.create({
  card: {backgroundColor: colors.surface, borderColor: colors.border, borderRadius: 8, borderWidth: 1, gap: 8, padding: 14},
});

export default CouponWalletScreen;
