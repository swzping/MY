import React from 'react';
import {StyleSheet, View} from 'react-native';
import {Text} from 'react-native-paper';

import ActionButton from '@app/components/ActionButton';
import ProductCard from '@app/components/ProductCard';
import Screen from '@app/components/Screen';
import {modules} from '@app/config/modules';
import {navigateTo} from '@app/helpers/navigation';
import {linkExamples, products} from '../../../core/data/mockData';
import {colors} from '@app/styles/theme';

const HomeScreen = () => (
  <Screen
    title="Guardian Lab"
    subtitle="This is loaded from src/override, proving the same @app import can prefer brand-specific files over core files.">
    <View style={styles.panel}>
      <Text variant="titleMedium" style={styles.heading}>Original project ideas</Text>
      <Text>Core/override architecture</Text>
      <Text>Module switches: {Object.keys(modules).length} registered modules</Text>
      <Text>Deep link examples: {linkExamples.length}</Text>
    </View>
    <ProductCard product={products[0]} actionLabel="Open Product" onPress={() => navigateTo('productDetail', {productUrlKey: products[0].urlKey})} />
    <ActionButton mode="outlined" onPress={() => navigateTo('couponWallet')}>Open Coupon Wallet</ActionButton>
  </Screen>
);

const styles = StyleSheet.create({
  panel: {backgroundColor: colors.surface, borderColor: colors.border, borderRadius: 8, borderWidth: 1, gap: 8, padding: 14},
  heading: {fontWeight: '700'},
});

export default HomeScreen;
