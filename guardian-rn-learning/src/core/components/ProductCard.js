import React from 'react';
import {StyleSheet, View} from 'react-native';
import {Text} from 'react-native-paper';

import ActionButton from '@app/components/ActionButton';
import {colors} from '@app/styles/theme';

const ProductCard = ({product, onPress, actionLabel = 'View'}) => (
  <View style={styles.card}>
    <Text variant="titleMedium" style={styles.name}>{product.name}</Text>
    <Text style={styles.meta}>{product.brand} / {product.category}</Text>
    <Text style={styles.description}>{product.description}</Text>
    <View style={styles.row}>
      <Text style={styles.price}>${product.price.toFixed(2)}</Text>
      <ActionButton onPress={onPress}>{actionLabel}</ActionButton>
    </View>
  </View>
);

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 8,
    borderWidth: 1,
    gap: 8,
    padding: 14,
  },
  name: {fontWeight: '700', color: colors.text},
  meta: {color: colors.primaryDark},
  description: {color: colors.muted, lineHeight: 19},
  row: {alignItems: 'center', flexDirection: 'row', justifyContent: 'space-between'},
  price: {fontWeight: '700', color: colors.text},
});

export default ProductCard;
