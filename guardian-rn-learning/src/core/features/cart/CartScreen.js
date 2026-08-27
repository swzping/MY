import React from 'react';
import {useReactiveVar} from '@apollo/client';
import {StyleSheet, View} from 'react-native';
import {Text} from 'react-native-paper';

import ActionButton from '@app/components/ActionButton';
import Screen from '@app/components/Screen';
import {Storage, storageKeys} from '@app/helpers/storage';
import {changeCartQuantity, getCartTotals, removeCartItem} from '@app/helpers/cartLogic';
import {navigateTo} from '@app/helpers/navigation';
import {rxCartItems, rxSelectedCoupon, showSnackbar, syncCartState} from '@app/services/cache';
import {colors} from '@app/styles/theme';

const CartScreen = () => {
  const items = useReactiveVar(rxCartItems);
  const selectedCoupon = useReactiveVar(rxSelectedCoupon);
  const totals = getCartTotals(items, selectedCoupon);

  const updateCart = async nextItems => {
    syncCartState(nextItems);
    await Storage.set(storageKeys.CART_ITEMS, nextItems);
  };

  return (
    <Screen title="Cart" subtitle="Apollo reactive variables keep cart state available across tabs.">
      {items.length === 0 ? <Text>Your cart is empty. Add a product from Catalog.</Text> : null}
      {items.map(item => (
        <View key={item.sku} style={styles.item}>
          <Text variant="titleMedium">{item.name}</Text>
          <Text>${item.price.toFixed(2)} x {item.quantity}</Text>
          <View style={styles.row}>
            <ActionButton mode="outlined" onPress={() => updateCart(changeCartQuantity(items, item.sku, item.quantity - 1))}>-</ActionButton>
            <ActionButton mode="outlined" onPress={() => updateCart(changeCartQuantity(items, item.sku, item.quantity + 1))}>+</ActionButton>
            <ActionButton mode="text" onPress={() => updateCart(removeCartItem(items, item.sku))}>Remove</ActionButton>
          </View>
        </View>
      ))}
      <View style={styles.total}>
        <Text>Subtotal: ${totals.subtotal.toFixed(2)}</Text>
        <Text>Discount: ${totals.discount.toFixed(2)}</Text>
        <Text variant="titleLarge">Grand Total: ${totals.grandTotal.toFixed(2)}</Text>
      </View>
      <ActionButton onPress={() => navigateTo('couponWallet')}>Choose Coupon</ActionButton>
      <ActionButton mode="outlined" onPress={() => showSnackbar('Checkout is intentionally mocked in this learning app')}>Mock Checkout</ActionButton>
    </Screen>
  );
};

const styles = StyleSheet.create({
  item: {backgroundColor: colors.surface, borderColor: colors.border, borderRadius: 8, borderWidth: 1, gap: 8, padding: 14},
  row: {flexDirection: 'row', gap: 8},
  total: {backgroundColor: colors.surface, borderRadius: 8, gap: 6, padding: 14},
});

export default CartScreen;
